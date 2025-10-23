# 🚗 Thai License Plate Recognition System
## **Automatic Motorcycle License Plate Reader**

<p align="center">
  <strong>Senior Project - Computer Engineering</strong>
</p>

---

## 📋 **Table of Contents**

1. ⭐ What is this project?
2. 🎯 Goals
3. 💻 Technology Used
4. 🏗️ System Design
5. ✨ Features We Built
6. 📊 Test Results
7. 🚀 How to Use
8. 🔮 Future Work

---

# ⭐ **What is this project?**

---

## 📖 **Simple Explanation**

An automatic system that reads Thai motorcycle license plates using AI.

### **Input:**
- 📸 Photo of a license plate (Upload or Live Camera)

### **What it does:**
- 🤖 AI reads the plate using YOLO + Tesseract OCR
- 💾 Saves to database

### **Output:**
- 📝 Plate number (e.g., "กว 1234")
- 📍 Province name (e.g., "Bangkok")
- ⭐ Confidence score (how sure the AI is)
- 🖼️ Cropped plate image

### **(Optional) Hardware:**
- 🔧 Control Arduino + Servo Motor
- 🚪 Auto open/close gate

---

## 🎬 **Quick Example**

### **Input:**
```
Photo of motorcycle
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
  "province_text": "Bangkok",
  "confidence": 0.89,
  "timestamp": "2025-10-22 14:30:00"
}
```

---

# 🎯 **Goals**

---

## 🎓 **Main Goals**

### **1. Learn AI & Machine Learning**
- ✅ Train YOLO model for finding plates
- ✅ Train YOLO model for reading text
- ✅ Understand OCR technology

### **2. Build Full-Stack Web App**
- ✅ Backend: FastAPI (Python)
- ✅ Frontend: HTML + JavaScript
- ✅ Database: SQLite
- ✅ Real-time: WebSocket

### **3. Connect Hardware**
- ✅ Program Arduino (C++)
- ✅ Serial communication (USB)
- ✅ Control servo motor

### **4. Make it Actually Work**
- ✅ Easy-to-use web interface
- ✅ Works on mobile & desktop
- ✅ Live camera detection
- ✅ Save all records

---

## 🚫 **What This Is NOT**

❌ Not for commercial use  
❌ Not designed for large scale  
❌ No cloud deployment  
❌ No mobile app

> **Note:** This is a **Proof of Concept** and **Learning Project**

---

# 💻 **Technology Used**

---

## 🧠 **AI & Machine Learning**

### **1. YOLOv11 (Ultralytics)**

**For Finding License Plates:**
```
Input:  Full image
Output: Box around the plate
Model:  models/detector/best.pt
Data:   ~300 images (Train/Valid/Test)
```

**For Reading Characters:**
```
Input:  Cropped plate image
Output: Each character
Model:  models/reader/best.pt
Data:   ~500 character images
```

**Why YOLO?**
- ⚡ Fast: Real-time
- 🎯 Accurate: Best results
- 🛠️ Easy to use
- 📚 Good documentation

---

### **2. Tesseract OCR**

```
Input:  Plate image (cleaned up)
Output: Text it can read
Config: Thai + English
```

**Why do we need Tesseract?**
- 🛡️ Backup: If YOLO fails
- 📊 Compare: Check both results
- 🔤 Flexible: Supports many languages

---

## 🌐 **Backend**

### **FastAPI (Python)**

```python
# Example API endpoint
@app.post("/detect")
async def detect(file: UploadFile):
    # 1. Get image
    # 2. YOLO finds plate
    # 3. YOLO reads text
    # 4. Tesseract backup
    # 5. Save to database
    # 6. Return result
    return {"plate_text": "กว 1234", ...}
```

**Features:**
- ✅ Fast (async/await)
- ✅ Auto documentation (Swagger)
- ✅ Input validation
- ✅ WebSocket support
- ✅ Easy to use

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

-- Table: users (login)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    hashed_password TEXT,
    is_admin BOOLEAN,
    created_at TIMESTAMP
);
```

**Why SQLite?**
- ✅ No extra setup needed
- ✅ One file = easy backup
- ✅ Fast enough for prototype
- ✅ Can upgrade to PostgreSQL later

---

## 🎨 **Frontend**

### **HTML + JavaScript + CSS**

```javascript
// Live Camera Feature
navigator.mediaDevices.getUserMedia({ 
    video: { facingMode: 'environment' } 
})
.then(stream => {
    video.srcObject = stream;
    // Take photo every 2 seconds
    setInterval(captureAndDetect, 2000);
});
```

**Features:**
- ✅ Upload file
- ✅ Live camera (phone/webcam)
- ✅ Real-time results
- ✅ Works on mobile
- ✅ Admin page

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
  gate.write(OPEN_ANGLE);  // Open
  delay(2000);             // Wait 2 seconds
  gate.write(CLOSE_ANGLE); // Close
}
```

**Commands:**
```
Computer → Arduino: "OPEN:กว1234\n"
Arduino → Computer: "ACK:OPEN:กว1234\n"

Available: PING, OPEN, CLOSE, STATUS
Speed: 115200 baud
```

---

# 🏗️ **System Design**

---

## 📐 **How Everything Connects**

```
┌─────────────────────────────────────────────┐
│          User Interface                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Desktop │  │ Mobile  │  │ Camera  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘    │
└───────┼───────────┼────────────┼──────────┘
        │           │            │
        └───────────┴────────────┘
                    │ Internet
┌───────────────────┼──────────────────────────┐
│         FastAPI Server (Port 8000)           │
│  ┌─────────────────────────────────────┐    │
│  │ Pages:                               │    │
│  │ - POST /detect (read plate)          │    │
│  │ - GET  /records (view history)       │    │
│  │ - WS   /ws (live updates)            │    │
│  └─────────────────────────────────────┘    │
└───────────────────┼──────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────┼──────────┐    ┌──────┼──────────┐
│  AI Models       │    │  Storage        │
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
│  └────────────┘  │
└──────────────────┘
        │
┌───────┼────────────┐
│  Hardware (Optional)│
│  ┌──────────┐      │
│  │ Arduino  │      │
│  └────┬─────┘      │
│  ┌────┴──────┐     │
│  │  Servo    │     │
│  │  Motor    │     │
│  └───────────┘     │
└────────────────────┘
```

---

## 🔄 **Step-by-Step Process**

```
1. User uploads image or uses camera
        ↓
2. FastAPI receives request
        ↓
3. Clean up image (resize, fix brightness)
        ↓
4. YOLO Detector finds the plate
        ├─ Success → Box location
        └─ Fail → Return error
        ↓
5. Crop the plate area
        ↓
6. YOLO Reader reads text
        ├─ Success → Characters
        └─ Fail → Try Tesseract
        ↓
7. Tesseract OCR (if needed)
        ↓
8. Figure out province
        "กว" → "Bangkok"
        ↓
9. Save to database
        ├─ plate_records table
        └─ Save plate image
        ↓
10. Send live update (WebSocket)
        ↓
11. (Optional) Tell Arduino to open gate
        If SERIAL_ENABLED=true
        ↓
12. Return JSON result
```

---

# ✨ **Features We Built**

---

## 📱 **Web Application**

### **1. Main Page**
```
┌────────────────────────────────────┐
│  Thai LPR System                   │
├────────────────────────────────────┤
│  [Choose File] [Live Camera]       │
│                                    │
│  📁 Upload a photo or              │
│  📷 Use camera for live reading    │
└────────────────────────────────────┘
```

**What you can do:**
- ✅ Upload photo (JPEG, PNG)
- ✅ Use live camera
- ✅ Auto-detect every 2 seconds
- ✅ See results instantly

---

### **2. Results Display**
```
┌────────────────────────────────────┐
│  ✅ Success!                        │
├────────────────────────────────────┤
│  📋 Plate: กว 1234                 │
│  📍 Province: Bangkok               │
│  ⭐ Confidence: 89%                │
│  🕐 Time: 2025-10-22 14:30         │
│                                    │
│  [Photo of detected plate]         │
└────────────────────────────────────┘
```

---

### **3. History Page**
```
┌──────────────────────────────────────────┐
│  📊 All Detections                        │
├────┬──────────┬────────────┬──────┬──────┤
│ ID │ Plate    │ Province   │ Time │ Conf │
├────┼──────────┼────────────┼──────┼──────┤
│ 42 │ กว 1234  │ Bangkok    │14:30 │ 89% │
│ 41 │ 1กก 5678 │ ChiangMai  │14:25 │ 92% │
│ 40 │ กข 9999  │ Phuket     │14:20 │ 87% │
└────┴──────────┴────────────┴──────┴──────┘

Features:
- See all detections
- Filter by date/province
- Export to CSV
- Click for details
```

---

### **4. Admin Panel**
```
┌────────────────────────────────────┐
│  👤 Admin Panel                     │
├────────────────────────────────────┤
│  📊 Total: 152 detections           │
│  📅 Today: 23                       │
│  ⭐ Average: 91% confidence        │
│                                    │
│  🔧 System Status:                  │
│  ✅ API: Running                    │
│  ✅ Database: Connected             │
│  ⚠️ Arduino: Not connected         │
│                                    │
│  ⚙️ Settings:                       │
│  SERIAL_ENABLED: false              │
│  GATE_TRIGGER_MODE: cooldown        │
└────────────────────────────────────┘
```

---

## 🎥 **Live Camera**

### **How it works:**
```javascript
1. Ask permission to use camera
2. getUserMedia() → Camera opens
3. Show video on screen
4. Every 2 seconds:
   - Take a photo
   - Convert to JPEG
   - Send to /detect
   - Show result
5. Keep going until stopped
```

**Works on:**
- ✅ Desktop webcam
- ✅ Phone front camera
- ✅ Phone back camera
- ✅ Auto-focus

---

## 🔌 **Arduino Connection**

### **🔗 How Website Connects to Arduino**

```
Website (Python)         USB Cable          Arduino (C++)
     ↓                       ↓                    ↓
api/main.py          /dev/cu.usbmodem     gate_control_wifi.ino
  line 411                11201                line 54
     ↓                       ↓                    ↓
send_open_gate()  ─────→  Serial  ─────→  Serial.read()
     ↓                       ↓                    ↓
"OPEN:กว1234"        (Electric signal)     Get command
                                                ↓
                                          gate.write(90)
                                                ↓
                                          Servo moves!
```

### **Code That Connects:**

**Python Side (api/main.py):**
```python
# Line 404-414
ok, reason = should_open(plate_text or "", conf)

if ok:
    print("[SERIAL] → OPEN", flush=True)
    send_open_gate(plate_text or "")  # ← 🔴 Connection point!
```

**Python Serial (api/arduino.py):**
```python
# Line 42-43
ser.write(f"{cmd}\n".encode())  # ← 🔴 Send via USB!
response = ser.readline()       # ← 🔴 Get response back
```

**Arduino Side (gate_control_wifi.ino):**
```cpp
// Line 52-65
void handleSerialCommands() {
  while (Serial.available()) {  // ← 🔴 Receive from USB
    char c = Serial.read();
    processCommand(serialBuffer);
  }
}

// Line 102-114
void openGate(String plateText) {
  gate.write(OPEN_ANGLE);  // ← 🔴 Servo moves 90°!
  Serial.println("ACK:OPEN");  // ← 🔴 Send back to Python
}
```

---

### **Commands you can send:**

| Command | What it does | Response |
|---------|-------------|----------|
| `PING` | Test if connected | `PONG` |
| `OPEN` | Open gate | `ACK:OPEN` |
| `OPEN:กว1234` | Open with plate info | `ACK:OPEN:กว1234` |
| `CLOSE` | Close gate | `ACK:CLOSE` |
| `STATUS` | Check status | `STATUS:CLOSED\|ANGLE:0\|...` |

### **Gate Modes:**

**1. every_record**
```python
# Open gate every time we read a plate
GATE_TRIGGER_MODE=every_record
```

**2. per_plate_cooldown** (Best!)
```python
# Wait 30 seconds before opening for same plate
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=30
```

**3. never**
```python
# Just read plates, don't open gate
GATE_TRIGGER_MODE=never
```

---

## 🔐 **Login System**

### **User Management:**
```python
# Create admin account
python create_admin.py

# Login
POST /auth/login
{
  "username": "admin",
  "password": "admin123"
}

# You get back
{
  "access_token": "eyJ0eXAi...",
  "user": {
    "id": 1,
    "username": "admin",
    "is_admin": true
  }
}
```

**Protected pages:**
- `/admin/*` - Admin only
- `/records` - Must login
- `/detect` - Anyone can use

---

# 📊 **Test Results**

---

## 🎯 **How Accurate Is It?**

### **YOLO Detector (Finding plates):**
```
Training data: 300 images
- Train: 210 images
- Valid: 60 images
- Test: 30 images

Results:
- Precision: 0.95 (95% correct when it finds something)
- Recall: 0.93 (93% finds all plates)
- mAP@0.5: 0.94 (overall score)

Summary: Can find plates 94-95% of the time
```

### **YOLO Reader (Reading text):**
```
Training data: 500 character images
- Classes: Thai letters + numbers (76 types)
- Train: 350 images
- Valid: 100 images
- Test: 50 images

Results:
- Precision: 0.91
- Recall: 0.87
- mAP@0.5: 0.89

Summary: Reads text correctly 89-91% of the time
```

### **Tesseract OCR:**
```
Test: 50 plate images

Results:
- Perfect: 35/50 (70%)
- Partial: 10/50 (20%)
- Failed: 5/50 (10%)

Summary: Works OK when image is clear, not as good as YOLO
```

---

## ⚡ **How Fast Is It?**

### **Speed Test:**
```
Computer: MacBook Pro M1
- Find plate: ~0.5 seconds
- Read text: ~0.3 seconds
- OCR backup: ~0.4 seconds
- Save to database: ~0.1 seconds
- Total: ~2-3 seconds

Computer: PC (Intel i5, GTX 1050)
- Find plate: ~1.2 seconds
- Read text: ~0.8 seconds
- OCR backup: ~0.5 seconds
- Save to database: ~0.1 seconds
- Total: ~3-5 seconds
```

**Summary:** Depends on your computer, usually 2-5 seconds per image

---

## 📸 **What Photos Work Best?**

### **Different conditions tested:**

| Condition | Success Rate | Notes |
|-----------|--------------|-------|
| ☀️ Good light, clear plate | 95% | Best! |
| 🌤️ Medium light | 89% | Good |
| 🌧️ Dark/low light | 65% | Needs work |
| 📐 Plate tilted < 30° | 85% | OK |
| 📐 Plate tilted > 30° | 60% | Hard |
| 💦 Dirty/wet plate | 70% | Difficult |
| 🔍 Plate too small | 50% | Often fails |

**Tips for best results:**
- ✅ Take photo in good light
- ✅ Keep plate straight
- ✅ Get close enough
- ✅ Clean plate (not wet/dirty)

---

## 🐛 **Known Problems**

### **1. Plates that don't work well:**
- ❌ Very old/faded plates
- ❌ Plate covered by tape/stickers
- ❌ Plate very bent/damaged
- ❌ Light reflection (flash glare)

### **2. Characters that confuse AI:**
- ⚠️ "0" (zero) vs "O" (letter)
- ⚠️ "1" vs Thai "ท"
- ⚠️ "8" vs Thai "บ"

### **3. Hardware issues:**
- ⚠️ Servo needs extra power if heavy
- ⚠️ USB port name might change

---

# 🚀 **How to Use**

---

## 💻 **Setup**

### **1. What you need:**
```
- Python 3.9 or newer
- Tesseract OCR
- Arduino IDE (if using hardware)
- Web browser (Chrome/Safari/Firefox)
```

### **2. Install:**
```bash
# Get the code
git clone https://github.com/your-repo/thai-lpr-api.git
cd thai-lpr-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt

# Setup settings
cp .env.example .env
# Edit .env file as needed
```

### **3. Start server:**
```bash
# For development
python -m api.main

# For production
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Open in browser
http://localhost:8000
```

---

## 📱 **Use on Phone**

### **1. Connect to same WiFi:**
```bash
# Find your computer's IP
ifconfig | grep "inet "  # Mac/Linux
ipconfig  # Windows

# Let's say you get: 192.168.1.100
```

### **2. Open on phone:**
```
Open Safari/Chrome on phone
→ Type: http://192.168.1.100:8000
→ Click "Live Camera"
→ Allow camera access
→ Point at license plate
→ System reads automatically
```

---

## 🔧 **Connect Arduino**

### **Wiring:**
```
Arduino UNO          Servo Motor SG90
  Pin 9  ────────────  Signal (Orange wire)
  5V     ────────────  VCC (Red wire)
  GND    ────────────  GND (Brown wire)
```

### **Upload Code:**
```
1. Open Arduino IDE
2. File → Open → arduino/gate_control_wifi.ino
3. Tools → Board → Arduino UNO
4. Tools → Port → Choose your port
5. Click Upload (→ button)
6. Wait for "Upload complete"
```

### **Test:**
```bash
# Open Serial Monitor (115200 baud)
Type: PING
→ Should see: PONG

Type: OPEN
→ Should see: ACK:OPEN
→ Servo moves 90° → waits 2 sec → moves back 0°

Type: STATUS
→ Should see: STATUS:CLOSED|ANGLE:0|UPTIME:123s
```

---

## ⚙️ **Settings File (.env)**

```bash
# Server
APP_HOST=0.0.0.0
APP_PORT=8000

# Arduino
SERIAL_ENABLED=true  # turn on/off
SERIAL_PORT=/dev/cu.usbmodem1101  # Mac
# SERIAL_PORT=COM3  # Windows
SERIAL_BAUD=115200

# Gate Control
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=30

# AI Models
DETECTOR_WEIGHTS=models/detector/best.pt
READER_WEIGHTS=models/reader/best.pt

# OCR
OCR_LANG=tha+eng
TESSERACT_CMD=/opt/homebrew/bin/tesseract

# Database
DATABASE_URL=sqlite:///./data.db
```

---

# 🔮 **Future Improvements**

---

## 🎯 **What Could Be Better**

### **1. AI Model:**
- 🔄 More training data (300 → 1000+ images)
- 🔄 Better data variety (angles, lighting, weather)
- 🔄 Support 4-wheel car plates
- 🔄 Support different plate colors

### **2. Speed:**
- ⚡ Make model smaller/faster
- ⚡ Use GPU (graphics card)
- ⚡ Process multiple images at once
- ⚡ Remember recent results

### **3. New Features:**
- 📱 Make a mobile app
- ☁️ Put on cloud (AWS/Google Cloud)
- 📊 Better statistics page
- 🔔 Send notifications

### **4. More Accurate:**
- 🎯 Better image cleanup
- 🎯 Use multiple models together
- 🎯 Spell checker for results

### **5. Security:**
- 🔐 Add HTTPS (encrypted connection)
- 🔐 Limit requests (prevent abuse)
- 🔐 Better input checking
- 🔐 Better session management

---

## 💡 **Ideas for Later**

### **1. Multiple Cameras:**
```
Camera 1: Entry gate
Camera 2: Exit gate
Camera 3: Inside parking
```

### **2. Vehicle Types:**
```
- Motorcycle
- Car
- Truck
- Van
```

### **3. Lists:**
```
Whitelist: Employee vehicles → auto open
Blacklist: Banned vehicles → alert
Unknown: Regular vehicles → ask permission
```

### **4. Connect to:**
```
- Line Notify: Alert when car enters
- Email: Daily report
- Dashboard: Live monitoring
- Mobile App: Remote control
```

---

# 🎓 **Summary**

---

## ✅ **What We Did**

### **Technical:**
- ✅ Trained 2 AI models (Detector + Reader)
- ✅ Built full web application
- ✅ Connected Arduino hardware
- ✅ Made live camera work
- ✅ Added database & login

### **Learning:**
- ✅ Machine Learning / AI
- ✅ Computer Vision
- ✅ Web Development
- ✅ Hardware Programming
- ✅ Putting systems together

### **Results:**
- ✅ Accuracy: 89-95%
- ✅ Speed: 2-5 seconds
- ✅ Works on mobile
- ✅ Actually functions

---

## 📚 **What We Learned**

### **1. AI/ML:**
- How YOLO works
- How to train models
- How to test accuracy
- OCR technology

### **2. Software:**
- FastAPI framework
- Async programming
- Real-time communication
- Database design

### **3. Hardware:**
- Arduino programming
- Serial communication
- Motor control
- Basic circuits

### **4. Problem Solving:**
- Fixing AI errors
- Handling edge cases
- Making things faster
- Good user experience

---

## 🎯 **Challenges We Faced**

| Problem | How We Fixed It |
|---------|----------------|
| Thai text hard to read | Used YOLO + Tesseract together |
| Not enough training data | Data augmentation |
| Too slow | Made model smaller |
| Hardware bugs | Good error handling |
| Mobile compatibility | Responsive design |

---

## 💬 **Common Questions**

### **Q1: Does it really work?**
**A:** Yes! But it's a learning project, not ready for commercial use.

### **Q2: Why not use Google Cloud?**
**A:** We wanted to learn how to train our own models and work offline.

### **Q3: Is 89% accuracy good enough?**
**A:** For a student project with limited data (300 images), yes! Can improve with more data.

### **Q4: Do you save personal information?**
**A:** No. Only plate number, province, time. No owner info.

### **Q5: Can I use this code?**
**A:** Yes! It's open source (MIT License) for educational use.

---

## 🙏 **Thank You**

<p align="center">
<strong>Thai License Plate Recognition System</strong><br/>
Senior Project - Computer Engineering<br/><br/>
Created by: [Your Team Name]<br/>
Advisor: [Advisor Name]<br/>
Year: 2025<br/><br/>
🌟 GitHub: github.com/your-repo/thai-lpr-api<br/>
📧 Contact: your-email@example.com
</p>

---

## 📎 **Extra Info**

### **A. File Organization:**
```
thai-lpr-api/
├── api/
│   ├── main.py           # Main app
│   ├── models.py         # Database
│   ├── local_models.py   # YOLO
│   ├── ocr.py           # Tesseract
│   ├── arduino.py       # Hardware
│   └── auth.py          # Login
├── models/
│   ├── detector/best.pt # Find plates
│   └── reader/best.pt   # Read text
├── static/
│   ├── index.html       # Web page
│   ├── js/app.js        # JavaScript
│   └── css/style.css    # Design
├── arduino/
│   └── gate_control_wifi.ino
├── .env                 # Settings
├── requirements.txt     # Python packages
└── README.md           # Instructions
```

### **B. What You Need to Install:**
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

### **C. Website Pages:**
```
POST   /detect            # Read plate
GET    /records           # View history
DELETE /records/{id}      # Delete record
POST   /auth/login        # Login
POST   /auth/register     # Sign up
WS     /ws               # Live updates
GET    /arduino/status    # Hardware status
POST   /arduino/open      # Manual open gate
```

---

<p align="center">
<strong style="font-size: 1.5em;">THE END</strong><br/>
Thank you! 🙏
</p>

