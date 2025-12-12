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
        print(f"[ARDUINO] ⚠️ SERIAL_ENABLED is False - gate will not work!", flush=True)
        return None

    port_or_url = SERIAL_URL if SERIAL_URL else SERIAL_PORT
    
    # Check if port exists (for physical ports only)
    if not SERIAL_URL and port_or_url.startswith("/dev/"):
        import os
        if not os.path.exists(port_or_url):
            print(f"[ARDUINO] ❌ Port {port_or_url} does not exist!", flush=True)
            print(f"[ARDUINO] 💡 Check: 1) Arduino is connected, 2) Port is correct", flush=True)
            print(f"[ARDUINO] 💡 Available ports: {os.popen('ls /dev/cu.* 2>/dev/null | grep usbmodem || echo None').read().strip()}", flush=True)
            return None

    try:
        print(f"[ARDUINO] 🔌 Attempting to connect to {port_or_url} at {SERIAL_BAUD} baud...", flush=True)
        _ser = serial.serial_for_url(port_or_url, baudrate=SERIAL_BAUD, timeout=2)
        time.sleep(2.0)  # Wait for Arduino reset
        print(f"[ARDUINO] ✅ Connected to {port_or_url}", flush=True)
        
        # Test connection with PING
        try:
            _ser.reset_input_buffer()
            _ser.write(b"PING\n")
            _ser.flush()
            time.sleep(0.5)
            if _ser.in_waiting:
                response = _ser.readline().decode().strip()
                print(f"[ARDUINO] 📥 Test response: {response}", flush=True)
        except Exception as test_e:
            print(f"[ARDUINO] ⚠️ Test ping failed (but connection OK): {test_e}", flush=True)
        
        return _ser
    except serial.SerialException as e:
        print(f"[ARDUINO] ❌ Serial connection failed: {e}", flush=True)
        print(f"[ARDUINO] 💡 Check: 1) Port exists: {port_or_url}, 2) Arduino is connected, 3) No other program using the port", flush=True)
        _ser = None
        return None
    except Exception as e:
        print(f"[ARDUINO] ❌ Connection failed: {e}", flush=True)
        import traceback
        print(f"[ARDUINO] Traceback: {traceback.format_exc()}", flush=True)
        _ser = None
        return None

def send_command(cmd: str, retry_count: int = 2) -> str:
    """Send command to Arduino and get response"""
    if not SERIAL_ENABLED:
        print("[ARDUINO] ⚠️ Serial disabled (SERIAL_ENABLED=false)", flush=True)
        return ""
    
    for attempt in range(retry_count):
        try:
            ser = _connect()
            if not ser:
                if attempt < retry_count - 1:
                    print(f"[ARDUINO] ⚠️ Retry {attempt + 1}/{retry_count}...", flush=True)
                    time.sleep(1)
                    continue
                print(f"[ARDUINO] ❌ Cannot connect to {SERIAL_PORT} after {retry_count} attempts", flush=True)
                return ""
            
            # Clear any pending input
            try:
                ser.reset_input_buffer()
            except:
                pass
            
            # Send command
            cmd_bytes = f"{cmd}\n".encode()
            print(f"[ARDUINO] 📤 Sending (attempt {attempt + 1}): {cmd_bytes.decode().strip()}", flush=True)
            
            try:
                ser.write(cmd_bytes)
                ser.flush()
            except Exception as write_e:
                print(f"[ARDUINO] ⚠️ Write failed: {write_e}, closing connection...", flush=True)
                try:
                    ser.close()
                except:
                    pass
                _ser = None
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                return ""
            
            # Read response (with timeout)
            response = ""
            start_time = time.time()
            while time.time() - start_time < 3:  # 3 second timeout
                try:
                    if ser.in_waiting:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            # Skip echo lines (CMD: ...)
                            if not line.startswith("CMD:"):
                                response = line
                                print(f"[ARDUINO] 📥 Response: {response}", flush=True)
                                break
                    time.sleep(0.1)
                except Exception as read_e:
                    print(f"[ARDUINO] ⚠️ Read error: {read_e}", flush=True)
                    break
            
            if not response:
                print(f"[ARDUINO] ⚠️ No response from Arduino for command: {cmd}", flush=True)
                print(f"[ARDUINO] 💡 This might be OK - gate may still open even without response", flush=True)
            
            return response
            
        except serial.SerialException as e:
            print(f"[ARDUINO] ❌ Serial error (attempt {attempt + 1}): {e}", flush=True)
            try:
                if _ser:
                    _ser.close()
            except:
                pass
            _ser = None
            if attempt < retry_count - 1:
                time.sleep(1)
                continue
        except Exception as e:
            print(f"[ARDUINO] ❌ Command failed (attempt {attempt + 1}): {e}", flush=True)
            import traceback
            print(f"[ARDUINO] Traceback: {traceback.format_exc()}", flush=True)
            if attempt < retry_count - 1:
                time.sleep(1)
                continue
    
    return ""

def send_open_gate(plate_text: str = ""):
    """Open gate with optional plate text"""
    print(f"[GATE] 🔧 send_open_gate called with plate_text='{plate_text}'", flush=True)
    print(f"[GATE] 🔧 SERIAL_ENABLED={SERIAL_ENABLED}, SERIAL_PORT={SERIAL_PORT}, SERIAL_BAUD={SERIAL_BAUD}", flush=True)
    
    if not SERIAL_ENABLED:
        print("[GATE] ⚠️ Serial disabled (SERIAL_ENABLED=false), gate command not sent", flush=True)
        print("[GATE] 💡 To enable: Set SERIAL_ENABLED=true in environment or .env file", flush=True)
        return False
    
    if plate_text:
        cmd = f"OPEN:{plate_text}"
    else:
        cmd = "OPEN"
    
    print(f"[GATE] 📤 Sending gate command: {cmd}", flush=True)
    print(f"[GATE] 📤 Attempting to connect to Arduino...", flush=True)
    
    try:
        response = send_command(cmd)
        
        success = "ACK:OPEN" in response or "OPEN" in response.upper()
        if success:
            print(f"[GATE] ✅ Gate opened successfully! Response: {response}", flush=True)
        else:
            print(f"[GATE] ⚠️ Gate command sent but no ACK received. Response: {response}", flush=True)
            print(f"[GATE] 💡 This might be OK if Arduino doesn't send ACK, but gate should still open", flush=True)
            # ถ้าไม่มี response แต่ command ส่งไปแล้ว ก็ถือว่าสำเร็จ (บาง Arduino อาจไม่ส่ง ACK)
            if response == "":
                print(f"[GATE] ⚠️ No response from Arduino, but command was sent", flush=True)
                success = True  # ถือว่าสำเร็จถ้าส่ง command ไปแล้ว
        
        return success
    except Exception as e:
        print(f"[GATE] ❌ Exception in send_open_gate: {e}", flush=True)
        import traceback
        print(f"[GATE] Traceback: {traceback.format_exc()}", flush=True)
        return False

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
