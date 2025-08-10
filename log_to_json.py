#!/usr/bin/env python3
"""
Focus Session Log Parser
Converts Raycast focus session logs to structured JSON format.
"""

import json
import re
from datetime import datetime
from pathlib import Path


def load_or_create_json(json_path):
    """Load existing JSON data or create empty structure."""
    if Path(json_path).exists():
        with open(json_path, 'r') as f:
            return json.load(f)
    else:
        return {}


def get_date_from_timestamp(timestamp_str):
    """Parse timestamp string to date key format."""
    # Parse "2025-08-10 14:18:11.777" -> "2025-08-10"
    dt = datetime.fromisoformat(timestamp_str.split('.')[0])
    return dt.strftime('%Y-%m-%d')


def extract_timestamp(line):
    """Extract timestamp from log line."""
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
    return match.group(1) if match else None


def calculate_duration(start_time, end_time):
    """Calculate duration in minutes between two timestamps."""
    try:
        start = datetime.fromisoformat(start_time.split('.')[0])
        end = datetime.fromisoformat(end_time.split('.')[0])
        return int((end - start).total_seconds() / 60)
    except:
        return 0


def initialize_day_data(data, date_key):
    """Initialize day structure if it doesn't exist."""
    if date_key not in data:
        data[date_key] = {
            "total_time_minutes": 0,
            "time_per_goal": {},
            "items": [],
            "active_sessions": {}
        }


def handle_session_start(line, data, current_session_data):
    """Handle 'Start focus session' log line."""
    timestamp = extract_timestamp(line)
    if not timestamp:
        return
    
    date_key = get_date_from_timestamp(timestamp)
    initialize_day_data(data, date_key)
    
    # Store current session info for subsequent lines
    current_session_data.update({
        'timestamp': timestamp,
        'date_key': date_key,
        'start_time': timestamp
    })


def extract_goal(line, current_session_data):
    """Extract goal from 'Goal: ...' line."""
    if "Goal:" in line:
        goal = line.split("Goal:")[1].strip()
        current_session_data['goal'] = goal




def add_to_active_sessions(data, current_session_data):
    """Add session to active_sessions once we have goal."""
    if not all(k in current_session_data for k in ['goal', 'date_key', 'start_time']):
        return
    
    goal = current_session_data['goal']
    date_key = current_session_data['date_key']
    start_time = current_session_data['start_time']
    
    # Check if session with same goal and start_time already exists in completed items
    for item in data[date_key].get('items', []):
        if (item.get('goal') == goal and 
            item.get('start_time') == start_time):
            # Session already processed, skip
            return
    
    # Check if already in active sessions
    if goal in data[date_key]['active_sessions']:
        existing_start = data[date_key]['active_sessions'][goal].get('start_time')
        if existing_start == start_time:
            # Same session already active, skip
            return
    
    # Add to active sessions
    data[date_key]['active_sessions'][goal] = {
        'goal': goal,
        'start_time': start_time,
        'state': 'started'
    }


def handle_session_end(line, data, current_session_data):
    """Handle 'Complete focus session' or 'Cancel focus session' lines."""
    timestamp = extract_timestamp(line)
    if not timestamp:
        return
    
    date_key = get_date_from_timestamp(timestamp)
    initialize_day_data(data, date_key)
    
    # Try to find matching active session by most recent goal
    recent_goal = current_session_data.get('goal')
    
    # Check if this session end is already processed by looking for completed session with matching end_time
    for item in data[date_key].get('items', []):
        if (item.get('goal') == recent_goal and 
            item.get('end_time') == timestamp and
            item.get('state') == 'completed'):
            # Session already completed, skip
            return
    
    # Look for active session to complete
    session_to_complete = None
    goal_key = None
    
    if recent_goal and recent_goal in data[date_key]['active_sessions']:
        session_to_complete = data[date_key]['active_sessions'].pop(recent_goal)
        goal_key = recent_goal
    elif data[date_key]['active_sessions']:
        # Fallback: take the most recent active session
        goal_key = list(data[date_key]['active_sessions'].keys())[-1]
        session_to_complete = data[date_key]['active_sessions'].pop(goal_key)
    
    if session_to_complete:
        # Only calculate if not already completed
        if session_to_complete.get('state') != 'completed':
            # Complete the session
            session_to_complete.update({
                'end_time': timestamp,
                'cancelled': "Cancel" in line,
                'actual_duration': calculate_duration(session_to_complete['start_time'], timestamp),
                'pauses': 0,  # Will be updated by activity summary
                'blocks': 0,
                'snoozes': 0,
                'state': 'completed'  # Mark as completed to prevent recalculation
            })
        
        data[date_key]['items'].append(session_to_complete)
        
        # Store for activity summary matching
        current_session_data['last_completed_goal'] = goal_key


def handle_activity_summary_line(line, data, current_session_data):
    """Handle activity summary lines (Start date, Pauses Count, etc.)."""
    if "Start date:" in line:
        # Extract start date to match with recent session
        match = re.search(r'Start date: (.+)', line)
        if match:
            current_session_data['activity_start_date'] = match.group(1).strip()
    
    elif "Duration:" in line and current_session_data.get('in_activity_summary'):
        # This is actual duration from activity summary
        duration_text = line.split("Duration:")[1].strip()
        current_session_data['activity_duration'] = duration_text
    
    elif "Pauses Count:" in line:
        match = re.search(r'Pauses Count: (\d+)', line)
        if match:
            update_last_session_stat(data, current_session_data, 'pauses', int(match.group(1)))
    
    elif "Block Events Count:" in line:
        match = re.search(r'Block Events Count: (\d+)', line)
        if match:
            update_last_session_stat(data, current_session_data, 'blocks', int(match.group(1)))
    
    elif "Snooze Events Count:" in line:
        match = re.search(r'Snooze Events Count: (\d+)', line)
        if match:
            update_last_session_stat(data, current_session_data, 'snoozes', int(match.group(1)))


def update_last_session_stat(data, current_session_data, stat_name, value):
    """Update the most recent session with activity summary stats."""
    goal = current_session_data.get('last_completed_goal')
    if not goal:
        return
    
    # Find the most recent session for this goal
    for date_key in reversed(list(data.keys())):
        if 'items' in data[date_key]:
            for session in reversed(data[date_key]['items']):
                if session.get('goal') == goal:
                    session[stat_name] = value
                    return


def recalculate_daily_totals(data):
    """Recalculate total_time_minutes and time_per_goal for each day."""
    for date_key in data:
        if 'items' in data[date_key]:
            # Calculate total time and time per goal
            total_time = 0
            time_per_goal = {}
            
            for item in data[date_key]['items']:
                # Only count completed, non-cancelled sessions
                if (item.get('state') == 'completed' and 
                    not item.get('cancelled', False)):
                    duration = item.get('actual_duration', 0)
                    goal = item.get('goal', 'unknown')
                    
                    total_time += duration
                    time_per_goal[goal] = time_per_goal.get(goal, 0) + duration
            
            data[date_key]['total_time_minutes'] = total_time
            data[date_key]['time_per_goal'] = time_per_goal


def save_json(data, json_path):
    """Save data to JSON file with pretty formatting."""
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_log_file(log_file_path, json_output_path):
    """Main function to parse log file and convert to JSON structure."""
    print(f"Parsing {log_file_path} -> {json_output_path}")
    
    # Load existing JSON or create empty structure
    data = load_or_create_json(json_output_path)
    
    # Track current session data across lines
    current_session_data = {}
    
    try:
        with open(log_file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Handle different log line types
                    if "Start focus session" in line:
                        handle_session_start(line, data, current_session_data)
                    
                    elif "Goal:" in line:
                        extract_goal(line, current_session_data)
                        # Add to active sessions once we have the goal
                        if 'start_time' in current_session_data:
                            add_to_active_sessions(data, current_session_data)
                    
                    elif "Complete focus session" in line or "Cancel focus session" in line:
                        handle_session_end(line, data, current_session_data)
                    
                    elif "Focus session activity summary" in line:
                        current_session_data['in_activity_summary'] = True
                    
                    elif current_session_data.get('in_activity_summary'):
                        handle_activity_summary_line(line, data, current_session_data)
                    
                    elif "Restoring stored form state" in line:
                        # Reset session data for form state
                        current_session_data = {}
                
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
                    print(f"Line content: {line}")
                    continue
    
    except FileNotFoundError:
        print(f"Error: Log file not found: {log_file_path}")
        return
    
    # Recalculate daily totals
    recalculate_daily_totals(data)
    
    # Save updated JSON
    save_json(data, json_output_path)
    
    # Print summary
    total_days = len(data)
    total_sessions = sum(len(day_data.get('items', [])) for day_data in data.values())
    print(f"Processed {total_days} days, {total_sessions} sessions")
    
    return data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python log_to_json.py <log_file> [output_file]")
        print("Example: python log_to_json.py focus.2025-08-10.log data/2025-08-10.json")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    # Default output file based on input name
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # Generate output filename from input
        log_path = Path(log_file)
        output_file = f"data/{log_path.stem}.json"
    
    # Parse the log file
    result = parse_log_file(log_file, output_file)
    
    if result:
        print(f"✅ Successfully converted to {output_file}")
    else:
        print("❌ Conversion failed")