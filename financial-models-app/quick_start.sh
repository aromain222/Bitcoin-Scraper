#!/bin/bash

echo "🚀 Starting Financial Models App..."
echo "=================================="

# Kill any existing servers on these ports
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start backend
echo "🐍 Starting backend API on port 5001..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment
sleep 3

# Start frontend
echo "🌐 Starting frontend on port 8080..."
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

# Wait a moment
sleep 2

echo ""
echo "🎉 SUCCESS! Your website is running:"
echo "📱 Main Website: http://localhost:8080"
echo "🧪 Test Page: http://localhost:8080/test.html"
echo "🔧 API Health: http://localhost:5001/api/health"
echo ""
echo "🌐 Opening your website now..."

# Open browser
open http://localhost:8080

echo ""
echo "✅ Servers are running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop servers, press Ctrl+C or run:"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Leave this terminal open to keep servers running..."

# Keep script running
wait 