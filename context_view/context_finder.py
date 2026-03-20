import requests
from chromadb import HttpClient

HEADERS = {"x-api-key": "mysecretkey"}

# -------- CONFIGURATION --------
OLLAMA_HOST    = "http://www.munalbaraili.com"
CHROMA_HOST    = "localhost"
CHROMA_PORT    = 8000
CHROMA_COLLECTION = "pdf_vectors"
EMBED_MODEL    = "mxbai-embed-large:latest"
TOP_K          = 5  # how many chunks to retrieve
# -------------------------------

chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection    = chroma_client.get_collection(name=CHROMA_COLLECTION)


def embed_query(text: str) -> list[float]:
    response = requests.post(f"{OLLAMA_HOST}/api/embeddings", json={
        "model": EMBED_MODEL,
        "prompt": text
    }, headers=HEADERS)
    return response.json()["embedding"]


def retrieve_context(query: str, top_k: int = TOP_K) -> list[dict]:
    embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "page":     meta.get("page", "unknown"),
            "distance": round(dist, 4)
        })

    return chunks


def show_context(chunks: list[dict]) -> None:
    print("\n" + "=" * 60)
    print(f"  📚 Retrieved {len(chunks)} context chunk(s)")
    print("=" * 60)

    for i, chunk in enumerate(chunks, 1):
        print(f"\n🔹 Chunk #{i}")
        print(f"   Source   : {chunk['source']}")
        print(f"   Page     : {chunk['page']}")
        print(f"   Distance : {chunk['distance']}  {'✅ close' if chunk['distance'] < 0.5 else '⚠️ distant'}")
        print(f"   Text     :\n")
        # Word-wrap the text at 70 chars for readability
        words = chunk["text"].split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > 70:
                print(f"      {line}")
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            print(f"      {line}")
        print("\n" + "-" * 60)


# --- Usage ---
if __name__ == "__main__":
    query = input("🔍 Enter your query: ")
    chunks = retrieve_context(query)
    show_context(chunks)

    # Also return raw context string for use in LLM prompts
    context_text = "\n\n".join(c["text"] for c in chunks)
    print("\n✅ context_text ready to pass to LLM")