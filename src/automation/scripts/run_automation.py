#!/usr/bin/env python3
"""
Automation Functions
Individual automation functions that can be called with specific configs
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time
import pytz

def run_gmail_automation(config):
    """Run Gmail downloader automation with IMAP (no OAuth required)
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        # Use IMAP downloader instead of OAuth version
        gmail_script = config.get_script_path("gmail", "gmail_imap_downloader.py")
        
        if not gmail_script.exists():
            return {"success": False, "message": "Gmail IMAP downloader script not found"}
        
        # Get email credentials from environment
        gmail_email = os.environ.get('GMAIL_EMAIL')
        gmail_password = os.environ.get('GMAIL_PASSWORD')  # App password
        
        if not gmail_email or not gmail_password:
            return {
                "success": False, 
                "message": "Gmail credentials not found. Set GMAIL_EMAIL and GMAIL_PASSWORD environment variables."
            }
        
        print("📧 Running Gmail IMAP downloader...")
        result = subprocess.run([
            sys.executable, str(gmail_script.absolute()), 
            "--email", gmail_email,
            "--password", gmail_password,
            "--days", "1"  # Look back 1 day to catch any missed emails
        ], cwd=str(gmail_script.parent.absolute()))
        
        if result.returncode == 0:
            return {"success": True, "message": "Gmail IMAP download completed successfully"}
        else:
            return {"success": False, "message": "Gmail IMAP download failed"}
            
    except Exception as e:
        return {"success": False, "message": f"Gmail IMAP error: {str(e)}"}
    
def run_evolve_automation(config):
    """Run Evolve scraper automation
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        evolve_script = config.get_script_path("evolve", "evolveScrape.py")
        if not evolve_script.exists():
            return {"success": False, "message": "Evolve scraper script not found"}
        
        print("🏠 Running Evolve scraper...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        result = subprocess.run([
            sys.executable, str(evolve_script.absolute()), "--headless"
        ], cwd=str(evolve_script.parent.absolute()), env=env,
           capture_output=True, text=True, encoding='utf-8')
        
        # Look for EVOLVE_SUMMARY in output first
        output = result.stdout + "\n" + result.stderr
        evolve_summary = None
        
        for line in output.split('\n'):
            if "EVOLVE_SUMMARY:" in line:
                # Extract the summary after the marker
                evolve_summary = line.split("EVOLVE_SUMMARY:")[1].strip()
                # Parse the key=value pairs
                parts = evolve_summary.split(', ')
                tab1_success = tab2_success = False
                tab1_rows = tab2_rows = 0
                
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=')
                        if key == 'Tab1Success':
                            tab1_success = value == 'True'
                        elif key == 'Tab2Success':
                            tab2_success = value == 'True'
                        elif key == 'Tab1Rows':
                            tab1_rows = int(value)
                        elif key == 'Tab2Rows':
                            tab2_rows = int(value)
                
                if tab1_success or tab2_success:
                    message = f"2 files — {tab1_rows} reservations, {tab2_rows} blocks"
                    return {"success": True, "message": message}
                else:
                    return {"success": False, "message": "Both tab exports failed"}
        
        # Fallback to status file if no EVOLVE_SUMMARY found
        from src.automation.config_wrapper import Config
        status_file = Config.get_csv_process_dir() / "evolve_status.json"
        
        if status_file.exists():
            try:
                import json
                with open(status_file, 'r') as f:
                    status = json.load(f)
                
                # Build detailed message based on actual results
                tab1_status = "✅" if status.get("tab1_success", False) else "❌"
                tab2_status = "✅" if status.get("tab2_success", False) else "❌"
                tab1_rows = status.get("tab1_rows", 0)
                tab2_rows = status.get("tab2_rows", 0)
                
                if status.get("overall_success", False):
                    message = f"2 files — {tab1_rows} reservations, {tab2_rows} blocks"
                    return {"success": True, "message": message}
                else:
                    message = status.get("message", "Evolve scraping failed")
                    return {"success": False, "message": f"{message} - Tab1: {tab1_status}, Tab2: {tab2_status}"}
                    
            except Exception as e:
                # Fall back to return code
                if result.returncode == 0:
                    return {"success": True, "message": "Evolve scraping completed successfully"}
                else:
                    return {"success": False, "message": "Evolve scraping failed"}
        else:
            # No status file, use return code
            if result.returncode == 0:
                return {"success": True, "message": "Evolve scraping completed successfully"}
            else:
                return {"success": False, "message": "Evolve scraping failed"}
            
    except Exception as e:
        return {"success": False, "message": f"Evolve error: {str(e)}"}
    
def run_csv_automation(config):
    """Process iTrip and Evolve CSV files to Airtable
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        # Try processors in order of preference
        processors = [
            "csvProcess_enhanced.py",  # Enhanced version with property grouping
            "csvProcess_memory.py",    # Memory version with UID detection
            "csvProcess_best.py",      # Best version wrapper
            "csvProcess.py"            # Original version
        ]
        
        csv_script = None
        for processor in processors:
            script_path = config.get_script_path("CSVtoAirtable", processor)
            if script_path.exists():
                csv_script = script_path
                print(f"📊 Using CSV processor: {processor}")
                break
        
        if not csv_script:
            return {"success": False, "message": "CSV processor script not found"}
        
        print("📊 Processing iTrip and Evolve CSV files to Airtable...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Capture output to extract sync details
        result = subprocess.run([
            sys.executable, str(csv_script.absolute())
        ], cwd=str(csv_script.parent.absolute()), env=env,
           capture_output=True, text=True, encoding='utf-8')
        
        # Try to get sync summary from the CSV sync log
        sync_summary = None
        log_file = config.get_log_path(f'csv_sync_{config.environment_name}.log')
        
        if log_file.exists():
            try:
                # Read the last 100 lines of the log
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]
                
                # Look for the sync complete message
                for line in reversed(lines):
                    if "CSV_SYNC_SUMMARY:" in line:
                        # Parse the new structured summary format
                        summary_text = line.split("CSV_SYNC_SUMMARY:")[1].strip()
                        # Parse key=value pairs
                        parts = summary_text.split(", ")
                        files = new_count = mod_count = rem_count = 0
                        new_detail = mod_detail = rem_detail = ""
                        
                        for part in parts:
                            if "=" in part:
                                key, value = part.split("=", 1)
                                if key == "Files":
                                    files = int(value)
                                elif key == "New":
                                    # Extract count and detail
                                    if "(" in value:
                                        new_count = int(value.split(" ")[0])
                                        new_detail = value
                                    else:
                                        new_count = int(value)
                                elif key == "Modified":
                                    if "(" in value:
                                        mod_count = int(value.split(" ")[0])
                                        mod_detail = value
                                    else:
                                        mod_count = int(value)
                                elif key == "Removed":
                                    if "(" in value:
                                        rem_count = int(value.split(" ")[0])
                                        rem_detail = value
                                    else:
                                        rem_count = int(value)
                        
                        # Build formatted message
                        sync_summary = f"{files} files — new {new_detail} — modified {mod_detail} — removed {rem_detail}"
                        break
                    elif "Sync complete * created" in line:
                        # Legacy format fallback
                        match = line.strip().split(" INFO: ")[-1]
                        sync_summary = match
                        break
                    elif "No CSV files to process" in line:
                        sync_summary = "No CSV files to process"
                        break
                    elif "No valid reservations found" in line:
                        sync_summary = "No valid reservations found in CSV files"
                        break
            except Exception as e:
                print(f"⚠️ Could not read CSV sync log: {e}")
        
        if result.returncode == 0:
            if sync_summary:
                return {"success": True, "message": sync_summary}
            else:
                return {"success": True, "message": "CSV processing to Airtable completed successfully"}
        else:
            # Extract error details from output
            output = result.stdout + "\n" + result.stderr
            error_msg = extract_csv_error_details(output)
            return {"success": False, "message": f"CSV processing failed: {error_msg}"}
            
    except Exception as e:
        return {"success": False, "message": f"CSV processing error: {str(e)}"}
    
def extract_csv_error_details(output):
    """Extract error details from CSV processing output"""
    error_patterns = [
        ("Unknown field name", "Airtable field configuration error"),
        ("422 Client Error", "Airtable API error"),
        ("Missing property links", "Properties not found in Airtable"),
        ("No CSV files to process", "No CSV files found in process directory"),
        ("Error processing", "Failed to process CSV file"),
        ("Missing required columns", "CSV file missing required columns"),
        ("HTTPError", "HTTP request failed"),
        ("UNKNOWN_FIELD_NAME", "Airtable field does not exist"),
        ("ConnectionError", "Network connection failed"),
        ("PermissionError", "Permission denied"),
        ("FileNotFoundError", "Required file not found"),
        ("KeyError", "Missing required data field"),
        ("ValueError", "Invalid data format"),
        ("Property Guest Overrides", "Guest overrides table access error (non-critical)"),
        ("UnicodeDecodeError", "CSV file encoding error")
    ]
    
    # First check for Python traceback
    if "Traceback (most recent call last):" in output:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "Traceback" in line:
                # Get the actual error line (usually the last line of traceback)
                for j in range(i, min(i+20, len(lines))):
                    if lines[j].strip() and not lines[j].startswith(' '):
                        error_line = lines[j].strip()
                        # Extract just the error type and message
                        if ':' in error_line:
                            return error_line
    
    # Check for specific error patterns
    for line in output.split('\n'):
        for pattern, description in error_patterns:
            if pattern in line:
                # Include more context from the line
                if "422 Client Error" in line and "Unknown field name" in line:
                    import re
                    field_match = re.search(r'Unknown field name: "([^"]+)"', line)
                    if field_match:
                        return f"Airtable field '{field_match.group(1)}' does not exist"
                elif "Missing property links" in line:
                    import re
                    count_match = re.search(r'(\d+) reservation\(s\) missing Property mapping', line)
                    if count_match:
                        return f"{count_match.group(1)} reservations have properties not found in Airtable"
                elif "Missing required columns" in line:
                    # Extract filename if present
                    import re
                    file_match = re.search(r'([^/]+\.csv)', line)
                    if file_match:
                        return f"CSV file '{file_match.group(1)}' is missing required columns"
                elif "Property Guest Overrides" in line and "403" in line:
                    return "Guest overrides table not accessible (non-critical, processing continues)"
                return f"{description}: {line.strip()[:100]}"
    
    # Check if no output was produced
    if not output.strip():
        return "Script produced no output - may have crashed silently"
    
    # Check for common script execution issues
    if "No such file or directory" in output:
        return "Script file not found or missing dependencies"
    
    if "Permission denied" in output:
        return "Permission denied - check file permissions"
    
    if "ModuleNotFoundError" in output:
        import re
        module_match = re.search(r"No module named '([^']+)'", output)
        if module_match:
            return f"Missing Python module: {module_match.group(1)}"
    
    return "No specific error found - script may have exited unexpectedly"

def extract_ics_error_details(output):
    """Extract error details from ICS sync output"""
    error_patterns = [
        ("Unknown field name", "Airtable field configuration error"),
        ("422 Client Error", "Airtable API error"), 
        ("Error fetching/grouping records", "Failed to fetch records from Airtable"),
        ("Unhandled exception", "Script crashed unexpectedly"),
        ("requests.exceptions", "Network or API connection error"),
        ("Failed to fetch", "Unable to download ICS feed"),
        ("API rate limit", "Airtable API rate limit exceeded"),
        ("HTTPError", "HTTP request failed"),
        ("UNKNOWN_FIELD_NAME", "Airtable field does not exist"),
        ("ConnectionError", "Network connection failed"),
        ("Timeout", "Request timed out"),
        ("PermissionError", "Permission denied"),
        ("FileNotFoundError", "Required file not found"),
        ("KeyError", "Missing required data field"),
        ("ValueError", "Invalid data format"),
        ("TypeError", "Data type mismatch")
    ]
    
    # First check for Python traceback
    if "Traceback (most recent call last):" in output:
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "Traceback" in line:
                # Get the actual error line (usually the last line of traceback)
                for j in range(i, min(i+20, len(lines))):
                    if lines[j].strip() and not lines[j].startswith(' '):
                        error_line = lines[j].strip()
                        # Extract just the error type and message
                        if ':' in error_line:
                            return error_line
    
    # Check for specific error patterns
    for line in output.split('\n'):
        for pattern, description in error_patterns:
            if pattern in line:
                # Include more context from the line
                if "422 Client Error" in line and "Unknown field name" in line:
                    import re
                    field_match = re.search(r'Unknown field name: "([^"]+)"', line)
                    if field_match:
                        return f"Airtable field '{field_match.group(1)}' does not exist"
                elif "Failed to fetch" in line:
                    # Extract URL if present
                    import re
                    url_match = re.search(r'Failed to fetch ([^\s]+)', line)
                    if url_match:
                        return f"Failed to download ICS feed: {url_match.group(1)}"
                return f"{description}: {line.strip()[:100]}"
    
    # Check if no output was produced
    if not output.strip():
        return "Script produced no output - may have crashed silently"
    
    # Check for common script execution issues
    if "No such file or directory" in output:
        return "Script file not found or missing dependencies"
    
    if "Permission denied" in output:
        return "Permission denied - check file permissions"
    
    if "ModuleNotFoundError" in output:
        import re
        module_match = re.search(r"No module named '([^']+)'", output)
        if module_match:
            return f"Missing Python module: {module_match.group(1)}"
    
    return "No specific error found - script may have exited unexpectedly"

def extract_ics_stats(output):
    """Extract statistics from ICS sync output"""
    stats = {
        'feeds': 0,
        'new': 0,
        'modified': 0,
        'removed': 0,
        'unchanged': 0,
        'errors': 0,
        'new_detail': '',
        'modified_detail': '',
        'removed_detail': ''
    }
    
    # Look for summary line
    for line in output.split('\n'):
        if "ICS_SUMMARY:" in line:
            # Parse structured summary - handle commas inside parentheses
            import re
            summary_text = line.split("ICS_SUMMARY:")[1].strip()
            
            # First extract all key=value pairs, being careful with parentheses
            # Split by comma, but not commas inside parentheses
            # Use a simpler approach - split on commas followed by a space and a letter
            parts = re.split(r',\s*(?=[A-Z])', summary_text)
            
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'feeds':
                        stats['feeds'] = int(value)
                    elif key == 'new':
                        stats['new'] = int(value)
                    elif key == 'modified':
                        stats['modified'] = int(value)
                    elif key == 'removed':
                        stats['removed'] = int(value)
                    elif key == 'unchanged':
                        stats['unchanged'] = int(value)
                    elif key == 'errors':
                        stats['errors'] = int(value)
                    elif key == 'newdetail':
                        stats['new_detail'] = value
                    elif key == 'modifieddetail':
                        stats['modified_detail'] = value
                    elif key == 'removeddetail':
                        stats['removed_detail'] = value
        
        # Also look for legacy format and optimized format
        elif "ICS Sync complete" in line:
            import re
            # Look for new enhanced format with breakdown: created 15 (13 res, 2 block)
            created_match = re.search(r'created (\d+)\s*(?:\(([^)]+)\))?', line)
            modified_match = re.search(r'modified (\d+)\s*(?:\(([^)]+)\))?', line)
            unchanged_match = re.search(r'unchanged (\d+)', line)
            removed_match = re.search(r'removed (\d+)\s*(?:\(([^)]+)\))?', line)
            
            if created_match:
                stats['new'] = int(created_match.group(1))
                if created_match.group(2):
                    # Store the full format with number and parentheses
                    stats['new_detail'] = f"{created_match.group(1)} ({created_match.group(2)})"
            if modified_match:
                stats['modified'] = int(modified_match.group(1))
                if modified_match.group(2):
                    # Store the full format with number and parentheses
                    stats['modified_detail'] = f"{modified_match.group(1)} ({modified_match.group(2)})"
            if unchanged_match:
                stats['unchanged'] = int(unchanged_match.group(1))
            if removed_match:
                stats['removed'] = int(removed_match.group(1))
                if removed_match.group(2):
                    # Store the full format with number and parentheses
                    stats['removed_detail'] = f"{removed_match.group(1)} ({removed_match.group(2)})"
        
        # Count parsed feeds (original version)
        elif "Parsed feed=" in line:
            stats['feeds'] += 1
            
        # Extract feed count from optimized version
        elif "Fetching" in line and "ICS feeds concurrently" in line:
            import re
            match = re.search(r'Fetching (\d+) ICS feeds', line)
            if match:
                stats['feeds'] = int(match.group(1))
    
    return stats

def run_ics_automation(config):
    """Run ICS calendar sync with detailed error capture
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        # Try processors in order of preference
        processors = [
            "icsProcess_enhanced.py",   # Enhanced version with property grouping
            "icsProcess_memory.py",     # Memory version with UID detection
            "icsProcess_best.py",       # Best version wrapper
            "icsProcess_optimized.py",  # Optimized version
            "icsProcess.py"             # Original version
        ]
        
        ics_script = None
        for processor in processors:
            script_path = config.get_script_path("icsAirtableSync", processor)
            if script_path.exists():
                ics_script = script_path
                print(f"📅 Using ICS processor: {processor}")
                break
        
        if not ics_script:
            return {"success": False, "message": "ICS processor script not found"}
        
        print("📅 Running ICS calendar sync...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Capture both stdout and stderr
        result = subprocess.run([
            sys.executable, str(ics_script.absolute())
        ], cwd=str(ics_script.parent.absolute()), env=env, 
           capture_output=True, text=True, encoding='utf-8')
        
        # Combine output
        output = result.stdout + "\n" + result.stderr
        
        # Check for critical errors in output
        error_indicators = [
            "Unhandled exception",
            "Error fetching",
            "Unknown field name",
            "422 Client Error",
            "HTTPError",
            "UNKNOWN_FIELD_NAME",
            "Failed to update Airtable"
        ]
        
        has_error = any(indicator in output for indicator in error_indicators)
        
        # Extract statistics
        stats = extract_ics_stats(output)
        
        # Build status message
        if has_error or result.returncode != 0:
            # Extract specific error
            error_msg = extract_ics_error_details(output)
            
            # Add exit code information if non-zero
            if result.returncode != 0 and result.returncode is not None:
                error_msg = f"{error_msg} (exit code: {result.returncode})"
            
            if stats['feeds'] > 0:
                # Partial success
                return {
                    "success": False,
                    "message": f"⚠️ ICS sync partial: {stats['feeds']} feeds attempted, "
                              f"{stats['new']} new, {stats['modified']} modified - "
                              f"Error: {error_msg}"
                }
            else:
                # Complete failure
                return {
                    "success": False,
                    "message": f"ICS sync failed: {error_msg}"
                }
        else:
            # Success
            if stats['feeds'] > 0:
                # Build message with optional detail breakdown
                # The detail fields from ICS_SUMMARY already include the total and breakdown
                # Always use detail fields if available, even if some are "0 (0 res, 0 block)"
                if 'new_detail' in stats:
                    new_text = stats['new_detail']
                else:
                    new_text = str(stats['new'])
                    
                if 'modified_detail' in stats:
                    modified_text = stats['modified_detail']
                else:
                    modified_text = str(stats['modified'])
                    
                if 'removed_detail' in stats:
                    removed_text = stats['removed_detail']
                else:
                    removed_text = str(stats['removed'])
                
                return {
                    "success": True,
                    "message": f"{stats['feeds']} feeds — new {new_text} — "
                              f"modified {modified_text} — removed {removed_text}"
                }
            else:
                # No feeds processed (might be intentional)
                return {
                    "success": True,
                    "message": "ICS sync completed (no feeds to process)"
                }
            
    except Exception as e:
        return {"success": False, "message": f"ICS sync error: {str(e)}"}
    
def run_add_jobs_automation(config):
    """Run HCP service job creation only
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        print("🔧 Running HCP service job creation...")
        
        # Run the environment-specific HCP sync script in add-only mode
        script_name = "dev-hcp-sync.cjs" if not config.is_production else "prod-hcp-sync.cjs"
        hcp_script = config.get_script_path("hcp", script_name)
        if not hcp_script.exists():
            return {"success": False, "message": f"HCP sync script not found: {script_name}"}
        
        # Set environment variables for the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Pass Airtable credentials
        if config.is_production:
            env['PROD_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['PROD_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
        else:
            env['DEV_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['DEV_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
        
        # Pass HCP token - use environment-specific token
        if config.is_production:
            hcp_token = config.get('PROD_HCP_TOKEN')
        else:
            hcp_token = config.get('DEV_HCP_TOKEN')
        
        if hcp_token:
            env['HCP_TOKEN'] = hcp_token
        
        result = subprocess.run([
            "node", str(hcp_script.absolute()), "--add-only"
        ], cwd=str(hcp_script.parent.absolute()), env=env)
        
        if result.returncode == 0:
            return {"success": True, "message": "HCP service job creation completed successfully"}
        else:
            return {"success": False, "message": "HCP service job creation failed"}
        
    except Exception as e:
        return {"success": False, "message": f"HCP service job creation error: {str(e)}"}

def run_sync_jobs_automation(config):
    """Run HCP service job sync verification only
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        print("🔍 Running HCP service job sync verification...")
        
        # Run the environment-specific HCP sync script in sync-only mode
        script_name = "dev-hcp-sync.cjs" if not config.is_production else "prod-hcp-sync.cjs"
        hcp_script = config.get_script_path("hcp", script_name)
        if not hcp_script.exists():
            return {"success": False, "message": f"HCP sync script not found: {script_name}"}
        
        # Set environment variables for the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Pass Airtable credentials
        if config.is_production:
            env['PROD_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['PROD_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
        else:
            env['DEV_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['DEV_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
        
        # Pass HCP token - use environment-specific token
        if config.is_production:
            hcp_token = config.get('PROD_HCP_TOKEN')
        else:
            hcp_token = config.get('DEV_HCP_TOKEN')
        
        if hcp_token:
            env['HCP_TOKEN'] = hcp_token
        
        result = subprocess.run([
            "node", str(hcp_script.absolute()), "--sync-only"
        ], cwd=str(hcp_script.parent.absolute()), env=env, 
        capture_output=True, text=True, encoding='utf-8')
        
        # Look for HCP_SYNC_SUMMARY in output
        output = result.stdout + "\n" + result.stderr
        sync_summary = None
        
        for line in output.split('\n'):
            if "HCP_SYNC_SUMMARY:" in line:
                # Extract the summary after the marker
                sync_summary = line.split("HCP_SYNC_SUMMARY:")[1].strip()
                # Parse the key=value pairs
                parts = sync_summary.split(', ')
                created = verified = total = errors = 0
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=')
                        if key == 'Created':
                            created = int(value)
                        elif key == 'Verified':
                            verified = int(value)
                        elif key == 'Total':
                            total = int(value)
                        elif key == 'Errors':
                            errors = int(value)
                
                message = f"verified {verified}/{total} jobs — created {created} new"
                if errors > 0:
                    message += f" — {errors} errors"
                break
        
        if result.returncode == 0:
            if sync_summary:
                return {"success": True, "message": message}
            else:
                return {"success": True, "message": "HCP service job sync verification completed successfully"}
        else:
            return {"success": False, "message": "HCP service job sync verification failed"}
        
    except Exception as e:
        return {"success": False, "message": f"HCP service job sync verification error: {str(e)}"}

def run_hcp_automation(config):
    """Legacy function - Run HCP service job creation/sync (deprecated, use separated functions)
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        print("🔧 Running HCP service job sync (legacy mode)...")
        
        # Run the environment-specific HCP sync script
        script_name = "dev-hcp-sync.cjs" if not config.is_production else "prod-hcp-sync.cjs"
        hcp_script = config.get_script_path("hcp", script_name)
        if not hcp_script.exists():
            return {"success": False, "message": f"HCP sync script not found: {script_name}"}
        
        # Set environment variables for the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Pass Airtable credentials
        if config.is_production:
            env['PROD_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['PROD_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
        else:
            env['DEV_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['DEV_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
        
        # Pass HCP token - use environment-specific token
        if config.is_production:
            hcp_token = config.get('PROD_HCP_TOKEN')
        else:
            hcp_token = config.get('DEV_HCP_TOKEN')
        
        if hcp_token:
            env['HCP_TOKEN'] = hcp_token
        
        result = subprocess.run([
            "node", str(hcp_script.absolute())
        ], cwd=str(hcp_script.parent.absolute()), env=env)
        
        if result.returncode == 0:
            return {"success": True, "message": "HCP service job sync completed successfully"}
        else:
            return {"success": False, "message": "HCP service job sync failed"}
        
    except Exception as e:
        return {"success": False, "message": f"HCP service job error: {str(e)}"}

def run_service_line_updates(config):
    """Run HCP service line updates
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        print("📝 Running HCP service line updates...")
        
        # Run the enhanced service line update script with owner detection
        update_script = config.get_script_path("hcp", "update-service-lines-enhanced.py")
        if not update_script.exists():
            # Fall back to original script if enhanced doesn't exist
            update_script = config.get_script_path("hcp", "update-service-lines.py")
            if not update_script.exists():
                return {"success": False, "message": "Service line update script not found"}
        
        # Set environment
        env_arg = 'production' if config.is_production else 'development'
        
        # Pass environment variables
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Pass Airtable credentials
        if config.is_production:
            env['PROD_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['PROD_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
            env['PROD_HCP_TOKEN'] = config.get('PROD_HCP_TOKEN', '')
        else:
            env['DEV_AIRTABLE_API_KEY'] = config.get_airtable_api_key()
            env['DEV_AIRTABLE_BASE_ID'] = config.get_airtable_base_id()
            env['DEV_HCP_TOKEN'] = config.get('DEV_HCP_TOKEN', '')
        
        result = subprocess.run([
            sys.executable, str(update_script.absolute()),
            '--env', env_arg
        ], 
        cwd=str(update_script.parent.absolute()),
        capture_output=True,
        text=True,
        env=env
        )
        
        if result.returncode == 0:
            # Parse output for statistics
            output = result.stdout
            
            # Look for SERVICE_LINE_SUMMARY first
            sync_summary = None
            for line in output.split('\n'):
                if "SERVICE_LINE_SUMMARY:" in line:
                    # Extract the summary after the marker
                    sync_summary = line.split("SERVICE_LINE_SUMMARY:")[1].strip()
                    # Parse the key=value pairs
                    parts = sync_summary.split(', ')
                    owner_arriving = service_lines = total = 0
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=')
                            if key == 'OwnerArriving':
                                owner_arriving = int(value)
                            elif key == 'ServiceLines':
                                service_lines = int(value)
                            elif key == 'Total':
                                total = int(value)
                    
                    message = f"updated {service_lines}/{total} service lines"
                    if owner_arriving > 0:
                        message += f" — {owner_arriving} owner arrivals"
                    return {"success": True, "message": message}
            
            # Fallback to legacy parsing
            if "All service lines are up to date!" in output:
                return {"success": True, "message": "All service lines are up to date"}
            elif "Service line update complete!" in output:
                # Extract number of updates
                import re
                match = re.search(r'Updated (\d+) jobs', output)
                if match:
                    count = match.group(1)
                    return {"success": True, "message": f"Updated {count} service line descriptions"}
                else:
                    return {"success": True, "message": "Service line updates completed"}
            else:
                return {"success": True, "message": "Service line update completed"}
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return {"success": False, "message": f"Service line update failed: {error_msg}"}
            
    except Exception as e:
        return {"success": False, "message": f"Service line update error: {str(e)}"}

def run_job_reconciliation(config, execute=False):
    """Run HCP job reconciliation to match unlinked jobs to reservations
    
    Args:
        config: DevConfig or ProdConfig instance
        execute: If True, perform the reconciliation. If False, run in dry-run mode
    
    Returns:
        dict: Result with success status and message
    """
    try:
        print("🔄 Running HCP job reconciliation...")
        
        reconcile_script = config.get_script_path("hcp", "reconcile-jobs-optimized.py")
        if not reconcile_script.exists():
            return {"success": False, "message": "Job reconciliation script not found"}
        
        # Determine environment name
        environment = 'prod' if config.is_production else 'dev'
        
        # Build command
        cmd = [
            sys.executable, str(reconcile_script.absolute()),
            "--env", environment,
            "--json"  # Get JSON output
        ]
        
        if execute:
            cmd.append("--execute")
            print("  Mode: Execute (will update Airtable)")
        else:
            print("  Mode: Dry-run (analysis only)")
        
        # Set environment variables
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        # Run the reconciliation
        result = subprocess.run(
            cmd, 
            cwd=str(reconcile_script.parent.absolute()),
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse JSON output
            import json
            try:
                output = json.loads(result.stdout)
                if output.get('success'):
                    results = output.get('results', {})
                    matched = results.get('matched', 0)
                    total = results.get('total', 0)
                    mode = "executed" if execute else "analyzed"
                    
                    message = f"Reconciliation {mode}: {matched}/{total} jobs matched"
                    if matched > 0:
                        print(f"  ✅ {message}")
                    else:
                        print(f"  ℹ️  {message}")
                    
                    return {"success": True, "message": message, "results": results}
                else:
                    return {"success": False, "message": output.get('message', 'Reconciliation failed')}
            except json.JSONDecodeError:
                # Fallback to text output
                return {"success": True, "message": f"Reconciliation completed (output: {result.stdout.strip()})"}
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return {"success": False, "message": f"Reconciliation failed: {error_msg}"}
            
    except Exception as e:
        return {"success": False, "message": f"Job reconciliation error: {str(e)}"}