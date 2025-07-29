#!/usr/bin/env python3
"""
Analyze automation patterns to find what's triggering them at X:06-X:07
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.automation.config_wrapper import Config
from pyairtable import Table

def analyze_automation_patterns():
    """Analyze when automations run and look for patterns"""
    
    config = Config()
    table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "Automation")
    
    # Get all automation records
    records = table.all()
    
    print("=== AUTOMATION TIMING ANALYSIS ===")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Group by minute of hour
    minute_patterns = defaultdict(list)
    
    for record in records:
        fields = record['fields']
        name = fields.get('Name', 'Unknown')
        last_ran = fields.get('Last Ran Time')
        sync_details = fields.get('Sync Details', '')
        
        if last_ran:
            # Parse timestamp
            dt = datetime.fromisoformat(last_ran.replace('Z', '+00:00'))
            local_dt = dt.astimezone()
            minute = local_dt.minute
            
            # Track success/failure
            is_success = '✅' in sync_details[:10]
            is_failure = '❌' in sync_details[:10]
            
            minute_patterns[minute].append({
                'name': name,
                'time': local_dt,
                'success': is_success,
                'failure': is_failure,
                'details': sync_details[:100]
            })
    
    # Analyze patterns
    print("=== MINUTE DISTRIBUTION ===")
    for minute in sorted(minute_patterns.keys()):
        items = minute_patterns[minute]
        success_count = sum(1 for i in items if i['success'])
        failure_count = sum(1 for i in items if i['failure'])
        
        print(f"\nMinute :{minute:02d} - {len(items)} runs (✅ {success_count}, ❌ {failure_count})")
        
        # Show most recent for this minute
        latest = max(items, key=lambda x: x['time'])
        print(f"  Latest: {latest['name']} at {latest['time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # If this is in the suspicious window, show all
        if 6 <= minute <= 10:
            print("  ⚠️  SUSPICIOUS TIMING - All runs at this minute:")
            for item in sorted(items, key=lambda x: x['time'], reverse=True)[:5]:
                status = "✅" if item['success'] else "❌"
                print(f"    {status} {item['name']} - {item['time'].strftime('%Y-%m-%d %H:%M')}")
    
    # Look for sequences
    print("\n=== SEQUENTIAL PATTERNS ===")
    all_runs = []
    for minute_runs in minute_patterns.values():
        all_runs.extend(minute_runs)
    
    all_runs.sort(key=lambda x: x['time'], reverse=True)
    
    # Find runs within 5 minutes of each other
    print("\nRecent run sequences (within 5 minutes):")
    for i, run in enumerate(all_runs[:20]):
        print(f"\n{run['time'].strftime('%Y-%m-%d %H:%M:%S')} - {run['name']}")
        
        # Look for other runs within 5 minutes
        run_time = run['time']
        nearby = []
        for other in all_runs:
            if other == run:
                continue
            time_diff = abs((other['time'] - run_time).total_seconds())
            if time_diff < 300:  # 5 minutes
                nearby.append((time_diff, other))
        
        if nearby:
            nearby.sort(key=lambda x: x[0])
            for diff, other in nearby[:3]:
                print(f"  +{int(diff)}s: {other['name']}")
    
    # Check for external triggers
    print("\n=== CHECKING FOR EXTERNAL TRIGGERS ===")
    
    # Look for any button configurations
    for record in records:
        fields = record['fields']
        if 'Run Now' in fields:
            run_now = fields['Run Now']
            print(f"\n{fields['Name']} button config: {run_now}")
    
    # Check logs
    print("\n=== RECENT LOG ENTRIES ===")
    log_files = [
        ('automation_prod.log', 'Production automation'),
        ('automation_prod_cron.log', 'Production cron'),
        ('webhook.log', 'Webhook activity'),
        ('automation_trigger_monitor.log', 'Trigger monitor')
    ]
    
    for log_file, description in log_files:
        log_path = Config.get_logs_dir() / log_file
        if log_path.exists():
            print(f"\n{description} ({log_file}):")
            # Get last few lines
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        if any(keyword in line for keyword in [':06:', ':07:', ':08:', 'trigger', 'run']):
                            print(f"  {line.strip()}")
            except:
                print("  (Unable to read)")

if __name__ == "__main__":
    analyze_automation_patterns()