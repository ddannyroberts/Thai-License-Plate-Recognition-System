"""
สร้างกราฟแสดงสัดส่วนผลลัพธ์ End-to-End (6.3.1)
แสดง: การจดจำที่ถูกต้อง, การจดจำบางส่วน, การตรวจจับได้แต่จดจำล้มเหลว, ล้มเหลวทั้งหมด
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ตั้งค่า font
plt.rcParams['font.size'] = 12

def create_pie_chart(save_path: str = "figures/6.3.1_end_to_end_results_pie.png"):
    """
    สร้างกราฟวงกลมแสดงสัดส่วนผลลัพธ์
    """
    # ข้อมูลจาก paper Section 6.3
    labels = [
        "Fully Correct\nRecognition",
        "Partial\nRecognition",
        "Detection Success\nRecognition Failed",
        "Complete\nFailure"
    ]
    
    # ข้อมูลจาก paper
    sizes = [87.4, 8.2, 3.1, 1.3]
    colors = ['#10b981', '#f59e0b', '#ef4444', '#6b7280']  # เขียว, ส้ม, แดง, เทา
    explode = (0.05, 0, 0, 0)  # เน้นส่วนแรก
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(10, 8))
    
    wedges, texts, autotexts = ax.pie(
        sizes,
        explode=explode,
        labels=labels,
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
    
    ax.set_title('End-to-End System Results Distribution', 
                fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved pie chart to: {save_path}")
    
    plt.close()


def create_stacked_bar_chart(save_path: str = "figures/6.3.1_end_to_end_results_bar.png"):
    """
    สร้างกราฟแท่งซ้อนแสดงสัดส่วนผลลัพธ์
    """
    # ข้อมูลจาก paper
    categories = ["End-to-End Results"]
    fully_correct = [87.4]
    partial = [8.2]
    detection_only = [3.1]
    complete_failure = [1.3]
    
    colors = ['#10b981', '#f59e0b', '#ef4444', '#6b7280']
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # สร้าง stacked bar
    p1 = ax.bar(categories, fully_correct, label='Fully Correct (87.4%)', 
                color=colors[0], edgecolor='black', linewidth=1.5)
    p2 = ax.bar(categories, partial, bottom=fully_correct, 
                label='Partial Recognition (8.2%)', 
                color=colors[1], edgecolor='black', linewidth=1.5)
    p3 = ax.bar(categories, detection_only, 
                bottom=[fully_correct[0] + partial[0]], 
                label='Detection Success, Recognition Failed (3.1%)', 
                color=colors[2], edgecolor='black', linewidth=1.5)
    p4 = ax.bar(categories, complete_failure, 
                bottom=[fully_correct[0] + partial[0] + detection_only[0]], 
                label='Complete Failure (1.3%)', 
                color=colors[3], edgecolor='black', linewidth=1.5)
    
    # เพิ่มค่าเปอร์เซ็นต์บนแท่ง
    ax.text(0, fully_correct[0]/2, f'{fully_correct[0]}%', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(0, fully_correct[0] + partial[0]/2, f'{partial[0]}%', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(0, fully_correct[0] + partial[0] + detection_only[0]/2, f'{detection_only[0]}%', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(0, fully_correct[0] + partial[0] + detection_only[0] + complete_failure[0]/2, 
            f'{complete_failure[0]}%', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    # ตั้งค่าแกน
    ax.set_ylabel('Percentage (%)', fontsize=14, fontweight='bold')
    ax.set_title('End-to-End System Results Distribution', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim([0, 100])
    ax.set_xticks([])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Legend
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved stacked bar chart to: {save_path}")
    
    plt.close()


def create_horizontal_stacked_bar(save_path: str = "figures/6.3.1_end_to_end_results_horizontal.png"):
    """
    สร้างกราฟแท่งซ้อนแนวนอน
    """
    # ข้อมูลจาก paper
    labels = ["End-to-End Results"]
    fully_correct = [87.4]
    partial = [8.2]
    detection_only = [3.1]
    complete_failure = [1.3]
    
    colors = ['#10b981', '#f59e0b', '#ef4444', '#6b7280']
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(10, 3))
    
    # สร้าง stacked bar แนวนอน
    p1 = ax.barh(labels, fully_correct, label='Fully Correct (87.4%)', 
                 color=colors[0], edgecolor='black', linewidth=1.5)
    p2 = ax.barh(labels, partial, left=fully_correct, 
                 label='Partial Recognition (8.2%)', 
                 color=colors[1], edgecolor='black', linewidth=1.5)
    p3 = ax.barh(labels, detection_only, 
                 left=[fully_correct[0] + partial[0]], 
                 label='Detection Success, Recognition Failed (3.1%)', 
                 color=colors[2], edgecolor='black', linewidth=1.5)
    p4 = ax.barh(labels, complete_failure, 
                 left=[fully_correct[0] + partial[0] + detection_only[0]], 
                 label='Complete Failure (1.3%)', 
                 color=colors[3], edgecolor='black', linewidth=1.5)
    
    # เพิ่มค่าเปอร์เซ็นต์
    ax.text(fully_correct[0]/2, 0, f'{fully_correct[0]}%', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(fully_correct[0] + partial[0]/2, 0, f'{partial[0]}%', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(fully_correct[0] + partial[0] + detection_only[0]/2, 0, f'{detection_only[0]}%', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(fully_correct[0] + partial[0] + detection_only[0] + complete_failure[0]/2, 0, 
            f'{complete_failure[0]}%', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    # ตั้งค่าแกน
    ax.set_xlabel('Percentage (%)', fontsize=14, fontweight='bold')
    ax.set_title('End-to-End System Results Distribution', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim([0, 100])
    ax.set_yticks([])
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Legend
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9, ncol=2)
    
    plt.tight_layout()
    
    # บันทึก
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved horizontal stacked bar chart to: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    print("📊 Creating End-to-End Results Charts (6.3.1)\n")
    
    # สร้างกราฟวงกลม
    print("1. Creating pie chart...")
    create_pie_chart()
    
    # สร้างกราฟแท่งซ้อน
    print("\n2. Creating stacked bar chart...")
    create_stacked_bar_chart()
    
    # สร้างกราฟแท่งซ้อนแนวนอน
    print("\n3. Creating horizontal stacked bar chart...")
    create_horizontal_stacked_bar()
    
    print("\n✅ Done!")
    print("\n📝 Note:")
    print("   - Data from paper Section 6.3:")
    print("     * Fully Correct: 87.4%")
    print("     * Partial Recognition: 8.2%")
    print("     * Detection Success, Recognition Failed: 3.1%")
    print("     * Complete Failure: 1.3%")
    print("   - Three chart types created:")
    print("     * Pie chart: figures/6.3.1_end_to_end_results_pie.png")
    print("     * Stacked bar: figures/6.3.1_end_to_end_results_bar.png")
    print("     * Horizontal stacked bar: figures/6.3.1_end_to_end_results_horizontal.png")

