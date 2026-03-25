"""
database/db.py
--------------
Initialises the SQLite database for the Defence Zone Facial Recognition System.

Tables:
  - personnel   : Stores authorised person details and clearance level.
  - entry_logs  : Audit trail of every recognition event.
"""

import sqlite3
import os

# Resolve absolute path so the DB is always created relative to this file's
# parent directory, regardless of where the script is launched from.
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "defence.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------------ #
    # personnel table
    # clearance_level : 1 (lowest) – 5 (highest)
    # roles           : Soldier | Officer | Scientist | Visitor | Admin
    # ------------------------------------------------------------------ #
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personnel (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL UNIQUE,
            role            TEXT    NOT NULL,
            clearance_level INTEGER NOT NULL CHECK(clearance_level BETWEEN 1 AND 5),
            department      TEXT,
            photo_path      TEXT
        )
    """)

    # ------------------------------------------------------------------ #
    # entry_logs table – one row per recognition attempt
    # status : ALLOWED | DENIED | UNAUTHORIZED
    # ------------------------------------------------------------------ #
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entry_logs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER,
            name         TEXT    NOT NULL,
            role         TEXT,
            status       TEXT    NOT NULL,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialised at:", DB_PATH)


def get_person_by_name(name: str) -> dict | None:
    """Fetch a personnel record by exact name match. Returns dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personnel WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_personnel() -> list[dict]:
    """Return all personnel as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personnel ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_log(personnel_id, name: str, role: str, status: str) -> None:
    """Insert an entry into the entry_logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entry_logs (personnel_id, name, role, status) VALUES (?, ?, ?, ?)",
        (personnel_id, name, role, status),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50) -> list[dict]:
    """Return the most recent `limit` entry log rows, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM entry_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
