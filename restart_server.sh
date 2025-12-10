#!/bin/bash

# Thai LPR API - Restart Script
# This script stops the current server and starts a new one with proper environment variables

echo "🔄 Restarting Thai License Plate Recognition API..."
echo "=================================================="

# Find and kill existing uvicorn processes
echo "🛑 Stopping existing server..."
pkill -f "uvicorn api.main:app" || echo "   No existing server found"

# Wait a moment for process to stop
sleep 2

# Load environment variables from .env
if [ -f .env ]; then
    echo "✅ Loading .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env file not found, using defaults from start.sh"
    source start.sh
    exit 0
fi

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
echo "✅ Serial enabled: ${SERIAL_ENABLED}"
echo "✅ Serial port: ${SERIAL_PORT}"
echo "✅ Serial baud: ${SERIAL_BAUD}"
echo ""

# Get port from environment or use default 8001
PORT=${APP_PORT:-8001}

echo "🚀 Starting server on http://0.0.0.0:${PORT}"
echo "   Press CTRL+C to stop"
echo ""

# Start the server
uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --reload

