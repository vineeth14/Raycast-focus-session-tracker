#!/usr/bin/env python3
"""Focus Streak Calculation Module

Calculates and maintains focus streak statistics based on daily focus data.
A streak day is defined as any day with >0 minutes of focus activity.
"""

import json
from pathlib import Path


def load_streaks(path="data/streaks.json"):
    """Load existing streak data from file.
    
    Args:
        path (str): Path to streaks JSON file
        
    Returns:
        dict: Streak data with current_streak and longest_streak keys
    """
    streak_file = Path(path)
    if streak_file.exists():
        with open(streak_file, "r") as f:
            return json.load(f)
    return {"current_streak": 0, "longest_streak": 0}


def save_streaks(streaks, path="data/streaks.json"):
    """Save streak data to file.
    
    Args:
        streaks (dict): Streak data to save
        path (str): Path to output file
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(streaks, f, indent=2)


def update_streaks(daily_data, streaks_path="data/streaks.json"):
    """Update streak statistics based on daily focus data.
    
    Args:
        daily_data (dict): Daily focus data keyed by date (YYYY-MM-DD)
        streaks_path (str): Path to streaks file
        
    Returns:
        dict: Updated streak data
    """
    streaks = load_streaks(streaks_path)
    
    current_streak = _calculate_current_streak(daily_data)
    previous_current = streaks.get("current_streak", 0)
    
    # Update current_streak in memory
    streaks["current_streak"] = current_streak
    
    # Only save to file if current_streak actually changed or longest_streak improved
    should_save = False
    if current_streak != previous_current:
        should_save = True
        
    # Only update longest_streak if this is a NEW record
    if current_streak > streaks["longest_streak"]:
        streaks["longest_streak"] = current_streak
        should_save = True
        
    if should_save:
        save_streaks(streaks, streaks_path)
    
    return streaks


def _calculate_current_streak(daily_data):
    """Calculate current consecutive streak days.
    
    Args:
        daily_data (dict): Daily focus data keyed by date
        
    Returns:
        int: Current streak length in days
    """
    current_streak = 0
    
    for date in reversed(sorted(daily_data.keys())):
        if daily_data[date].get("total_time_minutes", 0) > 0:
            current_streak += 1
        else:
            break
    
    return current_streak
