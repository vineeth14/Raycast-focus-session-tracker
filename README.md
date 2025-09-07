# Raycast Focus Session Tracker

A macOS menu bar application that tracks your Raycast focus sessions and displays productivity statistics with interactive heatmaps.

Monitor your focus patterns, build streaks, and visualize your productivity over time with a clean menu bar interface and GitHub-style calendar heatmaps.

## How Session Completion is Handled

The tracker accurately captures your actual focus time by intelligently processing Raycast's activity summaries. Early completions show real focus time (not planned time), cancelled sessions don't count toward totals, pause time is excluded from duration calculations, and multiple sessions per goal are tracked separately. Only completed, non-cancelled sessions contribute to daily totals and streak calculations, ensuring your statistics reflect genuine productivity.

## Installation

```bash
git clone https://github.com/vineeth14/Raycast-focus-session-tracker.git
cd Raycast-focus-session-tracker
```

then

with [uv](https://docs.astral.sh/uv/) installed you can build the project with
```bash
uv venv --python 3.11
uv pip install -e .
```

or simply run

```
pip install -e .
```

## Usage

**Setup:**
1. Open Raycast settings (Cmd+,)
2. Go to Advanced tab
3. Check "Open Raycast in developer mode"

**Start:**
```bash
raycast-tracker
```

**Stop:**
```bash
raycast-tracker-stop
```

The app displays a 🎯 icon in your menu bar showing:
- Current and longest focus streaks
- Today's total focus time
- Time breakdown by goal
- Interactive GitHub-style heatmap

## Screenshots

### Menu Bar Dropdown
<img src="images/dropdown.png" alt="Menu Bar Dropdown" width="200">

### Focus Heatmap
![Focus Heatmap](images/heatmap.png)

## Requirements

- macOS (required)
- Python 3.8+
- Raycast application with focus sessions

## Dependencies

- [rumps](https://github.com/jaredks/rumps) - macOS menu bar framework
- [lesley](https://github.com/astariul/lesley) - Calendar heatmap visualization
