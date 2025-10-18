# api/province_parser.py
"""
แยกจังหวัดจากข้อความป้ายทะเบียน
"""
import re

# รายการอักษรย่อจังหวัดทั้งหมด (2 ตัวอักษรไทย)
THAI_PROVINCES = {
    # กรุงเทพและปริมณฑล
    "กท": "กรุงเทพมหานคร",
    "นบ": "นนทบุรี", 
    "ปท": "ปทุมธานี",
    "สป": "สมุทรปราการ",
    "นน": "นครนายก",
    "สค": "สมุทรสาคร",
    "ฉช": "ฉะเชิงเทรา",
    
    # ภาคเหนือ
    "กพ": "กำแพงเพชร",
    "ชร": "เชียงราย",
    "ชม": "เชียงใหม่",
    "ตก": "ตาก",
    "นว": "น่าน",
    "พจ": "พิจิตร",
    "พร": "เพชรบูรณ์",
    "พย": "พะเยา",
    "แพ": "แพร่",
    "มห": "แม่ฮ่องสอน",
    "ลป": "ลำปาง",
    "ลน": "ลำพูน",
    "สท": "สุโขทัย",
    "อต": "อุตรดิตถ์",
    "อน": "อุทัยธานี",
    
    # ภาคตะวันออกเฉียงเหนือ
    "กส": "กาฬสินธุ์",
    "ขก": "ขอนแก่น",
    "ชย": "ชัยภูมิ",
    "นค": "นครพนม",
    "นฐ": "นครราชสีมา",
    "บร": "บุรีรัมย์",
    "มค": "มหาสารคาม",
    "มห": "มุกดาหาร",
    "รอ": "ร้อยเอ็ด",
    "ลย": "เลย",
    "สน": "ศรีสะเกษ",
    "สก": "สกลนคร",
    "สร": "สุรินทร์",
    "หนอ": "หนองคาย",
    "หบ": "หนองบัวลำภู",
    "อบ": "อุบลราชธานี",
    "อด": "อุดรธานี",
    "อม": "อำนาจเจริญ",
    "บก": "บึงกาฬ",
    
    # ภาคกลาง
    "อท": "อ่างทอง",
    "อย": "พระนครศรีอยุธยา",
    "ชน": "ชัยนาท",
    "ลบ": "ลพบุรี",
    "สห": "สระบุรี",
    "สิง": "สิงห์บุรี",
    "สบ": "สุพรรณบุรี",
    
    # ภาคตะวันตก
    "กจ": "กาญจนบุรี",
    "ตร": "ตราด",
    "ปข": "ประจวบคีรีขันธ์",
    "พบ": "เพชรบุรี",
    "รบ": "ราชบุรี",
    "สส": "สมุทรสงคราม",
    
    # ภาคตะวันออก
    "จบ": "จันทบุรี",
    "ชบ": "ชลบุรี",
    "ระยอง": "ระยอง",
    "สระแก้ว": "สระแก้ว",
    
    # ภาคใต้
    "กระบี่": "กระบี่",
    "กบ": "กระบี่",
    "ชุม": "ชุมพร",
    "ตง": "ตรัง",
    "นฐ": "นครศรีธรรมราช",
    "นว": "นราธิวาส",
    "ปน": "ปัตตานี",
    "พง": "พังงา",
    "พท": "พัทลุง",
    "ภก": "ภูเก็ต",
    "ยล": "ยะลา",
    "ระนอง": "ระนอง",
    "สฎ": "สตูล",
    "สง": "สงขลา",
    "สต": "สุราษฎร์ธานี",
    
    # รหัสพิเศษ
    "กร": "กรุงเทพมหานคร (รถราชการ)",
    "นก": "นครปฐม",
}

def extract_province(text: str) -> tuple[str, str]:
    """
    แยกจังหวัดจากข้อความป้ายทะเบียน
    
    Returns:
        (plate_number, province_code): เช่น ("1234", "กก")
    """
    if not text or len(text) < 2:
        return text, ""
    
    # ลบช่องว่างและอักขระพิเศษ
    text = text.strip()
    
    # รูปแบบป้ายทะเบียนไทย: [รหัสจังหวัด 1-2 ตัว] [ตัวเลข] หรือ [ตัวเลข][รหัสจังหวัด][ตัวเลข]
    
    # ลองหา 2 ตัวอักษรไทยที่ขึ้นต้น
    match = re.match(r'^([ก-ฮ]{1,2})\s*(.+)$', text)
    if match:
        province_code = match.group(1)
        plate_number = match.group(2).strip()
        
        # ตรวจสอบว่าเป็นรหัสจังหวัดจริงหรือไม่
        if province_code in THAI_PROVINCES:
            return plate_number, province_code
        # ถ้าไม่ใช่ อาจเป็นส่วนหนึ่งของเลขป้าย
        return text, ""
    
    # ลองหา pattern: ตัวเลข + ตัวอักษรไทย + ตัวเลข
    match = re.search(r'([ก-ฮ]{1,2})', text)
    if match:
        province_code = match.group(1)
        if province_code in THAI_PROVINCES:
            # ลบรหัสจังหวัดออก
            plate_number = text.replace(province_code, '').strip()
            return plate_number, province_code
    
    # ไม่พบจังหวัด
    return text, ""

def get_province_name(province_code: str) -> str:
    """
    แปลงรหัสจังหวัดเป็นชื่อเต็ม
    
    Args:
        province_code: รหัสจังหวัด เช่น "กก", "กร"
        
    Returns:
        ชื่อจังหวัดเต็ม หรือ รหัสเดิมถ้าไม่พบ
    """
    return THAI_PROVINCES.get(province_code, province_code)

def format_plate_text(text: str) -> str:
    """
    จัดรูปแบบข้อความป้ายให้สวยงาม
    เช่น "กก1234" -> "กก 1234"
    """
    if not text:
        return text
    
    # ลองแยก province
    plate_number, province_code = extract_province(text)
    
    if province_code:
        # มี province code - จัดรูปแบบให้มีช่องว่าง
        return f"{province_code} {plate_number}".strip()
    
    return text

def parse_plate(text: str) -> dict:
    """
    แยกวิเคราะห์ข้อความป้ายทะเบียนให้สมบูรณ์
    
    Returns:
        {
            "plate_number": "1234",
            "province_code": "กก", 
            "province_name": "กรุงเทพมหานคร",
            "full_text": "กก 1234",
            "formatted_text": "กก 1234"
        }
    """
    plate_number, province_code = extract_province(text)
    province_name = get_province_name(province_code) if province_code else ""
    formatted_text = format_plate_text(text)
    
    return {
        "plate_number": plate_number,
        "province_code": province_code,
        "province_name": province_name,
        "full_text": text,
        "formatted_text": formatted_text
    }

