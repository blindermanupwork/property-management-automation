#!/usr/bin/env python3
"""
Create a timeline of UID events - when added, modified, removed
Searches through ICS sync logs and Airtable records
"""
import sys
import re
from datetime import datetime, timedelta
import subprocess
import argparse
import os

def search_ics_logs_by_date(uid, start_date=None, end_date=None):
    """Search ICS logs for a UID within a date range"""
    log_dir = "/home/opc/automation/src/automation/logs"
    events = []
    
    # Define patterns to look for
    patterns = {
        'new_event': r'Creating new record.*Status:\s*New',
        'modified_event': r'Updating existing record.*Status:\s*Modified',
        'removed_event': r'Mark.*as Removed|Setting status to.*Removed',
        'marked_old': r'Mark.*as.*Old|Setting status to.*Old',
        'duplicate': r'duplicate.*detected|Ignoring duplicate',
        'feed_complete': r'Feed.*completed:.*(\d+) new.*(\d+) modified.*(\d+) removed',
        'processing': r'Processing event|Found existing record'
    }
    
    # Search through logs
    try:
        # Build grep command to search for UID
        if start_date and end_date:
            # Convert dates to grep-friendly format
            date_pattern = f"2025-0[6-9]-[0-9][0-9]"  # Adjust based on your date range
        else:
            date_pattern = "2025-[0-9][0-9]-[0-9][0-9]"
        
        cmd = f'grep -h "{uid}" {log_dir}/ics_sync.log {log_dir}/automation_prod*.log 2>/dev/null | grep -E "^{date_pattern}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                # Extract timestamp
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not timestamp_match:
                    continue
                    
                timestamp = timestamp_match.group(1)
                
                # Check date range if specified
                if start_date and end_date:
                    line_date = datetime.strptime(timestamp.split()[0], '%Y-%m-%d')
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    if not (start <= line_date <= end):
                        continue
                
                # Determine event type
                event_info = None
                
                # Check for new record
                if ('Creating new record' in line and 'Status: New' in line) or \
                   ('Creating new record' in line and uid in line) or \
                   ('New reservation' in line and uid in line) or \
                   ('new events processed' in line and uid in line):
                    event_info = {
                        'type': 'ADDED',
                        'description': 'New reservation added to Airtable',
                        'status': 'New'
                    }
                # Check for modification
                elif 'Updating existing record' in line or ('Modified' in line and 'Status' in line):
                    event_info = {
                        'type': 'MODIFIED',
                        'description': 'Reservation modified',
                        'status': 'Modified'
                    }
                # Check for removal
                elif ('Mark' in line and 'Removed' in line) or \
                     ('Setting status to \'Removed\'' in line) or \
                     ('Mark' in line and 'as Removed' in line) or \
                     ('removed events' in line and uid in line):
                    event_info = {
                        'type': 'REMOVED',
                        'description': 'Reservation removed from ICS feed',
                        'status': 'Removed'
                    }
                # Check for marked as old
                elif 'Mark' in line and 'Old' in line:
                    event_info = {
                        'type': 'MARKED_OLD',
                        'description': 'Previous version marked as Old',
                        'status': 'Old'
                    }
                # Check for duplicate
                elif 'duplicate' in line.lower():
                    event_info = {
                        'type': 'DUPLICATE',
                        'description': 'Duplicate reservation detected',
                        'status': 'Duplicate'
                    }
                # Feed processing summary
                elif 'Feed' in line and 'completed:' in line and uid in line:
                    match = re.search(r'(\d+) new.*(\d+) modified.*(\d+) removed', line)
                    if match:
                        event_info = {
                            'type': 'FEED_SUMMARY',
                            'description': f'Feed processed: {match.group(1)} new, {match.group(2)} modified, {match.group(3)} removed',
                            'status': 'Summary'
                        }
                
                if event_info:
                    events.append({
                        'timestamp': timestamp,
                        'type': event_info['type'],
                        'description': event_info['description'],
                        'raw_line': line.strip()
                    })
                    
    except Exception as e:
        print(f"Error searching logs: {e}")
    
    return sorted(events, key=lambda x: x['timestamp'])

def create_timeline(uid, days_back=30):
    """Create a visual timeline of UID events"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    print(f"\n📊 Timeline for UID: {uid}")
    print(f"📅 Period: {start_date} to {end_date}")
    print("=" * 80)
    
    events = search_ics_logs_by_date(uid, start_date, end_date)
    
    # Filter out duplicates and only keep meaningful events
    meaningful_events = [e for e in events if e['type'] in ['ADDED', 'MODIFIED', 'REMOVED', 'MARKED_OLD']]
    
    if not meaningful_events:
        print("\n❌ No meaningful events (added/modified/removed) found in this period")
        print("   Searching further back may reveal when this UID was added...")
        return
    
    # Group events by date
    events_by_date = {}
    for event in meaningful_events:
        date = event['timestamp'].split()[0]
        if date not in events_by_date:
            events_by_date[date] = []
        events_by_date[date].append(event)
    
    # Display timeline - only show dates with meaningful events
    for date in sorted(events_by_date.keys()):
        print(f"\n📅 {date}")
        print("-" * 60)
        
        for event in events_by_date[date]:
            time = event['timestamp'].split()[1]
            icon = {
                'ADDED': '✅',
                'MODIFIED': '📝',
                'REMOVED': '❌',
                'MARKED_OLD': '🔄',
                'DUPLICATE': '👥',
                'FEED_SUMMARY': '📊'
            }.get(event['type'], '•')
            
            print(f"  {time} {icon} {event['type']}: {event['description']}")
            
            # Show raw line for context if it's not too long
            if len(event['raw_line']) < 150:
                print(f"           Raw: {event['raw_line']}")
    
    # Summary - only count meaningful events
    print(f"\n📈 Summary:")
    type_counts = {}
    for event in meaningful_events:
        type_counts[event['type']] = type_counts.get(event['type'], 0) + 1
    
    for event_type, count in sorted(type_counts.items()):
        print(f"   {event_type}: {count} occurrence(s)")
    
    # Find key events
    added = next((e for e in meaningful_events if e['type'] == 'ADDED'), None)
    removed = next((e for e in reversed(meaningful_events) if e['type'] == 'REMOVED'), None)
    
    if added:
        print(f"\n   ➕ First added: {added['timestamp']}")
    if removed:
        print(f"   ➖ Removed: {removed['timestamp']}")
        if added and removed:
            # Calculate lifetime
            added_dt = datetime.strptime(added['timestamp'], '%Y-%m-%d %H:%M:%S')
            removed_dt = datetime.strptime(removed['timestamp'], '%Y-%m-%d %H:%M:%S')
            lifetime = removed_dt - added_dt
            print(f"   ⏱️  Lifetime: {lifetime.days} days, {lifetime.seconds//3600} hours")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Track UID timeline')
    parser.add_argument('uid', help='The UID to track')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='Number of days to look back (default: 30)')
    parser.add_argument('--start-date', '-s', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', '-e', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.start_date and args.end_date:
        events = search_ics_logs_by_date(args.uid, args.start_date, args.end_date)
        print(f"\n📊 Events for UID: {args.uid}")
        print(f"📅 Period: {args.start_date} to {args.end_date}")
        print("=" * 80)
        for event in events:
            print(f"\n{event['timestamp']} - {event['type']}")
            print(f"  {event['description']}")
    else:
        create_timeline(args.uid, args.days)