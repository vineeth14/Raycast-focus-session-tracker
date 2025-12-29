"""Unit tests for notifications.py module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from raycast_focus_tracker.notifications import (
    send_notification,
    check_and_notify_streak,
    MILESTONES,
    MOTIVATIONAL_QUOTES
)


class TestNotifications:
    """Test notification functions."""

    def test_milestones_defined(self):
        """Test that milestones are properly defined."""
        assert MILESTONES == [3, 5, 7, 10, 14, 21, 30, 50, 100]

    def test_motivational_quotes_exist(self):
        """Test that motivational quotes are defined."""
        assert len(MOTIVATIONAL_QUOTES) > 0
        for quote in MOTIVATIONAL_QUOTES:
            assert isinstance(quote, str)
            assert len(quote) > 0

    @patch('subprocess.run')
    def test_send_notification_basic(self, mock_run):
        """Test basic notification sending."""
        send_notification("Test Title", "Test Message")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "osascript"
        assert "Test Title" in call_args[0][0][2]
        assert "Test Message" in call_args[0][0][2]

    @patch('subprocess.run')
    def test_send_notification_with_sound(self, mock_run):
        """Test notification with sound enabled."""
        send_notification("Test", "Message", sound=True)

        call_args = mock_run.call_args
        assert 'with sound name "default"' in call_args[0][0][2]

    @patch('subprocess.run')
    def test_send_notification_without_sound(self, mock_run):
        """Test notification without sound."""
        send_notification("Test", "Message", sound=False)

        call_args = mock_run.call_args
        assert 'with sound name' not in call_args[0][0][2]

    @patch('subprocess.run', side_effect=Exception("Test error"))
    def test_send_notification_handles_errors(self, mock_run):
        """Test that send_notification handles errors gracefully."""
        # Should not raise exception
        send_notification("Test", "Message")


class TestCheckAndNotifyStreak:
    """Test streak notification logic."""

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_first_day_streak_no_notification(self, mock_notify):
        """Test that no notification is sent for first day of a new streak."""
        check_and_notify_streak(current=1, previous=0, longest=5)

        # No daily notifications for starting a streak
        mock_notify.assert_not_called()

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_streak_broken(self, mock_notify):
        """Test notification when streak is broken."""
        check_and_notify_streak(current=0, previous=5, longest=10)

        mock_notify.assert_called_once()
        args = mock_notify.call_args[0]
        assert args[0] == "Raycast Focus Tracker"
        assert "Streak Reset" in args[1]
        # Message should contain one of the motivational quotes
        assert any(quote in args[1] for quote in MOTIVATIONAL_QUOTES)

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_new_record(self, mock_notify):
        """Test notification for new personal record."""
        check_and_notify_streak(current=11, previous=10, longest=10)

        mock_notify.assert_called_once()
        args = mock_notify.call_args[0]
        assert args[0] == "Raycast Focus Tracker"
        assert "New Record" in args[1]
        assert "11" in args[1]

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_milestone_reached(self, mock_notify):
        """Test notification when milestone is reached."""
        check_and_notify_streak(current=7, previous=6, longest=10)

        mock_notify.assert_called_once()
        args = mock_notify.call_args[0]
        assert args[0] == "Raycast Focus Tracker"
        assert "7" in args[1]

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_no_notification_for_regular_day(self, mock_notify):
        """Test that no notification is sent for regular streak continuation."""
        check_and_notify_streak(current=4, previous=3, longest=10)

        # 4 is not a milestone, not first day, not broken, not record
        mock_notify.assert_not_called()

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_no_notification_when_same_streak(self, mock_notify):
        """Test that no notification is sent when streak hasn't changed."""
        check_and_notify_streak(current=5, previous=5, longest=10)

        mock_notify.assert_not_called()

    @patch('raycast_focus_tracker.notifications.send_notification')
    def test_all_milestones(self, mock_notify):
        """Test that all milestones trigger notifications."""
        for milestone in MILESTONES:
            mock_notify.reset_mock()
            check_and_notify_streak(
                current=milestone,
                previous=milestone-1,
                longest=milestone+10
            )
            mock_notify.assert_called_once()
