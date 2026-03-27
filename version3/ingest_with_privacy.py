"""
Privacy-aware PDF ingestion with LLM-based content classification.
Processes PDFs, classifies each chunk, and stores with enhanced metadata in ChromaDB.
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
    """Walk the directory and return all PDF file paths."""
    pdf_paths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(dirpath, filename))
    return sorted(pdf_paths)


def get_embedding(text: str) -> list[float]:
    """Get embedding vector from Ollama."""
    # Truncate text for embedding model
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
) -> tuple[int, int, int, int]:
    """
    Ingest a single PDF with privacy classification.
    
    Returns:
        Tuple of (total_chunks, public_count, internal_count, confidential_count)
    """
    try:
        reader = PdfReader(pdf_path)
        filename = os.path.basename(pdf_path)
        folder = os.path.relpath(os.path.dirname(pdf_path), base_dir) or "."
        
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        # Statistics
        total_chunks = 0
        level_counts = {"public": 0, "internal": 0, "confidential": 0}
        
        print(f"\n{STATUS_ICONS['document']} Ingesting: {pdf_path}")
        print(f"   Pages: {len(reader.pages)}")
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text or not text.strip():
                continue
            
            text = text.strip()
            
            # Classify the chunk using LLM
            print(f"   {STATUS_ICONS['progress']} Classifying page {page_num + 1}...", end=" ")
            sensitivity_level = classifier.classify_chunk(text)
            print(f"{SENSITIVITY_ICONS.get(sensitivity_level, '❓')} {sensitivity_level.upper()}")
            
            # Update statistics
            level_counts[sensitivity_level] += 1
            total_chunks += 1
            
            # Create chunk ID
            chunk_id = f"{folder}__{filename}__page_{page_num}"
            
            # Get embedding
            embedding = get_embedding(text)
            
            # Create enhanced metadata
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
            
            # Store document preview (first 1000 chars)
            document_text = text[:CHUNK_SIZE] if len(text) > CHUNK_SIZE else text
            
            ids.append(chunk_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            documents.append(document_text)
        
        # Batch insert to ChromaDB
        if ids:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
            print(f"   {STATUS_ICONS['success']} Stored {len(ids)} chunks")
            print(f"   🟢 PUBLIC: {level_counts['public']} | 🟡 INTERNAL: {level_counts['internal']} | 🔒 CONFIDENTIAL: {level_counts['confidential']}")
        else:
            print(f"   {STATUS_ICONS['warning']} No text content found")
        
        return (
            total_chunks,
            level_counts["public"],
            level_counts["internal"],
            level_counts["confidential"]
        )
    
    except Exception as e:
        print(f"   {STATUS_ICONS['error']} Failed: {e}")
        return (0, 0, 0, 0)


def main(pdf_dir: str = "version3/test_data"):
    """
    Main ingestion function.
    
    Args:
        pdf_dir: Directory containing PDFs to ingest
    """
    print(f"{STATUS_ICONS['brain']} Privacy-Aware RAG Ingestion")
    print(f"{STATUS_ICONS['info']} Using LLM-based classification\n")
    
    # Initialize ChromaDB
    print(f"{STATUS_ICONS['progress']} Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        print(f"{STATUS_ICONS['success']} Connected to collection: {COLLECTION_NAME}\n")
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to connect to ChromaDB: {e}")
        print(f"Make sure ChromaDB is running: docker-compose up -d")
        return
    
    # Initialize classifier
    classifier = ContentClassifier()
    
    # Collect PDFs
    pdf_paths = collect_pdfs(pdf_dir)
    
    if not pdf_paths:
        print(f"{STATUS_ICONS['warning']} No PDFs found in {pdf_dir}")
        print(f"Add your PDFs to {pdf_dir}/ and run again")
        return
    
    print(f"{STATUS_ICONS['folder']} Found {len(pdf_paths)} PDF(s) in {pdf_dir}\n")
    
    # Process each PDF
    total_docs = 0
    total_public = 0
    total_internal = 0
    total_confidential = 0
    
    for pdf_path in pdf_paths:
        chunks, pub, inter, conf = ingest_pdf(pdf_path, classifier, collection, pdf_dir)
        total_docs += chunks
        total_public += pub
        total_internal += inter
        total_confidential += conf
    
    # Print summary
    print(f"\n{STATUS_ICONS['complete']} Ingestion Complete!")
    print(f"\n{STATUS_ICONS['info']} Summary:")
    print(f"   Total chunks: {total_docs}")
    print(f"   🟢 PUBLIC: {total_public} ({total_public/total_docs*100:.1f}%)" if total_docs > 0 else "   🟢 PUBLIC: 0")
    print(f"   🟡 INTERNAL: {total_internal} ({total_internal/total_docs*100:.1f}%)" if total_docs > 0 else "   🟡 INTERNAL: 0")
    print(f"   🔒 CONFIDENTIAL: {total_confidential} ({total_confidential/total_docs*100:.1f}%)" if total_docs > 0 else "   🔒 CONFIDENTIAL: 0")
    
    # Print classifier stats
    print()
    classifier.print_stats()
    
    print(f"\n{STATUS_ICONS['success']} Ready to query! Run: python version3/interactive_query.py")


# Import sensitivity icons
from theme.constants import SENSITIVITY_ICONS


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest PDFs with privacy classification")
    parser.add_argument(
        "--dir",
        type=str,
        default="version3/test_data",
        help="Directory containing PDFs (default: version3/test_data)"
    )
    
    args = parser.parse_args()
    
    main(pdf_dir=args.dir)
