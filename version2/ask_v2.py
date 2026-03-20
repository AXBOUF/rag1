import chromadb
import requests

HEADERS = {"x-api-key": "mysecretkey"}

# --- SETUP ---
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
OLLAMA_BASE = "http://www.munalbaraili.com"  # Single source of truth

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = client.get_collection("pdf_vectors")

# --- STEP 1: Get user question ---
query = input("Ask a question: ")

# --- STEP 2: Embed query using Ollama ---
def embed_text(text):
    response = requests.post(f"{OLLAMA_BASE}/api/embeddings", json={
        "model": "mxbai-embed-large:latest",
        "prompt": text
    }, headers=HEADERS)
    return response.json()["embedding"]

query_embedding = embed_text(query)

# --- STEP 3: Search Chroma for relevant chunks ---
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

contexts = results["documents"][0]
context_text = "\n\n".join(contexts)

# --- STEP 4: Ask LLM (via Ollama) with context ---
def ask_llm(context, question):
    prompt = f"""Answer the question based on the context below.

Context:
{context}

Question: {question}
Answer:"""

    response = requests.post(f"{OLLAMA_BASE}/api/generate", json={
        "model": "qwen2.5:7b",
        "prompt": prompt,
        "stream": False
    }, headers=HEADERS)
    return response.json()["response"]

answer = ask_llm(context_text, query)
print("\n🧠 Answer:")
print(answer)