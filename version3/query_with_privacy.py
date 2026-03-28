"""
Role-based query engine with privacy filtering.
Queries ChromaDB with role-based access control and audit logging.
"""

import sys
import requests
import time
from pathlib import Path
from chromadb import HttpClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.metadata import get_chromadb_where_filter, format_metadata_display
from utils.audit_log import AuditLogger
from theme.constants import (
    OLLAMA_BASE,
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    API_KEY,
    DEFAULT_MODEL,
    EMBED_MODEL,
    QUERY_SYSTEM_PROMPT,
    STATUS_ICONS,
    ROLE_ACCESS,
    ROLE_ICONS,
)

HEADERS = {"x-api-key": API_KEY}


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for query."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE}/embed",
            json={
                "model": EMBED_MODEL,
                "text": text[:500]  # Truncate for embedding
            },
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}")
        
        return response.json()["embedding"]
    
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Embedding failed: {e}")
        raise


def query_with_role(
    query: str,
    role: str,
    collection,
    top_k: int = 3,
    audit_logger: AuditLogger = None,
    user_id: str = "anonymous",
) -> dict:
    """
    Query the RAG system with role-based access control.
    
    Args:
        query: User's query
        role: User role (employee/manager/admin)
        collection: ChromaDB collection
        top_k: Number of results to retrieve
        audit_logger: Optional audit logger
        user_id: Username for audit logging
        
    Returns:
        Dictionary with response, retrieved docs, and metadata
    """
    start_time = time.time()
    
    # Validate role
    role_lower = role.lower()
    if role_lower not in ROLE_ACCESS:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLE_ACCESS.keys())}")
    
    try:
        # Get query embedding
        print(f"{STATUS_ICONS['progress']} Embedding query...")
        query_embedding = get_embedding(query)
        
        # Get role-based WHERE filter
        where_filter = get_chromadb_where_filter(role_lower)
        allowed_levels = ROLE_ACCESS[role_lower]
        
        print(f"{STATUS_ICONS['search']} Searching with role: {ROLE_ICONS[role_lower]} {role.upper()}")
        print(f"   Allowed levels: {', '.join([l.upper() for l in allowed_levels])}")
        
        # Query ChromaDB with role filter
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Extract results
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        distances = results['distances'][0] if results['distances'] else []
        
        print(f"{STATUS_ICONS['success']} Retrieved {len(documents)} chunks")
        
        # Check if results were filtered
        # Query without filter to see total available
        results_unfiltered = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents"]
        )
        total_available = len(results_unfiltered['documents'][0]) if results_unfiltered['documents'] else 0
        filtered_count = total_available - len(documents)
        
        if filtered_count > 0:
            print(f"{STATUS_ICONS['lock']} {filtered_count} chunks filtered by role restrictions")
        
        # Display retrieved chunks
        if documents:
            print(f"\n{STATUS_ICONS['info']} Retrieved Context:")
            for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
                print(f"   {i}. {format_metadata_display(meta)}")
                print(f"      Preview: {doc[:100]}...")
        else:
            print(f"{STATUS_ICONS['warning']} No relevant documents found with your access level")
            return {
                "response": "I don't have access to documents that can answer this question with your current role.",
                "documents": [],
                "metadatas": [],
                "filtered_count": filtered_count,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "no_results"
            }
        
        # Build context for LLM
        context = "\n\n---\n\n".join([
            f"Document: {meta['filename']} (page {meta['page']}) [Sensitivity: {meta.get('sensitivity_level', 'unknown').upper()}]\n{doc}"
            for doc, meta in zip(documents, metadatas)
        ])
        
        # Determine required role for restricted actions
        required_role = "Manager or Admin"
        if role_lower == "manager":
            required_role = "Admin"
        
        # Generate response with LLM
        print(f"\n{STATUS_ICONS['brain']} Generating response...")
        
        system_prompt = QUERY_SYSTEM_PROMPT.format(
            context=context,
            role_upper=role.upper(),
            required_role=required_role
        )
        
        response = requests.post(
            f"{OLLAMA_BASE}/llm",
            json={
                "model": DEFAULT_MODEL,
                "prompt": f"{system_prompt}\n\nUser Question: {query}\n\nAnswer:",
            },
            headers=HEADERS,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"LLM API returned status {response.status_code}")
        
        answer = response.json()["response"]
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log to audit
        if audit_logger:
            audit_logger.log_query(
                user_role=role_lower,
                query=query,
                retrieved_docs=metadatas,
                filtered_count=filtered_count,
                response=answer,
                execution_time_ms=execution_time_ms,
                status="success",
                user_id=user_id,
            )
        
        return {
            "response": answer,
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
            "filtered_count": filtered_count,
            "execution_time_ms": execution_time_ms,
            "status": "success"
        }
    
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        print(f"{STATUS_ICONS['error']} Query failed: {e}")
        
        if audit_logger:
            audit_logger.log_query(
                user_role=role_lower,
                query=query,
                retrieved_docs=[],
                filtered_count=0,
                response=f"Error: {e}",
                execution_time_ms=execution_time_ms,
                status="error",
                user_id=user_id,
            )
        
        raise


if __name__ == "__main__":
    # Test the query engine
    print(f"{STATUS_ICONS['brain']} Testing Role-Based Query Engine\n")
    
    # Connect to ChromaDB
    try:
        chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        print(f"{STATUS_ICONS['success']} Connected to ChromaDB\n")
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to connect: {e}")
        print("Make sure you've run ingest_with_privacy.py first")
        sys.exit(1)
    
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    # Test queries
    test_queries = [
        ("What information is in the documents?", "employee"),
        ("What information is in the documents?", "admin"),
    ]
    
    for query, role in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Role: {role.upper()}")
        print('='*60)
        
        try:
            result = query_with_role(query, role, collection, audit_logger=audit_logger)
            print(f"\n{STATUS_ICONS['success']} Response:")
            print(result['response'])
            print(f"\nExecution time: {result['execution_time_ms']}ms")
        except Exception as e:
            print(f"{STATUS_ICONS['error']} Failed: {e}")
