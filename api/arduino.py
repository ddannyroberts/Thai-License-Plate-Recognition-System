# api/arduino.py - Arduino/Serial Communication with WebSocket support
import os, time
import serial

SERIAL_ENABLED = os.getenv("SERIAL_ENABLED", "false").lower() == "true"
SERIAL_PORT    = os.getenv("SERIAL_PORT", "/dev/ttyACM0")   # macOS: /dev/cu.usbmodem*, Linux: /dev/ttyACM0
SERIAL_URL     = os.getenv("SERIAL_URL")                    # Optional: socket://host:port
SERIAL_BAUD    = int(os.getenv("SERIAL_BAUD", "115200"))

_ser = None

def _connect():
    """Establish serial connection to Arduino"""
    global _ser
    if _ser and _ser.is_open:
        return _ser
    if not SERIAL_ENABLED:
        return None

    try:
        port_or_url = SERIAL_URL if SERIAL_URL else SERIAL_PORT
        print(f"[ARDUINO] Attempting to connect to {port_or_url} at {SERIAL_BAUD} baud...", flush=True)
        _ser = serial.serial_for_url(port_or_url, baudrate=SERIAL_BAUD, timeout=1)
        time.sleep(1.5)  # Wait for Arduino reset
        print(f"[ARDUINO] ✅ Connected to {port_or_url}", flush=True)
        return _ser
    except Exception as e:
        print(f"[ARDUINO] ❌ Connection failed: {e}", flush=True)
        print(f"[ARDUINO] Check: 1) Port exists: {port_or_url}, 2) SERIAL_ENABLED=true, 3) Arduino is connected", flush=True)
        return None

def send_command(cmd: str) -> str:
    """Send command to Arduino and get response"""
    if not SERIAL_ENABLED:
        print("[ARDUINO] ⚠️ Serial disabled (SERIAL_ENABLED=false)", flush=True)
        return ""
    
    try:
        ser = _connect()
        if not ser:
            print(f"[ARDUINO] ⚠️ Cannot connect to {SERIAL_PORT}", flush=True)
            return ""
        
        # Clear any pending input
        ser.reset_input_buffer()
        
        # Send command
        cmd_bytes = f"{cmd}\n".encode()
        print(f"[ARDUINO] 📤 Sending: {cmd_bytes.decode().strip()}", flush=True)
        ser.write(cmd_bytes)
        ser.flush()
        
        # Read response (with timeout)
        response = ""
        start_time = time.time()
        while time.time() - start_time < 3:  # Increased timeout to 3 seconds
            if ser.in_waiting:
                line = ser.readline().decode().strip()
                if line:
                    # Skip echo lines (CMD: ...)
                    if not line.startswith("CMD:"):
                        response = line
                        print(f"[ARDUINO] 📥 Response: {response}", flush=True)
                        break
            time.sleep(0.1)  # Small delay to avoid busy waiting
        
        if not response:
            print(f"[ARDUINO] ⚠️ No response from Arduino for command: {cmd}", flush=True)
        
        return response
        
    except Exception as e:
        print(f"[ARDUINO] ❌ Command failed: {e}", flush=True)
        import traceback
        print(f"[ARDUINO] Traceback: {traceback.format_exc()}", flush=True)
        return ""

def send_open_gate(plate_text: str = ""):
    """Open gate with optional plate text"""
    if not SERIAL_ENABLED:
        print("[GATE] ⚠️ Serial disabled, gate command not sent", flush=True)
        return False
    
    if plate_text:
        cmd = f"OPEN:{plate_text}"
    else:
        cmd = "OPEN"
    
    print(f"[GATE] 📤 Sending gate command: {cmd}", flush=True)
    response = send_command(cmd)
    
    success = "ACK:OPEN" in response
    if success:
        print(f"[GATE] ✅ Gate opened successfully! Response: {response}", flush=True)
    else:
        print(f"[GATE] ❌ Gate command failed. Response: {response}", flush=True)
    
    return success

def send_close_gate():
    """Close gate immediately"""
    response = send_command("CLOSE")
    return "ACK:CLOSE" in response

def ping_arduino() -> bool:
    """Test Arduino connection"""
    response = send_command("PING")
    return "PONG" in response

def get_gate_status() -> dict:
    """Get current gate status"""
    response = send_command("STATUS")
    
    # Parse response: STATUS:OPEN|ANGLE:90|UPTIME:123s
    status = {
        "connected": bool(response),
        "is_open": "OPEN" in response,
        "angle": 0,
        "uptime": 0
    }
    
    if response:
        parts = response.split("|")
        for part in parts:
            if "ANGLE:" in part:
                try:
                    status["angle"] = int(part.split(":")[1])
                except:
                    pass
            if "UPTIME:" in part:
                try:
                    status["uptime"] = int(part.split(":")[1].replace("s", ""))
                except:
                    pass
    
    return status

def disconnect():
    """Close serial connection"""
    global _ser
    if _ser and _ser.is_open:
        _ser.close()
        _ser = None
        print("[ARDUINO] Disconnected", flush=True)
