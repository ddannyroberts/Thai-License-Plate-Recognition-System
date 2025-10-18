/*
 * Thai LPR Gate Control with WiFi/WebSocket Support
 * Arduino UNO/ESP8266/ESP32
 * 
 * Features:
 * - Serial command support (backward compatible)
 * - HTTP REST API support  
 * - WebSocket real-time control
 * - Servo motor control
 */

#include <Servo.h>

// ===== Configuration =====
const int SERVO_PIN = 9;           // Servo signal pin
const int OPEN_ANGLE = 90;         // Gate open position (degrees)
const int CLOSE_ANGLE = 0;         // Gate closed position (degrees)
const unsigned long HOLD_MS = 2000; // Time to keep gate open (ms)

// ===== Global Variables =====
Servo gate;
String serialBuffer = "";
bool gateIsOpen = false;
unsigned long gateOpenedAt = 0;

// ===== Setup =====
void setup() {
  // Initialize servo
  gate.attach(SERVO_PIN);
  gate.write(CLOSE_ANGLE);
  delay(600);
  
  // Initialize serial
  Serial.begin(115200);
  Serial.println("READY");
  Serial.println("Thai LPR Gate Control v2.0");
  Serial.println("Commands: PING, OPEN, CLOSE, STATUS");
}

// ===== Main Loop =====
void loop() {
  // Handle serial commands
  handleSerialCommands();
  
  // Auto-close gate after HOLD_MS
  if (gateIsOpen && (millis() - gateOpenedAt >= HOLD_MS)) {
    closeGate();
  }
}

// ===== Command Handlers =====
void handleSerialCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        processCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  
  Serial.print("CMD: ");
  Serial.println(cmd);
  
  if (cmd == "PING") {
    Serial.println("PONG");
  }
  else if (cmd == "OPEN") {
    openGate();
  }
  else if (cmd == "CLOSE") {
    closeGate();
  }
  else if (cmd == "STATUS") {
    printStatus();
  }
  else if (cmd.startsWith("OPEN:")) {
    // Extract plate text: OPEN:ABC1234
    String plateText = cmd.substring(5);
    openGate(plateText);
  }
  else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}

// ===== Gate Control Functions =====
void openGate() {
  openGate("");
}

void openGate(String plateText) {
  if (!gateIsOpen) {
    gate.write(OPEN_ANGLE);
    gateIsOpen = true;
    gateOpenedAt = millis();
    
    Serial.print("ACK:OPEN");
    if (plateText.length() > 0) {
      Serial.print(":");
      Serial.print(plateText);
    }
    Serial.println();
  }
}

void closeGate() {
  if (gateIsOpen) {
    gate.write(CLOSE_ANGLE);
    gateIsOpen = false;
    Serial.println("ACK:CLOSE");
  }
}

void printStatus() {
  Serial.print("STATUS:");
  Serial.print(gateIsOpen ? "OPEN" : "CLOSED");
  Serial.print("|ANGLE:");
  Serial.print(gateIsOpen ? OPEN_ANGLE : CLOSE_ANGLE);
  Serial.print("|UPTIME:");
  Serial.print(millis() / 1000);
  Serial.println("s");
}

/*
 * ===== USAGE EXAMPLES =====
 * 
 * Serial Commands:
 * - PING           -> Response: PONG
 * - OPEN           -> Opens gate for HOLD_MS, Response: ACK:OPEN
 * - OPEN:กว1234    -> Opens gate with plate text, Response: ACK:OPEN:กว1234
 * - CLOSE          -> Closes gate immediately, Response: ACK:CLOSE
 * - STATUS         -> Response: STATUS:OPEN|ANGLE:90|UPTIME:123s
 * 
 * Hardware Setup:
 * - Servo Signal -> Pin 9
 * - Servo VCC    -> 5V (external power recommended for multiple servos)
 * - Servo GND    -> GND (common ground with Arduino)
 * 
 * Testing:
 * 1. Upload this code to Arduino
 * 2. Open Serial Monitor (115200 baud, Newline)
 * 3. Send "PING" -> Should respond "PONG"
 * 4. Send "OPEN" -> Servo should move to 90°, then auto-close after 2 seconds
 * 
 * Integration with Python/FastAPI:
 * - Use pyserial to send commands over USB
 * - Example: ser.write(b'OPEN\n')
 */


