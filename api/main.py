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
SESSION_EXPIRY_HOURS = 24  # Session expires after 24 hours

def cleanup_expired_sessions():
    """Remove expired sessions"""
    now = datetime.utcnow()
    expired_tokens = [
        token for token, session_data in sessions.items()
        if (now - session_data.get("created_at", now)).total_seconds() > SESSION_EXPIRY_HOURS * 3600
    ]
    for token in expired_tokens:
        del sessions[token]

def get_session_user(session_token: str):
    """Get user from session token"""
    cleanup_expired_sessions()
    if session_token not in sessions:
        return None
    return sessions[session_token]

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
    cleanup_expired_sessions()
    user_data = get_session_user(session_token)
    
    if not user_data:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Not authenticated or session expired"}
        )
    
    return {
        "success": True,
        "user": user_data
    }

# =============================
# Gate decision configs (ENV)
# =============================
FORCE_OPEN_ALWAYS = os.getenv("FORCE_OPEN_ALWAYS", "0") == "1"
GATE_TRIGGER_MODE = os.getenv("GATE_TRIGGER_MODE", "every_record")  # every_record | per_plate_cooldown
OPEN_COOLDOWN_SEC = int(os.getenv("OPEN_COOLDOWN_SEC", "10"))
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
        return True, "force_open"

    if not plate_text:
        return False, "empty_plate"

    plate_norm = _normalize_plate(plate_text)

    if PLATE_STRICT and not _allowed_by_prefix(plate_norm):
        return False, f"prefix_blocked plate={plate_norm} allowed={ALLOWED_PREFIXES}"

    if GATE_TRIGGER_MODE == "every_record":
        return True, "every_record"

    if GATE_TRIGGER_MODE == "per_plate_cooldown":
        now = datetime.utcnow()
        last = _recent_open_by_plate.get(plate_norm)
        if last and (now - last) < timedelta(seconds=OPEN_COOLDOWN_SEC):
            left = OPEN_COOLDOWN_SEC - int((now - last).total_seconds())
            return False, f"cooldown({left}s) plate={plate_norm}"
        _recent_open_by_plate[plate_norm] = now
        return True, f"cooldown_ok plate={plate_norm}"

    return False, f"unknown_mode({GATE_TRIGGER_MODE})"

# =============================
# /detect: detector -> reader (+fallback OCR), save DB, THEN gate decision -> Arduino
# =============================
@app.post("/detect", response_model=PlateCreateResponse)
async def detect(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None)
):
    if not file and not image_url:
        return JSONResponse(status_code=400, content={"detail": "Provide file or image_url"})

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
    
    # Resize image if too large to speed up processing (max 1920px width)
    MAX_WIDTH = 1920
    if W > MAX_WIDTH:
        scale = MAX_WIDTH / W
        new_h = int(H * scale)
        new_w = MAX_WIDTH
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        H, W = img.shape[:2]
        print(f"DEBUG: Resized image from {W}x{H} to {new_w}x{new_h} for faster processing", flush=True)

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

    # DEBUG save crop (disabled for performance - enable only when debugging)
    # try:
    #     debug_path = f"/tmp/ocr_crop_{uuid4().hex}.png"
    #     cv2.imwrite(debug_path, img_for_ocr)
    #     print("DEBUG saved crop:", debug_path, flush=True)
    # except Exception as e:
    #     print("DEBUG save crop error:", e, flush=True)

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
    
    # --- Reader-first pipeline: ใช้ผลจาก Reader Model เรียงตัวอักษรทีละตัว ---
    plate_text = ""
    province_text = ""
    conf = None
    character_details = []
    
    def _build_plate_from_reader(preds_list):
        """เรียงตัวอักษรตามตำแหน่งและรวมเป็นข้อความแบบเป็นแถว"""
        if not preds_list:
            return "", [], None
        
        try:
            filtered = [p for p in preds_list if float(p.get("confidence", 0)) >= 0.35]
            if not filtered:
                return "", [], None
            
            # ประเมินความสูงเฉลี่ยเพื่อใช้ threshold แยกแถว
            heights = []
            for p in filtered:
                y1, y2 = p.get("y1"), p.get("y2")
                if y1 is not None and y2 is not None:
                    heights.append(abs(float(y2) - float(y1)))
            avg_h = sum(heights) / len(heights) if heights else 40.0
            row_thresh = max(20.0, avg_h * 0.6)  # ยืดหยุ่นตามขนาดตัวอักษร
            
            # จัดกลุ่มตามแถว (y)
            rows: dict[float, list] = {}
            for p in filtered:
                y = float(p.get("y", 0))
                found = False
                for row_y in sorted(rows.keys()):
                    if abs(y - row_y) < row_thresh:
                        rows[row_y].append(p)
                        found = True
                        break
                if not found:
                    rows[y] = [p]
            
            # เรียงแถวบนลงล่าง และซ้ายไปขวา
            character_details_local = []
            row_texts = []
            for row_y in sorted(rows.keys()):
                row = rows[row_y]
                row.sort(key=lambda p: float(p.get("x", 0)))
                row_chars = []
                for p in row:
                    char_cls = (p.get("class") or p.get("name") or "").strip()
                    c_conf = float(p.get("confidence", p.get("conf", 0)) or 0)
                    if not char_cls:
                        continue
                    row_chars.append(char_cls)
                    character_details_local.append({
                        "character": char_cls,
                        "confidence": c_conf,
                        "bbox": {
                            "x1": p.get("x1"), "y1": p.get("y1"),
                            "x2": p.get("x2"), "y2": p.get("y2"),
                        },
                        "method": "reader_model"
                    })
                if row_chars:
                    row_texts.append("".join(row_chars))
            
            full_text = " ".join(row_texts).strip()
            # ทำความสะอาดช่องว่างซ้ำ
            full_text = " ".join(full_text.split())
            
            avg_conf = None
            try:
                avg_conf = sum(d["confidence"] for d in character_details_local) / len(character_details_local) if character_details_local else None
            except Exception:
                avg_conf = None
            
            return full_text, character_details_local, avg_conf
        except Exception as e:
            print(f"DEBUG _build_plate_from_reader error: {e}", flush=True)
            return "", [], None
    
    # 1) ใช้ Reader Model ตรง
    if preds:
        plate_text, character_details, conf_reader = _build_plate_from_reader(preds)
        if conf is None and conf_reader is not None:
            conf = conf_reader
    
    # 2) Fallback Character Segmentation + OCR ถ้า reader ไม่ได้ผล
    if not plate_text or len(plate_text) < 2:
        try:
            from .character_segmentation import read_plate_by_characters
            segmented_text, character_details = read_plate_by_characters(img_for_ocr)
            if segmented_text and len(segmented_text) >= 2:
                plate_text = segmented_text
                print(f"DEBUG Character Segmentation result: {plate_text} ({len(character_details)} chars)", flush=True)
        except Exception as e:
            print(f"DEBUG Character segmentation error: {e}", flush=True)
    
    # 3) Fallback OCR เต็มป้าย ถ้ายังว่าง
    if not plate_text or len(plate_text) < 2:
        try:
            h_, w_ = img_for_ocr.shape[:2]
            plate_text = _clean_text(run_ocr_on_bbox(img_for_ocr, 0, 0, w_, h_))
            print(f"DEBUG OCR fallback result: {plate_text}", flush=True)
        except Exception as ocr_error:
            print(f"DEBUG OCR fallback error: {ocr_error}", flush=True)

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
    existing_plate = None
    rec_id = None
    is_new_plate = True
    seen_count = 1
    first_seen_at = datetime.utcnow()
    
    try:
        normalized_plate = _normalize_plate(plate_text or "")
        
        if normalized_plate:
            # Check if this plate (normalized) was seen before
            existing_plate = db.query(PlateRecord).filter(
                func.replace(func.replace(PlateRecord.plate_text, " ", ""), "-", "") == normalized_plate
            ).order_by(PlateRecord.created_at.asc()).first()
            
            if existing_plate:
                is_new_plate = False
                first_seen_at = existing_plate.first_seen_at or existing_plate.created_at
                # Count all records with same normalized plate
                seen_count = db.query(func.count(PlateRecord.id)).filter(
                    func.replace(func.replace(PlateRecord.plate_text, " ", ""), "-", "") == normalized_plate
                ).scalar() + 1
        
        # --- Save DB ---
        rec = PlateRecord(
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
        rec_id = rec.id
    except Exception as e:
        print(f"ERROR saving to database: {e}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        db.rollback()
    finally:
        db.close()
    
    if rec_id is None:
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to save record to database"}
        )
    
    # --- Get first seen record info if duplicate (for WebSocket) ---
    first_seen_info_ws = None
    if not is_new_plate and existing_plate:
        try:
            first_seen_at_str = None
            if existing_plate.first_seen_at:
                first_seen_at_str = existing_plate.first_seen_at.isoformat()
            elif existing_plate.created_at:
                first_seen_at_str = existing_plate.created_at.isoformat()
            
            first_seen_info_ws = {
                "id": existing_plate.id,
                "first_seen_at": first_seen_at_str,
                "first_seen_confidence": float(existing_plate.confidence) if existing_plate.confidence is not None else None
            }
        except Exception as e:
            print(f"ERROR creating first_seen_info_ws: {e}", flush=True)
    
    # --- Broadcast via WebSocket (with full detection info) ---
    await manager.broadcast({
        "type": "detection",
        "id": rec_id,
        "plate_text": plate_text or "",
        "province_text": province_text or "",
        "confidence": float(conf) if conf is not None else None,
        "is_new_plate": is_new_plate,
        "seen_count": seen_count,
        "first_seen_at": first_seen_at.isoformat() if isinstance(first_seen_at, datetime) else None,
        "first_seen_info": first_seen_info_ws,
        "timestamp": datetime.utcnow().isoformat()
    })

    # --- เปิด gate ทุกครั้งที่บันทึกข้อมูลสำเร็จ (ไม่ต้องเช็คเงื่อนไข) ---
    if plate_text and len(plate_text.strip()) > 0:
        print(f"[GATE] 🚀 Starting gate open process...", flush=True)
        print(f"[GATE] 🚀 Plate: '{plate_text}', Confidence: {conf}, New: {is_new_plate}, Seen: {seen_count}", flush=True)
        
        try:
            gate_success = send_open_gate(plate_text or "")
            print(f"[GATE] 🚀 Gate command result: {gate_success}", flush=True)
            
            # Broadcast gate event (always broadcast, even if gate failed)
            await manager.broadcast({
                "type": "gate",
                "action": "opened" if gate_success else "attempted",
                "plate_text": plate_text or "",
                "reason": "บันทึกข้อมูลสำเร็จ - เปิด gate ทุกครั้ง",
                "is_new_plate": is_new_plate,
                "seen_count": seen_count,
                "confidence": float(conf) if conf is not None else None,
                "gate_success": gate_success
            })
            
            if gate_success:
                print(f"[GATE] ✅ Gate opened successfully for plate: '{plate_text}'", flush=True)
            else:
                print(f"[GATE] ⚠️ Gate command sent but may not have opened. Check Arduino connection.", flush=True)
                
        except Exception as e:
            # อย่าให้ API พังถ้า serial ล้มเหลว
            print(f"[GATE] ❌ ERROR in gate control: {e}", flush=True)
            import traceback
            print(f"[GATE] Traceback: {traceback.format_exc()}", flush=True)
            await manager.broadcast({
                "type": "gate",
                "action": "error",
                "plate_text": plate_text or "",
                "error": str(e)
            })
    else:
        print(f"[GATE] ⚠️ Skipping gate open - no plate text detected", flush=True)

    # --- Get first seen record info if duplicate ---
    first_seen_info = None
    if not is_new_plate and existing_plate:
        try:
            first_seen_at_str = None
            if existing_plate.first_seen_at:
                first_seen_at_str = existing_plate.first_seen_at.isoformat()
            elif existing_plate.created_at:
                first_seen_at_str = existing_plate.created_at.isoformat()
            
            first_seen_info = {
                "id": existing_plate.id,
                "first_seen_at": first_seen_at_str,
                "first_seen_confidence": float(existing_plate.confidence) if existing_plate.confidence is not None else None
            }
        except Exception as e:
            print(f"ERROR creating first_seen_info: {e}", flush=True)
            first_seen_info = None
    
    # Format first_seen_at for response
    first_seen_at_str = None
    try:
        if isinstance(first_seen_at, datetime):
            first_seen_at_str = first_seen_at.isoformat()
        elif isinstance(first_seen_at, str):
            first_seen_at_str = first_seen_at
    except Exception as e:
        print(f"ERROR formatting first_seen_at: {e}", flush=True)
    
    response_data = {
        "id": rec_id,
        "plate_text": plate_text or "",
        "province_text": province_text or "",
        "confidence": float(conf) if conf is not None else None,
        "is_new_plate": is_new_plate,
        "seen_count": seen_count,
        "first_seen_at": first_seen_at_str,
        "first_seen_info": first_seen_info
    }
    
    try:
        return PlateCreateResponse(**response_data)
    except Exception as e:
        print(f"ERROR creating response: {e}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error creating response: {str(e)}"}
        )

# =============================
# /detect-video (optional)
# =============================
@app.post("/detect-video")
async def detect_video(
    file: UploadFile | None = File(default=None),
    video_url: str | None = Form(default=None),
    frame_stride: int = int(os.getenv("VIDEO_FRAME_STRIDE", "10")),
    max_frames: int = int(os.getenv("VIDEO_MAX_FRAMES", "600")),
    open_gate_first: bool = os.getenv("VIDEO_OPEN_GATE_FIRST", "true").lower() == "true"
):
    if not file and not video_url:
        return JSONResponse(status_code=400, content={"detail": "Provide video file or video_url"})

    local_video_path = None
    cap_source = None
    
    try:
        if file:
            # Get file extension from filename or content type
            filename = file.filename or "video"
            ext = os.path.splitext(filename)[1] or ".mp4"
            if ext not in [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]:
                ext = ".mp4"  # Default to mp4
            
            data = await file.read()
            if not data or len(data) == 0:
                return JSONResponse(status_code=400, content={"detail": "Empty video file"})
            
            local_video_path = f"/tmp/{uuid4().hex}{ext}"
            with open(local_video_path, "wb") as f:
                f.write(data)
            cap_source = local_video_path
            image_path_for_db = local_video_path
            print(f"DEBUG: Saved video file to {local_video_path} ({len(data)} bytes)", flush=True)
        else:
            cap_source = video_url
            image_path_for_db = video_url
            print(f"DEBUG: Using video URL: {video_url}", flush=True)

        # Try to open video
        cap = cv2.VideoCapture(cap_source)
        
        if not cap.isOpened():
            # If URL, try downloading first
            if video_url:
                try:
                    import urllib.request
                    tmpv = f"/tmp/{uuid4().hex}.mp4"
                    print(f"DEBUG: Downloading video from URL...", flush=True)
                    urllib.request.urlretrieve(video_url, tmpv)
                    cap = cv2.VideoCapture(tmpv)
                    if cap.isOpened():
                        local_video_path = tmpv
                        cap_source = tmpv
                        print(f"DEBUG: Successfully downloaded and opened video", flush=True)
                    else:
                        if local_video_path and os.path.exists(local_video_path):
                            try: os.remove(local_video_path)
                            except: pass
                        return JSONResponse(status_code=400, content={"detail": "Cannot open video file. Please check if the video format is supported (MP4, AVI, MOV, etc.)"})
                except Exception as e:
                    print(f"DEBUG: Error downloading video: {e}", flush=True)
                    if local_video_path and os.path.exists(local_video_path):
                        try: os.remove(local_video_path)
                        except: pass
                    return JSONResponse(status_code=400, content={"detail": f"Cannot fetch video: {str(e)}"})
            else:
                if local_video_path and os.path.exists(local_video_path):
                    try: os.remove(local_video_path)
                    except: pass
                return JSONResponse(status_code=400, content={"detail": "Cannot open video file. Please check if the video format is supported (MP4, AVI, MOV, etc.)"})
        
        # Verify video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"DEBUG: Video opened successfully - FPS: {fps}, Frames: {frame_count}, Size: {width}x{height}", flush=True)
        
        if frame_count == 0:
            cap.release()
            if local_video_path and os.path.exists(local_video_path):
                try: os.remove(local_video_path)
                except: pass
            return JSONResponse(status_code=400, content={"detail": "Video file appears to be empty or corrupted"})
            
    except Exception as e:
        print(f"DEBUG: Error preparing video: {e}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        if local_video_path and os.path.exists(local_video_path):
            try: os.remove(local_video_path)
            except: pass
        return JSONResponse(status_code=500, content={"detail": f"Error processing video: {str(e)}"})

    seen_plates: Set[str] = set()
    saved_ids: List[int] = []
    session_id = uuid4().hex

    i = 0
    processed = 0
    errors_count = 0
    max_errors = 10  # Stop if too many consecutive errors
    
    print(f"DEBUG: Starting video processing - stride: {frame_stride}, max_frames: {max_frames}", flush=True)
    
    while True:
        ok, frame = cap.read()
        if not ok:
            print(f"DEBUG: Reached end of video or failed to read frame at index {i}", flush=True)
            break
        
        i += 1
        
        # Skip frames based on stride
        if i % max(1, frame_stride) != 0:
            continue
        
        processed += 1
        
        # Check max frames limit
        if processed > max_frames:
            print(f"DEBUG: Reached max_frames limit ({max_frames})", flush=True)
            break
        
        # Validate frame
        if frame is None or frame.size == 0:
            print(f"DEBUG: Invalid frame at index {i}, skipping", flush=True)
            errors_count += 1
            if errors_count >= max_errors:
                print(f"DEBUG: Too many errors ({errors_count}), stopping video processing", flush=True)
                break
            continue
        
        errors_count = 0  # Reset error count on successful frame read
        
        # Save frame to temporary file
        tmp_img_path = f"/tmp/frame_{session_id}_{i}.jpg"
        try:
            success = cv2.imwrite(tmp_img_path, frame)
            if not success:
                print(f"DEBUG: Failed to save frame {i} to {tmp_img_path}", flush=True)
                continue
        except Exception as e:
            print(f"DEBUG: Error saving frame {i}: {e}", flush=True)
            continue

        try:
            # Read frame image from file
            frame_img = cv2.imread(tmp_img_path)
            if frame_img is None or frame_img.size == 0:
                print(f"DEBUG: Failed to read frame image from {tmp_img_path}", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            print(f"DEBUG: Processing frame {i} ({frame_img.shape[1]}x{frame_img.shape[0]})", flush=True)
            
            # 1) Detector
            try:
                det_preds = infer_detector(frame_img)
            except Exception as det_error:
                print(f"DEBUG: Detector error on frame {i}: {det_error}", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            if not det_preds or len(det_preds) == 0:
                print(f"DEBUG: No detections in frame {i}, skipping", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            print(f"DEBUG: Found {len(det_preds)} detections in frame {i}", flush=True)
            
            # 2) Reader - get best detection
            try:
                best_det = max(det_preds, key=lambda x: float(x.get("confidence", 0)))
                x1, y1, x2, y2 = int(best_det["x1"]), int(best_det["y1"]), int(best_det["x2"]), int(best_det["y2"])
            except Exception as det_parse_error:
                print(f"DEBUG: Error parsing detection bbox: {det_parse_error}", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            # Sanitize and add padding
            H, W = frame_img.shape[:2]
            x1, y1 = max(0, min(x1, x2)), max(0, min(y1, y2))
            x2, y2 = max(0, max(x1, x2)), max(0, max(y1, y2))
            x1, y1, x2, y2 = min(x1, W-1), min(y1, H-1), min(x2, W), min(y2, H)
            
            # Validate bbox
            if x2 <= x1 or y2 <= y1:
                print(f"DEBUG: Invalid bbox in frame {i}: ({x1},{y1},{x2},{y2})", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            pad = int(0.05 * max(x2 - x1, y2 - y1))
            x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
            x2p, y2p = min(W, x2 + pad), min(H, y2 + pad)
            crop = frame_img[y1p:y2p, x1p:x2p]
            
            # Validate crop
            if crop is None or crop.size == 0:
                print(f"DEBUG: Invalid crop in frame {i}", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
            
            # 3) Reader
            try:
                rf = infer_reader(crop)
            except Exception as reader_error:
                print(f"DEBUG: Reader error on frame {i}: {reader_error}", flush=True)
                try: os.remove(tmp_img_path)
                except: pass
                continue
                
        except Exception as e:
            print(f"DEBUG video processing error on frame {i}: {e}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)
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

        # --- Save cropped plate image from video ---
        plate_img_filename = None
        if crop is not None and crop.size > 0:
            plate_img_filename = f"plate_{uuid4().hex}.jpg"
            plate_img_path = f"uploads/plates/{plate_img_filename}"
            cv2.imwrite(plate_img_path, crop)
        
        db = SessionLocal()
        try:
            rec = PlateRecord(
                plate_text=plate_text,
                province_text=province_text,
                confidence=conf,
                image_path=f"{image_path_for_db}#frame={i}",
                plate_image_path=plate_img_filename,
                detections_json=json.dumps({"frame_index": i, "rf": rf}, ensure_ascii=False)
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            saved_ids.append(rec.id)
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

        # --- เปิด gate ทุกครั้งที่บันทึกข้อมูลสำเร็จ (ไม่ต้องเช็คเงื่อนไข) ---
        if plate_text and len(plate_text.strip()) > 0:
            print(f"[GATE(video)] 🚀 Starting gate open process for video frame {i}...", flush=True)
            print(f"[GATE(video)] 🚀 Plate: '{plate_text}', Confidence: {conf}, Frame: {i}", flush=True)
            
            try:
                gate_success = send_open_gate(plate_text)
                print(f"[GATE(video)] 🚀 Gate command result: {gate_success}", flush=True)
                
                seen_plates.add(plate_text)
                
                # Broadcast gate event (always broadcast, even if gate failed)
                await manager.broadcast({
                    "type": "gate",
                    "action": "opened" if gate_success else "attempted",
                    "plate_text": plate_text,
                    "reason": "บันทึกข้อมูลสำเร็จจากวิดีโอ - เปิด gate ทุกครั้ง",
                    "source": "video",
                    "frame": i,
                    "gate_success": gate_success
                })
                
                if gate_success:
                    print(f"[GATE(video)] ✅ Gate opened successfully for plate: '{plate_text}' (frame {i})", flush=True)
                else:
                    print(f"[GATE(video)] ⚠️ Gate command sent but may not have opened. Check Arduino connection.", flush=True)
                    
            except Exception as e:
                print(f"[GATE(video)] ❌ ERROR in gate control: {e}", flush=True)
                import traceback
                print(f"[GATE(video)] Traceback: {traceback.format_exc()}", flush=True)
                await manager.broadcast({
                    "type": "gate",
                    "action": "error",
                    "plate_text": plate_text,
                    "error": str(e),
                    "source": "video"
                })

        try: 
            os.remove(tmp_img_path)
        except Exception as cleanup_error:
            print(f"DEBUG: Error cleaning up frame file {tmp_img_path}: {cleanup_error}", flush=True)
            pass

    # Cleanup
    try:
        cap.release()
        print(f"DEBUG: Video capture released", flush=True)
    except Exception as e:
        print(f"DEBUG: Error releasing video capture: {e}", flush=True)
    
    if local_video_path and os.path.exists(local_video_path):
        try: 
            os.remove(local_video_path)
            print(f"DEBUG: Cleaned up video file: {local_video_path}", flush=True)
        except Exception as e:
            print(f"DEBUG: Error cleaning up video file: {e}", flush=True)

    print(f"DEBUG: Video processing complete - Processed: {processed}, Saved: {len(saved_ids)}, Unique plates: {len(seen_plates)}", flush=True)
    
    return {
        "session_id": session_id,
        "frames_processed": processed,
        "unique_plates": sorted(list(seen_plates)),
        "records_saved": len(saved_ids),
        "sample_record_ids": saved_ids[:10]
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
async def get_records(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    """Get paginated records"""
    offset = (page - 1) * limit
    records = db.query(PlateRecord).order_by(desc(PlateRecord.created_at)).offset(offset).limit(limit).all()
    total = db.query(func.count(PlateRecord.id)).scalar()
    
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
async def get_stats(db: Session = Depends(get_db)):
    """Get statistics for admin dashboard"""
    total_records = db.query(func.count(PlateRecord.id)).scalar()
    
    # Today's records
    today = datetime.utcnow().date()
    today_records = db.query(func.count(PlateRecord.id)).filter(
        func.date(PlateRecord.created_at) == today
    ).scalar()
    
    # Average confidence
    avg_confidence = db.query(func.avg(PlateRecord.confidence)).scalar()
    
    return {
        "total_records": total_records or 0,
        "today_records": today_records or 0,
        "avg_confidence": float(avg_confidence) if avg_confidence else 0
    }

@app.post("/api/gate/test")
async def test_gate():
    """Test gate open command"""
    try:
        send_open_gate("TEST")
        await manager.broadcast({
            "type": "gate",
            "action": "opened",
            "plate_text": "TEST"
        })
        return {"message": "Test command sent successfully"}
    except Exception as e:
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
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    deleted = db.query(PlateRecord).filter(PlateRecord.created_at < cutoff_date).delete()
    db.commit()
    
    return {"deleted_count": deleted}

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
