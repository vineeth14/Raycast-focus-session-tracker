#!/usr/bin/env python3
"""Stop Raycast Focus Tracker
Terminates all raycast-tracker related processes.
"""

import subprocess
import sys
import time

def main():
    """Stop all raycast-tracker processes."""
    print("Stopping Raycast Focus Tracker...")
    
    patterns = [
        "raycast-tracker",
        "focus-tracker.sh", 
        "log stream.*com.raycast.macos",
        "menuBar.py",
        "raycast_focus_tracker"
    ]
    
    stopped_pids = []
    
    # First, find all processes
    for pattern in patterns:
        try:
            result = subprocess.run(['pgrep', '-f', pattern], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip()]
                stopped_pids.extend(pids)
                print(f"Found {len(pids)} processes matching '{pattern}': {', '.join(pids)}")
        except Exception as e:
            print(f"Warning: Error finding {pattern}: {e}")
    
    if not stopped_pids:
        print("No Raycast Focus Tracker processes were running")
        return
    
    # Remove duplicates
    stopped_pids = list(set(stopped_pids))
    print(f"Stopping {len(stopped_pids)} processes: {', '.join(stopped_pids)}")
    
    # Kill processes with TERM first
    for pattern in patterns:
        try:
            subprocess.run(['pkill', '-TERM', '-f', pattern], 
                         capture_output=True, text=True)
        except Exception:
            pass
    
    # Wait briefly for graceful shutdown
    time.sleep(1)
    
    # Force kill any remaining processes
    for pattern in patterns:
        try:
            subprocess.run(['pkill', '-KILL', '-f', pattern], 
                         capture_output=True, text=True)
        except Exception:
            pass
    
    # Wait and verify
    time.sleep(0.5)
    remaining = []
    for pid in stopped_pids:
        try:
            result = subprocess.run(['kill', '-0', pid], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                remaining.append(pid)
        except Exception:
            pass
    
    if remaining:
        print(f"Warning: {len(remaining)} processes still running: {', '.join(remaining)}")
        # Final force kill
        for pid in remaining:
            try:
                subprocess.run(['kill', '-9', pid], capture_output=True)
            except Exception:
                pass
        print("Attempted force kill on remaining processes")
    
    print("All Raycast Focus Tracker processes stopped")

if __name__ == "__main__":
    main()