#!/bin/bash

echo "🚀 Starting Financial Models App..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found${NC}"

# Start backend
echo -e "${BLUE}🐍 Starting Python backend...${NC}"
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1

# Start Flask app in background
echo -e "${GREEN}🚀 Starting Flask backend on http://localhost:5000${NC}"
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is running (updated to port 5001)
if curl -s http://localhost:5001/api/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running successfully on port 5001${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Open frontend directly in browser (no separate server needed)
cd ../frontend
echo -e "${BLUE}🌐 Opening frontend...${NC}"
echo -e "${GREEN}💡 Opening index.html directly in browser${NC}"
echo -e "${YELLOW}📱 The frontend will connect to backend on port 5001${NC}"

# Get absolute path to index.html
FRONTEND_PATH="$(pwd)/index.html"

# Try to open in browser
if command_exists open; then
    echo -e "${GREEN}🚀 Opening in default browser...${NC}"
    open "file://${FRONTEND_PATH}"
elif command_exists xdg-open; then
    echo -e "${GREEN}🚀 Opening in default browser...${NC}"
    xdg-open "file://${FRONTEND_PATH}"
else
    echo -e "${YELLOW}📁 Please open this file in your browser:${NC}"
    echo -e "${BLUE}file://${FRONTEND_PATH}${NC}"
fi

echo -e "${GREEN}✅ Setup complete! The app should now be running.${NC}"
echo -e "${BLUE}Backend API: http://localhost:5001${NC}"
echo -e "${BLUE}Frontend: file://${FRONTEND_PATH}${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the backend server.${NC}"

# Keep the backend running
wait $BACKEND_PID

# Cleanup on exit
cleanup() {
    echo -e "${YELLOW}🛑 Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM 