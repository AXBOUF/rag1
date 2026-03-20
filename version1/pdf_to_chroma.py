import os
from pypdf import PdfReader
from ollama import Client
from chromadb import HttpClient

# -------- CONFIGURATION --------
PDF_PATH = "scholarship.pdf"  # 👈 Change this to your local PDF
OLLAMA_MODEL = "mxbai-embed-large:latest"
OLLAMA_HOST = "http://192.168.1.186:11434"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
CHROMA_COLLECTION = "pdf_vectors"
# -------------------------------

# Connect to Ollama
ollama_client = Client(host=OLLAMA_HOST)

# Connect to Chroma running in Docker
chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION)

# Load PDF and split into pages
reader = PdfReader(PDF_PATH)
texts = []

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        chunk_id = f"{os.path.basename(PDF_PATH)}_page_{i}"
        texts.append((chunk_id, text.strip()))

print(f"[INFO] Loaded {len(texts)} pages from {PDF_PATH}")

# Embed and store in Chroma
ids = []
embeddings = []
metadatas = []
documents = []

for doc_id, text in texts:
    # Truncate text if it's too long
    prompt = text[:500]
    response = ollama_client.embeddings(model=OLLAMA_MODEL, prompt=prompt)
    embedding = response["embedding"]

    ids.append(doc_id)
    embeddings.append(embedding)
    metadatas.append({"source": PDF_PATH, "page": doc_id})
    documents.append(text[:1000])  # Optional preview

print(f"[INFO] Generated {len(embeddings)} embeddings")

# Store in Chroma
collection.add(
    ids=ids,
    embeddings=embeddings,
    metadatas=metadatas,
    documents=documents
)

print(f"[SUCCESS] Stored embeddings in Chroma collection: {CHROMA_COLLECTION}")