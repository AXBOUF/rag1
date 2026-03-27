"""
Side-by-side role comparison demo.
Shows how different roles see different content for the same query.
"""

import sys
from pathlib import Path
from chromadb import HttpClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from query_with_privacy import query_with_role
from theme.constants import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    STATUS_ICONS,
    ROLE_ICONS,
)


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_role_comparison(query: str, collection):
    """
    Compare query results across all roles.
    
    Args:
        query: Query to test
        collection: ChromaDB collection
    """
    roles = ["employee", "manager", "admin"]
    results = {}
    
    print(f"\n{STATUS_ICONS['search']} Query: {query}")
    print_separator()
    
    # Execute query for each role
    for role in roles:
        print(f"\n{ROLE_ICONS[role]} Testing as {role.upper()}...")
        try:
            result = query_with_role(
                query=query,
                role=role,
                collection=collection,
                top_k=5,
            )
            results[role] = result
        except Exception as e:
            print(f"{STATUS_ICONS['error']} Failed: {e}")
            results[role] = None
    
    # Display comparison
    print(f"\n\n{STATUS_ICONS['complete']} COMPARISON RESULTS")
    print_separator("=", 80)
    
    for role in roles:
        print(f"\n{ROLE_ICONS[role]} {role.upper()}")
        print_separator("-", 80)
        
        result = results.get(role)
        if not result:
            print(f"{STATUS_ICONS['error']} No results")
            continue
        
        # Show retrieved chunks
        metadatas = result.get('metadatas', [])
        print(f"\n{STATUS_ICONS['document']} Retrieved {len(metadatas)} chunks:")
        
        if metadatas:
            for i, meta in enumerate(metadatas, 1):
                level = meta.get('sensitivity_level', 'unknown')
                icon = "🟢" if level == "public" else ("🟡" if level == "internal" else "🔒")
                print(f"  {i}. {icon} {level.upper()} - {meta.get('filename', 'unknown')} (page {meta.get('page', '?')})")
        else:
            print(f"  {STATUS_ICONS['warning']} No documents accessible")
        
        # Show filtered count
        filtered = result.get('filtered_count', 0)
        if filtered > 0:
            print(f"\n{STATUS_ICONS['lock']} {filtered} chunks filtered by role")
        
        # Show response preview
        response = result.get('response', '')
        print(f"\n{STATUS_ICONS['brain']} Response Preview:")
        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")
    
    print_separator("=", 80)
    
    # Summary comparison
    print(f"\n{STATUS_ICONS['info']} ACCESS SUMMARY:")
    for role in roles:
        result = results.get(role)
        if result:
            retrieved = len(result.get('metadatas', []))
            filtered = result.get('filtered_count', 0)
            total = retrieved + filtered
            print(f"  {ROLE_ICONS[role]} {role.upper()}: {retrieved}/{total} chunks accessible")


def main():
    """Run demo comparison."""
    print(f"\n{STATUS_ICONS['brain']} Privacy-Aware RAG - Role Comparison Demo")
    print_separator()
    
    # Connect to ChromaDB
    print(f"\n{STATUS_ICONS['progress']} Connecting to ChromaDB...")
    try:
        chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        print(f"{STATUS_ICONS['success']} Connected")
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to connect: {e}")
        print("\nMake sure:")
        print("  1. ChromaDB is running: docker-compose up -d")
        print("  2. Documents are ingested: python version3/ingest_with_privacy.py")
        return
    
    # Test queries
    test_queries = [
        "What information is available in the documents?",
        "Tell me about confidential information",
        "What are the internal processes?",
    ]
    
    print(f"\n{STATUS_ICONS['info']} Running {len(test_queries)} test queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#'*80}")
        print(f"# TEST {i}/{len(test_queries)}")
        print(f"{'#'*80}")
        print_role_comparison(query, collection)
        
        if i < len(test_queries):
            input(f"\n{STATUS_ICONS['info']} Press Enter to continue to next test...")
    
    print(f"\n\n{STATUS_ICONS['complete']} Demo Complete!")
    print("\nKey Observations:")
    print("  1. Employee can only access PUBLIC documents")
    print("  2. Manager can access PUBLIC + INTERNAL documents")
    print("  3. Admin can access all document levels")
    print("  4. Same query returns different results based on role")
    print("  5. Filtering happens at retrieval level (privacy-preserving)")


if __name__ == "__main__":
    main()
