# api/local_models.py
import os
from ultralytics import YOLO

_DET_PATH = os.getenv("DETECTOR_WEIGHTS", "models/detector/best.pt")
_READ_PATH = os.getenv("READER_WEIGHTS", "models/reader/best.pt")

print(f"[INFO] 🟠 Using local YOLO DETECTOR from: {_DET_PATH}", flush=True)
print(f"[INFO] 🔵 Using local YOLO READER   from: {_READ_PATH}", flush=True)

_det = YOLO(_DET_PATH)
_reader = YOLO(_READ_PATH)

def infer_detector(img):
    # คืนผลเป็น list ของ {x1,y1,x2,y2,confidence,class/name}
    res = _det(img)[0]
    out = []
    for b in res.boxes:
        x1, y1, x2, y2 = map(float, b.xyxy[0].tolist())
        conf = float(b.conf[0].item())
        cls_id = int(b.cls[0].item())
        cls_name = res.names.get(cls_id, str(cls_id))
        out.append({"x1":x1,"y1":y1,"x2":x2,"y2":y2,"confidence":conf,"class":cls_name})
    return out

def infer_reader(img):
    # คืนผลแบบ Roboflow-style {predictions:[{class/name, confidence, x,y,width,height,x1,y1,x2,y2}...]}
    res = _reader(img)[0]
    preds = []
    for b in res.boxes:
        x1, y1, x2, y2 = map(float, b.xyxy[0].tolist())
        w, h = x2 - x1, y2 - y1
        x, y = x1 + w/2, y1 + h/2
        conf = float(b.conf[0].item())
        cls_id = int(b.cls[0].item())
        cls_name = res.names.get(cls_id, str(cls_id))
        preds.append({
            "class": cls_name, 
            "confidence": conf, 
            "x": x, 
            "y": y, 
            "width": w, 
            "height": h,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        })
    return {"predictions": preds}
