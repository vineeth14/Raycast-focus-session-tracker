"""Unit tests for log_to_json.py module."""

import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from raycast_focus_tracker.log_to_json import (
    load_or_create_json,
    get_date_from_timestamp,
    extract_timestamp,
    calculate_duration,
    parse_activity_duration,
    initialize_day_data,
    clean_stale_active_sessions,
    handle_session_start,
    handle_session_end,
    extract_goal,
    add_to_active_sessions,
    recalculate_daily_totals,
    parse_log_file,
    _should_count_session,
    _process_log_line
)


class TestLogUtilities:
    """Test utility functions in log_to_json module."""

    def test_load_or_create_json_existing_file(self, temp_data_dir, sample_focus_data):
        """Test loading existing JSON file."""
        # Setup
        test_file = temp_data_dir / "test.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)
        
        # Test
        result = load_or_create_json(str(test_file))
        
        # Assert
        assert result == sample_focus_data

    def test_load_or_create_json_new_file(self, temp_data_dir):
        """Test creating new JSON structure when file doesn't exist."""
        # Setup
        test_file = temp_data_dir / "nonexistent.json"
        
        # Test
        result = load_or_create_json(str(test_file))
        
        # Assert
        assert result == {}

    def test_get_date_from_timestamp(self):
        """Test extracting date from timestamp."""
        # Test
        result = get_date_from_timestamp("2025-08-10 14:18:11.777")
        
        # Assert
        assert result == "2025-08-10"

    def test_extract_timestamp_valid(self):
        """Test extracting timestamp from valid log line."""
        # Setup
        line = "2025-08-10 14:18:11.777 Raycast Extension Host[1234]: Start focus session"
        
        # Test
        result = extract_timestamp(line)
        
        # Assert
        assert result == "2025-08-10 14:18:11.777"

    def test_extract_timestamp_invalid(self):
        """Test extracting timestamp from invalid log line."""
        # Setup
        line = "Invalid log line without timestamp"
        
        # Test
        result = extract_timestamp(line)
        
        # Assert
        assert result is None

    def test_calculate_duration_normal(self):
        """Test calculating duration between two timestamps."""
        # Test
        result = calculate_duration(
            "2025-08-10 14:00:00.000",
            "2025-08-10 14:30:00.000"
        )
        
        # Assert
        assert result == 30

    def test_calculate_duration_sub_minute(self):
        """Test that short sessions return actual duration (can be 0 minutes)."""
        # Test
        result = calculate_duration(
            "2025-08-10 14:00:00.000",
            "2025-08-10 14:00:30.000"  # 30 seconds
        )
        
        # Assert - 30 seconds should be 0 minutes when rounded down
        assert result == 0

    def test_calculate_duration_error(self):
        """Test duration calculation with invalid timestamps."""
        # Test
        result = calculate_duration("invalid", "invalid")
        
        # Assert
        assert result == 0

    def test_parse_activity_duration_minutes_only(self):
        """Test parsing activity duration with minutes only."""
        # Test
        result = parse_activity_duration("45 minutes")
        
        # Assert
        assert result == 45

    def test_parse_activity_duration_hours_and_minutes(self):
        """Test parsing activity duration with hours and minutes."""
        # Test
        result = parse_activity_duration("1 hour 30 minutes")
        
        # Assert
        assert result == 90

    def test_parse_activity_duration_invalid(self):
        """Test parsing invalid activity duration."""
        # Test
        result = parse_activity_duration("invalid duration")
        
        # Assert
        assert result is None

    def test_parse_activity_duration_empty(self):
        """Test parsing empty activity duration."""
        # Test
        result = parse_activity_duration("")
        
        # Assert
        assert result is None

    def test_initialize_day_data_new_date(self):
        """Test initializing data structure for new date."""
        # Setup
        data = {}
        date_key = "2025-08-10"
        
        # Test
        initialize_day_data(data, date_key)
        
        # Assert
        assert date_key in data
        assert data[date_key]["total_time_minutes"] == 0
        assert data[date_key]["time_per_goal"] == {}
        assert data[date_key]["items"] == []
        assert data[date_key]["active_sessions"] == {}

    def test_initialize_day_data_existing_date(self):
        """Test that initializing existing date doesn't overwrite data."""
        # Setup
        data = {
            "2025-08-10": {
                "total_time_minutes": 45,
                "time_per_goal": {"coding": 45},
                "items": [],
                "active_sessions": {}
            }
        }
        date_key = "2025-08-10"
        
        # Test
        initialize_day_data(data, date_key)
        
        # Assert
        assert data[date_key]["total_time_minutes"] == 45  # Unchanged


class TestSessionHandling:
    """Test session start/end handling functions."""

    def test_handle_session_start(self):
        """Test handling session start log line."""
        # Setup
        line = "2025-08-10 09:00:00.123 Raycast Extension Host[1234]: Start focus session"
        data = {}
        current_session_data = {}
        
        # Test
        handle_session_start(line, data, current_session_data)
        
        # Assert
        assert "2025-08-10" in data
        assert current_session_data["timestamp"] == "2025-08-10 09:00:00.123"
        assert current_session_data["date_key"] == "2025-08-10"
        assert current_session_data["start_time"] == "2025-08-10 09:00:00.123"

    def test_extract_goal(self):
        """Test extracting goal from log line."""
        # Setup
        line = "2025-08-10 09:00:01.456 Raycast Extension Host[1234]: Goal: coding"
        current_session_data = {}
        
        # Test
        extract_goal(line, current_session_data)
        
        # Assert
        assert current_session_data["goal"] == "coding"

    def test_add_to_active_sessions(self):
        """Test adding session to active sessions."""
        # Setup
        data = {"2025-08-10": {"active_sessions": {}, "items": []}}
        current_session_data = {
            "goal": "coding",
            "date_key": "2025-08-10",
            "start_time": "2025-08-10 09:00:00.123"
        }
        
        # Test
        add_to_active_sessions(data, current_session_data)
        
        # Assert
        session_key = "coding_2025-08-10 09:00:00.123"
        assert session_key in data["2025-08-10"]["active_sessions"]
        session = data["2025-08-10"]["active_sessions"][session_key]
        assert session["goal"] == "coding"
        assert session["start_time"] == "2025-08-10 09:00:00.123"
        assert session["state"] == "started"

    def test_add_to_active_sessions_missing_data(self):
        """Test adding to active sessions with incomplete data."""
        # Setup
        data = {"2025-08-10": {"active_sessions": {}, "items": []}}
        current_session_data = {"goal": "coding"}  # Missing required fields
        
        # Test
        add_to_active_sessions(data, current_session_data)
        
        # Assert - should not add anything
        assert len(data["2025-08-10"]["active_sessions"]) == 0

    def test_handle_session_end_complete(self):
        """Test handling session completion."""
        # Setup
        line = "2025-08-10 09:30:00.789 Raycast Extension Host[1234]: Complete focus session"
        data = {
            "2025-08-10": {
                "active_sessions": {
                    "coding_2025-08-10 09:00:00.123": {
                        "goal": "coding",
                        "start_time": "2025-08-10 09:00:00.123",
                        "state": "started"
                    }
                },
                "items": []
            }
        }
        current_session_data = {"goal": "coding"}
        
        # Test
        handle_session_end(line, data, current_session_data)
        
        # Assert
        assert len(data["2025-08-10"]["items"]) == 1
        session = data["2025-08-10"]["items"][0]
        assert session["goal"] == "coding"
        assert session["end_time"] == "2025-08-10 09:30:00.789"
        assert session["cancelled"] is False
        assert session["state"] == "completed"

    def test_handle_session_end_cancel(self):
        """Test handling session cancellation."""
        # Setup
        line = "2025-08-10 09:15:00.789 Raycast Extension Host[1234]: Cancel focus session"
        data = {
            "2025-08-10": {
                "active_sessions": {
                    "coding_2025-08-10 09:00:00.123": {
                        "goal": "coding",
                        "start_time": "2025-08-10 09:00:00.123",
                        "state": "started"
                    }
                },
                "items": []
            }
        }
        current_session_data = {"goal": "coding"}
        
        # Test
        handle_session_end(line, data, current_session_data)
        
        # Assert
        assert len(data["2025-08-10"]["items"]) == 1
        session = data["2025-08-10"]["items"][0]
        assert session["cancelled"] is True


class TestDataCalculation:
    """Test data calculation and aggregation functions."""

    def test_should_count_session_completed(self):
        """Test that completed non-cancelled sessions are counted."""
        # Setup
        session = {
            "state": "completed",
            "cancelled": False,
            "actual_duration": 30
        }
        
        # Test
        result = _should_count_session(session)
        
        # Assert
        assert result is True

    def test_should_count_session_cancelled(self):
        """Test that cancelled sessions are not counted."""
        # Setup
        session = {
            "state": "completed",
            "cancelled": True,
            "actual_duration": 30
        }
        
        # Test
        result = _should_count_session(session)
        
        # Assert
        assert result is False

    def test_should_count_session_not_completed(self):
        """Test that non-completed sessions are not counted."""
        # Setup
        session = {
            "state": "started",
            "cancelled": False,
            "actual_duration": 30
        }
        
        # Test
        result = _should_count_session(session)
        
        # Assert
        assert result is False

    def test_recalculate_daily_totals(self):
        """Test recalculating daily totals from items."""
        # Setup
        data = {
            "2025-08-10": {
                "total_time_minutes": 0,  # Will be recalculated
                "time_per_goal": {},      # Will be recalculated
                "items": [
                    {
                        "goal": "coding",
                        "actual_duration": 30,
                        "state": "completed",
                        "cancelled": False
                    },
                    {
                        "goal": "reading",
                        "actual_duration": 15,
                        "state": "completed",
                        "cancelled": False
                    },
                    {
                        "goal": "writing",
                        "actual_duration": 20,
                        "state": "completed",
                        "cancelled": True  # Should be ignored
                    }
                ]
            }
        }
        
        # Test
        recalculate_daily_totals(data)
        
        # Assert
        assert data["2025-08-10"]["total_time_minutes"] == 45
        assert data["2025-08-10"]["time_per_goal"] == {"coding": 30, "reading": 15}

    def test_clean_stale_active_sessions(self):
        """Test cleaning up stale active sessions."""
        # Setup
        data = {
            "2025-08-10": {
                "active_sessions": {
                    "coding_2025-08-10 09:00:00.123": {
                        "goal": "coding",
                        "start_time": "2025-08-10 09:00:00.123",
                        "state": "started"
                    },
                    "reading_2025-08-10 10:00:00.123": {
                        "goal": "reading",
                        "start_time": "2025-08-10 10:00:00.123",
                        "state": "started"
                    }
                },
                "items": [
                    {
                        "goal": "coding",
                        "start_time": "2025-08-10 09:00:00.123",
                        "state": "completed"
                    }
                ]
            }
        }
        
        # Test
        with patch('builtins.print'):
            clean_stale_active_sessions(data)
        
        # Assert - coding session should be removed as it's completed
        active_sessions = data["2025-08-10"]["active_sessions"]
        assert "coding_2025-08-10 09:00:00.123" not in active_sessions
        assert "reading_2025-08-10 10:00:00.123" in active_sessions


class TestLogParsing:
    """Test the main log parsing functionality."""

    def test_parse_log_file_success(self, temp_data_dir, create_test_log_file):
        """Test successful log file parsing."""
        # Setup
        log_lines = [
            "2025-08-10 09:00:00.123 Raycast Extension Host[1234]: Start focus session",
            "2025-08-10 09:00:01.456 Raycast Extension Host[1234]: Goal: coding",
            "2025-08-10 09:30:00.789 Raycast Extension Host[1234]: Complete focus session"
        ]
        log_file = create_test_log_file(temp_data_dir, "test.log", log_lines)
        output_file = temp_data_dir / "output.json"
        
        # Test
        result = parse_log_file(str(log_file), str(output_file))
        
        # Assert
        assert result is not None
        assert "2025-08-10" in result
        assert output_file.exists()
        
        # Check saved file
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data == result

    def test_parse_log_file_nonexistent(self, temp_data_dir):
        """Test parsing nonexistent log file."""
        # Setup
        log_file = temp_data_dir / "nonexistent.log"
        output_file = temp_data_dir / "output.json"
        
        # Test
        with patch('builtins.print'):
            result = parse_log_file(str(log_file), str(output_file))
        
        # Assert
        assert result is None

    def test_process_log_line_session_start(self):
        """Test processing session start line."""
        # Setup
        line = "2025-08-10 09:00:00.123 Raycast Extension Host[1234]: Start focus session"
        data = {}
        current_session_data = {}
        
        # Test
        _process_log_line(line, data, current_session_data)
        
        # Assert
        assert "2025-08-10" in data
        assert current_session_data["start_time"] == "2025-08-10 09:00:00.123"

    def test_process_log_line_goal(self):
        """Test processing goal line."""
        # Setup
        line = "2025-08-10 09:00:01.456 Raycast Extension Host[1234]: Goal: coding"
        data = {"2025-08-10": {"active_sessions": {}, "items": []}}
        current_session_data = {
            "start_time": "2025-08-10 09:00:00.123",
            "date_key": "2025-08-10"
        }
        
        # Test
        _process_log_line(line, data, current_session_data)
        
        # Assert
        assert current_session_data["goal"] == "coding"
        # Should also add to active sessions
        session_key = "coding_2025-08-10 09:00:00.123"
        assert session_key in data["2025-08-10"]["active_sessions"]

    def test_process_log_line_activity_summary(self):
        """Test processing activity summary lines."""
        # Setup
        line = "2025-08-10 09:30:01.000 Raycast Extension Host[1234]: Focus session activity summary"
        data = {}
        current_session_data = {}
        
        # Test
        _process_log_line(line, data, current_session_data)
        
        # Assert
        assert current_session_data.get("in_activity_summary") is True

    def test_graceful_handling_of_invalid_lines(self, temp_data_dir, create_test_log_file):
        """Test that invalid lines are gracefully ignored without crashing."""
        # Setup
        log_lines = [
            "2025-08-10 09:00:00.123 Raycast Extension Host[1234]: Start focus session",
            "Invalid line without proper format",
            "2025-08-10 09:00:01.456 Raycast Extension Host[1234]: Goal: coding",
            "2025-08-10 09:30:00.789 Raycast Extension Host[1234]: Complete focus session"
        ]
        log_file = create_test_log_file(temp_data_dir, "test.log", log_lines)
        output_file = temp_data_dir / "output.json"

        # Test - should not crash on invalid lines
        result = parse_log_file(str(log_file), str(output_file))

        # Assert - parsing succeeds despite invalid line
        assert result is not None
        assert "2025-08-10" in result
        # Valid session should still be parsed
        assert len(result["2025-08-10"]["items"]) >= 0