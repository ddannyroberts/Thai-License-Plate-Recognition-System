"""
Character Segmentation and OCR
แยกตัวอักษรทีละตัวจากป้ายทะเบียน แล้วค่อย OCR แต่ละตัว
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from .local_models import infer_reader
from .ocr import _tess, _clean, _sharp, _clahe, _th_otsu, _th_adapt, TESS_LANG, WHITE_LIST

def sort_characters_by_position(char_boxes: List[Dict]) -> List[Dict]:
    """
    จัดเรียงตัวอักษรตามตำแหน่ง (ซ้ายไปขวา, บนลงล่าง)
    
    Args:
        char_boxes: List of character boxes with x, y, width, height
        
    Returns:
        Sorted list of character boxes
    """
    if not char_boxes:
        return []
    
    # คำนวณ average y เพื่อแยกว่าอยู่แถวบนหรือล่าง
    avg_y = sum(box.get("y", 0) for box in char_boxes) / len(char_boxes)
    
    # แยกเป็นแถว (ถ้ามี 2 แถว)
    row1 = []
    row2 = []
    
    for box in char_boxes:
        y = box.get("y", 0)
        if y < avg_y:
            row1.append(box)
        else:
            row2.append(box)
    
    # จัดเรียงแต่ละแถวตาม x (ซ้ายไปขวา)
    row1.sort(key=lambda b: b.get("x", 0))
    row2.sort(key=lambda b: b.get("x", 0))
    
    # รวมแถว (แถวบนมาก่อน)
    return row1 + row2

def extract_character_regions(plate_img: np.ndarray, reader_predictions: List[Dict], 
                              min_conf: float = 0.3) -> List[Dict]:
    """
    Extract character regions จาก reader model predictions
    
    Args:
        plate_img: ภาพป้ายทะเบียนที่ crop แล้ว
        reader_predictions: ผลลัพธ์จาก infer_reader()
        min_conf: Confidence threshold ขั้นต่ำ
        
    Returns:
        List of character regions with bounding boxes
    """
    H, W = plate_img.shape[:2]
    char_regions = []
    
    for pred in reader_predictions:
        conf = float(pred.get("confidence", 0.0))
        if conf < min_conf:
            continue
        
        # Try to get corner coordinates first (more accurate)
        x1 = pred.get("x1")
        y1 = pred.get("y1")
        x2 = pred.get("x2")
        y2 = pred.get("y2")
        
        if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
            # Use corner coordinates directly
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        else:
            # Fallback to center-based calculation
            x_center = float(pred.get("x", 0))
            y_center = float(pred.get("y", 0))
            width = float(pred.get("width", 0))
            height = float(pred.get("height", 0))
            
            x1 = max(0, int(x_center - width / 2))
            y1 = max(0, int(y_center - height / 2))
            x2 = min(W, int(x_center + width / 2))
            y2 = min(H, int(y_center + height / 2))
        
        # Sanitize coordinates
        x1, y1 = max(0, min(x1, W-1)), max(0, min(y1, H-1))
        x2, y2 = max(0, max(x1, x2)), max(0, max(y1, y2))
        x2, y2 = min(W, x2), min(H, y2)
        
        # Ensure valid region
        width = x2 - x1
        height = y2 - y1
        
        if x2 > x1 and y2 > y1 and width > 5 and height > 5:
            # Add small padding
            pad = 2
            x1_pad = max(0, x1 - pad)
            y1_pad = max(0, y1 - pad)
            x2_pad = min(W, x2 + pad)
            y2_pad = min(H, y2 + pad)
            
            char_regions.append({
                "x1": x1_pad,
                "y1": y1_pad,
                "x2": x2_pad,
                "y2": y2_pad,
                "x": (x1 + x2) / 2,
                "y": (y1 + y2) / 2,
                "width": x2_pad - x1_pad,
                "height": y2_pad - y1_pad,
                "confidence": conf,
                "class": pred.get("class", ""),
                "region_img": plate_img[y1_pad:y2_pad, x1_pad:x2_pad].copy()
            })
    
    return char_regions

def ocr_single_character(char_img: np.ndarray, char_class: Optional[str] = None, 
                         model_confidence: float = 0.0) -> str:
    """
    อ่านตัวอักษรเดียว - ใช้ Model Dataset เป็นหลัก แล้ว OCR เป็น fallback
    
    Priority:
    1. ใช้ class name จาก Reader Model (dataset ของคุณ) ถ้า confidence สูง
    2. ใช้ OCR เป็น fallback ถ้า model confidence ต่ำหรือไม่มี class
    
    Args:
        char_img: ภาพตัวอักษรเดียว
        char_class: Class name จาก Reader Model (dataset ของคุณ) - เช่น "ก", "1", "กร"
        model_confidence: Confidence จาก Reader Model
        
    Returns:
        ข้อความที่อ่านได้
    """
    if char_img.size == 0:
        return ""
    
    # ===== Priority 1: ใช้ Class Name จาก Reader Model (Dataset ของคุณ) =====
    MODEL_CONFIDENCE_THRESHOLD = 0.5  # ถ้า confidence สูงกว่านี้ ใช้ class name จาก model
    
    if char_class and model_confidence >= MODEL_CONFIDENCE_THRESHOLD:
        # Clean class name (อาจมี space, ตัวเลข, หรืออักขระพิเศษ)
        cleaned_class = char_class.strip()
        
        # ถ้า class name เป็นตัวอักษร/ตัวเลขเดียว
        if len(cleaned_class) == 1 and cleaned_class in WHITE_LIST:
            print(f"DEBUG: Using model class '{cleaned_class}' (conf={model_confidence:.2f})", flush=True)
            return cleaned_class
        
        # ถ้า class name เป็นหลายตัวอักษร (เช่น "กร", "12") ใช้ตัวแรก
        if len(cleaned_class) > 1:
            first_char = cleaned_class[0]
            if first_char in WHITE_LIST:
                print(f"DEBUG: Using first char '{first_char}' from model class '{cleaned_class}' (conf={model_confidence:.2f})", flush=True)
                return first_char
    
    # ===== Priority 2: ใช้ OCR เป็น Fallback =====
    # Preprocess for better OCR
    h, w = char_img.shape[:2]
    
    # Upscale สำหรับ OCR ที่ดีขึ้น
    target_height = 100
    if h > 0:
        scale = max(2, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        char_img = cv2.resize(char_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # Try multiple preprocessing variants
    variants = []
    
    # Grayscale
    if len(char_img.shape) == 3:
        gray = cv2.cvtColor(char_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = char_img
    
    variants.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
    variants.append(cv2.cvtColor(_th_otsu(gray), cv2.COLOR_GRAY2BGR))
    variants.append(cv2.cvtColor(_th_adapt(gray), cv2.COLOR_GRAY2BGR))
    
    # Sharpened
    if len(char_img.shape) == 3:
        variants.append(_sharp(char_img))
        variants.append(_clahe(char_img))
    
    # Inverted
    for v in variants[:]:
        variants.append(cv2.bitwise_not(v))
    
    # Try OCR with different PSM modes (PSM 10 = single character)
    best_text = ""
    
    for variant in variants:
        # PSM 10 = Treat the image as a single character
        text = _clean(_tess(variant, psm=10))
        
        if text and len(text) > 0:
            # Filter by whitelist
            filtered = "".join(c for c in text if c in WHITE_LIST)
            if filtered:
                best_text = filtered
                print(f"DEBUG: OCR fallback result: '{best_text}'", flush=True)
                break
    
    # ถ้า OCR ไม่ได้ผล แต่มี class name จาก model (confidence ต่ำ) ให้ลองใช้เป็น fallback
    if not best_text and char_class:
        cleaned_class = char_class.strip()
        if len(cleaned_class) == 1 and cleaned_class in WHITE_LIST:
            print(f"DEBUG: Using model class '{cleaned_class}' as fallback (conf={model_confidence:.2f})", flush=True)
            return cleaned_class
    
    return best_text[:1] if best_text else ""  # Return only first character

def read_plate_by_characters(plate_img: np.ndarray) -> Tuple[str, List[Dict]]:
    """
    อ่านป้ายทะเบียนโดยแยกตัวอักษรทีละตัวก่อน
    
    Pipeline:
    1. ใช้ Reader Model detect ตัวอักษรแต่ละตัว
    2. จัดเรียงตัวอักษรตามตำแหน่ง (ซ้ายไปขวา)
    3. OCR แต่ละตัวอักษร
    4. รวมเป็นข้อความ
    
    Args:
        plate_img: ภาพป้ายทะเบียนที่ crop แล้ว
        
    Returns:
        (plate_text, character_details)
        character_details: List of dict with char, confidence, position
    """
    # Step 1: ใช้ Reader Model detect ตัวอักษร
    reader_result = infer_reader(plate_img)
    predictions = reader_result.get("predictions", [])
    
    if not predictions:
        return "", []
    
    print(f"DEBUG: Found {len(predictions)} character detections", flush=True)
    
    # Step 2: Extract character regions
    char_regions = extract_character_regions(plate_img, predictions, min_conf=0.3)
    
    if not char_regions:
        return "", []
    
    print(f"DEBUG: Extracted {len(char_regions)} character regions", flush=True)
    
    # Step 3: จัดเรียงตัวอักษรตามตำแหน่ง
    sorted_chars = sort_characters_by_position(char_regions)
    
    # Step 4: OCR แต่ละตัวอักษร
    character_details = []
    plate_chars = []
    
    for idx, char_region in enumerate(sorted_chars):
        char_img = char_region.get("region_img")
        char_class = char_region.get("class", "")
        conf = char_region.get("confidence", 0.0)
        
        if char_img is None or char_img.size == 0:
            continue
        
        # อ่านตัวอักษร - ใช้ Model Dataset (class name) เป็นหลัก แล้ว OCR เป็น fallback
        char_text = ocr_single_character(char_img, char_class, model_confidence=conf)
        
        if char_text:
            plate_chars.append(char_text)
            character_details.append({
                "index": idx,
                "character": char_text,
                "confidence": conf,
                "x": char_region.get("x", 0),
                "y": char_region.get("y", 0),
                "bbox": {
                    "x1": char_region.get("x1", 0),
                    "y1": char_region.get("y1", 0),
                    "x2": char_region.get("x2", 0),
                    "y2": char_region.get("y2", 0)
                },
                "model_class": char_class
            })
    
    # Step 5: รวมตัวอักษรเป็นข้อความ
    plate_text = "".join(plate_chars)
    
    # Clean up text (remove extra spaces, normalize)
    plate_text = " ".join(plate_text.split())  # Normalize spaces
    
    print(f"DEBUG: Character segmentation result: '{plate_text}' from {len(character_details)} characters", flush=True)
    
    return plate_text, character_details

