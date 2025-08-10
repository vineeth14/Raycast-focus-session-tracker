import rumps
import json
import july
from datetime import datetime, timedelta
from pathlib import Path
from data_access import (
    get_today_minutes,
    get_current_streak,
    get_longest_streak,
    get_today_by_goal,
)


class FocusApp(rumps.App):
    def __init__(self):
        super(FocusApp, self).__init__("🎯")
        self.create_menu()

    def create_menu(self):
        # Clear existing menu first
        self.menu.clear()

        # Create submenus with actual data
        streak_submenu = self.build_streak_submenu()
        time_submenu = self.build_time_submenu()
        goals_submenu = self.build_goals_submenu()

        # Update menu
        self.menu.update(
            [
                ("Streak Data", streak_submenu),
                ("Today's Time", time_submenu),
                ("Time by Goal", goals_submenu),
                rumps.separator,
                "Show Heatmap",
                "Refresh",
            ]
        )

    def build_streak_submenu(self):
        current = get_current_streak()
        longest = get_longest_streak()

        return [f"Current: {current} days", f"Longest: {longest} days"]

    def build_time_submenu(self):
        minutes = get_today_minutes()
        hours = minutes // 60
        remaining_mins = minutes % 60

        submenu = [f"Total: {minutes} minutes"]

        if hours > 0:
            submenu.append(f"= {hours}h {remaining_mins}m")

        return submenu

    def build_goals_submenu(self):
        goals = get_today_by_goal()

        if not goals:
            return ["No sessions today"]

        submenu = []
        total = 0

        for goal, minutes in goals.items():
            submenu.append(f"{goal}: {minutes}m")
            total += minutes

        submenu.extend([rumps.separator, f"Total: {total}m"])

        return submenu

    def get_year_data(self, year=None):
        """Get focus data for entire year from JSON files"""
        if year is None:
            year = datetime.now().year
        
        script_dir = Path(__file__).parent
        data_dir = script_dir / "data"
        
        year_data = {}
        
        # Generate all dates for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Try to find data file for this date
            focus_file = data_dir / f"focus.{date_str}.json"
            
            if focus_file.exists():
                try:
                    with open(focus_file, 'r') as f:
                        data = json.load(f)
                        if date_str in data:
                            minutes = data[date_str].get('total_time_minutes', 0)
                            year_data[date_str] = minutes
                        else:
                            year_data[date_str] = 0
                except:
                    year_data[date_str] = 0
            else:
                year_data[date_str] = 0
            
            current_date += timedelta(days=1)
        
        return year_data

    def create_heatmap(self):
        """Create GitHub-style heatmap of focus sessions"""
        year_data = self.get_year_data()
        
        # Convert to lists for july
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in year_data.keys()]
        values = list(year_data.values())
        
        # Monkey-patch matplotlib to fix july compatibility with newer matplotlib
        import matplotlib.cbook as cbook
        if not hasattr(cbook, 'MatplotlibDeprecationWarning'):
            cbook.MatplotlibDeprecationWarning = UserWarning
        
        # Create GitHub-style heatmap using july with minimal parameters
        import matplotlib.pyplot as plt
        july.heatmap(dates, values, cmap="github")
        plt.show()

    @rumps.clicked("Show Heatmap")
    def show_heatmap(self, _):
        """Open heatmap in browser"""
        self.create_heatmap()

    @rumps.clicked("Refresh")
    def refresh(self, _):
        # Rebuild all menus with fresh data
        self.create_menu()


if __name__ == "__main__":
    app = FocusApp()
    app.run()

