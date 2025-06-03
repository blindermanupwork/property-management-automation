import os
import base64
import datetime
import argparse
import logging
import pickle
import time
import re
import sys
from pathlib import Path
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Import the automation config
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.automation.config_wrapper import Config

# ── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_DOWNLOAD_FOLDER = str(Config.get_itripcsv_downloads_dir())

# Default parameters
SENDER_OPTIONS = ["scottsdaleitrip@itrip.net", "scottsdaleinfo@itrip.net"]  # Multiple possible senders
SUBJECT = "iTrip Checkouts Report"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = str(Path(__file__).parent / "token.pickle")
CREDS_PATH = str(Path(__file__).parent / "credentials.json")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Download iTrip CSV reports from Gmail')
parser.add_argument('--days', type=int, default=0, 
                    help='Number of days to look back (0=today only, 1=include yesterday)')
parser.add_argument('--list-only', action='store_true', 
                    help='Only list matching emails without downloading')
parser.add_argument('--debug', action='store_true', 
                    help='Enable debug logging')
parser.add_argument('--all-emails', action='store_true',
                    help='List all emails regardless of subject')
parser.add_argument('--ignore-sender', action='store_true',
                    help='Ignore sender email (search by subject only)')
parser.add_argument('--output-dir', type=str, 
                    default=DEFAULT_DOWNLOAD_FOLDER,
                    help='Directory where CSV files will be downloaded')
parser.add_argument('--force', action='store_true',
                    help='Force download even if already processed today')
parser.add_argument('--use-label', type=str, default=None,
                    help='Search by label instead of subject (e.g., "iTrip")')
args = parser.parse_args()

# Set up download folder
DOWNLOAD_FOLDER = args.output_dir
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ── Timezone Configuration ──────────────────────────────────────────────────
# PST for logging, Arizona for data/timestamps sent to external systems
pst = pytz.timezone('US/Pacific')  # For logging
arizona_tz = pytz.timezone('America/Phoenix')  # For data timestamps
class PSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, tz=pst)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Create formatter and handler
formatter = PSTFormatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
logger.addHandler(handler)

# Create a processed emails tracking file
PROCESSED_FILE = str(Path(__file__).parent / "processed_emails.txt")

def record_processed_email(message_id):
    """Record an email as processed to avoid downloading it again"""
    today = datetime.datetime.now(arizona_tz).strftime("%Y-%m-%d")
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{today},{message_id}\n")

def is_already_processed(message_id):
    """Check if an email has already been processed today"""
    if not os.path.exists(PROCESSED_FILE) or args.force:
        return False
        
    today = datetime.datetime.now(arizona_tz).strftime("%Y-%m-%d")
    try:
        with open(PROCESSED_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2 and parts[0] == today and parts[1] == message_id:
                    return True
    except:
        pass
    return False

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
            logger.debug("Loaded credentials from %s", TOKEN_PATH)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials, running OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
            logger.debug("Saved new credentials to %s", TOKEN_PATH)

    return build('gmail', 'v1', credentials=creds)

def find_parts_with_attachments(payload):
    """
    Recursively yield all payload parts that have attachments.
    """
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('filename'):
                yield part
            # if it has nested parts
            yield from find_parts_with_attachments(part)

def download_today_csv():
    """Download CSV attachments from recent iTrip Checkouts Report emails."""
    service = get_gmail_service()
    
    # Calculate the date range for search
    today = datetime.datetime.now().date()
    if args.days > 0:
        start_date = today - datetime.timedelta(days=args.days)
        date_str = start_date.strftime('%Y/%m/%d')
        logger.info(f"Searching for emails from {args.days+1} days (since {date_str})")
    else:
        date_str = today.strftime('%Y/%m/%d')
        logger.info(f"Searching for today's emails only ({date_str})")
    
    # Build search query
    if args.use_label:
        SEARCH_QUERY = f'label:{args.use_label} after:{date_str}'
        logger.info(f"Searching for emails with label: '{args.use_label}'")
    elif args.all_emails:
        SEARCH_QUERY = f'after:{date_str}'
        logger.info(f"Listing ALL emails since {date_str}")
    else:
        SEARCH_QUERY = f'subject:"{SUBJECT}" after:{date_str}'
        logger.info(f"Looking for emails with subject: '{SUBJECT}'")
    
    # Add sender filter if not ignoring sender
    if not args.ignore_sender and not args.all_emails and not args.use_label:
        # Use parentheses to group the OR conditions
        sender_filters = []
        for sender in SENDER_OPTIONS:
            sender_filters.append(f'from:{sender}')
        if sender_filters:
            SEARCH_QUERY += f' ({" OR ".join(sender_filters)})'
    
    logger.debug(f"Search query: {SEARCH_QUERY}")
    
    # Retry the search a few times with a delay to avoid caching issues
    for attempt in range(3):
        resp = service.users().messages().list(userId='me', q=SEARCH_QUERY, maxResults=20).execute()
        messages = resp.get('messages', [])
        
        if messages:
            break
            
        # If no messages found and not first attempt, wait and retry
        if attempt < 2:
            logger.debug(f"No results on attempt {attempt+1}, retrying in 2 seconds...")
            time.sleep(2)  # Wait before retrying
    
    if not messages:
        # Try a broader search if nothing found
        if not args.all_emails and not args.use_label:
            broader_query = f'subject:iTrip after:{date_str}'
            logger.info(f"No results found. Trying broader search: {broader_query}")
            resp = service.users().messages().list(userId='me', q=broader_query, maxResults=20).execute()
            messages = resp.get('messages', [])
            
            if not messages:
                logger.warning("No matching emails found in the specified time range.")
                return False
            else:
                logger.info(f"Found {len(messages)} emails with broader search.")
        else:
            logger.warning("No matching emails found in the specified time range.")
            return False
    else:
        logger.info(f"Found {len(messages)} potential matching emails")
    
    download_count = 0
    processed_count = 0
    
    for msg_meta in messages:
        msg_id = msg_meta['id']
        
        # Skip already processed emails unless forced
        if is_already_processed(msg_id) and not args.force:
            logger.debug(f"Skipping already processed message {msg_id}")
            processed_count += 1
            continue
            
        msg = service.users().messages().get(userId='me', id=msg_id).execute()
        
        # Extract message date
        internal_dt = datetime.datetime.fromtimestamp(int(msg['internalDate'])/1000)
        msg_date = internal_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract subject and sender from headers
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        
        # Extract a clean sender email from the from_header
        sender_email = ""
        email_match = re.search(r'<([^>]+)>', from_header)
        if email_match:
            sender_email = email_match.group(1)
        else:
            sender_email = from_header
        
        # List the email details
        logger.info(f"Email [{msg_date}]: '{subject}' from {from_header}")
        logger.debug(f"Sender email extracted: {sender_email}")
        
        if args.list_only:
            # Just list the email details without downloading
            continue
            
        # Skip emails that don't match our criteria in broader search mode
        if not args.all_emails and not args.use_label and SUBJECT.lower() not in subject.lower():
            logger.debug(f"Skipping email with non-matching subject: {subject}")
            continue
        
        # Process attachments
        payload = msg.get('payload', {})
        csv_found = False
        
        for part in find_parts_with_attachments(payload):
            filename = part.get('filename', '')
            
            logger.debug(f"Found attachment: {filename}")
            
            if not filename.lower().endswith('.csv'):
                logger.debug(f"Skipping non-CSV attachment: {filename}")
                continue
                
            csv_found = True
            attach_id = part['body'].get('attachmentId')
            if not attach_id:
                logger.warning(f"No attachmentId for CSV attachment: {filename}")
                continue
            
            logger.info(f"Downloading CSV attachment: {filename}")
            
            try:
                attachment = service.users().messages().attachments().get(
                    userId='me', messageId=msg_id, id=attach_id
                ).execute()

                data = base64.urlsafe_b64decode(attachment.get('data', ''))
                
                # Create a unique filename with Arizona timezone timestamp
                timestamp = datetime.datetime.now(arizona_tz).strftime('%Y%m%d_%H%M%S')
                out_name = f"iTrip_Report_{timestamp}.csv"
                
                # Alternatively, use original filename
                # out_name = filename
                
                out_path = os.path.join(DOWNLOAD_FOLDER, out_name)
                
                with open(out_path, 'wb') as f:
                    f.write(data)
                
                file_size = os.path.getsize(out_path)
                logger.info(f"✓ SUCCESS: Downloaded CSV ({file_size} bytes) to {out_path}")
                download_count += 1
                
                # Mark email as processed
                record_processed_email(msg_id)
                
            except Exception as e:
                logger.error(f"Failed to download attachment: {str(e)}")
        
        if not csv_found and not args.list_only:
            logger.debug(f"No CSV attachments found in this email")
    
    if args.list_only:
        logger.info(f"Listed {len(messages)} emails matching the search criteria")
        return True
        
    if processed_count > 0:
        logger.info(f"Skipped {processed_count} already processed emails")
        
    if download_count > 0:
        logger.info(f"Successfully downloaded {download_count} CSV attachments")
        return True
    else:
        logger.warning("No CSV attachments found in the matching emails")
        return False

def main():
    """Main entry point for the Gmail downloader script"""
    if args.list_only:
        logger.info("Running in LIST-ONLY mode (no downloads)")
    elif args.all_emails:
        logger.info("Running in ALL-EMAILS mode (checking all emails)")
    elif args.ignore_sender:
        logger.info("Running with IGNORE-SENDER option (searching by subject only)")
    elif args.force:
        logger.info("Running with FORCE option (re-downloading previously processed emails)")
    elif args.use_label:
        logger.info(f"Searching by label: {args.use_label}")
    
    logger.info(f"Download folder: {DOWNLOAD_FOLDER}")
    
    success = download_today_csv()
    
    if args.list_only:
        logger.info("✓ COMPLETE: Email listing completed")
    elif success:
        logger.info("✓ COMPLETE: CSV download process completed successfully")
    else:
        logger.warning("⚠ COMPLETE: No CSV files were downloaded")
        
    # Helper message if no emails were found
    if not success and not args.list_only:
        logger.info("\nTIP: Try these options to troubleshoot:")
        logger.info("  - List all recent emails: python gmail_downloader.py --list-only --all-emails")
        logger.info("  - Ignore sender (search by subject only): python gmail_downloader.py --ignore-sender")
        logger.info("  - Force re-download of emails: python gmail_downloader.py --force")
        logger.info("  - Use a Gmail label instead: python gmail_downloader.py --use-label \"iTrip\"")
        logger.info("  - Check emails from yesterday: python gmail_downloader.py --days 1")
        logger.info("  - Show debug info: python gmail_downloader.py --debug")
        logger.info("  - Specify download location: python gmail_downloader.py --output-dir \"PATH\"")
    
    return success

if __name__ == "__main__":
    main()