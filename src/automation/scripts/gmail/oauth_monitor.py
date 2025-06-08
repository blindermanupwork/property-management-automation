#!/usr/bin/env python3
"""
Gmail OAuth Token Health Monitor

This script monitors the health of Gmail OAuth tokens and attempts automatic
refresh. It can be run by cron to proactively manage token expiration.

Usage:
    python3 oauth_monitor.py                    # Check and refresh if needed
    python3 oauth_monitor.py --force-refresh   # Force token refresh
    python3 oauth_monitor.py --notify          # Send notifications on issues
    python3 oauth_monitor.py --quiet           # Minimal output
"""

import os
import sys
import pickle
import logging
import argparse
import datetime
import time
from pathlib import Path
import pytz

# Add automation config to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.automation.config_wrapper import Config

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ── Configuration ─────────────────────────────────────────────────────────────
TOKEN_PATH = str(Path(__file__).parent / "token.pickle")
CREDS_PATH = str(Path(__file__).parent / "credentials.json")
MONITOR_LOG = str(Config.get_logs_dir() / "gmail_oauth_monitor.log")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Monitor Gmail OAuth token health')
parser.add_argument('--force-refresh', action='store_true',
                    help='Force token refresh even if valid')
parser.add_argument('--notify', action='store_true',
                    help='Send notifications on token issues')
parser.add_argument('--quiet', action='store_true',
                    help='Minimal output (errors only)')
parser.add_argument('--check-expiry', type=int, default=24,
                    help='Check if token expires within N hours (default: 24)')
args = parser.parse_args()

# ── Logging Setup ──────────────────────────────────────────────────────────────
mst = pytz.timezone('America/Phoenix')

class MSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, tz=mst)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if not args.quiet else logging.ERROR)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# File handler
file_handler = logging.FileHandler(MONITOR_LOG)
file_handler.setFormatter(MSTFormatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

# Console handler
if not args.quiet:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(MSTFormatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)

def send_notification(message, is_error=False):
    """Send notification about token issues"""
    if not args.notify:
        return
        
    # You can implement email/Slack/webhook notifications here
    # For now, just log the notification
    level = logging.ERROR if is_error else logging.INFO
    logger.log(level, f"NOTIFICATION: {message}")
    
    # Example: Could send email using Config.get_notification_email()
    # or send to Slack webhook, etc.

def check_token_health():
    """
    Check Gmail OAuth token health and attempt refresh if needed.
    Returns: (is_healthy, status_message, days_until_expiry)
    """
    if not os.path.exists(TOKEN_PATH):
        return False, "No token file exists", None
        
    if not os.path.exists(CREDS_PATH):
        return False, "No credentials.json file found", None
    
    try:
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
            
        # Check if credentials are valid
        if creds.valid and not args.force_refresh:
            # Check how long until expiry
            if creds.expiry:
                now = datetime.datetime.now(datetime.timezone.utc)
                time_until_expiry = creds.expiry - now
                hours_until_expiry = time_until_expiry.total_seconds() / 3600
                days_until_expiry = hours_until_expiry / 24
                
                if hours_until_expiry < args.check_expiry:
                    logger.warning(f"Token expires in {hours_until_expiry:.1f} hours")
                    return True, f"Token valid but expires soon ({days_until_expiry:.1f} days)", days_until_expiry
                else:
                    logger.info(f"Token valid for {days_until_expiry:.1f} more days")
                    return True, f"Token healthy ({days_until_expiry:.1f} days remaining)", days_until_expiry
            else:
                return True, "Token valid (no expiry info)", None
                
        # Token expired or invalid, try to refresh
        if creds.expired and creds.refresh_token:
            logger.info("Attempting to refresh expired token...")
            
            try:
                creds.refresh(Request())
                
                # Save refreshed token
                with open(TOKEN_PATH, 'wb') as f:
                    pickle.dump(creds, f)
                os.chmod(TOKEN_PATH, 0o600)
                
                # Calculate new expiry
                if creds.expiry:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    time_until_expiry = creds.expiry - now
                    days_until_expiry = time_until_expiry.total_seconds() / (3600 * 24)
                    logger.info(f"✅ Token refreshed successfully, valid for {days_until_expiry:.1f} days")
                    return True, f"Token refreshed successfully ({days_until_expiry:.1f} days)", days_until_expiry
                else:
                    logger.info("✅ Token refreshed successfully")
                    return True, "Token refreshed successfully", None
                    
            except Exception as refresh_error:
                logger.error(f"❌ Token refresh failed: {refresh_error}")
                return False, f"Token refresh failed: {refresh_error}", None
        else:
            return False, "Token invalid and cannot be refreshed", None
            
    except Exception as e:
        logger.error(f"❌ Error checking token: {e}")
        return False, f"Error checking token: {e}", None

def main():
    """Main monitoring function"""
    logger.info("🔍 Starting Gmail OAuth token health check...")
    
    is_healthy, status_message, days_until_expiry = check_token_health()
    
    if is_healthy:
        logger.info(f"✅ {status_message}")
        
        # Send notification if token expires soon
        if days_until_expiry is not None and days_until_expiry < 7:
            send_notification(
                f"Gmail OAuth token expires in {days_until_expiry:.1f} days. "
                f"Consider running manual refresh soon.",
                is_error=False
            )
        
        return True
        
    else:
        logger.error(f"❌ {status_message}")
        
        # Send error notification
        send_notification(
            f"Gmail OAuth token issue: {status_message}. Manual intervention required.",
            is_error=True
        )
        
        # Log instructions for manual fix
        logger.error("Manual intervention required:")
        logger.error("1. Run: python3 gmail_downloader.py --list-only")
        logger.error("2. This will trigger OAuth flow if needed")
        logger.error("3. Or check credentials.json for validity")
        
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        
        if not args.quiet:
            if success:
                print("✅ Gmail OAuth token is healthy")
            else:
                print("❌ Gmail OAuth token requires attention")
                
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error in OAuth monitor: {e}")
        send_notification(f"Gmail OAuth monitor crashed: {e}", is_error=True)
        if not args.quiet:
            print(f"❌ Monitor failed: {e}")
        sys.exit(1)