"""Raycast Focus Tracker - macOS Menu Bar Application

Displays focus session statistics and streak data in the menu bar.
Provides access to heatmap visualization and real-time data refresh.
"""

import json
import os
import subprocess
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import lesley
import rumps

from .data_access import (
    get_current_streak,
    get_longest_streak,
    get_today_by_goal,
    get_today_minutes,
    DATA_DIR,
)
from .streak_calculation import update_streaks


class FocusApp(rumps.App):
    def __init__(self):
        super().__init__("🎯")
        
        # --- Use same directory as data_access.py ---
        self.script_dir = Path(__file__).parent
        self.data_dir = Path(DATA_DIR)
        
        # Ensure the data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._start_background_tracker()
        self._parse_latest_logs()  # Parse logs before building menu
        self.create_menu()
        
        # Auto-refresh every 5 seconds
        self._auto_refresh_timer = rumps.Timer(self._auto_refresh, 5)
        self._auto_refresh_timer.start()

    def create_menu(self):
        self.menu.clear()
        self._refresh_data()

        self.menu.update(
            [
                ("Streak Data", self._build_streak_submenu()),
                ("Today's Time", self._build_time_submenu()),
                ("Time by Goal", self._build_goals_submenu()),
                rumps.separator,
                "Show Heatmap",
                "Refresh",
            ]
        )

    def _refresh_data(self):
        """Load all focus data and update streaks."""
        daily_data = {}
        for focus_file in self.data_dir.glob("focus.*.json"):
            with open(focus_file, "r") as f:
                daily_data.update(json.load(f))
        update_streaks(daily_data, str(self.data_dir / "streaks.json"))

    def _build_streak_submenu(self):
        """Build streak information submenu."""
        current = get_current_streak()
        longest = get_longest_streak()

        return [
            rumps.MenuItem(f"Current: {current} days", callback=self._do_nothing),
            rumps.MenuItem(f"Longest: {longest} days", callback=self._do_nothing),
        ]

    def _build_time_submenu(self):
        """Build today's time information submenu."""
        minutes = get_today_minutes()
        hours, remaining_mins = divmod(minutes, 60)

        submenu = [
            rumps.MenuItem(f"Total: {minutes} minutes", callback=self._do_nothing)
        ]

        if hours > 0:
            submenu.append(
                rumps.MenuItem(
                    f"= {hours}h {remaining_mins}m", callback=self._do_nothing
                )
            )

        return submenu

    def _build_goals_submenu(self):
        """Build goals breakdown submenu."""
        goals = get_today_by_goal()

        if not goals:
            return [rumps.MenuItem("No sessions today", callback=self._do_nothing)]

        submenu = []
        total = 0

        for goal, minutes in goals.items():
            submenu.append(
                rumps.MenuItem(f"{goal}: {minutes}m", callback=self._do_nothing)
            )
            total += minutes

        submenu.extend(
            [
                rumps.separator,
                rumps.MenuItem(f"Total: {total}m", callback=self._do_nothing),
            ]
        )

        return submenu

    def _parse_latest_logs(self):
        """Parse any new log data to JSON files."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Look for logs in project directory first, then home directory
            project_log_dir = self.script_dir.parent / "logs"
            home_log_dir = Path.home() / ".raycast-focus-tracker" / "logs"
            
            log_file = None
            if (project_log_dir / f"focus.{today}.log").exists():
                log_file = project_log_dir / f"focus.{today}.log"
            elif (home_log_dir / f"focus.{today}.log").exists():
                log_file = home_log_dir / f"focus.{today}.log"
            
            if log_file:
                json_file = self.data_dir / f"focus.{today}.json"
                # Import and run log parser
                from .log_to_json import parse_log_file
                parse_log_file(str(log_file), str(json_file))
                print(f"Parsed {log_file} -> {json_file}")
            else:
                print(f"No log file found for {today}")
        except Exception as e:
            print(f"Error parsing logs: {e}")
    
    def _update_menu_data(self):
        """Update menu data without rebuilding the entire menu."""
        self._refresh_data()

        # Update submenus in place
        self._update_submenu("Streak Data", self._build_streak_submenu())
        self._update_submenu("Today's Time", self._build_time_submenu())
        self._update_submenu("Time by Goal", self._build_goals_submenu())

    def _update_submenu(self, menu_title, items):
        """Helper to update a submenu with new items."""
        self.menu[menu_title].clear()
        for item in items:
            self.menu[menu_title].add(item)

    def _create_heatmap(self):
        """Create GitHub-style heatmap of focus sessions."""
        # Collect all focus data
        daily_data = {}
        for focus_file in self.data_dir.glob("focus.*.json"):
            with open(focus_file, "r") as f:
                daily_data.update(json.load(f))

        # Generate year data for heatmap
        year = datetime.now().year
        dates, values = self._generate_year_data(daily_data, year)

        # Create and save heatmap
        chart = lesley.cal_heatmap(
            dates,
            values,
            days_of_week=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            cmap="Greens",
        )

        heatmap_path = Path.cwd() / "focus_heatmap.html"
        chart.save(str(heatmap_path))
        webbrowser.open(heatmap_path.as_uri())

    def _generate_year_data(self, daily_data, year):
        """Generate dates and values for the entire year."""
        dates = []
        values = []
        current_date = datetime(year, 1, 1)

        while current_date <= datetime(year, 12, 31):
            date_str = current_date.strftime("%Y-%m-%d")
            minutes = daily_data.get(date_str, {}).get("total_time_minutes", 0)

            dates.append(current_date)
            values.append(f"Time Spent Focussing {minutes}min")
            current_date += timedelta(days=1)

        return dates, values

    @rumps.clicked("Show Heatmap")
    def show_heatmap(self, _):
        """Generate and display focus heatmap."""
        self._create_heatmap()

    @rumps.clicked("Refresh")
    def refresh(self, _):
        """Refresh all menu data by parsing latest logs."""
        self._parse_latest_logs()
        self._update_menu_data()
    
    def _auto_refresh(self, _):
        """Auto-refresh menu data every 5 seconds."""
        print(f"Auto-refresh triggered at {datetime.now()}")
        self._parse_latest_logs()
        self._update_menu_data()
    
    def quit_application(self, _):
        """Override rumps quit to stop background tracker."""
        try:
            # Stop auto-refresh timer
            if hasattr(self, '_auto_refresh_timer'):
                self._auto_refresh_timer.stop()
            
            # Stop background tracker processes
            subprocess.run(['/usr/bin/pkill', '-f', 'focus-tracker.sh'], 
                         capture_output=True)
            subprocess.run(['/usr/bin/pkill', '-f', 'log stream.*com.raycast.macos'], 
                         capture_output=True)
            print("Stopped background tracker")
        except Exception as e:
            print(f"Error stopping background tracker: {e}")
        
        super().quit_application(_)

    def _start_background_tracker(self):
        """Start the focus tracker script in the background if not already running."""
        try:
            # Check if focus-tracker.sh script is already running  
            result = subprocess.run(['/usr/bin/pgrep', '-f', 'focus-tracker.sh'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                existing_pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip()]
                print(f"Focus tracker already running (PIDs: {', '.join(existing_pids)})")
                return
            
            # Start the tracker script in background
            script_path = Path(__file__).parent / "focus-tracker.sh"
            if not script_path.exists():
                print(f"Warning: focus-tracker.sh not found at {script_path}")
                print("You may need to manually start the tracker script")
                return
            
            # Start process
            process = subprocess.Popen([str(script_path)], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           cwd=str(self.data_dir.parent),
                           start_new_session=True)
            
            # Brief wait to ensure process starts
            time.sleep(0.5)
            if process.poll() is None:
                print(f"Started focus tracker in background (PID: {process.pid})")
            else:
                print("Warning: Focus tracker failed to start")
            
        except Exception as e:
            print(f"Error starting background tracker: {e}")

    def _do_nothing(self, _):
        """Empty callback to make menu items appear clickable but do nothing when clicked."""
        pass


def main():
    """Entry point for console script."""
    import sys
    import signal
    
    # Check if another menuBar instance is already running
    current_pid = os.getpid()
    result = subprocess.run(['/usr/bin/pgrep', '-f', 'menuBar.py'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        existing_pids = [pid.strip() for pid in result.stdout.strip().split('\n') 
                       if pid.strip() and pid.strip() != str(current_pid)]
        if existing_pids:
            print(f"Raycast Focus Tracker is already running (PIDs: {', '.join(existing_pids)})")
            print("Use 'raycast-tracker-stop' to stop existing instances first.")
            sys.exit(1)
    
    print("Starting Raycast Focus Tracker...")
    print("Use 'Quit' from menu bar or Ctrl+C to stop")
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        """Handle Ctrl+C by cleaning up background processes."""
        print("\nReceived interrupt, cleaning up...")
        try:
            subprocess.run(['/usr/bin/pkill', '-f', 'focus-tracker.sh'], capture_output=True)
            subprocess.run(['/usr/bin/pkill', '-f', 'log stream.*com.raycast.macos'], capture_output=True)
            print("Stopped background tracker")
        except Exception as e:
            print(f"Error stopping background tracker: {e}")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        app = FocusApp()
        app.run()
    except Exception as e:
        print(f"ERROR: Failed to start menu bar app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

