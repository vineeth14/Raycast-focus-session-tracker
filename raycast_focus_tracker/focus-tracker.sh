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

# Check if running in development environment (by checking for setup.py or pyproject.toml)
if [ -f "$SCRIPT_DIR/../setup.py" ] || [ -f "$SCRIPT_DIR/../pyproject.toml" ]; then
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

# Main logging loop - capture Raycast focus logs to file
# Raycast supports file logging via macOS log stream with debug level
echo "$(date): Starting Raycast focus log capture..." >> "$TRACKER_LOG"

/usr/bin/log stream --predicate 'subsystem == "com.raycast.macos"' --level debug --style compact | while read -r line; do
    # Get current date for log file naming
    CURRENT_DATE=$(date +%Y-%m-%d)

    # Define file paths for daily logs
    DAILY_LOG_FILE="$LOG_DIR/focus.$CURRENT_DATE.log"

    # Write the log line to the daily file
    echo "$line" >> "$DAILY_LOG_FILE"

    # Log that we captured a line (less frequently to avoid spam)
    if [[ $((RANDOM % 100)) -eq 0 ]]; then
        echo "$(date): Captured log lines for $CURRENT_DATE" >> "$TRACKER_LOG"
    fi
done