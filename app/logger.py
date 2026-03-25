"""
app/logger.py
-------------
Logging utilities for the Defence Zone Facial Recognition System.

Responsibilities:
  - Write structured entry events to a rotating log file.
  - Print real-time console output colour-coded by status.
  - Trigger an alert (print + log) when an UNAUTHORIZED face is detected.
"""

import os
import logging
import logging.handlers
from datetime import datetime

# ── Log file location ─────────────────────────────────────────────────────── #
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR  = os.path.join(ROOT_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "entry_log.log")

os.makedirs(LOG_DIR, exist_ok=True)

# ── Configure rotating logger ─────────────────────────────────────────────── #
logger = logging.getLogger("DefenceZone")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # Rotating file handler – max 5 MB per file, keep last 5 files
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)


# ── Public helpers ────────────────────────────────────────────────────────── #

def log_entry(name: str, role: str | None, status: str) -> None:
    """Log an entry event at the appropriate severity level."""
    msg = f"ENTRY | name={name!r:<30} role={str(role):<12} status={status}"
    if status == "ALLOWED":
        logger.info(msg)
    elif status == "DENIED":
        logger.warning(msg)
    else:  # UNAUTHORIZED
        logger.error(msg)


def trigger_alert(name: str) -> None:
    """
    Raise an alert for an unknown / unauthorised intruder.

    Currently logs at CRITICAL level and prints a prominent console message.
    Extend this function to send emails, SMS, or push notifications.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_msg = (
        f"\n{'!'*60}\n"
        f"  ⚠️  SECURITY ALERT – UNAUTHORIZED FACE DETECTED\n"
        f"  Name     : {name}\n"
        f"  Timestamp: {timestamp}\n"
        f"{'!'*60}\n"
    )
    logger.critical(alert_msg)
    # TODO: Integrate with external alerting service here (email / webhook)
