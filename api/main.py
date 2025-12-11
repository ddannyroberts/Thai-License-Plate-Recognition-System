# api/main.py
import os, json, cv2, uvicorn, numpy as np
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List, Set, Tuple
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .local_models import infer_detector, infer_reader
from .database import engine, SessionLocal
from .models import Base, PlateRecord, User
from .schemas import PlateCreateResponse
from .ocr import run_ocr_on_bbox
from .utils import extract_bboxes, merge_boxes
from .arduino import send_open_gate
from .auth import create_user, authenticate_user, generate_session_token
from .province_parser import parse_plate

# =============================
# DB + APP bootstrap
# =============================
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Thai Motorcycle License Plate API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

# =============================
# User Authentication
# =============================
# In-memory session storage (use Redis in production)
sessions = {}

@app.post("/api/auth/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Register a new user"""
    db = SessionLocal()
    try:
        # Validate input
        if not username or len(username) < 3:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Username must be at least 3 characters"}
            )
        
        if not email or "@" not in email:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid email address"}
            )
        
        if not password or len(password) < 6:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Password must be at least 6 characters"}
            )
        
        if password != confirm_password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Passwords do not match"}
            )
        
        # Create user
        user = create_user(db, username, email, password)
        
        if not user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Username or email already exists"}
            )
        
        return {
            "success": True,
            "message": "Registration successful! Please login.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    
    finally:
        db.close()

@app.post("/api/auth/login")
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    """Login user"""
    db = SessionLocal()
    try:
        user = authenticate_user(db, username, password)
        
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid username or password"}
            )
        
        # Create session
        session_token = generate_session_token()
        sessions[session_token] = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": datetime.utcnow()
        }
        
        return {
            "success": True,
            "message": "Login successful",
            "session_token": session_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    
    finally:
        db.close()

@app.post("/api/auth/logout")
async def logout(session_token: str = Form(...)):
    """Logout user"""
    if session_token in sessions:
        del sessions[session_token]
    
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user(session_token: str):
    """Get current user info"""
    if session_token not in sessions:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Not authenticated"}
        )
    
    return {
        "success": True,
        "user": sessions[session_token]
    }

# =============================
# Gate decision configs (ENV)
# =============================
FORCE_OPEN_ALWAYS = os.getenv("FORCE_OPEN_ALWAYS", "0") == "1"
GATE_TRIGGER_MODE = os.getenv("GATE_TRIGGER_MODE", "every_record")  # every_record | per_plate_cooldown
OPEN_COOLDOWN_SEC = int(os.getenv("OPEN_COOLDOWN_SEC", "10"))

# Debug: Print gate settings on startup
print(f"[GATE CONFIG] FORCE_OPEN_ALWAYS={FORCE_OPEN_ALWAYS}", flush=True)
print(f"[GATE CONFIG] GATE_TRIGGER_MODE={GATE_TRIGGER_MODE}", flush=True)
print(f"[GATE CONFIG] OPEN_COOLDOWN_SEC={OPEN_COOLDOWN_SEC}", flush=True)
ALLOWED_PREFIXES  = os.getenv("ALLOWED_PREFIXES", "").strip()  # ex: "กร,กต,กว"
PLATE_STRICT      = os.getenv("PLATE_STRICT", "0") == "1"

_recent_open_by_plate: dict[str, datetime] = {}  # {"plate_norm": datetime}

def _clean_text(s: str) -> str:
    return "".join(ch for ch in (s or "").strip() if ch not in "\r\n\t").strip()

def _normalize_plate(s: str) -> str:
    # เอาเว้นวรรค/ขีด/แท่งที่อาจกวนออก เพื่อเทียบ prefix/cooldown ได้
    return "".join(ch for ch in s if ch.isalnum())

def _allowed_by_prefix(plate_norm: str) -> bool:
    if not ALLOWED_PREFIXES:
        return True
    return any(plate_norm.startswith(p) for p in ALLOWED_PREFIXES.split(","))

def should_open(plate_text: str, conf: float | None) -> Tuple[bool, str]:
    """ตัดสินใจว่าจะเปิดไม้หรือไม่ ตาม ENV ที่ตั้งไว้"""
    if FORCE_OPEN_ALWAYS:
        print(f"[GATE DECISION] ✅ FORCE_OPEN_ALWAYS enabled", flush=True)
        return True, "force_open"

    if not plate_text or len(plate_text.strip()) < 2:
        print(f"[GATE DECISION] ❌ Empty or invalid plate text: '{plate_text}'", flush=True)
        return False, "empty_plate"

    plate_norm = _normalize_plate(plate_text)
    print(f"[GATE DECISION] Normalized plate: '{plate_norm}' from '{plate_text}'", flush=True)

    if PLATE_STRICT and not _allowed_by_prefix(plate_norm):
        print(f"[GATE DECISION] ❌ Prefix blocked: {plate_norm} not in {ALLOWED_PREFIXES}", flush=True)
        return False, f"prefix_blocked plate={plate_norm} allowed={ALLOWED_PREFIXES}"

    if GATE_TRIGGER_MODE == "every_record":
        print(f"[GATE DECISION] ✅ Mode: every_record - Opening gate", flush=True)
        return True, "every_record"

    if GATE_TRIGGER_MODE == "per_plate_cooldown":
        now = datetime.utcnow()
        last = _recent_open_by_plate.get(plate_norm)
        if last and (now - last) < timedelta(seconds=OPEN_COOLDOWN_SEC):
            left = OPEN_COOLDOWN_SEC - int((now - last).total_seconds())
            print(f"[GATE DECISION] ⏳ Cooldown active: {left}s remaining for plate {plate_norm}", flush=True)
            return False, f"cooldown({left}s) plate={plate_norm}"
        _recent_open_by_plate[plate_norm] = now
        print(f"[GATE DECISION] ✅ Cooldown OK - Opening gate for plate {plate_norm}", flush=True)
        return True, f"cooldown_ok plate={plate_norm}"

    print(f"[GATE DECISION] ❌ Unknown mode: {GATE_TRIGGER_MODE}", flush=True)
    return False, f"unknown_mode({GATE_TRIGGER_MODE})"

# =============================
# /detect: detector -> reader (+fallback OCR), save DB, THEN gate decision -> Arduino
# =============================
@app.post("/detect", response_model=PlateCreateResponse)
async def detect(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    session_token: str | None = Form(default=None)
):
    """
    Detect license plate from image or video file.
    Supports both image and video files - automatically detects file type.
    For videos, processes first frame with plate detected and opens gate.
    """
    if not file and not image_url:
        return JSONResponse(status_code=400, content={"detail": "Provide file or image_url"})
    
    # Check if uploaded file is a video
    is_video = False
    if file:
        content_type = file.content_type or ""
        file_extension = (file.filename or "").lower()
        is_video = content_type.startswith("video/") or any(file_extension.endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"])
        
        # If video file, process first frame with plate detected
        if is_video:
            data = await file.read()
            tmp_video_path = f"/tmp/{uuid4().hex}.mp4"
            with open(tmp_video_path, "wb") as f:
                f.write(data)
            
            try:
                cap = cv2.VideoCapture(tmp_video_path)
                if not cap.isOpened():
                    return JSONResponse(status_code=400, content={"detail": "Cannot open video file"})
                
                # Read first few frames to find one with a plate
                frame_count = 0
                max_frames_to_check = 30  # Check first 30 frames
                best_frame = None
                best_detection = None
                best_plate_text = ""
                best_conf = 0.0
                
                while frame_count < max_frames_to_check:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Try to detect plate in this frame
                    det_preds = infer_detector(frame)
                    if det_preds:
                        # Found a plate, process it
                        best_det = max(det_preds, key=lambda x: float(x.get("confidence", 0)))
                        x1, y1, x2, y2 = int(best_det["x1"]), int(best_det["y1"]), int(best_det["x2"]), int(best_det["y2"])
                        H, W = frame.shape[:2]
                        x1, y1 = max(0, min(x1, x2)), max(0, min(y1, y2))
                        x2, y2 = max(0, max(x1, x2)), max(0, max(y1, y2))
                        x1, y1, x2, y2 = min(x1, W-1), min(y1, H-1), min(x2, W), min(y2, H)
                        pad = int(0.05 * max(x2 - x1, y2 - y1))
                        x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
                        x2p, y2p = min(W, x2 + pad), min(H, y2 + pad)
                        crop = frame[y1p:y2p, x1p:x2p]
                        
                        rf = infer_reader(crop)
                        from .character_segmentation import read_plate_by_characters
                        plate_text, character_details = read_plate_by_characters(crop)
                        
                        if plate_text and len(plate_text) >= 2:
                            conf = float(best_det.get("confidence", 0))
                            if conf > best_conf:
                                best_frame = crop
                                best_detection = det_preds
                                best_plate_text = plate_text
                                best_conf = conf
                                break  # Found a good plate, use it
                    
                    frame_count += 1
                    # Skip frames
                    for _ in range(5):
                        cap.read()
                
                cap.release()
                
                if best_frame is None or not best_plate_text:
                    try: os.remove(tmp_video_path)
                    except: pass
                    return JSONResponse(status_code=400, content={"detail": "No license plate detected in video"})
                
                # Process the best frame found (similar to image detection)
                # Use the crop as the image for OCR
                img_for_ocr = best_frame
                used_crop = True
                image_source = tmp_video_path
                plate_text = best_plate_text
                det_preds = best_detection
                rf = infer_reader(img_for_ocr)
                
                # Continue with normal detection flow...
                # (จะใช้โค้ดเดิมต่อไป)
                
            except Exception as e:
                try: os.remove(tmp_video_path)
                except: pass
                return JSONResponse(status_code=500, content={"detail": f"Video processing error: {str(e)}"})

    # --- Prepare image source ---
    used_crop = False
    image_source = None
    if file:
        data = await file.read()  # async read OK
        tmp_path = f"/tmp/{uuid4().hex}_{file.filename or 'upload'}"
        with open(tmp_path, "wb") as f:
            f.write(data)
        image_source = tmp_path
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    else:
        image_source = image_url
        # Support both regular image URLs and MJPEG streams (like DroidCam)
        if "mjpegfeed" in image_url.lower() or "mjpeg" in image_url.lower():
            # MJPEG stream - use VideoCapture to get a frame
            cap = cv2.VideoCapture(image_url)
            if cap.isOpened():
                ret, img = cap.read()
                cap.release()
                if not ret or img is None:
                    return JSONResponse(status_code=400, content={"detail": "Cannot read frame from MJPEG stream"})
            else:
                return JSONResponse(status_code=400, content={"detail": "Cannot connect to MJPEG stream. Check IP and Port."})
        else:
            # Regular image URL
            try:
                import urllib.request
                resp = urllib.request.urlopen(image_url, timeout=5)
                arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            except Exception as e:
                return JSONResponse(status_code=400, content={"detail": f"Cannot fetch image from URL: {str(e)}"})

    if img is None:
        return JSONResponse(status_code=400, content={"detail": "Cannot read image"})

    H, W = img.shape[:2]

    # --- 1) Detector ---
    det_preds = infer_detector(img)
    try:
        print("DEBUG detector:",
              [(p.get("class"), round(float(p.get("confidence", 0)), 3)) for p in det_preds][:8],
              flush=True)
    except Exception as e:
        print("DEBUG detector print error:", e, flush=True)

    # --- Choose ROI for reader/OCR ---
    if det_preds:
        best_det = max(det_preds, key=lambda x: float(x.get("confidence", 0)))
        x1, y1, x2, y2 = int(best_det["x1"]), int(best_det["y1"]), int(best_det["x2"]), int(best_det["y2"])
        # sanitize
        x1, y1 = max(0, min(x1, x2)), max(0, min(y1, y2))
        x2, y2 = max(0, max(x1, x2)), max(0, max(y1, y2))
        x1, y1, x2, y2 = min(x1, W-1), min(y1, H-1), min(x2, W), min(y2, H)
        # 5% padding helps OCR
        pad = int(0.05 * max(x2 - x1, y2 - y1))
        x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
        x2p, y2p = min(W, x2 + pad), min(H, y2 + pad)
        crop = img[y1p:y2p, x1p:x2p]
        img_for_ocr = crop
        used_crop = True
    else:
        best_det = None
        img_for_ocr = img

    # DEBUG save crop
    try:
        debug_path = f"/tmp/ocr_crop_{uuid4().hex}.png"
        cv2.imwrite(debug_path, img_for_ocr)
        print("DEBUG saved crop:", debug_path, flush=True)
    except Exception as e:
        print("DEBUG save crop error:", e, flush=True)

    # --- 2) Reader on ROI ---
    rf = infer_reader(img_for_ocr)
    try:
        print("DEBUG reader preds:",
              [(p.get("class") or p.get("name"),
                round(float(p.get("confidence", p.get("conf", 0))), 3))
               for p in rf.get("predictions", [])][:12],
              flush=True)
    except Exception as e:
        print("DEBUG reader print error:", e, flush=True)

    preds = rf.get("predictions", [])
    
    # --- Character Segmentation + OCR แต่ละตัวอักษร ---
    plate_text = ""
    province_text = ""
    conf = None
    character_details = []
    
    # Get confidence from reader model (refined detection)
    if preds:
        try:
            conf = float(sum([float(p.get("confidence", 0)) for p in preds]) / len(preds))
        except Exception:
            conf = None
    
    # Use full OCR directly (skip character segmentation to avoid incorrect readings)
    try:
        h_, w_ = img_for_ocr.shape[:2]
        plate_text = _clean_text(run_ocr_on_bbox(img_for_ocr, 0, 0, w_, h_))
        print(f"DEBUG Full OCR result: {plate_text}", flush=True)
    except Exception as ocr_error:
        print(f"DEBUG OCR error: {ocr_error}", flush=True)
        plate_text = ""

    # --- Parse province from plate_text ---
    if plate_text and not province_text:
        parsed = parse_plate(plate_text)
        if parsed["province_code"]:
            province_text = parsed["province_name"]
            plate_text = parsed["formatted_text"]  # จัดรูปแบบให้สวย
        print(f"DEBUG parsed plate: {parsed}", flush=True)

    # --- Backfill conf from detector if missing ---
    if conf is None and best_det is not None:
        try:
            conf = float(best_det.get("confidence", 0.0))
        except Exception:
            conf = None

    # --- Save cropped plate image ---
    plate_img_filename = None
    if img_for_ocr is not None and img_for_ocr.size > 0:
        plate_img_filename = f"plate_{uuid4().hex}.jpg"
        plate_img_path = f"uploads/plates/{plate_img_filename}"
        cv2.imwrite(plate_img_path, img_for_ocr)
    
    # --- Check if plate has been seen before ---
    db = SessionLocal()
    try:
        normalized_plate = _normalize_plate(plate_text or "")
        is_new_plate = True
        seen_count = 1
        first_seen_at = datetime.utcnow()
        duplicate_records = []
        
        if normalized_plate:
            # Find all existing records with same normalized plate
            existing_records = db.query(PlateRecord).filter(
                func.replace(func.replace(PlateRecord.plate_text, " ", ""), "-", "") == normalized_plate
            ).order_by(PlateRecord.created_at.asc()).all()
            
            if existing_records:
                is_new_plate = False
                first_seen_at = existing_records[0].first_seen_at or existing_records[0].created_at
                seen_count = len(existing_records) + 1
                
                # Collect duplicate record information
                for dup_rec in existing_records:
                    duplicate_records.append({
                        "id": dup_rec.id,
                        "plate_text": dup_rec.plate_text,
                        "plate_image": f"/uploads/plates/{dup_rec.plate_image_path}" if dup_rec.plate_image_path else None,
                        "confidence": dup_rec.confidence,
                        "created_at": dup_rec.created_at.isoformat() if dup_rec.created_at else None,
                        "first_seen_at": (dup_rec.first_seen_at or dup_rec.created_at).isoformat() if (dup_rec.first_seen_at or dup_rec.created_at) else None
                    })
        
        # --- Get user_id and role from session ---
        user_id = None
        is_admin = False
        if session_token and session_token in sessions:
            user_id = sessions[session_token].get("id")
            is_admin = sessions[session_token].get("role") == "admin"
        
        # --- Save DB ---
        rec = PlateRecord(
            user_id=user_id,  # Save user_id who uploaded this record
            plate_text=plate_text or "",
            province_text=province_text or "",
            confidence=conf,
            image_path=(image_source if not used_crop else f"{image_source}#crop"),
            plate_image_path=plate_img_filename,
            detections_json=json.dumps({
                "reader": rf, 
                "detector": det_preds[:5],
                "character_details": character_details
            }, ensure_ascii=False),
            is_new_plate=is_new_plate,
            seen_count=seen_count,
            first_seen_at=first_seen_at
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        print(f"[DB] ✅ Record saved to database: ID={rec.id}, plate_text='{plate_text}', is_new_plate={is_new_plate}", flush=True)
    except Exception as db_error:
        db.rollback()
        print(f"[DB] ❌ Failed to save record: {db_error}", flush=True)
        raise
    finally:
        db.close()
    
    # --- Broadcast via WebSocket ---
    await manager.broadcast({
        "type": "detection",
        "plate_text": plate_text or "",
        "province_text": province_text or "",
        "confidence": conf,
        "timestamp": datetime.utcnow().isoformat()
    })

    # --- AFTER database save: Decide & trigger Arduino (only for admin) ---
    gate_opened = False
    print(f"[GATE] ════════════════════════════════════════════════════════", flush=True)
    print(f"[GATE] Database saved successfully. Checking gate control...", flush=True)
    print(f"[GATE] Admin status: is_admin={is_admin}, user_id={user_id}, session_token={'present' if session_token else 'missing'}", flush=True)
    print(f"[GATE] Plate info: plate_text='{plate_text}', confidence={conf}, record_id={rec.id}", flush=True)
    
    # Only open gate if:
    # 1. User is admin
    # 2. Plate text is valid (not empty, length >= 2)
    # 3. Record was successfully saved to database
    if is_admin and plate_text and len(plate_text.strip()) >= 2:
        ok, reason = should_open(plate_text or "", conf)
        print(f"[GATE] Decision: ok={ok}, reason={reason}", flush=True)

        if ok:
            try:
                print("[GATE] 🚪 Admin user - Opening gate AFTER database save...", flush=True)
                print(f"[GATE] Record ID {rec.id} saved. Plate: '{plate_text}'", flush=True)
                print("[SERIAL] → Sending OPEN command to Arduino", flush=True)
                success = send_open_gate(plate_text or "")
                if success:
                    gate_opened = True
                    print(f"[GATE] ✅ Gate opened successfully for plate: {plate_text} (Record ID: {rec.id})", flush=True)
                    await manager.broadcast({
                        "type": "gate",
                        "action": "opened",
                        "plate_text": plate_text or "",
                        "record_id": rec.id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    print(f"[GATE] ⚠️ Gate command sent but no ACK received from Arduino", flush=True)
                    print(f"[GATE] ⚠️ Check: 1) Arduino is connected, 2) SERIAL_ENABLED=true, 3) SERIAL_PORT is correct", flush=True)
            except Exception as e:
                # อย่าให้ API พังถ้า serial ล้มเหลว
                print(f"[GATE] ❌ WARN serial error: {e}", flush=True)
                import traceback
                print(f"[GATE] Traceback: {traceback.format_exc()}", flush=True)
        else:
            print(f"[GATE] ⚠️ Gate decision: NOT opening (reason: {reason})", flush=True)
    elif not is_admin:
        print(f"[GATE] ⚠️ User is not admin (role: {sessions.get(session_token, {}).get('role', 'unknown') if session_token else 'no session'}), gate will not open", flush=True)
    elif not plate_text or len(plate_text.strip()) < 2:
        print(f"[GATE] ⚠️ Invalid plate text: '{plate_text}', gate will not open", flush=True)
    print(f"[GATE] ════════════════════════════════════════════════════════", flush=True)

    # --- Prepare response data ---
    # Only send duplicate_records for admin users
    response_data = {
        "id": rec.id,
        "plate_text": plate_text or "",
        "province_text": province_text or "",
        "confidence": conf,
        "is_new_plate": is_new_plate,
        "seen_count": seen_count,
        "duplicate_records": duplicate_records if (duplicate_records and is_admin) else None,
        "plate_image": f"/uploads/plates/{plate_img_filename}" if plate_img_filename else None,
        "gate_opened": gate_opened
    }
    
    return PlateCreateResponse(**response_data)

# =============================
# /detect-video (optional)
# =============================
@app.post("/detect-video")
async def detect_video(
    file: UploadFile | None = File(default=None),
    video_url: str | None = Form(default=None),
    frame_stride: int = int(os.getenv("VIDEO_FRAME_STRIDE", "30")),  # Increased from 10 to 30 for faster processing
    max_frames: int = int(os.getenv("VIDEO_MAX_FRAMES", "300")),  # Reduced from 600 to 300
    open_gate_first: bool = os.getenv("VIDEO_OPEN_GATE_FIRST", "true").lower() == "true",
    session_token: str | None = Form(default=None)
):
    if not file and not video_url:
        return JSONResponse(status_code=400, content={"detail": "Provide video file or video_url"})

    local_video_path = None
    if file:
        data = await file.read()
        local_video_path = f"/tmp/{uuid4().hex}.mp4"
        with open(local_video_path, "wb") as f:
            f.write(data)
        cap_source = local_video_path
        image_path_for_db = local_video_path
    else:
        cap_source = video_url
        image_path_for_db = video_url

    cap = cv2.VideoCapture(cap_source)
    if not cap.isOpened() and video_url:
        try:
            import urllib.request
            tmpv = f"/tmp/{uuid4().hex}.mp4"
            urllib.request.urlretrieve(video_url, tmpv)
            cap = cv2.VideoCapture(tmpv)
            if not cap.isOpened():
                return JSONResponse(status_code=400, content={"detail": "Cannot open video"})
            local_video_path = tmpv
        except Exception as e:
            return JSONResponse(status_code=400, content={"detail": f"Cannot fetch video: {e}"})
    elif not cap.isOpened():
        return JSONResponse(status_code=400, content={"detail": "Cannot open video"})

    seen_plates: Set[str] = set()
    saved_ids: List[int] = []
    plate_details: dict = {}  # Store plate details with duplicate info: {plate_text: {"is_new": bool, "duplicate_records": list, "seen_count": int}}
    duplicate_cache: dict = {}  # Cache duplicate check results: {normalized_plate: {"is_new": bool, "duplicate_records": list, "seen_count": int, "first_seen_at": datetime}}
    session_id = uuid4().hex

    i = 0
    processed = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        i += 1
        if i % max(1, frame_stride) != 0:
            continue
        processed += 1
        if processed > max_frames:
            break

        tmp_img_path = f"/tmp/frame_{session_id}_{i}.jpg"
        cv2.imwrite(tmp_img_path, frame)

        try:
            # Use local models instead of roboflow
            frame_img = cv2.imread(tmp_img_path)
            if frame_img is None:
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            # 1) Detector
            det_preds = infer_detector(frame_img)
            if not det_preds:
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            # 2) Reader
            best_det = max(det_preds, key=lambda x: float(x.get("confidence", 0)))
            x1, y1, x2, y2 = int(best_det["x1"]), int(best_det["y1"]), int(best_det["x2"]), int(best_det["y2"])
            
            # Sanitize and add padding
            H, W = frame_img.shape[:2]
            x1, y1 = max(0, min(x1, x2)), max(0, min(y1, y2))
            x2, y2 = max(0, max(x1, x2)), max(0, max(y1, y2))
            x1, y1, x2, y2 = min(x1, W-1), min(y1, H-1), min(x2, W), min(y2, H)
            
            pad = int(0.05 * max(x2 - x1, y2 - y1))
            x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
            x2p, y2p = min(W, x2 + pad), min(H, y2 + pad)
            crop = frame_img[y1p:y2p, x1p:x2p]
            
            rf = infer_reader(crop)
        except Exception as e:
            print(f"DEBUG video processing error: {e}", flush=True)
            try: os.remove(tmp_img_path)
            except: pass
            continue

        # --- 3) Character Segmentation + OCR ---
        preds = rf.get("predictions", [])
        plate_text, province_text = "", ""
        conf = None
        character_details = []
        
        # Get confidence from reader model
        if preds:
            try:
                conf = float(sum([float(p.get("confidence", 0)) for p in preds]) / len(preds))
            except Exception:
                conf = None
        
        # Use Character Segmentation (แยกตัวอักษรทีละตัว)
        if crop.size > 0:
            try:
                from .character_segmentation import read_plate_by_characters
                segmented_text, character_details = read_plate_by_characters(crop)
                
                if segmented_text and len(segmented_text) >= 2:
                    plate_text = segmented_text
                    print(f"DEBUG video Character Segmentation: {plate_text} ({len(character_details)} chars)", flush=True)
                else:
                    # Fallback to full OCR
                    plate_text = _clean_text(run_ocr_on_bbox(crop, 0, 0, crop.shape[1], crop.shape[0]))
                    print(f"DEBUG video Fallback OCR: {plate_text}", flush=True)
                
                # Parse province from plate text
                if plate_text:
                    parsed = parse_plate(plate_text)
                    if parsed["province_code"]:
                        province_text = parsed["province_name"]
                        plate_text = parsed["formatted_text"]
                    print(f"DEBUG video parsed: {plate_text}, Province: {province_text}", flush=True)
            except Exception as e:
                print(f"DEBUG video OCR error: {e}, trying fallback", flush=True)
                try:
                    plate_text = _clean_text(run_ocr_on_bbox(crop, 0, 0, crop.shape[1], crop.shape[0]))
                except Exception as e2:
                    print(f"DEBUG video fallback OCR also failed: {e2}", flush=True)
        
        # Skip if no text detected
        if not plate_text or len(plate_text) < 2:
            try: os.remove(tmp_img_path)
            except: pass
            continue

        # --- Check if plate has been seen before (for duplicate tracking) ---
        normalized_plate = _normalize_plate(plate_text)
        is_new_plate = True
        seen_count = 1
        first_seen_at = datetime.utcnow()
        duplicate_records = []
        
        # Use cache to avoid repeated database queries for the same plate (OPTIMIZATION)
        if normalized_plate and normalized_plate in duplicate_cache:
            cached = duplicate_cache[normalized_plate]
            is_new_plate = cached["is_new_plate"]
            seen_count = cached["seen_count"] + 1  # Increment for this detection
            first_seen_at = cached["first_seen_at"]
            duplicate_records = cached["duplicate_records"].copy() if cached["duplicate_records"] else []
        elif normalized_plate:
            # Only query database once per unique plate (OPTIMIZATION)
            db_check = SessionLocal()
            try:
                # Find all existing records with same normalized plate
                existing_records = db_check.query(PlateRecord).filter(
                    func.replace(func.replace(PlateRecord.plate_text, " ", ""), "-", "") == normalized_plate
                ).order_by(PlateRecord.created_at.asc()).all()
                
                if existing_records:
                    is_new_plate = False
                    first_seen_at = existing_records[0].first_seen_at or existing_records[0].created_at
                    seen_count = len(existing_records) + 1
                    
                    # Collect duplicate record information (limit to first 10 for performance)
                    for dup_rec in existing_records[:10]:
                        duplicate_records.append({
                            "id": dup_rec.id,
                            "plate_text": dup_rec.plate_text,
                            "plate_image": f"/uploads/plates/{dup_rec.plate_image_path}" if dup_rec.plate_image_path else None,
                            "confidence": dup_rec.confidence,
                            "created_at": dup_rec.created_at.isoformat() if dup_rec.created_at else None,
                            "first_seen_at": (dup_rec.first_seen_at or dup_rec.created_at).isoformat() if (dup_rec.first_seen_at or dup_rec.created_at) else None
                        })
                else:
                    is_new_plate = True
                    seen_count = 1
                    first_seen_at = datetime.utcnow()
                
                # Cache the result to avoid repeated queries
                duplicate_cache[normalized_plate] = {
                    "is_new_plate": is_new_plate,
                    "seen_count": len(existing_records) if existing_records else 0,
                    "duplicate_records": duplicate_records.copy(),
                    "first_seen_at": first_seen_at
                }
            finally:
                db_check.close()

        # --- Save cropped plate image from video ---
        plate_img_filename = None
        if crop is not None and crop.size > 0:
            plate_img_filename = f"plate_{uuid4().hex}.jpg"
            plate_img_path = f"uploads/plates/{plate_img_filename}"
            cv2.imwrite(plate_img_path, crop)
        
        # --- Get user_id and role from session ---
        user_id = None
        is_admin = False
        if session_token and session_token in sessions:
            user_id = sessions[session_token].get("id")
            is_admin = sessions[session_token].get("role") == "admin"
        
        db = SessionLocal()
        try:
            rec = PlateRecord(
                user_id=user_id,  # Save user_id who uploaded this record
                plate_text=plate_text,
                province_text=province_text,
                confidence=conf,
                image_path=f"{image_path_for_db}#frame={i}",
                plate_image_path=plate_img_filename,
                detections_json=json.dumps({"frame_index": i, "rf": rf}, ensure_ascii=False),
                is_new_plate=is_new_plate,
                seen_count=seen_count,
                first_seen_at=first_seen_at
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            saved_ids.append(rec.id)
            print(f"[DB(video)] ✅ Record saved to database: ID={rec.id}, plate_text='{plate_text}', is_new_plate={is_new_plate}", flush=True)
            
            # Store plate details for response (only for first occurrence of each plate)
            if plate_text not in seen_plates:
                plate_details[plate_text] = {
                    "is_new_plate": is_new_plate,
                    "seen_count": seen_count,
                    "duplicate_records": duplicate_records if is_admin else None,  # Only include for admin
                    "plate_image": f"/uploads/plates/{plate_img_filename}" if plate_img_filename else None,
                    "confidence": conf
                }
                seen_plates.add(plate_text)
        except Exception as db_error:
            db.rollback()
            print(f"[DB(video)] ❌ Failed to save record: {db_error}", flush=True)
            raise
        finally:
            db.close()
        
        # --- Broadcast via WebSocket ---
        await manager.broadcast({
            "type": "detection",
            "plate_text": plate_text,
            "province_text": province_text,
            "confidence": conf,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "video"
        })

        # --- AFTER database save: Only check gate for first occurrence of each plate (only for admin) ---
        if is_admin and open_gate_first and (plate_text not in seen_plates) and plate_text and len(plate_text.strip()) >= 2:
            print(f"[GATE(video)] ════════════════════════════════════════════════════════", flush=True)
            print(f"[GATE(video)] Database saved successfully. Checking gate control...", flush=True)
            print(f"[GATE(video)] Record ID: {rec.id}, Plate: '{plate_text}', Confidence: {conf}", flush=True)
            
            ok, reason = should_open(plate_text, conf)
            print(f"[GATE(video)] Decision: ok={ok}, reason={reason}", flush=True)
            
            if ok:
                try:
                    print("[GATE(video)] 🚪 Admin user - Opening gate AFTER database save...", flush=True)
                    print(f"[GATE(video)] Record ID {rec.id} saved. Plate: '{plate_text}'", flush=True)
                    print("[SERIAL(video)] → Sending OPEN command to Arduino", flush=True)
                    success = send_open_gate(plate_text)
                    if success:
                        print(f"[GATE(video)] ✅ Gate opened successfully for plate: {plate_text} (Record ID: {rec.id})", flush=True)
                    else:
                        print(f"[GATE(video)] ⚠️ Gate command sent but no ACK received", flush=True)
                        print(f"[GATE(video)] ⚠️ Check: 1) Arduino is connected, 2) SERIAL_ENABLED=true, 3) SERIAL_PORT is correct", flush=True)
                except Exception as e:
                    print(f"[GATE(video)] ❌ WARN serial error: {e}", flush=True)
                    import traceback
                    print(f"[GATE(video)] Traceback: {traceback.format_exc()}", flush=True)
            else:
                print(f"[GATE(video)] ⚠️ Gate decision: NOT opening (reason: {reason})", flush=True)
            print(f"[GATE(video)] ════════════════════════════════════════════════════════", flush=True)
        elif not is_admin:
            print(f"[GATE(video)] ⚠️ User is not admin, gate will not open", flush=True)
        elif not plate_text or len(plate_text.strip()) < 2:
            print(f"[GATE(video)] ⚠️ Invalid plate text: '{plate_text}', gate will not open", flush=True)

        try: os.remove(tmp_img_path)
        except: pass

    cap.release()
    if local_video_path:
        try: os.remove(local_video_path)
        except: pass

    # Get admin status from session (check once at the end)
    is_admin_user = False
    if session_token and session_token in sessions:
        is_admin_user = sessions[session_token].get("role") == "admin"
    
    # Build plate details list with duplicate information (only for admin)
    plates_with_details = []
    for plate_text in sorted(seen_plates):
        if plate_text in plate_details:
            plate_detail = plate_details[plate_text]
            plates_with_details.append({
                "plate_text": plate_text,
                "is_new_plate": plate_detail["is_new_plate"],
                "seen_count": plate_detail["seen_count"],
                "duplicate_records": plate_detail["duplicate_records"] if is_admin_user else None,
                "plate_image": plate_detail["plate_image"],
                "confidence": plate_detail["confidence"]
            })
        else:
            # Fallback if plate not in details
            plates_with_details.append({
                "plate_text": plate_text,
                "is_new_plate": True,
                "seen_count": 1,
                "duplicate_records": None,
                "plate_image": None,
                "confidence": None
            })
    
    return {
        "session_id": session_id,
        "frames_processed": processed,
        "unique_plates": sorted(list(seen_plates)),
        "records_saved": len(saved_ids),
        "sample_record_ids": saved_ids[:10],
        "plates_with_details": plates_with_details
    }

# =============================
# WebSocket endpoint
# =============================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"type": "pong", "message": "Connected"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# =============================
# Web UI endpoints
# =============================
@app.get("/", response_class=FileResponse)
async def serve_index():
    return "static/index.html"

# =============================
# API endpoints for frontend
# =============================
@app.get("/api/records")
async def get_records(
    page: int = 1, 
    limit: int = 20, 
    session_token: str | None = None,
    db: Session = Depends(get_db)
):
    """Get paginated records - User sees only their own records, Admin sees all"""
    offset = (page - 1) * limit
    
    # Get current user from session
    user_id = None
    is_admin = False
    if session_token and session_token in sessions:
        user_info = sessions[session_token]
        user_id = user_info.get("id")
        is_admin = user_info.get("role") == "admin"
    
    # Build query - filter by user_id if not admin
    query = db.query(PlateRecord)
    if not is_admin and user_id:
        # User: only see their own records
        query = query.filter(PlateRecord.user_id == user_id)
    # Admin: see all records (no filter)
    
    records = query.order_by(desc(PlateRecord.created_at)).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "records": [
            {
                "id": r.id,
                "plate_text": r.plate_text,
                "province_text": r.province_text,
                "confidence": r.confidence,
                "plate_image": f"/uploads/plates/{r.plate_image_path}" if r.plate_image_path else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "is_new_plate": getattr(r, 'is_new_plate', True),
                "seen_count": getattr(r, 'seen_count', 1)
            }
            for r in records
        ],
        "total": total,
        "page": page,
        "limit": limit
    }

@app.get("/api/records/{record_id}")
async def get_record(record_id: int, db: Session = Depends(get_db)):
    """Get single record details"""
    record = db.query(PlateRecord).filter(PlateRecord.id == record_id).first()
    
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Record not found"})
    
    return {
        "id": record.id,
        "plate_text": record.plate_text,
        "province_text": record.province_text,
        "confidence": record.confidence,
        "image_path": record.image_path,
        "detections_json": record.detections_json,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }

@app.get("/api/stats")
async def get_stats(
    session_token: str | None = None,
    db: Session = Depends(get_db)
):
    """Get statistics - User sees only their own stats, Admin sees all"""
    try:
        # Get current user from session
        user_id = None
        is_admin = False
        if session_token and session_token in sessions:
            user_info = sessions[session_token]
            user_id = user_info.get("id")
            is_admin = user_info.get("role") == "admin"
        
        # Build query - filter by user_id if not admin
        base_query = db.query(PlateRecord)
        if not is_admin and user_id:
            # User: only see their own records
            base_query = base_query.filter(PlateRecord.user_id == user_id)
        # Admin: see all records (no filter)
        
        total_records = base_query.count()
        
        # Today's records
        today = datetime.utcnow().date()
        today_query = base_query.filter(func.date(PlateRecord.created_at) == today)
        today_records = today_query.count()
        
        # Average confidence
        avg_confidence = base_query.with_entities(func.avg(PlateRecord.confidence)).scalar()
        
        return {
            "total_records": total_records or 0,
            "today_records": today_records or 0,
            "avg_confidence": float(avg_confidence) if avg_confidence else 0
        }
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return {
            "total_records": 0,
            "today_records": 0,
            "avg_confidence": 0
        }

@app.post("/api/gate/test")
async def test_gate():
    """Test gate open command"""
    try:
        from .arduino import SERIAL_ENABLED, SERIAL_PORT, ping_arduino
        
        # Check if serial is enabled
        if not SERIAL_ENABLED:
            return JSONResponse(
                status_code=400, 
                content={"detail": "Serial communication is disabled. Set SERIAL_ENABLED=true"}
            )
        
        # Test connection first
        print(f"[GATE TEST] Testing connection to {SERIAL_PORT}...", flush=True)
        if not ping_arduino():
            return JSONResponse(
                status_code=500,
                content={"detail": f"Arduino not responding. Check connection to {SERIAL_PORT}"}
            )
        
        # Send open command
        success = send_open_gate("TEST")
        if success:
            await manager.broadcast({
                "type": "gate",
                "action": "opened",
                "plate_text": "TEST"
            })
            return {"message": "Test command sent successfully", "arduino_ack": True}
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": "Gate command sent but no ACK received from Arduino"}
            )
    except Exception as e:
        import traceback
        print(f"[GATE TEST] Error: {e}\n{traceback.format_exc()}", flush=True)
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/gate/close")
async def close_gate():
    """Force close gate"""
    try:
        # Send close command to Arduino
        from .arduino import send_command
        send_command("CLOSE")
        await manager.broadcast({
            "type": "gate",
            "action": "closed",
            "plate_text": ""
        })
        return {"message": "Close command sent successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/api/plates/status")
async def get_plate_status(db: Session = Depends(get_db)):
    """Get plate status counts (new vs duplicate)"""
    
    # Count new plates (is_new_plate = True)
    new_plates_count = db.query(func.count(PlateRecord.id)).filter(
        PlateRecord.is_new_plate == True
    ).scalar() or 0
    
    # Count duplicate plates (is_new_plate = False)
    duplicate_plates_count = db.query(func.count(PlateRecord.id)).filter(
        PlateRecord.is_new_plate == False
    ).scalar() or 0
    
    # Total unique plates (plates where seen_count = 1 or first_seen_at matches)
    total_plates = db.query(func.count(func.distinct(PlateRecord.plate_text))).filter(
        PlateRecord.plate_text != ""
    ).scalar() or 0
    
    # Get new plates (first occurrence only)
    new_plates = db.query(PlateRecord).filter(
        PlateRecord.is_new_plate == True
    ).order_by(desc(PlateRecord.created_at)).limit(50).all()
    
    # Get duplicate plates (recent duplicates)
    duplicate_plates = db.query(PlateRecord).filter(
        PlateRecord.is_new_plate == False
    ).order_by(desc(PlateRecord.created_at)).limit(50).all()
    
    return {
        "new_plates_count": new_plates_count,
        "duplicate_plates_count": duplicate_plates_count,
        "total_unique_plates": total_plates,
        "new_plates": [
            {
                "id": r.id,
                "plate_text": r.plate_text,
                "province_text": r.province_text,
                "confidence": r.confidence,
                "plate_image": f"/uploads/plates/{r.plate_image_path}" if r.plate_image_path else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "seen_count": getattr(r, 'seen_count', 1)
            }
            for r in new_plates
        ],
        "duplicate_plates": [
            {
                "id": r.id,
                "plate_text": r.plate_text,
                "province_text": r.province_text,
                "confidence": r.confidence,
                "plate_image": f"/uploads/plates/{r.plate_image_path}" if r.plate_image_path else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "seen_count": getattr(r, 'seen_count', 1)
            }
            for r in duplicate_plates
        ]
    }

@app.post("/api/settings")
async def save_settings(settings: dict):
    """Save system settings"""
    # In production, save to database or config file
    # For now, just return success
    return {"message": "Settings saved successfully", "settings": settings}

@app.get("/api/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    """Export records as CSV"""
    import io
    import csv
    records = db.query(PlateRecord).order_by(desc(PlateRecord.created_at)).limit(1000).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Plate Text', 'Province', 'Confidence', 'Created At'])
    
    for r in records:
        writer.writerow([
            r.id,
            r.plate_text,
            r.province_text,
            r.confidence,
            r.created_at.isoformat() if r.created_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=records.csv"}
    )

@app.delete("/api/records/clear-old")
async def clear_old_records(days: int = 30, db: Session = Depends(get_db)):
    """Clear records older than specified days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(PlateRecord).filter(PlateRecord.created_at < cutoff_date).delete()
        db.commit()
        return {"message": f"Deleted {deleted} records", "deleted_count": deleted}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail": str(e)})

# =============================
# Modified detect endpoint to broadcast via WebSocket
# =============================
# Update the existing /detect endpoint to broadcast detections
# (This would be done by adding broadcast calls after detection)

# =============================
# Uvicorn entry
# =============================
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
    )
