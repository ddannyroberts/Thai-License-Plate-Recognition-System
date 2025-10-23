# 🚗 Thai License Plate Recognition System
## **โปรเจคระบบอ่านป้ายทะเบียนรถมอเตอร์ไซค์ไทย**

<p align="center">
  <strong>Senior Project - Computer Engineering</strong>
</p>

---

## 📋 **Outline**

1. ⭐ โปรเจคนี้คืออะไร?
2. 🎯 วัตถุประสงค์
3. 💻 เทคโนโลยีที่ใช้
4. 🏗️ สถาปัตยกรรมระบบ
5. ✨ Features ที่พัฒนา
6. 📊 ผลการทดสอบ
7. 🚀 การใช้งาน
8. 🔮 การพัฒนาต่อ

---

# ⭐ **โปรเจคนี้คืออะไร?**

---

## 📖 **คำอธิบาย**

ระบบอ่านป้ายทะเบียนรถมอเตอร์ไซค์ไทยอัตโนมัติ โดยใช้ AI

### **Input:**
- 📸 รูปถ่ายป้ายทะเบียน (Upload)

### **Process:**
- 🤖 AI ประมวลผลด้วย YOLO + Tesseract OCR
- 💾 บันทึกลง Database

### **Output:**
- 📝 เลขทะเบียน (เช่น "กว 1234")
- 📍 ชื่อจังหวัด (เช่น "กรุงเทพมหานคร")
- ⭐ ความแม่นยำ (Confidence Score)
- 🖼️ รูปป้ายที่ตรวจจับได้

### **(Optional) Hardware Integration:**
- 🔧 ควบคุม Arduino Servo Motor
- 🚪 เปิด-ปิดไม้กั้นอัตโนมัติ

---

## 🎬 **Demo ตัวอย่าง**

### **Input:**
```
รูปถ่ายมอเตอร์ไซค์
┌─────────────────────────┐
│     🏍️                  │
│   [กว 1234]            │
│  กรุงเทพมหานคร          │
└─────────────────────────┘
```

### **Output:**
```json
{
  "id": 42,
  "plate_text": "กว 1234",
  "province_text": "กรุงเทพมหานคร",
  "confidence": 0.89,
  "timestamp": "2025-10-22 14:30:00"
}
```

---

# 🎯 **วัตถุประสงค์**

---

## 🎓 **วัตถุประสงค์หลัก**

### **1. ศึกษาและพัฒนา AI Model**
- ✅ ฝึก YOLO Model สำหรับ Detection
- ✅ ฝึก YOLO Model สำหรับ Character Recognition
- ✅ ทำความเข้าใจ OCR Technology

### **2. พัฒนา Full-Stack Application**
- ✅ Backend: FastAPI (Python)
- ✅ Frontend: HTML + JavaScript
- ✅ Database: SQLite
- ✅ Real-time: WebSocket

### **3. Hardware Integration**
- ✅ Arduino Programming (C++)
- ✅ Serial Communication (USB)
- ✅ Servo Motor Control

### **4. สร้างระบบที่ใช้งานได้จริง**
- ✅ Web UI ใช้งานง่าย
- ✅ รองรับ Mobile & Desktop
- ✅ บันทึกข้อมูลครบถ้วน

---

## 🚫 **สิ่งที่ไม่ใช่วัตถุประสงค์**

❌ ไม่ได้มุ่งเน้น commercialization  
❌ ไม่ได้ออกแบบสำหรับ production scale  
❌ ไม่มี cloud deployment  
❌ ไม่มี mobile app

> **หมายเหตุ:** โปรเจคนี้เป็น **Proof of Concept** และ **Educational Project**

---

# 💻 **เทคโนโลยีที่ใช้**

---

## 🧠 **AI & Machine Learning**

### **1. YOLOv11 (Ultralytics)**

**สำหรับ License Plate Detection:**
```
Input:  รูปทั้งหมด (Full Image)
Output: Bounding Box ของป้ายทะเบียน
Model:  models/detector/best.pt
Dataset: ~300 รูป (Train/Valid/Test)
```

**สำหรับ Character Recognition:**
```
Input:  รูปป้ายที่ crop แล้ว
Output: ตัวอักษรแต่ละตัว
Model:  models/reader/best.pt
Dataset: ~500 รูปตัวอักษร
```

**ทำไมเลือก YOLO?**
- ⚡ เร็ว: Real-time detection
- 🎯 แม่นยำ: State-of-the-art accuracy
- 🛠️ ใช้งานง่าย: Ultralytics library
- 📚 Documentation ดี

---

### **2. Tesseract OCR**

```
Input:  รูปป้ายทะเบียน (pre-processed)
Output: ข้อความที่อ่านได้
Config: Thai + English language pack
```

**ทำไมต้องมี Tesseract?**
- 🛡️ Backup: กรณี YOLO อ่านไม่ได้
- 📊 Comparison: เปรียบเทียบผลลัพธ์
- 🔤 Flexibility: รองรับภาษาหลากหลาย

---

## 🌐 **Backend**

### **FastAPI (Python)**

```python
# ตัวอย่าง API Endpoint
@app.post("/detect")
async def detect(file: UploadFile):
    # 1. รับรูป
    # 2. YOLO Detection
    # 3. YOLO Reader
    # 4. Tesseract OCR
    # 5. บันทึก Database
    # 6. Return ผลลัพธ์
    return {"plate_text": "กว 1234", ...}
```

**Features:**
- ✅ Async/Await (Non-blocking)
- ✅ Auto Documentation (Swagger UI)
- ✅ Type Validation (Pydantic)
- ✅ WebSocket Support
- ✅ CORS Enabled

---

### **SQLite Database**

```sql
-- Table: plate_records
CREATE TABLE plate_records (
    id INTEGER PRIMARY KEY,
    plate_text TEXT,
    province_text TEXT,
    confidence FLOAT,
    image_path TEXT,
    plate_image_path TEXT,
    created_at TIMESTAMP,
    detections_json TEXT
);

-- Table: users (Authentication)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    hashed_password TEXT,
    is_admin BOOLEAN,
    created_at TIMESTAMP
);
```

**ทำไมเลือก SQLite?**
- ✅ ไม่ต้องติดตั้ง server แยก
- ✅ Portable (ไฟล์เดียว)
- ✅ เร็วพอสำหรับ prototype
- ✅ อัปเกรดเป็น PostgreSQL ได้ง่าย

---

## 🎨 **Frontend**

### **HTML + JavaScript + CSS**

```javascript
// File Upload Feature
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/detect', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(result => displayResult(result));
```

**Features:**
- ✅ File Upload
- ✅ Real-time Results (WebSocket)
- ✅ Responsive Design
- ✅ Admin Dashboard

---

## 🔧 **Hardware**

### **Arduino UNO + Servo Motor**

```cpp
// arduino/gate_control_wifi.ino
#include <Servo.h>

Servo gate;
const int SERVO_PIN = 9;
const int OPEN_ANGLE = 90;
const int CLOSE_ANGLE = 0;

void openGate() {
  gate.write(OPEN_ANGLE);
  delay(2000);
  gate.write(CLOSE_ANGLE);
}
```

**Serial Protocol:**
```
Computer → Arduino: "OPEN:กว1234\n"
Arduino → Computer: "ACK:OPEN:กว1234\n"

Commands: PING, OPEN, CLOSE, STATUS
Baud Rate: 115200
```

---

# 🏗️ **สถาปัตยกรรมระบบ**

---

## 📐 **System Architecture**

```
┌─────────────────────────────────────────────┐
│          User Interface Layer               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Desktop │  │ Mobile  │  │ Camera  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘    │
└───────┼───────────┼────────────┼──────────┘
        │           │            │
        └───────────┴────────────┘
                    │ HTTP/WebSocket
┌───────────────────┼──────────────────────────┐
│         FastAPI Server (Port 8000)           │
│  ┌─────────────────────────────────────┐    │
│  │ Routes:                              │    │
│  │ - POST /detect                       │    │
│  │ - GET  /records                      │    │
│  │ - WS   /ws                           │    │
│  │ - GET  /static/*                     │    │
│  └─────────────────────────────────────┘    │
└───────────────────┼──────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────┼──────────┐    ┌──────┼──────────┐
│  AI Pipeline     │    │  Data Layer     │
│  ┌────────────┐  │    │  ┌───────────┐ │
│  │ Detector   │  │    │  │  SQLite   │ │
│  │ best.pt    │  │    │  │  data.db  │ │
│  └─────┬──────┘  │    │  └───────────┘ │
│  ┌─────┴──────┐  │    │  ┌───────────┐ │
│  │ Reader     │  │    │  │  Images   │ │
│  │ best.pt    │  │    │  │  uploads/ │ │
│  └─────┬──────┘  │    │  └───────────┘ │
│  ┌─────┴──────┐  │    └─────────────────┘
│  │ Tesseract  │  │
│  │ OCR        │  │
│  └────────────┘  │
└──────────────────┘
        │
┌───────┼────────────┐
│  Hardware Layer    │
│  ┌──────────┐      │
│  │ Arduino  │      │
│  │   UNO    │      │
│  └────┬─────┘      │
│  ┌────┴──────┐     │
│  │  Servo    │     │
│  │  Motor    │     │
│  └───────────┘     │
└────────────────────┘
```

---

## 🔄 **Data Flow**

```
1. User uploads image / uses camera
        ↓
2. FastAPI receives request
        ↓
3. Image preprocessing (resize, enhance)
        ↓
4. YOLO Detector inference
        ├─ Success → Bounding Box
        └─ Fail → Return error
        ↓
5. Crop license plate region
        ↓
6. YOLO Reader inference
        ├─ Success → Characters
        └─ Fail → Try Tesseract
        ↓
7. Tesseract OCR (fallback)
        ↓
8. Province Parser
        "กว" → "กรุงเทพมหานคร"
        ↓
9. Save to Database
        ├─ plate_records table
        └─ Save cropped plate image
        ↓
10. WebSocket broadcast (if connected)
        ↓
11. (Optional) Send command to Arduino
        SERIAL_ENABLED=true
        ↓
12. Return JSON response
```

---

# ✨ **Features ที่พัฒนา**

---

## 📱 **Web Application**

### **1. Main Detection Page**
```
┌────────────────────────────────────┐
│  Thai LPR System                   │
├────────────────────────────────────┤
│  [Choose File]                     │
│                                    │
│  📁 Upload รูปป้ายทะเบียน         │
│  🔍 กดปุ่ม Detect เพื่ออ่าน       │
└────────────────────────────────────┘
```

**Features:**
- ✅ File upload (JPEG, PNG)
- ✅ Show results instantly

---

### **2. Results Display**
```
┌────────────────────────────────────┐
│  ✅ Detection Successful!           │
├────────────────────────────────────┤
│  📋 Plate: กว 1234                 │
│  📍 Province: กรุงเทพมหานคร        │
│  ⭐ Confidence: 89%                │
│  🕐 Time: 2025-10-22 14:30         │
│                                    │
│  [รูปป้ายที่ตรวจจับได้]             │
└────────────────────────────────────┘
```

---

### **3. Records Page**
```
┌──────────────────────────────────────────┐
│  📊 Detection History                     │
├────┬──────────┬────────────┬──────┬──────┤
│ ID │ Plate    │ Province   │ Time │ Conf │
├────┼──────────┼────────────┼──────┼──────┤
│ 42 │ กว 1234  │ กรุงเทพฯ  │14:30 │ 89% │
│ 41 │ 1กก 5678 │ เชียงใหม่ │14:25 │ 92% │
│ 40 │ กข 9999  │ ภูเก็ต    │14:20 │ 87% │
└────┴──────────┴────────────┴──────┴──────┘

Features:
- View all detections
- Filter by date/province
- Export to CSV
- Click to see full details
```

---

### **4. Admin Dashboard**
```
┌────────────────────────────────────┐
│  👤 Admin Panel                     │
├────────────────────────────────────┤
│  📊 Total Detections: 152           │
│  📅 Today: 23                       │
│  ⭐ Avg Confidence: 91%            │
│                                    │
│  🔧 System Status:                  │
│  ✅ API: Running                    │
│  ✅ Database: Connected             │
│  ⚠️ Arduino: Not connected         │
│                                    │
│  ⚙️ Settings:                       │
│  SERIAL_ENABLED: false              │
│  GATE_TRIGGER_MODE: per_plate_cd    │
└────────────────────────────────────┘
```

---

## 🔌 **Arduino Integration**

### **🔗 จุดเชื่อมต่อระหว่าง Website กับ Arduino**

```
Website (Python)         USB Cable          Arduino (C++)
     ↓                       ↓                    ↓
api/main.py          /dev/cu.usbmodem     gate_control_wifi.ino
  บรรทัด 411             11201                บรรทัด 54
     ↓                       ↓                    ↓
send_open_gate()  ─────→  Serial  ─────→  Serial.read()
     ↓                       ↓                    ↓
"OPEN:กว1234"         (สัญญาณไฟฟ้า)         รับคำสั่ง
                                                ↓
                                          gate.write(90)
                                                ↓
                                          Servo หมุน!
```

### **Code ที่เชื่อมต่อ:**

**Python Side (api/main.py):**
```python
# บรรทัด 404-414
ok, reason = should_open(plate_text or "", conf)

if ok:
    print("[SERIAL] → OPEN", flush=True)
    send_open_gate(plate_text or "")  # ← 🔴 จุดเชื่อมต่อ!
```

**Python Serial (api/arduino.py):**
```python
# บรรทัด 42-43
ser.write(f"{cmd}\n".encode())  # ← 🔴 ส่งผ่าน USB!
response = ser.readline()       # ← 🔴 รับคำตอบกลับ
```

**Arduino Side (arduino/gate_control_wifi.ino):**
```cpp
// บรรทัด 52-65
void handleSerialCommands() {
  while (Serial.available()) {  // ← 🔴 รับจาก USB
    char c = Serial.read();
    processCommand(serialBuffer);
  }
}

// บรรทัด 102-114
void openGate(String plateText) {
  gate.write(OPEN_ANGLE);  // ← 🔴 Servo หมุน 90°!
  Serial.println("ACK:OPEN");  // ← 🔴 ส่งกลับ Python
}
```

---

### **Serial Commands:**

| Command | Description | Response |
|---------|-------------|----------|
| `PING` | Test connection | `PONG` |
| `OPEN` | Open gate | `ACK:OPEN` |
| `OPEN:กว1234` | Open with plate | `ACK:OPEN:กว1234` |
| `CLOSE` | Close gate | `ACK:CLOSE` |
| `STATUS` | Get status | `STATUS:CLOSED\|ANGLE:0\|UPTIME:123s` |

### **Gate Trigger Modes:**

**1. every_record**
```python
# เปิดทุกครั้งที่อ่านป้ายได้
GATE_TRIGGER_MODE=every_record
```

**2. per_plate_cooldown** (แนะนำ)
```python
# เปิดต่อเมื่อป้ายเดียวกันห่างกัน 30 วินาที
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=30
```

**3. never**
```python
# ไม่เปิดเลย (ใช้แค่อ่านป้าย)
GATE_TRIGGER_MODE=never
```

---

## 🔐 **Authentication System**

### **User Management:**
```python
# Create admin user
python create_admin.py

# Login
POST /auth/login
{
  "username": "admin",
  "password": "admin123"
}

# Response
{
  "access_token": "eyJ0eXAi...",
  "user": {
    "id": 1,
    "username": "admin",
    "is_admin": true
  }
}
```

**Protected Routes:**
- `/admin/*` - Admin only
- `/records` - Authenticated users
- `/detect` - Public

---

# 📊 **ผลการทดสอบ**

---

## 🎯 **Accuracy (ความแม่นยำ)**

### **YOLO Detector (หาป้าย):**
```
Training: 300 images
- Train: 210 images
- Valid: 60 images
- Test: 30 images

Results:
- Precision: 0.95
- Recall: 0.93
- mAP@0.5: 0.94

Conclusion: สามารถหาตำแหน่งป้ายได้แม่นยำ 94-95%
```

### **YOLO Reader (อ่านอักษร):**
```
Training: 500 character images
- Classes: ก-ฮ, 0-9, กก,กข,กท,... (76 classes)
- Train: 350 images
- Valid: 100 images
- Test: 50 images

Results:
- Precision: 0.91
- Recall: 0.87
- mAP@0.5: 0.89

Conclusion: อ่านตัวอักษรได้แม่นยำ 89-91%
```

### **Tesseract OCR:**
```
Test: 50 cropped plate images

Results:
- Perfect Match: 35/50 (70%)
- Partial Match: 10/50 (20%)
- Fail: 5/50 (10%)

Conclusion: ใช้ได้ดีเมื่อรูปชัดเจน แต่ต่ำกว่า YOLO
```

---

## ⚡ **Performance (ความเร็ว)**

### **Detection Speed:**
```
Hardware: MacBook Pro M1
- YOLO Detector: ~0.5 วินาที
- YOLO Reader: ~0.3 วินาที
- Tesseract OCR: ~0.4 วินาที
- Database Save: ~0.1 วินาที
- Total: ~2-3 วินาที

Hardware: PC (Intel i5, GTX 1050)
- YOLO Detector: ~1.2 วินาที
- YOLO Reader: ~0.8 วินาที
- Tesseract OCR: ~0.5 วินาที
- Database Save: ~0.1 วินาที
- Total: ~3-5 วินาที
```

**Conclusion:** ขึ้นอยู่กับสเปคเครื่อง แต่โดยเฉลี่ย 2-5 วินาที/รูป

---

## 📸 **Image Quality Requirements**

### **ทดสอบกับรูปหลากหลาย:**

| Condition | Success Rate | Note |
|-----------|--------------|------|
| ☀️ แสงสว่างดี ป้ายชัด | 95% | Best case |
| 🌤️ แสงปานกลาง | 89% | Good |
| 🌧️ แสงน้อย / มืด | 65% | Needs improvement |
| 📐 ป้ายเอียง < 30° | 85% | OK |
| 📐 ป้ายเอียง > 30° | 60% | Difficult |
| 💦 ป้ายสกปรก/เปียก | 70% | Challenging |
| 🔍 ป้ายเล็กเกินไป | 50% | Fail often |

**Recommendation:**
- ✅ ถ่ายในที่แสงสว่าง
- ✅ ป้ายตรง ไม่เอียง
- ✅ ระยะใกล้พอที่จะเห็นชัด
- ✅ ป้ายสะอาด ไม่เปียกน้ำ

---

## 🐛 **Known Issues**

### **1. ป้ายที่อ่านยาก:**
- ❌ ป้ายเก่า/จางมาก
- ❌ ป้ายถูกบัง (ด้วยของ/เทป)
- ❌ ป้ายบิดเบี้ยวมาก
- ❌ แสงสะท้อน (glare) จาก flash

### **2. การจำแนกตัวอักษร:**
- ⚠️ "0" (zero) กับ "O" (o)
- ⚠️ "1" กับ "ท"
- ⚠️ "8" กับ "บ"

### **3. Hardware:**
- ⚠️ Servo motor ต้องใช้ power supply แยก (ถ้าหนักเกิน 200g)
- ⚠️ Serial port อาจเปลี่ยนชื่อเมื่อ reconnect

---

# 🚀 **การใช้งาน**

---

## 💻 **การติดตั้ง**

### **1. Requirements:**
```
- Python 3.9+
- Tesseract OCR
- Arduino IDE (ถ้าต้องการใช้ hardware)
- Modern web browser
```

### **2. Installation:**
```bash
# Clone repository
git clone https://github.com/your-repo/thai-lpr-api.git
cd thai-lpr-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# แก้ไข .env ตามต้องการ
```

### **3. Run Server:**
```bash
# Development
python -m api.main

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Access
http://localhost:8000
```

---

## 📱 **การใช้งานบนมือถือ**

### **1. เชื่อมต่อ WiFi เดียวกัน:**
```bash
# หา IP ของเครื่อง server
ifconfig | grep "inet "  # macOS/Linux
ipconfig  # Windows

# สมมุติได้: 192.168.1.100
```

### **2. เปิดบนมือถือ:**
```
Safari/Chrome บนมือถือ
→ พิมพ์: http://192.168.1.100:8000
→ กด "Choose File"
→ เลือกรูปป้ายทะเบียน
→ กด "Detect Plate"
→ ดูผลลัพธ์
```

---

## 🔧 **การต่อ Arduino**

### **Wiring:**
```
Arduino UNO          Servo Motor SG90
  Pin 9  ───────────── Signal (Orange)
  5V     ───────────── VCC (Red)
  GND    ───────────── GND (Brown)
```

### **Upload Code:**
```
1. เปิด Arduino IDE
2. File → Open → arduino/gate_control_wifi.ino
3. Tools → Board → Arduino UNO
4. Tools → Port → /dev/cu.usbmodem... (เลือกตาม port ที่เสียบ)
5. Upload (→ button)
6. รอจน "Upload complete"
```

### **Test:**
```bash
# Serial Monitor (115200 baud)
PING
→ Response: PONG

OPEN
→ Response: ACK:OPEN
→ Servo หมุน 90° → รอ 2 วิ → หมุนกลับ 0°

STATUS
→ Response: STATUS:CLOSED|ANGLE:0|UPTIME:123s
```

---

## ⚙️ **Configuration (.env)**

```bash
# Server
APP_HOST=0.0.0.0
APP_PORT=8000

# Arduino
SERIAL_ENABLED=true  # เปิด/ปิด
SERIAL_PORT=/dev/cu.usbmodem1101  # macOS
# SERIAL_PORT=COM3  # Windows
SERIAL_BAUD=115200

# Gate Control
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=30

# Models
DETECTOR_WEIGHTS=models/detector/best.pt
READER_WEIGHTS=models/reader/best.pt

# OCR
OCR_LANG=tha+eng
TESSERACT_CMD=/opt/homebrew/bin/tesseract

# Database
DATABASE_URL=sqlite:///./data.db
```

---

# 🔮 **การพัฒนาต่อ**

---

## 🎯 **สิ่งที่ควรปรับปรุง**

### **1. AI Model:**
- 🔄 เพิ่ม training data (จาก 300 → 1000+ images)
- 🔄 Data augmentation (rotation, brightness, noise)
- 🔄 รองรับป้ายรถยนต์ 4 ล้อ
- 🔄 รองรับป้ายหลากสี (ขาว, เหลือง, เขียว)

### **2. Performance:**
- ⚡ Model optimization (quantization, pruning)
- ⚡ GPU acceleration (CUDA)
- ⚡ Batch processing
- ⚡ Caching results

### **3. Features:**
- 📱 Mobile app (React Native / Flutter)
- ☁️ Cloud deployment (AWS / Google Cloud)
- 📊 Analytics dashboard
- 🔔 Notification system

### **4. Accuracy:**
- 🎯 Better pre-processing (de-skewing, denoising)
- 🎯 Ensemble methods (combine multiple models)
- 🎯 Post-processing (spell checker, database lookup)

### **5. Security:**
- 🔐 HTTPS support
- 🔐 Rate limiting
- 🔐 Input validation
- 🔐 Session management

---

## 💡 **Ideas for Future**

### **1. Multiple Camera Support:**
```
Camera 1: หน้าทางเข้า (Detection)
Camera 2: หน้าทางออก (Detection)
Camera 3: ภายใน (Security)
```

### **2. Vehicle Classification:**
```
- มอเตอร์ไซค์
- รถยนต์
- รถบรรทุก
- รถตู้
```

### **3. Blacklist/Whitelist:**
```
Whitelist: รถของพนักงาน → เปิดอัตโนมัติ
Blacklist: รถที่ห้ามเข้า → แจ้งเตือน
Unknown: รถทั่วไป → แจ้งเตือน + ขออนุมัติ
```

### **4. Integration:**
```
- Line Notify: แจ้งเตือนเมื่อมีรถเข้า
- Email: รายงานประจำวัน
- Dashboard: Real-time monitoring
- Mobile App: Remote control
```

---

# 🎓 **สรุป**

---

## ✅ **สิ่งที่ทำสำเร็จ**

### **Technical:**
- ✅ ฝึก AI Model 2 ตัว (Detector + Reader)
- ✅ พัฒนา Full-stack Web Application
- ✅ Arduino Hardware Integration
- ✅ Database & Authentication

### **Learning:**
- ✅ Machine Learning / Deep Learning
- ✅ Computer Vision
- ✅ Web Development
- ✅ Hardware Programming
- ✅ System Integration

### **Results:**
- ✅ Accuracy: 89-95%
- ✅ Speed: 2-5 seconds
- ✅ Working prototype
- ✅ Usable on mobile

---

## 📚 **สิ่งที่ได้เรียนรู้**

### **1. AI/ML:**
- YOLO architecture
- Transfer learning
- Model training & evaluation
- OCR technology

### **2. Software Engineering:**
- FastAPI framework
- Async programming
- WebSocket real-time communication
- Database design

### **3. Hardware:**
- Arduino programming
- Serial communication
- Motor control
- Circuit design basics

### **4. Problem Solving:**
- Debugging ML models
- Handling edge cases
- Performance optimization
- User experience design

---

## 🎯 **Challenges & Solutions**

| Challenge | Solution |
|-----------|----------|
| ป้ายไทยอ่านยาก | ใช้ YOLO + Tesseract ร่วมกัน |
| Training data น้อย | Data augmentation |
| Speed ช้า | Optimize model size |
| Hardware ขัดข้อง | Protocol design + Error handling |
| Mobile compatibility | Responsive design + getUserMedia API |

---

## 💬 **Q&A**

### **Q1: ใช้งานได้จริงไหม?**
**A:** ได้! แต่เป็น prototype สำหรับการเรียนรู้ ยังไม่พร้อม production

### **Q2: ทำไมไม่ใช้ Cloud API?**
**A:** เพื่อเรียนรู้การฝึก Model เอง และทำงาน offline ได้

### **Q3: Accuracy 89% ต่ำไหม?**
**A:** สำหรับ prototype ที่ใช้ data น้อย (300 รูป) ถือว่าดีแล้ว สามารถปรับปรุงได้ด้วยข้อมูลมากขึ้น

### **Q4: เก็บข้อมูลส่วนบุคคลไหม?**
**A:** ไม่ เก็บแค่เลขทะเบียน, จังหวัด, เวลา ไม่มีข้อมูลเจ้าของรถ

### **Q5: License?**
**A:** Open Source (MIT License) ใช้ได้เพื่อการศึกษา

---

## 🙏 **ขอบคุณ**

<p align="center">
<strong>Thai License Plate Recognition System</strong><br/>
Senior Project - Computer Engineering<br/><br/>
Created by: [Your Team Name]<br/>
Advisor: [Advisor Name]<br/>
Year: 2568 (2025)<br/><br/>
🌟 GitHub: github.com/your-repo/thai-lpr-api<br/>
📧 Contact: your-email@example.com
</p>

---

## 📎 **Appendix**

### **A. File Structure:**
```
thai-lpr-api/
├── api/
│   ├── main.py           # FastAPI app
│   ├── models.py         # Database models
│   ├── local_models.py   # YOLO loader
│   ├── ocr.py           # Tesseract wrapper
│   ├── arduino.py       # Serial communication
│   └── auth.py          # Authentication
├── models/
│   ├── detector/best.pt # Detection model
│   └── reader/best.pt   # Reading model
├── static/
│   ├── index.html       # Frontend
│   ├── js/app.js        # JavaScript
│   └── css/style.css    # Styles
├── arduino/
│   └── gate_control_wifi.ino
├── .env                 # Configuration
├── requirements.txt     # Python deps
└── README.md           # Documentation
```

### **B. Dependencies:**
```
fastapi==0.115.0
uvicorn==0.30.6
ultralytics==8.3.32
pytesseract==0.3.13
opencv-python==4.11.0.86
pyserial==3.5
sqlalchemy==2.0.35
python-dotenv==1.0.1
```

### **C. API Endpoints:**
```
POST   /detect            # Detect plate
GET    /records           # Get all records
DELETE /records/{id}      # Delete record
POST   /auth/login        # Login
POST   /auth/register     # Register
WS     /ws               # WebSocket
GET    /arduino/status    # Arduino status
POST   /arduino/open      # Manual open gate
```

---

<p align="center">
<strong style="font-size: 1.5em;">THE END</strong><br/>
Thank you for your attention! 🙏
</p>

