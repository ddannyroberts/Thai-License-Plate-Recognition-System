# 🚗 Automatic License Plate Recognition System
## Thai License Plate Recognition System

**4th Year Computer Engineering Senior Project**  
**Prince of Songkla University, Phuket Campus**

---

## 📋 Contents

1. What is this project?
2. Why we built this
3. Scope & Limitations
4. Technology used
5. How it works
6. Main features
7. Test results
8. Real-world application
9. Summary

---

# ⭐ What is this project?

An automatic Thai motorcycle license plate recognition system powered by AI to make entering and exiting the university faster and more convenient.

### Main Purpose
**To facilitate easy access to the university** without having to stop and show ID cards every time. The system reads license plates and opens barriers automatically.

### Where it can be used
- Entry/exit points at PSU Phuket
- Student and staff parking areas
- Buildings with controlled access

---

## 🎯 Why we built this

### The Problem
Current systems using student cards or manual barrier control have limitations:
- Must stop the vehicle every time, wasting time
- Long queues during morning and evening rush hours
- Forgotten or lost cards prevent entry
- Requires staff presence at all times

### Our Solution
Use AI-powered license plate recognition that works automatically 24/7. Registered vehicles can enter and exit without stopping.

---

# 📏 Project Scope & Limitations

## Scope of Use

### 🎯 Location
- **Designed primarily for PSU Phuket**
- Can be adapted for other locations like residential areas, condos, office buildings
- Suitable for controlled access points

### 🏍️ Vehicle Type
- **Supports motorcycles** primarily (2 wheels)
- Does not yet support 4-wheel cars (planned for future development)

### 📝 Language Support
- **Thai license plates only** (Thai characters + numbers)
- Does not support foreign license plates

## Technical Limitations

### 🚦 Vehicle Speed
- Vehicle must **stop or slow down** for clear camera capture
- Recommended speed: **≤ 10-15 km/h** (crawling speed)
- If vehicle moves too fast, image will be blurred and unreadable

### ☀️ Lighting
- **Requires adequate lighting** - natural daylight or artificial lighting
- Night or very dark conditions: **accuracy drops to 65%**
- Recommend installing lights near camera

### 📐 Camera Angle
- License plate must be **clearly visible** to camera
- Plate tilted more than 30° will be difficult to read (60% success rate)
- Optimal distance: **2-3 meters** from camera

### 🧹 Plate Condition
- Plate must be **clean, clear, not dirty**
- Very old/faded/covered plates: **unreadable or errors**
- Plates with light reflection (glare): **difficult to read**

### ⏱️ Processing Time
- Takes **2-5 seconds** per image (depends on computer specs)
- Not fast enough for vehicles passing without stopping

### 🎯 Accuracy
- Accuracy **89-95%** in good conditions
- Still **5-11% chance of errors** especially for similar characters

### 💾 Training Data
- Only **300 images** used for training - insufficient for production use
- Needs more data for improved accuracy

## Usage Requirements Summary ✅

| Condition | Requirement |
|-----------|-------------|
| Vehicle Speed | ≤ 10-15 km/h (slow or stop) |
| Lighting | Must have adequate light (daytime or artificial) |
| Camera Angle | Plate tilt ≤ 30° |
| Distance | 2-3 meters from camera |
| Plate Condition | Clean, clear, not too old |
| Vehicle Type | Motorcycle (2 wheels) |
| Language | Thai plates only |

---

# 💻 Technology Used

## 🧠 AI and Machine Learning

We use **YOLO AI Model** trained on real Thai license plate images with two capabilities:
1. **Find the plate location** - Detect where the plate is in the image
2. **Read the text** - Read numbers and letters on the plate

Plus **Tesseract OCR** as a backup system for increased accuracy.

## 🌐 Web Application

Built with **FastAPI** (Python) for fast and stable backend.

Web interface uses **HTML + JavaScript** and works on both desktop and mobile.

## 🔧 Hardware Integration

Connects to **Arduino + Servo Motor** to control barriers automatically.

## 💾 Database

Uses **SQLite** to record all entry/exit data with Admin login system.

---

# 🔄 How Does It Work?

### Process Flow (Takes 2-3 seconds)

1. **Camera captures image** - When vehicle approaches checkpoint
2. **AI finds the plate** - Identifies plate location in image
3. **AI reads the text** - Converts to text like "กว 1234"
4. **Identifies province** - Converts "กว" to "Bangkok"
5. **Checks database** - Verifies access permission
6. **Opens barrier** - Commands Arduino to open automatically if authorized
7. **Records data** - Saves entry/exit time in system

### Real Scenario

```
Motorcycle approaches barrier
        ↓
Camera takes photo and sends to AI
        ↓
AI reads: "กก 5678 Phuket"
        ↓
System checks: Student vehicle ✅
        ↓
Arduino opens barrier automatically
        ↓
Vehicle passes without stopping 🎉
```

---

# ✨ Main Features

## 1. Upload Photos

Upload license plate images through web interface. System analyzes and displays results instantly. Supports taking photos from mobile phones.

## 2. Display Results

Shows information:
- License plate number (e.g., กว 1234)
- Province (e.g., Bangkok)
- Confidence score (e.g., 89%)
- Cropped plate image

## 3. Entry/Exit History

View all historical data with search by date or plate number. Export to CSV available.

## 4. Automatic Barrier Control

Connects to Arduino via USB. Can open/close barriers automatically or manually through Admin Panel.

## 5. Admin System

Management interface for staff with capabilities to:
- View daily entry/exit statistics
- Manage vehicle database
- Configure barrier system settings
- View activity logs

## 6. Mobile Support

Works on mobile devices when connected to same WiFi. Ideal for Security Guards.

---

# 📊 Test Results

## Accuracy

We tested with 300+ real license plate images with these results:

- **Plate detection:** 94-95% accurate
- **Text reading:** 89-91% accurate
- **Speed:** 2-3 seconds per image

## Testing Conditions

| Condition | Success Rate | Notes |
|-----------|--------------|-------|
| Good lighting, clear plate | 95% | Best case |
| Medium lighting | 89% | Works well |
| Low light/dark | 65% | Needs improvement |
| Slightly tilted plate | 85% | Still usable |
| Dirty plate | 70% | Difficult to read |

## Usage Recommendations

✅ Install camera in well-lit area  
✅ Adjust camera angle for straight-on plate view  
✅ Distance approximately 2-3 meters  
✅ Avoid light reflections

---

# 🚀 Real-World Application

## Simulated Scenarios at PSU Phuket

### Installation Point 1: Main University Entrance
- Camera captures incoming vehicle plates
- Opens barrier automatically for students and staff
- Records entry time

### Installation Point 2: Building Parking Lot
- Identifies which vehicles have parking permission
- Alerts if unauthorized vehicle detected
- Counts available parking spaces

### Installation Point 3: University Exit
- Records exit time
- Checks if all entered vehicles have exited

## Benefits

### For Students
- Convenient entry/exit without stopping
- No worry about forgetting ID cards
- Saves time during rush hours

### For University
- Reduces security guard workload
- Real-time entry/exit data
- Increased security with automation
- Long-term cost savings

### For Staff
- Easy statistics checking
- Manual barrier control from mobile
- Clear historical records

---

# 🔮 Future Development

## Short-term (3-6 months)

1. **More AI training data** - Collect more plate images for better accuracy
2. **Support 4-wheel vehicles** - Expand to support all vehicle types
3. **Line notification system** - Alert staff when unusual vehicles detected

## Long-term (6-12 months)

### 📹 1. Live Camera Streaming
- **View real-time camera feeds** on website and mobile
- Monitor all entry/exit points simultaneously
- Automatic video clip recording when vehicles enter/exit
- Support multiple IP cameras at once

### 📱 2. Mobile Application
- **Create iOS and Android apps** connected to main system
- View live camera feeds from anywhere, anytime
- Receive push notifications when vehicles enter/exit
- Control barriers remotely from mobile (Admin only)
- View entry/exit history and statistics

### 👤 3. User Portal on Website
- **Dedicated page for regular users** (students/staff) to:
  - Register their own vehicle plates
  - View their personal entry/exit history
  - Edit vehicle information (add/remove plates)
  - Report issues or request assistance
- **Role-based access** Regular User, Admin, Super Admin

### 🔐 4. Smart Whitelist/Blacklist System
- Automatically manage permitted/banned vehicles
- Set time-based access (e.g., students only 6:00-22:00)
- Instant alerts when blacklisted vehicles detected

### ☁️ 5. Cloud Deployment
- Deploy to Cloud (AWS/Google Cloud) for access from anywhere
- Support multiple concurrent users
- Automatic data backup

## Additional Ideas

- **Vehicle classification** - Distinguish motorcycles, cars, trucks
- **Multiple cameras** - Install at multiple points with single connection
- **Automatic reports** - Send daily statistics via Email
- **Parking payment** - Integrate payment system for visitors
- **QR Code backup** - Use QR codes when plate reading fails

---

# 🎓 Summary

## What We Accomplished

✅ **Developed AI Model** that reads Thai plates with 89-95% accuracy  
✅ **Built Web Application** that's easy to use and mobile-friendly  
✅ **Connected Hardware** that actually controls barriers  
✅ **Tested functionality** with satisfactory results

## What We Learned

- Training AI models from real data
- Full-stack web application development
- Integrating software with hardware
- Problem-solving when facing obstacles

## Current Limitations

⚠️ Still a **Prototype** for learning purposes  
⚠️ Works well in good lighting, needs improvement for nighttime  
⚠️ Limited training data (300 images), can be improved  
⚠️ Not ready for production use, requires more testing

## Benefits to University

This project demonstrates that **AI technology can be applied to solve real university problems**, not just theory. It serves as a prototype that can be further developed in the future.

---

# 🙏 Thank You

<p align="center">
<strong style="font-size: 1.2em;">Automatic License Plate Recognition System</strong><br/>
<strong>Thai License Plate Recognition System</strong><br/><br/>
4th Year Computer Engineering Senior Project<br/>
Prince of Songkla University, Phuket Campus<br/>
Academic Year 2025<br/><br/>
</p>

---

## 💬 Frequently Asked Questions

**Q: Does it really work?**  
A: Yes! But it's a prototype for learning. Needs more development for production use.

**Q: Is 89% accuracy good enough?**  
A: For training with 300 images, it's very good. Can improve with more data.

**Q: Why not use Google Cloud?**  
A: We wanted to learn how to train our own models and work offline.

**Q: Do you store personal information?**  
A: No. Only plate number, province, and time. No vehicle owner information.

**Q: Can it be used outside university?**  
A: Yes. Such as residential areas, condos, office buildings, or parking lots.

---

<p align="center">
<strong style="font-size: 1.5em;">END OF PRESENTATION</strong><br/>
Thank you for watching 🙏
</p>
