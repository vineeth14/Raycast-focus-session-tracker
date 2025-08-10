#!/usr/bin/env python3
"""Simple focus streak tracker"""

import json
from pathlib import Path


def load_streaks(path="data/streaks.json"):
    if Path(path).exists():
        with open(path, "r") as f:
            return json.load(f)
    return {"current_streak": 0, "longest_streak": 0}


def save_streaks(streaks, path="data/streaks.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(streaks, f, indent=2)


def update_streaks(daily_data, streaks_path="data/streaks.json"):
    streaks = load_streaks(streaks_path)

    # Count current streak from end
    current_streak = 0
    for date in reversed(sorted(daily_data.keys())):
        if daily_data[date].get("total_time_minutes", 0) >= 60:
            current_streak += 1
        else:
            break

    # Update streaks
    streaks["current_streak"] = current_streak
    streaks["longest_streak"] = max(streaks["longest_streak"], current_streak)

    save_streaks(streaks, streaks_path)
    return streaks
