# api/main.py
import os, json, cv2, uvicorn, numpy as np
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List, Set, Tuple
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
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
        import urllib.request
        resp = urllib.request.urlopen(image_url)
        arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

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
    
    # --- ใช้ OCR เป็นหลัก (Reader Model ไม่ได้เทรนมาอ่านตัวอักษร) ---
    plate_text = ""
    province_text = ""
    conf = None
    
    # Get confidence from reader model (refined detection)
    if preds:
        try:
            conf = float(sum([float(p.get("confidence", 0)) for p in preds]) / len(preds))
        except Exception:
            conf = None
    
    # Run OCR on the cropped plate
    try:
        h_, w_ = img_for_ocr.shape[:2]
        plate_text = _clean_text(run_ocr_on_bbox(img_for_ocr, 0, 0, w_, h_))
        print(f"DEBUG OCR result: {plate_text}", flush=True)
    except Exception as e:
        print("DEBUG OCR error:", e, flush=True)

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
    
    # --- Save DB FIRST ---
    db: Session = next(get_db())
    rec = PlateRecord(
        plate_text=plate_text or "",
        province_text=province_text or "",
        confidence=conf,
        image_path=(image_source if not used_crop else f"{image_source}#crop"),
        plate_image_path=plate_img_filename,
        detections_json=json.dumps({"reader": rf, "detector": det_preds[:5]}, ensure_ascii=False)
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    
    # --- Broadcast via WebSocket ---
    await manager.broadcast({
        "type": "detection",
        "plate_text": plate_text or "",
        "province_text": province_text or "",
        "confidence": conf,
        "timestamp": datetime.utcnow().isoformat()
    })

    # --- Decide & THEN trigger Arduino ---
    ok, reason = should_open(plate_text or "", conf)
    print(f"[GATE] decision ok={ok} reason={reason} plate='{plate_text}' conf={conf}", flush=True)

    if ok:
        try:
            print("[SERIAL] → OPEN", flush=True)
            send_open_gate(plate_text or "")
        except Exception as e:
            # อย่าให้ API พังถ้า serial ล้มเหลว
            print("WARN serial:", e, flush=True)

    return PlateCreateResponse(
        id=rec.id,
        plate_text=plate_text or "",
        province_text=province_text or "",
        confidence=conf
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

        # --- 3) Use OCR (Reader Model ไม่ได้เทรนมาอ่านตัวอักษร) ---
        preds = rf.get("predictions", [])
        plate_text, province_text = "", ""
        conf = None
        
        # Get confidence from reader model
        if preds:
            try:
                conf = float(sum([float(p.get("confidence", 0)) for p in preds]) / len(preds))
            except Exception:
                conf = None
        
        # Run OCR on cropped plate
        if crop.size > 0:
            try:
                plate_text = _clean_text(run_ocr_on_bbox(crop, 0, 0, crop.shape[1], crop.shape[0]))
                
                # Parse province from plate text
                if plate_text:
                    parsed = parse_plate(plate_text)
                    if parsed["province_code"]:
                        province_text = parsed["province_name"]
                        plate_text = parsed["formatted_text"]
                    print(f"DEBUG video OCR: {plate_text}, Province: {province_text}", flush=True)
            except Exception as e:
                print(f"DEBUG video OCR error: {e}", flush=True)
        
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
        
        db: Session = next(get_db())
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
        
        # --- Broadcast via WebSocket ---
        await manager.broadcast({
            "type": "detection",
            "plate_text": plate_text,
            "province_text": province_text,
            "confidence": conf,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "video"
        })

        if open_gate_first and (plate_text not in seen_plates):
            ok, reason = should_open(plate_text, conf)
            print(f"[GATE(video)] ok={ok} reason={reason} plate='{plate_text}' conf={conf}", flush=True)
            if ok:
                try:
                    print("[SERIAL(video)] → OPEN", flush=True)
                    send_open_gate(plate_text)
                    seen_plates.add(plate_text)
                except Exception as e:
                    print("WARN serial(video):", e, flush=True)

        try: os.remove(tmp_img_path)
        except: pass

    cap.release()
    if local_video_path:
        try: os.remove(local_video_path)
        except: pass

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
async def get_records(page: int = 1, limit: int = 20):
    """Get paginated records"""
    db: Session = next(get_db())
    
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
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ],
        "total": total,
        "page": page,
        "limit": limit
    }

@app.get("/api/records/{record_id}")
async def get_record(record_id: int):
    """Get single record details"""
    db: Session = next(get_db())
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
async def get_stats():
    """Get statistics for admin dashboard"""
    db: Session = next(get_db())
    
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

@app.post("/api/settings")
async def save_settings(settings: dict):
    """Save system settings"""
    # In production, save to database or config file
    # For now, just return success
    return {"message": "Settings saved successfully", "settings": settings}

@app.get("/api/export/csv")
async def export_csv():
    """Export records as CSV"""
    import io
    import csv
    
    db: Session = next(get_db())
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
async def clear_old_records(days: int = 30):
    """Clear records older than specified days"""
    db: Session = next(get_db())
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
