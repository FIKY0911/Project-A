#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend-python"
FRONTEND_DIR="$PROJECT_ROOT/frontend-javafx"
MVN="/home/fiky/.local/bin/mvn"

echo "=========================================================="
echo "          J . A . R . V . I . S .  SYSTEM STARTUP         "
echo "        Just A Rather Very Intelligent System             "
echo "=========================================================="

# 0. Ensure port 8765 is not occupied by old zombie processes
fuser -k 8765/tcp 2>/dev/null || true

# 1. Start Python Backend in background
echo "[1/3] Activating virtual environment & launching FastAPI Backend..."
source "$BACKEND_DIR/.venv/bin/activate"
(cd "$BACKEND_DIR" && python main.py) &
BACKEND_PID=$!

# Trap signals to ensure backend terminates when GUI closes
cleanup() {
    echo ""
    echo "[J.A.R.V.I.S.] Shutting down backend service (PID: $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    fuser -k 8765/tcp 2>/dev/null || true
    echo "[J.A.R.V.I.S.] Shutdown complete. Goodbye, Sir."
}
trap cleanup EXIT INT TERM

# 2. Wait for backend to open port 8765
echo "[2/3] Waiting for WebSocket gateway on 127.0.0.1:8765..."
count=0
while ! nc -z 127.0.0.1 8765 2>/dev/null && ! (echo > /dev/tcp/127.0.0.1/8765) 2>/dev/null; do
    sleep 0.5
    count=$((count+1))
    if [ "$count" -ge 20 ]; then
        echo "[!] Timeout waiting for backend. Checking status..."
        break
    fi
done
echo "[J.A.R.V.I.S.] Core Backend is ONLINE."

# 3. Launch JavaFX HUD
echo "[3/3] Initializing JavaFX Sci-Fi HUD Interface..."
if [ -f "$FRONTEND_DIR/target/jarvis-hud.jar" ]; then
    java -jar "$FRONTEND_DIR/target/jarvis-hud.jar"
elif [ -x "$MVN" ]; then
    (cd "$FRONTEND_DIR" && "$MVN" javafx:run)
else
    mvn -f "$FRONTEND_DIR/pom.xml" javafx:run
fi
