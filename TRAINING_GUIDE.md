# 🎓 คู่มือการเทรน Models ใหม่

## 📋 สรุปสถานการณ์

### ❌ **ปัญหาที่พบ:**
- Reader Model ปัจจุบันมีแค่ 1 class (`License_Plate`)
- ควรมี 124 classes สำหรับอ่านตัวอักษร (ก-ฮ, 0-9, รหัสจังหวัด)
- Dataset พร้อมแล้ว แต่ยังไม่ได้เทรน

### ✅ **Datasets ที่มี:**

1. **Detector Dataset** (`license_plate_recognition.v11i.yolov11`)
   - Images: 10,125 รูป
   - Classes: 1 (`License_Plate`)
   - Purpose: ตรวจจับตำแหน่งป้ายทะเบียน

2. **Character Reader Dataset** (`lpr_plate.v1i.yolov11`)
   - Images: 9,597 รูป
   - Classes: 124 (ตัวเลข, ตัวอักษรไทย, รหัสจังหวัด)
   - Purpose: อ่านตัวอักษรบนป้าย

---

## 🚀 วิธีเทรน (2 ทางเลือก)

### **ทางที่ 1: ใช้สคริปต์อัตโนมัติ** ⭐ แนะนำ

```bash
cd /Users/dannyroberts/Documents/thai-lpr-api
source .venv/bin/activate
python train_models.py
```

**สคริปต์จะ:**
1. ✅ ตรวจสอบ datasets
2. ✅ เทรน Detector Model (100 epochs)
3. ✅ เทรน Character Reader Model (100 epochs)
4. ✅ บันทึก best weights อัตโนมัติ

---

### **ทางที่ 2: เทรนแบบ Manual**

#### **Step 1: เทรน Detector Model**

```python
from ultralytics import YOLO

# Load base model
model = YOLO('yolo11n.pt')

# Train detector
results = model.train(
    data='datasets/license_plate_recognition.v11i.yolov11/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='detector_new',
    patience=20,
    device='mps',  # Mac: mps, NVIDIA: cuda, CPU: cpu
    save=True,
    plots=True
)

# Save best model
# Best weights จะอยู่ที่: runs/detect/detector_new/weights/best.pt
```

#### **Step 2: เทรน Character Reader Model**

```python
from ultralytics import YOLO

# Load base model
model = YOLO('yolo11n.pt')

# Train character reader
results = model.train(
    data='datasets/lpr_plate.v1i.yolov11/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='character_reader_new',
    patience=20,
    device='mps',
    save=True,
    plots=True
)

# Best weights: runs/detect/character_reader_new/weights/best.pt
```

#### **Step 3: แทนที่ Models เก่า**

```bash
# Backup models เก่า
mv models/detector/best.pt models/detector/best_old.pt
mv models/reader/best.pt models/reader/best_old.pt

# Copy models ใหม่
cp runs/detect/detector_new/weights/best.pt models/detector/best.pt
cp runs/detect/character_reader_new/weights/best.pt models/reader/best.pt

# Restart server
./start.sh
```

---

## ⏱️ ระยะเวลา

### **Detector Model:**
- Dataset: 10,125 images
- Epochs: 100
- Time: **2-3 ชั่วโมง** (Mac M1/M2)

### **Character Reader Model:**
- Dataset: 9,597 images
- Epochs: 100
- Classes: 124
- Time: **3-5 ชั่วโมง** (Mac M1/M2)

**รวมทั้งหมด: 5-8 ชั่วโมง**

---

## 💻 ความต้องการระบบ

### **แนะนำ:**
- ✅ Mac M1/M2 (MPS)
- ✅ NVIDIA GPU (CUDA)
- ✅ RAM: 16GB+
- ✅ Storage: 10GB+ ว่าง

### **ขั้นต่ำ:**
- ⚠️ CPU only (ช้ามาก 10-20 ชั่วโมง)
- ⚠️ RAM: 8GB
- ⚠️ Storage: 5GB

---

## 📊 ผลลัพธ์ที่คาดหวัง

### **หลังเทรนเสร็จ:**

**Detector Model:**
- ✅ mAP50: >95%
- ✅ ตรวจจับป้ายได้แม่น
- ✅ False Positive ต่ำ

**Character Reader Model:**
- ✅ mAP50: >92%
- ✅ อ่านตัวอักษรไทยได้ถูกต้อง
- ✅ อ่านตัวเลขได้แม่น
- ✅ รู้จักรหัสจังหวัด 77+ จังหวัด

---

## 🎯 หลังเทรนเสร็จ

### **ระบบจะทำงานแบบนี้:**

```
1. YOLO Detector (ที่เทรนใหม่) → หาป้าย
2. Crop ป้ายออกมา
3. YOLO Reader (ที่เทรนใหม่) → อ่านตัวอักษรทีละตัว
   - เรียงตามตำแหน่ง
   - ต่อเป็นข้อความ
4. Province Parser → แยกจังหวัด
5. บันทึก + แสดงผล
```

**ไม่ต้องพึ่ง OCR อีกต่อไป!** 🎉

---

## ⚠️ หมายเหตุ

### **ระหว่างเทรน:**
- 💾 **อย่าปิดเครื่อง**
- 🔋 **เสียบไฟ** (Mac จะร้อนและใช้พลังงานมาก)
- 📊 **ดู progress** ใน terminal
- 🖼️ **ดู plots** ใน `runs/detect/*/`

### **หากต้องการหยุด:**
- กด `Ctrl+C`
- Training จะหยุด
- Weights ที่ดีที่สุดจนถึงตอนนั้นจะถูกบันทึก

---

## 📁 โครงสร้างไฟล์หลังเทรน

```
runs/detect/
  ├── detector_new/
  │   ├── weights/
  │   │   ├── best.pt       ← ใช้อันนี้!
  │   │   └── last.pt
  │   ├── results.png
  │   ├── confusion_matrix.png
  │   └── ...
  │
  └── character_reader_new/
      ├── weights/
      │   ├── best.pt       ← ใช้อันนี้!
      │   └── last.pt
      ├── results.png
      └── ...
```

---

## 🎉 พร้อมเริ่มเทรน!

**รันคำสั่ง:**
```bash
cd /Users/dannyroberts/Documents/thai-lpr-api
source .venv/bin/activate
python train_models.py
```

**หรือเทรนทีละตัว:**
```python
from ultralytics import YOLO

# Detector
model = YOLO('yolo11n.pt')
model.train(data='datasets/license_plate_recognition.v11i.yolov11/data.yaml', epochs=100, imgsz=640, batch=16, device='mps')

# Character Reader  
model = YOLO('yolo11n.pt')
model.train(data='datasets/lpr_plate.v1i.yolov11/data.yaml', epochs=100, imgsz=640, batch=16, device='mps')
```

**GO! 🚀**


