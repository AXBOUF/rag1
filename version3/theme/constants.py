"""
Constants for version3 privacy-aware RAG.
Icons, messages, role configurations.
"""

# Status Icons
STATUS_ICONS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "progress": "⏳",
    "complete": "🎉",
    "upload": "📤",
    "download": "📥",
    "document": "📄",
    "folder": "📁",
    "search": "🔍",
    "lock": "🔒",
    "unlock": "🔓",
    "user": "👤",
    "brain": "🧠",
}

# Sensitivity Icons
SENSITIVITY_ICONS = {
    "public": "🟢",
    "internal": "🟡",
    "confidential": "🔒",
}

# Role Icons
ROLE_ICONS = {
    "employee": "👤",
    "manager": "👔",
    "admin": "👑",
}

# Sensitivity Levels
SENSITIVITY_LEVELS = ["public", "internal", "confidential"]

# Role Access Mapping
ROLE_ACCESS = {
    "employee": ["public"],
    "manager": ["public", "internal"],
    "admin": ["public", "internal", "confidential"],
}

# Status Messages
MESSAGES = {
    # Classification
    "classification_start": "⏳ Analyzing content sensitivity...",
    "classification_complete": "✅ Classified {count} chunks",
    "classification_error": "❌ Classification failed: {error}",
    
    # Upload
    "upload_start": "📤 Processing document...",
    "upload_success": "✅ Document uploaded successfully",
    "upload_error": "❌ Upload failed: {error}",
    
    # Retrieval
    "retrieval_start": "🔍 Searching for relevant content...",
    "retrieval_complete": "✅ Found {count} relevant chunks",
    "retrieval_filtered": "🔒 {count} chunks filtered by role",
    "retrieval_error": "❌ Retrieval failed: {error}",
    
    # Query
    "query_processing": "🧠 Generating response...",
    "query_complete": "✅ Response generated",
    "query_error": "❌ Query failed: {error}",
    
    # Audit
    "audit_logged": "📋 Query logged to audit trail",
    
    # Access Control
    "access_denied": "🔒 Access denied: {reason}",
    "access_granted": "✅ Access granted",
}

# LLM Prompts
CLASSIFICATION_PROMPT = """Analyze the following text and classify its sensitivity level.

Classification Rules:
- PUBLIC: General information accessible to everyone. No sensitive data, no internal processes, no confidential details.
- INTERNAL: Company-specific information for internal use only. Business processes, internal policies, non-sensitive employee info.
- CONFIDENTIAL: Highly sensitive information requiring strict access control. PII (personal identifiable information), financial data, trade secrets, executive decisions, salary information, legal matters.

Text to classify:
{text}

Respond with ONLY one word: PUBLIC, INTERNAL, or CONFIDENTIAL"""

QUERY_SYSTEM_PROMPT = """You are a helpful AI assistant with access to a document database.

CRITICAL INSTRUCTIONS:
1. ONLY answer based on the provided context below
2. DO NOT generate information outside the retrieved documents
3. If the context doesn't contain the answer, clearly state: "I don't have information about that in the available documents."
4. DO NOT make assumptions or infer information not explicitly stated in the context
5. Cite the source document when possible

Context:
{context}

Answer the user's question based ONLY on the above context."""

# Chunk size for document processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ChromaDB collection name
COLLECTION_NAME = "privacy_aware_vectors"

# API configuration (override with .env)
OLLAMA_BASE = "http://www.munalbaraili.com"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
API_KEY = "mysecretkey"
DEFAULT_MODEL = "qwen2.5:7b"
EMBED_MODEL = "mxbai-embed-large:latest"
