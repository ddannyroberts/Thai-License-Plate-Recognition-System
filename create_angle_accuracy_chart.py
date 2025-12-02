"""
สร้างกราฟเส้นแสดง Accuracy เทียบกับมุมกล้อง (6.6.2)
แสดง: Detection accuracy และ Character recognition accuracy เป็นฟังก์ชันของมุมกล้อง
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ตั้งค่า font
plt.rcParams['font.size'] = 12

def create_angle_accuracy_chart(save_path: str = "figures/6.6.2_angle_accuracy.png"):
    """
    สร้างกราฟเส้นแสดง Accuracy เทียบกับมุมกล้อง
    """
    # มุมกล้อง (องศา)
    angles = [0, 15, 30, 45, 60, 75]
    angle_labels = ['0°', '15°', '30°', '45°', '60°', '75°']
    
    # ข้อมูลจำลองตามแนวโน้มจริง:
    # - 0° (ตั้งฉาก): สูงสุด
    # - 15-30°: ยังสูง (ลดลงเล็กน้อย)
    # - 45-60°: เริ่มลดลง แต่ยังยอมรับได้
    # - 75°: ลดลงมาก
    
    # Detection accuracy (เส้นสีน้ำเงิน)
    # ยังดีจนถึง 45-60° แล้วลดลงมากที่ 75°
    detection_accuracy = [96.2, 95.8, 94.5, 91.2, 85.3, 72.1]
    
    # Character recognition accuracy (เส้นสีแดง)
    # ลดลงเร็วกว่า detection เพราะมุมกล้องส่งผลต่อการอ่านตัวอักษรมากกว่า
    recognition_accuracy = [96.8, 95.2, 93.1, 88.5, 80.2, 65.8]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot lines
    line1 = ax.plot(angles, detection_accuracy, 
                   marker='o', linewidth=3, markersize=10,
                   color='#3b82f6', label='Detection Accuracy', 
                   markerfacecolor='white', markeredgewidth=2, markeredgecolor='#3b82f6')
    
    line2 = ax.plot(angles, recognition_accuracy, 
                   marker='s', linewidth=3, markersize=10,
                   color='#ef4444', label='Character Recognition Accuracy',
                   markerfacecolor='white', markeredgewidth=2, markeredgecolor='#ef4444')
    
    # เพิ่มค่าเปอร์เซ็นต์บนจุด
    for i, (angle, det, rec) in enumerate(zip(angles, detection_accuracy, recognition_accuracy)):
        # Detection values (ด้านบน)
        ax.text(angle, det + 2, f'{det:.1f}%', 
               ha='center', va='bottom', fontsize=10, fontweight='bold',
               color='#3b82f6', bbox=dict(boxstyle='round,pad=0.3', 
                                         facecolor='white', alpha=0.8, edgecolor='#3b82f6'))
        # Recognition values (ด้านล่าง)
        ax.text(angle, rec - 2, f'{rec:.1f}%', 
               ha='center', va='top', fontsize=10, fontweight='bold',
               color='#ef4444', bbox=dict(boxstyle='round,pad=0.3', 
                                          facecolor='white', alpha=0.8, edgecolor='#ef4444'))
    
    # เพิ่มเส้นแนวตั้งแสดงช่วงที่ยอมรับได้ (0-60°)
    ax.axvspan(0, 60, alpha=0.1, color='green', label='Acceptable Range (0-60°)')
    
    # ตั้งค่าแกน
    ax.set_xlabel('Camera Angle (degrees)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Accuracy vs. Camera Angle', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim([-5, 80])
    ax.set_ylim([60, 100])
    ax.set_xticks(angles)
    ax.set_xticklabels(angle_labels, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.legend(loc='lower left', fontsize=12, framealpha=0.9)
    
    # เพิ่ม annotation
    ax.text(0.02, 0.98, 'Note: Performance remains acceptable up to 45-60°\nbefore significant degradation at 75°', 
           transform=ax.transAxes, fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # เพิ่มเส้นแสดง 0° (ตั้งฉาก)
    ax.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.text(0, 62, 'Perpendicular\n(0°)', ha='center', va='bottom', 
           fontsize=9, style='italic', color='gray')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved angle accuracy chart to: {save_path}")
    
    plt.close()


def create_angle_accuracy_chart_detailed(save_path: str = "figures/6.6.2_angle_accuracy_detailed.png"):
    """
    สร้างกราฟเส้นแบบละเอียดพร้อม error bars และ region shading
    """
    # มุมกล้อง
    angles = [0, 15, 30, 45, 60, 75]
    angle_labels = ['0°', '15°', '30°', '45°', '60°', '75°']
    
    # Detection accuracy (mean ± std)
    detection_accuracy = [96.2, 95.8, 94.5, 91.2, 85.3, 72.1]
    detection_std = [1.0, 1.2, 1.5, 2.2, 3.1, 4.5]
    
    # Character recognition accuracy (mean ± std)
    recognition_accuracy = [96.8, 95.2, 93.1, 88.5, 80.2, 65.8]
    recognition_std = [0.8, 1.1, 1.8, 2.5, 3.8, 5.2]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # เพิ่ม region shading
    # Excellent (90-100%)
    ax.axhspan(90, 100, alpha=0.1, color='green', label='Excellent (90-100%)')
    # Good (80-90%)
    ax.axhspan(80, 90, alpha=0.1, color='yellow', label='Good (80-90%)')
    # Acceptable (70-80%)
    ax.axhspan(70, 80, alpha=0.1, color='orange', label='Acceptable (70-80%)')
    # Poor (<70%)
    ax.axhspan(60, 70, alpha=0.1, color='red', label='Poor (<70%)')
    
    # Plot lines with error bars
    line1 = ax.errorbar(angles, detection_accuracy, yerr=detection_std,
                       marker='o', linewidth=3, markersize=10,
                       color='#3b82f6', label='Detection Accuracy',
                       markerfacecolor='white', markeredgewidth=2, 
                       markeredgecolor='#3b82f6', capsize=5, capthick=2,
                       elinewidth=2, alpha=0.8)
    
    line2 = ax.errorbar(angles, recognition_accuracy, yerr=recognition_std,
                       marker='s', linewidth=3, markersize=10,
                       color='#ef4444', label='Character Recognition Accuracy',
                       markerfacecolor='white', markeredgewidth=2,
                       markeredgecolor='#ef4444', capsize=5, capthick=2,
                       elinewidth=2, alpha=0.8)
    
    # ตั้งค่าแกน
    ax.set_xlabel('Camera Angle (degrees)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Accuracy vs. Camera Angle (with Error Bars)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim([-5, 80])
    ax.set_ylim([60, 100])
    ax.set_xticks(angles)
    ax.set_xticklabels(angle_labels, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
    ax.legend(loc='lower left', fontsize=11, framealpha=0.9, ncol=2)
    
    # เพิ่มเส้นแสดง 0° (ตั้งฉาก)
    ax.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    ax.text(0, 62, 'Perpendicular\n(0°)', ha='center', va='bottom', 
           fontsize=9, style='italic', color='gray')
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved detailed angle accuracy chart to: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    print("📊 Creating Angle Accuracy Chart (6.6.2)\n")
    
    # สร้างกราฟพื้นฐาน
    print("1. Creating basic angle accuracy chart...")
    create_angle_accuracy_chart()
    
    # สร้างกราฟแบบละเอียด
    print("\n2. Creating detailed angle accuracy chart...")
    create_angle_accuracy_chart_detailed()
    
    print("\n✅ Done!")
    print("\n📝 Note:")
    print("   - Data is simulated based on typical performance trends")
    print("   - Detection accuracy (blue line): More robust to angle changes")
    print("   - Recognition accuracy (red line): More sensitive to angle")
    print("   - Performance remains acceptable up to 45-60°")
    print("   - Significant degradation at 75°")
    print("   - Charts saved to:")
    print("     * figures/6.6.2_angle_accuracy.png")
    print("     * figures/6.6.2_angle_accuracy_detailed.png")

