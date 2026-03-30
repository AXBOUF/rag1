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
    # Hide sidebar on login
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            .main .block-container { max-width: 100%; padding: 0; }
        </style>
    """, unsafe_allow_html=True)
    
    # Centered container
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<div style='height: 10vh'></div>", unsafe_allow_html=True)
        
        # Card header with logo
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="width: 64px; height: 64px; margin: 0 auto 1rem; 
                    background: linear-gradient(135deg, #0a84ff, #5856d6); 
                    border-radius: 16px; display: flex; align-items: center; 
                    justify-content: center; font-size: 28px;">
                    R
                </div>
                <h2 style="color: #f5f5f7; margin: 0; font-weight: 600;">RAG ANYTHING</h2>
                <p style="color: #86868b; font-size: 14px; margin-top: 8px;">Sign in to continue</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="collapsed")
            
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
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
        
        st.markdown("<hr style='border: none; border-top: 1px solid #38383a; margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #86868b; font-size: 13px;'>Don't have an account?</p>", unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True, type="secondary"):
            st.session_state.page = "register"
            st.rerun()


def show_register():
    """Display registration page."""
    # Hide sidebar on register
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            .main .block-container { max-width: 100%; padding: 0; }
        </style>
    """, unsafe_allow_html=True)
    
    # Centered container
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<div style='height: 8vh'></div>", unsafe_allow_html=True)
        
        # Card header
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="width: 64px; height: 64px; margin: 0 auto 1rem; 
                    background: linear-gradient(135deg, #30d158, #34c759); 
                    border-radius: 16px; display: flex; align-items: center; 
                    justify-content: center; font-size: 28px;">
                    +
                </div>
                <h2 style="color: #f5f5f7; margin: 0; font-weight: 600;">Create Account</h2>
                <p style="color: #86868b; font-size: 14px; margin-top: 8px;">Register to get started</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Choose username", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Choose password", label_visibility="collapsed")
            confirm = st.text_input("Confirm", type="password", placeholder="Confirm password", label_visibility="collapsed")
            
            role = st.selectbox(
                "Role",
                options=["Employee", "Manager", "Admin"],
                index=0
            )
            
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("All fields required")
                elif password != confirm:
                    st.error("Passwords do not match")
                else:
                    success, msg = register_user(username, password, role.lower())
                    if success:
                        st.success("Account created! Please sign in.")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)
        
        st.markdown("<hr style='border: none; border-top: 1px solid #38383a; margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #86868b; font-size: 13px;'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True, type="secondary"):
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
    """Display main application with tabbed navigation."""
    user = st.session_state.user
    role = user["role"]
    username = user["username"]
    
    # Initialize current tab
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "Chat"
    
    # Sidebar navigation
    with st.sidebar:
        # User info header
        st.markdown(f"""
            <div style="text-align: center; padding: 1rem 0;">
                <div style="width: 48px; height: 48px; margin: 0 auto 0.5rem; 
                    background: linear-gradient(135deg, #0a84ff, #5856d6); 
                    border-radius: 50%; display: flex; align-items: center; 
                    justify-content: center; font-size: 20px; color: white; font-weight: 600;">
                    {username[0].upper()}
                </div>
                <p style="margin: 0; color: #f5f5f7; font-weight: 500;">{username}</p>
                <p style="margin: 0; color: #86868b; font-size: 12px;">{role.upper()}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation menu
        st.markdown("#### Menu")
        
        nav_items = ["Chat", "Profile", "Settings"]
        if role == "admin":
            nav_items.append("Admin")
        
        for item in nav_items:
            is_active = st.session_state.current_tab == item
            btn_type = "primary" if is_active else "secondary"
            if st.button(item, use_container_width=True, type=btn_type, key=f"nav_{item}"):
                st.session_state.current_tab = item
                st.rerun()
        
        st.divider()
        
        # Logout at bottom
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.messages = []
            st.session_state.page = "login"
            st.rerun()
    
    # Main content based on selected tab
    if st.session_state.current_tab == "Chat":
        show_chat_tab(username, role)
    elif st.session_state.current_tab == "Profile":
        show_profile_tab(username, role)
    elif st.session_state.current_tab == "Settings":
        show_settings_tab()
    elif st.session_state.current_tab == "Admin":
        show_admin_tab()


def show_chat_tab(username, role):
    """Chat assistant tab."""
    st.markdown("### Assistant")
    st.caption(f"Access: {' / '.join([l.upper() for l in ROLE_ACCESS[role]])}")
    
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
                
                with st.expander(f"Sources ({meta_count})"):
                    for i, meta in enumerate(message["metadatas"], 1):
                        level = meta.get("sensitivity_level", "unknown").upper()
                        fname = meta.get("filename", "unknown")
                        page = meta.get("page", "?")
                        st.caption(f"{i}. [{level}] {fname} p.{page}")
                    
                    if filtered > 0:
                        st.caption(f"{filtered} filtered")
    
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
    
    # Clear chat button
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()


def show_profile_tab(username, role):
    """User profile tab (mock)."""
    st.markdown("### Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Profile picture placeholder
        st.markdown(f"""
            <div style="width: 120px; height: 120px; margin: 0 auto; 
                background: linear-gradient(135deg, #0a84ff, #5856d6); 
                border-radius: 50%; display: flex; align-items: center; 
                justify-content: center; font-size: 48px; color: white; font-weight: 600;">
                {username[0].upper()}
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.button("Change Photo", use_container_width=True, disabled=True)
    
    with col2:
        st.markdown("#### Account Information")
        
        # Mock form
        with st.form("profile_form"):
            st.text_input("Username", value=username, disabled=True)
            st.text_input("Email", value=f"{username}@company.com", disabled=True)
            st.text_input("Department", value="Operations", disabled=True)
            st.selectbox("Role", options=[role.title()], disabled=True)
            st.text_input("Phone", placeholder="+1 (555) 000-0000")
            
            st.form_submit_button("Save Changes", disabled=True)
    
    st.divider()
    
    st.markdown("#### Activity")
    st.caption("Recent activity will appear here")
    
    # Mock activity items
    activities = [
        {"action": "Logged in", "time": "Just now"},
        {"action": "Queried documents", "time": "2 minutes ago"},
        {"action": "Updated profile", "time": "1 hour ago"},
    ]
    
    for act in activities:
        st.markdown(f"""
            <div style="padding: 0.5rem 0; border-bottom: 1px solid #38383a;">
                <span style="color: #f5f5f7;">{act['action']}</span>
                <span style="color: #86868b; float: right; font-size: 12px;">{act['time']}</span>
            </div>
        """, unsafe_allow_html=True)


def show_settings_tab():
    """Settings tab (mock)."""
    st.markdown("### Settings")
    
    # Appearance
    st.markdown("#### Appearance")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Theme", options=["Dark", "Light", "System"], index=0, disabled=True)
    with col2:
        st.selectbox("Language", options=["English", "Spanish", "French"], index=0, disabled=True)
    
    st.divider()
    
    # Notifications
    st.markdown("#### Notifications")
    st.toggle("Email notifications", value=True, disabled=True)
    st.toggle("Push notifications", value=False, disabled=True)
    st.toggle("Weekly digest", value=True, disabled=True)
    
    st.divider()
    
    # Privacy
    st.markdown("#### Privacy & Security")
    st.toggle("Two-factor authentication", value=False, disabled=True)
    st.toggle("Show online status", value=True, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Change Password", use_container_width=True, disabled=True)
    with col2:
        st.button("Export Data", use_container_width=True, disabled=True)
    
    st.divider()
    
    # About
    st.markdown("#### About")
    st.caption("RAG Assistant v3.0")
    st.caption("Privacy-aware document retrieval system")


def show_admin_tab():
    """Admin panel tab."""
    st.markdown("### Admin Panel")
    
    # Sub-tabs for admin
    admin_tab = st.radio(
        "Section",
        options=["Documents", "Users", "Logs"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if admin_tab == "Documents":
        st.markdown("#### Upload Documents")
        
        uploaded_files = st.file_uploader(
            "PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded_files and st.button("Process & Classify", use_container_width=False):
            process_uploaded_files(uploaded_files, get_chromadb())
        
        st.divider()
        
        st.markdown("#### Collection Stats")
        try:
            collection = get_chromadb()
            if collection:
                count = collection.count()
                st.metric("Total Documents", count)
        except:
            st.caption("Unable to fetch stats")
    
    elif admin_tab == "Users":
        st.markdown("#### Registered Users")
        
        users = list_users()
        
        # Display as table
        if users:
            for u in users:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{u['username']}**")
                with col2:
                    role_color = {"admin": "#ff453a", "manager": "#ff9f0a", "employee": "#30d158"}
                    st.markdown(f"<span style='color: {role_color.get(u['role'], '#86868b')}'>{u['role'].upper()}</span>", unsafe_allow_html=True)
                with col3:
                    st.caption(u.get('created_at', 'N/A')[:10] if u.get('created_at') else 'N/A')
        else:
            st.caption("No users found")
    
    elif admin_tab == "Logs":
        st.markdown("#### Audit Logs")
        
        logs = st.session_state.audit_logger.get_recent_logs(limit=20)
        
        if logs:
            for log in logs:
                with st.expander(f"{log.get('user_id', 'unknown')} - {log.get('query', '')[:50]}..."):
                    st.caption(f"Time: {log.get('timestamp', 'N/A')}")
                    st.caption(f"Role: {log.get('user_role', 'N/A')}")
                    st.caption(f"Status: {log.get('status', 'N/A')}")
                    st.caption(f"Retrieved: {log.get('retrieved_count', 0)} | Filtered: {log.get('filtered_count', 0)}")
        else:
            st.caption("No logs available")


# Router
if not st.session_state.authenticated:
    if st.session_state.page == "register":
        show_register()
    else:
        show_login()
else:
    show_main()
