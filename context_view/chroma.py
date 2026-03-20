import chromadb

# --- SETUP ---
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = client.get_collection("pdf_vectors")

# --- COLLECTION INFO ---
print(f"📦 Collection: pdf_vectors")
print(f"📄 Total documents: {collection.count()}")
print("-" * 60)

# --- FETCH ALL DATA ---
data = collection.get(include=["documents", "metadatas", "embeddings"])

ids        = data["ids"]
documents  = data["documents"]
metadatas  = data["metadatas"]
embeddings = data["embeddings"]

# --- PREVIEW EACH CHUNK ---
for i, (doc_id, doc, meta, emb) in enumerate(zip(ids, documents, metadatas, embeddings)):
    print(f"\n🔹 Chunk #{i+1}")
    print(f"   ID       : {doc_id}")
    print(f"   Metadata : {meta}")
    print(f"   Embedding: [{emb[0]:.4f}, {emb[1]:.4f}, ... ] (dim={len(emb)})")
    print(f"   Text     : {doc[:200]}{'...' if len(doc) > 200 else ''}")
    print("-" * 60)
