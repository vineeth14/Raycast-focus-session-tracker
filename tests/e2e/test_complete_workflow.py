"""End-to-end tests for the complete Raycast Focus Tracker workflow."""

import json
import subprocess
import tempfile
import shutil
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import time

# Import modules for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCompleteWorkflow:
    """End-to-end tests that simulate the complete user workflow."""

    def test_log_to_json_to_menubar_workflow(self, temp_data_dir):
        """Test the complete workflow from log file to menu bar display."""
        # Setup
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create realistic log content
        log_content = f"""
{today} 09:00:00.123 Raycast Extension Host[1234]: Start focus session
{today} 09:00:01.456 Raycast Extension Host[1234]: Goal: morning_coding
{today} 09:25:00.789 Raycast Extension Host[1234]: Complete focus session
{today} 09:25:01.000 Raycast Extension Host[1234]: Focus session activity summary
{today} 09:25:01.001 Raycast Extension Host[1234]: Start date: {today} 09:00:00
{today} 09:25:01.002 Raycast Extension Host[1234]: Duration: 25 minutes
{today} 09:25:01.003 Raycast Extension Host[1234]: Pauses Count: 1
{today} 09:25:01.004 Raycast Extension Host[1234]: Block Events Count: 0
{today} 09:25:01.005 Raycast Extension Host[1234]: Snooze Events Count: 0
{today} 14:00:00.100 Raycast Extension Host[1234]: Restoring stored form state
{today} 14:00:00.200 Raycast Extension Host[1234]: Start focus session
{today} 14:00:01.300 Raycast Extension Host[1234]: Goal: afternoon_review
{today} 14:35:00.400 Raycast Extension Host[1234]: Complete focus session
{today} 14:35:01.500 Raycast Extension Host[1234]: Focus session activity summary
{today} 14:35:01.501 Raycast Extension Host[1234]: Start date: {today} 14:00:00
{today} 14:35:01.502 Raycast Extension Host[1234]: Duration: 35 minutes
{today} 14:35:01.503 Raycast Extension Host[1234]: Pauses Count: 0
{today} 14:35:01.504 Raycast Extension Host[1234]: Block Events Count: 2
{today} 14:35:01.505 Raycast Extension Host[1234]: Snooze Events Count: 1
        """.strip()
        
        # Create log file
        log_file = temp_data_dir / f"focus.{today}.log"
        with open(log_file, 'w') as f:
            f.write(log_content)
        
        json_file = temp_data_dir / f"focus.{today}.json"
        
        # Step 1: Parse log to JSON
        from raycast_focus_tracker.log_to_json import parse_log_file
        result = parse_log_file(str(log_file), str(json_file))
        
        # Verify JSON was created correctly
        assert json_file.exists()
        assert result is not None
        assert today in result
        
        day_data = result[today]
        assert day_data["total_time_minutes"] == 60  # 25 + 35
        assert day_data["time_per_goal"] == {"morning_coding": 25, "afternoon_review": 35}
        assert len(day_data["items"]) == 2
        
        # Verify session details
        sessions = day_data["items"]
        morning_session = next(s for s in sessions if s["goal"] == "morning_coding")
        afternoon_session = next(s for s in sessions if s["goal"] == "afternoon_review")
        
        assert morning_session["actual_duration"] == 25
        assert morning_session["pauses"] == 1
        assert afternoon_session["actual_duration"] == 35
        assert afternoon_session["blocks"] == 2
        assert afternoon_session["snoozes"] == 1
        
        # Step 2: Test data access functions
        with patch_data_dir(temp_data_dir):
            from raycast_focus_tracker.data_access import get_today_minutes, get_today_by_goal
            
            minutes = get_today_minutes()
            goals = get_today_by_goal()
            
            assert minutes == 60
            assert goals == {"morning_coding": 25, "afternoon_review": 35}
        
        # Step 3: Test streak calculation
        from raycast_focus_tracker.streak_calculation import update_streaks
        streaks_file = temp_data_dir / "streaks.json"
        
        streaks = update_streaks(result, str(streaks_file))
        assert streaks["current_streak"] == 1
        assert streaks["longest_streak"] == 1
        
        # Step 4: Add more days to test streak calculation
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result[yesterday] = {
            "total_time_minutes": 30,
            "time_per_goal": {"coding": 30},
            "items": []
        }
        
        streaks = update_streaks(result, str(streaks_file))
        assert streaks["current_streak"] == 2
        assert streaks["longest_streak"] == 2

    def test_multi_day_streak_workflow(self, temp_data_dir):
        """Test workflow with multiple days of data to verify streak calculations."""
        # Create 5 days of focus data
        base_date = datetime.now() - timedelta(days=4)
        focus_data = {}
        
        for i in range(5):
            date = base_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Skip day 2 to test streak breaking
            if i == 2:
                focus_data[date_str] = {
                    "total_time_minutes": 0,
                    "time_per_goal": {},
                    "items": []
                }
            else:
                minutes = 25 + (i * 5)
                focus_data[date_str] = {
                    "total_time_minutes": minutes,
                    "time_per_goal": {"work": minutes},
                    "items": [
                        {
                            "goal": "work",
                            "start_time": f"{date_str} 10:00:00.000",
                            "end_time": f"{date_str} 10:{minutes:02d}:00.000",
                            "actual_duration": minutes,
                            "cancelled": False,
                            "state": "completed"
                        }
                    ]
                }
        
        # Save to JSON files
        for date_str, data in focus_data.items():
            json_file = temp_data_dir / f"focus.{date_str}.json"
            with open(json_file, 'w') as f:
                json.dump({date_str: data}, f, indent=2)
        
        # Test streak calculation
        from raycast_focus_tracker.streak_calculation import update_streaks
        streaks_file = temp_data_dir / "streaks.json"
        
        streaks = update_streaks(focus_data, str(streaks_file))
        
        # Should have current streak of 2 (last 2 days) and longest of 2 (first 2 days)
        assert streaks["current_streak"] == 2
        assert streaks["longest_streak"] == 2

    def test_error_recovery_workflow(self, temp_data_dir):
        """Test that the system handles errors gracefully and can recover."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Test 1: Malformed log file
        malformed_log = temp_data_dir / f"malformed.{today}.log"
        with open(malformed_log, 'w') as f:
            f.write("This is not a valid log file\nWith random content\n")
        
        json_file = temp_data_dir / f"malformed.{today}.json"
        
        from raycast_focus_tracker.log_to_json import parse_log_file
        result = parse_log_file(str(malformed_log), str(json_file))
        
        # Should not crash and should return empty but valid structure
        assert result is not None
        assert isinstance(result, dict)
        
        # Test 2: Corrupted JSON file recovery
        corrupted_json = temp_data_dir / "corrupted.json"
        with open(corrupted_json, 'w') as f:
            f.write("{ invalid json content")
        
        from raycast_focus_tracker.streak_calculation import load_streaks
        streaks = load_streaks(str(corrupted_json))
        
        # Should return default values
        assert streaks == {"current_streak": 0, "longest_streak": 0}
        
        # Test 3: Missing data directory
        missing_dir = temp_data_dir / "nonexistent"

        from raycast_focus_tracker.data_access import get_today_minutes, get_today_by_goal

        # Should not crash and should return default values
        # Use search_dirs to isolate from real data on disk
        assert get_today_minutes(search_dirs=[missing_dir]) == 0
        assert get_today_by_goal(search_dirs=[missing_dir]) == {}

    def test_concurrent_session_workflow(self, temp_data_dir):
        """Test handling of concurrent or overlapping sessions."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create log with overlapping sessions (simulating user canceling and restarting)
        log_content = f"""
{today} 09:00:00.123 Raycast Extension Host[1234]: Start focus session
{today} 09:00:01.456 Raycast Extension Host[1234]: Goal: work
{today} 09:10:00.789 Raycast Extension Host[1234]: Cancel focus session
{today} 09:10:05.000 Raycast Extension Host[1234]: Focus session activity summary
{today} 09:10:05.001 Raycast Extension Host[1234]: Duration: 10 minutes
{today} 09:15:00.100 Raycast Extension Host[1234]: Restoring stored form state
{today} 09:15:00.200 Raycast Extension Host[1234]: Start focus session
{today} 09:15:01.300 Raycast Extension Host[1234]: Goal: work
{today} 10:00:00.400 Raycast Extension Host[1234]: Complete focus session
{today} 10:00:01.500 Raycast Extension Host[1234]: Focus session activity summary
{today} 10:00:01.502 Raycast Extension Host[1234]: Duration: 45 minutes
        """.strip()
        
        log_file = temp_data_dir / f"concurrent.{today}.log"
        with open(log_file, 'w') as f:
            f.write(log_content)
        
        json_file = temp_data_dir / f"concurrent.{today}.json"
        
        from raycast_focus_tracker.log_to_json import parse_log_file
        result = parse_log_file(str(log_file), str(json_file))
        
        assert result is not None
        day_data = result[today]
        
        # Should have 2 sessions: 1 cancelled, 1 completed
        assert len(day_data["items"]) == 2
        
        # Only the completed session should count toward total
        assert day_data["total_time_minutes"] == 45
        assert day_data["time_per_goal"]["work"] == 45
        
        # Check session states
        sessions = day_data["items"]
        cancelled_session = next(s for s in sessions if s["cancelled"])
        completed_session = next(s for s in sessions if not s["cancelled"])
        
        assert cancelled_session["actual_duration"] == 10
        assert completed_session["actual_duration"] == 45

    def test_large_dataset_performance(self, temp_data_dir):
        """Test system performance with large amounts of data."""
        # Create 100 days of data with multiple sessions per day
        base_date = datetime.now() - timedelta(days=99)
        
        large_data = {}
        for i in range(100):
            date = base_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Create 3-5 sessions per day
            sessions_count = 3 + (i % 3)
            total_minutes = 0
            time_per_goal = {}
            items = []
            
            for j in range(sessions_count):
                goal = f"goal_{j % 3}"  # Rotate between 3 different goals
                minutes = 15 + (j * 10)
                total_minutes += minutes
                time_per_goal[goal] = time_per_goal.get(goal, 0) + minutes
                
                items.append({
                    "goal": goal,
                    "start_time": f"{date_str} {9 + j}:00:00.000",
                    "end_time": f"{date_str} {9 + j}:{minutes:02d}:00.000",
                    "actual_duration": minutes,
                    "cancelled": False,
                    "state": "completed",
                    "pauses": j,
                    "blocks": 0,
                    "snoozes": 0
                })
            
            large_data[date_str] = {
                "total_time_minutes": total_minutes,
                "time_per_goal": time_per_goal,
                "items": items
            }
        
        # Test streak calculation performance
        from raycast_focus_tracker.streak_calculation import update_streaks
        streaks_file = temp_data_dir / "large_streaks.json"
        
        start_time = time.time()
        streaks = update_streaks(large_data, str(streaks_file))
        end_time = time.time()
        
        # Should complete in reasonable time (< 1 second for 100 days)
        assert end_time - start_time < 1.0
        
        # Should calculate correct streak (all 100 days have focus time)
        assert streaks["current_streak"] == 100
        assert streaks["longest_streak"] == 100
        
        # Test data access with large dataset
        # Create JSON file with all data (name must match focus.*.json glob)
        large_json = temp_data_dir / "focus.large.json"
        with open(large_json, 'w') as f:
            json.dump(large_data, f)

        from raycast_focus_tracker.data_access import get_today_minutes, get_today_by_goal

        # Should still work efficiently
        # Use search_dirs to isolate from real data on disk
        start_time = time.time()
        minutes = get_today_minutes(search_dirs=[temp_data_dir])
        goals = get_today_by_goal(search_dirs=[temp_data_dir])
        end_time = time.time()

        # Should complete quickly
        assert end_time - start_time < 0.1

        # Should return today's data correctly
        today = datetime.now().strftime("%Y-%m-%d")
        if today in large_data:
            assert minutes == large_data[today]["total_time_minutes"]
            assert goals == large_data[today]["time_per_goal"]

    def test_data_migration_workflow(self, temp_data_dir):
        """Test migration between different data formats or structures."""
        # Create old format data (simulating legacy format)
        legacy_data = {
            "sessions": [
                {
                    "date": "2025-08-10",
                    "goal": "coding",
                    "minutes": 30
                }
            ],
            "current_streak": 1,
            "longest_streak": 5
        }
        
        legacy_file = temp_data_dir / "sessions.json"
        with open(legacy_file, 'w') as f:
            json.dump(legacy_data, f)
        
        # Test that data_access can handle legacy format
        with patch_data_dir(temp_data_dir):
            from raycast_focus_tracker.data_access import get_current_streak, get_longest_streak
            
            # Should be able to read streak data from legacy format
            current = get_current_streak()
            longest = get_longest_streak()
            
            assert current == 1
            assert longest == 5

    def test_real_time_update_workflow(self, temp_data_dir):
        """Test that updates appear in real-time as new data comes in."""
        today = datetime.now().strftime("%Y-%m-%d")
        json_file = temp_data_dir / f"focus.{today}.json"
        
        # Start with empty data
        initial_data = {today: {"total_time_minutes": 0, "time_per_goal": {}, "items": []}}
        with open(json_file, 'w') as f:
            json.dump(initial_data, f)
        
        with patch_data_dir(temp_data_dir):
            from raycast_focus_tracker.data_access import get_today_minutes, get_today_by_goal
            
            # Initially should show zero
            assert get_today_minutes() == 0
            assert get_today_by_goal() == {}
            
            # Add some focus data
            updated_data = {
                today: {
                    "total_time_minutes": 25,
                    "time_per_goal": {"coding": 25},
                    "items": [
                        {
                            "goal": "coding",
                            "actual_duration": 25,
                            "state": "completed",
                            "cancelled": False
                        }
                    ]
                }
            }
            
            with open(json_file, 'w') as f:
                json.dump(updated_data, f)
            
            # Should now show the updated data
            assert get_today_minutes() == 25
            assert get_today_by_goal() == {"coding": 25}
            
            # Add more data
            updated_data[today]["total_time_minutes"] = 50
            updated_data[today]["time_per_goal"]["reading"] = 25
            updated_data[today]["time_per_goal"]["coding"] = 25
            
            with open(json_file, 'w') as f:
                json.dump(updated_data, f)
            
            # Should reflect the latest changes
            assert get_today_minutes() == 50
            assert get_today_by_goal() == {"coding": 25, "reading": 25}


def patch_data_dir(temp_dir):
    """Context manager to temporarily patch DATA_DIR for testing."""
    from unittest.mock import patch
    return patch('raycast_focus_tracker.data_access.DATA_DIR', temp_dir)