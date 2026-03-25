"""
app/security.py
---------------
Security / access-control layer.

After a face is recognised, this module:
  1. Queries the personnel DB for the matched name.
  2. Evaluates clearance level against the zone threshold.
  3. Writes an entry log.
  4. Returns a structured access result dict.

Clearance policy for this demo:
  Level 1–2  → DENIED  (low clearance)
  Level 3–5  → ALLOWED (sufficient clearance)
  UNKNOWN    → UNAUTHORIZED
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_person_by_name, insert_log
from app.logger import trigger_alert

# Minimum clearance level required to enter the zone
CLEARANCE_THRESHOLD = 3


def evaluate_access(name: str) -> dict:
    """
    Given a recognised name (or "UNKNOWN"), determine access and log the event.

    Returns:
    {
        "name":            str,
        "role":            str | None,
        "department":      str | None,
        "clearance_level": int | None,
        "access_status":   "ALLOWED" | "DENIED" | "UNAUTHORIZED",
        "message":         str          # short human-readable verdict
    }
    """
    if name == "UNKNOWN":
        # Unknown face – immediate alert
        trigger_alert("UNKNOWN")
        insert_log(
            personnel_id=None,
            name="UNKNOWN",
            role="N/A",
            status="UNAUTHORIZED",
        )
        return {
            "name":            "UNKNOWN",
            "role":            None,
            "department":      None,
            "clearance_level": None,
            "access_status":   "UNAUTHORIZED",
            "message":         "⚠️  Unidentified individual – Access denied. Alert raised.",
        }

    # Look up the person in the DB
    person = get_person_by_name(name)

    if not person:
        # Name recognised by ML model but not in DB (data mismatch) – treat as denied
        insert_log(personnel_id=None, name=name, role="N/A", status="DENIED")
        return {
            "name":            name,
            "role":            None,
            "department":      None,
            "clearance_level": None,
            "access_status":   "DENIED",
            "message":         f"⛔  {name} not found in personnel register.",
        }

    clearance = person["clearance_level"]
    if clearance >= CLEARANCE_THRESHOLD:
        status  = "ALLOWED"
        message = f"✅  {name} – Access GRANTED (Clearance L{clearance})."
    else:
        status  = "DENIED"
        message = f"⛔  {name} – Access DENIED (Clearance L{clearance} below threshold)."

    insert_log(
        personnel_id=person["id"],
        name=name,
        role=person["role"],
        status=status,
    )

    return {
        "name":            name,
        "role":            person["role"],
        "department":      person["department"],
        "clearance_level": clearance,
        "access_status":   status,
        "message":         message,
    }
