#!/usr/bin/env bash
# ============================================================================
#  Wall Street Financial-Models – One-Click Startup Script (Mac / Linux)
# ----------------------------------------------------------------------------
#  What this script does
#  1) Detects the project root and moves there
#  2) Creates & activates a Python virtual-env (./venv) if it does not exist
#  3) Installs / upgrades all required packages (silent if already satisfied)
#  4) Kills any process already listening on ports 5001 (backend) or 8080 (UI)
#  5) Launches the Flask backend on :5001
#  6) Launches a lightweight HTTP server for the static frontend on :8080
#  7) Opens your default browser at http://localhost:8080
#  8) Streams logs so you can quit with CTRL-C
# ----------------------------------------------------------------------------
#  Usage:  chmod +x start.sh && ./start.sh
# ============================================================================
set -euo pipefail

# -------- 1.  Locate project root ------------------------------------------------
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/financial-models-app"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [[ ! -d "$BACKEND_DIR" || ! -d "$FRONTEND_DIR" ]]; then
  echo "❌ Could not find backend or frontend directory."
  echo "   Expected: $BACKEND_DIR and $FRONTEND_DIR"
  exit 1
fi

cd "$PROJECT_ROOT"

# -------- 2.  Python virtual-env --------------------------------------------------
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  echo "🐍 Creating Python virtual-environment (./venv)…"
  python3 -m venv venv
fi
source "$PROJECT_ROOT/venv/bin/activate"

# -------- 3.  Install / update dependencies --------------------------------------
REQ_FILE="$BACKEND_DIR/requirements.txt"
if [[ -f "$REQ_FILE" ]]; then
  echo "📦 Installing / updating Python dependencies…"
  python -m pip install --upgrade pip >/dev/null
  python -m pip install -r "$REQ_FILE" >/dev/null
else
  echo "⚠️  requirements.txt not found – skipping pip install"
fi

# -------- 4.  Free up ports 5001 & 8080 -----------------------------------------
for PORT in 5001 8080; do
  PIDS=$(lsof -ti :$PORT || true)
  if [[ -n "$PIDS" ]]; then
    echo "🔪 Killing processes on port $PORT ($PIDS)…"
    kill $PIDS || true
  fi
done
sleep 1

# -------- 5.  Launch backend -----------------------------------------------------
echo "🚀 Starting Flask backend on http://localhost:5001 …"
cd "$BACKEND_DIR"
python3 app.py &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# -------- 6.  Launch static frontend --------------------------------------------
echo "🌐 Serving static UI on http://localhost:8080 …"
cd "$FRONTEND_DIR"
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

# -------- 7.  Auto-open browser --------------------------------------------------
( sleep 3 && open "http://localhost:8080" >/dev/null 2>&1 ) &

# -------- 8.  Wait / stream logs -------------------------------------------------
echo "🎉 All set!  Hit CTRL-C to stop servers.  (backend PID $BACKEND_PID, UI PID $FRONTEND_PID)"
trap 'echo "\n🛑 Stopping servers…"; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT

wait 