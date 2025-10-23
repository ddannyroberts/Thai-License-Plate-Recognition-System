#!/bin/bash

# Thai LPR API - Start Script
# This script sets up environment variables and starts the FastAPI server

echo "🚗 Starting Thai License Plate Recognition API..."
echo "=================================================="

# Set environment variables (using SQLite for local development)
export DATABASE_URL="sqlite:///./data.db"
export ARDUINO_PORT="/dev/cu.usbserial-0001"
export ARDUINO_BAUD="9600"
export GATE_MODE="per_plate_cooldown"
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
echo "🚀 Starting server on http://0.0.0.0:8000"
echo "   Press CTRL+C to stop"
echo ""

# Start the server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload



