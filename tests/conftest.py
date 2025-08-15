"""Test configuration and fixtures for Raycast Focus Tracker tests."""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_focus_data():
    """Sample focus data for testing."""
    return {
        "2025-08-10": {
            "total_time_minutes": 45,
            "time_per_goal": {
                "coding": 30,
                "reading": 15
            },
            "items": [
                {
                    "goal": "coding",
                    "start_time": "2025-08-10 09:00:00.000",
                    "end_time": "2025-08-10 09:30:00.000",
                    "actual_duration": 30,
                    "cancelled": False,
                    "state": "completed",
                    "pauses": 0,
                    "blocks": 0,
                    "snoozes": 0
                },
                {
                    "goal": "reading",
                    "start_time": "2025-08-10 14:00:00.000",
                    "end_time": "2025-08-10 14:15:00.000",
                    "actual_duration": 15,
                    "cancelled": False,
                    "state": "completed",
                    "pauses": 1,
                    "blocks": 0,
                    "snoozes": 0
                }
            ],
            "active_sessions": {}
        },
        "2025-08-11": {
            "total_time_minutes": 60,
            "time_per_goal": {
                "coding": 60
            },
            "items": [
                {
                    "goal": "coding",
                    "start_time": "2025-08-11 10:00:00.000",
                    "end_time": "2025-08-11 11:00:00.000",
                    "actual_duration": 60,
                    "cancelled": False,
                    "state": "completed",
                    "pauses": 0,
                    "blocks": 0,
                    "snoozes": 0
                }
            ],
            "active_sessions": {}
        },
        "2025-08-12": {
            "total_time_minutes": 0,
            "time_per_goal": {},
            "items": [],
            "active_sessions": {}
        }
    }


@pytest.fixture
def sample_log_lines():
    """Sample log lines for testing log parsing."""
    return [
        "2025-08-10 09:00:00.123 Raycast Extension Host[1234]: Start focus session",
        "2025-08-10 09:00:01.456 Raycast Extension Host[1234]: Goal: coding",
        "2025-08-10 09:30:00.789 Raycast Extension Host[1234]: Complete focus session",
        "2025-08-10 09:30:01.000 Raycast Extension Host[1234]: Focus session activity summary",
        "2025-08-10 09:30:01.001 Raycast Extension Host[1234]: Start date: 2025-08-10 09:00:00",
        "2025-08-10 09:30:01.002 Raycast Extension Host[1234]: Duration: 30 minutes",
        "2025-08-10 09:30:01.003 Raycast Extension Host[1234]: Pauses Count: 0",
        "2025-08-10 09:30:01.004 Raycast Extension Host[1234]: Block Events Count: 0",
        "2025-08-10 09:30:01.005 Raycast Extension Host[1234]: Snooze Events Count: 0",
    ]


@pytest.fixture
def sample_streak_data():
    """Sample streak data for testing."""
    return {
        "current_streak": 2,
        "longest_streak": 5
    }


@pytest.fixture
def mock_today():
    """Mock today's date to 2025-08-13 for consistent testing."""
    return "2025-08-13"


@pytest.fixture
def create_test_json_file():
    """Factory fixture to create test JSON files."""
    def _create_file(temp_dir: Path, filename: str, data: dict):
        file_path = temp_dir / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return file_path
    return _create_file


@pytest.fixture
def create_test_log_file():
    """Factory fixture to create test log files."""
    def _create_file(temp_dir: Path, filename: str, lines: list):
        file_path = temp_dir / filename
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        return file_path
    return _create_file


@pytest.fixture
def complex_focus_data():
    """More complex focus data for advanced testing scenarios."""
    base_date = datetime(2025, 8, 1)
    data = {}
    
    # Create 10 days of data with varying patterns
    for i in range(10):
        date = base_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        if i % 3 == 0:  # Every 3rd day has no focus
            data[date_str] = {
                "total_time_minutes": 0,
                "time_per_goal": {},
                "items": [],
                "active_sessions": {}
            }
        else:
            minutes = 25 + (i * 10)  # Increasing focus time
            goal = "work" if i % 2 == 0 else "study"
            
            data[date_str] = {
                "total_time_minutes": minutes,
                "time_per_goal": {goal: minutes},
                "items": [
                    {
                        "goal": goal,
                        "start_time": f"{date_str} 10:00:00.000",
                        "end_time": f"{date_str} 10:{minutes:02d}:00.000",
                        "actual_duration": minutes,
                        "cancelled": False,
                        "state": "completed",
                        "pauses": i % 3,
                        "blocks": i % 2,
                        "snoozes": 0
                    }
                ],
                "active_sessions": {}
            }
    
    return data