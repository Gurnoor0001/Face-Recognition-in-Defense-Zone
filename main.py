"""
main.py
-------
Entry point for the Defence Zone Facial Recognition System.

Usage:
  python main.py               – Init DB, encode faces, launch Flask server
  python main.py --init-only   – Only init DB + seed data (no server)
  python main.py --encode      – Only re-generate face encodings (no server)
"""

import sys
import os

# ── Ensure project root is on sys.path ────────────────────────────────────── #
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# ── Imports ───────────────────────────────────────────────────────────────── #
from database.db     import init_db
from database.seed   import seed
from app.encode_faces import generate_encodings


def bootstrap():
    """Initialise the database and seed sample data."""
    print("=" * 60)
    print("  DefenceShield – Facial Recognition System")
    print("=" * 60)
    init_db()
    seed()


def encode():
    """Generate face encodings from the /photos directory."""
    generate_encodings()


def run_server():
    """Launch the Flask development server."""
    from app.app import app
    print("\n[SERVER] Starting Flask on http://127.0.0.1:5000")
    print("[SERVER] Press CTRL+C to stop.\n")
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--init-only" in args:
        bootstrap()
        print("\n[DONE] DB & seed complete. Exiting.")
        sys.exit(0)

    if "--encode" in args:
        encode()
        print("\n[DONE] Encoding complete. Exiting.")
        sys.exit(0)

    # Default: full startup
    bootstrap()
    encode()
    run_server()
