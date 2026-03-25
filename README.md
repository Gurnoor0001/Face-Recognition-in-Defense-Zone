# 🛡️ DefenceShield – AI Facial Recognition System

> AI-powered biometric access control for secure defence zone entry.  
> Built with Python · face_recognition · OpenCV · Flask · SQLite

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Add Personnel Photos](#add-personnel-photos)
4. [Run the System](#run-the-system)
5. [Using the Web UI](#using-the-web-ui)
6. [Project Structure](#project-structure)
7. [API Reference](#api-reference)
8. [Security Rules](#security-rules)
9. [Sample Personnel](#sample-personnel)
10. [Extend the System](#extend-the-system)

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.9 → 3.11 | ⚠️ Python 3.12+ may have `dlib` issues |
| pip | latest | comes with Python |
| CMake | any | [Download](https://cmake.org/download/) — required by `dlib` |
| VS Build Tools | 2019 / 2022 | **Windows only** — [Download](https://aka.ms/vs/17/release/vs_BuildTools.exe) |
| Webcam | any | Required for live scanning |

> **macOS / Linux:** CMake + VS Build Tools are not needed. `dlib` compiles natively.

---

## 2. Installation

### Step 1 — Clone / open the project
```bash
cd C:\projects\project
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv
```

### Step 3 — Activate the virtual environment

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

#### ❗ Trouble installing `face-recognition` on Windows?

Run these **in order**:
```bash
pip install cmake
pip install dlib
pip install face-recognition
pip install flask opencv-python numpy Pillow
```

---

## 3. Add Personnel Photos

Each person needs a sub-folder inside `/photos/` whose name **exactly matches** their name in the database.

```
photos/
  Col. Arjun Singh/       ← folder name = DB name
      photo1.jpg
      photo2.jpg
  Maj. Priya Sharma/
      photo.jpg
  ...
```

**Rules:**
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`
- ≥ 1 photo per person (more = better accuracy)
- Face must be clearly visible, well-lit, front-facing

The 6 sample folders (`Col. Arjun Singh/`, `Maj. Priya Sharma/`, etc.) are already created — just drop photos inside them.

---

## 4. Run the System

### ▶ Full startup (recommended)
Initialises the database, seeds sample data, generates face encodings, then starts the web server — all in one command:

```bash
python main.py
```

Expected output:
```
============================================================
  DefenceShield – Facial Recognition System
============================================================
[DB] Database initialised at: …/database/defence.db
[SEED] Inserted 6 personnel records.
[ENCODE] Found 6 person folder(s). Processing…
  [OK]   Col. Arjun Singh/photo.jpg → 1 encoding(s)
  ...
[ENCODE] Done. 6 encoding(s) saved → models/encodings.pkl
[SERVER] Starting Flask on http://127.0.0.1:5000
```

### Other CLI options

| Command | What it does |
|---|---|
| `python main.py` | Full startup (DB + encode + server) |
| `python main.py --init-only` | Init DB + seed only (no server) |
| `python main.py --encode` | Re-generate encodings only (no server) |

> **Re-encode after adding new photos:**
> ```bash
> python main.py --encode
> ```

---

## 5. Using the Web UI

1. Open your browser and go to: **http://127.0.0.1:5000**
2. Click **⏵ START CAMERA** → allow camera access when prompted
3. Hold a person's face in front of the camera, then:
   - Click **⊙ SCAN FRAME** for a single scan, or
   - Click **⟳ AUTO (2s)** to scan automatically every 2 seconds
4. The panel on the right shows:
   - **Name, Role, Department, Clearance Level**
   - **GREEN banner** = ✅ ACCESS GRANTED
   - **RED banner** = ⛔ ACCESS DENIED
   - **AMBER banner** = ⚠️ UNAUTHORIZED (unknown face)
5. The **ENTRY LOG** table at the bottom records every scan with timestamp
6. Unknown faces trigger an **alert toast** notification

---

## 6. Project Structure

```
project/
├── main.py                     ← Entry point
├── requirements.txt
│
├── photos/                     ← Face image dataset
│   ├── Col. Arjun Singh/
│   │   └── photo.jpg
│   └── ...
│
├── models/
│   └── encodings.pkl           ← Auto-generated (do not edit)
│
├── database/
│   ├── db.py                   ← SQLite schema & helpers
│   ├── seed.py                 ← Sample data
│   └── defence.db              ← Auto-generated SQLite file
│
├── app/
│   ├── app.py                  ← Flask routes
│   ├── encode_faces.py         ← Encoding generator
│   ├── recognizer.py           ← Face matching engine
│   ├── security.py             ← Clearance / access logic
│   ├── logger.py               ← Rotating file log + alerts
│   ├── templates/
│   │   └── index.html          ← Operator dashboard UI
│   └── static/
│       ├── styles.css
│       └── main.js
│
└── logs/
    └── entry_log.log           ← Auto-generated rotating log
```

---

## 7. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Operator dashboard UI |
| `POST` | `/recognize` | Run face recognition on a base64 image |
| `GET` | `/logs` | Return last 50 entry log rows (JSON) |
| `GET` | `/api/personnel` | Return all personnel records (JSON) |

**`POST /recognize` – request body:**
```json
{ "image": "data:image/jpeg;base64,/9j/4AAQ..." }
```

**`POST /recognize` – response:**
```json
[
  {
    "name": "Col. Arjun Singh",
    "role": "Officer",
    "department": "Command",
    "clearance_level": 5,
    "access_status": "ALLOWED",
    "message": "✅  Col. Arjun Singh – Access GRANTED (Clearance L5).",
    "confidence": 0.873,
    "bbox": { "top": 72, "right": 310, "bottom": 210, "left": 172 }
  }
]
```

---

## 8. Security Rules

| Clearance Level | Typical Roles | Access |
|:---:|---|:---:|
| L5 | Command Officers, Admins | ✅ ALLOWED |
| L4 | Senior Officers, Scientists | ✅ ALLOWED |
| L3 | Soldiers | ✅ ALLOWED |
| L2 | Logistics / Support | ⛔ DENIED |
| L1 | Visitors | ⛔ DENIED |
| — | Unrecognised face | ⚠️ UNAUTHORIZED |

**Minimum clearance threshold:** L3 (configurable in `app/security.py` → `CLEARANCE_THRESHOLD`)

---

## 9. Sample Personnel

These are pre-seeded into the database when you run `python main.py`:

| Name | Role | Clearance | Department |
|---|---|:---:|---|
| Col. Arjun Singh | Officer | L5 | Command |
| Maj. Priya Sharma | Officer | L4 | Intelligence |
| Sgt. Ravi Kumar | Soldier | L3 | Infantry |
| Cpl. Anita Verma | Soldier | L2 | Logistics |
| Dr. Karan Mehta | Scientist | L4 | R&D |
| Visitor Rahul Das | Visitor | L1 | External |

---

## 10. Extend the System

| Goal | What to change |
|---|---|
| Add a new person | Create `photos/<Name>/photo.jpg`, run `python main.py --encode` |
| Add email/SMS alerts | Edit `trigger_alert()` in `app/logger.py` |
| Change access threshold | Edit `CLEARANCE_THRESHOLD` in `app/security.py` |
| Use GPU (CUDA) | Change `model="hog"` → `model="cnn"` in `app/recognizer.py` |
| Switch to MySQL | Replace `sqlite3` calls in `database/db.py` with `mysql-connector-python` |
