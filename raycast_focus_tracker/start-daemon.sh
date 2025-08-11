#!/bin/bash
# Raycast Focus Tracker Background Launcher

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for existing processes
if pgrep -f "menuBar.py" >/dev/null 2>&1; then
    echo "Raycast Focus Tracker is already running!"
    echo "Use 'raycast-tracker-stop' to stop existing instances first."
    exit 1
fi

echo "Starting Raycast Focus Tracker in background..."
echo "Use 'raycast-tracker-stop' to stop it."

# Start the menuBar app in background, redirecting output to logs
if [ -f "$SCRIPT_DIR/../setup.py" ]; then
    # Development mode
    LOG_DIR="$SCRIPT_DIR/../logs"
    DATA_DIR="$SCRIPT_DIR/../data"
else
    # Installed mode
    LOG_DIR="$HOME/.raycast-focus-tracker/logs"
    DATA_DIR="$HOME/.raycast-focus-tracker/data"
fi

mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

# Start the Python app in background
nohup python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from menuBar import FocusApp
app = FocusApp()
app.run()
" > "$LOG_DIR/daemon.log" 2>&1 &

echo "Started with PID $!"
echo "Logs: $LOG_DIR/daemon.log"