#!/bin/bash

# Raycast Focus Session Log Capture Script
# 
# Streams macOS logs for Raycast focus sessions and writes them to daily log files.
# The logs are processed by log_to_json.py to create structured data.
#
# Usage: ./focus-tracker.sh
# Logs: focus.YYYY-MM-DD.log (daily focus logs)
#       tracker.log (script status and errors)

# Exit immediately on command failure or undefined variable
set -euo pipefail

# Configuration
LOG_DIR="$HOME/Projects/raycast-tracker"
TRACKER_LOG="$LOG_DIR/tracker.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

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
        # Stream Raycast logs and filter for focus session events
        log stream \
            --predicate 'subsystem == "com.raycast.macos"' \
            --level debug \
            --style compact | \
        grep --line-buffered -E "(focus\] (Start|Cancel|Complete|Stop|Pause|Restoring|Focus session activity summary)|Goal:|Duration:|Start date:|Pauses Count:|Block Events Count:|Snooze Events Count:|Source:|Title:|Filter Mode:)" | \
        while read -r line; do
            # Write each matching line to daily log file
            echo "$line" >> "$LOG_DIR/focus.$(date +%Y-%m-%d).log"
        done
    } 2>> "$TRACKER_LOG"
    
    # Log restart and brief pause before retrying
    echo "$(date): Log stream ended, restarting..." >> "$TRACKER_LOG"
    sleep 5
done
