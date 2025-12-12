#!/bin/bash

# Script สำหรับตรวจสอบ Serial Port สำหรับ Arduino
# Usage: ./check_serial_port.sh

echo "🔍 ตรวจสอบ Serial Port สำหรับ Arduino"
echo "========================================"
echo ""

# ตรวจสอบ OS
OS="$(uname -s)"
echo "📱 Operating System: $OS"
echo ""

# หา Serial Ports
echo "🔌 Serial Ports ที่พบในระบบ:"
echo ""

if [[ "$OS" == "Darwin" ]]; then
    # macOS
    echo "=== macOS Serial Ports (cu.*) ==="
    ls -lh /dev/cu.* 2>/dev/null | grep -E "(usbmodem|USB)" || echo "❌ ไม่พบ USB Serial Ports"
    echo ""
    echo "=== macOS Serial Ports (tty.*) ==="
    ls -lh /dev/tty.* 2>/dev/null | grep -E "(usbmodem|USB)" || echo "❌ ไม่พบ USB Serial Ports"
elif [[ "$OS" == "Linux" ]]; then
    # Linux
    echo "=== Linux Serial Ports ==="
    ls -lh /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "❌ ไม่พบ Serial Ports"
else
    echo "⚠️  OS อื่นๆ - ตรวจสอบด้วยตนเอง"
fi

echo ""
echo "========================================"
echo ""

# ตรวจสอบการตั้งค่าใน start.sh
if [ -f "start.sh" ]; then
    echo "📝 การตั้งค่าใน start.sh:"
    SERIAL_PORT=$(grep "SERIAL_PORT=" start.sh | head -1 | cut -d'"' -f2)
    SERIAL_BAUD=$(grep "SERIAL_BAUD=" start.sh | head -1 | cut -d'"' -f2)
    SERIAL_ENABLED=$(grep "SERIAL_ENABLED=" start.sh | head -1 | cut -d'"' -f2)
    
    echo "   SERIAL_ENABLED: $SERIAL_ENABLED"
    echo "   SERIAL_PORT: $SERIAL_PORT"
    echo "   SERIAL_BAUD: $SERIAL_BAUD"
    echo ""
    
    # ตรวจสอบว่า port มีอยู่จริงหรือไม่
    if [ -n "$SERIAL_PORT" ]; then
        if [ -e "$SERIAL_PORT" ]; then
            echo "✅ Port $SERIAL_PORT พบในระบบ!"
            echo "   Permission: $(ls -l $SERIAL_PORT | awk '{print $1}')"
        else
            echo "❌ Port $SERIAL_PORT ไม่พบในระบบ!"
            echo "   💡 แนะนำ: ตรวจสอบว่า Arduino เชื่อมต่อแล้วหรือยัง"
        fi
    fi
else
    echo "⚠️  ไม่พบไฟล์ start.sh"
fi

echo ""
echo "========================================"
echo ""

# ตรวจสอบ .env file (ถ้ามี)
if [ -f ".env" ]; then
    echo "📝 การตั้งค่าใน .env:"
    if grep -q "SERIAL_PORT" .env; then
        ENV_PORT=$(grep "SERIAL_PORT" .env | head -1 | cut -d'=' -f2 | tr -d ' ')
        ENV_BAUD=$(grep "SERIAL_BAUD" .env | head -1 | cut -d'=' -f2 | tr -d ' ')
        ENV_ENABLED=$(grep "SERIAL_ENABLED" .env | head -1 | cut -d'=' -f2 | tr -d ' ')
        
        echo "   SERIAL_ENABLED: $ENV_ENABLED"
        echo "   SERIAL_PORT: $ENV_PORT"
        echo "   SERIAL_BAUD: $ENV_BAUD"
        
        if [ -n "$ENV_PORT" ] && [ -e "$ENV_PORT" ]; then
            echo "   ✅ Port $ENV_PORT พบในระบบ!"
        elif [ -n "$ENV_PORT" ]; then
            echo "   ❌ Port $ENV_PORT ไม่พบในระบบ!"
        fi
    else
        echo "   ⚠️  ไม่มีการตั้งค่า SERIAL_PORT ใน .env"
    fi
else
    echo "⚠️  ไม่พบไฟล์ .env (ใช้ค่าจาก start.sh แทน)"
fi

echo ""
echo "========================================"
echo ""

# คำแนะนำ
echo "💡 คำแนะนำ:"
echo ""
echo "1. บน macOS ใช้ /dev/cu.* สำหรับ serial communication"
echo "2. บน Linux ใช้ /dev/ttyACM* หรือ /dev/ttyUSB*"
echo "3. ตรวจสอบว่า Arduino เชื่อมต่อแล้วและ upload firmware แล้ว"
echo "4. ทดสอบด้วย Serial Monitor ใน Arduino IDE:"
echo "   - เปิด Serial Monitor (Ctrl+Shift+M)"
echo "   - ตั้ง Baud Rate: 115200"
echo "   - พิมพ์: PING → ต้องได้ PONG"
echo ""
echo "5. ถ้า port ไม่ถูกต้อง แก้ไขใน start.sh หรือ .env:"
echo "   export SERIAL_PORT=\"/dev/cu.usbmodem11201\"  # macOS"
echo "   export SERIAL_PORT=\"/dev/ttyACM0\"            # Linux"
echo ""

