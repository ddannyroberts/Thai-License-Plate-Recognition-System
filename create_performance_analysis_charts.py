"""
สร้างกราฟและรูปภาพสำหรับการวิเคราะห์ประสิทธิภาพ (6.7.1, 6.7.2, 6.7.3)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ตั้งค่า font
plt.rcParams['font.size'] = 12

# ============================================
# 6.7.1: Processing Time Distribution Pie Chart
# ============================================

def create_processing_time_pie_chart(save_path: str = "figures/6.7.1_processing_time_distribution.png"):
    """
    สร้างกราฟวงกลมแสดงสัดส่วนเวลาในการประมวลผลแต่ละขั้นตอน
    """
    # ขั้นตอนการประมวลผล
    stages = [
        "Image\nPreprocessing",
        "Model Inference\n(Detection)",
        "Model Inference\n(Recognition)",
        "OCR\nOperations",
        "Database/\nFormatting"
    ]
    
    # เปอร์เซ็นต์เวลาที่ใช้ (จาก paper)
    percentages = [15, 30, 30, 20, 5]
    colors = ['#3b82f6', '#10b981', '#10b981', '#f59e0b', '#8b5cf6']
    explode = (0, 0.1, 0.1, 0, 0)  # เน้น model inference
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 8))
    
    wedges, texts, autotexts = ax.pie(
        percentages,
        explode=explode,
        labels=stages,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 11, 'fontweight': 'bold'},
        shadow=True
    )
    
    # ปรับแต่ง autopct
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)
    
    ax.set_title('Processing Time Distribution by Stage', 
                fontsize=16, fontweight='bold', pad=20)
    
    # เพิ่ม annotation
    ax.text(0, -1.3, 'Note: Model inference (detection + recognition) is the main bottleneck (60%)', 
           ha='center', fontsize=11, style='italic',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved processing time pie chart to: {save_path}")
    
    plt.close()


# ============================================
# 6.7.2: Memory Usage Over Time
# ============================================

def create_memory_usage_chart(save_path: str = "figures/6.7.2_memory_usage_over_time.png"):
    """
    สร้างกราฟเส้นแสดงการใช้หน่วยความจำตามเวลา
    """
    # สร้างข้อมูลจำลอง
    # Baseline: 200 MB
    # Model loading: เพิ่มขึ้นเป็น 800 MB
    # Processing: 500 MB per image
    # Video buffering: 1-2 GB
    
    time_points = np.linspace(0, 100, 200)  # 100 วินาที, 200 จุด
    memory_usage = np.zeros_like(time_points)
    
    # Baseline
    memory_usage[:] = 200
    
    # Model loading (0-5 seconds)
    model_load_start = 0
    model_load_end = 5
    load_mask = (time_points >= model_load_start) & (time_points <= model_load_end)
    memory_usage[load_mask] = 200 + (time_points[load_mask] - model_load_start) * (800 - 200) / (model_load_end - model_load_start)
    
    # After model loading (5-20 seconds) - processing images
    processing_start = 5
    processing_end = 20
    processing_mask = (time_points >= processing_start) & (time_points <= processing_end)
    memory_usage[processing_mask] = 800 + 100 * np.sin(np.linspace(0, 2*np.pi, np.sum(processing_mask)))  # Fluctuation
    
    # Single image processing (20-25 seconds)
    single_image_start = 20
    single_image_end = 25
    single_mask = (time_points >= single_image_start) & (time_points <= single_image_end)
    memory_usage[single_mask] = 500 + 50 * np.sin(np.linspace(0, np.pi, np.sum(single_mask)))
    
    # Video processing with buffering (25-60 seconds)
    video_start = 25
    video_end = 60
    video_mask = (time_points >= video_start) & (time_points <= video_end)
    memory_usage[video_mask] = 1200 + 400 * np.sin(np.linspace(0, 4*np.pi, np.sum(video_mask)))
    
    # Idle (60-100 seconds)
    idle_mask = time_points >= 60
    memory_usage[idle_mask] = 800
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot memory usage
    ax.plot(time_points, memory_usage, linewidth=2.5, color='#3b82f6', label='Memory Usage')
    
    # เพิ่ม region shading
    ax.axhspan(0, 200, alpha=0.1, color='green', label='Baseline (200 MB)')
    ax.axhspan(450, 550, alpha=0.1, color='yellow', label='Single Image Processing (500 MB)')
    ax.axhspan(1000, 2000, alpha=0.1, color='orange', label='Video Buffering (1-2 GB)')
    
    # เพิ่มเส้นแนวนอนแสดงระดับสำคัญ
    ax.axhline(200, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Baseline')
    ax.axhline(500, color='yellow', linestyle='--', linewidth=2, alpha=0.7, label='Single Image')
    ax.axhline(1200, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Video (avg)')
    ax.axhline(2000, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Video (peak)')
    
    # เพิ่ม annotation
    ax.annotate('Model Loading', xy=(2.5, 500), xytext=(10, 600),
               arrowprops=dict(arrowstyle='->', color='red', lw=2),
               fontsize=11, fontweight='bold', color='red',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    ax.annotate('Single Image\nProcessing', xy=(22.5, 500), xytext=(30, 400),
               arrowprops=dict(arrowstyle='->', color='blue', lw=2),
               fontsize=11, fontweight='bold', color='blue',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    ax.annotate('Video Processing\nwith Buffering', xy=(42.5, 1400), xytext=(50, 1800),
               arrowprops=dict(arrowstyle='->', color='orange', lw=2),
               fontsize=11, fontweight='bold', color='orange',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    # ตั้งค่าแกน
    ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Memory Usage (MB)', fontsize=14, fontweight='bold')
    ax.set_title('Memory Usage Over Time During Processing', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim([0, 2200])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9, ncol=2)
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved memory usage chart to: {save_path}")
    
    plt.close()


# ============================================
# 6.7.3: Processing Throughput Analysis
# ============================================

def create_throughput_chart(save_path: str = "figures/6.7.3_processing_throughput.png"):
    """
    สร้างกราฟแท่งหรือกราฟเส้นแสดงการวิเคราะห์ Processing Throughput
    """
    # Hardware configurations
    hardware_configs = [
        "MacBook Air\nM1",
        "Desktop\nCPU",
        "GPU-\nAccelerated",
        "Multi-worker\nParallel"
    ]
    
    # Throughput (images per minute)
    throughput = [12, 18, 45, 60]  # ภาพ/นาที
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # สร้างกราฟแท่ง
    bars = ax.bar(hardware_configs, throughput, color=colors, 
                 edgecolor='black', linewidth=2, alpha=0.8)
    
    # เพิ่มค่าเปอร์เซ็นต์บนแท่ง
    for bar, value in zip(bars, throughput):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
               f'{value} img/min', ha='center', va='bottom',
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', 
                        facecolor='white', alpha=0.8, edgecolor='black'))
    
    # เพิ่มเส้นแสดง improvement
    for i in range(len(throughput) - 1):
        improvement = ((throughput[i+1] - throughput[i]) / throughput[i]) * 100
        ax.annotate(f'+{improvement:.0f}%', 
                   xy=(i+0.5, (throughput[i] + throughput[i+1])/2),
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color='green', bbox=dict(boxstyle='round', 
                                           facecolor='lightgreen', alpha=0.7))
        ax.plot([i, i+1], [throughput[i], throughput[i+1]], 
               'g--', linewidth=2, alpha=0.5)
    
    # ตั้งค่าแกน
    ax.set_xlabel('Hardware Configuration', fontsize=14, fontweight='bold')
    ax.set_ylabel('Throughput (images per minute)', fontsize=14, fontweight='bold')
    ax.set_title('Processing Throughput by Hardware Configuration', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim([0, max(throughput) * 1.2])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # เพิ่ม annotation
    ax.text(0.02, 0.98, 'Note: GPU acceleration and parallel processing\nsignificantly improve throughput', 
           transform=ax.transAxes, fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved throughput chart to: {save_path}")
    
    plt.close()


def create_throughput_line_chart(save_path: str = "figures/6.7.3_processing_throughput_line.png"):
    """
    สร้างกราฟเส้นแสดงการวิเคราะห์ Processing Throughput
    """
    # Hardware configurations
    hardware_configs = [
        "MacBook Air\nM1",
        "Desktop\nCPU",
        "GPU-\nAccelerated",
        "Multi-worker\nParallel"
    ]
    
    # Throughput (images per minute)
    throughput = [12, 18, 45, 60]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot line
    line = ax.plot(hardware_configs, throughput, 
                  marker='o', linewidth=3, markersize=12,
                  color='#3b82f6', markerfacecolor='white', 
                  markeredgewidth=3, markeredgecolor='#3b82f6')
    
    # Fill area under curve
    ax.fill_between(range(len(hardware_configs)), throughput, 
                    alpha=0.3, color='#3b82f6')
    
    # เพิ่มค่าเปอร์เซ็นต์
    for i, value in enumerate(throughput):
        ax.text(i, value + 3, f'{value} img/min', 
               ha='center', va='bottom', fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', 
                        facecolor='white', alpha=0.8, edgecolor='#3b82f6'))
    
    # ตั้งค่าแกน
    ax.set_xlabel('Hardware Configuration', fontsize=14, fontweight='bold')
    ax.set_ylabel('Throughput (images per minute)', fontsize=14, fontweight='bold')
    ax.set_title('Processing Throughput by Hardware Configuration', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim([0, max(throughput) * 1.2])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved throughput line chart to: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    print("📊 Creating Performance Analysis Charts (6.7.1, 6.7.2, 6.7.3)\n")
    
    # 6.7.1: Processing Time Distribution
    print("1. Creating processing time distribution pie chart (6.7.1)...")
    create_processing_time_pie_chart()
    
    # 6.7.2: Memory Usage
    print("\n2. Creating memory usage chart (6.7.2)...")
    create_memory_usage_chart()
    
    # 6.7.3: Throughput Analysis
    print("\n3. Creating throughput analysis chart (6.7.3)...")
    create_throughput_chart()
    create_throughput_line_chart()
    
    print("\n✅ Done!")
    print("\n📝 Note:")
    print("   - 6.7.1: Pie chart shows model inference is the main bottleneck (60%)")
    print("   - 6.7.2: Memory usage chart shows baseline, model loading, and processing phases")
    print("   - 6.7.3: Throughput chart shows performance improvements with hardware upgrades")
    print("   - Charts saved to:")
    print("     * figures/6.7.1_processing_time_distribution.png")
    print("     * figures/6.7.2_memory_usage_over_time.png")
    print("     * figures/6.7.3_processing_throughput.png")
    print("     * figures/6.7.3_processing_throughput_line.png")

