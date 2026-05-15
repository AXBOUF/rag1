"""
Privacy-aware PDF ingestion for EVALUATION.
Minimal copy of `version3/ingest_with_privacy.py` with `COLLECTION_NAME` set in config.
"""

import os
import sys
import requests
from pypdf import PdfReader
from chromadb import HttpClient
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.classifier import ContentClassifier
from utils.metadata import create_chunk_metadata
from theme.constants import (
    OLLAMA_BASE,
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    API_KEY,
    EMBED_MODEL,
    CHUNK_SIZE,
    STATUS_ICONS,
)

# Configuration
HEADERS = {"x-api-key": API_KEY}


def collect_pdfs(root_dir: str) -> list[str]:
    pdf_paths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(dirpath, filename))
    return sorted(pdf_paths)


def get_embedding(text: str) -> list[float]:
    text_for_embedding = text[:CHUNK_SIZE] if len(text) > CHUNK_SIZE else text

    try:
        response = requests.post(
            f"{OLLAMA_BASE}/embed",
            json={
                "model": EMBED_MODEL,
                "text": text_for_embedding
            },
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}")

        return response.json()["embedding"]

    except Exception as e:
        print(f"{STATUS_ICONS['error']} Embedding failed: {e}")
        raise


def ingest_pdf(
    pdf_path: str,
    classifier: ContentClassifier,
    collection,
    base_dir: str,
    existing_ids: set = None,
) -> tuple[int, int, int, int, int]:
    if existing_ids is None:
        existing_ids = set()

    try:
        reader = PdfReader(pdf_path)
        filename = os.path.basename(pdf_path)
        folder = os.path.relpath(os.path.dirname(pdf_path), base_dir) or "."

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        total_chunks = 0
        skipped_chunks = 0
        level_counts = {"public": 0, "internal": 0, "confidential": 0}

        print(f"\n{STATUS_ICONS['document']} Ingesting: {pdf_path}")
        print(f"   Pages: {len(reader.pages)}")

        for page_num, page in enumerate(reader.pages):
            chunk_id = f"{folder}__{filename}__page_{page_num}"

            if chunk_id in existing_ids:
                skipped_chunks += 1
                print(f"   {STATUS_ICONS['success']} Page {page_num + 1} already exists, skipping")
                continue

            text = page.extract_text()
            if not text or not text.strip():
                continue

            text = text.strip()

            print(f"   {STATUS_ICONS['progress']} Classifying page {page_num + 1}...", end=" ")
            sensitivity_level = classifier.classify_chunk(text)
            print(f"{sensitivity_level.upper()}")

            level_counts[sensitivity_level] += 1
            total_chunks += 1

            embedding = get_embedding(text)

            metadata = create_chunk_metadata(
                filename=filename,
                folder=folder,
                path=pdf_path,
                page=page_num,
                chunk_index=total_chunks - 1,
                sensitivity_level=sensitivity_level,
                document_source=folder,
                classified_by="llm",
            )

            document_text = text[:CHUNK_SIZE] if len(text) > CHUNK_SIZE else text

            ids.append(chunk_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            documents.append(document_text)

        if ids:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
            print(f"   {STATUS_ICONS['success']} Stored {len(ids)} new chunks")
            print(f"   🟢 PUBLIC: {level_counts['public']} | 🟡 INTERNAL: {level_counts['internal']} | 🔒 CONFIDENTIAL: {level_counts['confidential']}")
        elif skipped_chunks > 0:
            print(f"   {STATUS_ICONS['success']} All {skipped_chunks} pages already ingested")
        else:
            print(f"   {STATUS_ICONS['warning']} No text content found")

        return (
            total_chunks,
            level_counts["public"],
            level_counts["internal"],
            level_counts["confidential"],
            skipped_chunks
        )

    except Exception as e:
        print(f"   {STATUS_ICONS['error']} Failed: {e}")
        return (0, 0, 0, 0, 0)


def get_existing_ids(collection) -> set:
    try:
        result = collection.get(include=[])
        return set(result['ids']) if result['ids'] else set()
    except Exception:
        return set()


def main(pdf_dir: str = "EVALUATION/test_data", flush: bool = False, resume: bool = True):
    print(f"{STATUS_ICONS['brain']} Privacy-Aware RAG Ingestion")
    print(f"{STATUS_ICONS['info']} Using LLM-based classification")
    if resume and not flush:
        print(f"{STATUS_ICONS['info']} Resume mode: will skip existing chunks\n")
    else:
        print()

    print(f"{STATUS_ICONS['progress']} Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

        if flush:
            try:
                chroma_client.delete_collection(name=COLLECTION_NAME)
                print(f"{STATUS_ICONS['success']} Flushed existing collection: {COLLECTION_NAME}")
            except Exception:
                pass

        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        existing_count = collection.count()
        print(f"{STATUS_ICONS['success']} Connected to collection: {COLLECTION_NAME} ({existing_count} existing chunks)\n")

        existing_ids = set()
        if resume and not flush and existing_count > 0:
            print(f"{STATUS_ICONS['progress']} Loading existing chunk IDs...")
            existing_ids = get_existing_ids(collection)
            print(f"{STATUS_ICONS['success']} Found {len(existing_ids)} existing chunks to skip\n")

    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to connect to ChromaDB: {e}")
        print(f"Make sure ChromaDB is running: docker-compose up -d")
        return

    classifier = ContentClassifier()

    pdf_paths = collect_pdfs(pdf_dir)

    if not pdf_paths:
        print(f"{STATUS_ICONS['warning']} No PDFs found in {pdf_dir}")
        print(f"Add your PDFs to {pdf_dir}/ and run again")
        return

    print(f"{STATUS_ICONS['folder']} Found {len(pdf_paths)} PDF(s) in {pdf_dir}\n")

    total_docs = 0
    total_public = 0
    total_internal = 0
    total_confidential = 0
    skipped_count = 0

    for pdf_path in pdf_paths:
        chunks, pub, inter, conf, skipped = ingest_pdf(
            pdf_path, classifier, collection, pdf_dir, existing_ids
        )
        total_docs += chunks
        total_public += pub
        total_internal += inter
        total_confidential += conf
        skipped_count += skipped

    print(f"\n{STATUS_ICONS['complete']} Ingestion Complete!")
    print(f"\n{STATUS_ICONS['info']} Summary:")
    print(f"   New chunks: {total_docs}")
    if skipped_count > 0:
        print(f"   Skipped (already existed): {skipped_count}")
    print(f"   🟢 PUBLIC: {total_public} ({total_public/total_docs*100:.1f}%)" if total_docs > 0 else "   🟢 PUBLIC: 0")
    print(f"   🟡 INTERNAL: {total_internal} ({total_internal/total_docs*100:.1f}%)" if total_docs > 0 else "   🟡 INTERNAL: 0")
    print(f"   🔒 CONFIDENTIAL: {total_confidential} ({total_confidential/total_docs*100:.1f}%)" if total_docs > 0 else "   🔒 CONFIDENTIAL: 0")

    print()
    classifier.print_stats()

    print(f"\n{STATUS_ICONS['success']} Ready to query! Run: python EVALUATION/interactive_query.py")


from theme.constants import SENSITIVITY_ICONS


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest PDFs with privacy classification")
    parser.add_argument(
        "--dir",
        type=str,
        default="EVALUATION/test_data",
        help="Directory containing PDFs (default: EVALUATION/test_data)"
    )
    parser.add_argument(
        "--flush",
        action="store_true",
        help="Delete existing collection before ingesting (fresh start)"
    )

    args = parser.parse_args()

    main(pdf_dir=args.dir, flush=args.flush)
