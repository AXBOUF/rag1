"""
Simple authentication system with SQLite storage.
"""

import sqlite3
import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple

DB_PATH = Path(__file__).parent / "users.db"


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with users table."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    # Create default admin if no users exist
    if count_users() == 0:
        register_user("admin", "admin123", "admin")


def hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = "rag_privacy_salt_v3"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def register_user(username: str, password: str, role: str = "employee") -> Tuple[bool, str]:
    """
    Register a new user.
    Returns (success, message).
    """
    if not username or not password:
        return False, "Username and password required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    
    if role not in ["employee", "manager", "admin"]:
        return False, "Invalid role"
    
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username.lower(), hash_password(password), role)
        )
        conn.commit()
        conn.close()
        return True, "User registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Registration failed: {e}"


def authenticate(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user.
    Returns user dict if successful, None otherwise.
    """
    if not username or not password:
        return None
    
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?",
        (username.lower(), hash_password(password))
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"id": row["id"], "username": row["username"], "role": row["role"]}
    return None


def get_user(username: str) -> Optional[dict]:
    """Get user by username."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, username, role FROM users WHERE username = ?",
        (username.lower(),)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"id": row["id"], "username": row["username"], "role": row["role"]}
    return None


def count_users() -> int:
    """Count total users."""
    conn = get_db()
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def list_users() -> list:
    """List all users (admin function)."""
    conn = get_db()
    cursor = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Initialize DB on import
init_db()
