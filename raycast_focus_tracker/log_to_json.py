#!/usr/bin/env python3
"""Focus Session Log Parser

Converts Raycast focus session logs from raw log format to structured JSON.
Handles session starts, completions, cancellations, and activity summaries.

Usage:
    python log_to_json.py <log_file> [output_file]
    
Example:
    python log_to_json.py focus.2025-08-10.log data/focus.2025-08-10.json
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


def load_or_create_json(json_path):
    """Load existing JSON data or create empty structure.
    
    Args:
        json_path (str): Path to JSON file
        
    Returns:
        dict: Existing data or empty dict
    """
    json_file = Path(json_path)
    if json_file.exists():
        with open(json_file, 'r') as f:
            return json.load(f)
    return {}


def get_date_from_timestamp(timestamp_str):
    """Parse timestamp string to date key format.
    
    Args:
        timestamp_str (str): Timestamp in format "2025-08-10 14:18:11.777"
        
    Returns:
        str: Date in "YYYY-MM-DD" format
    """
    dt = datetime.fromisoformat(timestamp_str.split('.')[0])
    return dt.strftime('%Y-%m-%d')


def extract_timestamp(line):
    """Extract timestamp from log line.
    
    Args:
        line (str): Log line text
        
    Returns:
        str or None: Timestamp if found, None otherwise
    """
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
    return match.group(1) if match else None


def calculate_duration(start_time, end_time):
    """Calculate duration in minutes between two timestamps.
    
    Args:
        start_time (str): Start timestamp
        end_time (str): End timestamp
        
    Returns:
        int: Duration in minutes, minimum 1 for completed sessions
    """
    try:
        start = datetime.fromisoformat(start_time.split('.')[0])
        end = datetime.fromisoformat(end_time.split('.')[0])
        duration_seconds = (end - start).total_seconds()
        duration_minutes = int(duration_seconds / 60)
        # Return at least 1 minute for any completed session to ensure it counts
        return max(1, duration_minutes) if duration_seconds > 0 else 0
    except Exception:
        return 0


def initialize_day_data(data, date_key):
    """Initialize day structure if it doesn't exist.
    
    Args:
        data (dict): Main data structure
        date_key (str): Date in "YYYY-MM-DD" format
    """
    if date_key not in data:
        data[date_key] = {
            "total_time_minutes": 0,
            "time_per_goal": {},
            "items": [],
            "active_sessions": {}
        }

def clean_stale_active_sessions(data):
    """Remove stale active sessions that have corresponding completed items.
    
    Args:
        data (dict): Main data structure to clean
    """
    for date_key, day_data in data.items():
        if 'active_sessions' not in day_data or 'items' not in day_data:
            continue
        
        # Get all completed session (goal, start_time) pairs
        completed_sessions = {
            (item['goal'], item['start_time']) 
            for item in day_data['items']
            if item.get('state') == 'completed'
        }
        
        # Remove active sessions that are already completed
        active_sessions = day_data['active_sessions']
        stale_keys = []
        
        for session_key, session in active_sessions.items():
            session_pair = (session['goal'], session['start_time'])
            if session_pair in completed_sessions:
                stale_keys.append(session_key)
        
        for key in stale_keys:
            del active_sessions[key]


def handle_session_start(line, data, current_session_data):
    """Handle 'Start focus session' log line.
    
    Args:
        line (str): Log line containing session start
        data (dict): Main data structure
        current_session_data (dict): Tracking data for current session
    """
    timestamp = extract_timestamp(line)
    if not timestamp:
        return
    
    date_key = get_date_from_timestamp(timestamp)
    initialize_day_data(data, date_key)
    
    current_session_data.update({
        'timestamp': timestamp,
        'date_key': date_key,
        'start_time': timestamp
    })


def extract_goal(line, current_session_data):
    """Extract goal from 'Goal: ...' line.
    
    Args:
        line (str): Log line containing goal information
        current_session_data (dict): Tracking data for current session
    """
    if "Goal:" in line:
        goal = line.split("Goal:")[1].strip()
        current_session_data['goal'] = goal


def add_to_active_sessions(data, current_session_data):
    """Add session to active_sessions once we have goal.
    
    Args:
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
    """
    required_keys = ['goal', 'date_key', 'start_time']
    if not all(k in current_session_data for k in required_keys):
        return
    
    goal = current_session_data['goal']
    date_key = current_session_data['date_key']
    start_time = current_session_data['start_time']
    
    # Skip if session already processed
    if _session_already_exists(data[date_key], goal, start_time):
        return
    
    # Use goal + start_time as unique key for active sessions
    session_key = f"{goal}_{start_time}"
    
    # Add to active sessions with unique key
    data[date_key]['active_sessions'][session_key] = {
        'goal': goal,
        'start_time': start_time,
        'state': 'started'
    }

def handle_session_end(line, data, current_session_data):
    """Handle 'Complete focus session' or 'Cancel focus session' lines.
    
    Args:
        line (str): Log line containing session end
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
    """
    timestamp = extract_timestamp(line)
    if not timestamp:
        return
    
    date_key = get_date_from_timestamp(timestamp)
    initialize_day_data(data, date_key)
    
    recent_goal = current_session_data.get('goal')
    
    # Debug print
    
    # Skip if session already completed
    if _session_end_already_processed(data[date_key], recent_goal, timestamp):
        return
    
    # Find and complete active session
    session_to_complete, goal_key = _find_active_session(
        data[date_key], recent_goal
    )
    
    if session_to_complete:
        _complete_session(session_to_complete, timestamp, line)
        data[date_key]['items'].append(session_to_complete)
        current_session_data['last_completed_goal'] = goal_key
        # Clear session state after completion to prepare for next session
        current_session_data.clear()
    else:
        pass  # No active session found

def handle_activity_summary_line(line, data, current_session_data):
    """Handle activity summary lines (Start date, Pauses Count, etc.).
    
    Args:
        line (str): Log line from activity summary
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
    """
    summary_handlers = {
        "Start date:": _handle_start_date,
        "Duration:": _handle_duration,
        "Pauses Count:": lambda l, d, c: _handle_count_stat(l, d, c, 'pauses'),
        "Block Events Count:": lambda l, d, c: _handle_count_stat(l, d, c, 'blocks'),
        "Snooze Events Count:": lambda l, d, c: _handle_count_stat(l, d, c, 'snoozes')
    }
    
    matched = False
    for key, handler in summary_handlers.items():
        if key in line:
            handler(line, data, current_session_data)
            matched = True
            break
    
    # Check if we've finished the activity summary (no more matching lines)
    if not matched and not any(key in line for key in summary_handlers.keys()) and line.strip():
        # If we encounter a non-summary line, exit activity summary mode
        if 'in_activity_summary' in current_session_data:
            del current_session_data['in_activity_summary']

def update_last_session_stat(data, current_session_data, stat_name, value):
    """Update the most recent session with activity summary stats.
    
    Args:
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
        stat_name (str): Name of statistic to update
        value (int): Value to set
    """
    goal = current_session_data.get('last_completed_goal')
    if not goal:
        return
    
    for date_key in reversed(list(data.keys())):
        if 'items' in data[date_key]:
            for session in reversed(data[date_key]['items']):
                if session.get('goal') == goal:
                    session[stat_name] = value
                    return


# Helper functions for session processing

def _session_already_exists(day_data, goal, start_time):
    """Check if session already exists in active sessions (only block active duplicates)."""
    # Only check active sessions - don't block re-processing completed sessions
    # This allows re-parsing to work correctly
    session_key = f"{goal}_{start_time}"
    return session_key in day_data.get('active_sessions', {})

def _session_end_already_processed(day_data, goal, timestamp):
    """Check if session end is already processed."""
    for item in day_data.get('items', []):
        if (
            item.get('goal') == goal and 
            item.get('end_time') == timestamp and
            item.get('state') == 'completed'):
            return True
    return False

def _find_active_session(day_data, recent_goal):
    """Find and remove active session to complete."""
    active_sessions = day_data.get('active_sessions', {})
    
    if not active_sessions:
        return None, None
    
    # Look for active session matching the goal
    matching_keys = [key for key in active_sessions.keys() 
                    if active_sessions[key]['goal'] == recent_goal]
    
    if matching_keys:
        # Take the most recent matching session (last one)
        session_key = matching_keys[-1]
        session = active_sessions.pop(session_key)
        return session, session_key
    elif active_sessions:
        # Fallback: take most recent active session of any goal
        session_key = list(active_sessions.keys())[-1]
        session = active_sessions.pop(session_key)
        return session, session_key
    
    return None, None

def _complete_session(session, timestamp, line):
    """Complete a session with end details."""
    if session.get('state') != 'completed':
        session.update({
            'end_time': timestamp,
            'cancelled': "Cancel" in line,
            'actual_duration': calculate_duration(session['start_time'], timestamp),
            'pauses': 0,
            'blocks': 0,
            'snoozes': 0,
            'state': 'completed'
        })

def _handle_start_date(line, data, current_session_data):
    """Handle start date from activity summary."""
    match = re.search(r'Start date: (.+)', line)
    if match:
        current_session_data['activity_start_date'] = match.group(1).strip()

def _handle_duration(line, data, current_session_data):
    """Handle duration from activity summary."""
    if current_session_data.get('in_activity_summary'):
        duration_text = line.split("Duration:")[1].strip()
        current_session_data['activity_duration'] = duration_text

def _handle_count_stat(line, data, current_session_data, stat_name):
    """Handle count statistics from activity summary."""
    pattern = f"{stat_name.title().replace('s', 'es')} Count: (\\d+)"
    if stat_name == 'pauses':
        pattern = "Pauses Count: (\\d+)"
    
    match = re.search(pattern, line)
    if match:
        update_last_session_stat(data, current_session_data, stat_name, int(match.group(1)))

def recalculate_daily_totals(data):
    """Recalculate total_time_minutes and time_per_goal for each day.
    
    Args:
        data (dict): Main data structure to update
    """
    for date_key in data:
        if 'items' not in data[date_key]:
            continue
            
        total_time = 0
        time_per_goal = {}
        
        for item in data[date_key]['items']:
            if _should_count_session(item):
                duration = item.get('actual_duration', 0)
                goal = item.get('goal', 'unknown')
                
                total_time += duration
                time_per_goal[goal] = time_per_goal.get(goal, 0) + duration
        
        data[date_key]['total_time_minutes'] = total_time
        data[date_key]['time_per_goal'] = time_per_goal

def _should_count_session(item):
    """Check if session should be counted in daily totals.
    
    Args:
        item (dict): Session item
        
    Returns:
        bool: True if session should be counted
    """
    return (
        item.get('state') == 'completed' and 
        not item.get('cancelled', False))

def save_json(data, json_path):
    """Save data to JSON file with pretty formatting.
    
    Args:
        data (dict): Data to save
        json_path (str): Output file path
    """
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def parse_log_file(log_file_path, json_output_path):
    """Main function to parse log file and convert to JSON structure.
    
    Args:
        log_file_path (str): Path to input log file
        json_output_path (str): Path to output JSON file
        
    Returns:
        dict or None: Parsed data or None if failed
    """
    print(f"Parsing {log_file_path} -> {json_output_path}")
    
    data = load_or_create_json(json_output_path)
    
    # Clean up stale active sessions from previous parsing
    clean_stale_active_sessions(data)
    
    current_session_data = {}
    
    try:
        with open(log_file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                
                try:
                    _process_log_line(line, data, current_session_data)
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
                    print(f"Line content: {line}")
                    continue
    
    except FileNotFoundError:
        print(f"Error: Log file not found: {log_file_path}")
        return None
    
    # Finalize data
    recalculate_daily_totals(data)
    save_json(data, json_output_path)
    
    # Print summary
    total_days = len(data)
    total_sessions = sum(len(day_data.get('items', [])) for day_data in data.values())
    print(f"Processed {total_days} days, {total_sessions} sessions")
    
    return data


def _process_log_line(line, data, current_session_data):
    """Process a single log line.
    
    Args:
        line (str): Log line to process
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
    """
    line_handlers = {
        "Start focus session": handle_session_start,
        "Goal:": _handle_goal_line,
        "Complete focus session": handle_session_end,
        "Cancel focus session": handle_session_end,
        "Focus session activity summary": _handle_activity_summary_start,
        "Restoring stored form state": _handle_form_state_reset
    }
    
    # Check for activity summary lines first
    if current_session_data.get('in_activity_summary'):
        handle_activity_summary_line(line, data, current_session_data)
        return
    
    # Process other line types
    matched = False
    for key, handler in line_handlers.items():
        if key in line:
            handler(line, data, current_session_data)
            matched = True
            break
    

def _handle_goal_line(line, data, current_session_data):
    """Handle goal extraction and session activation."""
    extract_goal(line, current_session_data)
    if 'start_time' in current_session_data:
        add_to_active_sessions(data, current_session_data)

def _handle_activity_summary_start(line, data, current_session_data):
    """Mark start of activity summary section."""
    current_session_data['in_activity_summary'] = True

def _handle_form_state_reset(line, data, current_session_data):
    """Reset session tracking data completely to prepare for new session."""
    # Clear all session state - form reset indicates we're starting fresh
    current_session_data.clear()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python log_to_json.py <log_file> [output_file]")
        print("Example: python log_to_json.py focus.2025-08-10.log data/2025-08-10.json")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        log_path = Path(log_file)
        output_file = f"data/{log_path.stem}.json"
    
    result = parse_log_file(log_file, output_file)
    
    if result:
        print(f"✅ Successfully converted to {output_file}")
    else:
        print("❌ Conversion failed")
