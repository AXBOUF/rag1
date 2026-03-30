"""
View and filter chunks in ChromaDB by sensitivity level.
Usage:
    python view_chunks.py                    # Show summary
    python view_chunks.py --level public     # Show PUBLIC chunks
    python view_chunks.py --level internal   # Show INTERNAL chunks  
    python view_chunks.py --level confidential  # Show CONFIDENTIAL chunks
    python view_chunks.py --all              # Show all chunks
    python view_chunks.py --limit 10         # Limit results
    python view_chunks.py --search "keyword" # Search in content
    python view_chunks.py --id "chunk_id"    # Get specific chunk by ID
    python view_chunks.py --file "filename"  # Filter by filename
"""

import argparse
from chromadb import HttpClient

# Config
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
COLLECTION_NAME = "privacy_aware_vectors"


def get_collection():
    """Connect to ChromaDB collection."""
    client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return client.get_collection(name=COLLECTION_NAME)


def get_chunks_by_level(collection, level: str = None, limit: int = None):
    """
    Get chunks filtered by sensitivity level.
    
    Args:
        collection: ChromaDB collection
        level: Sensitivity level (public/internal/confidential) or None for all
        limit: Max number of results
    """
    if level:
        # Filter by level
        where_filter = {"sensitivity_level": level.lower()}
        results = collection.get(
            where=where_filter,
            include=["metadatas", "documents"],
            limit=limit
        )
    else:
        results = collection.get(
            include=["metadatas", "documents"],
            limit=limit
        )
    
    return results


def search_chunks(collection, keyword: str, level: str = None, limit: int = 10):
    """Search chunks containing keyword."""
    # Get all chunks (with optional level filter)
    if level:
        where_filter = {"sensitivity_level": level.lower()}
        results = collection.get(
            where=where_filter,
            include=["metadatas", "documents"]
        )
    else:
        results = collection.get(include=["metadatas", "documents"])
    
    # Filter by keyword
    matches = []
    keyword_lower = keyword.lower()
    
    for i, doc in enumerate(results['documents']):
        if doc and keyword_lower in doc.lower():
            matches.append({
                'id': results['ids'][i],
                'metadata': results['metadatas'][i],
                'document': doc
            })
            if len(matches) >= limit:
                break
    
    return matches


def get_chunk_by_id(collection, chunk_id: str):
    """Get specific chunk by ID."""
    results = collection.get(
        ids=[chunk_id],
        include=["metadatas", "documents"]
    )
    return results


def get_chunks_by_filename(collection, filename: str, level: str = None):
    """Get chunks from a specific file."""
    if level:
        where_filter = {
            "$and": [
                {"filename": filename},
                {"sensitivity_level": level.lower()}
            ]
        }
    else:
        where_filter = {"filename": filename}
    
    results = collection.get(
        where=where_filter,
        include=["metadatas", "documents"]
    )
    return results


def display_full_chunk(chunk_id, metadata, document):
    """Display full chunk content for prompt crafting."""
    level = metadata.get('sensitivity_level', 'unknown').upper()
    filename = metadata.get('filename', 'unknown')
    page = metadata.get('page', '?')
    
    colors = {
        'PUBLIC': '\033[92m',
        'INTERNAL': '\033[93m',
        'CONFIDENTIAL': '\033[91m',
    }
    reset = '\033[0m'
    color = colors.get(level, '')
    
    print("\n" + "=" * 70)
    print(f"CHUNK DETAILS")
    print("=" * 70)
    print(f"\nSensitivity: {color}{level}{reset}")
    print(f"File: {filename}")
    print(f"Page: {page}")
    print(f"ID: {chunk_id}")
    print("\n" + "-" * 70)
    print("FULL CONTENT:")
    print("-" * 70)
    print(document)
    print("\n" + "-" * 70)
    print("SUGGESTED PROMPTS:")
    print("-" * 70)
    
    # Extract key terms for prompt suggestions
    words = document.split()[:20]
    key_terms = [w for w in words if len(w) > 5][:3]
    
    print(f"1. What is the {key_terms[0] if key_terms else 'topic'} mentioned in the documents?")
    print(f"2. Tell me about {filename.replace('.pdf', '')}")
    print(f"3. What does the document say about {' '.join(key_terms[:2]) if len(key_terms) >= 2 else 'this topic'}?")
    print("=" * 70 + "\n")


def display_chunks(results, show_content: bool = True):
    """Display chunks in readable format."""
    if not results['ids']:
        print("No chunks found.")
        return
    
    print(f"\nFound {len(results['ids'])} chunks\n")
    print("=" * 70)
    
    for i, (chunk_id, meta, doc) in enumerate(zip(
        results['ids'], 
        results['metadatas'], 
        results['documents']
    )):
        level = meta.get('sensitivity_level', 'unknown').upper()
        filename = meta.get('filename', 'unknown')
        page = meta.get('page', '?')
        
        # Color codes for terminal
        colors = {
            'PUBLIC': '\033[92m',      # Green
            'INTERNAL': '\033[93m',    # Yellow
            'CONFIDENTIAL': '\033[91m', # Red
        }
        reset = '\033[0m'
        color = colors.get(level, '')
        
        print(f"\n[{i+1}] {color}{level}{reset}")
        print(f"    File: {filename} | Page: {page}")
        print(f"    ID: {chunk_id}")
        
        if show_content and doc:
            preview = doc[:200].replace('\n', ' ')
            print(f"    Content: {preview}...")
        
        print("-" * 70)


def show_summary(collection):
    """Show summary statistics."""
    results = collection.get(include=["metadatas"])
    
    # Count by level
    counts = {"public": 0, "internal": 0, "confidential": 0, "unknown": 0}
    files_by_level = {"public": set(), "internal": set(), "confidential": set()}
    
    for meta in results['metadatas']:
        level = meta.get('sensitivity_level', 'unknown').lower()
        if level in counts:
            counts[level] += 1
        else:
            counts['unknown'] += 1
        
        if level in files_by_level:
            files_by_level[level].add(meta.get('filename', 'unknown'))
    
    total = len(results['ids'])
    
    print("\n" + "=" * 50)
    print("CHROMADB COLLECTION SUMMARY")
    print("=" * 50)
    print(f"\nCollection: {COLLECTION_NAME}")
    print(f"Total Chunks: {total}\n")
    
    print("-" * 50)
    print("CHUNKS BY SENSITIVITY LEVEL")
    print("-" * 50)
    
    print(f"\n\033[92mPUBLIC\033[0m:       {counts['public']:>5} chunks ({counts['public']/total*100:.1f}%)")
    print(f"   Files: {len(files_by_level['public'])}")
    for f in list(files_by_level['public'])[:3]:
        print(f"   - {f}")
    if len(files_by_level['public']) > 3:
        print(f"   ... and {len(files_by_level['public'])-3} more")
    
    print(f"\n\033[93mINTERNAL\033[0m:     {counts['internal']:>5} chunks ({counts['internal']/total*100:.1f}%)")
    print(f"   Files: {len(files_by_level['internal'])}")
    for f in list(files_by_level['internal'])[:3]:
        print(f"   - {f}")
    if len(files_by_level['internal']) > 3:
        print(f"   ... and {len(files_by_level['internal'])-3} more")
    
    print(f"\n\033[91mCONFIDENTIAL\033[0m: {counts['confidential']:>5} chunks ({counts['confidential']/total*100:.1f}%)")
    print(f"   Files: {len(files_by_level['confidential'])}")
    for f in list(files_by_level['confidential'])[:3]:
        print(f"   - {f}")
    if len(files_by_level['confidential']) > 3:
        print(f"   ... and {len(files_by_level['confidential'])-3} more")
    
    if counts['unknown'] > 0:
        print(f"\nUNKNOWN:      {counts['unknown']:>5} chunks")
    
    print("\n" + "=" * 50)
    print("ROLE ACCESS")
    print("=" * 50)
    print(f"\nEmployee: Can access {counts['public']} chunks (PUBLIC only)")
    print(f"Manager:  Can access {counts['public'] + counts['internal']} chunks (PUBLIC + INTERNAL)")
    print(f"Admin:    Can access {total} chunks (ALL)")
    print()


def main():
    parser = argparse.ArgumentParser(description="View ChromaDB chunks by sensitivity level")
    parser.add_argument("--level", "-l", choices=["public", "internal", "confidential"],
                        help="Filter by sensitivity level")
    parser.add_argument("--limit", "-n", type=int, default=10,
                        help="Limit number of results (default: 10)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Show all chunks (no limit)")
    parser.add_argument("--no-content", action="store_true",
                        help="Hide chunk content, show metadata only")
    parser.add_argument("--summary", "-s", action="store_true",
                        help="Show summary statistics only")
    parser.add_argument("--search", "-q", type=str,
                        help="Search for keyword in chunk content")
    parser.add_argument("--id", type=str,
                        help="Get specific chunk by ID (full content)")
    parser.add_argument("--file", "-f", type=str,
                        help="Filter chunks by filename")
    parser.add_argument("--full", action="store_true",
                        help="Show full content (not truncated)")
    
    args = parser.parse_args()
    
    try:
        collection = get_collection()
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        print("Make sure ChromaDB is running: docker-compose up -d")
        return
    
    # Get chunk by ID
    if args.id:
        results = get_chunk_by_id(collection, args.id)
        if results['ids']:
            display_full_chunk(
                results['ids'][0],
                results['metadatas'][0],
                results['documents'][0]
            )
        else:
            print(f"Chunk not found: {args.id}")
        return
    
    # Search by keyword
    if args.search:
        limit = None if args.all else args.limit
        matches = search_chunks(collection, args.search, args.level, limit or 10)
        
        print(f"\nSearch results for '{args.search}'")
        if args.level:
            print(f"Filtered by: {args.level.upper()}")
        print(f"Found: {len(matches)} matches\n")
        
        for i, match in enumerate(matches):
            level = match['metadata'].get('sensitivity_level', 'unknown').upper()
            filename = match['metadata'].get('filename', 'unknown')
            page = match['metadata'].get('page', '?')
            
            colors = {'PUBLIC': '\033[92m', 'INTERNAL': '\033[93m', 'CONFIDENTIAL': '\033[91m'}
            reset = '\033[0m'
            color = colors.get(level, '')
            
            print(f"[{i+1}] {color}{level}{reset} | {filename} p.{page}")
            print(f"    ID: {match['id']}")
            
            # Highlight keyword in preview
            doc = match['document']
            keyword_lower = args.search.lower()
            idx = doc.lower().find(keyword_lower)
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(doc), idx + len(args.search) + 100)
                snippet = doc[start:end]
                print(f"    ...{snippet}...")
            print("-" * 60)
        
        if matches:
            print(f"\nTo see full content: python view_chunks.py --id \"{matches[0]['id']}\"")
        return
    
    # Filter by filename
    if args.file:
        results = get_chunks_by_filename(collection, args.file, args.level)
        if results['ids']:
            print(f"\nChunks from: {args.file}")
            print(f"Total: {len(results['ids'])}\n")
            
            for i, (chunk_id, meta, doc) in enumerate(zip(
                results['ids'], results['metadatas'], results['documents']
            )):
                level = meta.get('sensitivity_level', 'unknown').upper()
                page = meta.get('page', '?')
                colors = {'PUBLIC': '\033[92m', 'INTERNAL': '\033[93m', 'CONFIDENTIAL': '\033[91m'}
                reset = '\033[0m'
                color = colors.get(level, '')
                
                print(f"[{i+1}] Page {page} | {color}{level}{reset}")
                print(f"    ID: {chunk_id}")
                if args.full:
                    print(f"    Content:\n{doc}\n")
                else:
                    print(f"    Preview: {doc[:150]}...")
                print("-" * 60)
        else:
            print(f"No chunks found for file: {args.file}")
        return
    
    # Show summary (default)
    if args.summary or (not args.level and not args.all):
        show_summary(collection)
        return
    
    limit = None if args.all else args.limit
    results = get_chunks_by_level(collection, args.level, limit)
    display_chunks(results, show_content=not args.no_content)


if __name__ == "__main__":
    main()
