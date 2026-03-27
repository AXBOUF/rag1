"""
ChromaDB collection management utility.
Flush, view stats, or delete collections.
"""

import sys
from pathlib import Path
from chromadb import HttpClient

sys.path.insert(0, str(Path(__file__).parent))

from config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME
from theme.constants import STATUS_ICONS


def list_collections():
    """List all collections in ChromaDB."""
    try:
        client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collections = client.list_collections()
        
        print(f"\n{STATUS_ICONS['info']} ChromaDB Collections:")
        if collections:
            for col in collections:
                count = col.count()
                print(f"  • {col.name} ({count} documents)")
        else:
            print(f"  {STATUS_ICONS['warning']} No collections found")
        
        return collections
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to connect: {e}")
        return []


def get_collection_stats(collection_name: str = COLLECTION_NAME):
    """Get statistics for a collection."""
    try:
        client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection(name=collection_name)
        
        count = collection.count()
        
        print(f"\n{STATUS_ICONS['info']} Collection: {collection_name}")
        print(f"  Total documents: {count}")
        
        if count > 0:
            # Get sample to check metadata
            results = collection.get(limit=min(10, count), include=["metadatas"])
            
            # Count by sensitivity level
            from collections import Counter
            levels = [meta.get('sensitivity_level', 'unknown') for meta in results['metadatas']]
            level_counts = Counter(levels)
            
            print(f"\n  Sensitivity levels (sample):")
            for level, cnt in level_counts.items():
                icon = "🟢" if level == "public" else ("🟡" if level == "internal" else ("🔒" if level == "confidential" else "❓"))
                print(f"    {icon} {level.upper()}: {cnt}")
        
        return collection
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Collection not found: {e}")
        return None


def flush_collection(collection_name: str = COLLECTION_NAME, confirm: bool = True):
    """Delete a collection (flush all data)."""
    try:
        client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Check if collection exists
        try:
            collection = client.get_collection(name=collection_name)
            count = collection.count()
        except Exception:
            print(f"{STATUS_ICONS['warning']} Collection '{collection_name}' does not exist")
            return False
        
        # Confirm deletion
        if confirm:
            print(f"\n{STATUS_ICONS['warning']} WARNING: This will delete collection '{collection_name}' with {count} documents!")
            response = input("Type 'yes' to confirm: ").strip().lower()
            if response != 'yes':
                print(f"{STATUS_ICONS['info']} Cancelled")
                return False
        
        # Delete collection
        client.delete_collection(name=collection_name)
        print(f"{STATUS_ICONS['success']} Flushed collection: {collection_name}")
        return True
        
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to flush: {e}")
        return False


def main():
    """Main CLI for collection management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Collection Manager")
    parser.add_argument(
        "action",
        choices=["list", "stats", "flush"],
        help="Action to perform"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=COLLECTION_NAME,
        help=f"Collection name (default: {COLLECTION_NAME})"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt for flush"
    )
    
    args = parser.parse_args()
    
    print(f"{STATUS_ICONS['brain']} ChromaDB Collection Manager")
    print(f"Connected to: {CHROMA_HOST}:{CHROMA_PORT}\n")
    
    if args.action == "list":
        list_collections()
    
    elif args.action == "stats":
        get_collection_stats(args.collection)
    
    elif args.action == "flush":
        flush_collection(args.collection, confirm=not args.yes)


if __name__ == "__main__":
    main()
