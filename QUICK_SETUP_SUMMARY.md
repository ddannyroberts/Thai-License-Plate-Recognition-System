# ⚡ Quick Setup Summary - Thai LPR System

คู่มือติดตั้งและใช้งานแบบย่อ สำหรับเริ่มต้นใช้งานเร็วๆ

---

## 📦 ติดตั้ง (5 นาที)

### 1. Clone & Install

```bash
# Clone repo
git clone <your-repo-url> thai-lpr-api
cd thai-lpr-api

# Create venv
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract
# macOS:
brew install tesseract tesseract-lang

# Ubuntu:
sudo apt-get install tesseract-ocr tesseract-ocr-tha
```

### 2. ตั้งค่า .env

```bash
# สร้างไฟล์ .env
cat > .env << 'EOF'
# Database (SQLite for quick start)
DATABASE_URL=sqlite:///./data.db

# Arduino (ปิดไว้ก่อน)
SERIAL_ENABLED=false

# Gate Control
GATE_TRIGGER_MODE=every_record
EOF
```

### 3. รัน Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

เปิด: http://localhost:8000

---

## 🎯 การใช้งานพื้นฐาน

### Web UI

1. **อัพโหลดรูป:**
   - Upload Tab → เลือกรูป → Process
   
2. **เปิดกล้อง Real-time:**
   - Upload Tab → Live Camera → Open Camera
   - (รองรับทั้ง Desktop และ Mobile)

3. **ดูประวัติ:**
   - Records Tab → ดูการตรวจจับทั้งหมด

### API

```bash
# Test health
curl http://localhost:8000/health

# ตรวจจับรูป
curl -X POST http://localhost:8000/detect -F "file=@car.jpg"

# ดูประวัติ
curl http://localhost:8000/api/records?page=1&limit=20
```

---

## 🔌 เชื่อมต่อ Arduino (Optional)

### Hardware

```
Arduino UNO:
├── Servo Signal → Pin D9
├── Servo VCC    → 5V (External)
└── Servo GND    → GND (Common Ground)
```

### Software

1. **Upload Firmware:**
   - เปิด Arduino IDE
   - เปิดไฟล์: `arduino/gate_control_wifi.ino`
   - เลือก Board: Arduino UNO
   - เลือก Port: `/dev/ttyACM0` (Linux) หรือ `/dev/cu.usbmodem*` (macOS)
   - Upload (Ctrl+U)

2. **ทดสอบ Serial:**
   - เปิด Serial Monitor (Ctrl+Shift+M)
   - Baud: 115200
   - พิมพ์: `PING` → ต้องได้ `PONG`
   - พิมพ์: `OPEN` → Servo หมุน

3. **เปิดใน .env:**
   ```bash
   SERIAL_ENABLED=true
   SERIAL_PORT=/dev/ttyACM0  # เปลี่ยนตาม port ของคุณ
   SERIAL_BAUD=115200
   ```

4. **Restart Server:**
   ```bash
   # Stop (Ctrl+C) แล้ว
   uvicorn api.main:app --reload
   ```

---

## 📱 เข้าจากมือถือ

### หา IP ของคอมพิวเตอร์

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Output: inet 192.168.1.100
```

**Windows:**
```bash
ipconfig | findstr IPv4
```

### เข้าจากมือถือ

```
http://192.168.1.100:8000
```

**เปิดกล้อง Real-time:**
- Upload Tab → Live Camera → Open Camera
- มือถือจะใช้กล้องหลังอัตโนมัติ
- ระบบจะตรวจจับทุก 2 วินาที

---

## 🎯 โหมดการทำงาน

เปลี่ยนได้ใน `.env`:

### 1. Every Record (Default)
เปิดไม้กั้นทุกครั้งที่มีการตรวจจับ

```bash
GATE_TRIGGER_MODE=every_record
```

### 2. Cooldown per Plate
เปิดครั้งแรก แล้วรอ cooldown ต่อป้ายเดียวกัน

```bash
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=300  # 5 นาที
```

### 3. Whitelist Only
เปิดเฉพาะรหัสจังหวัดที่กำหนด

```bash
PLATE_STRICT=1
ALLOWED_PREFIXES=กร,กท,กว
```

---

## 🔄 Flow การทำงาน

```
อัพโหลดรูป / เปิดกล้อง
    ↓
Detector Model (หาตำแหน่งป้าย)
    ↓
Crop ป้ายออกมา
    ↓
Reader Model (refined detection)
    ↓
Tesseract OCR (อ่านตัวอักษร)
    ↓
Province Parser (แยกจังหวัด)
    ↓
บันทึก Database
    ↓
ตัดสินใจเปิด/ไม่เปิดไม้กั้น
    ↓
ส่งคำสั่งไป Arduino (ถ้าเปิดใช้)
    ↓
WebSocket broadcast (Real-time UI)
```

---

## 📂 ไฟล์สำคัญ

| ไฟล์ | หน้าที่ |
|------|---------|
| `api/main.py` | FastAPI endpoints |
| `api/local_models.py` | โหลด YOLO models |
| `api/ocr.py` | Tesseract OCR |
| `api/arduino.py` | Arduino serial control |
| `models/detector/best.pt` | **Detector Model** |
| `models/reader/best.pt` | **Reader Model** |
| `static/index.html` | Web UI |
| `static/js/app.js` | JavaScript (camera, WebSocket) |

---

## 🐛 Troubleshooting

### 1. Import Error

```bash
# วิธีแก้
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn api.main:app --reload
```

### 2. Tesseract Not Found

```bash
# ติดตั้งใหม่
brew install tesseract tesseract-lang  # macOS
sudo apt-get install tesseract-ocr tesseract-ocr-tha  # Ubuntu
```

### 3. Arduino Permission Denied (Linux)

```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### 4. Camera ไม่เปิด (Mobile)

- ใช้ HTTPS หรือ
- เข้าผ่าน IP local: `http://192.168.1.x:8000`
- เช็ค Browser permissions

### 5. Models Not Found

```bash
# ตรวจสอบว่ามี models
ls -lh models/detector/best.pt
ls -lh models/reader/best.pt

# ถ้าไม่มี ให้ train:
python train_models.py  # Detector
python train_reader_only.py  # Reader
```

---

## 📊 การตรวจสอบ Logs

```bash
# ดู logs real-time
uvicorn api.main:app --reload

# ดู debug messages
# [INFO] 🟠 Using local YOLO DETECTOR from: models/detector/best.pt
# [INFO] 🔵 Using local YOLO READER   from: models/reader/best.pt
# DEBUG detector: [('plate', 0.95)]
# DEBUG reader preds: [('char', 0.92), ...]
# DEBUG OCR result: กร 1234
# [GATE] decision ok=True reason=every_record plate='กร 1234' conf=0.95
# [SERIAL] → OPEN
# [ARDUINO] CMD: OPEN → ACK:OPEN
```

---

## 🚀 Next Steps

1. ✅ ทดสอบอัพโหลดรูป
2. ✅ ทดสอบเปิดกล้อง (mobile)
3. ✅ เชื่อมต่อ Arduino
4. ✅ ปรับแต่ง Gate Control Mode
5. ✅ Setup HTTPS (production)
6. ✅ Train Models ใหม่ (ถ้าต้องการ)

---

## 📚 เอกสารเพิ่มเติม

- [README.md](README.md) - คู่มือหลักฉบับเต็ม
- [ARDUINO_CONNECTION_GUIDE.md](ARDUINO_CONNECTION_GUIDE.md) - Arduino ละเอียด
- [CAMERA_REALTIME_GUIDE.md](CAMERA_REALTIME_GUIDE.md) - Camera feature ละเอียด
- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - การ train models
- [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) - Web UI guide

---

## 📞 ติดปัญหา?

1. เช็ค Troubleshooting section ด้านบน
2. ดู logs: `uvicorn api.main:app --reload`
3. ทดสอบ components แยก:
   - Models: `python test_models.py`
   - Arduino: Serial Monitor → `PING` → `PONG`
   - Camera: Console (F12) → ดู errors
4. เปิด GitHub Issue

---

**🎉 Happy Coding!**

**Project Stack:**
- FastAPI (Backend)
- YOLO11 (Detector + Reader Models)
- Tesseract OCR (Thai + English)
- PostgreSQL / SQLite (Database)
- Arduino UNO + Servo (Gate Control)
- WebSocket (Real-time Updates)
- Modern Web UI (HTML/CSS/JS)

---

**เวอร์ชัน:** 2.0  
**อัพเดตล่าสุด:** 2025-10-15  
**ผู้พัฒนา:** Your Team

