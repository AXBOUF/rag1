"""
Streamlit Web UI for Privacy-Aware RAG System.
Apple-inspired minimal dark theme with authentication.
"""

import streamlit as st
import sys
import tempfile
import os
import requests
from pathlib import Path
from chromadb import HttpClient
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent))

from query_with_privacy import query_with_role
from utils.audit_log import AuditLogger
from utils.classifier import ContentClassifier
from utils.metadata import create_chunk_metadata
from theme.styles import CUSTOM_CSS
from theme.constants import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    ROLE_ACCESS,
)
from config import OLLAMA_BASE, EMBED_MODEL, API_KEY, CHUNK_SIZE
from auth import authenticate, register_user, list_users

HEADERS = {"x-api-key": API_KEY}

# Page config
st.set_page_config(
    page_title="RAG System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audit_logger" not in st.session_state:
    st.session_state.audit_logger = AuditLogger()


def show_login():
    """Display login page."""
    st.markdown("## Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                st.error("Enter username and password")
    
    st.markdown("---")
    st.caption("New user?")
    if st.button("Register", use_container_width=True):
        st.session_state.page = "register"
        st.rerun()


def show_register():
    """Display registration page."""
    st.markdown("## Register")
    
    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose username")
        password = st.text_input("Password", type="password", placeholder="Choose password")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
        
        role = st.selectbox(
            "Role",
            options=["Employee", "Manager", "Admin"],
            index=0
        )
        
        submit = st.form_submit_button("Register", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("All fields required")
            elif password != confirm:
                st.error("Passwords do not match")
            else:
                success, msg = register_user(username, password, role.lower())
                if success:
                    st.success("Registered. Please login.")
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)
    
    st.markdown("---")
    if st.button("Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()


@st.cache_resource
def get_chromadb():
    try:
        client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        return client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        st.error(f"ChromaDB connection failed: {e}")
        return None


def get_embedding(text: str) -> list[float]:
    text_for_embedding = text[:CHUNK_SIZE] if len(text) > CHUNK_SIZE else text
    response = requests.post(
        f"{OLLAMA_BASE}/embed",
        json={"model": EMBED_MODEL, "text": text_for_embedding},
        headers=HEADERS,
        timeout=30
    )
    if response.status_code != 200:
        raise Exception(f"Embedding failed: {response.status_code}")
    return response.json()["embedding"]


def process_uploaded_files(uploaded_files, collection):
    if collection is None:
        st.error("ChromaDB not connected")
        return
    
    classifier = ContentClassifier()
    total_chunks = 0
    level_counts = {"public": 0, "internal": 0, "confidential": 0}
    
    progress = st.progress(0)
    status = st.empty()
    
    for idx, uploaded_file in enumerate(uploaded_files):
        status.text(f"Processing {uploaded_file.name}...")
        
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
                status.text(f"Classifying {filename} p.{page_num + 1}")
                
                sensitivity_level = classifier.classify_chunk(text)
                level_counts[sensitivity_level] += 1
                total_chunks += 1
                
                chunk_id = f"upload__{filename}__page_{page_num}"
                embedding = get_embedding(text)
                
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
            
            if ids:
                collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
        finally:
            os.unlink(tmp_path)
        
        progress.progress((idx + 1) / len(uploaded_files))
    
    progress.empty()
    status.empty()
    
    st.success(f"Processed {len(uploaded_files)} files, {total_chunks} chunks")
    st.caption(f"Public: {level_counts['public']} / Internal: {level_counts['internal']} / Confidential: {level_counts['confidential']}")


def show_main():
    """Display main application."""
    user = st.session_state.user
    role = user["role"]
    username = user["username"]
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### {username}")
        st.caption(f"{role.upper()}")
        
        # Access levels
        allowed_levels = ROLE_ACCESS[role]
        access_text = " / ".join([l.upper() for l in allowed_levels])
        st.caption(f"Access: {access_text}")
        
        st.divider()
        
        # Admin upload
        if role == "admin":
            st.markdown("#### Upload")
            
            uploaded_files = st.file_uploader(
                "PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            if uploaded_files and st.button("Process", use_container_width=True):
                process_uploaded_files(uploaded_files, get_chromadb())
            
            st.divider()
            
            # User management
            with st.expander("Users"):
                users = list_users()
                for u in users:
                    st.caption(f"{u['username']} - {u['role']}")
            
            st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.messages = []
                st.session_state.page = "login"
                st.rerun()
    
    # Main content
    collection = get_chromadb()
    
    if collection is None:
        st.error("Database not available")
        st.stop()
    
    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if message["role"] == "assistant" and "metadatas" in message:
                meta_count = len(message["metadatas"])
                filtered = message.get("filtered_count", 0)
                
                with st.expander(f"Context ({meta_count} chunks)"):
                    for i, meta in enumerate(message["metadatas"], 1):
                        level = meta.get("sensitivity_level", "unknown").upper()
                        fname = meta.get("filename", "unknown")
                        page = meta.get("page", "?")
                        st.caption(f"{i}. [{level}] {fname} p.{page}")
                    
                    if filtered > 0:
                        st.caption(f"{filtered} chunks filtered")
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    result = query_with_role(
                        query=prompt,
                        role=role,
                        collection=collection,
                        audit_logger=st.session_state.audit_logger,
                        user_id=username,
                    )
                    
                    response = result['response']
                    st.markdown(response)
                    
                    filtered = result.get('filtered_count', 0)
                    if filtered > 0:
                        st.caption(f"{filtered} documents filtered")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "metadatas": result.get('metadatas', []),
                        "filtered_count": filtered,
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Error: {str(e)}",
                    })


# Router
if not st.session_state.authenticated:
    if st.session_state.page == "register":
        show_register()
    else:
        show_login()
else:
    show_main()
