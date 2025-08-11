# Raycast Focus Session Tracker

A macOS menu bar application that monitors and visualizes your Raycast focus sessions, providing insights into your productivity patterns through interactive heatmaps and real-time statistics.

## Features

- **Real-time monitoring** of Raycast focus sessions via macOS log streaming
- **Menu bar integration** showing current streak, daily totals, and goal breakdowns
- **Interactive heatmaps** with GitHub-style calendar visualization
- **Streak tracking** for consecutive days of focus activity
- **Goal categorization** to see time spent on different focus objectives

## How It Works

The tracker captures Raycast focus session logs, processes them into structured JSON data, calculates productivity streaks, and presents everything through a clean macOS menu bar interface with visual heatmaps.

## Tools & Libraries

### Core Technologies
- **[Python 3](https://www.python.org/)** - Main programming language
- **[Bash](https://www.gnu.org/software/bash/)** - Log capture scripting
- **[macOS Log Streaming](https://developer.apple.com/documentation/os/logging)** - Real-time log capture

### Python Libraries
- **[rumps](https://github.com/jaredks/rumps)** - macOS menu bar application framework
- **[lesley](https://github.com/astariul/lesley)** - Calendar heatmap visualization library
- **[altair](https://altair-viz.github.io/)** - Declarative statistical visualization (used by lesley)
- **[pandas](https://pandas.pydata.org/)** - Data manipulation and analysis

### Data Processing
- **JSON** - Structured data storage and parsing
- **Regular expressions** - Log parsing and pattern matching
- **Datetime** - Time calculations and streak logic

## Quick Start

1. **Start log capture:**
   ```bash
   ./focus-tracker.sh
   ```

2. **Run menu bar app:**
   ```bash
   python3 menuBar.py
   ```

3. **View heatmap** - Click "Show Heatmap" in the menu bar

## File Structure

```
├── focus-tracker.sh      # Log capture script
├── menuBar.py           # Menu bar application
├── log_to_json.py       # Log parser
├── data_access.py       # Data access layer
├── streak_calculation.py # Streak logic
└── data/                # JSON data storage
    ├── focus.*.json     # Daily focus data
    └── streaks.json     # Streak statistics
```

Built for productivity enthusiasts who want to track and visualize their focus patterns on macOS.