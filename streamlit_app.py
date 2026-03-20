import streamlit as st
import chromadb
import requests
from pathlib import Path
from pypdf import PdfReader
import tempfile
import os

HEADERS = {"x-api-key": "mysecretkey"}

# --- CONFIG ---
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
OLLAMA_BASE = "http://www.munalbaraili.com"
EMBED_MODEL = "mxbai-embed-large:latest"
LLM_MODEL = "qwen2.5:7b"

# --- SETUP ---
st.set_page_config(page_title="Multi-Version RAG Chat", layout="wide")

@st.cache_resource
def get_chroma_client():
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

def get_collection(version):
    """Get or create collection for a version"""
    client = get_chroma_client()
    collection_name = "pdf_vectors"
    return client.get_or_create_collection(name=collection_name)

def embed_text(text):
    """Embed text using Ollama"""
    try:
        response = requests.post(f"{OLLAMA_BASE}/embed", json={
            "model": EMBED_MODEL,
            "text": text[:500]
        }, headers=HEADERS)
        return response.json()["embedding"]
    except Exception as e:
        st.error(f"Embedding error: {e}")
        return None

def ask_llm(context, question):
    """Ask LLM with context"""
    try:
        prompt = f"""Answer the question based on the context below.

Context:
{context}

Question: {question}
Answer:"""
        response = requests.post(f"{OLLAMA_BASE}/llm", json={
            "model": LLM_MODEL,
            "text": prompt,
            "stream": False
        }, headers=HEADERS)
        return response.json()["response"]
    except Exception as e:
        return f"Error: {e}"

def process_pdf(pdf_path, collection, version):
    """Extract text from PDF and embed"""
    reader = PdfReader(pdf_path)
    progress = st.progress(0)
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            chunk_id = f"{Path(pdf_path).stem}_page_{i}"
            embedding = embed_text(text)
            
            if embedding:
                collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    metadatas={"source": Path(pdf_path).name, "page": i},
                    documents=[text[:1000]]
                )
        
        progress.progress((i + 1) / len(reader.pages))
    
    st.success(f"✅ Embedded {len(reader.pages)} pages from {Path(pdf_path).name}")

# --- SIDEBAR ---
st.sidebar.title("🔧 Settings")
version = st.sidebar.radio("Select Version", ["streamversion1", "streamversion2"])
collection = get_collection(version)

st.sidebar.divider()
st.sidebar.subheader("📤 Upload & Embed")
uploaded_file = st.sidebar.file_uploader("Upload PDF", type="pdf", key=f"{version}_upload")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    
    if st.sidebar.button("🚀 Embed PDF", key=f"{version}_embed"):
        with st.sidebar.status("Processing..."):
            process_pdf(tmp_path, collection, version)
        os.unlink(tmp_path)

# --- MAIN ---
st.title(f"📚 RAG Chat - {version}")

# Initialize chat history
if f"{version}_messages" not in st.session_state:
    st.session_state[f"{version}_messages"] = []

messages = st.session_state[f"{version}_messages"]

# Display chat history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            st.caption(f"📄 Sources: {msg['sources']}")

# Chat input
if question := st.chat_input("Ask a question..."):
    # Add user message
    messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    
    # Generate response
    with st.chat_message("assistant"):
        # Search for context
        query_embedding = embed_text(question)
        
        if query_embedding:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
            
            if results["documents"] and results["documents"][0]:
                contexts = results["documents"][0]
                context_text = "\n\n".join(contexts)
                sources = results["metadatas"][0] if results["metadatas"] else []
                
                # Get answer
                answer = ask_llm(context_text, question)
                st.markdown(answer)
                
                # Show sources
                source_names = [f"{s.get('source', 'Unknown')} (p.{s.get('page', '?')})" for s in sources]
                st.caption(f"📄 Sources: {', '.join(source_names)}")
                
                messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": source_names
                })
            else:
                msg = "No relevant documents found in this version's collection."
                st.markdown(msg)
                messages.append({"role": "assistant", "content": msg})
        else:
            msg = "Failed to embed query."
            st.markdown(msg)
            messages.append({"role": "assistant", "content": msg})
