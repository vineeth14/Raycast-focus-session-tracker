# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Raycast Focus Session Tracker** that monitors macOS focus sessions, processes them into structured data, and provides a menubar application for viewing statistics and visualizations.

## Architecture

**Data Flow Pipeline:**
1. `focus-tracker.sh` → Captures Raycast logs to file via `log stream --level debug` (WORKING)
2. `log_to_json.py` → Parses raw logs into structured JSON
3. `data_access.py` → Provides clean API for accessing focus data
4. `streak_calculation.py` → Calculates current/longest streaks
5. `menuBar.py` → macOS menubar app displaying stats and heatmaps

**Key Data Structures:**
- Raw logs: `focus.YYYY-MM-DD.log` (captured by shell script)
- Structured data: `data/focus.YYYY-MM-DD.json` (parsed by Python)
- Streaks: `data/streaks.json` (current_streak, longest_streak)

**JSON Schema Example:**
```json
{
  "2025-08-10": {
    "total_time_minutes": 25,
    "time_per_goal": {"rumps": 1, "raycast": 24},
    "items": [
      {
        "goal": "rumps",
        "start_time": "2025-08-10 14:18:11.777",
        "end_time": "2025-08-10 14:18:13.896", 
        "actual_duration": 0,
        "cancelled": false,
        "state": "completed"
      }
    ]
  }
}
```

## Common Commands

**Activate virtual environment:**
```bash
source .venv/bin/activate
```

**Install dependencies (after activating venv):**
```bash
uv pip install lesley rumps
```

**Start log capture:**
```bash
./focus-tracker.sh
```

**Parse logs to JSON:**
```bash
python3 log_to_json.py focus.2025-08-10.log data/focus.2025-08-10.json
```

**Run menubar app:**
```bash
python3 menuBar.py
```

**Test data access functions:**
```bash
python3 -c "from data_access import get_today_minutes; print(get_today_minutes())"
```

## Important Implementation Details

**Streak Logic:** Any day with >0 minutes counts as a streak day (changed from 60+ minutes requirement)

**Heatmap Implementation:** Uses `lesley` library with GitHub-style calendar visualization. Creates `focus_heatmap.html` and opens in browser. Available parameters: `cmap` (colormap like 'YlGn', 'Blues', 'Greys'), `height`, `width`, and `days_of_week` labels.

**Menu Bar Features:**
- Live streak data (auto-updates on refresh)
- Today's focus time breakdown by goal
- Interactive heatmap with tooltips showing "Time Spent Focussing Xmin"

**Dependencies:**
- `rumps` for macOS menubar integration
- `lesley` + `altair` for heatmap visualization  
- Standard Python libraries for JSON/datetime processing

**Data Directory Structure:**
```
data/
├── focus.YYYY-MM-DD.json  # Parsed focus session data
├── streaks.json           # Streak calculations
└── sessions.json          # Legacy format (fallback)
```

## Development Notes

When modifying streak calculations, update both `streak_calculation.py` and `data_access.py` (specifically `is_streak_day_today()` function).

The menubar app automatically recalculates streaks on menu refresh by collecting all `focus.*.json` files and calling `update_streaks()`.

Log parsing is stateful - the parser tracks session starts/ends across multiple log lines to match goals with completions.

## Recent Bug Fixes and Improvements

### Refresh Functionality (August 2025)
Fixed critical issues with menu bar refresh functionality where completed focus sessions weren't appearing after clicking refresh:

**Root Cause:** The `rumps` framework doesn't support reliable in-place submenu updates. The original `_update_submenu()` method was failing to refresh menu content.

**Solution:** Replaced partial menu updates with full menu rebuild approach:
- Removed `_update_submenu()` and `_update_menu_data()` methods
- Modified `refresh()` method to call `create_menu()` for complete menu reconstruction
- Updated auto-refresh timer to use full rebuilds

**Key Changes:**
1. **menuBar.py:186-199** - Enhanced `refresh()` method with comprehensive error handling and full menu rebuild
2. **menuBar.py:201-220** - Fixed `auto_refresh()` method with timer restart capability
3. **menuBar.py** - Removed problematic `_update_submenu()` method entirely

**Data Access Improvements:**
- Enhanced multi-directory data search in `data_access.py`
- Fixed data consolidation across project and home directories
- Added comprehensive debug logging for troubleshooting

**Testing:**
- Created extensive test suite with 85+ test cases covering unit, integration, and e2e scenarios
- Verified both manual refresh (click button) and auto-refresh (5-second timer) functionality
- Tests show successful data updates (e.g., 123→124 minutes detection)

### Data Structure Updates
The JSON schema now includes additional tracking fields:
```json
{
  "items": [
    {
      "goal": "Focus",
      "start_time": "2025-08-13 15:11:51.064",
      "end_time": "2025-08-13 16:19:10.557", 
      "actual_duration": 67,
      "pauses": 0,
      "blocks": 0,
      "snoozes": 0,
      "cancelled": false,
      "state": "completed"
    }
  ],
  "active_sessions": {
    "Focus_2025-08-13 15:12:04.234": {
      "goal": "Focus",
      "start_time": "2025-08-13 15:12:04.234",
      "state": "started"
    }
  }
}
```

### Testing Infrastructure
Added comprehensive testing framework:
```
tests/
├── unit/                    # Individual component tests
├── integration/            # Cross-component tests  
├── e2e/                    # End-to-end workflow tests
├── run_tests.py            # Test runner with coverage
└── fixtures/               # Sample test data
```

**Test Categories:**
- `python tests/run_tests.py unit` - Unit tests only
- `python tests/run_tests.py integration` - Integration tests
- `python tests/run_tests.py e2e` - End-to-end tests
- `python tests/run_tests.py all` - All tests with coverage

### Architecture Notes
**Multi-Directory Data Access:** The system now searches both:
- `./data/` (project directory)
- `~/.raycast-focus-tracker/data/` (home directory)

**Error Recovery:** All refresh operations include comprehensive error handling with fallback mechanisms and detailed debug logging.