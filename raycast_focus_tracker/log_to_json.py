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

STATE_FILE = Path.home() / ".raycast-focus-tracker" / ".parser_state.json"




def load_or_create_json(json_path):
    """Load existing JSON data or create empty structure.
    
    Args:
        json_path (str): Path to JSON file
        
    Returns:
        dict: Existing data or empty dict
    """
    try:
        json_file = Path(json_path)
        if json_file.exists():
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Validate that we got a dictionary
                if isinstance(data, dict):
                    return data
                else:
                    print(f"Warning: Invalid JSON structure in {json_path}, starting fresh")
                    return {}
    except (json.JSONDecodeError, PermissionError, OSError) as e:
        print(f"Warning: Could not load {json_path}: {e}, starting fresh")
    return {}


def load_parser_state(state_file_path):
    """Loads the parser state from a file."""
    state_file = Path(state_file_path)
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError, OSError) as e:
            print(f"Warning: Could not load parser state: {e}")
    return {}


def save_parser_state(state_file_path, state):
    """Saves the parser state to a file."""
    try:
        with open(state_file_path, 'w') as f:
            json.dump(state, f, indent=2)
    except (PermissionError, OSError, IOError) as e:
        print(f"Warning: Could not save parser state: {e}")


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
        # Return actual duration in minutes (can be 0 for very short sessions)
        return duration_minutes
    except Exception:
        return 0

def parse_activity_duration(duration_text):
    """Parse activity summary duration text to minutes.
    
    Args:
        duration_text (str): Duration from activity summary (e.g., "1 hour 22 minutes", "45 minutes")
        
    Returns:
        int: Duration in minutes, or None if parsing fails
    """
    try:
        if not duration_text or not isinstance(duration_text, str) or duration_text.strip() == "":
            return None
            
        duration_text = duration_text.strip().lower()
        total_minutes = 0
        
        # Parse hours
        import re
        hour_match = re.search(r'(\d+)\s*hour', duration_text)
        if hour_match:
            hours = int(hour_match.group(1))
            if hours >= 0:  # Validate non-negative
                total_minutes += hours * 60
        
        # Parse minutes
        minute_match = re.search(r'(\d+)\s*minute', duration_text)
        if minute_match:
            minutes = int(minute_match.group(1))
            if minutes >= 0:  # Validate non-negative
                total_minutes += minutes
        
        return total_minutes if total_minutes > 0 else None
    except (ValueError, AttributeError, TypeError) as e:
        print(f"Warning: Error parsing duration '{duration_text}': {e}")
        return None


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
    cleaned_count = 0
    for date_key, day_data in data.items():
        if 'active_sessions' not in day_data or 'items' not in day_data:
            continue
        
        # Get all completed session start_times
        completed_start_times = {
            item['start_time'] 
            for item in day_data['items']
            if item.get('state') == 'completed'
        }
        
        # Remove active sessions that are already completed
        active_sessions = day_data['active_sessions']
        stale_keys = []
        
        for session_key, session in active_sessions.items():
            if session['start_time'] in completed_start_times:
                stale_keys.append(session_key)
        
        for key in stale_keys:
            del active_sessions[key]
            cleaned_count += 1
    
    if cleaned_count > 0:
        print(f"Cleaned {cleaned_count} stale active sessions")


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
        # Set last completed goal for activity summary processing (preserve goal from completed session)
        completed_goal = session_to_complete.get('goal')
        current_session_data.clear()
        current_session_data['last_completed_goal'] = completed_goal
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
        "Source:": lambda l, d, c: None,  # Ignore source lines
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

def update_last_session_duration(data, current_session_data, activity_minutes):
    """Update the most recent session with activity summary duration.
    
    Args:
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
        activity_minutes (int): Duration from activity summary in minutes
    """
    goal = current_session_data.get('last_completed_goal')
    if not goal:
        return
    
    for date_key in reversed(list(data.keys())):
        if 'items' in data[date_key]:
            for session in reversed(data[date_key]['items']):
                if session.get('goal') == goal:
                    # Update actual_duration with activity summary duration
                    session['actual_duration'] = activity_minutes
                    # Recalculate totals for this date
                    _recalculate_totals(data, date_key)
                    return

def _recalculate_totals(data, date_key):
    """Recalculate total_time_minutes and time_per_goal for a specific date.
    
    Args:
        data (dict): Main data structure
        date_key (str): Date key to recalculate
    """
    if date_key not in data or 'items' not in data[date_key]:
        return
    
    total_time = 0
    time_per_goal = {}
    
    for item in data[date_key]['items']:
        if _should_count_session(item):
            duration = item.get('actual_duration', 0)
            goal = item.get('goal', 'unknown')
            
            total_time += duration
            time_per_goal[goal] = time_per_goal.get(goal, 0) + duration
    
    # Update the data structure
    data[date_key]['total_time_minutes'] = total_time
    data[date_key]['time_per_goal'] = time_per_goal


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
    """Find and remove active session to complete using chronological order."""
    active_sessions = day_data.get('active_sessions', {})
    
    if not active_sessions:
        return None, None
    
    # If we have a recent goal from current session data, try to match it first
    if recent_goal:
        matching_keys = [key for key in active_sessions.keys() 
                        if active_sessions[key]['goal'] == recent_goal]
        
        if matching_keys:
            # Take the most recent matching session (last one)
            session_key = matching_keys[-1]
            session = active_sessions.pop(session_key)
            return session, session_key
    
    # Fallback: find the chronologically oldest active session
    # This is most likely to be the one being completed
    if active_sessions:
        # Sort sessions by start_time to get the oldest one
        sessions_by_time = sorted(
            active_sessions.items(),
            key=lambda x: x[1]['start_time']
        )
        session_key, session = sessions_by_time[0]
        active_sessions.pop(session_key)
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
        
        # Parse and apply the duration to the last completed session
        activity_minutes = parse_activity_duration(duration_text)
        if activity_minutes is not None:
            update_last_session_duration(data, current_session_data, activity_minutes)

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
    try:
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (PermissionError, OSError, IOError) as e:
        print(f"Warning: Could not save to {json_path}: {e}")
    except TypeError as e:
        print(f"Warning: Data serialization error for {json_path}: {e}")

def parse_log_file(log_file_path, json_output_path):
    """Main function to parse log file and convert to JSON structure.
    
    Args:
        log_file_path (str): Path to input log file
        json_output_path (str): Path to output JSON file
        
    Returns:
        dict or None: Parsed data or None if failed
    """
    print(f"Parsing {log_file_path} -> {json_output_path}")
    
    parser_state = load_parser_state(STATE_FILE)
    last_processed_line = parser_state.get(log_file_path, 0)

    # Get current total lines in file
    try:
        with open(log_file_path, 'r') as f:
            total_lines = sum(1 for _ in f)
    except FileNotFoundError:
        print(f"Log file not found: {log_file_path}")
        return None

    print(f"Processing lines {last_processed_line + 1} to {total_lines}...")

    data = load_or_create_json(json_output_path)

    # If file has more lines than we processed last time, process the new lines
    if total_lines <= last_processed_line:
        print("No new lines to process.")
        return data

    # Clean up stale active sessions from previous parsing
    clean_stale_active_sessions(data)

    current_session_data = {}
    lines_processed = 0

    try:
        with open(log_file_path, 'r') as f:
            # Skip already processed lines
            for _ in range(last_processed_line):
                next(f)

            for line_num, line in enumerate(f, last_processed_line + 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    _process_log_line(line, data, current_session_data)
                    lines_processed += 1
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
                    print(f"Line content: {line}")
                    continue
    
    except FileNotFoundError:
        print(f"Error: Log file not found: {log_file_path}")
        return None
    except StopIteration:
        # This means we have reached the end of the file, which is fine
        pass
        
    if lines_processed == 0:
        print("No new lines to process.")
        return data

    # Finalize data
    recalculate_daily_totals(data)
    save_json(data, json_output_path)
    
    # Update parser state with total lines processed so far
    parser_state[log_file_path] = total_lines
    save_parser_state(STATE_FILE, parser_state)
    
    # Print summary
    total_days = len(data)
    total_sessions = sum(len(day_data.get('items', [])) for day_data in data.values())
    print(f"Processed {lines_processed} new lines, {total_days} days, {total_sessions} sessions")
    
    return data


def parse_log_file_to_separate_dates(log_file_path, output_dir):
    """Parse a log file and write each date's data to separate JSON files.
    
    Args:
        log_file_path (str): Path to the log file
        output_dir (str): Directory to write JSON files
    
    Returns:
        dict: Mapping of date -> json_file_path for files created
    """
    from pathlib import Path
    
    # First parse the log file normally
    temp_json = "/tmp/temp_parse.json"
    data = parse_log_file(log_file_path, temp_json)
    
    if not data:
        return {}
    
    output_dir = Path(output_dir)
    result = {}
    
    # Write each date's data to its own file
    for date, day_data in data.items():
        json_file = output_dir / f"focus.{date}.json"
        
        # Create single-date data structure
        single_date_data = {date: day_data}
        
        # If file exists, merge with existing data for that date only
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    existing_data = json.load(f)
                
                # Only keep data for this specific date
                if date in existing_data:
                    # Merge items and update totals
                    existing_items = existing_data[date].get('items', [])
                    new_items = day_data.get('items', [])
                    
                    # Combine and deduplicate items based on start_time
                    all_items = existing_items + new_items
                    seen_start_times = set()
                    unique_items = []
                    
                    for item in all_items:
                        if item['start_time'] not in seen_start_times:
                            unique_items.append(item)
                            seen_start_times.add(item['start_time'])
                    
                    # Update the day data with unique items
                    single_date_data[date]['items'] = unique_items
                    
            except Exception as e:
                print(f"Warning: Could not merge existing data for {date}: {e}")
        
        # Recalculate totals for this date only
        recalculate_daily_totals(single_date_data)
        
        # Clean stale sessions for this date only
        clean_stale_active_sessions(single_date_data)
        
        # Save to date-specific file
        save_json(single_date_data, str(json_file))
        result[date] = str(json_file)
    
    # Clean up temp file
    # try:
    #     Path(temp_json).unlink(missing_ok=True)
    # except:
    #     pass
    
    return result


def _process_log_line(line, data, current_session_data):
    """Process a single log line.
    
    Args:
        line (str): Log line to process
        data (dict): Main data structure
        current_session_data (dict): Session tracking data
    """
    try:
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
                try:
                    handler(line, data, current_session_data)
                    matched = True
                    break
                except Exception as e:
                    # Log the error but continue processing
                    print(f"Warning: Error in handler for '{key}': {e}")
                    continue
    except Exception as e:
        # Catch any unexpected errors in the main processing logic
        print(f"Warning: Error processing log line: {e}")
        print(f"Line content: {line}")
        pass
    

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
    # Preserve last_completed_goal for activity summary processing
    last_goal = current_session_data.get('last_completed_goal')
    # Clear all session state - form reset indicates we're starting fresh
    current_session_data.clear()
    # Restore the last completed goal for activity summary processing
    if last_goal:
        current_session_data['last_completed_goal'] = last_goal


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
