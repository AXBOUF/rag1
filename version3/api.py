"""
FastAPI backend for version3 RAG system.
Wraps existing Python modules and exposes them as REST endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import tempfile
import os
from pathlib import Path
from typing import Optional, List
from chromadb import HttpClient
from pypdf import PdfReader

import sys
sys.path.insert(0, str(Path(__file__).parent))

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

from auth import authenticate, register_user, list_users
from query_with_privacy import query_with_role
from utils.audit_log import AuditLogger
from utils.classifier import ContentClassifier
from utils.metadata import create_chunk_metadata
from config import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    CHUNK_SIZE,
    OLLAMA_BASE,
    EMBED_MODEL,
    API_KEY,
)
from theme.constants import ROLE_ACCESS

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Initialize FastAPI app
app = FastAPI(title="RAG System API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Dev URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving PDFs
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Request/Response models
class LoginRequest(BaseModel):
    username: str  # Accepts email or username
    password: str

class RegisterRequest(BaseModel):
    username: str  # Expects email format
    password: str
    role: str = "employee"

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: Optional[str] = None

class MessageResponse(BaseModel):
    status: str
    message: str

# Helper functions
def create_jwt_token(user_id: int, username: str, role: str) -> str:
    """Create JWT token."""
    payload = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(authorization: str = Header(None)) -> dict:
    """Verify JWT token and return payload."""
    from jose import JWTError, ExpiredSignatureError

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization[7:]  # Remove "Bearer " prefix
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_chromadb_collection():
    """Get ChromaDB collection."""
    try:
        client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        return client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ChromaDB connection failed: {e}")

def get_admin_or_fail(payload: dict):
    """Check if user is admin."""
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = authenticate(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(user["id"], user["username"], user["role"])
    return TokenResponse(
        access_token=token,
        user=user,
    )

@app.post("/auth/register", response_model=MessageResponse)
async def register(request: RegisterRequest):
    """Register a new user."""
    success, message = register_user(request.username, request.password, request.role)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return MessageResponse(status="success", message=message)

@app.get("/auth/me", response_model=dict)
async def get_me(payload: dict = Depends(verify_token)):
    """Get current user info from token."""
    return {
        "id": payload.get("id"),
        "username": payload.get("sub"),
        "role": payload.get("role"),
    }

# Query endpoint
@app.post("/query")
async def query(
    request: QueryRequest,
    payload: dict = Depends(verify_token),
):
    """Query RAG system with role-based access control."""
    role = payload.get("role")
    user_id = payload.get("sub")

    collection = get_chromadb_collection()
    audit_logger = AuditLogger()

    try:
        result = query_with_role(
            query=request.query,
            role=role,
            collection=collection,
            top_k=request.top_k,
            audit_logger=audit_logger,
            user_id=user_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/admin/users", response_model=List[UserResponse])
async def admin_get_users(payload: dict = Depends(verify_token)):
    """Get all users (admin only)."""
    get_admin_or_fail(payload)
    users = list_users()
    return [UserResponse(**u) for u in users]

@app.get("/admin/stats")
async def admin_get_stats(payload: dict = Depends(verify_token)):
    """Get collection statistics (admin only)."""
    get_admin_or_fail(payload)
    collection = get_chromadb_collection()
    try:
        count = collection.count()
        return {"total_documents": count, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/logs")
async def admin_get_logs(payload: dict = Depends(verify_token), limit: int = 20):
    """Get audit logs (admin only)."""
    get_admin_or_fail(payload)
    audit_logger = AuditLogger()
    logs = audit_logger.get_recent_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}

@app.post("/admin/upload")
async def admin_upload(
    files: List[UploadFile] = File(...),
    payload: dict = Depends(verify_token),
):
    """Upload and process PDF files (admin only)."""
    get_admin_or_fail(payload)

    collection = get_chromadb_collection()
    if collection is None:
        raise HTTPException(status_code=503, detail="ChromaDB not available")

    classifier = ContentClassifier()
    audit_logger = AuditLogger()
    total_chunks = 0
    level_counts = {"public": 0, "internal": 0, "confidential": 0}

    import requests

    def get_embedding(text: str) -> list[float]:
        """Get embedding from API."""
        response = requests.post(
            f"{OLLAMA_BASE}/embed",
            json={"model": EMBED_MODEL, "text": text[:CHUNK_SIZE]},
            headers={"x-api-key": API_KEY},
            timeout=30
        )
        if response.status_code != 200:
            raise Exception(f"Embedding failed: {response.status_code}")
        return response.json()["embedding"]

    try:
        for file in files:
            if not file.filename.endswith(".pdf"):
                continue

            # Save PDF to uploads directory
            file_bytes = await file.read()
            filename = file.filename or "document.pdf"
            file_path = UPLOADS_DIR / filename

            # Save to disk
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            # Create temp file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                reader = PdfReader(tmp_path)
                ids, embeddings, metadatas, documents = [], [], [], []

                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if not text or not text.strip():
                        continue

                    text = text.strip()
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
                        document_source="api_upload",
                        classified_by="llm",
                    )

                    ids.append(chunk_id)
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    documents.append(text[:CHUNK_SIZE])

                if ids:
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        documents=documents
                    )
            finally:
                os.unlink(tmp_path)

        return {
            "status": "success",
            "message": f"Processed {len(files)} files, {total_chunks} chunks",
            "chunks_by_level": level_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents(payload: dict = Depends(verify_token)):
    """List all available PDFs from test_data."""
    documents = []

    def find_pdfs(directory):
        """Recursively find all PDFs."""
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() == ".pdf":
                relative_path = item.relative_to(TEST_DATA_DIR)
                documents.append({
                    "filename": str(relative_path),  # Path relative to test_data
                    "name": item.name,
                    "size": item.stat().st_size,
                    "created_at": item.stat().st_ctime,
                })
            elif item.is_dir():
                find_pdfs(item)

    if TEST_DATA_DIR.exists():
        find_pdfs(TEST_DATA_DIR)

    return {"documents": sorted(documents, key=lambda x: x["filename"])}

@app.get("/documents/file/{file_path:path}")
async def get_document(file_path: str, payload: dict = Depends(verify_token)):
    """Serve a PDF from test_data. file_path can include subdirectories."""
    full_path = TEST_DATA_DIR / file_path

    # Security check: prevent directory traversal
    try:
        full_path = full_path.resolve()
        TEST_DATA_DIR_RESOLVED = TEST_DATA_DIR.resolve()
        if not str(full_path).startswith(str(TEST_DATA_DIR_RESOLVED)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Document not found: {file_path}")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    if full_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    return FileResponse(full_path, media_type="application/pdf", filename=full_path.name)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
