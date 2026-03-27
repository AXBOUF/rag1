"""
Enhanced metadata schema for privacy-aware RAG.
Expands ChromaDB metadata with privacy and audit fields.
"""

from datetime import datetime
from typing import Optional
from theme.constants import SENSITIVITY_LEVELS

def create_chunk_metadata(
    # Original metadata
    filename: str,
    folder: str,
    path: str,
    page: int,
    chunk_index: int,
    
    # Privacy metadata
    sensitivity_level: str,
    
    # Additional context
    document_source: Optional[str] = None,
    classified_by: str = "llm",
    
    # Optional fields
    document_id: Optional[str] = None,
    total_chunks: Optional[int] = None,
) -> dict:
    """
    Create enhanced metadata for a document chunk.
    
    Args:
        filename: Name of the source file
        folder: Folder containing the file
        path: Full path to the file
        page: Page number in the PDF
        chunk_index: Index of this chunk in the document
        sensitivity_level: Classification (public/internal/confidential)
        document_source: Optional description of document type
        classified_by: Method used for classification (llm/manual/folder)
        document_id: Optional unique document identifier
        total_chunks: Optional total number of chunks in document
        
    Returns:
        Dictionary with enhanced metadata
    """
    # Validate sensitivity level
    if sensitivity_level.lower() not in SENSITIVITY_LEVELS:
        raise ValueError(f"Invalid sensitivity level: {sensitivity_level}. Must be one of {SENSITIVITY_LEVELS}")
    
    metadata = {
        # Original fields (compatibility with v1/v2)
        "filename": filename,
        "folder": folder,
        "path": path,
        "page": page,
        
        # Enhanced fields
        "chunk_index": chunk_index,
        "sensitivity_level": sensitivity_level.lower(),
        "classified_at": datetime.utcnow().isoformat(),
        "classified_by": classified_by,
        "document_source": document_source or folder,
    }
    
    # Optional fields
    if document_id:
        metadata["document_id"] = document_id
    if total_chunks:
        metadata["total_chunks"] = total_chunks
    
    return metadata


def validate_metadata(metadata: dict) -> bool:
    """
    Validate that metadata contains required fields.
    
    Args:
        metadata: Metadata dictionary to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = [
        "filename",
        "folder",
        "path",
        "page",
        "chunk_index",
        "sensitivity_level",
    ]
    
    missing = [field for field in required_fields if field not in metadata]
    
    if missing:
        raise ValueError(f"Missing required metadata fields: {missing}")
    
    # Validate sensitivity level
    level = metadata["sensitivity_level"]
    if level not in SENSITIVITY_LEVELS:
        raise ValueError(f"Invalid sensitivity level: {level}")
    
    return True


def filter_metadata_by_role(metadata_list: list[dict], role: str) -> list[dict]:
    """
    Filter metadata list based on user role access.
    
    Args:
        metadata_list: List of metadata dictionaries
        role: User role (employee/manager/admin)
        
    Returns:
        Filtered list of metadata
    """
    from theme.constants import ROLE_ACCESS
    
    role_lower = role.lower()
    if role_lower not in ROLE_ACCESS:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLE_ACCESS.keys())}")
    
    allowed_levels = ROLE_ACCESS[role_lower]
    
    return [
        meta for meta in metadata_list
        if meta.get("sensitivity_level") in allowed_levels
    ]


def get_chromadb_where_filter(role: str) -> dict:
    """
    Generate ChromaDB WHERE clause for role-based filtering.
    
    Args:
        role: User role (employee/manager/admin)
        
    Returns:
        ChromaDB where filter dictionary
    """
    from theme.constants import ROLE_ACCESS
    
    role_lower = role.lower()
    if role_lower not in ROLE_ACCESS:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLE_ACCESS.keys())}")
    
    allowed_levels = ROLE_ACCESS[role_lower]
    
    # ChromaDB where filter format
    if len(allowed_levels) == 1:
        return {"sensitivity_level": allowed_levels[0]}
    else:
        return {"sensitivity_level": {"$in": allowed_levels}}


def format_metadata_display(metadata: dict) -> str:
    """
    Format metadata for human-readable display.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Formatted string
    """
    from theme.constants import SENSITIVITY_ICONS
    
    level = metadata.get("sensitivity_level", "unknown")
    icon = SENSITIVITY_ICONS.get(level, "❓")
    
    return f"{icon} {level.upper()} | {metadata.get('filename', 'unknown')} (page {metadata.get('page', '?')})"


if __name__ == "__main__":
    # Test metadata creation
    print("Testing metadata creation...\n")
    
    meta = create_chunk_metadata(
        filename="test.pdf",
        folder="documents",
        path="/path/to/test.pdf",
        page=1,
        chunk_index=0,
        sensitivity_level="confidential",
        document_source="financial_report",
        total_chunks=10,
    )
    
    print("Created metadata:")
    for key, value in meta.items():
        print(f"  {key}: {value}")
    
    # Test validation
    print("\n✅ Validation passed")
    validate_metadata(meta)
    
    # Test filtering
    print("\nTesting role-based filtering...\n")
    
    test_metadata = [
        {"sensitivity_level": "public", "filename": "doc1.pdf"},
        {"sensitivity_level": "internal", "filename": "doc2.pdf"},
        {"sensitivity_level": "confidential", "filename": "doc3.pdf"},
    ]
    
    for role in ["employee", "manager", "admin"]:
        filtered = filter_metadata_by_role(test_metadata, role)
        print(f"{role.upper()}: Can access {len(filtered)} documents")
    
    # Test WHERE filter generation
    print("\nChromaDB WHERE filters:")
    for role in ["employee", "manager", "admin"]:
        where = get_chromadb_where_filter(role)
        print(f"  {role}: {where}")
