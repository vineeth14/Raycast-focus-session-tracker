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

# Always prioritize the user's home directory if it has data
home_data_dir = Path.home() / ".raycast-focus-tracker" / "data"
project_data_dir = SCRIPT_DIR.parent / "data"

if home_data_dir.exists() and any(home_data_dir.glob("focus.*.json")):
    # Use home directory if it has focus data
    DATA_DIR = home_data_dir
elif project_data_dir.exists() and any(project_data_dir.glob("focus.*.json")):
    # Fall back to project directory if it has focus data
    DATA_DIR = project_data_dir
elif "site-packages" in str(SCRIPT_DIR):
    # Installed mode: use user's home directory  
    DATA_DIR = home_data_dir
else:
    # Development mode: use local data directory
    DATA_DIR = project_data_dir

# Ensure the data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_today_minutes(search_dirs=None):
    """Get today's total focus minutes.
    
    Args:
        search_dirs (list, optional): List of directories to search. Defaults to None.
    
    Returns:
        int: Total minutes focused today, 0 if no data or error.
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
                        if today in data and "total_time_minutes" in data[today]:
                            return data[today].get("total_time_minutes", 0)
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


def get_today_by_goal():
    """Get today's time breakdown by goal/category.
    
    Returns:
        dict: Mapping of goal names to minutes spent, empty if no data or error.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Check both home and project directories for today's data
        search_dirs = [
            DATA_DIR,
            Path(__file__).parent.parent / "data",  # Project data directory
            Path.home() / ".raycast-focus-tracker" / "data",  # Home directory
            Path(__file__).parent / "data"  # Package data directory
        ]
        
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

