"""
Database module for FrameTruth AI Forensic Tool.
Handles SQLite database initialization and connection management.
"""

import sqlite3
import os
import time
from typing import Optional
from pathlib import Path

# Database configuration
DB_PATH = os.environ.get("AIFT_DB", "aift.db")

# Database schema definition
DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at REAL NOT NULL,
    last_login REAL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT,
    sha256 TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    detector_name TEXT NOT NULL,
    detector_version TEXT NOT NULL,
    score REAL NOT NULL,
    label TEXT NOT NULL,
    confidence REAL,
    metadata TEXT,  -- JSON string for additional detector-specific data
    created_at REAL NOT NULL,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

CREATE TABLE IF NOT EXISTS acl (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    grantee_user_id INTEGER NOT NULL,
    permission TEXT NOT NULL CHECK(permission IN ('read', 'write', 'admin')),
    granted_by INTEGER NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL,  -- Optional expiration
    UNIQUE(file_id, grantee_user_id, permission),
    FOREIGN KEY(file_id) REFERENCES files(id),
    FOREIGN KEY(grantee_user_id) REFERENCES users(id),
    FOREIGN KEY(granted_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY,
    actor_user_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('VIEW', 'DOWNLOAD', 'UPLOAD', 'DELETE', 'SHARE', 'REVOKE')),
    ip_address TEXT,
    user_agent TEXT,
    ts REAL NOT NULL,
    metadata TEXT,  -- JSON string for additional context
    FOREIGN KEY(actor_user_id) REFERENCES users(id),
    FOREIGN KEY(file_id) REFERENCES files(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_files_owner ON files(owner_id);
CREATE INDEX IF NOT EXISTS idx_files_sha256 ON files(sha256);
CREATE INDEX IF NOT EXISTS idx_detections_file ON detections(file_id);
CREATE INDEX IF NOT EXISTS idx_acl_file_grantee ON acl(file_id, grantee_user_id);
CREATE INDEX IF NOT EXISTS idx_access_log_actor ON access_log(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_access_log_file ON access_log(file_id);
CREATE INDEX IF NOT EXISTS idx_access_log_ts ON access_log(ts);
"""


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def init_database(self) -> bool:
        """Initialize the database with all tables and indexes."""
        try:
            with self.get_connection() as conn:
                conn.executescript(DDL)
                conn.commit()
            return True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset the database by dropping all tables and recreating them."""
        try:
            with self.get_connection() as conn:
                # Drop all tables
                conn.execute("DROP TABLE IF EXISTS access_log")
                conn.execute("DROP TABLE IF EXISTS acl")
                conn.execute("DROP TABLE IF EXISTS detections")
                conn.execute("DROP TABLE IF EXISTS files")
                conn.execute("DROP TABLE IF EXISTS users")
                conn.commit()
            
            # Reinitialize
            return self.init_database()
        except Exception as e:
            print(f"Database reset failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get information about the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table information
                tables = cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """).fetchall()
                
                # Get row counts
                counts = {}
                for table in tables:
                    table_name = table[0]
                    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    counts[table_name] = count
                
                return {
                    "db_path": self.db_path,
                    "tables": [table[0] for table in tables],
                    "row_counts": counts,
                    "size_mb": os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
                }
        except Exception as e:
            return {"error": str(e)}


# Global database manager instance
db_manager = DatabaseManager()


def get_connection() -> sqlite3.Connection:
    """Get a database connection using the global manager."""
    return db_manager.get_connection()


def init_db() -> bool:
    """Initialize the database using the global manager."""
    return db_manager.init_database()


def reset_db() -> bool:
    """Reset the database using the global manager."""
    return db_manager.reset_database()


def get_db_info() -> dict:
    """Get database information using the global manager."""
    return db_manager.get_database_info()


if __name__ == "__main__":
    # Test database initialization
    print("Initializing database...")
    if init_db():
        print("Database initialized successfully!")
        info = get_db_info()
        print(f"Database info: {info}")
    else:
        print("Database initialization failed!")
