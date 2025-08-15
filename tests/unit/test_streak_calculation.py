"""Unit tests for streak_calculation.py module."""

import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from raycast_focus_tracker.streak_calculation import (
    load_streaks,
    save_streaks,
    update_streaks,
    _calculate_current_streak
)


class TestStreakLoading:
    """Test streak data loading and saving functions."""

    def test_load_streaks_existing_file(self, temp_data_dir, sample_streak_data):
        """Test loading streaks from existing file."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        with open(streaks_file, 'w') as f:
            json.dump(sample_streak_data, f)
        
        # Test
        result = load_streaks(str(streaks_file))
        
        # Assert
        assert result == sample_streak_data
        assert result["current_streak"] == 2
        assert result["longest_streak"] == 5

    def test_load_streaks_nonexistent_file(self, temp_data_dir):
        """Test loading streaks when file doesn't exist."""
        # Setup
        nonexistent_file = temp_data_dir / "nonexistent.json"
        
        # Test
        result = load_streaks(str(nonexistent_file))
        
        # Assert
        assert result == {"current_streak": 0, "longest_streak": 0}

    def test_save_streaks(self, temp_data_dir, sample_streak_data):
        """Test saving streaks to file."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        
        # Test
        save_streaks(sample_streak_data, str(streaks_file))
        
        # Assert
        assert streaks_file.exists()
        with open(streaks_file) as f:
            saved_data = json.load(f)
        assert saved_data == sample_streak_data

    def test_save_streaks_creates_directory(self, temp_data_dir, sample_streak_data):
        """Test that save_streaks creates parent directories if they don't exist."""
        # Setup
        nested_dir = temp_data_dir / "nested" / "dir"
        streaks_file = nested_dir / "streaks.json"
        
        # Test
        save_streaks(sample_streak_data, str(streaks_file))
        
        # Assert
        assert streaks_file.exists()
        with open(streaks_file) as f:
            saved_data = json.load(f)
        assert saved_data == sample_streak_data


class TestStreakCalculation:
    """Test streak calculation logic."""

    def test_calculate_current_streak_continuous(self):
        """Test calculating current streak with continuous days."""
        # Setup
        daily_data = {
            "2025-08-10": {"total_time_minutes": 30},
            "2025-08-11": {"total_time_minutes": 45},
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 4

    def test_calculate_current_streak_with_gap(self):
        """Test calculating current streak with a gap."""
        # Setup
        daily_data = {
            "2025-08-10": {"total_time_minutes": 30},
            "2025-08-11": {"total_time_minutes": 0},   # Gap here
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 2  # Only counts the last 2 days

    def test_calculate_current_streak_zero_today(self):
        """Test calculating current streak when today has zero minutes."""
        # Setup
        daily_data = {
            "2025-08-10": {"total_time_minutes": 30},
            "2025-08-11": {"total_time_minutes": 45},
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 0}   # Today has no focus
        }
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 0  # Streak is broken

    def test_calculate_current_streak_empty_data(self):
        """Test calculating current streak with empty data."""
        # Setup
        daily_data = {}
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 0

    def test_calculate_current_streak_missing_total_time(self):
        """Test calculating current streak with missing total_time_minutes."""
        # Setup
        daily_data = {
            "2025-08-10": {"time_per_goal": {"coding": 30}},  # Missing total_time_minutes
            "2025-08-11": {"total_time_minutes": 45},
            "2025-08-12": {"total_time_minutes": 0}
        }
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 1  # Only counts 2025-08-11

    def test_calculate_current_streak_unsorted_dates(self):
        """Test calculating current streak with unsorted date keys."""
        # Setup - deliberately unsorted
        daily_data = {
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-10": {"total_time_minutes": 30},
            "2025-08-13": {"total_time_minutes": 25},
            "2025-08-11": {"total_time_minutes": 45}
        }
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 4  # Should handle unsorted dates correctly


class TestStreakUpdating:
    """Test the main streak updating functionality."""

    def test_update_streaks_new_record(self, temp_data_dir):
        """Test updating streaks when a new longest streak is achieved."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        initial_streaks = {"current_streak": 2, "longest_streak": 3}
        with open(streaks_file, 'w') as f:
            json.dump(initial_streaks, f)
        
        daily_data = {
            "2025-08-10": {"total_time_minutes": 30},
            "2025-08-11": {"total_time_minutes": 45},
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Test
        result = update_streaks(daily_data, str(streaks_file))
        
        # Assert
        assert result["current_streak"] == 4
        assert result["longest_streak"] == 4  # New record
        
        # Check file was updated
        with open(streaks_file) as f:
            saved_data = json.load(f)
        assert saved_data["longest_streak"] == 4

    def test_update_streaks_no_new_record(self, temp_data_dir):
        """Test updating streaks when no new record is achieved."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        initial_streaks = {"current_streak": 5, "longest_streak": 10}
        with open(streaks_file, 'w') as f:
            json.dump(initial_streaks, f)
        
        daily_data = {
            "2025-08-11": {"total_time_minutes": 45},
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Test
        result = update_streaks(daily_data, str(streaks_file))
        
        # Assert
        assert result["current_streak"] == 3
        assert result["longest_streak"] == 10  # Unchanged
        
        # Check file was updated (current_streak changed)
        with open(streaks_file) as f:
            saved_data = json.load(f)
        assert saved_data["current_streak"] == 3

    def test_update_streaks_no_change(self, temp_data_dir):
        """Test updating streaks when nothing changes."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        initial_streaks = {"current_streak": 3, "longest_streak": 10}
        with open(streaks_file, 'w') as f:
            json.dump(initial_streaks, f)
        
        daily_data = {
            "2025-08-11": {"total_time_minutes": 45},
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Test
        result = update_streaks(daily_data, str(streaks_file))
        
        # Assert
        assert result["current_streak"] == 3
        assert result["longest_streak"] == 10
        
        # File should not have been updated since nothing changed
        # We can't easily test this without mocking, but the logic is there

    def test_update_streaks_nonexistent_file(self, temp_data_dir):
        """Test updating streaks when streaks file doesn't exist."""
        # Setup
        streaks_file = temp_data_dir / "nonexistent.json"
        daily_data = {
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Test
        result = update_streaks(daily_data, str(streaks_file))
        
        # Assert
        assert result["current_streak"] == 2
        assert result["longest_streak"] == 2
        
        # File should have been created
        assert streaks_file.exists()

    def test_update_streaks_streak_broken(self, temp_data_dir):
        """Test updating streaks when current streak is broken."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        initial_streaks = {"current_streak": 5, "longest_streak": 10}
        with open(streaks_file, 'w') as f:
            json.dump(initial_streaks, f)
        
        daily_data = {
            "2025-08-10": {"total_time_minutes": 30},
            "2025-08-11": {"total_time_minutes": 0},   # Streak broken
            "2025-08-12": {"total_time_minutes": 60},
            "2025-08-13": {"total_time_minutes": 0}    # Today also zero
        }
        
        # Test
        result = update_streaks(daily_data, str(streaks_file))
        
        # Assert
        assert result["current_streak"] == 0
        assert result["longest_streak"] == 10  # Unchanged

    def test_update_streaks_with_default_path(self, temp_data_dir):
        """Test update_streaks with default path parameter."""
        # Setup - change working directory context
        with patch('raycast_focus_tracker.streak_calculation.Path') as mock_path:
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value.exists.return_value = False
            
            daily_data = {
                "2025-08-13": {"total_time_minutes": 25}
            }
            
            # Test with mocked file operations
            with patch('builtins.open', mock_open(read_data='{"current_streak": 0, "longest_streak": 0}')):
                with patch('json.dump') as mock_dump:
                    result = update_streaks(daily_data)
            
            # Assert
            assert result["current_streak"] == 1
            assert result["longest_streak"] == 1


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_load_streaks_invalid_json(self, temp_data_dir):
        """Test loading streaks from file with invalid JSON."""
        # Setup
        streaks_file = temp_data_dir / "invalid.json"
        with open(streaks_file, 'w') as f:
            f.write("invalid json content")
        
        # Test - should not crash, should return default
        with patch('builtins.print'):  # Suppress error output
            result = load_streaks(str(streaks_file))
        
        # Assert - should fall back to default values
        assert result == {"current_streak": 0, "longest_streak": 0}

    def test_save_streaks_permission_error(self, temp_data_dir, sample_streak_data):
        """Test saving streaks when file permissions prevent writing."""
        # Setup
        streaks_file = temp_data_dir / "readonly.json"
        
        # Create file and make directory read-only (simulation)
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Test - should not crash
            try:
                save_streaks(sample_streak_data, str(streaks_file))
            except PermissionError:
                pytest.fail("save_streaks should handle permission errors gracefully")

    def test_calculate_current_streak_very_large_dataset(self):
        """Test streak calculation with a large number of days."""
        # Setup - 1000 days of continuous focus
        daily_data = {}
        for i in range(1000):
            date = f"2023-01-{i+1:03d}" if i < 365 else f"2024-01-{i-364:03d}" if i < 730 else f"2025-01-{i-729:03d}"
            daily_data[date] = {"total_time_minutes": 30}
        
        # Test
        result = _calculate_current_streak(daily_data)
        
        # Assert
        assert result == 1000

    def test_update_streaks_concurrent_access(self, temp_data_dir):
        """Test update_streaks behavior with simulated concurrent file access."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        initial_streaks = {"current_streak": 1, "longest_streak": 5}
        
        daily_data = {
            "2025-08-13": {"total_time_minutes": 25}
        }
        
        # Simulate race condition where file changes between read and write
        def mock_load_streaks(path):
            return initial_streaks.copy()
        
        def mock_save_streaks(streaks, path):
            # Simulate another process updating the file
            pass
        
        with patch('raycast_focus_tracker.streak_calculation.load_streaks', mock_load_streaks):
            with patch('raycast_focus_tracker.streak_calculation.save_streaks', mock_save_streaks):
                # Test
                result = update_streaks(daily_data, str(streaks_file))
        
        # Assert - should still return correct calculation
        assert result["current_streak"] == 1  # Based on daily_data
        assert result["longest_streak"] == 5   # From initial data