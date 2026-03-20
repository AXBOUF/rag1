import os
import requests
from pypdf import PdfReader
from chromadb import HttpClient

# -------- CONFIGURATION --------
PDF_DIR           = "./test1"               # 👈 point to your folder of PDFs
OLLAMA_MODEL      = "mxbai-embed-large:latest"
OLLAMA_BASE       = "http://www.munalbaraili.com"
CHROMA_HOST       = "localhost"
CHROMA_PORT       = 8000
CHROMA_COLLECTION = "_vectors"
HEADERS           = {"x-api-key": "mysecretkey"}
# -------------------------------
chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection    = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION)


def collect_pdfs(root_dir: str) -> list[str]:
    """Walk the directory and return all PDF file paths."""
    pdf_paths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(dirpath, filename))
    return sorted(pdf_paths)


def ingest_pdf(pdf_path: str):
    reader   = PdfReader(pdf_path)
    filename = os.path.basename(pdf_path)
    folder   = os.path.relpath(os.path.dirname(pdf_path), PDF_DIR) or "."

    ids        = []
    embeddings = []
    metadatas  = []
    documents  = []

    print(f"\n📄 Ingesting: {pdf_path}  ({len(reader.pages)} pages)")

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text or not text.strip():
            continue

        chunk_id  = f"{folder}__{filename}__page_{i}"
        prompt    = text.strip()[:500]
        response  = requests.post(f"{OLLAMA_BASE}/api/embeddings", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt
        }, headers=HEADERS)
        embedding = response.json()["embedding"]

        ids.append(chunk_id)
        embeddings.append(embedding)
        metadatas.append({
            "filename": filename,
            "folder":   folder,
            "path":     pdf_path,
            "page":     i,
        })
        documents.append(text.strip()[:1000])

        print(f"  ✅ Page {i} embedded  [{folder} / {filename}]")

    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        print(f"  💾 Stored {len(ids)} chunks from {filename}")
    else:
        print(f"  ⚠️  No extractable text found in {filename}")


# --- Run ---
if __name__ == "__main__":
    pdf_files = collect_pdfs(PDF_DIR)

    if not pdf_files:
        print(f"❌ No PDFs found in '{PDF_DIR}'")
    else:
        print(f"📁 Found {len(pdf_files)} PDF(s) in '{PDF_DIR}'")
        for pdf_path in pdf_files:
            ingest_pdf(pdf_path)
        print(f"\n🎉 Done! All PDFs ingested into collection: '{CHROMA_COLLECTION}'")