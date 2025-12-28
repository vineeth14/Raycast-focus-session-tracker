# Raycast Focus Tracker

macOS menu bar app that tracks Raycast focus sessions and displays productivity statistics.

## Architecture

```
Raycast App → focus-tracker.sh → log_to_json.py → data_access.py → menuBar.py
   (logs)        (capture)          (parse)         (read)         (display)
```

## Core Files

### `raycast_focus_tracker/`

| File | Purpose |
|------|---------|
| `menuBar.py` | RUMPS menu bar app - displays stats, auto-refreshes every 5s |
| `log_to_json.py` | Parses Raycast logs → JSON with sessions, durations, goals |
| `data_access.py` | Data layer - `get_today_minutes()`, `get_current_streak()` |
| `streak_calculation.py` | Calculates current/longest streaks from daily data |
| `daemon_launcher.py` | Entry point: `raycast-tracker` command |
| `stop_tracker.py` | Entry point: `raycast-tracker-stop` command |
| `focus-tracker.sh` | Streams macOS logs for Raycast focus events |

## Data Structures

### Session (in `focus.YYYY-MM-DD.json`)
```json
{
  "2025-12-27": {
    "total_time_minutes": 120,
    "time_per_goal": {"leetcode": 80, "reading": 40},
    "items": [{
      "goal": "leetcode",
      "start_time": "2025-12-27 09:00:00.000",
      "end_time": "2025-12-27 10:20:00.000",
      "actual_duration": 80,
      "state": "completed",
      "cancelled": false,
      "pauses": 1
    }],
    "active_sessions": {}
  }
}
```

### Streaks (in `streaks.json`)
```json
{"current_streak": 5, "longest_streak": 12}
```

## Key Functions

### log_to_json.py
- `parse_log_file(log_path, json_path)` - Main parser entry point
- `handle_session_start/end()` - Process session lifecycle
- `recalculate_daily_totals()` - Aggregate time per goal
- `_should_count_session()` - Returns true if completed and not cancelled

### data_access.py
- `get_today_minutes()` - Today's total focus time
- `get_today_by_goal()` - Dict of goal → minutes
- `get_current_streak()` / `get_longest_streak()` - Streak stats

### streak_calculation.py
- `update_streaks(daily_data)` - Recalculate and save streaks
- `_calculate_current_streak()` - Count consecutive days with >0 minutes

## Data Directories

- Development: `./logs/`, `./data/`
- Installed: `~/.raycast-focus-tracker/logs/`, `~/.raycast-focus-tracker/data/`

## Log Format (from Raycast)

```
2025-12-27 09:00:00.000 I [focus] Start focus session
Goal: leetcode
Duration: 3600
...
2025-12-27 10:00:00.000 I [focus] Complete focus session
...
2025-12-27 10:00:00.100 I [focus] Focus session activity summary
Duration: 60 minutes
Pauses Count: 1
```

## Commands

```bash
raycast-tracker       # Start menu bar app
raycast-tracker-stop  # Stop all tracker processes
```

## Dependencies

- `rumps` - macOS menu bar framework
- `lesley` - Calendar heatmap generation
