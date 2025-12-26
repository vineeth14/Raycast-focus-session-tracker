"""Unit tests for data_access.py module."""

import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from raycast_focus_tracker.data_access import (
    get_today_minutes,
    get_today_by_goal,
    get_current_streak,
    get_longest_streak,
    _get_streak_value,
    DATA_DIR
)


class TestDataAccess:
    """Test suite for data access functions."""

    @patch('raycast_focus_tracker.data_access.datetime')
    @patch('raycast_focus_tracker.data_access.DATA_DIR')
    def test_get_today_minutes_success(self, mock_data_dir, mock_datetime, temp_data_dir, sample_focus_data):
        """Test successful retrieval of today's minutes."""
        # Setup
        mock_datetime.now.return_value.strftime.return_value = "2025-08-10"
        mock_data_dir.__truediv__ = lambda self, other: temp_data_dir / other
        mock_data_dir.glob = lambda pattern: [temp_data_dir / "focus.2025-08-10.json"]
        
        # Create test file
        test_file = temp_data_dir / "focus.2025-08-10.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)
        
        # Test
        result = get_today_minutes()
        
        # Assert
        assert result == 45

    @patch('raycast_focus_tracker.data_access.datetime')
    def test_get_today_minutes_no_data(self, mock_datetime, temp_data_dir):
        """Test get_today_minutes when no data exists."""
        # Setup
        mock_datetime.now.return_value.strftime.return_value = "2025-08-13"
        
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir), \
             patch.object(Path, 'glob', return_value=[]):
            # Test
            result = get_today_minutes()
            
            # Assert
            assert result == 0

    @patch('raycast_focus_tracker.data_access.datetime')
    @patch('raycast_focus_tracker.data_access.DATA_DIR')
    def test_get_today_by_goal_success(self, mock_data_dir, mock_datetime, temp_data_dir, sample_focus_data):
        """Test successful retrieval of today's goals breakdown."""
        # Setup
        mock_datetime.now.return_value.strftime.return_value = "2025-08-10"
        mock_data_dir.__truediv__ = lambda self, other: temp_data_dir / other
        mock_data_dir.glob = lambda pattern: [temp_data_dir / "focus.2025-08-10.json"]
        
        # Create test file
        test_file = temp_data_dir / "focus.2025-08-10.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)
        
        # Test
        result = get_today_by_goal()
        
        # Assert
        expected = {"coding": 30, "reading": 15}
        assert result == expected

    @patch('raycast_focus_tracker.data_access.datetime')
    def test_get_today_by_goal_no_data(self, mock_datetime, temp_data_dir):
        """Test get_today_by_goal when no data exists."""
        # Setup
        mock_datetime.now.return_value.strftime.return_value = "2025-08-13"
        
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir), \
             patch.object(Path, 'glob', return_value=[]):
            # Test
            result = get_today_by_goal()
            
            # Assert
            assert result == {}

    @patch('raycast_focus_tracker.data_access._get_streak_value')
    def test_get_current_streak(self, mock_get_streak):
        """Test get_current_streak function."""
        # Setup
        mock_get_streak.return_value = 5
        
        # Test
        result = get_current_streak()
        
        # Assert
        assert result == 5
        mock_get_streak.assert_called_once_with("current_streak")

    @patch('raycast_focus_tracker.data_access._get_streak_value')
    def test_get_longest_streak(self, mock_get_streak):
        """Test get_longest_streak function."""
        # Setup
        mock_get_streak.return_value = 10
        
        # Test
        result = get_longest_streak()
        
        # Assert
        assert result == 10
        mock_get_streak.assert_called_once_with("longest_streak")

    def test_get_streak_value_success(self, temp_data_dir, sample_streak_data):
        """Test successful streak value retrieval."""
        # Setup
        streaks_file = temp_data_dir / "streaks.json"
        with open(streaks_file, 'w') as f:
            json.dump(sample_streak_data, f)
        
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir):
            # Test
            result = _get_streak_value("current_streak")
            
            # Assert
            assert result == 2

    def test_get_streak_value_no_file(self, temp_data_dir):
        """Test streak value retrieval when no file exists."""
        with patch('raycast_focus_tracker.data_access.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            mock_path.home.return_value = temp_data_dir
            # Test
            result = _get_streak_value("current_streak")
            
            # Assert
            assert result == 0

    def test_get_streak_value_legacy_fallback(self, temp_data_dir, sample_streak_data):
        """Test fallback to legacy sessions.json file."""
        # Setup - create only legacy file
        legacy_file = temp_data_dir / "sessions.json"
        with open(legacy_file, 'w') as f:
            json.dump(sample_streak_data, f)
        
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir):
            # Test
            result = _get_streak_value("longest_streak")
            
            # Assert
            assert result == 5

    @patch('raycast_focus_tracker.data_access.datetime')
    def test_search_multiple_directories(self, mock_datetime, temp_data_dir, sample_focus_data):
        """Test that the function searches multiple directories for data."""
        # Setup
        mock_datetime.now.return_value.strftime.return_value = "2025-08-10"
        
        home_dir = temp_data_dir / "home"
        project_dir = temp_data_dir / "project"
        home_dir.mkdir()
        project_dir.mkdir()

        # Create a file in the project directory
        test_file = project_dir / "focus.2025-08-10.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)

        # Test
        result = get_today_minutes(search_dirs=[home_dir, project_dir])
        
        # Assert
        assert result == 45

    def test_error_handling_in_get_today_minutes(self, temp_data_dir):
        """Test error handling in get_today_minutes."""
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir), \
             patch.object(Path, 'glob', side_effect=Exception("Test error")), \
             patch('builtins.print') as mock_print:
            
            # Test
            result = get_today_minutes()
            
            # Assert
            assert result == 0
            mock_print.assert_called_once()
            assert "Error accessing today's minutes" in str(mock_print.call_args)

    def test_error_handling_in_get_today_by_goal(self, temp_data_dir):
        """Test error handling in get_today_by_goal."""
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir), \
             patch.object(Path, 'glob', side_effect=Exception("Test error")), \
             patch('builtins.print') as mock_print:
            
            # Test
            result = get_today_by_goal()
            
            # Assert
            assert result == {}
            mock_print.assert_called_once()
            assert "Error accessing today's goals" in str(mock_print.call_args)

    def test_error_handling_in_get_streak_value(self, temp_data_dir):
        """Test error handling in _get_streak_value."""
        with patch('raycast_focus_tracker.data_access.DATA_DIR', temp_data_dir), \
             patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json")):
            
            # Test
            result = _get_streak_value("current_streak")
            
            # Assert
            assert result == 0


class TestDataDirectoryLogic:
    """Test the data directory selection logic."""
    
    def test_data_directory_prioritization(self):
        """Test that DATA_DIR is selected correctly based on priority."""
        # This test verifies the logic in data_access.py for selecting DATA_DIR
        # The actual DATA_DIR value depends on the environment and existing files
        assert DATA_DIR is not None
        assert isinstance(DATA_DIR, Path)
        assert DATA_DIR.name in ["data", ".raycast-focus-tracker"]