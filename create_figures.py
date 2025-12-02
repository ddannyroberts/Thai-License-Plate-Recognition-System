"""
Script สำหรับสร้างรูปภาพสำหรับ Research Paper
- Precision-Recall Curve
- ตัวอย่างผลการตรวจจับ
"""

import numpy as np
import matplotlib.pyplot as plt
import cv2
from pathlib import Path
from typing import List, Tuple, Dict
import json

# ============================================
# 1. สร้างกราฟ Precision-Recall Curve
# ============================================

def calculate_precision_recall(predictions: List[Dict], ground_truth: List[Dict], 
                               iou_threshold: float = 0.5) -> Tuple[List[float], List[float]]:
    """
    คำนวณ Precision และ Recall สำหรับแต่ละ confidence threshold
    
    Args:
        predictions: List ของ predictions จาก model [{x1, y1, x2, y2, confidence, class}]
        ground_truth: List ของ ground truth boxes [{x1, y1, x2, y2, class}]
        iou_threshold: IoU threshold สำหรับนับว่า match หรือไม่
    
    Returns:
        precisions: List ของ precision values
        recalls: List ของ recall values
    """
    # เรียง predictions ตาม confidence จากมากไปน้อย
    sorted_preds = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    
    # สร้าง confidence thresholds (0.0 ถึง 1.0)
    thresholds = np.linspace(0.0, 1.0, 100)
    
    precisions = []
    recalls = []
    
    for threshold in thresholds:
        # กรอง predictions ที่มี confidence >= threshold
        filtered_preds = [p for p in sorted_preds if p['confidence'] >= threshold]
        
        if len(filtered_preds) == 0:
            precisions.append(1.0)  # ถ้าไม่มี prediction = perfect precision
            recalls.append(0.0)      # แต่ recall = 0
            continue
        
        # คำนวณ TP, FP, FN
        tp = 0  # True Positive
        fp = 0  # False Positive
        matched_gt = set()  # เก็บ index ของ ground truth ที่ match แล้ว
        
        for pred in filtered_preds:
            pred_box = [pred['x1'], pred['y1'], pred['x2'], pred['y2']]
            best_iou = 0
            best_gt_idx = -1
            
            # หา ground truth ที่ match ดีที่สุด
            for gt_idx, gt in enumerate(ground_truth):
                if gt_idx in matched_gt:
                    continue
                
                gt_box = [gt['x1'], gt['y1'], gt['x2'], gt['y2']]
                iou = calculate_iou(pred_box, gt_box)
                
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx
            
            # ถ้า IoU >= threshold = True Positive
            if best_iou >= iou_threshold:
                tp += 1
                matched_gt.add(best_gt_idx)
            else:
                fp += 1
        
        # False Negative = ground truth ที่ไม่ match กับ prediction ใดๆ
        fn = len(ground_truth) - len(matched_gt)
        
        # คำนวณ Precision และ Recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        precisions.append(precision)
        recalls.append(recall)
    
    return precisions, recalls


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """คำนวณ Intersection over Union (IoU) ของ 2 boxes"""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    # หาพื้นที่ intersection
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)
    
    if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
        return 0.0
    
    inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
    
    # หาพื้นที่ union
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0


def plot_precision_recall_curve(precisions: List[float], recalls: List[float],
                                optimal_point: Tuple[float, float] = None,
                                save_path: str = "figures/precision_recall_curve.png"):
    """
    สร้างกราฟ Precision-Recall Curve
    
    Args:
        precisions: List ของ precision values
        recalls: List ของ recall values
        optimal_point: จุดที่เหมาะสมที่สุด (precision, recall) - เช่น (0.962, 0.948)
        save_path: path สำหรับบันทึกรูปภาพ
    """
    # สร้าง figure
    plt.figure(figsize=(10, 8))
    
    # Plot curve
    plt.plot(recalls, precisions, linewidth=2.5, color='#6366f1', label='Precision-Recall Curve')
    
    # Plot optimal point ถ้ามี
    if optimal_point:
        opt_recall, opt_precision = optimal_point
        plt.plot(opt_recall, opt_precision, 'ro', markersize=12, 
                label=f'Optimal Point (P={opt_precision:.1%}, R={opt_recall:.1%})')
        plt.annotate(f'({opt_precision:.1%}, {opt_recall:.1%})',
                    xy=(opt_recall, opt_precision),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
    
    # ตั้งค่าแกนและ labels
    plt.xlabel('Recall', fontsize=14, fontweight='bold')
    plt.ylabel('Precision', fontsize=14, fontweight='bold')
    plt.title('Precision-Recall Curve for License Plate Detection', 
             fontsize=16, fontweight='bold', pad=20)
    
    # ตั้งค่าแกน
    plt.xlim([0, 1.05])
    plt.ylim([0, 1.05])
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='lower left', fontsize=12)
    
    # เพิ่ม grid lines ที่สำคัญ
    plt.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5)
    plt.axvline(x=0.5, color='gray', linestyle=':', alpha=0.5)
    
    # ปรับแต่ง
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved Precision-Recall Curve to: {save_path}")
    
    plt.close()


# ============================================
# 2. สร้างรูปภาพตัวอย่างผลการตรวจจับ
# ============================================

def draw_detection_results(image_path: str, predictions: List[Dict], 
                           ground_truth: List[Dict] = None,
                           iou_threshold: float = 0.5,
                           save_path: str = "figures/detection_examples.png"):
    """
    วาดผลการตรวจจับบนรูปภาพ
    
    Args:
        image_path: path ของรูปภาพ
        predictions: List ของ predictions
        ground_truth: List ของ ground truth (optional)
        iou_threshold: IoU threshold สำหรับกำหนด TP/FP
        save_path: path สำหรับบันทึกรูปภาพ
    """
    # อ่านรูปภาพ
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Cannot read image: {image_path}")
        return
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_draw = img_rgb.copy()
    
    # วาด ground truth (ถ้ามี) - สีฟ้า
    if ground_truth:
        for gt in ground_truth:
            x1, y1, x2, y2 = int(gt['x1']), int(gt['y1']), int(gt['x2']), int(gt['y2'])
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), (0, 255, 255), 2)  # สีฟ้า (Cyan)
            cv2.putText(img_draw, 'GT', (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, (0, 255, 255), 2)
    
    # ตรวจสอบว่า prediction แต่ละตัวเป็น TP หรือ FP
    matched_gt = set()
    
    for pred in predictions:
        pred_box = [pred['x1'], pred['y1'], pred['x2'], pred['y2']]
        x1, y1, x2, y2 = int(pred['x1']), int(pred['y1']), int(pred['x2']), int(pred['y2'])
        conf = pred['confidence']
        
        # หา ground truth ที่ match
        best_iou = 0
        best_gt_idx = -1
        
        if ground_truth:
            for gt_idx, gt in enumerate(ground_truth):
                if gt_idx in matched_gt:
                    continue
                
                gt_box = [gt['x1'], gt['y1'], gt['x2'], gt['y2']]
                iou = calculate_iou(pred_box, gt_box)
                
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx
        
        # กำหนดสีและ label
        if ground_truth and best_iou >= iou_threshold:
            # True Positive - สีเขียว
            color = (0, 255, 0)  # สีเขียว
            label = f'TP: {conf:.2f}'
            matched_gt.add(best_gt_idx)
        elif ground_truth:
            # False Positive - สีแดง
            color = (255, 0, 0)  # สีแดง
            label = f'FP: {conf:.2f}'
        else:
            # ไม่มี ground truth - สีน้ำเงิน
            color = (0, 0, 255)  # สีน้ำเงิน
            label = f'Det: {conf:.2f}'
        
        # วาดกล่อง
        cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 3)
        cv2.putText(img_draw, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, color, 2)
    
    # วาด False Negatives (ground truth ที่ไม่ match) - สีเหลือง
    if ground_truth:
        for gt_idx, gt in enumerate(ground_truth):
            if gt_idx not in matched_gt:
                x1, y1, x2, y2 = int(gt['x1']), int(gt['y1']), int(gt['x2']), int(gt['y2'])
                cv2.rectangle(img_draw, (x1, y1), (x2, y2), (255, 255, 0), 2)  # สีเหลือง
                cv2.putText(img_draw, 'FN', (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (255, 255, 0), 2)
    
    # แสดงผล
    plt.figure(figsize=(12, 8))
    plt.imshow(img_draw)
    plt.axis('off')
    plt.title('Detection Results\n(Green=TP, Red=FP, Yellow=FN, Cyan=GT)', 
             fontsize=14, fontweight='bold', pad=10)
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved detection example to: {save_path}")
    
    plt.close()


def create_detection_examples_grid(image_paths: List[str], 
                                   predictions_list: List[List[Dict]],
                                   ground_truth_list: List[List[Dict]] = None,
                                   titles: List[str] = None,
                                   save_path: str = "figures/detection_examples_grid.png"):
    """
    สร้าง grid ของตัวอย่างผลการตรวจจับ (แถวบน: สำเร็จ, แถวล่าง: ท้าทาย)
    
    Args:
        image_paths: List ของ path รูปภาพ
        predictions_list: List ของ predictions สำหรับแต่ละรูป
        ground_truth_list: List ของ ground truth (optional)
        titles: List ของ titles สำหรับแต่ละรูป
        save_path: path สำหรับบันทึก
    """
    n_images = len(image_paths)
    cols = min(4, n_images)  # แสดงสูงสุด 4 รูปต่อแถว
    rows = (n_images + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4*rows))
    if rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)
    
    for idx, (img_path, preds) in enumerate(zip(image_paths, predictions_list)):
        row = idx // cols
        col = idx % cols
        ax = axes[row, col] if rows > 1 else axes[col]
        
        # อ่านและวาดรูป
        img = cv2.imread(img_path)
        if img is None:
            ax.text(0.5, 0.5, f'Cannot load\n{img_path}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')
            continue
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_draw = img_rgb.copy()
        
        # วาด predictions
        gt_list = ground_truth_list[idx] if ground_truth_list else []
        matched_gt = set()
        
        for pred in preds:
            x1, y1, x2, y2 = int(pred['x1']), int(pred['y1']), int(pred['x2']), int(pred['y2'])
            conf = pred['confidence']
            
            # ตรวจสอบ TP/FP
            is_tp = False
            if gt_list:
                for gt_idx, gt in enumerate(gt_list):
                    if gt_idx in matched_gt:
                        continue
                    iou = calculate_iou([pred['x1'], pred['y1'], pred['x2'], pred['y2']],
                                       [gt['x1'], gt['y1'], gt['x2'], gt['y2']])
                    if iou >= 0.5:
                        is_tp = True
                        matched_gt.add(gt_idx)
                        break
            
            color = (0, 255, 0) if is_tp else (255, 0, 0)  # เขียว=TP, แดง=FP
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img_draw, f'{conf:.2f}', (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # วาด False Negatives
        if gt_list:
            for gt_idx, gt in enumerate(gt_list):
                if gt_idx not in matched_gt:
                    x1, y1, x2, y2 = int(gt['x1']), int(gt['y1']), int(gt['x2']), int(gt['y2'])
                    cv2.rectangle(img_draw, (x1, y1), (x2, y2), (255, 255, 0), 2)  # เหลือง=FN
        
        ax.imshow(img_draw)
        ax.axis('off')
        if titles and idx < len(titles):
            ax.set_title(titles[idx], fontsize=10, fontweight='bold', pad=5)
    
    # ซ่อน axes ที่เหลือ
    for idx in range(n_images, rows * cols):
        row = idx // cols
        col = idx % cols
        ax = axes[row, col] if rows > 1 else axes[col]
        ax.axis('off')
    
    plt.suptitle('Detection Examples\n(Green=TP, Red=FP, Yellow=FN)', 
                fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved detection examples grid to: {save_path}")
    
    plt.close()


# ============================================
# 3. ตัวอย่างการใช้งาน
# ============================================

if __name__ == "__main__":
    print("📊 Creating figures for research paper...")
    
    # ตัวอย่างข้อมูล (ควรแทนที่ด้วยข้อมูลจริง)
    # 1. สร้าง Precision-Recall Curve
    print("\n1. Creating Precision-Recall Curve...")
    
    # ตัวอย่าง: สร้างข้อมูลจำลอง
    # ในกรณีจริง ควรใช้ข้อมูลจาก validation/test set
    sample_precisions = np.linspace(1.0, 0.85, 100)
    sample_recalls = np.linspace(0.0, 1.0, 100)
    
    # Plot curve
    plot_precision_recall_curve(
        precisions=sample_precisions,
        recalls=sample_recalls,
        optimal_point=(0.948, 0.962),  # (recall, precision)
        save_path="figures/6.1.1_precision_recall_curve.png"
    )
    
    # 2. สร้างตัวอย่างผลการตรวจจับ
    print("\n2. Creating detection examples...")
    print("   (Note: ต้องมีรูปภาพและข้อมูล predictions/ground truth จริง)")
    
    # ตัวอย่างการใช้งาน (ต้องมีรูปภาพจริง)
    # draw_detection_results(
    #     image_path="test_images/example1.jpg",
    #     predictions=[
    #         {"x1": 100, "y1": 100, "x2": 300, "y2": 200, "confidence": 0.95}
    #     ],
    #     ground_truth=[
    #         {"x1": 105, "y1": 105, "x2": 295, "y2": 195}
    #     ],
    #     save_path="figures/6.1.2_detection_examples.png"
    # )
    
    print("\n✅ Done! Check the 'figures/' directory for generated images.")
    print("\n📝 Next steps:")
    print("   1. รัน evaluation บน test set เพื่อได้ precision/recall จริง")
    print("   2. ใช้รูปภาพจริงจาก test set สำหรับ detection examples")
    print("   3. ปรับแต่งกราฟให้สวยงามตามต้องการ")

