"""
Streamlit Web UI for Privacy-Aware RAG System.
Clean minimal dark theme with role-based access control demo.
"""

import streamlit as st
import sys
import tempfile
import os
import requests
from pathlib import Path
from chromadb import HttpClient
from pypdf import PdfReader

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from query_with_privacy import query_with_role
from utils.audit_log import AuditLogger
from utils.classifier import ContentClassifier
from utils.metadata import create_chunk_metadata
from theme.styles import CUSTOM_CSS, get_sensitivity_badge_html, get_role_badge_html
from theme.constants import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    STATUS_ICONS,
    ROLE_ACCESS,
    ROLE_ICONS,
    SENSITIVITY_ICONS,
)
from config import OLLAMA_BASE, EMBED_MODEL, API_KEY, CHUNK_SIZE

HEADERS = {"x-api-key": API_KEY}

# Page config
st.set_page_config(
    page_title="Privacy-Aware RAG",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Additional CSS to ensure sidebar toggle is always accessible
st.markdown("""
<style>
    /* Force sidebar toggle to be visible */
    button[kind="header"] {
        visibility: visible !important;
        display: block !important;
    }
    
    /* Sidebar collapse button styling */
    [data-testid="baseButton-header"] {
        color: #f5f5f7 !important;
        background-color: #1c1c1e !important;
        border-radius: 8px !important;
    }
    
    [data-testid="baseButton-header"]:hover {
        background-color: #2c2c2e !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "role" not in st.session_state:
    st.session_state.role = "employee"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audit_logger" not in st.session_state:
    st.session_state.audit_logger = AuditLogger()


# Initialize ChromaDB connection
@st.cache_resource
def get_chromadb():
    """Get or create ChromaDB connection."""
    try:
        client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection(name=COLLECTION_NAME)
        return collection
    except Exception as e:
        st.error(f"Failed to connect to ChromaDB: {e}")
        st.info("Make sure you've run: `python version3/ingest_with_privacy.py`")
        return None


def get_embedding(text: str) -> list[float]:
    """Get embedding vector from Ollama."""
    text_for_embedding = text[:CHUNK_SIZE] if len(text) > CHUNK_SIZE else text
    response = requests.post(
        f"{OLLAMA_BASE}/embed",
        json={"model": EMBED_MODEL, "text": text_for_embedding},
        headers=HEADERS,
        timeout=30
    )
    if response.status_code != 200:
        raise Exception(f"Embedding API returned status {response.status_code}")
    return response.json()["embedding"]


def process_uploaded_files(uploaded_files, collection):
    """Process uploaded PDF files with classification (Admin only)."""
    if collection is None:
        st.error("ChromaDB not connected!")
        return
    
    classifier = ContentClassifier()
    total_chunks = 0
    level_counts = {"public": 0, "internal": 0, "confidential": 0}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for file_idx, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"📄 Processing: {uploaded_file.name}")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        
        try:
            reader = PdfReader(tmp_path)
            filename = uploaded_file.name
            
            ids, embeddings, metadatas, documents = [], [], [], []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                
                text = text.strip()
                
                # Classify chunk
                status_text.text(f"🔍 Classifying: {filename} (page {page_num + 1})")
                sensitivity_level = classifier.classify_chunk(text)
                level_counts[sensitivity_level] += 1
                total_chunks += 1
                
                # Generate ID and embedding
                chunk_id = f"upload__{filename}__page_{page_num}"
                embedding = get_embedding(text)
                
                # Create metadata
                metadata = create_chunk_metadata(
                    filename=filename,
                    folder="uploads",
                    path=f"uploads/{filename}",
                    page=page_num,
                    chunk_index=total_chunks - 1,
                    sensitivity_level=sensitivity_level,
                    document_source="web_upload",
                    classified_by="llm",
                )
                
                ids.append(chunk_id)
                embeddings.append(embedding)
                metadatas.append(metadata)
                documents.append(text[:CHUNK_SIZE])
            
            # Add to ChromaDB
            if ids:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents,
                )
        
        finally:
            os.unlink(tmp_path)  # Clean up temp file
        
        progress_bar.progress((file_idx + 1) / len(uploaded_files))
    
    progress_bar.empty()
    status_text.empty()
    
    # Show results
    st.success(f"✅ Processed {len(uploaded_files)} file(s), {total_chunks} chunks")
    st.markdown(f"""
    **Classification Results:**
    - 🟢 PUBLIC: {level_counts['public']}
    - 🟡 INTERNAL: {level_counts['internal']}
    - 🔒 CONFIDENTIAL: {level_counts['confidential']}
    """)


# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Role selector
    st.subheader(f"{STATUS_ICONS['user']} User Role")
    
    role_options = {
        f"{ROLE_ICONS['employee']} Employee": "employee",
        f"{ROLE_ICONS['manager']} Manager": "manager",
        f"{ROLE_ICONS['admin']} Admin": "admin",
    }
    
    selected_role = st.selectbox(
        "Select your role:",
        options=list(role_options.keys()),
        index=list(role_options.values()).index(st.session_state.role),
    )
    
    new_role = role_options[selected_role]
    
    # Clear chat if role changed
    if new_role != st.session_state.role:
        st.session_state.role = new_role
        st.session_state.messages = []
        st.rerun()
    
    # Show access levels
    st.markdown("**Access Levels:**")
    allowed_levels = ROLE_ACCESS[st.session_state.role]
    for level in ["public", "internal", "confidential"]:
        if level in allowed_levels:
            icon = "🟢" if level == "public" else ("🟡" if level == "internal" else "🔒")
            st.markdown(f"{icon} {level.upper()} ✅")
        else:
            icon = "🟢" if level == "public" else ("🟡" if level == "internal" else "🔒")
            st.markdown(f"{icon} {level.upper()} ❌")
    
    st.divider()
    
    # Admin-only file upload
    if st.session_state.role == "admin":
        st.subheader(f"{STATUS_ICONS['upload']} Upload Documents")
        st.caption("👑 Admin only")
        
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload PDFs to ingest with automatic classification"
        )
        
        if uploaded_files and st.button(f"{STATUS_ICONS['brain']} Process & Classify", use_container_width=True):
            process_uploaded_files(uploaded_files, get_chromadb())
    
    st.divider()
    
    # Clear chat button
    if st.button(f"{STATUS_ICONS['complete']} Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Audit log toggle
    show_audit = st.checkbox("Show Audit Log", value=False)
    
    if show_audit:
        st.subheader(f"{STATUS_ICONS['info']} Recent Queries")
        recent_logs = st.session_state.audit_logger.get_recent_logs(limit=5)
        
        if recent_logs:
            for log in recent_logs:
                role_icon = ROLE_ICONS.get(log.get("user_role", "employee"), "👤")
                st.caption(f"{role_icon} {log.get('user_role', 'unknown').upper()}")
                st.text(log.get('query', '')[:50] + "...")
                st.divider()
        else:
            st.caption("No queries yet")


# Main content
st.title(f"{STATUS_ICONS['lock']} Privacy-Aware RAG System")

# Show current role
role_html = get_role_badge_html(st.session_state.role)
st.markdown(f"Current Role: {role_html}", unsafe_allow_html=True)

st.markdown("---")

# Get ChromaDB collection
collection = get_chromadb()

if collection is None:
    st.error("ChromaDB not available. Please check configuration.")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show retrieved documents if available
        if message["role"] == "assistant" and "metadatas" in message:
            with st.expander(f"{STATUS_ICONS['document']} View Retrieved Context ({len(message['metadatas'])} chunks)"):
                for i, meta in enumerate(message["metadatas"], 1):
                    level = meta.get("sensitivity_level", "unknown")
                    badge = get_sensitivity_badge_html(level)
                    st.markdown(f"**Chunk {i}:** {badge} {meta.get('filename', 'unknown')} (page {meta.get('page', '?')})", unsafe_allow_html=True)
                
                if message.get("filtered_count", 0) > 0:
                    st.warning(f"{STATUS_ICONS['lock']} {message['filtered_count']} chunks were filtered by role restrictions")

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner(f"{STATUS_ICONS['progress']} Searching and generating response..."):
            try:
                result = query_with_role(
                    query=prompt,
                    role=st.session_state.role,
                    collection=collection,
                    audit_logger=st.session_state.audit_logger,
                )
                
                response = result['response']
                st.markdown(response)
                
                # Show filtered count if any
                if result.get('filtered_count', 0) > 0:
                    st.info(f"{STATUS_ICONS['lock']} {result['filtered_count']} documents were filtered due to role restrictions")
                
                # Add assistant message with metadata
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "metadatas": result.get('metadatas', []),
                    "filtered_count": result.get('filtered_count', 0),
                })
                
            except Exception as e:
                error_msg = f"{STATUS_ICONS['error']} Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

# Footer
st.markdown("---")
st.caption(f"{STATUS_ICONS['info']} Queries are logged for audit purposes")
