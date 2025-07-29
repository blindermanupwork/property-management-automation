#!/usr/bin/env python3
"""
Monitor and log all automation triggers to find what's calling them at X:06-X:07
"""
import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.automation.config_wrapper import Config

def monitor_automation_activity():
    """Monitor various logs and processes to catch automation triggers"""
    
    log_file = Config.get_logs_dir() / "automation_trigger_monitor.log"
    
    def log_event(message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")
    
    log_event("=== Starting Automation Trigger Monitor ===")
    log_event(f"Monitoring for triggers around :06-:07 minutes")
    
    while True:
        current_minute = datetime.now().minute
        
        # Focus monitoring around :05-:10 window
        if 5 <= current_minute <= 10:
            log_event(f"Active monitoring window - minute {current_minute:02d}")
            
            # Check for any process accessing automation endpoints
            try:
                # Check nginx access logs
                nginx_check = subprocess.run(
                    ["sudo", "tail", "-n", "100", "/var/log/nginx/access.log"],
                    capture_output=True, text=True
                )
                if "automation" in nginx_check.stdout or "api/prod" in nginx_check.stdout:
                    for line in nginx_check.stdout.splitlines():
                        if "automation" in line or "api/prod" in line:
                            log_event(f"NGINX: {line}")
                
                # Check systemd journal for API activity
                journal_check = subprocess.run(
                    ["sudo", "journalctl", "-u", "airscripts-api-https", "--since", "1 minute ago", "--no-pager"],
                    capture_output=True, text=True
                )
                if journal_check.stdout:
                    for line in journal_check.stdout.splitlines():
                        if any(keyword in line for keyword in ["POST", "GET", "automation", "run"]):
                            log_event(f"API: {line}")
                
                # Check for any cron or scheduled task activity
                ps_check = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True, text=True
                )
                for line in ps_check.stdout.splitlines():
                    if any(keyword in line for keyword in ["automation", "run_automation", "airscripts"]):
                        if "monitor_automation_triggers" not in line:  # Skip self
                            log_event(f"PROCESS: {line}")
                
                # Check Airtable automation table for recent updates
                from pyairtable import Table
                config = Config()
                table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "Automation")
                
                # Get all automation records
                records = table.all()
                for record in records:
                    if 'Last Ran Time' in record['fields']:
                        last_ran = datetime.fromisoformat(record['fields']['Last Ran Time'].replace('Z', '+00:00'))
                        time_diff = (datetime.now(tz=last_ran.tzinfo) - last_ran).total_seconds()
                        
                        # If updated within last 2 minutes
                        if time_diff < 120:
                            log_event(f"AIRTABLE UPDATE: {record['fields']['Name']} - Last Ran: {last_ran} ({time_diff:.1f}s ago)")
                
                # Check for any webhooks
                webhook_logs = Config.get_logs_dir() / "webhook.log"
                if webhook_logs.exists():
                    webhook_check = subprocess.run(
                        ["tail", "-n", "20", str(webhook_logs)],
                        capture_output=True, text=True
                    )
                    for line in webhook_check.stdout.splitlines():
                        if datetime.now().strftime("%H:%M") in line:
                            log_event(f"WEBHOOK: {line}")
                
            except Exception as e:
                log_event(f"ERROR during monitoring: {str(e)}")
            
            # Sleep for 10 seconds during active window
            time.sleep(10)
        else:
            # Sleep for 30 seconds outside active window
            time.sleep(30)

if __name__ == "__main__":
    monitor_automation_activity()