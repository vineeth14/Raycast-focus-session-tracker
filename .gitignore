#!/bin/bash

# e -> exit immediately if any commands fails
# u -> exit if using undefined variableds
set -euo pipefail

LOG_DIR="$HOME/Projects/raycast-tracker"
mkdir -p "$LOG_DIR"

cleanup() {
    echo "$(date): Stopped" >>"$LOG_DIR/tracker.log"
    exit 0
}
trap cleanup TERM INT

echo "$(date): Started" >>"$LOG_DIR/tracker.log"

while true; do
    {
        log stream --predicate 'subsystem == "com.raycast.macos"' --level debug --style compact |
            grep --line-buffered -E "(focus\] (Start|Cancel|Complete|Stop|Pause|Restoring|Focus session activity summary)|Goal:|Duration:|Start date:|Pauses Count:|Block Events Count:|Snooze Events Count:|Source:|Title:|Filter Mode:)" |
            while read -r line; do
                echo $line >>"$LOG_DIR/focus.$(date +%Y-%m-%d).log"
            done
    } 2>>"$LOG_DIR/tracker.log"

    echo "$(date): Restarting..." >>"$LOG_DIR/tracker.log"
    sleep 5
done
