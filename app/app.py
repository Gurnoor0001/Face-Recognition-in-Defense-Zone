"""
app/app.py
----------
Flask backend for the Defence Zone Facial Recognition System.

Routes:
  GET  /                → Render the main operator UI
  POST /recognize       → Accept base64-encoded image, run recognition, return JSON
  GET  /logs            → Return last 50 entry log rows as JSON
  GET  /api/personnel   → Return all personnel records as JSON
"""

import os
import sys
import base64
import io
import numpy as np

from flask import Flask, request, jsonify, render_template

# Ensure project root is on the path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from app.recognizer import recognize
from app.security   import evaluate_access
from app.logger     import log_entry
from database.db    import get_recent_logs, get_all_personnel

# ── Flask app ─────────────────────────────────────────────────────────────── #
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    import cv2


# ── Helpers ───────────────────────────────────────────────────────────────── #

def decode_image(data_uri: str) -> np.ndarray:
    """
    Decode a base64 data-URI (e.g. from a <canvas> capture) into an RGB
    numpy array suitable for face_recognition.
    """
    # Strip the 'data:image/...;base64,' prefix if present
    if "," in data_uri:
        data_uri = data_uri.split(",", 1)[1]

    raw = base64.b64decode(data_uri)

    if PIL_AVAILABLE:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        return np.array(image)
    else:
        arr = np.frombuffer(raw, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


# ── Routes ────────────────────────────────────────────────────────────────── #

@app.route("/")
def index():
    """Render the operator dashboard."""
    return render_template("index.html")


@app.route("/recognize", methods=["POST"])
def recognize_face():
    """
    Accept a JSON body: { "image": "<base64 data-URI>" }
    Returns a JSON list of recognition results, one per detected face.
    """
    body = request.get_json(force=True, silent=True) or {}
    image_data = body.get("image")

    if not image_data:
        return jsonify({"error": "No image provided"}), 400

    try:
        image_rgb = decode_image(image_data)
    except Exception as exc:
        return jsonify({"error": f"Image decode failed: {exc}"}), 400

    # ── Recognition ───────────────────────────────────────────────────────── #
    detections = recognize(image_rgb)

    results = []
    for det in detections:
        # Security check + DB lookup
        access = evaluate_access(det["name"])
        # Log to file as well
        log_entry(access["name"], access["role"], access["access_status"])

        top, right, bottom, left = det["location"]
        results.append({
            "name":            access["name"],
            "role":            access["role"],
            "department":      access["department"],
            "clearance_level": access["clearance_level"],
            "access_status":   access["access_status"],
            "message":         access["message"],
            "confidence":      det["confidence"],
            "bbox":            {
                "top": top, "right": right, "bottom": bottom, "left": left
            },
        })

    # If no face was detected at all
    if not results:
        results.append({
            "name":            "NO FACE",
            "role":            None,
            "department":      None,
            "clearance_level": None,
            "access_status":   "NO FACE",
            "message":         "No face detected in frame.",
            "confidence":      None,
            "bbox":            None,
        })

    return jsonify(results)


@app.route("/logs")
def get_logs():
    """Return the last 50 entry log rows as JSON."""
    logs = get_recent_logs(50)
    return jsonify(logs)


@app.route("/api/personnel")
def api_personnel():
    """Return all personnel records as JSON."""
    return jsonify(get_all_personnel())


# ── Dev server entry-point ────────────────────────────────────────────────── #
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
