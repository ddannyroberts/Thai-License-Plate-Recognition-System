# 🚗 Thai Motorcycle License Plate Recognition (LPR) + Automated Gate System

ระบบจดจำป้ายทะเบียนรถจักรยานยนต์ไทยแบบ Real-time พร้อมระบบควบคุมไม้กั้นอัตโนมัติผ่าน Arduino

**Stack:** FastAPI · Python 3.11+ · Ultralytics YOLO11 · Tesseract OCR · PostgreSQL · Arduino UNO · WebSocket

---

## 📚 สารบัญ

1. [ภาพรวมระบบ](#-ภาพรวมระบบ)
2. [หลักการทำงาน](#-หลักการทำงาน)
3. [โครงสร้างโปรเจค](#-โครงสร้างโปรเจค)
4. [Models ที่ใช้](#-models-ที่ใช้)
5. [การติดตั้ง](#-การติดตั้ง)
6. [การรันระบบ](#-การรันระบบ)
7. [การใช้งาน API](#-การใช้งาน-api)
8. [Web Interface](#-web-interface)
9. [การเชื่อมต่อ Arduino](#-การเชื่อมต่อ-arduino)
10. [การ Train Models](#-การ-train-models)
11. [Environment Variables](#-environment-variables)
12. [Troubleshooting](#-troubleshooting)

---

## 🎯 ภาพรวมระบบ

ระบบนี้ออกแบบมาเพื่อ:
- **ตรวจจับ** ป้ายทะเบียนรถจักรยานยนต์ไทยจากภาพหรือวิดีโอ
- **อ่านข้อความ** บนป้ายทะเบียน (ตัวอักษรไทย + ตัวเลข)
- **แยกจังหวัด** จากรหัสป้ายทะเบียน (เช่น "กร", "กท", "นบ")
- **บันทึกข้อมูล** ลงฐานข้อมูล PostgreSQL พร้อม timestamp
- **ควบคุมไม้กั้น** อัตโนมัติผ่าน Arduino UNO + Servo Motor
- **แสดงผล Real-time** ผ่าน Web Dashboard (WebSocket)

### ✨ Features

- ✅ รองรับทั้ง **รูปภาพ** และ **วิดีโอ**
- ✅ ใช้ **Custom YOLO Models** ที่เทรนจากข้อมูลป้ายทะเบียนไทย
- ✅ **OCR แม่นยำ** ด้วย Tesseract (Thai + English)
- ✅ **Auto Province Detection** - แยกจังหวัดอัตโนมัติ
- ✅ **Web UI** สวยงาม responsive
- ✅ **User Authentication** (Login/Register)
- ✅ **Admin Dashboard** สำหรับจัดการระบบ
- ✅ **Gate Control** หลายโหมด (Every Detection, Cooldown, Whitelist)
- ✅ **Real-time Updates** ผ่าน WebSocket
- ✅ **Data Export** เป็น CSV
- ✅ **Docker Support** พร้อม docker-compose

---

## 🔧 หลักการทำงาน

### Pipeline การประมวลผล (Image/Video)

```
┌─────────────────┐
│  Upload Image   │
│   or Video      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. DETECTOR MODEL (YOLO)           │
│  - Input: รูปภาพเต็ม                 │
│  - Output: Bounding Box ของป้าย     │
│  - Model: models/detector/best.pt   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  2. CROP & PADDING                  │
│  - ตัดเฉพาะส่วนป้ายทะเบียน           │
│  - เพิ่ม padding 5% รอบๆ             │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  3. READER MODEL (YOLO)             │
│  - Input: ภาพป้ายที่ crop แล้ว       │
│  - Output: Refined detection        │
│  - Model: models/reader/best.pt     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. TESSERACT OCR                   │
│  - ลอง preprocess หลายแบบ:           │
│    • Grayscale                      │
│    • Sharpening                     │
│    • CLAHE (contrast enhancement)   │
│    • Otsu Threshold                 │
│    • Adaptive Threshold             │
│    • Invert colors                  │
│  - ลอง PSM modes: 6, 7, 8, 13       │
│  - เลือกผลลัพธ์ที่ได้คะแนนดีที่สุด   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  5. PROVINCE PARSER                 │
│  - แยกรหัสจังหวัด (เช่น "กร", "กท")  │
│  - แปลงเป็นชื่อเต็ม                   │
│  - จัดรูปแบบข้อความให้สวยงาม          │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  6. SAVE TO DATABASE                │
│  - บันทึก plate_text, province      │
│  - บันทึก confidence, timestamp     │
│  - บันทึกภาพป้าย (cropped)           │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  7. GATE DECISION                   │
│  - ตรวจสอบเงื่อนไข (ENV config)      │
│  - ส่งคำสั่ง OPEN/CLOSE to Arduino  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  8. WEBSOCKET BROADCAST             │
│  - ส่งข้อมูล real-time to UI        │
└─────────────────────────────────────┘
```

### Gate Control Logic

```python
# โหมดที่รองรับ:
1. FORCE_OPEN_ALWAYS=1          # เปิดไม้ทุกครั้งไม่เงื่อนไข
2. GATE_TRIGGER_MODE=every_record     # เปิดทุกครั้งที่มี detection
3. GATE_TRIGGER_MODE=per_plate_cooldown  # เปิดครั้งแรก แล้วรอ cooldown
4. PLATE_STRICT=1 + ALLOWED_PREFIXES="กร,กท"  # เปิดเฉพาะจังหวัดที่กำหนด
```

---

## 📁 โครงสร้างโปรเจค

```
thai-lpr-api/
├── api/
│   ├── main.py              # 🔥 FastAPI App (endpoints, WebSocket)
│   ├── local_models.py      # 🤖 YOLO Model Loaders (Detector + Reader)
│   ├── ocr.py              # 📝 Tesseract OCR Engine
│   ├── province_parser.py  # 🗺️ Province Code Parser (77 จังหวัด)
│   ├── arduino.py          # 🔌 Arduino Serial Communication
│   ├── auth.py             # 🔐 User Authentication (register/login)
│   ├── models.py           # 💾 SQLAlchemy Models (PlateRecord, User)
│   ├── schemas.py          # 📋 Pydantic Schemas
│   ├── database.py         # 🗄️ Database Connection
│   └── utils.py            # 🛠️ Utility Functions
│
├── models/
│   ├── detector/
│   │   └── best.pt         # 🎯 YOLO Detector Model (Plate Detection)
│   └── reader/
│       └── best.pt         # 🔍 YOLO Reader Model (Character Detection)
│
├── datasets/
│   ├── license_plate_recognition.v11i.yolov11/  # Detector Dataset
│   └── lpr_plate.v1i.yolov11/                   # Reader Dataset
│
├── static/
│   ├── index.html          # 🌐 Web UI
│   └── css/style.css       # 🎨 Styles
│
├── uploads/
│   ├── originals/          # ภาพต้นฉบับที่อัพโหลด
│   └── plates/             # ภาพป้ายทะเบียนที่ crop แล้ว
│
├── arduino/
│   └── gate_control_wifi.ino  # 🤖 Arduino Firmware
│
├── train_models.py         # 🏋️ Training Script (Detector)
├── train_reader_only.py   # 🏋️ Training Script (Reader)
├── test_models.py          # 🧪 Model Testing
├── create_admin.py         # 👤 Create Admin User
│
├── requirements.txt        # 📦 Python Dependencies
├── Dockerfile             # 🐳 Docker Image
├── docker-compose.yml     # 🐳 Docker Compose Config
├── start.sh              # 🚀 Quick Start Script
│
├── QUICK_START.md         # ⚡ Quick Start Guide
├── TRAINING_GUIDE.md      # 📚 Training Guide
├── WEB_APP_GUIDE.md       # 🌐 Web App Guide
└── README.md             # 📖 This file
```

---

## 🤖 Models ที่ใช้

โปรเจคนี้ใช้ **YOLO11 Models 2 ตัว** ที่เทรนมาจาก Custom Dataset:

### 1. Detector Model (`models/detector/best.pt`)

**หน้าที่:** ตรวจจับตำแหน่งป้ายทะเบียนในรูปภาพ

- **Input:** รูปภาพเต็ม (Full Image)
- **Output:** Bounding Box (x1, y1, x2, y2) + Confidence
- **Dataset:** `datasets/license_plate_recognition.v11i.yolov11/`
- **Classes:** `plate` (1 class)
- **Architecture:** YOLOv11n
- **Training:** Train จาก Roboflow Dataset (1000+ images)

**ตัวอย่างการใช้:**
```python
from api.local_models import infer_detector
import cv2

img = cv2.imread("image.jpg")
detections = infer_detector(img)
# Output: [{"x1": 100, "y1": 200, "x2": 300, "y2": 280, "confidence": 0.95, "class": "plate"}]
```

### 2. Reader Model (`models/reader/best.pt`)

**หน้าที่:** ตรวจจับรายละเอียดบนป้ายทะเบียน (Refined Detection)

- **Input:** รูปป้ายทะเบียนที่ crop แล้ว
- **Output:** Character/Region Bounding Boxes + Confidence
- **Dataset:** `datasets/lpr_plate.v1i.yolov11/`
- **Classes:** อาจมีหลาย class ตามที่ train (ตัวอักษร, ตัวเลข, หรือ region)
- **Architecture:** YOLOv11n
- **Training:** Train จาก Roboflow Dataset

**หมายเหตุ:** Reader Model ไม่ได้ train มาเพื่ออ่านตัวอักษรโดยตรง แต่ช่วย detect character regions ให้ OCR ทำงานได้ดีขึ้น

**ตัวอย่างการใช้:**
```python
from api.local_models import infer_reader
import cv2

plate_img = cv2.imread("plate_cropped.jpg")
result = infer_reader(plate_img)
# Output: {"predictions": [{"class": "char", "confidence": 0.92, "x": 50, "y": 30, ...}]}
```

### 3. Tesseract OCR (tha+eng)

**หน้าที่:** อ่านข้อความจริงๆ จากป้ายทะเบียน

- **Languages:** Thai + English
- **Whitelist:** ก-ฮ, 0-9, สระ/วรรณยุกต์, เครื่องหมาย
- **PSM Modes:** 6, 7, 8, 13 (ลองหลายแบบแล้วเลือกดีที่สุด)
- **Scoring:** มีระบบให้คะแนนผลลัพธ์ตามรูปแบบป้ายทะเบียนไทย

**ไฟล์:** `api/ocr.py`

---

## 🛠️ การติดตั้ง

### Prerequisites

1. **Python 3.11+** (แนะนำ 3.11 หรือ 3.12)
2. **Tesseract OCR** with Thai language pack
3. **PostgreSQL** (หรือใช้ Docker)
4. **Arduino IDE** (ถ้าใช้งาน Arduino)
5. **Git**

### A. การติดตั้งแบบ Native (macOS/Linux)

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/thai-lpr-api.git
cd thai-lpr-api
```

#### 2. ติดตั้ง Tesseract OCR

**macOS (Homebrew):**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-tha tesseract-ocr-eng
```

**ตรวจสอบการติดตั้ง:**
```bash
tesseract --version
tesseract --list-langs  # ต้องมี tha และ eng
```

#### 3. สร้าง Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

#### 4. ติดตั้ง Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. ตั้งค่า Environment Variables

สร้างไฟล์ `.env` หรือ `.env.local`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lpr_db
# หรือใช้ SQLite (dev):
# DATABASE_URL=sqlite:///./data.db

# App
APP_HOST=0.0.0.0
APP_PORT=8000

# Models (optional - มี default อยู่แล้ว)
DETECTOR_WEIGHTS=models/detector/best.pt
READER_WEIGHTS=models/reader/best.pt

# OCR
TESSERACT_LANG=tha+eng

# Arduino (optional)
SERIAL_ENABLED=false
SERIAL_PORT=/dev/ttyACM0      # Linux
# SERIAL_PORT=/dev/cu.usbmodem14201  # macOS
SERIAL_BAUD=115200

# Gate Control
FORCE_OPEN_ALWAYS=0
GATE_TRIGGER_MODE=every_record
OPEN_COOLDOWN_SEC=10
ALLOWED_PREFIXES=          # ว่างไว้ = อนุญาตทั้งหมด
PLATE_STRICT=0
```

#### 6. Setup Database (PostgreSQL)

```bash
# สร้าง database
createdb lpr_db

# หรือใช้ psql:
psql -U postgres
CREATE DATABASE lpr_db;
\q
```

ตาราง database จะถูกสร้างอัตโนมัติตอนรัน app ครั้งแรก (SQLAlchemy auto-migration)

#### 7. สร้าง Admin User (Optional)

```bash
python create_admin.py
# Enter username: admin
# Enter email: admin@example.com
# Enter password: ******
```

### B. การติดตั้งแบบ Docker

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/thai-lpr-api.git
cd thai-lpr-api
```

#### 2. สร้างไฟล์ `.env`

```bash
cp .env.example .env
# แก้ไขตามต้องการ
```

#### 3. Build & Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# ดู logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**Services ที่รัน:**
- `api`: FastAPI app (port 8000)
- `postgres`: PostgreSQL database (port 5432)

---

## 🚀 การรันระบบ

### แบบ Native

```bash
# Activate venv
source .venv/bin/activate

# รัน FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# หรือใช้ start script (ถ้ามี):
./start.sh
```

**เปิดเบราว์เซอร์:**
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### แบบ Docker

```bash
docker-compose up -d
```

### การรัน Background (Production)

```bash
# ใช้ screen หรือ tmux
screen -S lpr-api
uvicorn api.main:app --host 0.0.0.0 --port 8000
# กด Ctrl+A, D เพื่อ detach

# หรือใช้ systemd service (Linux)
sudo systemctl start lpr-api
```

---

## 📡 การใช้งาน API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok"}
```

### 2. Detect License Plate (Image)

**cURL:**
```bash
curl -X POST http://localhost:8000/detect \
  -F "file=@car.jpg"
```

**Python:**
```python
import requests

with open("car.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/detect",
        files={"file": f}
    )
    
print(response.json())
```

**Response:**
```json
{
  "id": 123,
  "plate_text": "กร 1234",
  "province_text": "กรุงเทพมหานคร (รถราชการ)",
  "confidence": 0.95
}
```

### 3. Detect from Video

```bash
curl -X POST http://localhost:8000/detect-video \
  -F "file=@video.mp4" \
  -F "frame_stride=10" \
  -F "max_frames=100"
```

**Response:**
```json
{
  "session_id": "abc123",
  "frames_processed": 45,
  "unique_plates": ["กร 1234", "กท 5678"],
  "records_saved": 2
}
```

### 4. Get Records (Paginated)

```bash
curl "http://localhost:8000/api/records?page=1&limit=20"
```

**Response:**
```json
{
  "records": [
    {
      "id": 123,
      "plate_text": "กร 1234",
      "province_text": "กรุงเทพมหานคร (รถราชการ)",
      "confidence": 0.95,
      "plate_image": "/uploads/plates/plate_abc123.jpg",
      "created_at": "2025-10-14T12:34:56"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20
}
```

### 5. Get Statistics (Admin)

```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "total_records": 1523,
  "today_records": 45,
  "avg_confidence": 0.89
}
```

### 6. Gate Control

**Test Gate:**
```bash
curl -X POST http://localhost:8000/api/gate/test
```

**Force Close:**
```bash
curl -X POST http://localhost:8000/api/gate/close
```

### 7. Export CSV

```bash
curl http://localhost:8000/api/export/csv -o records.csv
```

### 8. Authentication

**Register:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -F "username=testuser" \
  -F "email=test@example.com" \
  -F "password=123456" \
  -F "confirm_password=123456"
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -F "username=testuser" \
  -F "password=123456"
```

**Response:**
```json
{
  "success": true,
  "session_token": "abc123xyz",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user"
  }
}
```

---

## 🌐 Web Interface

### หน้าแรก (Upload)

1. เลือก **Image** หรือ **Video**
2. **Drag & Drop** หรือคลิกเพื่อเลือกไฟล์
3. กด **Process** เพื่อเริ่มประมวลผล
4. ดูผลลัพธ์:
   - Plate Text (ข้อความป้าย)
   - Province (จังหวัด)
   - Confidence (ความมั่นใจ %)
   - Gate Status (สถานะไม้กั้น)

### หน้า Records

- ดูประวัติการตรวจจับทั้งหมด
- ค้นหาด้วยเลขทะเบียน
- รูปภาพป้ายที่ crop แล้ว
- Pagination

### หน้า Admin Dashboard

**ต้อง login ด้วย admin account:**

1. **Statistics**
   - Total Records
   - Today's Detections
   - Average Confidence

2. **Gate Control**
   - Test Gate Open/Close
   - ดูสถานะการเชื่อมต่อ Arduino

3. **Settings**
   - Gate Mode (Every Detection / Cooldown / Whitelist)
   - Cooldown Duration

4. **Data Management**
   - Export CSV
   - Clear Old Data

### Real-time Updates Panel

- แสดงการตรวจจับแบบ Real-time
- ใช้ WebSocket (/ws)
- สถานะการเชื่อมต่อ (Connected/Disconnected)

---

## 🔌 การเชื่อมต่อ Arduino

### Hardware Setup

**อุปกรณ์:**
- Arduino UNO (หรือ compatible board)
- Servo Motor SG90 (หรือ MG90S)
- External 5V Power Supply (แนะนำ)
- Jumper Wires
- USB Cable (Arduino to Computer)

**Wiring:**
```
Servo Motor:
├── Signal (Orange/Yellow) → Arduino Pin D9
├── VCC (Red)            → 5V (External Power Supply)
└── GND (Brown/Black)    → GND (Common Ground with Arduino)

Arduino:
├── USB → Computer (Serial Communication)
└── GND → Power Supply GND (⚠️ ต้อง Common Ground!)
```

**⚠️ หมายเหตุสำคัญ:**
- **ต้อง Common Ground** ระหว่าง Arduino, Servo, และแหล่งจ่ายไฟ
- ไม่ควรใช้ไฟ 5V จาก Arduino เลี้ยง Servo (อาจทำให้ Arduino reset)
- ใช้แหล่งจ่ายไฟภายนอก 5V 1A+ สำหรับ Servo

### Firmware Upload

1. **เปิด Arduino IDE**

2. **เลือก Board:**
   - Tools → Board → Arduino UNO

3. **เลือก Port:**
   - macOS: `/dev/cu.usbmodem*`
   - Linux: `/dev/ttyACM0`
   - Windows: `COM3` (ตรวจสอบใน Device Manager)

4. **เปิดไฟล์:** `arduino/gate_control_wifi.ino`

5. **Upload** (กด ➡️ หรือ Ctrl+U)

6. **ทดสอบ Serial Monitor:**
   - เปิด Serial Monitor (Ctrl+Shift+M)
   - ตั้ง Baud Rate: **115200**
   - ตั้ง Line Ending: **Newline**
   - พิมพ์ `PING` → ต้องได้ `PONG`
   - พิมพ์ `OPEN` → Servo ต้องหมุน 90° และกลับ 0°

### คำสั่ง Serial ที่รองรับ

| Command | Description | Response |
|---------|-------------|----------|
| `PING` | Test connection | `PONG` |
| `OPEN` | Open gate (90°) for 2 sec, then close (0°) | `ACK:OPEN` → `ACK:CLOSE` |
| `CLOSE` | Force close gate (0°) | `ACK:CLOSE` |

### การตั้งค่า .env

```bash
# เปิดใช้งาน Serial
SERIAL_ENABLED=true

# Port (ตรวจสอบจาก ls /dev/tty* หรือ ls /dev/cu.*)
SERIAL_PORT=/dev/ttyACM0        # Linux
# SERIAL_PORT=/dev/cu.usbmodem14201  # macOS

# Baud Rate (ต้องตรงกับ Arduino Sketch)
SERIAL_BAUD=115200
```

### ทดสอบจาก API

```bash
# Test gate open
curl -X POST http://localhost:8000/api/gate/test

# Force close
curl -X POST http://localhost:8000/api/gate/close
```

**ตรวจสอบ Logs:**
```
[ARDUINO] Connected to /dev/ttyACM0
[SERIAL] → OPEN
[ARDUINO] CMD: OPEN → ACK:OPEN
[GATE] decision ok=True reason=every_record plate='กร 1234' conf=0.95
```

### Troubleshooting Arduino

**ปัญหา: Permission Denied (Linux)**
```bash
# เพิ่ม user เข้า dialout group
sudo usermod -a -G dialout $USER
# Logout/Login ใหม่

# หรือ chmod (temporary)
sudo chmod 666 /dev/ttyACM0
```

**ปัญหา: Servo กระตุก หรือ Arduino reset**
- ✅ ใช้ External Power Supply 5V 1A+
- ✅ ต้อง Common Ground
- ✅ ตรวจสอบสายไฟ

**ปัญหา: ไม่เห็น Serial Port**
- ตรวจสอบว่าสาย USB ไม่ใช่สายชาร์จอย่างเดียว (ต้องมี Data pins)
- Restart Arduino หรือถอดสายแล้วเสียบใหม่

---

## 🏋️ การ Train Models

### Dataset Preparation

**Detector Dataset:** `datasets/license_plate_recognition.v11i.yolov11/`
```
├── train/
│   ├── images/  # รูปภาพ
│   └── labels/  # ไฟล์ .txt (YOLO format)
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
└── data.yaml
```

**Reader Dataset:** `datasets/lpr_plate.v1i.yolov11/`
```
(โครงสร้างเดียวกัน)
```

### Training Detector

```bash
python train_models.py
```

**หรือ Custom Training:**
```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolo11n.pt')

# Train
results = model.train(
    data='datasets/license_plate_recognition.v11i.yolov11/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='detector_new',
    patience=20,
    save=True,
    device=0  # GPU 0, or 'cpu'
)

# Export
model.export(format='onnx')  # optional
```

**Trained Model จะถูกบันทึกที่:**
```
runs/detect/detector_new/weights/best.pt
```

**คัดลอกไปใช้:**
```bash
cp runs/detect/detector_new/weights/best.pt models/detector/best.pt
```

### Training Reader

```bash
python train_reader_only.py
```

**หรือ:**
```python
from ultralytics import YOLO

model = YOLO('yolo11n.pt')

results = model.train(
    data='datasets/lpr_plate.v1i.yolov11/data.yaml',
    epochs=50,
    imgsz=640,
    batch=16,
    name='character_reader'
)
```

**คัดลอก Model:**
```bash
cp runs/detect/character_reader/weights/best.pt models/reader/best.pt
```

### Testing Models

```bash
python test_models.py
```

**ตัวอย่างโค้ดทดสอบ:**
```python
from api.local_models import infer_detector, infer_reader
import cv2

# Test detector
img = cv2.imread("test_image.jpg")
detections = infer_detector(img)
print("Detections:", detections)

# Test reader (on cropped plate)
x1, y1, x2, y2 = int(detections[0]['x1']), int(detections[0]['y1']), int(detections[0]['x2']), int(detections[0]['y2'])
crop = img[y1:y2, x1:x2]
result = infer_reader(crop)
print("Reader result:", result)
```

### Model Evaluation

```bash
# Validate detector
yolo val model=models/detector/best.pt data=datasets/license_plate_recognition.v11i.yolov11/data.yaml

# Validate reader
yolo val model=models/reader/best.pt data=datasets/lpr_plate.v1i.yolov11/data.yaml
```

**Metrics:**
- Precision
- Recall
- mAP@0.5
- mAP@0.5:0.95

---

## ⚙️ Environment Variables

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data.db` |
| `POSTGRES_HOST` | PostgreSQL host (fallback) | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `lpr_db` |

### App

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_HOST` | Server host | `0.0.0.0` |
| `APP_PORT` | Server port | `8000` |

### Models

| Variable | Description | Default |
|----------|-------------|---------|
| `DETECTOR_WEIGHTS` | Detector model path | `models/detector/best.pt` |
| `READER_WEIGHTS` | Reader model path | `models/reader/best.pt` |

### OCR

| Variable | Description | Default |
|----------|-------------|---------|
| `TESSERACT_LANG` | Tesseract languages | `tha+eng` |

### Arduino Serial

| Variable | Description | Default |
|----------|-------------|---------|
| `SERIAL_ENABLED` | Enable serial communication | `false` |
| `SERIAL_PORT` | Serial port path | `/dev/ttyACM0` |
| `SERIAL_BAUD` | Baud rate | `115200` |
| `SERIAL_URL` | Serial URL (alternative) | - |

### Gate Control

| Variable | Description | Default |
|----------|-------------|---------|
| `FORCE_OPEN_ALWAYS` | Always open gate | `0` |
| `GATE_TRIGGER_MODE` | Trigger mode (`every_record` / `per_plate_cooldown`) | `every_record` |
| `OPEN_COOLDOWN_SEC` | Cooldown in seconds | `10` |
| `ALLOWED_PREFIXES` | Allowed province codes (comma-separated) | `` (all) |
| `PLATE_STRICT` | Strict prefix checking | `0` |

### Video Processing

| Variable | Description | Default |
|----------|-------------|---------|
| `VIDEO_FRAME_STRIDE` | Process every N frames | `10` |
| `VIDEO_MAX_FRAMES` | Max frames to process | `600` |
| `VIDEO_OPEN_GATE_FIRST` | Open gate on first detection | `true` |

---

## 🐛 Troubleshooting

### 1. Import Error: No module named 'api'

**วิธีแก้:**
```bash
# ตรวจสอบว่าอยู่ใน project root
pwd  # ต้องเห็น thai-lpr-api/

# Run with python -m
python -m uvicorn api.main:app --reload

# หรือเพิ่ม PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn api.main:app --reload
```

### 2. Tesseract not found

**วิธีแก้:**
```bash
# ติดตั้ง Tesseract
# macOS:
brew install tesseract tesseract-lang

# Ubuntu:
sudo apt-get install tesseract-ocr tesseract-ocr-tha

# ตรวจสอบ:
tesseract --version
which tesseract

# ถ้ายังไม่เจอ ให้ระบุ path ใน code:
# ocr.py
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
```

### 3. Database Connection Error

**วิธีแก้:**
```bash
# ตรวจสอบ PostgreSQL running
pg_isready

# Start PostgreSQL
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# ตรวจสอบ DATABASE_URL ใน .env
echo $DATABASE_URL
```

### 4. Model Loading Error

**วิธีแก้:**
```bash
# ตรวจสอบว่ามี model files
ls -lh models/detector/best.pt
ls -lh models/reader/best.pt

# ถ้าไม่มี ให้ train ใหม่:
python train_models.py
python train_reader_only.py

# หรือ download pre-trained models (ถ้ามี):
wget https://your-server.com/models/detector.pt -O models/detector/best.pt
wget https://your-server.com/models/reader.pt -O models/reader/best.pt
```

### 5. Arduino Permission Denied (Linux)

**วิธีแก้:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again
# Or run:
newgrp dialout

# Temporary fix:
sudo chmod 666 /dev/ttyACM0
```

### 6. Low OCR Accuracy

**วิธีแก้:**
- ✅ ตรวจสอบ lighting ในภาพต้นฉบับ
- ✅ เพิ่ม padding ใน `api/ocr.py` (ปรับ `target_height`)
- ✅ ปรับ whitelist characters ให้ครอบคลุมมากขึ้น
- ✅ ลอง preprocess เพิ่มเติม (เช่น denoise, morphology)

### 7. WebSocket Connection Failed

**วิธีแก้:**
```javascript
// ตรวจสอบ URL ใน browser console
// ต้องเป็น ws:// (not wss:// for localhost)
const ws = new WebSocket("ws://localhost:8000/ws");
```

### 8. Slow Inference (YOLO)

**วิธีแก้:**
```bash
# ใช้ GPU ถ้ามี
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# ตรวจสอบ CUDA:
python -c "import torch; print(torch.cuda.is_available())"

# หรือ ใช้ smaller model (yolo11n instead of yolo11x)
```

---

## 📚 เอกสารเพิ่มเติม

- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [TRAINING_GUIDE.md](TRAINING_GUIDE.md) - Model training guide
- [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) - Web interface guide
- [TEST_VIDEO.md](TEST_VIDEO.md) - Video processing guide

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [Roboflow](https://roboflow.com/) - Dataset hosting
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Arduino](https://www.arduino.cc/)

---

## 📞 Support

หากมีปัญหาหรือคำถาม กรุณา:
1. เช็ค [Troubleshooting](#-troubleshooting) section
2. เปิด [GitHub Issue](https://github.com/yourusername/thai-lpr-api/issues)
3. ส่ง email: support@example.com

---

**⭐ ถ้าโปรเจคนี้เป็นประโยชน์ กด Star ด้วยนะครับ! ⭐**
