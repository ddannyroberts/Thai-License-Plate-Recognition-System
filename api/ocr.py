import os
import cv2
import numpy as np
import pytesseract
from typing import Tuple, List

# ใช้จาก .env ถ้าเซ็ตไว้
TESS_LANG = os.getenv("TESSERACT_LANG", "tha+eng")

# อนุญาตเฉพาะอักขระที่พบในป้ายรถจักรยานยนต์ไทย (ลด noise)
# - ไทย ก-ฮ + สระ/วรรณยุกต์ทั่วไป + เว้นวรรค
# - ตัวเลข 0-9
# - เครื่องหมายคั่นที่บางที OCR เห็นเป็น | หรือ /
THAI_BLOCK = "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรฤลฦวศษสหฬอฮะาิีึืุูเแโใไ์่้๊๋็ๅๆฯ"
WHITE_LIST = f"0123456789{THAI_BLOCK} ์่้๊๋็์|/-"

# ---------- ตัวช่วย ----------
def _tess(img: np.ndarray, psm: int) -> str:
    cfg = f'--oem 3 --psm {psm} -l {TESS_LANG} -c tessedit_char_whitelist="{WHITE_LIST}"'
    try:
        s = pytesseract.image_to_string(img, config=cfg)
    except Exception:
        s = ""
    return s or ""

def _sharp(img: np.ndarray) -> np.ndarray:
    k = np.array([[0, -1, 0],
                  [-1, 5, -1],
                  [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(img, -1, k)

def _clahe(img: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

def _th_otsu(gray: np.ndarray) -> np.ndarray:
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

def _th_adapt(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(gray, 255,
                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 11)

def _clean(s: str) -> str:
    # ตัด \n และช่องว่างซ้ำ / normalize ให้เรียบ
    return " ".join(s.replace("\n", " ").replace("\r", " ").split())

def _score_plate(s: str) -> int:
    """
    ให้คะแนนสตริง: เน้นรูปแบบป้ายทะเบียนไทย
    รูปแบบที่ดี:
    - กร 1234 (รหัส 2 ตัว + เลข 4 ตัว)
    - 1กร 1234 (เลข + รหัส 2 ตัว + เลข)
    - กก 123 (รหัส 2 ตัว + เลข 3 ตัว)
    """
    import re
    s0 = s
    s = s.replace("|", "").replace("/", "").replace("-", "").strip()
    
    score = 0
    
    # Pattern 1: รหัสจังหวัด 2 ตัว + เลข 3-4 ตัว
    pattern1 = re.compile(r'^([ก-ฮ]{2})\s*([0-9]{3,4})$')
    m1 = pattern1.match(s)
    if m1:
        score += 100  # คะแนนสูงสุด
        score += len(m1.group(2)) * 10
        return score
    
    # Pattern 2: เลข 1 ตัว + รหัสจังหวัด 2 ตัว + เลข 4-5 ตัว
    pattern2 = re.compile(r'^([0-9]{1})([ก-ฮ]{2})\s*([0-9]{4,5})$')
    m2 = pattern2.match(s)
    if m2:
        score += 95
        score += len(m2.group(3)) * 8
        return score
    
    # Pattern 3: รหัสจังหวัด + เลข (ไม่จำกัดจำนวน)
    pattern3 = re.compile(r'([ก-ฮ]{1,2})\s*([0-9]+)')
    m3 = pattern3.search(s)
    if m3:
        score += 50
        score += len(m3.group(2)) * 5
        score += len(m3.group(1)) * 3
    
    # ลบตัวอักษรที่ไม่อยู่ใน whitelist
    kept = [ch for ch in s0 if ch in WHITE_LIST]
    score += len(kept)
    
    # ลดคะแนนถ้ามี noise มาก
    noise_chars = [ch for ch in s0 if ch not in WHITE_LIST]
    score -= len(noise_chars) * 5
    
    return max(0, score)

# ---------- ฟังก์ชันหลัก ----------
def run_ocr_on_bbox(img: np.ndarray, x: int, y: int, w: int, h: int) -> str:
    """
    รับภาพเต็ม + กรอบ (ซ้ายบน + กว้างสูง) -> คืนข้อความป้ายที่ดีที่สุด
    ลองหลายพรีโปรเซส/ค่า psm แล้วเลือกสตริงที่ได้คะแนนดีที่สุด
    """
    H, W = img.shape[:2]
    x = max(0, min(x, W - 1))
    y = max(0, min(y, H - 1))
    w = max(1, min(w, W - x))
    h = max(1, min(h, H - y))

    roi = img[y:y+h, x:x+w].copy()

    # upscale มากขึ้นเพื่อช่วย OCR (ขนาดเป้าหมาย: 300px)
    target_height = 300
    if h > 0:
        scale = max(2, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        print(f"DEBUG OCR upscale: {w}x{h} -> {new_w}x{new_h} (scale={scale:.1f}x)", flush=True)

    variants: List[np.ndarray] = []

    # พื้นฐาน
    variants.append(roi)
    variants.append(_sharp(roi))
    variants.append(_clahe(roi))

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    variants.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
    variants.append(cv2.cvtColor(_th_otsu(gray), cv2.COLOR_GRAY2BGR))
    variants.append(cv2.cvtColor(_th_adapt(gray), cv2.COLOR_GRAY2BGR))

    # กลับค่า (บางแผ่นพื้นอ่อน/ตัวอักษรเข้ม)
    for i in range(len(variants)):
        inv = cv2.bitwise_not(variants[i])
        variants.append(inv)

    # รันด้วย psm หลัก ๆ ที่ใช้ได้ดีกับป้าย
    psms = [7, 6, 8, 13]

    cands: List[str] = []
    for v in variants:
        for p in psms:
            cands.append(_clean(_tess(v, p)))

    # เลือกสตริงที่คะแนนดีที่สุด
    best = ""
    best_score = -1
    for s in cands:
        sc = _score_plate(s)
        if sc > best_score:
            best, best_score = s, sc

    return best
