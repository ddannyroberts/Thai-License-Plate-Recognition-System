# api/utils.py
import os
from typing import Dict, List, Tuple

# ตั้งค่าเกณฑ์คัดกรองกล่องจาก ENV (default 0.15)
MIN_BOX_CONF = float(os.getenv("READER_MIN_CONF", "0.15"))

# รองรับหลายชื่อคลาส (ยืดหยุ่นเรื่อง label)
ALIASES = {
    "letters": {"letters", "letter", "chars", "characters", "text"},
    "province": {"province", "prov", "region", "province_text", "prov_text"},
}

def extract_bboxes(
    predictions: List[Dict],
    target_class: str,
    min_conf: float = MIN_BOX_CONF
) -> List[Tuple[int, int, int, int, float]]:
    """
    รองรับ 2 ฟอร์แมต:
      - center-based: x,y,width,height
      - corner-based: x1,y1,x2,y2
    คืนค่า (x_tl, y_tl, w, h, conf)
    """
    want = {w.lower() for w in ALIASES.get(target_class, {target_class})}
    boxes: List[Tuple[int, int, int, int, float]] = []

    for p in predictions or []:
        cls = (p.get("class") or p.get("name") or "").lower()
        if cls not in want:
            continue

        conf = float(p.get("confidence", p.get("conf", 0.0)))

        # center-based
        if all(k in p for k in ("x", "y", "width", "height")):
            x_c, y_c = float(p["x"]), float(p["y"])
            w, h = float(p["width"]), float(p["height"])
            x_tl = int(round(x_c - w / 2))
            y_tl = int(round(y_c - h / 2))
            if conf >= min_conf and w > 3 and h > 3:
                boxes.append((x_tl, y_tl, int(round(w)), int(round(h)), conf))
            continue

        # corner-based
        x1, y1, x2, y2 = p.get("x1"), p.get("y1"), p.get("x2"), p.get("y2")
        if None not in (x1, y1, x2, y2):
            x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
            x_tl = int(round(min(x1, x2)))
            y_tl = int(round(min(y1, y2)))
            w = int(round(abs(x2 - x1)))
            h = int(round(abs(y2 - y1)))
            if conf >= min_conf and w > 3 and h > 3:
                boxes.append((x_tl, y_tl, w, h, conf))
            continue

    return boxes

def merge_boxes(boxes: List[Tuple[int, int, int, int, float]]):
    """
    รวมหลายกรอบเป็นกรอบเดียวแบบ union
    """
    if not boxes:
        return None
    x1s, y1s, x2s, y2s = [], [], [], []
    for x, y, w, h, _ in boxes:
        x1s.append(x); y1s.append(y)
        x2s.append(x + w); y2s.append(y + h)
    x1, y1 = min(x1s), min(y1s)
    x2, y2 = max(x2s), max(y2s)
    return int(x1), int(y1), int(x2 - x1), int(y2 - y1)
