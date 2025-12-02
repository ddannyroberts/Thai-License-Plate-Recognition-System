"""
สร้างกราฟเส้นแสดง Accuracy เทียบกับสภาพแสง (6.6.1)
แสดง: Detection accuracy และ Character recognition accuracy ในสภาพแสงต่างๆ
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ตั้งค่า font
plt.rcParams['font.size'] = 12

def create_lighting_accuracy_chart(save_path: str = "figures/6.6.1_lighting_accuracy.png"):
    """
    สร้างกราฟเส้นแสดง Accuracy เทียบกับสภาพแสง
    """
    # สภาพแสงต่างๆ (เรียงจากดีไปแย่)
    lighting_conditions = [
        "Bright\nSunlight",
        "Normal\nSunlight",
        "Cloudy/\nOvercast",
        "Indoor\nLighting",
        "Low\nLight",
        "Very Low\nLight"
    ]
    
    # ข้อมูลจำลองตามแนวโน้มจริง:
    # - Detection accuracy: สูงในแสงดี, ลดลงในแสงน้อย
    # - Recognition accuracy: สูงในแสงดี, ลดลงในแสงน้อย (แต่ลดลงมากกว่า detection)
    
    # Detection accuracy (เส้นสีน้ำเงิน)
    detection_accuracy = [96.5, 95.2, 93.8, 91.5, 87.3, 82.1]
    
    # Character recognition accuracy (เส้นสีแดง)
    recognition_accuracy = [96.8, 95.5, 93.2, 90.1, 84.7, 78.5]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot lines
    line1 = ax.plot(lighting_conditions, detection_accuracy, 
                   marker='o', linewidth=3, markersize=10,
                   color='#3b82f6', label='Detection Accuracy', 
                   markerfacecolor='white', markeredgewidth=2, markeredgecolor='#3b82f6')
    
    line2 = ax.plot(lighting_conditions, recognition_accuracy, 
                   marker='s', linewidth=3, markersize=10,
                   color='#ef4444', label='Character Recognition Accuracy',
                   markerfacecolor='white', markeredgewidth=2, markeredgecolor='#ef4444')
    
    # เพิ่มค่าเปอร์เซ็นต์บนจุด
    for i, (det, rec) in enumerate(zip(detection_accuracy, recognition_accuracy)):
        # Detection values (ด้านบน)
        ax.text(i, det + 1.5, f'{det:.1f}%', 
               ha='center', va='bottom', fontsize=10, fontweight='bold',
               color='#3b82f6', bbox=dict(boxstyle='round,pad=0.3', 
                                         facecolor='white', alpha=0.8, edgecolor='#3b82f6'))
        # Recognition values (ด้านล่าง)
        ax.text(i, rec - 1.5, f'{rec:.1f}%', 
               ha='center', va='top', fontsize=10, fontweight='bold',
               color='#ef4444', bbox=dict(boxstyle='round,pad=0.3', 
                                          facecolor='white', alpha=0.8, edgecolor='#ef4444'))
    
    # ตั้งค่าแกน
    ax.set_xlabel('Lighting Conditions', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Accuracy vs. Lighting Conditions', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim([70, 100])
    ax.set_xticks(range(len(lighting_conditions)))
    ax.set_xticklabels(lighting_conditions, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.legend(loc='lower left', fontsize=12, framealpha=0.9)
    
    # เพิ่ม annotation
    ax.text(0.02, 0.98, 'Note: Accuracy decreases as lighting conditions worsen', 
           transform=ax.transAxes, fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved lighting accuracy chart to: {save_path}")
    
    plt.close()


def create_lighting_accuracy_chart_detailed(save_path: str = "figures/6.6.1_lighting_accuracy_detailed.png"):
    """
    สร้างกราฟเส้นแบบละเอียดพร้อม error bars
    """
    # สภาพแสงต่างๆ
    lighting_conditions = [
        "Bright\nSunlight",
        "Normal\nSunlight",
        "Cloudy/\nOvercast",
        "Indoor\nLighting",
        "Low\nLight",
        "Very Low\nLight"
    ]
    
    # Detection accuracy (mean ± std)
    detection_accuracy = [96.5, 95.2, 93.8, 91.5, 87.3, 82.1]
    detection_std = [1.2, 1.5, 2.1, 2.8, 3.5, 4.2]
    
    # Character recognition accuracy (mean ± std)
    recognition_accuracy = [96.8, 95.5, 93.2, 90.1, 84.7, 78.5]
    recognition_std = [1.0, 1.3, 2.0, 2.9, 3.8, 4.5]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(lighting_conditions))
    
    # Plot lines with error bars
    line1 = ax.errorbar(x, detection_accuracy, yerr=detection_std,
                       marker='o', linewidth=3, markersize=10,
                       color='#3b82f6', label='Detection Accuracy',
                       markerfacecolor='white', markeredgewidth=2, 
                       markeredgecolor='#3b82f6', capsize=5, capthick=2,
                       elinewidth=2, alpha=0.8)
    
    line2 = ax.errorbar(x, recognition_accuracy, yerr=recognition_std,
                       marker='s', linewidth=3, markersize=10,
                       color='#ef4444', label='Character Recognition Accuracy',
                       markerfacecolor='white', markeredgewidth=2,
                       markeredgecolor='#ef4444', capsize=5, capthick=2,
                       elinewidth=2, alpha=0.8)
    
    # ตั้งค่าแกน
    ax.set_xlabel('Lighting Conditions', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Accuracy vs. Lighting Conditions (with Error Bars)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim([70, 100])
    ax.set_xticks(x)
    ax.set_xticklabels(lighting_conditions, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.legend(loc='lower left', fontsize=12, framealpha=0.9)
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved detailed lighting accuracy chart to: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    print("📊 Creating Lighting Accuracy Chart (6.6.1)\n")
    
    # สร้างกราฟพื้นฐาน
    print("1. Creating basic lighting accuracy chart...")
    create_lighting_accuracy_chart()
    
    # สร้างกราฟแบบละเอียด
    print("\n2. Creating detailed lighting accuracy chart...")
    create_lighting_accuracy_chart_detailed()
    
    print("\n✅ Done!")
    print("\n📝 Note:")
    print("   - Data is simulated based on typical performance trends")
    print("   - Detection accuracy (blue line): Higher in good lighting")
    print("   - Recognition accuracy (red line): More sensitive to lighting")
    print("   - Both decrease as lighting conditions worsen")
    print("   - Charts saved to:")
    print("     * figures/6.6.1_lighting_accuracy.png")
    print("     * figures/6.6.1_lighting_accuracy_detailed.png")

