"""Integration tests for menuBar.py module."""

import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestFocusAppIntegration:
    """Integration tests for FocusApp class."""

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_focus_app_initialization(self, mock_lesley, mock_rumps, temp_data_dir, sample_focus_data):
        """Test FocusApp initialization."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        
        # Create test data
        test_file = temp_data_dir / "focus.2025-08-10.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                # Test
                app = FocusApp()
                
                # Assert
                assert app.data_dir == temp_data_dir
                mock_rumps.App.assert_called_once_with("🎯")

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_refresh_data_integration(self, mock_lesley, mock_rumps, temp_data_dir, sample_focus_data):
        """Test _refresh_data method with real data."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        # Create test data files
        test_file1 = temp_data_dir / "focus.2025-08-10.json"
        with open(test_file1, 'w') as f:
            json.dump({"2025-08-10": sample_focus_data["2025-08-10"]}, f)
        
        test_file2 = temp_data_dir / "focus.2025-08-11.json"
        with open(test_file2, 'w') as f:
            json.dump({"2025-08-11": sample_focus_data["2025-08-11"]}, f)
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'), \
                 patch('raycast_focus_tracker.menuBar.update_streaks') as mock_update:
                
                app = FocusApp()
                
                # Test
                app._refresh_data()
                
                # Assert - should have called update_streaks with merged data
                mock_update.assert_called_once()
                call_args = mock_update.call_args[0]
                daily_data = call_args[0]
                assert "2025-08-10" in daily_data
                assert "2025-08-11" in daily_data

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_build_streak_submenu(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test _build_streak_submenu method."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.MenuItem.side_effect = lambda text, callback: MagicMock(text=text, callback=callback)
        mock_rumps.Timer.return_value = MagicMock()
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'), \
                 patch('raycast_focus_tracker.menuBar.get_current_streak', return_value=5), \
                 patch('raycast_focus_tracker.menuBar.get_longest_streak', return_value=10):
                
                app = FocusApp()
                
                # Test
                result = app._build_streak_submenu()
                
                # Assert
                assert len(result) == 2
                assert "Current: 5 days" in result[0].text
                assert "Longest: 10 days" in result[1].text

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_build_time_submenu(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test _build_time_submenu method with different time values."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.MenuItem.side_effect = lambda text, callback: MagicMock(text=text, callback=callback)
        mock_rumps.Timer.return_value = MagicMock()
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                
                # Test with minutes only
                with patch('raycast_focus_tracker.menuBar.get_today_minutes', return_value=45):
                    result = app._build_time_submenu()
                    assert len(result) == 1
                    assert "Total: 45 minutes" in result[0].text
                
                # Test with hours and minutes
                with patch('raycast_focus_tracker.menuBar.get_today_minutes', return_value=125):
                    result = app._build_time_submenu()
                    assert len(result) == 2
                    assert "Total: 125 minutes" in result[0].text
                    assert "= 2h 5m" in result[1].text

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_build_goals_submenu(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test _build_goals_submenu method."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.MenuItem.side_effect = lambda text, callback: MagicMock(text=text, callback=callback)
        mock_rumps.separator = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                
                # Test with goals
                with patch('raycast_focus_tracker.menuBar.get_today_by_goal', 
                          return_value={"coding": 30, "reading": 15}):
                    result = app._build_goals_submenu()
                    assert len(result) == 4  # 2 goals + separator + total
                    goal_texts = [item.text for item in result if hasattr(item, 'text')]
                    assert any("coding: 30m" in text for text in goal_texts)
                    assert any("reading: 15m" in text for text in goal_texts)
                    assert any("Total: 45m" in text for text in goal_texts)
                
                # Test with no goals
                with patch('raycast_focus_tracker.menuBar.get_today_by_goal', return_value={}):
                    result = app._build_goals_submenu()
                    assert len(result) == 1
                    assert "No sessions today" in result[0].text

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_parse_latest_logs_integration(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test _parse_latest_logs method."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        # Create log directory and file
        log_dir = temp_data_dir / "logs"
        log_dir.mkdir()
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"focus.{today}.log"
        
        log_content = [
            f"{today} 09:00:00.123 Raycast Extension Host[1234]: Start focus session",
            f"{today} 09:00:01.456 Raycast Extension Host[1234]: Goal: test",
            f"{today} 09:30:00.789 Raycast Extension Host[1234]: Complete focus session"
        ]
        with open(log_file, 'w') as f:
            f.write('\n'.join(log_content))
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, 'create_menu'):
                
                # Mock script_dir to point to our test structure
                app = FocusApp()
                app.script_dir = temp_data_dir
                
                # Test
                with patch('builtins.print') as mock_print:
                    app._parse_latest_logs()
                
                # Assert - should have created JSON file
                expected_json = temp_data_dir / f"focus.{today}.json"
                assert expected_json.exists()
                
                # Check log output
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any(f"Parsed {log_file}" in call for call in print_calls)

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_create_heatmap_integration(self, mock_lesley, mock_rumps, temp_data_dir, sample_focus_data):
        """Test _create_heatmap method."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        mock_chart = MagicMock()
        mock_lesley.cal_heatmap.return_value = mock_chart
        
        # Create test data
        test_file = temp_data_dir / "focus.2025-08-10.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'), \
                 patch('raycast_focus_tracker.menuBar.webbrowser') as mock_browser, \
                 patch('raycast_focus_tracker.menuBar.Path') as mock_path_class:
                
                mock_path_instance = MagicMock()
                mock_path_class.cwd.return_value = temp_data_dir
                mock_path_instance.as_uri.return_value = "file://test"
                mock_path_class.return_value = mock_path_instance
                
                app = FocusApp()
                
                # Test
                app._create_heatmap()
                
                # Assert
                mock_lesley.cal_heatmap.assert_called_once()
                mock_chart.save.assert_called_once()
                mock_browser.open.assert_called_once()

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_update_menu_data_integration(self, mock_lesley, mock_rumps, temp_data_dir, sample_focus_data):
        """Test _update_menu_data method."""
        # Setup
        mock_app = MagicMock()
        mock_rumps.App.return_value = mock_app
        mock_rumps.Timer.return_value = MagicMock()
        
        # Create test data
        test_file = temp_data_dir / "focus.2025-08-10.json"
        with open(test_file, 'w') as f:
            json.dump(sample_focus_data, f)
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                app.menu = {"Streak Data": MagicMock(), "Today's Time": MagicMock(), "Time by Goal": MagicMock()}
                
                # Test
                with patch.object(app, '_refresh_data') as mock_refresh, \
                     patch.object(app, '_update_submenu') as mock_update_submenu:
                    
                    app._update_menu_data()
                    
                    # Assert
                    mock_refresh.assert_called_once()
                    assert mock_update_submenu.call_count == 3

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_auto_refresh_integration(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test _auto_refresh method."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                
                # Test successful auto-refresh
                with patch.object(app, '_parse_latest_logs') as mock_parse, \
                     patch.object(app, '_update_menu_data') as mock_update, \
                     patch('builtins.print') as mock_print:
                    
                    app._auto_refresh(None)
                    
                    # Assert
                    mock_parse.assert_called_once()
                    mock_update.assert_called_once()
                    # Should print auto-refresh message
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Auto-refresh triggered" in call for call in print_calls)

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_auto_refresh_error_handling(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test _auto_refresh error handling."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                
                # Test auto-refresh with error
                with patch.object(app, '_parse_latest_logs', side_effect=Exception("Test error")), \
                     patch.object(app, 'create_menu') as mock_create_menu, \
                     patch('builtins.print') as mock_print:
                    
                    app._auto_refresh(None)
                    
                    # Assert - should handle error and try to rebuild menu
                    mock_create_menu.assert_called_once()
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Error during auto-refresh" in call for call in print_calls)


class TestMenuBarDataFlow:
    """Test the complete data flow through the menu bar application."""

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_complete_data_flow(self, mock_lesley, mock_rumps, temp_data_dir, create_test_log_file):
        """Test complete data flow from log to menu display."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create log data that should result in specific menu content
        log_lines = [
            f"{today} 09:00:00.123 Raycast Extension Host[1234]: Start focus session",
            f"{today} 09:00:01.456 Raycast Extension Host[1234]: Goal: integration_test",
            f"{today} 09:30:00.789 Raycast Extension Host[1234]: Complete focus session",
            f"{today} 09:30:01.000 Raycast Extension Host[1234]: Focus session activity summary",
            f"{today} 09:30:01.002 Raycast Extension Host[1234]: Duration: 30 minutes",
        ]
        
        # Create log directory and file
        log_dir = temp_data_dir / "logs"
        log_dir.mkdir()
        log_file = create_test_log_file(log_dir, f"focus.{today}.log", log_lines)
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                app.script_dir = temp_data_dir
                
                # Test the complete flow
                with patch('builtins.print'):
                    # Parse logs
                    app._parse_latest_logs()
                    
                    # Refresh data
                    app._refresh_data()
                    
                    # Build menus with the parsed data
                    time_submenu = app._build_time_submenu()
                    goals_submenu = app._build_goals_submenu()
                
                # Assert - check that the data flowed correctly
                # Should have created JSON file
                json_file = temp_data_dir / f"focus.{today}.json"
                assert json_file.exists()
                
                # Check JSON content
                with open(json_file) as f:
                    data = json.load(f)
                assert today in data
                assert data[today]["total_time_minutes"] == 30
                assert "integration_test" in data[today]["time_per_goal"]
                
                # Check menu content reflects the data
                time_texts = [item.text for item in time_submenu if hasattr(item, 'text')]
                assert any("Total: 30 minutes" in text for text in time_texts)
                
                goals_texts = [item.text for item in goals_submenu if hasattr(item, 'text')]
                assert any("integration_test: 30m" in text for text in goals_texts)

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_refresh_button_integration(self, mock_lesley, mock_rumps, temp_data_dir):
        """Test that the refresh button triggers the correct sequence."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', temp_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'):
                
                app = FocusApp()
                
                # Test refresh button click
                with patch.object(app, '_parse_latest_logs') as mock_parse, \
                     patch.object(app, '_update_menu_data') as mock_update:
                    
                    app.refresh(None)
                    
                    # Assert
                    mock_parse.assert_called_once()
                    mock_update.assert_called_once()

    @patch('raycast_focus_tracker.menuBar.rumps')
    @patch('raycast_focus_tracker.menuBar.lesley')
    def test_multiple_data_directories(self, mock_lesley, mock_rumps, temp_data_dir, sample_focus_data):
        """Test handling of multiple data directories."""
        # Setup
        mock_rumps.App.return_value = MagicMock()
        mock_rumps.Timer.return_value = MagicMock()
        
        # Create data in both directories
        home_data_dir = temp_data_dir / "home_data"
        project_data_dir = temp_data_dir / "project_data"
        home_data_dir.mkdir()
        project_data_dir.mkdir()
        
        # Different data in each directory
        home_file = home_data_dir / "focus.2025-08-10.json"
        with open(home_file, 'w') as f:
            json.dump({"2025-08-10": {"total_time_minutes": 20, "time_per_goal": {"old": 20}}}, f)
        
        project_file = project_data_dir / "focus.2025-08-11.json"
        with open(project_file, 'w') as f:
            json.dump({"2025-08-11": {"total_time_minutes": 40, "time_per_goal": {"new": 40}}}, f)
        
        with patch('raycast_focus_tracker.menuBar.DATA_DIR', home_data_dir):
            from raycast_focus_tracker.menuBar import FocusApp
            
            with patch.object(FocusApp, '_start_background_tracker'), \
                 patch.object(FocusApp, '_parse_latest_logs'), \
                 patch.object(FocusApp, 'create_menu'), \
                 patch('raycast_focus_tracker.menuBar.update_streaks') as mock_update:
                
                # Mock the project directory path
                with patch.object(Path, '__truediv__', side_effect=lambda self, other: project_data_dir if other == "data" else self.__truediv__(other)):
                    app = FocusApp()
                    app._refresh_data()
                    
                    # Assert - should have data from both directories
                    call_args = mock_update.call_args[0]
                    daily_data = call_args[0]
                    assert "2025-08-10" in daily_data
                    assert "2025-08-11" in daily_data
                    assert daily_data["2025-08-10"]["time_per_goal"]["old"] == 20
                    assert daily_data["2025-08-11"]["time_per_goal"]["new"] == 40