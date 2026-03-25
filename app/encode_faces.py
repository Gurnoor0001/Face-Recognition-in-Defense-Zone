"""
app/encode_faces.py
-------------------
Scans the /photos directory, generates 128-d face encodings using the
face_recognition library, and serialises them to /models/encodings.pkl.

Expected /photos folder layout:
    photos/
      Col. Arjun Singh/
          photo.jpg          ← one or more images per person
      Maj. Priya Sharma/
          photo.jpg
      ...

Each sub-folder name MUST exactly match the `name` field in the personnel table.
Run this script whenever new personnel photos are added.
"""

import os
import sys
import pickle
import face_recognition

# ── Path resolution ───────────────────────────────────────────────────────── #
ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS_DIR  = os.path.join(ROOT_DIR, "photos")
MODELS_DIR  = os.path.join(ROOT_DIR, "models")
OUTPUT_PATH = os.path.join(MODELS_DIR, "encodings.pkl")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

# ── Main encoding routine ─────────────────────────────────────────────────── #

def generate_encodings() -> dict:
    """
    Walk the photos directory, encode every face found, and return a dict:
      { "encodings": [list of 128-d arrays],
        "names":     [list of corresponding person names] }
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    all_encodings = []
    all_names     = []
    errors        = []

    if not os.path.isdir(PHOTOS_DIR):
        print(f"[ERROR] Photos directory not found: {PHOTOS_DIR}")
        sys.exit(1)

    person_dirs = [
        d for d in os.listdir(PHOTOS_DIR)
        if os.path.isdir(os.path.join(PHOTOS_DIR, d))
    ]

    if not person_dirs:
        print("[WARN] No sub-folders found in /photos. Add a folder per person.")
        return {"encodings": [], "names": []}

    print(f"[ENCODE] Found {len(person_dirs)} person folder(s). Processing…")

    for person_name in person_dirs:
        person_dir = os.path.join(PHOTOS_DIR, person_name)
        image_files = [
            f for f in os.listdir(person_dir)
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
        ]

        if not image_files:
            print(f"  [SKIP] No images in {person_name}/")
            continue

        for img_file in image_files:
            img_path = os.path.join(person_dir, img_file)
            try:
                # Load image as RGB numpy array
                image = face_recognition.load_image_file(img_path)
                # Locate all faces in the image
                boxes = face_recognition.face_locations(image, model="hog")
                if not boxes:
                    print(f"  [WARN] No face found in {img_path}")
                    continue
                # Compute 128-d encoding for each detected face
                encodings = face_recognition.face_encodings(image, boxes)
                for enc in encodings:
                    all_encodings.append(enc)
                    all_names.append(person_name)
                print(f"  [OK]   {person_name}/{img_file} → {len(encodings)} encoding(s)")
            except Exception as exc:
                msg = f"  [ERROR] {img_path}: {exc}"
                print(msg)
                errors.append(msg)

    data = {"encodings": all_encodings, "names": all_names}

    # Serialise to disk
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(data, f)

    print(f"\n[ENCODE] Done. {len(all_encodings)} encoding(s) saved → {OUTPUT_PATH}")
    if errors:
        print(f"[ENCODE] {len(errors)} error(s) encountered (see above).")

    return data


if __name__ == "__main__":
    generate_encodings()
