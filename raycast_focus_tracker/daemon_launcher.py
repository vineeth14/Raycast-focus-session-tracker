#!/usr/bin/env python3
"""Daemon launcher for Raycast Focus Tracker"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Launch Raycast Focus Tracker in background using nohup."""
    
    # Check for existing processes
    try:
        result = subprocess.run(['/usr/bin/pgrep', '-f', 'menuBar.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            existing_pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip()]
            print(f"Raycast Focus Tracker is already running (PIDs: {', '.join(existing_pids)})")
            print("Use 'raycast-tracker-stop' to stop existing instances first.")
            sys.exit(1)
    except Exception:
        pass

    print("Starting Raycast Focus Tracker in background...")
    print("Use 'raycast-tracker-stop' to stop it.")

    # Determine log directory
    script_dir = Path(__file__).parent
    if (script_dir.parent / "setup.py").exists():
        # Development mode
        log_dir = script_dir.parent / "logs"
    else:
        # Installed mode
        log_dir = Path.home() / ".raycast-focus-tracker" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "daemon.log"

    # Start the menuBar app in background
    try:
        # Run as a script to avoid relative import issues
        import sys
        menubar_path = script_dir / "menuBar.py"
        cmd = [sys.executable, str(menubar_path)]
        
        with open(log_file, 'a') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True  # This detaches from terminal
            )
        
        # Give it a moment to start
        import time
        time.sleep(0.5)
        
        if process.poll() is None:
            print(f"Started with PID {process.pid}")
            print(f"Logs: {log_file}")
        else:
            print("Failed to start - check logs for details")
            print(f"Logs: {log_file}")
            sys.exit(1)
        
    except Exception as e:
        print(f"Failed to start background process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()