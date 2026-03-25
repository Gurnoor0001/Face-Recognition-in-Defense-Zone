/**
 * main.js
 * -------
 * Frontend logic for the DefenceShield Facial Recognition UI.
 *
 * Responsibilities:
 *   - Drive webcam access via getUserMedia
 *   - Capture canvas frames and send base64 images to /recognize
 *   - Draw bounding boxes & labels on the overlay canvas
 *   - Update the identity panel, clearance bar, and access banner
 *   - Refresh the entry log table
 *   - Show alert toasts for UNAUTHORIZED detections
 */

"use strict";

// ── DOM references ───────────────────────────────────────────────────────── //
const video           = document.getElementById("videoElement");
const canvas          = document.getElementById("overlayCanvas");
const ctx             = canvas.getContext("2d");
const btnStart        = document.getElementById("btnStartCamera");
const btnCapture      = document.getElementById("btnCapture");
const btnAuto         = document.getElementById("btnAuto");
const btnRefreshLogs  = document.getElementById("btnRefreshLogs");
const clockDisplay    = document.getElementById("clockDisplay");
const feedBadge       = document.getElementById("feedBadge");

// Identity panel
const idName          = document.getElementById("idName");
const idRole          = document.getElementById("idRole");
const idDept          = document.getElementById("idDept");
const idClearance     = document.getElementById("idClearance");
const idConfidence    = document.getElementById("idConfidence");
const avatarInit      = document.getElementById("avatarPlaceholder");

// Access banner
const accessBanner    = document.getElementById("accessBanner");
const accessIcon      = document.getElementById("accessIcon");
const accessText      = document.getElementById("accessText");
const accessMessage   = document.getElementById("accessMessage");
const clearanceFill   = document.getElementById("clearanceFill");

// Log table
const logBody         = document.getElementById("logBody");

// Toast
const alertToast      = document.getElementById("alertToast");
const alertMsg        = document.getElementById("alertMsg");

// ── State ────────────────────────────────────────────────────────────────── //
let stream        = null;
let autoTimer     = null;        // interval ID for auto-scan
let autoActive    = false;
let scanning      = false;       // debounce flag

// ── Clock ─────────────────────────────────────────────────────────────────  //
function updateClock() {
  const now = new Date();
  clockDisplay.textContent = now.toTimeString().slice(0, 8);
}
setInterval(updateClock, 1000);
updateClock();

// ── Camera ─────────────────────────────────────────────────────────────── //
btnStart.addEventListener("click", async () => {
  if (stream) {
    // Stop camera
    stream.getTracks().forEach(t => t.stop());
    stream = null;
    video.srcObject = null;
    btnStart.textContent = "⏵ START CAMERA";
    btnCapture.disabled = true;
    btnAuto.disabled    = true;
    feedBadge.textContent = "OFFLINE";
    feedBadge.style.background = "#555";
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
      audio: false,
    });
    video.srcObject = stream;
    await video.play();
    btnStart.textContent = "⏹ STOP CAMERA";
    btnCapture.disabled  = false;
    btnAuto.disabled     = false;
    feedBadge.textContent = "LIVE";
    feedBadge.style.background = "";
    resizeCanvas();
  } catch (err) {
    showToast(`Camera error: ${err.message}`, false);
  }
});

// ── Resize canvas to match video element ─────────────────────────────────── //
function resizeCanvas() {
  canvas.width  = video.videoWidth  || video.clientWidth;
  canvas.height = video.videoHeight || video.clientHeight;
}
window.addEventListener("resize", resizeCanvas);
video.addEventListener("loadedmetadata", resizeCanvas);

// ── Capture + send ───────────────────────────────────────────────────────── //
btnCapture.addEventListener("click", captureAndRecognize);

async function captureAndRecognize() {
  if (scanning || !stream) return;
  scanning = true;

  // Draw current video frame onto a hidden capture canvas
  const capture = document.createElement("canvas");
  capture.width  = video.videoWidth;
  capture.height = video.videoHeight;
  capture.getContext("2d").drawImage(video, 0, 0);

  // Show scan sweep animation
  showScanSweep();

  const dataUrl = capture.toDataURL("image/jpeg", 0.85);

  try {
    const res  = await fetch("/recognize", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ image: dataUrl }),
    });
    const data = await res.json();
    handleResults(data, capture.width, capture.height);
  } catch (err) {
    setAccessBanner("ERROR", `⚡ Network error: ${err.message}`);
  } finally {
    scanning = false;
  }
}

// ── Handle recognition results ───────────────────────────────────────────── //
function handleResults(results, imgW, imgH) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!results || results.length === 0) return;

  // Use the first (or most confident) result for the identity panel
  const primary = results.reduce((best, r) =>
    (r.confidence || 0) > (best.confidence || 0) ? r : best
  , results[0]);

  results.forEach(r => drawBbox(r, imgW, imgH));
  updatePanel(primary);

  if (primary.access_status === "UNAUTHORIZED") {
    showToast(`⚠ INTRUDER DETECTED – ${new Date().toLocaleTimeString()}`, true);
  }

  // Refresh log table after each result
  fetchLogs();
}

// ── Draw bounding box on overlay canvas ─────────────────────────────────── //
function drawBbox(result, imgW, imgH) {
  if (!result.bbox) return;

  const { top, right, bottom, left } = result.bbox;
  const scaleX = canvas.width  / imgW;
  const scaleY = canvas.height / imgH;

  const x = left   * scaleX;
  const y = top    * scaleY;
  const w = (right - left)   * scaleX;
  const h = (bottom - top)   * scaleY;

  // Choose colour by status
  const color = statusColor(result.access_status);

  ctx.strokeStyle = color;
  ctx.lineWidth   = 2.5;
  ctx.shadowColor = color;
  ctx.shadowBlur  = 12;
  ctx.strokeRect(x, y, w, h);
  ctx.shadowBlur  = 0;

  // Label background
  const label  = `${result.name}  [${result.access_status}]`;
  const pxSize = 13;
  ctx.font         = `bold ${pxSize}px 'Share Tech Mono', monospace`;
  const textW      = ctx.measureText(label).width;
  ctx.fillStyle    = "rgba(0,0,0,0.72)";
  ctx.fillRect(x, y - pxSize - 6, textW + 10, pxSize + 8);

  ctx.fillStyle = color;
  ctx.fillText(label, x + 5, y - 6);
}

function statusColor(status) {
  switch (status) {
    case "ALLOWED":      return "#39ff14";
    case "DENIED":       return "#ff2244";
    case "UNAUTHORIZED": return "#fbbf24";
    default:             return "#38bdf8";
  }
}

// ── Update identity panel ────────────────────────────────────────────────── //
function updatePanel(r) {
  idName.textContent       = r.name       || "—";
  idRole.textContent       = r.role       || "—";
  idDept.textContent       = r.department || "—";
  idClearance.textContent  = r.clearance_level != null ? `L${r.clearance_level}` : "—";
  idConfidence.textContent = r.confidence  != null ? `${(r.confidence * 100).toFixed(1)}%` : "—";

  // Avatar initial letter
  avatarInit.textContent = (r.name && r.name !== "UNKNOWN" && r.name !== "NO FACE")
    ? r.name.charAt(0).toUpperCase()
    : "?";

  setAccessBanner(r.access_status, r.message);

  // Update clearance bar
  const lvl = r.clearance_level || 0;
  clearanceFill.style.width = `${(lvl / 5) * 100}%`;
}

function setAccessBanner(status, message) {
  // Reset classes
  accessBanner.className = "access-banner";
  accessText.className   = "access-text";

  const cfg = {
    ALLOWED:       { icon: "✅", text: "ACCESS GRANTED",   bannerCls: "banner-allowed", textCls: "text-allowed" },
    DENIED:        { icon: "⛔", text: "ACCESS DENIED",    bannerCls: "banner-denied",  textCls: "text-denied"  },
    UNAUTHORIZED:  { icon: "⚠️", text: "UNAUTHORIZED",     bannerCls: "banner-unknown", textCls: "text-unknown" },
    "NO FACE":     { icon: "🔍", text: "NO FACE DETECTED", bannerCls: "banner-noface",  textCls: ""             },
    ERROR:         { icon: "⚡", text: "SYSTEM ERROR",     bannerCls: "banner-denied",  textCls: "text-denied"  },
  }[status] || { icon: "⬡", text: "SCANNING…", bannerCls: "", textCls: "" };

  accessIcon.textContent = cfg.icon;
  accessText.textContent = cfg.text;
  if (cfg.bannerCls) accessBanner.classList.add(cfg.bannerCls);
  if (cfg.textCls)   accessText.classList.add(cfg.textCls);
  accessMessage.textContent = message || "";
}

// ── Auto mode ────────────────────────────────────────────────────────────── //
btnAuto.addEventListener("click", () => {
  if (autoActive) {
    clearInterval(autoTimer);
    autoActive = false;
    btnAuto.textContent = "⟳ AUTO (2s)";
    btnAuto.style.borderColor = "";
    btnAuto.style.color = "";
  } else {
    autoActive  = true;
    btnAuto.textContent = "⏸ AUTO ON";
    btnAuto.style.borderColor = "#39ff14";
    btnAuto.style.color = "#39ff14";
    captureAndRecognize();
    autoTimer = setInterval(captureAndRecognize, 2000);
  }
});

// ── Scan sweep animation ──────────────────────────────────────────────────  //
function showScanSweep() {
  const camContainer = document.querySelector(".camera-container");
  const sweep = document.createElement("div");
  sweep.className = "scan-sweep";
  camContainer.appendChild(sweep);
  setTimeout(() => sweep.remove(), 1600);
}

// ── Alert toast ───────────────────────────────────────────────────────────  //
let toastTimer = null;
function showToast(message, isAlert = true) {
  alertMsg.textContent = message;
  alertToast.style.borderColor = isAlert ? "#ff2244" : "#38bdf8";
  alertToast.style.color       = isAlert ? "#ff2244" : "#38bdf8";
  alertToast.classList.add("show");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => alertToast.classList.remove("show"), 5000);
}

// ── Entry log fetch ───────────────────────────────────────────────────────  //
btnRefreshLogs.addEventListener("click", fetchLogs);

async function fetchLogs() {
  try {
    const res  = await fetch("/logs");
    const logs = await res.json();
    renderLogs(logs);
  } catch (_) { /* silent fail */ }
}

function renderLogs(logs) {
  if (!logs || logs.length === 0) {
    logBody.innerHTML = '<tr><td colspan="5" class="no-data">No entries yet.</td></tr>';
    return;
  }
  logBody.innerHTML = logs.map((row, i) => {
    const statusCls = {
      ALLOWED:      "status-allowed",
      DENIED:       "status-denied",
      UNAUTHORIZED: "status-unauth",
    }[row.status] || "";
    return `<tr>
      <td>${row.id}</td>
      <td>${escHtml(row.name)}</td>
      <td>${escHtml(row.role || "N/A")}</td>
      <td class="${statusCls}">${row.status}</td>
      <td>${row.timestamp}</td>
    </tr>`;
  }).join("");
}

function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ── Initial log load ──────────────────────────────────────────────────────  //
fetchLogs();
