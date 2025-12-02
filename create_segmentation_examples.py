"""
สร้างรูปภาพตัวอย่างการแยกตัวอักษร (6.2.3)
แสดง: (a) ภาพป้ายทะเบียนที่ตัดมา (b) กล่องขอบเขต (c) ตัวอักษรแต่ละตัว (d) ผลลัพธ์
"""

import sqlite3
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from typing import List, Dict, Tuple
import os

# ตั้งค่า font
plt.rcParams['font.size'] = 12

def load_plate_records(db_path: str = "data.db", limit: int = 5):
    """
    ดึงข้อมูล plate records จาก database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, plate_text, detections_json, plate_image_path
        FROM plate_records
        WHERE plate_text IS NOT NULL 
        AND plate_text != ''
        AND detections_json IS NOT NULL
        AND plate_image_path IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    records = cursor.fetchall()
    conn.close()
    
    return records


def load_plate_image(image_path: str) -> np.ndarray:
    """
    โหลดภาพป้ายทะเบียน
    """
    if not os.path.exists(image_path):
        return None
    
    img = cv2.imread(image_path)
    if img is not None:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def extract_character_details(detections_json: str) -> List[Dict]:
    """
    ดึง character details จาก detections_json
    """
    try:
        det_data = json.loads(detections_json)
        char_details = det_data.get("character_details", [])
        return char_details
    except:
        return []


def draw_bounding_boxes(img: np.ndarray, char_details: List[Dict], 
                       color: Tuple[int, int, int] = (0, 255, 0),
                       thickness: int = 2) -> np.ndarray:
    """
    วาด bounding boxes บนภาพ
    """
    img_with_boxes = img.copy()
    
    for char_detail in char_details:
        bbox = char_detail.get("bbox", {})
        x1 = int(bbox.get("x1", 0))
        y1 = int(bbox.get("y1", 0))
        x2 = int(bbox.get("x2", 0))
        y2 = int(bbox.get("y2", 0))
        
        # วาดกล่อง
        cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), color, thickness)
        
        # เพิ่ม label
        char = char_detail.get("character", "")
        conf = char_detail.get("confidence", 0.0)
        label = f"{char} ({conf:.2f})"
        
        # วาด label background
        (text_width, text_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        cv2.rectangle(
            img_with_boxes,
            (x1, y1 - text_height - 5),
            (x1 + text_width, y1),
            color,
            -1
        )
        
        # วาด text
        cv2.putText(
            img_with_boxes,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
    
    return img_with_boxes


def extract_character_images(img: np.ndarray, char_details: List[Dict]) -> List[np.ndarray]:
    """
    แยกตัวอักษรแต่ละตัวออกมา
    """
    char_images = []
    
    for char_detail in char_details:
        bbox = char_detail.get("bbox", {})
        x1 = int(bbox.get("x1", 0))
        y1 = int(bbox.get("y1", 0))
        x2 = int(bbox.get("x2", 0))
        y2 = int(bbox.get("y2", 0))
        
        # เพิ่ม padding
        pad = 3
        h, w = img.shape[:2]
        x1_pad = max(0, x1 - pad)
        y1_pad = max(0, y1 - pad)
        x2_pad = min(w, x2 + pad)
        y2_pad = min(h, y2 + pad)
        
        char_img = img[y1_pad:y2_pad, x1_pad:x2_pad]
        if char_img.size > 0:
            char_images.append(char_img)
        else:
            char_images.append(None)
    
    return char_images


def create_segmentation_figure(plate_img: np.ndarray, char_details: List[Dict],
                               plate_text: str, save_path: str):
    """
    สร้างรูปภาพรวมแสดงผลการแยกตัวอักษร
    """
    # (a) ภาพป้ายทะเบียนที่ตัดมา
    img_a = plate_img.copy()
    
    # (b) ภาพพร้อม bounding boxes
    img_b = draw_bounding_boxes(plate_img.copy(), char_details, 
                                color=(0, 255, 0), thickness=2)
    
    # (c) ตัวอักษรแต่ละตัว
    char_images = extract_character_images(plate_img, char_details)
    
    # (d) ผลลัพธ์ข้อความ
    # สร้าง text image
    text_img = np.ones((100, 600, 3), dtype=np.uint8) * 255
    cv2.putText(
        text_img,
        f"Result: {plate_text}",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 0, 0),
        2
    )
    
    # สร้าง figure
    fig = plt.figure(figsize=(16, 10))
    
    # (a) Original cropped plate
    ax1 = plt.subplot(2, 2, 1)
    ax1.imshow(img_a)
    ax1.set_title("(a) Cropped License Plate", fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    # (b) With bounding boxes
    ax2 = plt.subplot(2, 2, 2)
    ax2.imshow(img_b)
    ax2.set_title("(b) Character Bounding Boxes", fontsize=14, fontweight='bold')
    ax2.axis('off')
    
    # (c) Individual characters
    ax3 = plt.subplot(2, 2, 3)
    ax3.axis('off')
    ax3.set_title("(c) Segmented Characters", fontsize=14, fontweight='bold', pad=10)
    
    # แสดงตัวอักษรแต่ละตัวใน grid
    n_chars = len(char_images)
    if n_chars > 0:
        cols = min(8, n_chars)
        rows = (n_chars + cols - 1) // cols
        
        # สร้าง grid
        char_grid = np.ones((rows * 60, cols * 60, 3), dtype=np.uint8) * 255
        
        for idx, char_img in enumerate(char_images):
            if char_img is None:
                continue
            
            row = idx // cols
            col = idx % cols
            
            # Resize character image
            char_resized = cv2.resize(char_img, (50, 50))
            h, w = char_resized.shape[:2]
            
            y_start = row * 60 + 5
            x_start = col * 60 + 5
            
            if len(char_resized.shape) == 2:
                char_resized = cv2.cvtColor(char_resized, cv2.COLOR_GRAY2RGB)
            
            char_grid[y_start:y_start+h, x_start:x_start+w] = char_resized
            
            # เพิ่ม label
            char = char_details[idx].get("character", "")
            cv2.putText(
                char_grid,
                char,
                (x_start, y_start + h + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 0, 0),
                1
            )
        
        ax3.imshow(char_grid)
    
    # (d) Final result
    ax4 = plt.subplot(2, 2, 4)
    ax4.imshow(text_img)
    ax4.set_title("(d) Recognition Result", fontsize=14, fontweight='bold')
    ax4.axis('off')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved segmentation example to: {save_path}")
    
    plt.close()


def create_multiple_examples(records: List[Tuple], save_dir: str = "figures"):
    """
    สร้างตัวอย่างหลายๆ รูป
    """
    os.makedirs(save_dir, exist_ok=True)
    
    successful = 0
    
    for idx, (record_id, plate_text, detections_json, plate_image_path) in enumerate(records):
        # สร้าง full path
        if plate_image_path:
            if not plate_image_path.startswith('/'):
                cropped_path = f"uploads/plates/{plate_image_path}"
            else:
                cropped_path = plate_image_path
        else:
            cropped_path = None
        
        # โหลดภาพ
        if not cropped_path or not os.path.exists(cropped_path):
            print(f"⚠️  Image not found: {cropped_path}")
            continue
        
        plate_img = load_plate_image(cropped_path)
        if plate_img is None:
            print(f"⚠️  Failed to load image: {cropped_path}")
            continue
        
        # ดึง character details
        char_details = extract_character_details(detections_json)
        if not char_details:
            print(f"⚠️  No character details for record {record_id}")
            continue
        
        # สร้างรูปภาพ
        save_path = f"{save_dir}/6.2.3_segmentation_example_{idx+1}.png"
        create_segmentation_figure(plate_img, char_details, plate_text, save_path)
        successful += 1
        
        print(f"✅ Created example {idx+1}: {plate_text}")
    
    return successful


if __name__ == "__main__":
    print("📊 Creating Character Segmentation Examples (6.2.3)\n")
    
    # ดึงข้อมูลจาก database
    print("1. Loading records from database...")
    records = load_plate_records(limit=3)
    print(f"   Found {len(records)} records")
    
    if not records:
        print("❌ No records found!")
        exit(1)
    
    # สร้างตัวอย่าง
    print("\n2. Creating segmentation examples...")
    successful = create_multiple_examples(records)
    
    print(f"\n✅ Done! Created {successful} example(s)")
    print("\n📝 Note:")
    print("   - Examples saved to: figures/6.2.3_segmentation_example_*.png")
    print("   - Each example shows: (a) cropped plate, (b) bounding boxes, (c) individual chars, (d) result")

