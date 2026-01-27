#!/usr/bin/env python3
"""Data Access Layer for Focus Session Data

Provides clean, consistent access to focus session data for menu bar
applications and other consumers. Handles file I/O and error cases gracefully.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# --- Dynamic Directory Configuration ---
# Get the path to the script's directory
SCRIPT_DIR = Path(__file__).parent

# Detect dev mode same way as focus-tracker.sh: check for pyproject.toml or setup.py
project_root = SCRIPT_DIR.parent
IS_DEV_MODE = (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists()

if IS_DEV_MODE:
    # Development mode: use project directory for everything
    DATA_DIR = project_root / "data"
    LOG_DIR = project_root / "logs"
else:
    # Installed mode: use home directory
    DATA_DIR = Path.home() / ".raycast-focus-tracker" / "data"
    LOG_DIR = Path.home() / ".raycast-focus-tracker" / "logs"

# Ensure the data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_today_minutes(search_dirs=None):
    """Get today's total focus minutes including active sessions.

    Args:
        search_dirs (list, optional): List of directories to search. Defaults to None.

    Returns:
        int: Total minutes focused today (completed + active), 0 if no data or error.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if search_dirs is None:
        search_dirs = [
            DATA_DIR,
            Path(__file__).parent.parent / "data",  # Project data directory
            Path.home() / ".raycast-focus-tracker" / "data",  # Home directory
            Path(__file__).parent / "data"  # Package data directory
        ]

    try:
        for data_dir in search_dirs:
            if not data_dir.exists():
                continue
            for focus_file in data_dir.glob("focus.*.json"):
                try:
                    with open(focus_file, "r") as f:
                        data = json.load(f)
                        if today in data:
                            completed_minutes = data[today].get("total_time_minutes", 0)

                            # Add time from active sessions
                            active_minutes = 0
                            active_sessions = data[today].get("active_sessions", {})
                            now = datetime.now()
                            for session in active_sessions.values():
                                start_str = session.get("start_time", "")
                                if start_str:
                                    try:
                                        start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S.%f")
                                        elapsed = (now - start_time).total_seconds() / 60
                                        active_minutes += int(elapsed)
                                    except ValueError:
                                        pass

                            return completed_minutes + active_minutes
                except (json.JSONDecodeError, KeyError, PermissionError):
                    continue  # Skip invalid files
    except Exception as e:
        print(f"Error accessing today's minutes: {e}")

    return 0


def get_current_streak():
    """Get current focus streak in days.
    
    Returns:
        int: Current consecutive days with focus activity, 0 if none or error.
    """
    return _get_streak_value("current_streak")


def get_longest_streak():
    """Get longest focus streak ever achieved.
    
    Returns:
        int: Longest consecutive days with focus activity, 0 if none or error.
    """
    return _get_streak_value("longest_streak")


def get_today_by_goal(search_dirs=None):
    """Get today's time breakdown by goal/category.

    Args:
        search_dirs (list, optional): List of directories to search. Defaults to None.

    Returns:
        dict: Mapping of goal names to minutes spent, empty if no data or error.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if search_dirs is None:
        search_dirs = [
            DATA_DIR,
            Path(__file__).parent.parent / "data",  # Project data directory
            Path.home() / ".raycast-focus-tracker" / "data",  # Home directory
            Path(__file__).parent / "data"  # Package data directory
        ]

    try:
        for data_dir in search_dirs:
            if not data_dir.exists():
                continue
            for focus_file in data_dir.glob("focus.*.json"):
                try:
                    with open(focus_file, "r") as f:
                        data = json.load(f)
                        if today in data and "time_per_goal" in data[today]:
                            return data[today].get("time_per_goal", {})
                except (json.JSONDecodeError, KeyError, PermissionError):
                    continue  # Skip invalid files
    except Exception as e:
        print(f"Error accessing today's goals: {e}")

    return {}


def get_week_minutes(week_offset=0):
    """Get total focus minutes for the current week (Monday-Sunday).

    Args:
        week_offset (int): 0 for current week, -1 for last week, etc.

    Returns:
        int: Total minutes focused this week.
    """
    from datetime import timedelta
    today = datetime.now().date()
    # Find Monday of the target week
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday) + timedelta(weeks=week_offset)

    total = 0
    for i in range(7):
        day = monday + timedelta(days=i)
        if day > today:
            break
        total += _get_day_minutes(day.strftime("%Y-%m-%d"))
    return total


def get_week_by_goal(week_offset=0):
    """Get week's time breakdown by goal.

    Args:
        week_offset (int): 0 for current week, -1 for last week, etc.

    Returns:
        dict: Mapping of goal names to minutes spent.
    """
    from datetime import timedelta
    today = datetime.now().date()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday) + timedelta(weeks=week_offset)

    totals = {}
    for i in range(7):
        day = monday + timedelta(days=i)
        if day > today:
            break
        day_goals = _get_day_by_goal(day.strftime("%Y-%m-%d"))
        for goal, minutes in day_goals.items():
            totals[goal] = totals.get(goal, 0) + minutes
    return totals


def get_week_by_day(week_offset=0):
    """Get week's data broken down by day with goals.

    Args:
        week_offset (int): 0 for current week, -1 for last week, etc.

    Returns:
        list: List of dicts with day info: {date, day_name, total, goals}
    """
    from datetime import timedelta
    today = datetime.now().date()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday) + timedelta(weeks=week_offset)

    days = []
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for i in range(7):
        day = monday + timedelta(days=i)
        if day > today:
            break
        date_str = day.strftime("%Y-%m-%d")
        total = _get_day_minutes(date_str)
        goals = _get_day_by_goal(date_str)

        days.append({
            "date": date_str,
            "day_name": day_names[i],
            "total": total,
            "goals": goals
        })

    return days


def get_month_minutes(month_offset=0):
    """Get total focus minutes for the current month.

    Args:
        month_offset (int): 0 for current month, -1 for last month, etc.

    Returns:
        int: Total minutes focused this month.
    """
    from datetime import timedelta
    today = datetime.now().date()

    # Calculate target month
    year = today.year
    month = today.month + month_offset
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1

    # First day of target month
    first_day = today.replace(year=year, month=month, day=1)

    # Last day to check (today if current month, else end of month)
    if year == today.year and month == today.month:
        last_day = today
    else:
        # Find last day of target month
        if month == 12:
            last_day = first_day.replace(year=year+1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=month+1, day=1) - timedelta(days=1)

    total = 0
    current = first_day
    while current <= last_day:
        total += _get_day_minutes(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return total


def get_month_by_goal(month_offset=0):
    """Get month's time breakdown by goal.

    Args:
        month_offset (int): 0 for current month, -1 for last month, etc.

    Returns:
        dict: Mapping of goal names to minutes spent.
    """
    from datetime import timedelta
    today = datetime.now().date()

    year = today.year
    month = today.month + month_offset
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1

    first_day = today.replace(year=year, month=month, day=1)

    if year == today.year and month == today.month:
        last_day = today
    else:
        if month == 12:
            last_day = first_day.replace(year=year+1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=month+1, day=1) - timedelta(days=1)

    totals = {}
    current = first_day
    while current <= last_day:
        day_goals = _get_day_by_goal(current.strftime("%Y-%m-%d"))
        for goal, minutes in day_goals.items():
            totals[goal] = totals.get(goal, 0) + minutes
        current += timedelta(days=1)
    return totals


def _get_day_minutes(date_str):
    """Get total minutes for a specific date.

    Args:
        date_str (str): Date in YYYY-MM-DD format.

    Returns:
        int: Total minutes for that date.
    """
    search_dirs = [
        DATA_DIR,
        Path(__file__).parent.parent / "data",
        Path.home() / ".raycast-focus-tracker" / "data",
        Path(__file__).parent / "data"
    ]

    try:
        for data_dir in search_dirs:
            if not data_dir.exists():
                continue
            for focus_file in data_dir.glob("focus.*.json"):
                try:
                    with open(focus_file, "r") as f:
                        data = json.load(f)
                        if date_str in data and "total_time_minutes" in data[date_str]:
                            return data[date_str].get("total_time_minutes", 0)
                except (json.JSONDecodeError, KeyError, PermissionError):
                    continue
    except Exception:
        pass
    return 0


def _get_day_by_goal(date_str):
    """Get goal breakdown for a specific date.

    Args:
        date_str (str): Date in YYYY-MM-DD format.

    Returns:
        dict: Mapping of goal names to minutes.
    """
    search_dirs = [
        DATA_DIR,
        Path(__file__).parent.parent / "data",
        Path.home() / ".raycast-focus-tracker" / "data",
        Path(__file__).parent / "data"
    ]

    try:
        for data_dir in search_dirs:
            if not data_dir.exists():
                continue
            for focus_file in data_dir.glob("focus.*.json"):
                try:
                    with open(focus_file, "r") as f:
                        data = json.load(f)
                        if date_str in data and "time_per_goal" in data[date_str]:
                            return data[date_str].get("time_per_goal", {})
                except (json.JSONDecodeError, KeyError, PermissionError):
                    continue
    except Exception:
        pass
    return {}


def _get_streak_value(streak_type):
    """Helper function to get streak values from possible files.

    Args:
        streak_type (str): Either 'current_streak' or 'longest_streak'

    Returns:
        int: Streak value, 0 if not found or error.
    """
    # Check multiple possible locations for streak files
    search_dirs = [
        DATA_DIR,
        Path(__file__).parent.parent / "data",  # Project data directory
        Path.home() / ".raycast-focus-tracker" / "data",  # Home directory
        Path(__file__).parent / "data"  # Package data directory
    ]
    
    try:
        for data_dir in search_dirs:
            if not data_dir.exists():
                continue
            possible_files = [
                data_dir / "streaks.json",
                data_dir / "sessions.json"  # Legacy fallback
            ]
            
            for file_path in possible_files:
                if file_path.exists():
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            if streak_type in data:
                                return data.get(streak_type, 0)
                    except (json.JSONDecodeError, KeyError, PermissionError):
                        continue  # Skip invalid files
    except Exception as e:
        print(f"Error accessing {streak_type}: {e}")
    
    return 0

