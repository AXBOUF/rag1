import os
import requests
from pypdf import PdfReader
from chromadb import HttpClient

# -------- CONFIGURATION --------
PDF_PATH = "version1/tripplanner.pdf"
OLLAMA_MODEL = "mxbai-embed-large:latest"
OLLAMA_BASE = "http://www.munalbaraili.com"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
CHROMA_COLLECTION = "transport_vectors"
HEADERS = {"x-api-key": "mysecretkey"}
# -------------------------------

chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION)

reader = PdfReader(PDF_PATH)
texts = []

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        chunk_id = f"{os.path.basename(PDF_PATH)}_page_{i}"
        texts.append((chunk_id, text.strip()))

print(f"[INFO] Loaded {len(texts)} pages from {PDF_PATH}")

ids, embeddings, metadatas, documents = [], [], [], []

for doc_id, text in texts:
    prompt = text[:500]
    response = requests.post(f"{OLLAMA_BASE}/embed", json={
        "model": OLLAMA_MODEL,
        "text": prompt
    }, headers=HEADERS)

    # Debug
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    embedding = response.json()["embedding"]

    ids.append(doc_id)
    embeddings.append(embedding)
    metadatas.append({"source": PDF_PATH, "page": doc_id})
    documents.append(text[:1000])

print(f"[INFO] Generated {len(embeddings)} embeddings")

collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
print(f"[SUCCESS] Stored embeddings in Chroma collection: {CHROMA_COLLECTION}")