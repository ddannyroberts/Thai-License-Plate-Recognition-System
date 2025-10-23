# 🔧 คู่มือติดตั้ง Arduino + เชื่อมต่อกับ Website
## **Step-by-Step Guide**

---

## 📋 **ภาพรวม**

```
Website (FastAPI) ←─ USB Cable ─→ Arduino UNO ←─ สาย 3 เส้น ─→ Servo Motor
     (คอมพิวเตอร์)                    (ตัวควบคุม)              (ไม้กั้น)
```

---

# 🛠️ **Part 1: ติดตั้ง Arduino**

---

## 📦 **สิ่งที่ต้องเตรียม**

### **Hardware:**
- ✅ Arduino UNO (หรือ compatible board)
- ✅ Servo Motor SG90
- ✅ สายไฟ 3 เส้น (มักมากับ Servo)
- ✅ สาย USB Type-B (สำหรับต่อ Arduino กับคอม)
- ✅ Breadboard (ถ้าสะดวก แต่ไม่จำเป็น)

### **Software:**
- ✅ Arduino IDE (ดาวน์โหลดจาก: https://www.arduino.cc/en/software)
- ✅ คอมพิวเตอร์ (macOS/Windows/Linux)

---

## 🔌 **ขั้นตอนที่ 1: ต่อสาย Servo Motor**

### **การต่อสาย:**

```
Arduino UNO                     Servo Motor SG90
┌──────────────────┐           ┌─────────────┐
│                  │           │             │
│  Digital Pin 9   ├───────────┤ Signal      │ สายสีส้ม/เหลือง
│                  │           │             │
│  5V              ├───────────┤ VCC (Power) │ สายสีแดง
│                  │           │             │
│  GND             ├───────────┤ GND         │ สายสีน้ำตาล/ดำ
│                  │           │             │
└──────────────────┘           └─────────────┘
```

### **วิธีต่อ:**

1. **ปิด Arduino ก่อน** (ถอดสาย USB ออก)

2. **ต่อสาย Servo:**
   - 🟠 **Signal (สายส้ม)** → ต่อเข้า **Pin 9** ของ Arduino
   - 🔴 **VCC (สายแดง)** → ต่อเข้า **5V** ของ Arduino
   - 🟤 **GND (สายน้ำตาล)** → ต่อเข้า **GND** ของ Arduino

3. **เช็คอีกครั้ง:**
   - ✅ Signal → Pin 9
   - ✅ VCC → 5V
   - ✅ GND → GND

> ⚠️ **คำเตือน:** ถ้าต่อผิด อาจทำให้ Servo หรือ Arduino เสียหายได้!

---

## 💻 **ขั้นตอนที่ 2: ติดตั้ง Arduino IDE**

### **macOS:**
```bash
1. ดาวน์โหลดจาก: https://www.arduino.cc/en/software
2. เปิดไฟล์ .dmg
3. ลาก Arduino.app ไปใส่ในโฟลเดอร์ Applications
4. เปิด Arduino IDE
```

### **Windows:**
```bash
1. ดาวน์โหลด .exe จาก: https://www.arduino.cc/en/software
2. Run installer
3. Next > Next > Install
4. เปิด Arduino IDE
```

### **Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install arduino

# หรือดาวน์โหลด .tar.xz จาก website
```

---

## 📂 **ขั้นตอนที่ 3: เปิดไฟล์ Arduino**

### **1. เปิด Arduino IDE**

### **2. เปิดไฟล์:**
```
File → Open → เลือกไฟล์
/Users/dannyroberts/Documents/thai-lpr-api/arduino/gate_control_wifi.ino
```

### **3. จะเห็นโค้ดหน้าตาประมาณนี้:**
```cpp
#include <Servo.h>

const int SERVO_PIN = 9;
const int OPEN_ANGLE = 90;
const int CLOSE_ANGLE = 0;

Servo gate;

void setup() {
  gate.attach(SERVO_PIN);
  Serial.begin(115200);
  ...
}
```

---

## 🔧 **ขั้นตอนที่ 4: ตั้งค่า Arduino IDE**

### **1. เลือก Board:**
```
Tools → Board → Arduino AVR Boards → Arduino UNO
```

### **2. เชื่อมต่อ Arduino กับคอม:**
- เสียบสาย USB เข้ากับ Arduino
- ปลายอีกด้านเสียบเข้าคอมพิวเตอร์

### **3. เลือก Port:**

**macOS:**
```
Tools → Port → /dev/cu.usbmodem14201 (Arduino Uno)
               หรือ /dev/cu.usbmodem* (เลือกที่มี Arduino)
```

**Windows:**
```
Tools → Port → COM3 (Arduino Uno)
               หรือ COM4, COM5, ... (ดูจาก Device Manager)
```

**Linux:**
```
Tools → Port → /dev/ttyACM0 (Arduino Uno)
               หรือ /dev/ttyUSB0
```

> 💡 **ไม่เห็น Port?** → ลองถอดแล้วเสียบใหม่ หรือติดตั้ง Driver

---

## ⬆️ **ขั้นตอนที่ 5: Upload โค้ดไปที่ Arduino**

### **1. กดปุ่ม Verify (✓):**
```
Sketch → Verify/Compile
หรือกดปุ่ม ✓ มุมซ้ายบน
```

รอจนเห็น:
```
Compiling sketch...
Done compiling.
```

### **2. กดปุ่ม Upload (→):**
```
Sketch → Upload
หรือกดปุ่ม → ข้างๆ ปุ่ม ✓
```

จะเห็น:
```
Uploading...
avrdude: writing flash...
avrdude: done.
Thank you.
```

### **3. รอจนเสร็จ:**
```
Done uploading.
```

🎉 **สำเร็จ!** Arduino พร้อมใช้งานแล้ว!

---

## 🧪 **ขั้นตอนที่ 6: ทดสอบ Arduino**

### **1. เปิด Serial Monitor:**
```
Tools → Serial Monitor
หรือกด Ctrl+Shift+M (Cmd+Shift+M บน Mac)
```

### **2. ตั้งค่า:**
- เลือก **115200 baud** ที่มุมขวาล่าง
- เลือก **Newline** หรือ **Both NL & CR**

### **3. ทดสอบ:**

**Test 1: PING**
```
พิมพ์: PING
กด Send

ต้องเห็น:
→ PONG
```

**Test 2: OPEN**
```
พิมพ์: OPEN
กด Send

ต้องเห็น:
→ ACK:OPEN
→ Servo หมุนไป 90° (ไม้กั้นเปิด)
→ รอ 2 วินาที
→ Servo หมุนกลับ 0° (ไม้กั้นปิด)
```

**Test 3: STATUS**
```
พิมพ์: STATUS
กด Send

ต้องเห็น:
→ STATUS:CLOSED|ANGLE:0|UPTIME:123s
```

✅ **ถ้าทดสอบผ่านทั้ง 3 ข้อ แสดงว่า Arduino พร้อมแล้ว!**

---

# 🌐 **Part 2: เชื่อมต่อกับ Website**

---

## 📝 **ขั้นตอนที่ 1: สร้างไฟล์ .env**

### **1. ไปที่ folder โปรเจค:**
```bash
cd /Users/dannyroberts/Documents/thai-lpr-api
```

### **2. สร้างไฟล์ .env:**
```bash
touch .env
```

### **3. เปิดด้วย Text Editor:**
```bash
# macOS
open -a TextEdit .env

# หรือใช้ VS Code
code .env
```

---

## ⚙️ **ขั้นตอนที่ 2: ใส่การตั้งค่า**

### **คัดลอกนี้ลงในไฟล์ .env:**

```bash
# ===== FastAPI Server =====
APP_HOST=0.0.0.0
APP_PORT=8000

# ===== Arduino Serial Connection =====
SERIAL_ENABLED=true
SERIAL_PORT=/dev/cu.usbmodem14201
SERIAL_BAUD=115200

# ===== Gate Control =====
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=30

# ===== AI Models =====
DETECTOR_WEIGHTS=models/detector/best.pt
READER_WEIGHTS=models/reader/best.pt

# ===== Database =====
DATABASE_URL=sqlite:///./data.db

# ===== OCR Settings =====
OCR_LANG=tha+eng
TESSERACT_CMD=/opt/homebrew/bin/tesseract

# ===== Plate Validation =====
FORCE_OPEN_ALWAYS=false
PLATE_STRICT=false
```

---

## 🔍 **ขั้นตอนที่ 3: หา Port ของ Arduino**

### **macOS:**
```bash
ls /dev/cu.*usb*

# จะเห็นประมาณ:
/dev/cu.usbmodem14201
/dev/cu.usbmodem1101
```

**แก้ใน .env:**
```bash
SERIAL_PORT=/dev/cu.usbmodem14201  # ← เปลี่ยนตามที่เจอ
```

### **Windows:**
```
1. เปิด Device Manager
2. Ports (COM & LPT)
3. จะเห็น: Arduino Uno (COM3)
```

**แก้ใน .env:**
```bash
SERIAL_PORT=COM3  # ← เปลี่ยนตาม port ที่เจอ
```

### **Linux:**
```bash
ls /dev/ttyACM* /dev/ttyUSB*

# จะเห็น:
/dev/ttyACM0
```

**แก้ใน .env:**
```bash
SERIAL_PORT=/dev/ttyACM0  # ← เปลี่ยนตามที่เจอ
```

---

## 🚀 **ขั้นตอนที่ 4: รันเซิร์ฟเวอร์**

### **1. Activate virtual environment:**
```bash
cd /Users/dannyroberts/Documents/thai-lpr-api
source .venv/bin/activate
```

### **2. รันเซิร์ฟเวอร์:**
```bash
python -m api.main
```

### **3. เช็คว่าเชื่อมต่อสำเร็จ:**

ต้องเห็นข้อความ:
```
[INFO] 🟠 Using local YOLO DETECTOR from: models/detector/best.pt
[INFO] 🔵 Using local YOLO READER   from: models/reader/best.pt
[ARDUINO] Connected to /dev/cu.usbmodem14201
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **เห็น "[ARDUINO] Connected" = เชื่อมต่อสำเร็จ!**

---

## 🧪 **ขั้นตอนที่ 5: ทดสอบจาก Website**

### **1. เปิดเบราว์เซอร์:**
```
http://localhost:8000
```

### **2. อัปโหลดรูปป้ายทะเบียน:**
- กด "Choose File"
- เลือกรูป
- กด "Detect Plate"

### **3. สังเกต:**
- ✅ ระบบอ่านป้ายได้
- ✅ บันทึกลง Database
- ✅ Servo Motor หมุน! (ไม้กั้นเปิด)
- ✅ รอ 2 วินาที
- ✅ Servo หมุนกลับ (ไม้กั้นปิด)

---

# 🎛️ **การตั้งค่าเพิ่มเติม**

---

## 🔧 **โหมดการเปิดไม้กั้น**

แก้ในไฟล์ `.env`:

### **1. every_record** (เปิดทุกครั้ง)
```bash
GATE_TRIGGER_MODE=every_record
```
- ✅ เปิดทุกครั้งที่อ่านป้ายได้
- ⚠️ อาจเปิดบ่อยเกินไป

### **2. per_plate_cooldown** (แนะนำ!)
```bash
GATE_TRIGGER_MODE=per_plate_cooldown
OPEN_COOLDOWN_SEC=30
```
- ✅ ป้ายเดียวกันต้องห่างกัน 30 วินาที
- ✅ ป้องกันเปิดซ้ำๆ

### **3. never** (แค่อ่านป้าย)
```bash
GATE_TRIGGER_MODE=never
```
- ✅ บันทึกอย่างเดียว
- ✅ ไม่เปิดไม้กั้น

---

## 🔌 **เปิด/ปิด Arduino**

### **เปิดใช้งาน:**
```bash
SERIAL_ENABLED=true
```

### **ปิดใช้งาน:**
```bash
SERIAL_ENABLED=false
```

> 💡 ใช้เมื่อ: ยังไม่มี Arduino หรือต้องการทดสอบแค่อ่านป้าย

---

# 🐛 **แก้ปัญหา**

---

## ❌ **ปัญหา: ไม่เห็น Port**

### **macOS:**
```bash
# ติดตั้ง Driver (ถ้าจำเป็น)
# Arduino UNO ใช้ CH340 chip บางรุ่น

# เช็คว่ามี port หรือไม่
ls /dev/cu.*

# ถอดแล้วเสียบใหม่
```

### **Windows:**
```
1. Device Manager → Ports (COM & LPT)
2. ไม่เห็น Arduino? → ติดตั้ง CH340 Driver
3. Download จาก: https://sparks.gogo.co.nz/ch340.html
```

### **Linux:**
```bash
# เพิ่ม user เข้ากลุ่ม dialout
sudo usermod -a -G dialout $USER

# Logout แล้ว login ใหม่
```

---

## ❌ **ปัญหา: Upload Error**

```
avrdude: stk500_recv(): programmer is not responding
```

**แก้:**
1. ปิด Serial Monitor
2. กด Reset บน Arduino (ปุ่มแดง)
3. Upload ใหม่ทันที

---

## ❌ **ปัญหา: Servo ไม่หมุน**

### **เช็ค:**
1. ✅ ต่อสายถูกหรือไม่?
   - Signal → Pin 9
   - VCC → 5V
   - GND → GND

2. ✅ Servo มีไฟหรือไม่?
   - LED บน Arduino ติดหรือเปล่า

3. ✅ โค้ดถูกหรือไม่?
   - Upload ใหม่อีกครั้ง

---

## ❌ **ปัญหา: Website ไม่เชื่อมต่อ Arduino**

### **เช็ค .env:**
```bash
# ต้องเป็น true
SERIAL_ENABLED=true

# Port ถูกหรือไม่?
SERIAL_PORT=/dev/cu.usbmodem14201  # ← เช็คให้ดี

# Baud rate ถูกหรือไม่?
SERIAL_BAUD=115200
```

### **ทดสอบ Python:**
```bash
python -c "from api.arduino import ping_arduino; print(ping_arduino())"

# ควรได้: True
# ถ้าได้: False → เช็ค port อีกครั้ง
```

---

## ❌ **ปัญหา: Permission Denied (Linux/macOS)**

```bash
# ให้สิทธิ์เข้าถึง port
sudo chmod 666 /dev/ttyACM0

# หรือเพิ่ม user เข้ากลุ่ม
sudo usermod -a -G dialout $USER  # Linux
sudo dscl . -append /Groups/_developer GroupMembership $USER  # macOS
```

---

# ✅ **Checklist ก่อนใช้งาน**

```
☑️ Arduino UNO ต่อสาย Servo แล้ว
☑️ Servo ต่อ: Signal→Pin9, VCC→5V, GND→GND
☑️ ติดตั้ง Arduino IDE แล้ว
☑️ Upload ไฟล์ gate_control_wifi.ino แล้ว
☑️ ทดสอบด้วย Serial Monitor แล้ว (PING → PONG)
☑️ สร้างไฟล์ .env แล้ว
☑️ ตั้งค่า SERIAL_ENABLED=true
☑️ ตั้งค่า SERIAL_PORT ถูกต้อง
☑️ รันเซิร์ฟเวอร์แล้ว
☑️ เห็นข้อความ "[ARDUINO] Connected"
☑️ ทดสอบอัปโหลดรูปแล้ว
☑️ Servo หมุนได้!
```

---

# 🎯 **สรุป**

## **Arduino:**
1. ต่อสาย Servo → Pin 9, 5V, GND
2. เปิด `arduino/gate_control_wifi.ino` ใน Arduino IDE
3. Upload ไปที่ Arduino
4. ทดสอบด้วย Serial Monitor

## **Website:**
1. สร้างไฟล์ `.env`
2. ตั้งค่า:
   - `SERIAL_ENABLED=true`
   - `SERIAL_PORT=/dev/cu.usbmodem...` (หา port ก่อน)
   - `SERIAL_BAUD=115200`
3. รันเซิร์ฟเวอร์: `python -m api.main`
4. เช็คว่าเห็น "[ARDUINO] Connected"
5. ทดสอบอัปโหลดรูป → ไม้กั้นเปิด!

---

**🎉 เสร็จแล้ว! พร้อมใช้งาน!**

ถ้ามีปัญหา ให้เช็คตาม "แก้ปัญหา" ด้านบนครับ 😊

