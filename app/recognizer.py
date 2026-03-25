"""
app/recognizer.py
-----------------
Loads face encodings from disk and matches faces detected in an input image
(supplied as a numpy array) against the known encodings.

Returns a list of recognition results, one per detected face:
  [
    {
      "name":       "Col. Arjun Singh",   # or "UNKNOWN"
      "location":   (top, right, bottom, left),
      "confidence": 0.87                  # 1 - distance; None for UNKNOWN
    },
    ...
  ]
"""

import os
import pickle
import face_recognition
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────── #
ROOT_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENCODINGS_PATH = os.path.join(ROOT_DIR, "models", "encodings.pkl")

# Tolerance: lower = stricter matching (0.5 is a good balance)
TOLERANCE = 0.50

# Cached data (loaded once per server lifetime)
_cache: dict | None = None


def _load_encodings() -> dict:
    """Load & cache face encodings from disk."""
    global _cache
    if _cache is not None:
        return _cache
    if not os.path.exists(ENCODINGS_PATH):
        print("[WARN] encodings.pkl not found. Run app/encode_faces.py first.")
        _cache = {"encodings": [], "names": []}
    else:
        with open(ENCODINGS_PATH, "rb") as f:
            _cache = pickle.load(f)
        print(f"[RECOGNIZER] Loaded {len(_cache['encodings'])} encoding(s).")
    return _cache


def reload_encodings() -> None:
    """Force a reload of encodings (call after adding new photos)."""
    global _cache
    _cache = None
    _load_encodings()


def recognize(image_rgb: np.ndarray) -> list[dict]:
    """
    Detect and identify all faces in `image_rgb` (H×W×3 uint8 numpy array in RGB).

    Returns a list of result dicts (see module docstring).
    """
    data = _load_encodings()
    known_encodings: list = data["encodings"]
    known_names: list[str] = data["names"]

    results: list[dict] = []

    # Detect face bounding boxes using HOG (fast, CPU-friendly)
    face_locations = face_recognition.face_locations(image_rgb, model="hog")
    if not face_locations:
        return results

    # Compute encodings for all detected faces in one call
    face_encodings = face_recognition.face_encodings(image_rgb, face_locations)

    for encoding, location in zip(face_encodings, face_locations):
        name = "UNKNOWN"
        confidence = None

        if known_encodings:
            # Compare this face against all known encodings
            distances = face_recognition.face_distance(known_encodings, encoding)
            best_idx  = int(np.argmin(distances))
            best_dist = float(distances[best_idx])

            if best_dist <= TOLERANCE:
                name       = known_names[best_idx]
                confidence = round(1.0 - best_dist, 3)

        results.append({
            "name":       name,
            "location":   location,   # (top, right, bottom, left)
            "confidence": confidence,
        })

    return results
