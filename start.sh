#!/bin/bash

# Thai LPR API - Start Script
# This script sets up environment variables and starts the FastAPI server

echo "🚗 Starting Thai License Plate Recognition API..."
echo "=================================================="

# Set environment variables (using SQLite for local development)
export DATABASE_URL="sqlite:///./data.db"
export SERIAL_ENABLED="true"
export SERIAL_PORT="/dev/cu.usbmodem11201"  # macOS: /dev/cu.usbmodem*, Linux: /dev/ttyACM0
export SERIAL_BAUD="115200"                  # Must match Arduino Serial.begin(115200)
export GATE_TRIGGER_MODE="per_plate_cooldown"
export GATE_COOLDOWN_SEC="10"
export VIDEO_MIN_LETTERS="2"
export VIDEO_SKIP_FRAMES="30"
export MIN_CONFIDENCE="0.3"

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if models exist
if [ ! -f "models/detector/best.pt" ] || [ ! -f "models/reader/best.pt" ]; then
    echo "❌ Error: Trained models not found!"
    echo "   Please ensure models/detector/best.pt and models/reader/best.pt exist."
    exit 1
fi

echo "✅ Models found"
echo "✅ Using SQLite database: data.db"
echo ""
# Get port from environment or use default 8001
PORT=${APP_PORT:-8001}

echo "🚀 Starting server on http://0.0.0.0:${PORT}"
echo "   Press CTRL+C to stop"
echo ""

# Start the server
uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --reload











