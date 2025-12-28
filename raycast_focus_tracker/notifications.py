#!/usr/bin/env python3
"""Streak Notifications Module

Sends macOS notifications for streak milestones and motivational messages.
Uses osascript for native macOS notifications (no dependencies).
"""

import random
import subprocess

MILESTONES = [3, 5, 7, 10, 14, 21, 30, 50, 100]

MOTIVATIONAL_QUOTES = [
    "Every expert was once a beginner. Start again!",
    "The only failure is not trying. Let's go!",
    "Today is a new opportunity. Make it count!",
    "Small steps lead to big changes. Begin now!",
    "Your next streak starts today!",
]


def send_notification(title, message, sound=False):
    """Send a macOS notification using osascript.

    Args:
        title (str): Notification title
        message (str): Notification body text
        sound (bool): Whether to play a sound
    """
    sound_str = 'with sound name "default"' if sound else ""
    script = f'display notification "{message}" with title "{title}" {sound_str}'

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5
        )
    except Exception:
        pass  # Silently ignore notification failures


def check_and_notify_streak(current, previous, longest):
    """Check streak changes and send appropriate notifications.

    Args:
        current (int): Current streak count
        previous (int): Previous streak count (before this update)
        longest (int): Longest streak ever achieved
    """
    # First day of a new streak
    if current == 1 and previous == 0:
        send_notification(
            "Focus Streak Started!",
            "You started a new streak. Keep it going!",
            sound=True
        )
        return

    # Streak broken
    if current == 0 and previous > 0:
        quote = random.choice(MOTIVATIONAL_QUOTES)
        send_notification(
            "Streak Reset",
            quote,
            sound=False
        )
        return

    # New personal record
    if current > longest and current > 1:
        send_notification(
            "New Personal Record!",
            f"{current}-day streak! You've beaten your best!",
            sound=True
        )
        return

    # Milestone reached
    if current in MILESTONES and current > previous:
        send_notification(
            f"{current}-Day Streak!",
            f"Amazing! You've maintained focus for {current} days!",
            sound=True
        )
        return
