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
    try:
        streak_file = Path(path)
        if streak_file.exists():
            with open(streak_file, "r") as f:
                data = json.load(f)
                # Validate the JSON structure
                if isinstance(data, dict) and "current_streak" in data and "longest_streak" in data:
                    return data
                else:
                    # Invalid JSON structure, return default
                    return {"current_streak": 0, "longest_streak": 0}
    except (json.JSONDecodeError, PermissionError, OSError):
        # Handle invalid JSON, permission errors, or other file access issues
        pass
    return {"current_streak": 0, "longest_streak": 0}


def save_streaks(streaks, path="data/streaks.json"):
    """Save streak data to file.
    
    Args:
        streaks (dict): Streak data to save
        path (str): Path to output file
    """
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(streaks, f, indent=2)
    except (PermissionError, OSError, IOError):
        # Silently handle permission errors and other file access issues
        # This allows the application to continue working even if file write fails
        pass


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
    from datetime import datetime, timedelta
    
    if not daily_data:
        return 0
    
    # Find the most recent date in our data
    most_recent_date = max(daily_data.keys())
    current_date = datetime.strptime(most_recent_date, "%Y-%m-%d")
    current_streak = 0
    
    # Work backwards day by day checking calendar continuity
    while True:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Check if we have data for this date
        if date_str in daily_data:
            day_data = daily_data[date_str]
            total_time = day_data.get("total_time_minutes")
            
            # Handle case where total_time_minutes might be missing or None
            if total_time is None:
                # If total_time_minutes is missing, calculate from time_per_goal
                time_per_goal = day_data.get("time_per_goal", {})
                total_time = sum(time_per_goal.values()) if time_per_goal else 0
                
            if total_time > 0:
                current_streak += 1
            else:
                # Day exists but has 0 minutes - streak broken
                break
        else:
            # Missing day - treat as 0 minutes, streak broken
            break
        
        # Move to previous day
        current_date -= timedelta(days=1)
    
    return current_streak
