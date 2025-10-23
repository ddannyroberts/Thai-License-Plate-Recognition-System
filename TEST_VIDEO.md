# 🎥 การทดสอบ Video Processing

## ✅ สิ่งที่แก้ไขแล้ว:

### 1. **ปัญหาเดิม:**
- ❌ ใช้ `extract_bboxes` และ `merge_boxes` ที่ไม่ได้รัน OCR จริงๆ
- ❌ ไม่มีการอ่านข้อความจากป้ายทะเบียน
- ❌ แสดงผล "Found 0 unique plates"

### 2. **การแก้ไข:**
- ✅ เปลี่ยนใช้ `run_ocr_on_bbox()` แบบเดียวกับ `/detect`
- ✅ รัน OCR บน cropped plate image โดยตรง
- ✅ ข้าม frame ที่อ่านไม่ได้ (น้อยกว่า 2 ตัวอักษร)
- ✅ เพิ่มการแสดงผลภาษาไทยใน Frontend
- ✅ เพิ่ม console.log สำหรับ debug

---

## 🧪 วิธีทดสอบ:

### **1. อัปโหลดวิดีโอ**
1. ไปที่ http://localhost:8000
2. เลือก "Video" radio button
3. คลิกที่พื้นที่อัปโหลดหรือลากวิดีโอมาวาง
4. กด "🚀 Process"

### **2. ตรวจสอบผลลัพธ์**
จะแสดง:
- **Plate Text**: เลขป้ายที่อ่านได้ทั้งหมด (คั่นด้วย comma)
- **Province**: จำนวนป้ายที่ไม่ซ้ำกัน
- **Confidence**: จำนวนเฟรมที่ประมวลผล
- **Gate Status**: จำนวนรายการที่บันทึก

### **3. ตรวจสอบ Console**
เปิด Developer Tools (F12) → Console
- จะเห็น log: `Video processing result: {...}`
- ดูข้อมูล: `unique_plates`, `frames_processed`, `records_saved`

---

## 🔍 ตัวอย่างผลลัพธ์:

### **กรณีพบป้าย:**
```json
{
  "session_id": "abc123...",
  "frames_processed": 68,
  "unique_plates": ["กก1234", "กข5678"],
  "records_saved": 12,
  "sample_record_ids": [1, 2, 3, ...]
}
```

**แสดงผล:**
- Plate Text: `กก1234, กข5678`
- Province: `พบ 2 ป้ายทะเบียนที่ไม่ซ้ำกัน`
- Confidence: `ประมวลผล 68 เฟรม`
- Gate Status: `บันทึก 12 รายการ`

### **กรณีไม่พบป้าย:**
```json
{
  "session_id": "abc123...",
  "frames_processed": 68,
  "unique_plates": [],
  "records_saved": 0,
  "sample_record_ids": []
}
```

**แสดงผล:**
- Plate Text: `❌ ไม่พบป้ายทะเบียน`
- Province: `ลองอัปโหลดวิดีโอที่มีป้ายทะเบียนชัดเจนกว่า`
- Confidence: `ประมวลผล 68 เฟรม`
- Gate Status: `บันทึก 0 รายการ`

---

## ⚙️ การตั้งค่า (Environment Variables):

### **Frame Processing:**
```bash
VIDEO_FRAME_STRIDE=10       # ประมวลผลทุก 10 เฟรม (เร็วขึ้น)
VIDEO_MAX_FRAMES=600        # ประมวลผลสูงสุด 600 เฟรม
VIDEO_MIN_LETTERS=2         # ต้องอ่านได้อย่างน้อย 2 ตัวอักษร
```

### **Gate Control:**
```bash
VIDEO_OPEN_GATE_FIRST=true  # เปิดประตูเมื่อเจอป้ายใหม่
```

---

## 🐛 การ Debug:

### **1. ตรวจสอบ Server Logs:**
```bash
# ดู logs ของ uvicorn
# จะเห็น:
# - "DEBUG video processing error: ..." (ถ้ามี error)
# - "[GATE(video)] ok=... reason=... plate='...' conf=..."
```

### **2. ตรวจสอบ Console:**
```javascript
// เปิด F12 → Console
// จะเห็น:
console.log('Video processing result:', data);
```

### **3. ตรวจสอบ Records Tab:**
- ไปที่แท็บ "📊 Records"
- ดูว่ามีรายการใหม่เพิ่มเข้ามาหรือไม่
- ถ้าไม่มี = OCR อ่านไม่ได้หรือ skip ทั้งหมด

---

## 💡 เคล็ดลับ:

### **1. วิดีโอที่ใช้ได้ดี:**
- ✅ ป้ายทะเบียนชัดเจน
- ✅ แสงสว่างเพียงพอ
- ✅ กล้องตรง ไม่เอียง
- ✅ ป้ายไม่เบลอ

### **2. วิดีโอที่อาจมีปัญหา:**
- ❌ ป้ายเลอะหรือสกปรก
- ❌ แสงน้อยเกินไป/มากเกินไป
- ❌ กล้องเอียงมาก
- ❌ ป้ายเบลอหรือเคลื่อนไหวเร็ว

### **3. การปรับแต่ง:**
- ลด `VIDEO_FRAME_STRIDE` = ประมวลผลบ่อยขึ้น (ช้าลง แต่แม่นขึ้น)
- เพิ่ม `VIDEO_FRAME_STRIDE` = ประมวลผลน้อยลง (เร็วขึ้น แต่อาจพลาด)
- ลด `VIDEO_MIN_LETTERS` = ยอมรับผลที่สั้นกว่า
- เพิ่ม `VIDEO_MAX_FRAMES` = ประมวลผลวิดีโอยาวขึ้น

---

## ✅ สรุป:

**ระบบ Video Processing ตอนนี้:**
1. ✅ ใช้ YOLO Detector หาตำแหน่งป้าย
2. ✅ Crop ป้ายทะเบียนออกมา
3. ✅ ใช้ YOLO Reader อ่านตัวอักษร
4. ✅ ใช้ Tesseract OCR อ่านข้อความจริงๆ
5. ✅ บันทึกลง Database
6. ✅ Broadcast ผ่าน WebSocket
7. ✅ ควบคุมประตูอัตโนมัติ

**พร้อมใช้งาน! ลองอัปโหลดวิดีโอดูได้เลยครับ** 🎥



