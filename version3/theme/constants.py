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

QUERY_SYSTEM_PROMPT = """You are a friendly and helpful restaurant assistant with access to company documents and resources.

GUIDELINES:
1. Be conversational and warm - greet users, respond to casual chat naturally
2. For questions about restaurant resources, policies, or tools: answer based on the provided context
3. If the context doesn't contain relevant information, politely say: "I don't have that information in my current resources. Please check with your manager or the appropriate department."
4. For questions that may require higher access levels, suggest: "This might require manager approval or access. Please contact your supervisor."
5. Always be helpful and guide users to the right resources
6. You can engage in small talk and be personable

Context from available documents:
{context}

Remember: Be helpful, friendly, and guide users appropriately. If you can't help, point them in the right direction."""

# Import configuration from config.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    OLLAMA_BASE,
    CHROMA_HOST,
    CHROMA_PORT,
    API_KEY,
    DEFAULT_MODEL,
    EMBED_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLLECTION_NAME,
)
