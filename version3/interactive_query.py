"""
Interactive CLI for querying the privacy-aware RAG system.
Allows role selection and conversational queries with audit logging.
"""

import sys
from pathlib import Path
from chromadb import HttpClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from query_with_privacy import query_with_role
from utils.audit_log import AuditLogger
from theme.constants import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    STATUS_ICONS,
    ROLE_ICONS,
    ROLE_ACCESS,
)


def print_welcome():
    """Print welcome message."""
    print(f"\n{STATUS_ICONS['brain']} Privacy-Aware RAG System")
    print("=" * 60)
    print("Query documents with role-based access control")
    print("=" * 60)


def select_role() -> str:
    """Prompt user to select their role."""
    print(f"\n{STATUS_ICONS['user']} Select your role:")
    print(f"  1. {ROLE_ICONS['employee']} Employee  (Access: 🟢 PUBLIC only)")
    print(f"  2. {ROLE_ICONS['manager']} Manager   (Access: 🟢 PUBLIC + 🟡 INTERNAL)")
    print(f"  3. {ROLE_ICONS['admin']} Admin     (Access: 🟢 PUBLIC + 🟡 INTERNAL + 🔒 CONFIDENTIAL)")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            return "employee"
        elif choice == "2":
            return "manager"
        elif choice == "3":
            return "admin"
        else:
            print(f"{STATUS_ICONS['warning']} Invalid choice. Please enter 1, 2, or 3.")


def print_role_info(role: str):
    """Print information about selected role."""
    allowed_levels = ROLE_ACCESS[role.lower()]
    icon = ROLE_ICONS[role.lower()]
    
    print(f"\n{STATUS_ICONS['success']} You are: {icon} {role.upper()}")
    print(f"   Access levels: {', '.join([l.upper() for l in allowed_levels])}")


def main():
    """Main interactive loop."""
    print_welcome()
    
    # Connect to ChromaDB
    print(f"\n{STATUS_ICONS['progress']} Connecting to ChromaDB...")
    try:
        chroma_client = HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        print(f"{STATUS_ICONS['success']} Connected to collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"{STATUS_ICONS['error']} Failed to connect to ChromaDB: {e}")
        print("\nMake sure:")
        print("  1. ChromaDB is running: docker-compose up -d")
        print("  2. You've ingested documents: python version3/ingest_with_privacy.py")
        return
    
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    # Select role
    role = select_role()
    print_role_info(role)
    
    # Query loop
    print(f"\n{STATUS_ICONS['info']} Ready for queries!")
    print("Type 'exit' or 'quit' to leave, 'role' to change role\n")
    
    while True:
        try:
            query = input(f"\n{STATUS_ICONS['search']} Your question: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print(f"\n{STATUS_ICONS['complete']} Goodbye!")
                break
            
            if query.lower() == 'role':
                role = select_role()
                print_role_info(role)
                continue
            
            # Execute query
            print()  # Blank line for readability
            result = query_with_role(
                query=query,
                role=role,
                collection=collection,
                audit_logger=audit_logger,
            )
            
            # Display response
            print(f"\n{STATUS_ICONS['brain']} Answer:")
            print("-" * 60)
            print(result['response'])
            print("-" * 60)
            
            # Show metadata
            if result.get('filtered_count', 0) > 0:
                print(f"\n{STATUS_ICONS['lock']} Note: {result['filtered_count']} restricted documents were filtered")
            
            print(f"\n{STATUS_ICONS['info']} Query time: {result['execution_time_ms']}ms")
        
        except KeyboardInterrupt:
            print(f"\n\n{STATUS_ICONS['complete']} Goodbye!")
            break
        
        except Exception as e:
            print(f"\n{STATUS_ICONS['error']} Error: {e}")
            print("Please try again or type 'exit' to quit")


if __name__ == "__main__":
    main()
