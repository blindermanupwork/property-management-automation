#!/usr/bin/env python3
"""
Track the history of a specific UID - when it was added, modified, or removed
"""
import sys
import re
from datetime import datetime
import subprocess
import argparse

def search_uid_in_logs(uid, log_files=None):
    """Search for all occurrences of a UID in ICS sync logs"""
    if log_files is None:
        log_files = [
            "/home/opc/automation/src/automation/logs/ics_sync.log",
            "/home/opc/automation/src/automation/logs/automation_prod.log",
            "/home/opc/automation/src/automation/logs/automation_prod_cron.log"
        ]
    
    events = []
    
    for log_file in log_files:
        try:
            # Use grep to efficiently search large log files
            cmd = f'grep -B5 -A5 "{uid}" {log_file} 2>/dev/null'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                
                # Parse the output to find relevant events
                for i, line in enumerate(lines):
                    # Look for timestamp at start of line
                    timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match and uid in line:
                        timestamp = timestamp_match.group(1)
                        
                        # Determine what happened
                        event_type = None
                        details = ""
                        
                        if "new" in line.lower() and uid in line:
                            event_type = "ADDED"
                            details = "New reservation created"
                        elif "modified" in line.lower() and uid in line:
                            event_type = "MODIFIED"
                            details = "Reservation modified"
                        elif "removed" in line.lower() and uid in line:
                            event_type = "REMOVED"
                            details = "Reservation removed from feed"
                        elif "mark.*as.*old" in line.lower() or "setting status to 'old'" in line.lower():
                            event_type = "MARKED_OLD"
                            details = "Status changed to Old"
                        elif "setting status to 'removed'" in line.lower():
                            event_type = "MARKED_REMOVED"
                            details = "Status changed to Removed"
                        elif "duplicate" in line.lower() and uid in line:
                            event_type = "DUPLICATE"
                            details = "Duplicate detected"
                        elif "processing event" in line.lower() and uid in line:
                            event_type = "PROCESSING"
                            details = "Processing event from ICS feed"
                        
                        if event_type:
                            # Try to get more context from surrounding lines
                            context_lines = []
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            for j in range(start, end):
                                if j != i and uid not in lines[j]:  # Don't duplicate the main line
                                    context_lines.append(lines[j].strip())
                            
                            events.append({
                                'timestamp': timestamp,
                                'event_type': event_type,
                                'details': details,
                                'log_file': log_file,
                                'line': line.strip(),
                                'context': context_lines
                            })
                        
        except Exception as e:
            print(f"Error searching {log_file}: {e}")
    
    # Sort events by timestamp
    events.sort(key=lambda x: x['timestamp'])
    
    return events

def find_removal_event(uid):
    """Specifically find when a UID was marked as removed"""
    events = search_uid_in_logs(uid)
    
    removal_events = [e for e in events if e['event_type'] in ['REMOVED', 'MARKED_REMOVED']]
    
    print(f"\n🔍 Tracking history for UID: {uid}")
    print("=" * 80)
    
    if removal_events:
        print(f"\n📅 REMOVAL EVENTS FOUND:")
        for event in removal_events:
            print(f"\n  ⏰ {event['timestamp']}")
            print(f"  📌 Event: {event['event_type']}")
            print(f"  📝 Details: {event['details']}")
            print(f"  📄 Log: {event['log_file'].split('/')[-1]}")
            print(f"  📜 Line: {event['line']}")
            if event['context']:
                print(f"  📋 Context:")
                for ctx in event['context'][:3]:  # Show up to 3 context lines
                    if ctx.strip():
                        print(f"      {ctx}")
    else:
        print(f"\n❌ No removal events found for this UID")
    
    return removal_events

def show_full_history(uid):
    """Show the complete history of a UID"""
    events = search_uid_in_logs(uid)
    
    print(f"\n🔍 Complete history for UID: {uid}")
    print("=" * 80)
    
    if events:
        # Group by date
        current_date = None
        
        for event in events:
            event_date = event['timestamp'].split(' ')[0]
            
            if event_date != current_date:
                current_date = event_date
                print(f"\n📅 {current_date}")
                print("-" * 40)
            
            time = event['timestamp'].split(' ')[1]
            print(f"\n  ⏰ {time} - {event['event_type']}")
            print(f"     {event['details']}")
            if event['line'] and len(event['line']) < 200:  # Don't show very long lines
                print(f"     Log: {event['line']}")
    else:
        print(f"\n❌ No history found for this UID")
        print("   This could mean:")
        print("   - The UID doesn't exist")
        print("   - The logs have been rotated")
        print("   - The UID is in a different log file")
    
    # Summary
    if events:
        print(f"\n📊 Summary:")
        print(f"   First seen: {events[0]['timestamp']}")
        print(f"   Last seen: {events[-1]['timestamp']}")
        print(f"   Total events: {len(events)}")
        
        # Count event types
        event_counts = {}
        for event in events:
            event_counts[event['event_type']] = event_counts.get(event['event_type'], 0) + 1
        
        print(f"   Event types:")
        for event_type, count in sorted(event_counts.items()):
            print(f"     - {event_type}: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Track UID history in ICS sync logs')
    parser.add_argument('uid', help='The UID to search for')
    parser.add_argument('--removal-only', '-r', action='store_true', 
                       help='Only show removal events')
    parser.add_argument('--log-files', '-l', nargs='+', 
                       help='Specific log files to search')
    
    args = parser.parse_args()
    
    if args.removal_only:
        find_removal_event(args.uid)
    else:
        show_full_history(args.uid)