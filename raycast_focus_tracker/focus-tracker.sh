#!/bin/bash

# Raycast Focus Session Log Capture and Processing Script
#
# Streams macOS logs for Raycast focus sessions, writes them to daily log files,
# and processes them into structured JSON data.
#
# This script is designed to run in two modes:
# 1. Development mode: When run from the project repository, it uses local
#    `logs` and `data` directories.
# 2. Installed mode: When installed via pip, it uses a dedicated folder in the
#    user's home directory (`~/.raycast-focus-tracker`).
#
# Usage: ./focus-tracker.sh
# Logs: focus.YYYY-MM-DD.log (daily focus logs)
#       tracker.log (script status and errors)

# Exit immediately on command failure or undefined variable
set -euo pipefail

# --- Dynamic Directory Configuration ---
# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running in development environment (by checking for setup.py)
if [ -f "$SCRIPT_DIR/../setup.py" ]; then
    # Development mode: use local directories relative to the script
    BASE_DIR="$SCRIPT_DIR/.."
    echo "Running in development mode."
else
    # Installed mode: use a hidden directory in the user's home folder
    BASE_DIR="$HOME/.raycast-focus-tracker"
    echo "Running in installed mode."
fi

# Define log and data directories
LOG_DIR="$BASE_DIR/logs"
DATA_DIR="$BASE_DIR/data"
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

TRACKER_LOG="$LOG_DIR/tracker.log"

# --- Main Execution ---

# Cleanup function for graceful shutdown
cleanup() {
    echo "$(date): Focus tracker stopped" >> "$TRACKER_LOG"
    exit 0
}

# Handle termination signals
trap cleanup TERM INT

echo "$(date): Focus tracker started" >> "$TRACKER_LOG"

# Main log capture loop
while true; do
    {
        # Define file paths for daily logs and JSON output
        DAILY_LOG_FILE="$LOG_DIR/focus.$(date +%Y-%m-%d).log"
        JSON_OUTPUT_FILE="$DATA_DIR/focus.$(date +%Y-%m-%d).json"

        # Stream Raycast logs and filter for focus session events
        log stream \
            --predicate 'subsystem == "com.raycast.macos"' \
            --level debug \
            --style compact | \
        grep --line-buffered -E "(focus] (Start|Cancel|Complete|Stop|Pause|Restoring|Focus session activity summary)|Goal:|Duration:|Start date:|Pauses Count:|Block Events Count:|Snooze Events Count:|Source:|Title:|Filter Mode:)" | \
        while read -r line; do
            # Write each matching line to the daily log file
            echo "$line" >> "$DAILY_LOG_FILE"
            
            # Process the entire log file to update JSON data in real-time
            # This ensures the data is always up-to-date
            python3 "$SCRIPT_DIR/log_to_json.py" "$DAILY_LOG_FILE" "$JSON_OUTPUT_FILE" 2>> "$TRACKER_LOG"
        done
    } 2>> "$TRACKER_LOG"
    
    # Log restart and brief pause before retrying
    echo "$(date): Log stream ended, restarting..." >> "$TRACKER_LOG"
    sleep 5
done