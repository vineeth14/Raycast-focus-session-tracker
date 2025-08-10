"""Raycast Focus Tracker - macOS Menu Bar Application

Displays focus session statistics and streak data in the menu bar.
Provides access to heatmap visualization and real-time data refresh.
"""

import json
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import lesley
import rumps

from data_access import (
    get_current_streak,
    get_longest_streak,
    get_today_by_goal,
    get_today_minutes,
)
from streak_calculation import update_streaks


class FocusApp(rumps.App):
    def __init__(self):
        super().__init__("🎯")
        self.data_dir = Path(__file__).parent / "data"
        self.create_menu()

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
        update_streaks(daily_data)

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
        """Refresh all menu data."""
        self._update_menu_data()

    def _do_nothing(self, _):
        """Empty callback to make menu items appear clickable but do nothing when clicked."""
        pass


if __name__ == "__main__":
    app = FocusApp()
    app.run()

