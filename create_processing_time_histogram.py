"""
สร้าง Histogram แสดงการกระจายเวลาในการประมวลผล (6.3.2)
แสดง: detection, character recognition, OCR, database operations
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ตั้งค่า font
plt.rcParams['font.size'] = 11

def generate_processing_times(n_samples: int = 100):
    """
    สร้างข้อมูลเวลาในการประมวลผลจำลอง
    ตามข้อมูลจาก paper: 2-5 วินาที/รูป
    """
    np.random.seed(42)  # สำหรับ reproducibility
    
    # สร้างข้อมูลจำลองตามการกระจายจริง
    # Detection: 0.5-1.5 วินาที (เฉลี่ย ~0.8s)
    detection_times = np.random.normal(0.8, 0.2, n_samples)
    detection_times = np.clip(detection_times, 0.3, 2.0)
    
    # Character Recognition: 0.8-2.0 วินาที (เฉลี่ย ~1.2s)
    recognition_times = np.random.normal(1.2, 0.3, n_samples)
    recognition_times = np.clip(recognition_times, 0.5, 2.5)
    
    # OCR: 0.3-1.0 วินาที (เฉลี่ย ~0.5s)
    ocr_times = np.random.normal(0.5, 0.15, n_samples)
    ocr_times = np.clip(ocr_times, 0.2, 1.2)
    
    # Database Operations: 0.05-0.3 วินาที (เฉลี่ย ~0.1s)
    db_times = np.random.normal(0.1, 0.05, n_samples)
    db_times = np.clip(db_times, 0.02, 0.4)
    
    # Total time (ควรอยู่ระหว่าง 2-5 วินาที)
    total_times = detection_times + recognition_times + ocr_times + db_times
    
    return {
        'detection': detection_times,
        'recognition': recognition_times,
        'ocr': ocr_times,
        'database': db_times,
        'total': total_times
    }


def create_histogram_separate_stages(times: dict, save_path: str = "figures/6.3.2_processing_time_histogram_separate.png"):
    """
    สร้าง histogram แยกตามขั้นตอน
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Processing Time Distribution by Stage', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    stages = [
        ('detection', 'Detection', axes[0, 0], '#3b82f6'),
        ('recognition', 'Character Recognition', axes[0, 1], '#10b981'),
        ('ocr', 'OCR', axes[1, 0], '#f59e0b'),
        ('database', 'Database Operations', axes[1, 1], '#8b5cf6')
    ]
    
    for stage_key, stage_name, ax, color in stages:
        data = times[stage_key]
        mean_time = np.mean(data)
        
        # สร้าง histogram
        n, bins, patches = ax.hist(data, bins=20, color=color, alpha=0.7, 
                                  edgecolor='black', linewidth=1)
        
        # เส้นเฉลี่ย
        ax.axvline(mean_time, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_time:.2f}s')
        
        # ตั้งค่า
        ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title(f'{stage_name}', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved separate histograms to: {save_path}")
    
    plt.close()


def create_histogram_overlay(times: dict, save_path: str = "figures/6.3.2_processing_time_histogram_overlay.png"):
    """
    สร้าง histogram ซ้อนทับกัน
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    stages = [
        ('detection', 'Detection', '#3b82f6', 0.6),
        ('recognition', 'Character Recognition', '#10b981', 0.6),
        ('ocr', 'OCR', '#f59e0b', 0.6),
        ('database', 'Database Operations', '#8b5cf6', 0.6)
    ]
    
    # สร้าง histogram ซ้อนทับ
    for stage_key, stage_name, color, alpha in stages:
        data = times[stage_key]
        mean_time = np.mean(data)
        
        ax.hist(data, bins=20, label=f'{stage_name} (mean: {mean_time:.2f}s)', 
               color=color, alpha=alpha, edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=14, fontweight='bold')
    ax.set_title('Processing Time Distribution by Stage (Overlay)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved overlay histogram to: {save_path}")
    
    plt.close()


def create_histogram_stacked(times: dict, save_path: str = "figures/6.3.2_processing_time_histogram_stacked.png"):
    """
    สร้าง histogram แบบ stacked
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # สร้าง bins ร่วม
    all_times = np.concatenate([
        times['detection'],
        times['recognition'],
        times['ocr'],
        times['database']
    ])
    
    bins = np.linspace(0, max(all_times) * 1.1, 25)
    
    # สร้าง histogram แบบ stacked
    detection_hist, _ = np.histogram(times['detection'], bins=bins)
    recognition_hist, _ = np.histogram(times['recognition'], bins=bins)
    ocr_hist, _ = np.histogram(times['ocr'], bins=bins)
    db_hist, _ = np.histogram(times['database'], bins=bins)
    
    # Plot stacked
    ax.bar(bins[:-1], detection_hist, width=bins[1]-bins[0], 
          label='Detection', color='#3b82f6', alpha=0.8, edgecolor='black')
    ax.bar(bins[:-1], recognition_hist, width=bins[1]-bins[0], 
          bottom=detection_hist, label='Character Recognition', 
          color='#10b981', alpha=0.8, edgecolor='black')
    ax.bar(bins[:-1], ocr_hist, width=bins[1]-bins[0], 
          bottom=detection_hist + recognition_hist, label='OCR', 
          color='#f59e0b', alpha=0.8, edgecolor='black')
    ax.bar(bins[:-1], db_hist, width=bins[1]-bins[0], 
          bottom=detection_hist + recognition_hist + ocr_hist, 
          label='Database Operations', color='#8b5cf6', alpha=0.8, edgecolor='black')
    
    # เส้นเฉลี่ย
    mean_detection = np.mean(times['detection'])
    mean_recognition = np.mean(times['recognition'])
    mean_ocr = np.mean(times['ocr'])
    mean_db = np.mean(times['database'])
    
    ax.axvline(mean_detection, color='#3b82f6', linestyle='--', linewidth=2, alpha=0.7)
    ax.axvline(mean_recognition, color='#10b981', linestyle='--', linewidth=2, alpha=0.7)
    ax.axvline(mean_ocr, color='#f59e0b', linestyle='--', linewidth=2, alpha=0.7)
    ax.axvline(mean_db, color='#8b5cf6', linestyle='--', linewidth=2, alpha=0.7)
    
    ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=14, fontweight='bold')
    ax.set_title('Processing Time Distribution by Stage (Stacked)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved stacked histogram to: {save_path}")
    
    plt.close()


def create_total_time_histogram(times: dict, save_path: str = "figures/6.3.2_processing_time_total.png"):
    """
    สร้าง histogram เวลารวม
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    total_times = times['total']
    mean_total = np.mean(total_times)
    
    # Histogram
    n, bins, patches = ax.hist(total_times, bins=25, color='#6366f1', 
                               alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # เส้นเฉลี่ย
    ax.axvline(mean_total, color='red', linestyle='--', linewidth=3, 
              label=f'Mean: {mean_total:.2f}s')
    
    # เส้น median
    median_total = np.median(total_times)
    ax.axvline(median_total, color='orange', linestyle='--', linewidth=2, 
              label=f'Median: {median_total:.2f}s')
    
    ax.set_xlabel('Total Processing Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=14, fontweight='bold')
    ax.set_title('Total Processing Time Distribution per Image', 
                fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # เพิ่มสถิติ
    stats_text = f'Mean: {mean_total:.2f}s | Median: {median_total:.2f}s | Std: {np.std(total_times):.2f}s'
    ax.text(0.5, 0.95, stats_text, transform=ax.transAxes, 
           ha='center', va='top', fontsize=11, 
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved total time histogram to: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    print("📊 Creating Processing Time Histograms (6.3.2)\n")
    
    # สร้างข้อมูลจำลอง
    print("1. Generating processing time data...")
    times = generate_processing_times(n_samples=100)
    
    print(f"   - Detection: {np.mean(times['detection']):.2f}s (avg)")
    print(f"   - Recognition: {np.mean(times['recognition']):.2f}s (avg)")
    print(f"   - OCR: {np.mean(times['ocr']):.2f}s (avg)")
    print(f"   - Database: {np.mean(times['database']):.2f}s (avg)")
    print(f"   - Total: {np.mean(times['total']):.2f}s (avg)")
    
    # สร้างกราฟ
    print("\n2. Creating histograms...")
    create_histogram_separate_stages(times)
    create_histogram_overlay(times)
    create_histogram_stacked(times)
    create_total_time_histogram(times)
    
    print("\n✅ Done!")
    print("\n📝 Note:")
    print("   - Data is simulated based on paper: 2-5 seconds per image")
    print("   - Four chart types created:")
    print("     * Separate histograms: figures/6.3.2_processing_time_histogram_separate.png")
    print("     * Overlay histogram: figures/6.3.2_processing_time_histogram_overlay.png")
    print("     * Stacked histogram: figures/6.3.2_processing_time_histogram_stacked.png")
    print("     * Total time histogram: figures/6.3.2_processing_time_total.png")

