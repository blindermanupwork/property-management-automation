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
        ], cwd=str(evolve_script.parent.absolute()), env=env)
        
        # Check for the status file to get detailed results
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
                
                if status.get("overall_success", False):
                    message = f"Evolve scraping completed - Tab1: {tab1_status}, Tab2: {tab2_status}"
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
        csv_script = config.get_script_path("CSVtoAirtable", "csvProcess.py")
        if not csv_script.exists():
            return {"success": False, "message": "CSV processor script not found"}
        
        print("📊 Processing iTrip and Evolve CSV files to Airtable...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        result = subprocess.run([
            sys.executable, str(csv_script.absolute())
        ], cwd=str(csv_script.parent.absolute()), env=env)
        
        if result.returncode == 0:
            return {"success": True, "message": "CSV processing to Airtable completed successfully"}
        else:
            return {"success": False, "message": "CSV processing failed"}
            
    except Exception as e:
        return {"success": False, "message": f"CSV processing error: {str(e)}"}
    
def extract_ics_error_details(output):
    """Extract error details from ICS sync output"""
    error_patterns = [
        "Unknown field name",
        "422 Client Error", 
        "Error fetching/grouping records",
        "Unhandled exception",
        "requests.exceptions",
        "Failed to fetch",
        "API rate limit",
        "HTTPError",
        "UNKNOWN_FIELD_NAME"
    ]
    
    for line in output.split('\n'):
        for pattern in error_patterns:
            if pattern in line:
                # Extract the line and next few lines for context
                return line.strip()
    
    return "Unknown error - check logs for details"

def extract_ics_stats(output):
    """Extract statistics from ICS sync output"""
    stats = {
        'feeds': 0,
        'new': 0,
        'modified': 0,
        'removed': 0,
        'unchanged': 0,
        'errors': 0
    }
    
    # Look for summary line
    for line in output.split('\n'):
        if "ICS_SUMMARY:" in line:
            # Parse structured summary
            parts = line.split("ICS_SUMMARY:")[1].strip()
            for part in parts.split(","):
                if "=" in part:
                    key, value = part.split("=")
                    key = key.strip().lower()
                    if key == 'feeds':
                        stats['feeds'] = int(value.strip())
                    elif key == 'new':
                        stats['new'] = int(value.strip())
                    elif key == 'modified':
                        stats['modified'] = int(value.strip())
                    elif key == 'removed':
                        stats['removed'] = int(value.strip())
                    elif key == 'errors':
                        stats['errors'] = int(value.strip())
        
        # Also look for legacy format and optimized format
        elif "ICS Sync complete" in line:
            import re
            # Look for pattern: created X * modified Y * unchanged Z * removed W
            created_match = re.search(r'created (\d+)', line)
            modified_match = re.search(r'modified (\d+)', line)
            unchanged_match = re.search(r'unchanged (\d+)', line)
            removed_match = re.search(r'removed (\d+)', line)
            
            if created_match:
                stats['new'] = int(created_match.group(1))
            if modified_match:
                stats['modified'] = int(modified_match.group(1))
            if unchanged_match:
                stats['unchanged'] = int(unchanged_match.group(1))
            if removed_match:
                stats['removed'] = int(removed_match.group(1))
        
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
        # Use the optimized version
        ics_script = config.get_script_path("icsAirtableSync", "icsProcess_optimized.py")
        if not ics_script.exists():
            # Fall back to original if optimized doesn't exist
            ics_script = config.get_script_path("icsAirtableSync", "icsProcess.py")
            if not ics_script.exists():
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
                    "message": f"❌ ICS sync failed: {error_msg}"
                }
        else:
            # Success
            if stats['feeds'] > 0:
                return {
                    "success": True,
                    "message": f"✅ ICS sync: {stats['feeds']} feeds processed, "
                              f"{stats['new']} new, {stats['modified']} modified, "
                              f"{stats['removed']} removed"
                }
            else:
                # No feeds processed (might be intentional)
                return {
                    "success": True,
                    "message": "✅ ICS sync completed (no feeds to process)"
                }
            
    except Exception as e:
        return {"success": False, "message": f"❌ ICS sync error: {str(e)}"}
    
def run_hcp_automation(config):
    """Run HCP service job creation/sync
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        print("🔧 Running HCP service job sync...")
        
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
            if "All service lines are up to date!" in output:
                return {"success": True, "message": "✅ All service lines are up to date"}
            elif "Service line update complete!" in output:
                # Extract number of updates
                import re
                match = re.search(r'Updated (\d+) jobs', output)
                if match:
                    count = match.group(1)
                    return {"success": True, "message": f"✅ Updated {count} service line descriptions"}
                else:
                    return {"success": True, "message": "✅ Service line updates completed"}
            else:
                return {"success": True, "message": "✅ Service line update completed"}
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