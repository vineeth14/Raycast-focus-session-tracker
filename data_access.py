#!/usr/bin/env python3
"""Data Access Layer for Focus Session Data

Provides clean, consistent access to focus session data for menu bar
applications and other consumers. Handles file I/O and error cases gracefully.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def get_today_minutes():
    """Get today's total focus minutes.
    
    Returns:
        int: Total minutes focused today, 0 if no data or error.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    focus_file = DATA_DIR / f"focus.{today}.json"
    
    try:
        if focus_file.exists():
            with open(focus_file, "r") as f:
                data = json.load(f)
                return data.get(today, {}).get("total_time_minutes", 0)
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


def get_today_by_goal():
    """Get today's time breakdown by goal/category.
    
    Returns:
        dict: Mapping of goal names to minutes spent, empty if no data or error.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    focus_file = DATA_DIR / f"focus.{today}.json"
    
    try:
        if focus_file.exists():
            with open(focus_file, "r") as f:
                data = json.load(f)
                return data.get(today, {}).get("time_per_goal", {})
    except Exception as e:
        print(f"Error accessing today's goals: {e}")
    
    return {}


def _get_streak_value(streak_type):
    """Helper function to get streak values from possible files.
    
    Args:
        streak_type (str): Either 'current_streak' or 'longest_streak'
    
    Returns:
        int: Streak value, 0 if not found or error.
    """
    possible_files = [
        DATA_DIR / "streaks.json",
        DATA_DIR / "sessions.json"  # Legacy fallback
    ]
    
    try:
        for file_path in possible_files:
            if file_path.exists():
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if streak_type in data:
                        return data.get(streak_type, 0)
    except Exception as e:
        print(f"Error accessing {streak_type}: {e}")
    
    return 0

