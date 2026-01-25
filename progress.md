# Heatmap Migration: lesley -> plotly-calplot

## Requirements
- [x] Rolling 12-month window (like GitHub)
- [ ] Navigation buttons to move backward/forward through time
- [ ] Grey boxes for days with no data
- [ ] Preserve all historical data (display change only)
- [ ] Interactive HTML output

## Implementation Steps

### Phase 1: Setup
- [x] Add `plotly-calplot` to requirements.txt
- [x] Convert project to uv with pyproject.toml
- [x] Update imports in menuBar.py

### Phase 2: Core Heatmap Changes
- [x] Modify `_create_heatmap()` to use plotly-calplot
- [x] Implement rolling 12-month date range calculation
- [x] Configure colorscale with grey for zero/no-data days
- [x] Update `_generate_year_data()` -> `_generate_rolling_year_data()`

### Phase 3: Navigation Feature
- [x] Add HTML/JS navigation controls (Previous/Next buttons)
- [x] Store current window offset in the heatmap
- [x] Enable moving backward through historical data
- [x] Enable moving forward (up to today)

### Phase 4: Testing & Cleanup
- [x] Test with existing data files
- [x] Verify all dates display correctly
- [ ] Test navigation through multiple time periods (manual testing)
- [ ] Remove lesley dependency (optional, after verification)

## Progress Log
| Date | Task | Status |
|------|------|--------|
| 2026-01-22 | Convert project to uv | Done |
| 2026-01-22 | Implement plotly-calplot heatmap | Done |
| 2026-01-22 | Add rolling 12-month window | Done |
| 2026-01-22 | Add navigation controls | Done |

## Notes
- Data files remain unchanged (focus.YYYY-MM-DD.json)
- Only the visualization method changes
- HTML output path stays the same: focus_heatmap.html
