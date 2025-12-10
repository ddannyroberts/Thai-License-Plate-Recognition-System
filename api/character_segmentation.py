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
    ปรับปรุงให้รองรับหลายแถวได้ดีขึ้น
    
    Args:
        char_boxes: List of character boxes with x, y, width, height
        
    Returns:
        Sorted list of character boxes
    """
    if not char_boxes:
        return []
    
    # คำนวณ average y และ std เพื่อแยกว่าแถว
    y_values = [box.get("y", 0) for box in char_boxes]
    avg_y = sum(y_values) / len(y_values)
    
    # คำนวณ height เพื่อใช้เป็น threshold
    heights = [box.get("height", 0) for box in char_boxes]
    avg_height = sum(heights) / len(heights) if heights else 20
    
    # ใช้ threshold ที่ดีขึ้น: ถ้าต่างกันมากกว่า 30% ของความสูงเฉลี่ย = ต่างแถว
    row_threshold = avg_height * 0.3
    
    # แยกเป็นแถว
    rows = {}
    
    for box in char_boxes:
        y = box.get("y", 0)
        
        # หาแถวที่ใกล้ที่สุด
        found_row = False
        for row_y in sorted(rows.keys()):
            if abs(y - row_y) < row_threshold:
                rows[row_y].append(box)
                found_row = True
                break
        
        if not found_row:
            rows[y] = [box]
    
    # จัดเรียงแต่ละแถวตาม x (ซ้ายไปขวา) และเรียงแถวตาม y (บนลงล่าง)
    sorted_rows = []
    for row_y in sorted(rows.keys()):
        row_chars = rows[row_y]
        row_chars.sort(key=lambda b: b.get("x", 0))
        sorted_rows.extend(row_chars)
    
    return sorted_rows

def extract_character_regions(plate_img: np.ndarray, reader_predictions: List[Dict], 
                              min_conf: float = 0.4) -> List[Dict]:
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
            # เพิ่ม padding มากขึ้นเพื่อให้ model อ่านได้ดีขึ้น
            pad_x = max(3, int(width * 0.1))  # 10% ของความกว้าง
            pad_y = max(3, int(height * 0.1))  # 10% ของความสูง
            x1_pad = max(0, x1 - pad_x)
            y1_pad = max(0, y1 - pad_y)
            x2_pad = min(W, x2 + pad_x)
            y2_pad = min(H, y2 + pad_y)
            
            # Crop character region
            char_crop = plate_img[y1_pad:y2_pad, x1_pad:x2_pad].copy()
            
            # Preprocess crop เพื่อให้อ่านได้ดีขึ้น
            # เพิ่ม contrast และ sharpness
            if char_crop.size > 0:
                # Convert to grayscale for processing
                if len(char_crop.shape) == 3:
                    gray_crop = cv2.cvtColor(char_crop, cv2.COLOR_BGR2GRAY)
                else:
                    gray_crop = char_crop.copy()
                
                # Apply CLAHE for better contrast
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
                enhanced = clahe.apply(gray_crop)
                
                # Convert back to BGR
                if len(char_crop.shape) == 3:
                    enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
                else:
                    enhanced_bgr = enhanced
                
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
                    "region_img": enhanced_bgr  # ใช้ enhanced image
                })
    
    return char_regions

def read_character_with_model(char_img: np.ndarray) -> Tuple[str, float]:
    """
    อ่านตัวอักษรเดียวโดยใช้ Reader Model โดยตรง
    ลองหลาย variants ของภาพเพื่อให้ได้ผลลัพธ์ที่ดีที่สุด
    
    Args:
        char_img: ภาพตัวอักษรเดียวที่ตัดแล้ว
        
    Returns:
        (character_text, confidence)
    """
    if char_img.size == 0:
        return "", 0.0
    
    # สร้าง variants หลายแบบเพื่อให้ model อ่านได้ดีขึ้น
    variants = []
    
    # 1. Original image (upscaled)
    h, w = char_img.shape[:2]
    target_height = 160  # เพิ่มขนาดเพื่อให้ model อ่านได้ดีขึ้น
    if h > 0:
        scale = max(3, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        upscaled = cv2.resize(char_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        variants.append(("original", upscaled))
    
    # 2. Grayscale
    if len(char_img.shape) == 3:
        gray = cv2.cvtColor(char_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = char_img.copy()
    
    if h > 0:
        gray_upscaled = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        variants.append(("grayscale", cv2.cvtColor(gray_upscaled, cv2.COLOR_GRAY2BGR)))
    
    # 3. Threshold (Otsu)
    if h > 0:
        th_otsu = _th_otsu(gray)
        th_otsu_upscaled = cv2.resize(th_otsu, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        variants.append(("otsu", cv2.cvtColor(th_otsu_upscaled, cv2.COLOR_GRAY2BGR)))
    
    # 4. Adaptive Threshold
    if h > 0:
        th_adapt = _th_adapt(gray)
        th_adapt_upscaled = cv2.resize(th_adapt, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        variants.append(("adaptive", cv2.cvtColor(th_adapt_upscaled, cv2.COLOR_GRAY2BGR)))
    
    # 5. Sharpened
    if len(char_img.shape) == 3 and h > 0:
        sharpened = _sharp(char_img)
        sharpened_upscaled = cv2.resize(sharpened, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        variants.append(("sharpened", sharpened_upscaled))
    
    # 6. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    if len(char_img.shape) == 3 and h > 0:
        clahe_img = _clahe(char_img)
        clahe_upscaled = cv2.resize(clahe_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        variants.append(("clahe", clahe_upscaled))
    
    # 7. Inverted versions
    inverted_variants = []
    for name, variant_img in variants:
        inverted = cv2.bitwise_not(variant_img)
        inverted_variants.append((f"{name}_inv", inverted))
    variants.extend(inverted_variants)
    
    # ลองใช้ Reader Model กับทุก variant และเลือกผลลัพธ์ที่ดีที่สุด
    all_predictions = []  # เก็บทุก prediction เพื่อเลือกที่ดีที่สุด
    
    for variant_name, variant_img in variants:
        try:
            reader_result = infer_reader(variant_img)
            predictions = reader_result.get("predictions", [])
            
            if predictions:
                # เก็บทุก prediction ที่ valid
                for pred in predictions:
                    char_class = pred.get("class", "").strip()
                    confidence = float(pred.get("confidence", 0.0))
                    
                    if char_class and confidence > 0.3:  # ลด threshold เพื่อให้ได้ตัวอักษรมากขึ้น
                        # ถ้าเป็นตัวอักษร/ตัวเลขเดียว
                        if len(char_class) == 1 and char_class in WHITE_LIST:
                            all_predictions.append({
                                "char": char_class,
                                "confidence": confidence,
                                "variant": variant_name
                            })
                        # ถ้าเป็นหลายตัวอักษร ใช้ตัวแรก
                        elif len(char_class) > 1:
                            first_char = char_class[0]
                            if first_char in WHITE_LIST:
                                all_predictions.append({
                                    "char": first_char,
                                    "confidence": confidence,
                                    "variant": variant_name
                                })
        except Exception as e:
            print(f"DEBUG: Error reading character with variant {variant_name}: {e}", flush=True)
            continue
    
    # เลือกผลลัพธ์ที่ดีที่สุด
    if all_predictions:
        # ถ้ามีหลาย prediction ที่เหมือนกัน ให้เลือกที่ confidence สูงสุด
        char_counts = {}
        for pred in all_predictions:
            char = pred["char"]
            if char not in char_counts:
                char_counts[char] = []
            char_counts[char].append(pred)
        
        # หา character ที่มี confidence สูงสุด
        best_char = ""
        best_confidence = 0.0
        best_variant = ""
        
        for char, preds in char_counts.items():
            # คำนวณ average confidence และ max confidence
            avg_conf = sum(p["confidence"] for p in preds) / len(preds)
            max_conf = max(p["confidence"] for p in preds)
            
            # ใช้ weighted score: (avg_conf * 0.3) + (max_conf * 0.7)
            score = (avg_conf * 0.3) + (max_conf * 0.7)
            
            if score > best_confidence:
                best_char = char
                best_confidence = score
                best_pred = max(preds, key=lambda p: p["confidence"])
                best_variant = best_pred["variant"]
        
        if best_char:
            print(f"DEBUG: Model read '{best_char}' (conf={best_confidence:.2f}, variant={best_variant}, total_predictions={len(all_predictions)})", flush=True)
            return best_char, best_confidence
    
    return "", 0.0

def ocr_single_character(char_img: np.ndarray, char_class: Optional[str] = None, 
                         model_confidence: float = 0.0) -> str:
    """
    อ่านตัวอักษรเดียว - ใช้ Reader Model อ่านโดยตรง (ไม่ใช้ OCR)
    
    Priority:
    1. ใช้ Reader Model อ่านตัวอักษรที่ตัดแล้วโดยตรง
    2. ใช้ class name จาก Reader Model (จากการ detect ครั้งแรก) ถ้า confidence สูง
    3. ใช้ OCR เป็น fallback สุดท้าย
    
    Args:
        char_img: ภาพตัวอักษรเดียว
        char_class: Class name จาก Reader Model (dataset ของคุณ) - เช่น "ก", "1", "กร"
        model_confidence: Confidence จาก Reader Model
        
    Returns:
        ข้อความที่อ่านได้
    """
    if char_img.size == 0:
        return ""
    
    # ===== Priority 1: ใช้ Reader Model อ่านตัวอักษรที่ตัดแล้วโดยตรง =====
    char_text, model_conf = read_character_with_model(char_img)
    if char_text:
        print(f"DEBUG: Using direct model reading: '{char_text}' (conf={model_conf:.2f})", flush=True)
        return char_text
    
    # ===== Priority 2: ใช้ Class Name จาก Reader Model (จากการ detect ครั้งแรก) =====
    MODEL_CONFIDENCE_THRESHOLD = 0.5  # ลด threshold เพราะใช้เป็น fallback
    
    if char_class and model_confidence >= MODEL_CONFIDENCE_THRESHOLD:
        cleaned_class = char_class.strip()
        
        if len(cleaned_class) == 1 and cleaned_class in WHITE_LIST:
            print(f"DEBUG: Using initial detection class '{cleaned_class}' (conf={model_confidence:.2f})", flush=True)
            return cleaned_class
        
        if len(cleaned_class) > 1:
            first_char = cleaned_class[0]
            if first_char in WHITE_LIST:
                print(f"DEBUG: Using first char '{first_char}' from initial detection '{cleaned_class}' (conf={model_confidence:.2f})", flush=True)
                return first_char
    
    # ===== Priority 3: ใช้ OCR เป็น Fallback สุดท้าย =====
    h, w = char_img.shape[:2]
    target_height = 100
    if h > 0:
        scale = max(2, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        char_img = cv2.resize(char_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    variants = []
    if len(char_img.shape) == 3:
        gray = cv2.cvtColor(char_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = char_img
    
    variants.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
    variants.append(cv2.cvtColor(_th_otsu(gray), cv2.COLOR_GRAY2BGR))
    variants.append(cv2.cvtColor(_th_adapt(gray), cv2.COLOR_GRAY2BGR))
    
    if len(char_img.shape) == 3:
        variants.append(_sharp(char_img))
        variants.append(_clahe(char_img))
    
    for v in variants[:]:
        variants.append(cv2.bitwise_not(v))
    
    best_text = ""
    for variant in variants:
        text = _clean(_tess(variant, psm=10))
        if text and len(text) > 0:
            filtered = "".join(c for c in text if c in WHITE_LIST)
            if filtered:
                best_text = filtered
                print(f"DEBUG: OCR fallback result: '{best_text}'", flush=True)
                break
    
    if not best_text and char_class:
        cleaned_class = char_class.strip()
        if len(cleaned_class) == 1 and cleaned_class in WHITE_LIST:
            print(f"DEBUG: Using model class '{cleaned_class}' as final fallback (conf={model_confidence:.2f})", flush=True)
            return cleaned_class
    
    return best_text[:1] if best_text else ""

def read_plate_by_characters(plate_img: np.ndarray) -> Tuple[str, List[Dict]]:
    """
    อ่านป้ายทะเบียนโดยแยกตัวอักษรทีละตัวก่อน
    
    Pipeline:
    1. ใช้ Reader Model detect ตัวอักษรแต่ละตัว (เพื่อหา bounding boxes)
    2. ตัดขอบให้แต่ละตัวอักษร (crop character regions)
    3. ใช้ Reader Model อ่านแต่ละตัวอักษรที่ตัดแล้วโดยตรง
    4. รวมเป็นข้อความ
    
    Args:
        plate_img: ภาพป้ายทะเบียนที่ crop แล้ว
        
    Returns:
        (plate_text, character_details)
        character_details: List of dict with char, confidence, position
    """
    # Step 1: ใช้ Reader Model detect ตัวอักษร (เพื่อหา bounding boxes)
    reader_result = infer_reader(plate_img)
    predictions = reader_result.get("predictions", [])
    
    if not predictions:
        return "", []
    
    print(f"DEBUG: Found {len(predictions)} character detections", flush=True)
    
    # Step 2: Extract character regions (ตัดขอบให้แต่ละตัว) - ลด threshold เพื่อจับตัวอักษรได้มากขึ้น
    char_regions = extract_character_regions(plate_img, predictions, min_conf=0.3)
    
    if not char_regions:
        return "", []
    
    print(f"DEBUG: Extracted {len(char_regions)} character regions (cropped)", flush=True)
    
    # Step 3: จัดเรียงตัวอักษรตามตำแหน่ง (ซ้ายไปขวา)
    sorted_chars = sort_characters_by_position(char_regions)
    
    # Step 4: ใช้ Reader Model อ่านแต่ละตัวอักษรที่ตัดแล้ว
    character_details = []
    plate_chars = []
    
    for idx, char_region in enumerate(sorted_chars):
        char_img = char_region.get("region_img")
        initial_class = char_region.get("class", "")  # class จาก detection ครั้งแรก
        initial_conf = char_region.get("confidence", 0.0)
        
        if char_img is None or char_img.size == 0:
            continue
        
        # ใช้ Reader Model อ่านตัวอักษรที่ตัดแล้วโดยตรง
        char_text = ocr_single_character(char_img, char_class=initial_class, model_confidence=initial_conf)
        
        if char_text:
            plate_chars.append(char_text)
            character_details.append({
                "index": idx,
                "character": char_text,
                "confidence": initial_conf,
                "x": char_region.get("x", 0),
                "y": char_region.get("y", 0),
                "bbox": {
                    "x1": char_region.get("x1", 0),
                    "y1": char_region.get("y1", 0),
                    "x2": char_region.get("x2", 0),
                    "y2": char_region.get("y2", 0)
                },
                "model_class": initial_class,
                "method": "reader_model"  # บอกว่าใช้ reader model อ่าน
            })
    
    # Step 5: รวมตัวอักษรเป็นข้อความ (รองรับหลายแถว)
    # จัดกลุ่มตัวอักษรตามแถว
    if not plate_chars:
        return "", []
    
    # หาแถวจาก character_details
    y_positions = [detail.get("y", 0) for detail in character_details]
    if y_positions:
        avg_y = sum(y_positions) / len(y_positions)
        row_threshold = 20  # threshold สำหรับแยกแถว
        
        row1_chars = []
        row2_chars = []
        
        for i, detail in enumerate(character_details):
            y = detail.get("y", 0)
            char = detail.get("character", "")
            if y < avg_y - row_threshold:
                row1_chars.append((i, char))
            elif y > avg_y + row_threshold:
                row2_chars.append((i, char))
            else:
                # ถ้าอยู่กลางๆ ให้ดูว่าใกล้แถวไหนมากกว่า
                if abs(y - (avg_y - row_threshold)) < abs(y - (avg_y + row_threshold)):
                    row1_chars.append((i, char))
                else:
                    row2_chars.append((i, char))
        
        # จัดเรียงแต่ละแถวตาม x
        row1_chars.sort(key=lambda x: character_details[x[0]].get("x", 0))
        row2_chars.sort(key=lambda x: character_details[x[0]].get("x", 0))
        
        # รวมข้อความ (แถวบนก่อน แล้วตามด้วยแถวล่าง)
        if row1_chars and row2_chars:
            row1_text = "".join([char for _, char in row1_chars])
            row2_text = "".join([char for _, char in row2_chars])
            plate_text = f"{row1_text} {row2_text}"
        elif row1_chars:
            plate_text = "".join([char for _, char in row1_chars])
        elif row2_chars:
            plate_text = "".join([char for _, char in row2_chars])
        else:
            plate_text = "".join(plate_chars)
    else:
        plate_text = "".join(plate_chars)
    
    # Clean up text (remove extra spaces, normalize)
    plate_text = " ".join(plate_text.split())  # Normalize spaces
    
    # Step 6: Validate และ filter noise
    # ลบตัวอักษรที่ไม่อยู่ใน whitelist
    filtered_text = "".join(c for c in plate_text if c in WHITE_LIST or c == " ")
    # ลบช่องว่างซ้ำ
    filtered_text = " ".join(filtered_text.split())
    
    # ถ้าผลลัพธ์มีตัวอักษรน้อยเกินไป หรือมี noise มาก ให้ใช้ filtered version
    if len(filtered_text) < len(plate_text) * 0.7:  # ถ้า filter ออกมากกว่า 30%
        print(f"DEBUG: Filtered noise from '{plate_text}' to '{filtered_text}'", flush=True)
        plate_text = filtered_text
    
    print(f"DEBUG: Character segmentation result: '{plate_text}' from {len(character_details)} characters", flush=True)
    
    return plate_text, character_details

