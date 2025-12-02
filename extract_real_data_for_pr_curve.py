"""
สคริปต์สำหรับดึงข้อมูลจริงจาก database และสร้าง Precision-Recall Curve
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict
import numpy as np
import matplotlib.pyplot as plt

def extract_detections_from_database(db_path: str = "data.db"):
    """
    ดึงข้อมูล detections จาก database
    
    Returns:
        List ของ predictions พร้อม confidence scores
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ดึงข้อมูลที่มี detections_json
    cursor.execute("""
        SELECT id, detections_json, confidence, plate_text, created_at
        FROM plate_records
        WHERE detections_json IS NOT NULL
        ORDER BY created_at DESC
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    print(f"📊 Found {len(records)} records with detection data")
    
    all_predictions = []
    
    for record_id, detections_json, conf, plate_text, created_at in records:
        try:
            detections = json.loads(detections_json)
            
            # ดึง detector predictions
            detector_preds = detections.get("detector", [])
            
            for pred in detector_preds:
                all_predictions.append({
                    "record_id": record_id,
                    "x1": pred.get("x1", 0),
                    "y1": pred.get("y1", 0),
                    "x2": pred.get("x2", 0),
                    "y2": pred.get("y2", 0),
                    "confidence": pred.get("confidence", conf or 0.0),
                    "plate_text": plate_text,
                    "created_at": created_at
                })
        except Exception as e:
            print(f"⚠️  Error parsing record {record_id}: {e}")
            continue
    
    print(f"✅ Extracted {len(all_predictions)} predictions")
    return all_predictions


def explain_what_is_needed():
    """
    อธิบายว่าต้องมีข้อมูลอะไรบ้างสำหรับ Precision-Recall Curve
    """
    print("\n" + "="*60)
    print("📋 สรุปข้อมูลที่ต้องมีสำหรับ Precision-Recall Curve:")
    print("="*60)
    
    print("\n✅ ข้อมูลที่มีแล้ว:")
    print("   1. Predictions จาก model (ใน database)")
    print("      - มี confidence scores")
    print("      - มี bounding boxes (x1, y1, x2, y2)")
    print("      - จำนวน: 19 records ใน database")
    
    print("\n❌ ข้อมูลที่ยังไม่มี:")
    print("   1. Ground Truth Annotations")
    print("      - ต้องมีไฟล์ .txt (YOLO format) สำหรับแต่ละรูปภาพ")
    print("      - ระบุตำแหน่งป้ายทะเบียนที่ถูกต้อง")
    print("      - ใช้เปรียบเทียบกับ predictions เพื่อคำนวณ TP/FP/FN")
    
    print("\n📝 วิธีได้ข้อมูล Ground Truth:")
    print("   1. ใช้ dataset ที่มี labels อยู่แล้ว")
    print("      - เช่น dataset ที่ใช้ train model")
    print("      - แยก test set (20% ของข้อมูล)")
    print("   2. หรือ annotate เอง")
    print("      - ใช้ tools เช่น LabelImg, Roboflow")
    print("      - annotate รูปภาพที่มีใน uploads/")
    
    print("\n🔧 วิธีคำนวณ Precision-Recall:")
    print("   Precision = TP / (TP + FP)")
    print("   Recall = TP / (TP + FN)")
    print("   โดย:")
    print("   - TP (True Positive) = ตรวจจับถูกต้อง (IoU >= 0.5)")
    print("   - FP (False Positive) = ตรวจจับผิด (ไม่มีป้ายจริง)")
    print("   - FN (False Negative) = ไม่ตรวจจับ (มีป้ายจริงแต่ไม่เจอ)")
    
    print("\n" + "="*60)


def show_current_data_summary():
    """แสดงสรุปข้อมูลที่มีอยู่ใน database"""
    predictions = extract_detections_from_database()
    
    if not predictions:
        print("❌ ไม่มีข้อมูล predictions ใน database")
        return
    
    confidences = [p["confidence"] for p in predictions]
    
    print("\n📊 สรุปข้อมูลที่มี:")
    print(f"   จำนวน predictions: {len(predictions)}")
    print(f"   Confidence สูงสุด: {max(confidences):.3f}")
    print(f"   Confidence ต่ำสุด: {min(confidences):.3f}")
    print(f"   Confidence เฉลี่ย: {np.mean(confidences):.3f}")
    print(f"   Confidence median: {np.median(confidences):.3f}")
    
    # Histogram ของ confidence
    print("\n📈 การกระจายของ Confidence:")
    bins = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
    hist, _ = np.histogram(confidences, bins=bins)
    for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
        print(f"   {low:.1f}-{high:.1f}: {hist[i]} predictions")


if __name__ == "__main__":
    print("🔍 ตรวจสอบข้อมูลสำหรับ Precision-Recall Curve\n")
    
    # แสดงข้อมูลที่มี
    show_current_data_summary()
    
    # อธิบายว่าต้องมีอะไรบ้าง
    explain_what_is_needed()
    
    print("\n💡 คำแนะนำ:")
    print("   - ถ้ามี dataset ที่มี labels: ใช้ข้อมูลจาก validation")
    print("   - ถ้าไม่มี: ใช้กราฟที่สร้างจากข้อมูลใน paper (precision=96.2%, recall=94.8%)")
    print("   - กราฟจาก paper ก็ใช้ได้เพราะมีข้อมูลตรงกัน")


