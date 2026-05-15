"""
Enhanced metadata schema for EVALUATION (copied from version3).
"""

from datetime import datetime
from typing import Optional
from theme.constants import SENSITIVITY_LEVELS


def create_chunk_metadata(
    filename: str,
    folder: str,
    path: str,
    page: int,
    chunk_index: int,
    sensitivity_level: str,
    document_source: Optional[str] = None,
    classified_by: str = "llm",
    document_id: Optional[str] = None,
    total_chunks: Optional[int] = None,
) -> dict:
    if sensitivity_level.lower() not in SENSITIVITY_LEVELS:
        raise ValueError(f"Invalid sensitivity level: {sensitivity_level}. Must be one of {SENSITIVITY_LEVELS}")

    metadata = {
        "filename": filename,
        "folder": folder,
        "path": path,
        "page": page,
        "chunk_index": chunk_index,
        "sensitivity_level": sensitivity_level.lower(),
        "classified_at": datetime.utcnow().isoformat(),
        "classified_by": classified_by,
        "document_source": document_source or folder,
    }

    if document_id:
        metadata["document_id"] = document_id
    if total_chunks:
        metadata["total_chunks"] = total_chunks

    return metadata


def validate_metadata(metadata: dict) -> bool:
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

    level = metadata["sensitivity_level"]
    if level not in SENSITIVITY_LEVELS:
        raise ValueError(f"Invalid sensitivity level: {level}")

    return True


def filter_metadata_by_role(metadata_list: list[dict], role: str) -> list[dict]:
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
    from theme.constants import ROLE_ACCESS

    role_lower = role.lower()
    if role_lower not in ROLE_ACCESS:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLE_ACCESS.keys())}")

    allowed_levels = ROLE_ACCESS[role_lower]

    if len(allowed_levels) == 1:
        return {"sensitivity_level": allowed_levels[0]}
    else:
        return {"sensitivity_level": {"$in": allowed_levels}}


def format_metadata_display(metadata: dict) -> str:
    from theme.constants import SENSITIVITY_ICONS

    level = metadata.get("sensitivity_level", "unknown")
    icon = SENSITIVITY_ICONS.get(level, "❓")

    return f"{icon} {level.upper()} | {metadata.get('filename', 'unknown')} (page {metadata.get('page', '?')})"
