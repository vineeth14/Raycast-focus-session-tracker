#!/usr/bin/env python3
"""Quick access functions for focus data - perfect for menubar apps"""

import json
import os
from datetime import datetime
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"


def get_today_minutes():
    """Get today's total focus minutes"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        # Check the focus file first (this has the right structure)
        focus_file = DATA_DIR / f"focus.{today}.json"
        if focus_file.exists():
            with open(focus_file, "r") as f:
                data = json.load(f)
                if today in data:
                    return data[today].get("total_time_minutes", 0)
        return 0
    except Exception as e:
        print(f"Error accessing today's minutes: {e}")
        return 0


def get_current_streak():
    """Get current focus streak days"""
    try:
        # Try possible streak files
        possible_files = [
            DATA_DIR / "streaks.json",
            DATA_DIR / "sessions.json"  # Might be in here
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if "current_streak" in data:
                        return data.get("current_streak", 0)
        return 0
    except Exception as e:
        print(f"Error accessing current streak: {e}")
        return 0


def get_longest_streak():
    """Get longest focus streak ever"""
    try:
        # Try possible streak files
        possible_files = [
            DATA_DIR / "streaks.json",
            DATA_DIR / "sessions.json"  # Might be in here
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if "longest_streak" in data:
                        return data.get("longest_streak", 0)
        return 0
    except Exception as e:
        print(f"Error accessing longest streak: {e}")
        return 0


def get_today_by_goal():
    """Get today's time breakdown by goal/category"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        # Check the focus file (this has the right structure)
        focus_file = DATA_DIR / f"focus.{today}.json"
        if focus_file.exists():
            with open(focus_file, "r") as f:
                data = json.load(f)
                if today in data:
                    return data[today].get("time_per_goal", {})
        return {}
    except Exception as e:
        print(f"Error accessing today's goals: {e}")
        return {}


def get_today_session_count():
    """Get number of completed sessions today"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        file_path = DATA_DIR / f"{today}.json"
        with open(file_path, "r") as f:
            data = json.load(f)
            items = data.get(today, {}).get("items", [])
            return len([item for item in items if not item.get("cancelled", False)])
    except:
        return 0


def is_streak_day_today():
    """Check if today qualifies as a streak day (>= 60 minutes)"""
    return get_today_minutes() >= 60


def get_today_summary():
    """Get complete today summary in one call"""
    return {
        "minutes": get_today_minutes(),
        "sessions": get_today_session_count(),
        "by_goal": get_today_by_goal(),
        "is_streak_day": is_streak_day_today(),
        "current_streak": get_current_streak(),
    }

