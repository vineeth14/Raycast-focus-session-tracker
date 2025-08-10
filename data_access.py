#!/usr/bin/env python3
"""Quick access functions for focus data - perfect for menubar apps"""

import json
from datetime import datetime


def get_today_minutes():
    """Get today's total focus minutes"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        with open(f"data/{today}.json", "r") as f:
            data = json.load(f)
            return data.get(today, {}).get("total_time_minutes", 0)
    except:
        return 0


def get_current_streak():
    """Get current focus streak days"""
    try:
        with open("data/streaks.json", "r") as f:
            return json.load(f).get("current_streak", 0)
    except:
        return 0


def get_longest_streak():
    """Get longest focus streak ever"""
    try:
        with open("data/streaks.json", "r") as f:
            return json.load(f).get("longest_streak", 0)
    except:
        return 0


def get_today_by_goal():
    """Get today's time breakdown by goal/category"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        with open(f"data/{today}.json", "r") as f:
            data = json.load(f)
            return data.get(today, {}).get("time_per_goal", {})
    except:
        return {}


def get_today_session_count():
    """Get number of completed sessions today"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        with open(f"data/{today}.json", "r") as f:
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

