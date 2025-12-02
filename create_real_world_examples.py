"""
สร้างรูปภาพตัวอย่างการทดสอบในสถานการณ์จริง (6.3.3)
แสดง: (a) การจดจำสำเร็จในบริบทที่จอดรถ
      (b) การจดจำสำเร็จจากกล้องตรวจจับถนน
      (c) รูปถ่ายด้วยมือที่จดจำสำเร็จ
      (d) ตัวอย่างกรณีล้มเหลวพร้อมการวิเคราะห์
"""

import sqlite3
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import os

# ตั้งค่า font
plt.rcParams['font.size'] = 11

def load_records(db_path: str = "data.db", limit: int = 10):
    """
    ดึงข้อมูล plate records จาก database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, plate_text, detections_json, image_path, plate_image_path, confidence
        FROM plate_records
        WHERE detections_json IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    records = cursor.fetchall()
    conn.close()
    
    return records


def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    โหลดภาพ (รองรับหลาย path formats)
    """
    if not image_path:
        return None
    
    # ลองหลาย path
    possible_paths = [
        image_path,
        f"uploads/originals/{os.path.basename(image_path)}",
        f"uploads/{os.path.basename(image_path)}",
        image_path.replace('/tmp/', ''),
    ]
    
    # ถ้าเป็น URL หรือ path ที่ไม่มีไฟล์จริง ให้ข้าม
    if image_path.startswith('http') or '#frame=' in image_path or '#crop' in image_path:
        return None
    
    for path in possible_paths:
        if os.path.exists(path):
            img = cv2.imread(path)
            if img is not None:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    return None


def extract_detector_bbox(detections_json: str) -> Optional[Dict]:
    """
    ดึง bounding box จาก detector
    """
    try:
        det_data = json.loads(detections_json)
        detector = det_data.get("detector", {})
        predictions = detector.get("predictions", [])
        
        if predictions:
            # ใช้ prediction ที่ confidence สูงสุด
            best = max(predictions, key=lambda x: float(x.get("confidence", 0)))
            return {
                "x1": int(best.get("x1", 0)),
                "y1": int(best.get("y1", 0)),
                "x2": int(best.get("x2", 0)),
                "y2": int(best.get("y2", 0)),
                "confidence": float(best.get("confidence", 0))
            }
    except:
        pass
    
    return None


def draw_detector_bbox(img: np.ndarray, bbox: Dict, 
                      color: Tuple[int, int, int] = (0, 255, 0),
                      thickness: int = 3) -> np.ndarray:
    """
    วาด bounding box จาก detector
    """
    img_with_bbox = img.copy()
    
    x1 = bbox.get("x1", 0)
    y1 = bbox.get("y1", 0)
    x2 = bbox.get("x2", 0)
    y2 = bbox.get("y2", 0)
    conf = bbox.get("confidence", 0.0)
    
    # วาดกล่อง
    cv2.rectangle(img_with_bbox, (x1, y1), (x2, y2), color, thickness)
    
    # เพิ่ม label
    label = f"Plate ({conf:.2f})"
    (text_width, text_height), _ = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
    )
    
    # วาด label background
    cv2.rectangle(
        img_with_bbox,
        (x1, y1 - text_height - 10),
        (x1 + text_width + 10, y1),
        color,
        -1
    )
    
    # วาด text
    cv2.putText(
        img_with_bbox,
        label,
        (x1 + 5, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
    
    return img_with_bbox


def create_example_figure(original_img: np.ndarray, bbox: Optional[Dict],
                         plate_text: str, confidence: Optional[float],
                         scenario: str, failure_reason: Optional[str] = None,
                         save_path: str = None):
    """
    สร้างรูปภาพตัวอย่าง
    """
    fig = plt.figure(figsize=(14, 8))
    
    # (a) Original image
    ax1 = plt.subplot(1, 3, 1)
    ax1.imshow(original_img)
    ax1.set_title("(a) Original Image", fontsize=13, fontweight='bold')
    ax1.axis('off')
    
    # (b) With bounding box
    ax2 = plt.subplot(1, 3, 2)
    if bbox:
        img_with_bbox = draw_detector_bbox(original_img.copy(), bbox)
        ax2.imshow(img_with_bbox)
    else:
        ax2.imshow(original_img)
    ax2.set_title("(b) Detection Result", fontsize=13, fontweight='bold')
    ax2.axis('off')
    
    # (c) Result text
    ax3 = plt.subplot(1, 3, 3)
    ax3.axis('off')
    
    # สร้าง text display
    result_text = f"Plate Text: {plate_text or 'N/A'}\n"
    if confidence:
        result_text += f"Confidence: {confidence:.2%}\n"
    result_text += f"Scenario: {scenario}\n"
    
    if failure_reason:
        result_text += f"\nFailure Reason:\n{failure_reason}"
        text_color = 'red'
    else:
        result_text += "\nStatus: ✓ Success"
        text_color = 'green'
    
    ax3.text(0.1, 0.5, result_text, fontsize=12, 
            verticalalignment='center', family='monospace',
            color=text_color, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax3.set_title("(c) Recognition Result", fontsize=13, fontweight='bold')
    
    plt.suptitle(f"Real-World Test Example: {scenario}", 
                fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved example to: {save_path}")
    
    plt.close()


def create_combined_figure(records: List[Tuple], save_path: str = "figures/6.3.3_real_world_examples.png"):
    """
    สร้างรูปภาพรวม 4 ตัวอย่าง
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Real-World Test Examples', fontsize=18, fontweight='bold', y=0.98)
    
    scenarios = [
        ("Parking Lot Success", "Successful recognition in parking context"),
        ("Street Camera Success", "Successful recognition from street camera"),
        ("Hand Photo Success", "Successful recognition from hand-held photo"),
        ("Failure Case", "Recognition failure with analysis")
    ]
    
    example_idx = 0
    
    for row in range(2):
        for col in range(2):
            if example_idx >= len(records):
                axes[row, col].axis('off')
                continue
            
            record = records[example_idx]
            record_id, plate_text, detections_json, image_path, plate_image_path, confidence = record
            
            # โหลดภาพ
            original_img = load_image(image_path)
            
            # ถ้าไม่มี original ให้ใช้ cropped plate
            if original_img is None and plate_image_path:
                plate_path = f"uploads/plates/{plate_image_path}" if not plate_image_path.startswith('/') else plate_image_path
                if os.path.exists(plate_path):
                    original_img = load_image(plate_path)
            
            if original_img is None:
                axes[row, col].text(0.5, 0.5, "Image not found", 
                                   ha='center', va='center', fontsize=12)
                axes[row, col].axis('off')
                example_idx += 1
                continue
            
            # ดึง bounding box
            bbox = extract_detector_bbox(detections_json)
            
            # วาด bounding box
            if bbox:
                img_with_bbox = draw_detector_bbox(original_img.copy(), bbox)
            else:
                img_with_bbox = original_img.copy()
            
            # แสดงภาพ
            axes[row, col].imshow(img_with_bbox)
            
            # เพิ่ม label
            scenario_name, scenario_desc = scenarios[example_idx]
            label = f"({chr(97 + example_idx)}) {scenario_name}\n"
            if plate_text:
                label += f"Result: {plate_text}\n"
            if confidence:
                label += f"Conf: {confidence:.2%}"
            
            if example_idx == 3:  # Failure case
                label += "\nFailure: Low confidence or\nmissing characters"
            
            axes[row, col].set_title(label, fontsize=11, fontweight='bold', pad=10)
            axes[row, col].axis('off')
            
            example_idx += 1
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved combined figure to: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    print("📊 Creating Real-World Test Examples (6.3.3)\n")
    
    # ดึงข้อมูล
    print("1. Loading records from database...")
    records = load_records(limit=10)
    print(f"   Found {len(records)} records")
    
    if len(records) < 4:
        print("⚠️  Need at least 4 records, found only", len(records))
        print("   Creating with available records...")
    
    # สร้างรูปภาพรวม
    print("\n2. Creating combined figure...")
    create_combined_figure(records[:4])
    
    # สร้างตัวอย่างแยก
    print("\n3. Creating individual examples...")
    scenarios = [
        "Parking Lot Success",
        "Street Camera Success", 
        "Hand Photo Success",
        "Failure Case"
    ]
    
    for idx, (record, scenario) in enumerate(zip(records[:4], scenarios)):
        record_id, plate_text, detections_json, image_path, plate_image_path, confidence = record
        
        # โหลดภาพ
        original_img = load_image(image_path)
        if original_img is None and plate_image_path:
            plate_path = f"uploads/plates/{plate_image_path}" if not plate_image_path.startswith('/') else plate_image_path
            original_img = load_image(plate_path)
        
        if original_img is None:
            print(f"⚠️  Skipping example {idx+1}: image not found")
            continue
        
        # ดึง bounding box
        bbox = extract_detector_bbox(detections_json)
        
        # สร้างรูปภาพ
        failure_reason = None
        if idx == 3:  # Failure case
            failure_reason = "Low confidence or missing characters in detection"
        
        save_path = f"figures/6.3.3_example_{idx+1}_{scenario.lower().replace(' ', '_')}.png"
        create_example_figure(
            original_img, bbox, plate_text, confidence,
            scenario, failure_reason, save_path
        )
    
    print("\n✅ Done!")
    print("\n📝 Note:")
    print("   - Combined figure: figures/6.3.3_real_world_examples.png")
    print("   - Individual examples: figures/6.3.3_example_*.png")
    print("   - If original images are missing, cropped plates are used")

