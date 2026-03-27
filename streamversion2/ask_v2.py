import chromadb
import requests

HEADERS = {"x-api-key": "mysecretkey"}

# --- SETUP ---
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
OLLAMA_BASE = "https://www.munalbaraili.com"

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = client.get_collection("pdf_vectors")

# --- STEP 1: Get user question ---
query = input("Ask a question: ")

# --- STEP 2: Embed query ---
def embed_text(text):
    response = requests.post(f"{OLLAMA_BASE}/embed", json={
        "model": "mxbai-embed-large:latest",
        "text": text
    }, headers=HEADERS)
    print(response.status_code)  # 👈 did you add this?
    print(response.json())       # 👈 and this?
    return response.json()["embedding"]

query_embedding = embed_text(query)

# --- STEP 3: Search Chroma ---
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

contexts = results["documents"][0]
context_text = "\n\n".join(contexts)

# --- STEP 4: Ask LLM ---
def ask_llm(context, question):
    prompt = f"""Answer the question based on the context below.

Context:
{context}

Question: {question}
Answer:"""

    response = requests.post(f"{OLLAMA_BASE}/llm", json={
        "model": "qwen2.5:7b",
        "prompt": prompt
    }, headers=HEADERS)
    return response.json()["response"]

answer = ask_llm(context_text, query)
print("\n🧠 Answer:")
print(answer)