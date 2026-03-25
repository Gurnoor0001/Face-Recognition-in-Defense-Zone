"""
database/seed.py
----------------
Populates the personnel table with sample defence zone personnel.
Run once after init_db() to provide demo data.
"""

import sys
import os

# Allow relative import when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_connection, init_db

SAMPLE_PERSONNEL = [
    # (name,              role,        clearance_level, department)
    ("Col. Arjun Singh",   "Officer",   5,               "Command"),
    ("Col. GurnoorSingh",  "Officer",   5,               "Command"),
    ("Maj. Priya Sharma", "Officer",   4,               "Intelligence"),
    ("Sgt. Ravi Kumar",   "Soldier",   3,               "Infantry"),
    ("Cpl. Anita Verma",  "Soldier",   2,               "Logistics"),
    ("Dr. Karan Mehta",   "Scientist", 4,               "R&D"),
    ("Visitor Rahul Das", "Visitor",   1,               "External"),
]


def seed() -> None:
    """Insert sample personnel if not already present."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    inserted = 0
    for name, role, clearance, dept in SAMPLE_PERSONNEL:
        try:
            cursor.execute(
                """
                INSERT INTO personnel (name, role, clearance_level, department)
                VALUES (?, ?, ?, ?)
                """,
                (name, role, clearance, dept),
            )
            inserted += 1
        except Exception:
            # Skip duplicates (UNIQUE constraint on name)
            pass
    conn.commit()
    conn.close()
    print(f"[SEED] Inserted {inserted} personnel records.")


if __name__ == "__main__":
    seed()
