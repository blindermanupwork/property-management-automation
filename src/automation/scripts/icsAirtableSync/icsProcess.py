#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ICS → Airtable synchroniser
#
# • Handles ICS feeds from multiple sources
# • Preserves complete history by cloning records for changes
# • Ensures ONLY ONE active record per reservation UID
# • Marks ALL older versions as "Old" when creating Modified/Removed
# • Concurrent processing of ICS feeds
# ---------------------------------------------------------------------------
import os
import sys
import asyncio
import aiohttp
import csv, logging, os, shutil
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import datetime, date
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from itertools import combinations
import re
import requests
from icalendar import Calendar
from pyairtable import Api
from pathlib import Path
import pytz

# Import the automation config
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.automation.config_wrapper import Config

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
# Use Config class for environment variables and paths

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL DATE FILTERING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
# These variables control which events are processed from ICS feeds based on dates.
# All filtering is based on the event's CHECK-IN DATE (start date).

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ BASIC DATE VARIABLES                                                        │
# └─────────────────────────────────────────────────────────────────────────────┘
today = None                    # Set to current date when script runs

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ LOOKBACK FILTERING                                                          │
# │ Controls how far back in time to include events                            │
# └─────────────────────────────────────────────────────────────────────────────┘
lookback_threshold = None       # Set from FETCH_RESERVATIONS_MONTHS_BEFORE
# Example: If FETCH_RESERVATIONS_MONTHS_BEFORE=2 and today is 2025-05-29:
#   - lookback_threshold = 2025-03-29 (2 months ago)
#   - Events with check-in >= 2025-03-29 will be processed
#   - Events with check-in < 2025-03-29 will be IGNORED

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ FUTURE FILTERING                                                            │
# │ Controls how far into the future to include events                         │
# └─────────────────────────────────────────────────────────────────────────────┘
future_start_threshold = None   # Set from IGNORE_BLOCKS_MONTHS_AWAY
future_end_threshold = None     # Set from IGNORE_EVENTS_ENDING_MONTHS_AWAY
# Example: If IGNORE_BLOCKS_MONTHS_AWAY=6 and today is 2025-05-29:
#   - future_start_threshold = 2025-11-29 (6 months from now)
#   - Events with check-in > 2025-11-29 will be IGNORED
#   - Events with check-in <= 2025-11-29 will be processed

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ IGNORE FLAGS                                                                │
# │ Boolean flags that enable/disable specific filtering rules                 │
# └─────────────────────────────────────────────────────────────────────────────┘
ignore_past = False             # Set from IGNORE_EVENTS_ENDING_BEFORE_TODAY
# Example: If IGNORE_EVENTS_ENDING_BEFORE_TODAY=true:
#   - Events with check-out < today will be IGNORED
#   - Useful for skipping events that have already ended

ignore_future_start = False     # Set to True if IGNORE_BLOCKS_MONTHS_AWAY is configured
# When True: Events starting too far in the future are ignored

ignore_future_end = False       # Set to True if IGNORE_EVENTS_ENDING_MONTHS_AWAY is configured  
# When True: Events ending too far in the future are ignored

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ EXAMPLE CONFIGURATION (MATCHES CSV PROCESSING)                             │
# └─────────────────────────────────────────────────────────────────────────────┘
# Your current .env settings:
#   FETCH_RESERVATIONS_MONTHS_BEFORE=2    → Process events starting 2+ months ago
#   HARDCODED: 3 months ahead              → Ignore events starting 3+ months ahead (matches csvProcess.py)
#   IGNORE_EVENTS_ENDING_BEFORE_TODAY=true → Ignore events that already ended
#
# With today = 2025-05-29, this means:
#   ✅ PROCESS: Events with check-in between 2025-03-29 and 2025-08-29 (same as CSV processing)
#   ❌ IGNORE:  Events with check-in before 2025-03-29 (too old)
#   ❌ IGNORE:  Events with check-in after 2025-08-29 (too far ahead)
#   ❌ IGNORE:  Events with check-out before 2025-05-29 (already ended)

LOG_FILE = str(Config.get_logs_dir() / "ics_sync.log")

# Fields to skip when cloning records (records Airtable won't let us write back)
WRITE_BLACKLIST = {
    "Final Service Time",          # computed roll-ups
    "Sync Date and Time",
    "Sync Details"
}

# Service fields to preserve when cloning records
HCP_FIELDS = [
    "Service Job ID", "Job Creation Time", "Sync Status",
    "Scheduled Service Time", "Sync Date and Time", "Sync Details",
    "Job Status", "Custom Service Time", "Entry Source"
]

# --- LOGGING -----------------------------------------------------------
LOG_PATH = LOG_FILE

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Remove any existing handlers to start fresh
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create file handler with PST timezone
file_handler = logging.FileHandler(LOG_PATH)
file_handler.setLevel(logging.INFO)

# Configure timezones: PST for logging, Arizona for Airtable data
mst = pytz.timezone('America/Phoenix')  # For logging
arizona_tz = pytz.timezone('America/Phoenix')  # For Airtable timestamps
class MSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=mst)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

file_formatter = MSTFormatter("%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create console handler with a simpler format (no level name)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)

# Add filter to exclude detailed digest logs from console
class ExcludeDigestFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        # Skip the run digest section and all property details in console output
        if "Run digest" in message:
            return False
        if " * " in message:
            return False
        if message.startswith("Feed ->") or message.startswith("URL ->"):
            return False
        if "  " in message and any(x in message for x in ["New", "Modified", "Removed", "Unchanged"]):
            return False
        return True

console_handler.addFilter(ExcludeDigestFilter())
logger.addHandler(console_handler)

# Start the run
logging.info("=== ICS sync run started ===")

# ---------------------------------------------------------------------------
# Helper Functions for Environment Variables
# ---------------------------------------------------------------------------
def getenv_bool(key, default=False):
    """Helper function to get boolean environment variables"""
    value = Config.get(key, str(default))
    return value.lower() in ('true', '1', 'yes', 'on') if isinstance(value, str) else bool(value)

def getenv_int(key, default=0):
    """Helper function to get integer environment variables"""
    try:
        return int(Config.get(key, str(default)))
    except (ValueError, TypeError):
        return default

# ---------------------------------------------------------------------------
# BatchCollector – collects 10-row chunks for batch_update / batch_create
# ---------------------------------------------------------------------------
class BatchCollector:
    def __init__(self, table, batch_size=10, op="update"):
        self.table   = table
        self.size    = batch_size
        self.op      = op            # "update" or "create"
        self.records = []
        self.count   = 0

    def add(self, record):
        self.records.append(record)
        if len(self.records) >= self.size:
            self.flush()

    def flush(self):
        if not self.records:
            return
        try:
            if self.op == "update":
                # dedupe on record ID
                seen = set()
                unique = []
                for r in self.records:
                    rid = r.get("id") or r.get("record_id")
                    if rid not in seen:
                        seen.add(rid)
                        unique.append(r)
                self.table.batch_update(unique)
                self.count += len(unique)
            else:
                # create
                self.table.batch_create([r["fields"] for r in self.records])
                self.count += len(self.records)
        except Exception as e:
            logging.error(f"Batch {self.op} error: {e}", exc_info=True)
        finally:
            self.records = []

    def done(self):
        self.flush()
        return self.count

# ---------------------------------------------------------------------------
# Clone Helper - clone an Airtable record with changes
# ---------------------------------------------------------------------------
def mark_all_as_old_and_clone(table, records, field_to_change, now_iso, status="Modified"):
    """
    • records ....... list of records with same UID to mark as Old
    • field_to_change e.g. {"Overlapping Dates": True}
    
    1. Marks ALL records as "Old"
    2. Creates ONE new clone with the specified changes and status
    3. Preserves all HCP fields from the most recent ACTIVE record
    4. Returns the new record ID
    """
    update_batch = BatchCollector(table, op="update")
    
    # Find the most recent ACTIVE record to use as template
    if not records:
        return None
    
    # Filter for active records (New or Modified)
    active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
    
    # If no active records, use the most recent record
    if active_records:
        latest = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
    else:
        latest = max(records, key=lambda r: r["fields"].get("Last Updated", ""))
    
    old_f = latest["fields"]
    
    # Mark ALL records as Old
    for record in records:
        update_batch.add({
            "id": record["id"],
            "fields": {"Status": "Old", "Last Updated": now_iso}
        })
    
    # Flush updates
    update_batch.done()
    
    # Build clone (copy everything except blacklist)
    clone = {k: v for k, v in old_f.items() if k not in WRITE_BLACKLIST}
    
    # IMPORTANT: Explicitly preserve ALL HCP fields from the latest record
    # This ensures they're carried forward even if some would normally be excluded
    for hcp_field in HCP_FIELDS:
        if hcp_field in old_f:
            # FORCE copy all HCP fields, even those in WRITE_BLACKLIST
            # This ensures fields like "Service Job ID" are preserved
            clone[hcp_field] = old_f[hcp_field]
    
    # Apply the changes and status
    clone.update(Status=status, **field_to_change, **{"Last Updated": now_iso})
    
    # Write new row
    return table.create(clone)

# ---------------------------------------------------------------------------
# Keyword Mappings for ICS Parsing
# ---------------------------------------------------------------------------
# Ensure these values EXACTLY match your Airtable Single Select options
ENTRY_TYPE_KEYWORDS = {
    'reserved': 'Reservation',
    'reservation': 'Reservation',
    'blocked': 'Block',
    'block': 'Block',
    'maintenance': 'Block',
    'owner stay': 'Owner Stay',
    'Service': 'Block',
    'not available': 'Block'
}
DEFAULT_ENTRY_TYPE = "Reservation"

SERVICE_TYPE_KEYWORDS = {
    'clean': 'Service',
    'maintenance': 'Maintenance',
    'repair': 'Maintenance',
    'inspection': 'Inspection',
}
DEFAULT_SERVICE_TYPE = None

BLOCK_TYPE_KEYWORDS = {
    'owner': 'Owner Block',
    'maintenance': 'Maintenance Block',
    'Service': 'Service Block',
    'prep': 'Prep Block',
    'buffer': 'Buffer Block',
}
DEFAULT_BLOCK_TYPE = None

ENTRY_SOURCE_KEYWORDS = {
    'airbnb': 'Airbnb',
    'booking.com': 'Booking.com',
    'booking': 'Booking.com',
    'guesty': 'Guesty',
    'homeaway': 'VRBO',
    'vrbo': 'VRBO',
    'hospitable': 'Hospitable',
    'hostshare': 'Hostshare',
    'hosttools': 'HostTools',
    'lodgify': 'Lodgify',
    'ownerrez': 'OwnerRez',
    'yourporter': 'YourPorter',
    # Add keywords found within aggregated feeds
    'channel: airbnb': 'Airbnb',
    'channel: vrbo': 'VRBO',
    'channel: booking': 'Booking.com',
}
DEFAULT_ENTRY_SOURCE = None

def detect_entry_source_from_url(url):
    """Extract source platform from ICS URL"""
    url_lower = url.lower()
    
    # Common patterns
    if 'airbnb' in url_lower:
        return 'Airbnb'
    elif 'vrbo.com' in url_lower or 'homeaway' in url_lower:
        return 'VRBO'
    elif 'booking.com' in url_lower:
        return 'Booking.com'
    elif 'hospitable.com' in url_lower:
        return 'Hospitable'
    elif 'hosttools.com' in url_lower:
        return 'HostTools'
    elif 'lodgify.com' in url_lower:
        return 'Lodgify'
    
    return None

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def convert_flag_value(value):
    """Convert Airtable flag values to bool for consistent comparison"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "checked", "t", "y", "1")
    return bool(value)

def normalize_date_for_comparison(date_value):
    """Convert any date format to YYYY-MM-DD for consistent comparison"""
    if not date_value:
        return ""
    try:
        dt = parse(date_value).date()
        return dt.isoformat()
    except Exception:
        return date_value

# ---------------------------------------------------------------------------
# ICS Feed Processing Functions
# ---------------------------------------------------------------------------
def mark_removed_feeds_old(reservations_table, ics_feeds_table):
    """
    Any feed in the ICS Feeds table marked 'Remove' will have all its
    New/Modified reservations in the Reservations table marked Old.
    """
    logging.info("Checking for feeds flagged 'Remove' to retire their reservations...")
    try:
        # 1) Fetch all feeds where Feed Status = 'Remove'
        remove_records = ics_feeds_table.all(
            formula="{Feed Status} = 'Remove'",
            fields=["ICS URL"]
        )
        urls_to_remove = [
            rec["fields"].get("ICS URL")
            for rec in remove_records
            if rec.get("fields", {}).get("ICS URL")
        ]

        logging.info(f"Found {len(urls_to_remove)} feeds flagged Remove.")

        # 2) For each URL, find any active New/Modified reservations and mark them Old
        now_iso = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")
        for url in urls_to_remove:
            # build a formula to grab only New/Modified for this feed
            formula = (
                "AND("
                f"{{ICS URL}} = '{url}', "
                "OR({Status} = 'New', {Status} = 'Modified')"
                ")"
            )
            to_retire = reservations_table.all(formula=formula)
            logging.info(f"Feed {url!r}: retiring {len(to_retire)} active reservation(s).")

            # Use BatchCollector for efficient updates
            update_batch = BatchCollector(reservations_table, op="update")
            for rec in to_retire:
                update_batch.add({
                    "id": rec["id"],
                    "fields": {"Status": "Old", "Last Updated": now_iso}
                })
            update_batch.done()

        logging.info("Finished retiring Remove-flagged feeds.")
    except Exception as e:
        logging.error(f"Error while marking Remove feeds Old: {e}", exc_info=True)

def get_active_ics_urls_from_airtable(feeds_table):
    """Fetches active ICS URLs and their linked Property IDs from the ICS Feeds table."""
    urls_to_process = []
    property_link_field_name = "Property Name"  # Make sure this matches your Airtable

    try:
        # First, let's see what's actually in the table
        all_records = feeds_table.all()  # Get all fields to see what's available
        logging.info(f"DEBUG: Found {len(all_records)} total records in ICS Feeds table")
        
        # Show available fields in first record
        if all_records:
            sample_fields = list(all_records[0].get("fields", {}).keys())
            logging.info(f"DEBUG: Available fields: {sample_fields}")
        
        for i, record in enumerate(all_records[:3]):  # Show first 3 records
            fields = record.get("fields", {})
            url = fields.get("ICS URL", "NO URL")
            status = fields.get("Feed Status", "NO STATUS")
            prop_field = fields.get(property_link_field_name, "NO PROPERTY LINK")
            logging.info(f"DEBUG: Record {i+1}: URL='{url}', Status='{status}', Property='{prop_field}'")
        
        # Now try to get active ones
        formula = "{Feed Status} = 'Active'"
        # Fetch URL and the linked Property record ID field (include Feed Status for formula to work)
        records = feeds_table.all(fields=["ICS URL", "Feed Status", property_link_field_name], formula=formula)
        logging.info(f"DEBUG: Formula returned {len(records)} active records")
        
        url_to_prop_map = {}  # To store the mapping: {ics_url: property_record_id}

        for record in records:
            fields = record.get("fields", {})
            url = fields.get("ICS URL")
            prop_links = fields.get(property_link_field_name)

            # Skip non-HTTP URLs (CSV feed identifiers, etc.)
            if url and not (url.startswith("http://") or url.startswith("https://")):
                logging.debug(f"Skipping non-HTTP URL: '{url}' (likely a CSV feed identifier)")
                continue

            logging.info(f"DEBUG: Processing URL='{url}', prop_links='{prop_links}', type={type(prop_links)}")
            
            if url and prop_links and isinstance(prop_links, list) and len(prop_links) > 0:
                # Assumes only ONE property linked per URL in the Feeds table
                if len(prop_links) == 1:
                    prop_id = prop_links[0]
                    if url in url_to_prop_map and url_to_prop_map[url] != prop_id:
                         logging.warning(f"ICS URL '{url}' is linked to multiple properties ({url_to_prop_map[url]}, {prop_id}) via '{feeds_table.name}'. Using first found property link.")
                    url_to_prop_map[url] = prop_id
                    logging.info(f"DEBUG: Successfully mapped URL '{url[:50]}...' to property '{prop_id}'")
                else:
                     logging.warning(f"ICS URL '{url}' in '{feeds_table.name}' links to {len(prop_links)} properties. Cannot determine unique property. Skipping URL.")
            elif url:
                logging.warning(f"Active ICS URL '{url}' is missing its Property link ('{property_link_field_name}' field) in the '{feeds_table.name}' table. Skipping URL. Got: {prop_links} (type: {type(prop_links)})")

        logging.info(f"Fetched {len(url_to_prop_map)} active ICS URLs mapped to Property IDs from Airtable.")
        return url_to_prop_map

    except Exception as e:
        # Check for specific error indicating 'Feed Status' field missing
        if isinstance(e, requests.exceptions.HTTPError) and 'UNKNOWN_FIELD_NAME' in str(e) and 'Feed Status' in str(e):
             logging.warning(f"Field 'Feed Status' not found in '{feeds_table.name}'. Fetching ALL URLs. Consider adding a 'Feed Status' field with 'Active' option to filter.")
             try:
                  # Retry without the formula
                  records = feeds_table.all(fields=["ICS URL", property_link_field_name])
                  url_to_prop_map = {}  # Reset map
                  for record in records:
                       fields = record.get("fields", {})
                       url = fields.get("ICS URL")
                       prop_links = fields.get(property_link_field_name)
                       if url and prop_links and isinstance(prop_links, list) and len(prop_links) == 1:
                            url_to_prop_map[url] = prop_links[0]
                  logging.info(f"Fetched {len(url_to_prop_map)} ICS URLs (unfiltered) mapped to Property IDs from Airtable.")
                  return url_to_prop_map
             except Exception as e2:
                  # Check if the error is STILL the field name - indicates persistent issue
                  if isinstance(e2, requests.exceptions.HTTPError) and 'UNKNOWN_FIELD_NAME' in str(e2) and property_link_field_name in str(e2):
                       logging.critical(f"CRITICAL: Field '{property_link_field_name}' still not found in '{feeds_table.name}' even after correction. Verify field name and type in Airtable EXACTLY.")
                  logging.error(f"Error fetching ICS URLs (unfiltered) from '{feeds_table.name}': {e2}", exc_info=True)
                  return {}
        else:
            # Log other errors, including if the corrected field name is still wrong
             if isinstance(e, requests.exceptions.HTTPError) and 'UNKNOWN_FIELD_NAME' in str(e) and property_link_field_name in str(e):
                  logging.critical(f"CRITICAL: Field '{property_link_field_name}' not found in '{feeds_table.name}'. Verify field name and type in Airtable EXACTLY.")
             logging.error(f"Error fetching ICS URLs from Airtable table '{feeds_table.name}': {e}", exc_info=True)
             return {}

async def fetch_ics_async(session, url):
    """Asynchronously fetches ICS content from a URL."""
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                return url, False, None, f"HTTP {resp.status} - {resp.reason}"
            content_type = resp.headers.get('Content-Type', '')
            if 'text/calendar' not in content_type:
                logging.warning(f"URL {url} did not return Content-Type 'text/calendar'. Response may not be valid ICS.")
            text = await resp.text()
            logging.info(f"Successfully fetched ICS from {url}")
            return url, True, text, None
    except asyncio.TimeoutError:
        msg = f"Timeout error fetching {url}"
        logging.error(msg)
        return url, False, None, msg
    except Exception as e:
        msg = f"Unexpected error fetching {url}: {str(e)}"
        logging.error(msg)
        return url, False, None, msg

def parse_ics(ics_text: str, feed_url: str):
    """
    Parses ICS text into a list of event dicts, applying date-filters and keyword fallback.
    Respects config settings for date filtering.
    """
    global lookback_threshold, future_start_threshold, future_end_threshold
    global today, ignore_past, ignore_future_start, ignore_future_end

    total_vevents = 0
    processed_events = []
    skipped_past = 0
    skipped_future = 0
    skipped_other = 0
    
    # Check for calendar-level entry source first
    calendar_level_entry_source = None
    # Check for URL-based detection first (most reliable)
    url_source = detect_entry_source_from_url(feed_url)
    if url_source:
        calendar_level_entry_source = url_source
    # This will store the raw calendar content for later fallback check if needed
    raw_calendar_content = None
    
    # 2) Parse the calendar
    try:
        cal = Calendar.from_ical(ics_text)
        
        # Store raw calendar content for potential later checks
        try:
            raw_calendar = cal.to_ical()
            try:
                raw_calendar_content = raw_calendar.decode("utf-8", errors="ignore").lower()
            except Exception:
                raw_calendar_content = str(raw_calendar).lower()
        except Exception as e:
            logging.debug(f"Error extracting raw calendar content: {e}")
            raw_calendar_content = ics_text.lower()
            
        # Try to extract source from calendar properties
        cal_prodid = str(cal.get('PRODID', '')).lower()
        cal_name = str(cal.get('X-WR-CALNAME', '')).lower()
        cal_desc = str(cal.get('X-WR-CALDESC', '')).lower()
        
        # Combine calendar metadata
        cal_text = f"{cal_prodid} {cal_name} {cal_desc}"
        
        # Check for entry source in calendar metadata
        for k, v in ENTRY_SOURCE_KEYWORDS.items():
            if (isinstance(k, re.Pattern) and k.search(cal_text)) or (isinstance(k, str) and k in cal_text):
                calendar_level_entry_source = v
                break
        
        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            total_vevents += 1
            uid = str(component.get("UID", "")).strip()
            summary = str(component.get("SUMMARY", "")).strip()
            description = str(component.get("DESCRIPTION", "")).strip()

            # extract raw DTSTART/DTEND
            try:
                raw_start = component.get("DTSTART").dt
                raw_end   = component.get("DTEND").dt
            except Exception as e:
                skipped_other += 1
                continue

            # ─── normalize to dates ───
            # if datetime → .date(); if date → keep; else (e.g. time-only) → skip
            if isinstance(raw_start, datetime):
                dtstart = raw_start.date()
            elif isinstance(raw_start, date):
                dtstart = raw_start
            else:
                skipped_other += 1
                continue

            if isinstance(raw_end, datetime):
                dtend = raw_end.date()
            elif isinstance(raw_end, date):
                dtend = raw_end
            else:
                skipped_other += 1
                continue
            # ─────────────────────────────

            # Apply date filtering based on CHECK-IN date only (match CSV processing)
            if lookback_threshold and dtstart < lookback_threshold:
                skipped_past += 1
                continue
            # REMOVED: ignore_past filter to match CSV processing behavior
            # CSV processing only filters by check-in dates, not check-out dates
                
            # Future filters based on CHECK-IN date
            if ignore_future_start and dtstart > future_start_threshold:
                skipped_future += 1
                continue
            if ignore_future_end and dtend > future_end_threshold:
                skipped_future += 1
                continue

            # 4) keyword‐map lookup
            entry_type   = DEFAULT_ENTRY_TYPE
            service_type = DEFAULT_SERVICE_TYPE
            block_type   = DEFAULT_BLOCK_TYPE
            # Start with calendar-level entry source if found
            url_source = detect_entry_source_from_url(feed_url)
            entry_source = url_source or calendar_level_entry_source or DEFAULT_ENTRY_SOURCE

            text = (summary + " " + description + " " + uid).lower()
            
            # Only try to determine entry source if not already found at calendar level
            if not entry_source or entry_source == DEFAULT_ENTRY_SOURCE:
                # Try to find entry source in the event text
                for k, v in ENTRY_SOURCE_KEYWORDS.items():
                    if (isinstance(k, re.Pattern) and k.search(text)) or (isinstance(k, str) and k in text):
                        entry_source = v
                        break
                        
            # Entry Type
            for k, v in ENTRY_TYPE_KEYWORDS.items():
                if k in text:
                    entry_type = v
                    break
            # Block Type
            if entry_type == "Block":
                for k, v in BLOCK_TYPE_KEYWORDS.items():
                    if k in text:
                        block_type = v
                        break
            # Service Type
            for k, v in SERVICE_TYPE_KEYWORDS.items():
                if k in text:
                    service_type = v
                    break

            # 5) fallback scan raw VEVENT if any still None
            raw_vevent_content = None
            if None in (entry_source, entry_type, service_type) or (entry_type == "Block" and block_type is None) or entry_source == DEFAULT_ENTRY_SOURCE:
                raw = component.to_ical()
                try:
                    raw_vevent_content = raw.decode("utf-8", errors="ignore").lower()
                except Exception:
                    raw_vevent_content = str(raw).lower()

                if entry_source is None or entry_source == DEFAULT_ENTRY_SOURCE:
                    for k, v in ENTRY_SOURCE_KEYWORDS.items():
                        if (isinstance(k, re.Pattern) and k.search(raw_vevent_content)) or (isinstance(k, str) and k in raw_vevent_content):
                            entry_source = v
                            break
                            
                if entry_type is None:
                    for k, v in ENTRY_TYPE_KEYWORDS.items():
                        if k in raw_vevent_content:
                            entry_type = v
                            break
                            
                if entry_type == "Block" and block_type is None:
                    for k, v in BLOCK_TYPE_KEYWORDS.items():
                        if k in raw_vevent_content:
                            block_type = v
                            break
                            
                if service_type is None:
                    for k, v in SERVICE_TYPE_KEYWORDS.items():
                        if k in raw_vevent_content:
                            service_type = v
                            break
            
            # 6) If entry source still not found, check the entire calendar
            if (entry_source is None or entry_source == DEFAULT_ENTRY_SOURCE) and raw_calendar_content:
                for k, v in ENTRY_SOURCE_KEYWORDS.items():
                    if (isinstance(k, re.Pattern) and k.search(raw_calendar_content)) or (isinstance(k, str) and k in raw_calendar_content):
                        entry_source = v
                        break
                
            # 7) Try extracting from the feed URL as a last resort
            if entry_source is None or entry_source == DEFAULT_ENTRY_SOURCE:
                url_lower = feed_url.lower()
                if 'airbnb' in url_lower:
                    entry_source = 'Airbnb'
                elif 'vrbo.com' in url_lower or 'homeaway' in url_lower:
                    entry_source = 'VRBO'
                elif 'booking.com' in url_lower:
                    entry_source = 'Booking.com'
                # Add other URL patterns as needed

            # 8) final defaults
            if entry_type == "Reservation" and service_type is None:
                service_type = "Turnover"
            if entry_type == "Block" and service_type is None:
                service_type = "Needs Review"

            # 9) collect
            processed_events.append({
                "uid": uid,
                "dtstart": dtstart.isoformat(),
                "dtend": dtend.isoformat(),
                "ics_url": feed_url,
                "summary_raw": summary,
                "description_raw": description,
                "entry_type": entry_type,
                "service_type": service_type,
                "block_type": block_type,
                "entry_source": entry_source,
                # Initialize flag fields that will be calculated later
                "overlapping": False,
                "same_day_turnover": False,
            })

        logging.info(f"Parsed feed={feed_url}: total_vevents={total_vevents}, processed={len(processed_events)}, skipped_past={skipped_past}, skipped_future={skipped_future}, skipped_other={skipped_other}")
    except Exception as e:
        logging.error(f"Critical error parsing ICS from {feed_url}: {e}", exc_info=True)

    return total_vevents, processed_events

def update_cron_table(cron_table, update_collector, create_collector, feed_url: str, success: bool, 
                     error_msg: str = None, total_vevents: int = 0, processed_count: int = 0):
    """
    Adds an update to the appropriate batch collector based on whether the record exists.
    """
    now_str = datetime.now(arizona_tz).isoformat(sep=' ', timespec='seconds')
    
    try:
        # Use formula to find exact URL match
        formula = f"{{ICS URL}} = '{feed_url}'"
        existing_rows = cron_table.all(formula=formula, fields=["ICS URL"])
        
        if existing_rows:
            # URL exists, queue update to the update collector
            existing_row = existing_rows[0]
            
            fields_update = {
                "ICS URL VEVENTS #": total_vevents,
                "ICS URL VEVENTS Reservations": processed_count,
                "Last Run": now_str,
                "ICS URL Response": "Success" if success else (error_msg or "Unknown Error")
            }
            
            logging.info(f"Queueing update for ICS Cron row: feed={feed_url}, row_id={existing_row['id']}")
            update_collector.add({
                "id": existing_row["id"],
                "fields": fields_update
            })
        else:
            # URL doesn't exist, queue creation to the create collector
            fields_create = {
                "ICS URL": feed_url,
                "ICS URL VEVENTS #": total_vevents,
                "ICS URL VEVENTS Reservations": processed_count,
                "Last Run": now_str,
                "First Run": now_str,
                "ICS URL Response": "Success" if success else (error_msg or "Unknown Error")
            }
            
            logging.info(f"Queueing creation for ICS Cron row: feed={feed_url}")
            create_collector.add({"fields": fields_create})
    except Exception as e:
        logging.error(f"Error preparing ICS Cron update for feed={feed_url}: {e}")

# ---------------------------------------------------------------------------
# Data Preparation and Processing Functions
# ---------------------------------------------------------------------------
def get_records_by_uid_feed(table):
    """Gets existing records keyed by (UID, ICS_URL)."""
    by_feed = defaultdict(list)
    # Fetch fields needed for comparison AND for copying to new records
    fields_to_fetch = [
        "Reservation UID", "ICS URL", "Check-in Date", "Check-out Date",
        "Status", "Entry Type", "Service Type", "Block Type", "Entry Source",
        "Property ID", "Last Updated", "Overlapping Dates", "Same-day Turnover"
    ] + HCP_FIELDS
    
    try:
        logging.info(f"Fetching existing records from '{table.name}' using fields: {fields_to_fetch}...")
        all_existing = table.all(fields=fields_to_fetch)
        logging.info(f"Fetched {len(all_existing)} records. Grouping by (UID, Feed)...")
        for record in all_existing:
            fields = record.get("fields", {})
            res_uid = fields.get("Reservation UID")
            feed = fields.get("ICS URL")
            if res_uid and feed:
                by_feed[(res_uid, feed)].append(record)
        logging.info(f"Finished grouping existing records.")
    except Exception as e:
        logging.error(f"Error fetching/grouping records by UID/Feed: {e}", exc_info=True)
        raise  # Stop the script if we can't load existing records
    return dict(by_feed)

def calculate_flags(events, url_to_prop):
    """
    Calculate overlapping dates and same-day turnover flags for all events locally.
    Similar to the CSV process function.
    """
    # Group by property_id
    by_property = defaultdict(list)
    for ev in events:
        # Get the property ID for this event's ICS URL
        property_id = url_to_prop.get(ev["ics_url"])
        if property_id:
            ev["property_id"] = property_id
            by_property[property_id].append(ev)
    
    # Process each property
    for property_id, property_events in by_property.items():
        # CHANGE HERE: Filter for reservation events only when checking overlaps
        reservation_events = [event for event in property_events if event["entry_type"] == "Reservation"]
        
        # Find overlaps (only between reservations)
        for a, b in combinations(reservation_events, 2):
            a_start = parse(a["dtstart"]).date()
            a_end = parse(a["dtend"]).date()
            b_start = parse(b["dtstart"]).date()
            b_end = parse(b["dtend"]).date()
            
            # Check for overlap: a starts before b ends AND a ends after b starts
            if a_start < b_end and a_end > b_start:
                a["overlapping"] = True
                b["overlapping"] = True
        
        # Find same-day turnovers - ONLY for Reservation entries (no change needed here)
        checkin_dates = {parse(res["dtstart"]).date() for res in reservation_events}
        
        for res in reservation_events:
            checkout_date = parse(res["dtend"]).date()
            checkin_date = parse(res["dtstart"]).date()
            
            # If checkout date equals another reservation's check-in date (and not its own)
            if checkout_date in checkin_dates and checkout_date != checkin_date:
                res["same_day_turnover"] = True
    
    return events

def has_changes(event, airtable_record):
    """Carefully detect if any important fields have changed"""
    
    # Get fields from Airtable record
    at_fields = airtable_record["fields"]
    
    # 1. Check dates (normalize to YYYY-MM-DD for comparison)
    at_checkin = normalize_date_for_comparison(at_fields.get("Check-in Date", ""))
    at_checkout = normalize_date_for_comparison(at_fields.get("Check-out Date", ""))
    
    # Event dates are already in ISO format
    if at_checkin != event["dtstart"] or at_checkout != event["dtend"]:
        logging.info(f"Dates changed for {event['uid']}: "
                    f"Check-in: {at_checkin} -> {event['dtstart']}, "
                    f"Check-out: {at_checkout} -> {event['dtend']}")
        return True
    
    # 2. Check property link
    at_property_links = at_fields.get("Property ID", [])
    at_property_id = at_property_links[0] if at_property_links else None
    
    if at_property_id != event.get("property_id"):
        logging.info(f"Property changed for {event['uid']}: "
                    f"{at_property_id} -> {event.get('property_id')}")
        return True
    
    # 3. Check flags
    at_overlap = convert_flag_value(at_fields.get("Overlapping Dates"))
    at_sameday = convert_flag_value(at_fields.get("Same-day Turnover"))
    
    if at_overlap != event["overlapping"] or at_sameday != event["same_day_turnover"]:
        logging.info(f"Flags changed for {event['uid']}: "
                    f"Overlap: {at_overlap} -> {event['overlapping']}, "
                    f"Same-day: {at_sameday} -> {event['same_day_turnover']}")
        return True
    
    # 4. Check other key fields
    if at_fields.get("Entry Type") != event["entry_type"]:
        logging.info(f"Entry Type changed for {event['uid']}: "
                    f"{at_fields.get('Entry Type')} -> {event['entry_type']}")
        return True
    
    if at_fields.get("Service Type") != event["service_type"]:
        logging.info(f"Service Type changed for {event['uid']}: "
                    f"{at_fields.get('Service Type')} -> {event['service_type']}")
        return True
    
    if at_fields.get("Block Type") != event["block_type"]:
        logging.info(f"Block Type changed for {event['uid']}: "
                    f"{at_fields.get('Block Type')} -> {event['block_type']}")
        return True
    
    if at_fields.get("Entry Source") != event["entry_source"]:
        logging.info(f"Entry Source changed for {event['uid']}: "
                    f"{at_fields.get('Entry Source')} -> {event['entry_source']}")
        return True
    
    # No important changes detected
    return False

def sync_ics_event(event, existing_records, url_to_prop, table, create_batch, update_batch):
    """
    Synchronize a single ICS event with Airtable.
    Uses mark_all_as_old_and_clone for proper history tracking.
    """
    uid = event["uid"]
    feed_url = event["ics_url"]
    property_id = url_to_prop.get(feed_url)
    now_iso = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")
    
    # Get ALL existing records for this (UID, feed_url) pair
    all_records = existing_records.get((uid, feed_url), [])
    
    # Filter for active records (New or Modified)
    active_records = [r for r in all_records if r["fields"].get("Status") in ("New", "Modified")]
    
    # Handle based on whether we have active records
    if active_records:
        # Get the most recent active record for comparison
        latest_active = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
        
        # Check if any important fields changed
        if has_changes(event, latest_active):
            # Create new fields to change
            new_fields = {
                "Check-in Date": event["dtstart"],
                "Check-out Date": event["dtend"],
                "Entry Type": event["entry_type"],
                "Service Type": event["service_type"],
                "Entry Source": event["entry_source"],
                "Overlapping Dates": event["overlapping"],
                "Same-day Turnover": event["same_day_turnover"],
            }
            
            # Add Block Type if it exists
            if event["block_type"]:
                new_fields["Block Type"] = event["block_type"]
            
            # Add Property ID if it exists
            if property_id:
                new_fields["Property ID"] = [property_id]
            
            # Mark ALL existing records as Old and create one new Modified record
            mark_all_as_old_and_clone(table, all_records, new_fields, now_iso, "Modified")
            
            return "Modified"
        else:
            # No changes - don't update Airtable at all
            return "Unchanged"
    else:
        # Create new record
        new_fields = {
            "Reservation UID": uid,
            "ICS URL": feed_url,
            "Check-in Date": event["dtstart"],
            "Check-out Date": event["dtend"],
            "Status": "New",
            "Entry Type": event["entry_type"],
            "Service Type": event["service_type"],
            "Entry Source": event["entry_source"],
            "Last Updated": now_iso,
            "Overlapping Dates": event["overlapping"],
            "Same-day Turnover": event["same_day_turnover"],
        }
        
        # Add Block Type if it exists
        if event["block_type"]:
            new_fields["Block Type"] = event["block_type"]
        
        # Add Property ID if it exists
        if property_id:
            new_fields["Property ID"] = [property_id]
        
        # First mark any existing non-active records as Old
        if all_records:
            for record in all_records:
                update_batch.add({
                    "id": record["id"],
                    "fields": {"Status": "Old", "Last Updated": now_iso}
                })
        
        # Then create the new record
        create_batch.add({"fields": new_fields})
        
        return "New"

def process_ics_feed(url, events, existing_records, url_to_prop, table, create_batch, update_batch):
    """
    Process all events from a single ICS feed.
    Track which events were processed to identify removals later.
    """
    if not events:
        logging.info(f"Feed {url} has 0 events within the date filter range. Skipping.")
        return {"New": 0, "Modified": 0, "Unchanged": 0, "Removed": 0}
    
    logging.info(f"Processing feed: {url} with {len(events)} events")
    
    # Track status counts and processed (UID, URL) pairs
    stats = {"New": 0, "Modified": 0, "Unchanged": 0}
    processed_uid_url_pairs = set()  # <-- Change to track UID+URL pairs
    
    # Process each event
    for event in events:
        uid = event["uid"]
        processed_uid_url_pairs.add((uid, url))  # <-- Track the pair
        
        status = sync_ics_event(
            event, 
            existing_records, 
            url_to_prop, 
            table,
            create_batch, 
            update_batch
        )
        
        # Update stats
        if status in stats:
            stats[status] += 1
    
    # Process removed events (in Airtable but not in feed anymore)
    now_iso = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")
    today_iso = date.today().isoformat()
    removed_count = 0
    
    # Get all UIDs for this feed URL
    feed_keys = [(uid, feed_url) for uid, feed_url in existing_records.keys() if feed_url == url]
    
    # Find pairs that exist in Airtable but weren't in this feed
    missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
    
    for uid, feed_url in missing_keys:
        records = existing_records.get((uid, feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        for rec in active_records:
            fields = rec["fields"]
            # Skip if the stay is fully past
            if fields.get("Check-out Date", "") < today_iso:
                continue
                
            # Mark this record as Removed through mark_all_as_old_and_clone
            mark_all_as_old_and_clone(table, records, {}, now_iso, "Removed")
            removed_count += 1
    
    # Return stats including removals
    stats["Removed"] = removed_count
    logging.info(f"Feed {url} completed: {stats['New']} new, {stats['Modified']} modified, "
                f"{stats['Unchanged']} unchanged, {stats['Removed']} removed")
    
    return stats

def update_property_id(reservations_table, ics_feeds_table):
    """
    Links reservations to properties by looking up the ICS URL in the ICS Feeds table.
    Skips any URLs that start with 'csv_' as those are handled by the CSV processor.
    """
    logging.info("Starting Property ID linking...")

    # 1. Build mapping from ICS URL -> Property Record ID from the ICS Feeds table
    url_to_prop_id_map = {}
    property_link_field_name_in_feeds = "Property Name"  # Check if this matches your Airtable
    try:
        logging.info(f"Fetching URL-to-Property mapping from '{ics_feeds_table.name}' (using link field '{property_link_field_name_in_feeds}')...")
        feed_records = ics_feeds_table.all(fields=["ICS URL", property_link_field_name_in_feeds])
        mapped_count = 0
        skipped_count = 0
        for record in feed_records:
            fields = record.get("fields", {})
            url = fields.get("ICS URL")
            prop_links = fields.get(property_link_field_name_in_feeds)
            if url and prop_links and isinstance(prop_links, list) and len(prop_links) == 1:
                 prop_id = prop_links[0]
                 if url in url_to_prop_id_map and url_to_prop_id_map[url] != prop_id:
                      logging.warning(f"Duplicate ICS URL found in Feeds table: {url}. Check configuration.")
                 url_to_prop_id_map[url] = prop_id
                 mapped_count += 1
            elif url and prop_links and len(prop_links) > 1:
                 logging.warning(f"ICS URL '{url}' in Feeds table links to multiple properties ({len(prop_links)}). Cannot reliably link.")
                 skipped_count +=1
            elif url:
                 logging.warning(f"ICS URL '{url}' in Feeds table is missing link via '{property_link_field_name_in_feeds}' field. Cannot map.")
                 skipped_count +=1

        logging.info(f"Built map for {mapped_count} ICS URLs to Property IDs. Skipped {skipped_count} URLs.")
        if not url_to_prop_id_map:
             logging.warning("No valid URL-to-Property mappings found in ICS Feeds table. Cannot link reservations.")
             return

    except Exception as e:
        if isinstance(e, requests.exceptions.HTTPError) and 'UNKNOWN_FIELD_NAME' in str(e) and property_link_field_name_in_feeds in str(e):
             logging.critical(f"CRITICAL: Field '{property_link_field_name_in_feeds}' not found in '{ics_feeds_table.name}'. Verify field name and type in Airtable EXACTLY.")
        logging.error(f"Error building URL-to-Property map from '{ics_feeds_table.name}': {e}", exc_info=True)

        return

    # 2. Iterate through Reservations and update Property ID link if needed
    property_link_field_in_reservations = "Property ID"  # Check if this matches your Airtable
    try:
        logging.info(f"Fetching reservations from '{reservations_table.name}' to check '{property_link_field_in_reservations}' links...")
        reservations_to_check = reservations_table.all(fields=["ICS URL", property_link_field_in_reservations])
        logging.info(f"Checking {len(reservations_to_check)} reservations for Property ID linking.")
        
        # Use BatchCollector for more efficient updates
        update_batch = BatchCollector(reservations_table, op="update")
        
        updated_count = 0
        already_linked_count = 0
        no_mapping_count = 0
        skipped_csv_count = 0

        for res in reservations_to_check:
            res_id = res['id']
            fields = res.get("fields", {})
            res_ics_url = fields.get("ICS URL", "")
            
            # Skip any CSV URLs (handled by CSV processor)
            if res_ics_url.startswith("csv_"):
                skipped_csv_count += 1
                continue
                
            current_prop_link_list = fields.get(property_link_field_in_reservations)

            # Find expected Property ID from our map
            expected_prop_id = url_to_prop_id_map.get(res_ics_url)

            if expected_prop_id:
                # We know what property this reservation *should* link to
                current_prop_id = current_prop_link_list[0] if (current_prop_link_list and isinstance(current_prop_link_list, list) and len(current_prop_link_list) > 0) else None

                if current_prop_id != expected_prop_id:
                    # Link is missing or incorrect, needs update
                    update_batch.add({
                        "id": res_id,
                        "fields": {property_link_field_in_reservations: [expected_prop_id]}
                    })
                    updated_count += 1
                else:
                    already_linked_count += 1
            elif res_ics_url and not res_ics_url.startswith("csv_"):
                 no_mapping_count += 1

        # Finalize the batch updates
        update_batch.done()
        logging.info(f"Property linking summary: Checked={len(reservations_to_check)}, Updated={updated_count}, AlreadyCorrect={already_linked_count}, NoMapping={no_mapping_count}, SkippedCSV={skipped_csv_count}")

    except Exception as e:
        if isinstance(e, requests.exceptions.HTTPError) and 'UNKNOWN_FIELD_NAME' in str(e) and property_link_field_in_reservations in str(e):
             logging.critical(f"CRITICAL: Field '{property_link_field_in_reservations}' not found in '{reservations_table.name}'. Verify field name and type in Airtable EXACTLY.")
        logging.error(f"Error processing reservations for Property ID update: {e}", exc_info=True)

    logging.info("Finished Property ID linking.")

# ---------------------------------------------------------------------------
# Report Generation Functions
# ---------------------------------------------------------------------------
def generate_report(overall_stats, id_to_name):
    """Generate detailed and summary reports"""
    if not overall_stats:
        logging.info("No feeds processed.")
        return
    
    # Track counts for final summary
    total_unchanged = 0
    total_new = 0
    total_modified = 0
    total_removed = 0
    
    # Log run digest (only goes to log file due to filter)
    logging.info("------------  Run digest  ------------")
    
    # Process all feeds and collect stats
    for feed_url, stats in overall_stats.items():
        # Get property name if available
        prop_id = stats.get("property_id")
        prop_name = id_to_name.get(prop_id, "Unknown Property")
        
        # Update totals
        total_unchanged += stats.get("Unchanged", 0)
        total_new += stats.get("New", 0)
        total_modified += stats.get("Modified", 0)
        total_removed += stats.get("Removed", 0)
        
        # Log feed information
        header = f"Feed -> {feed_url} ({prop_name})"
        logging.info(header)
        logging.info(f" * New: {stats.get('New', 0)} reservations")
        logging.info(f" * Modified: {stats.get('Modified', 0)} reservations")
        logging.info(f" * Unchanged: {stats.get('Unchanged', 0)} reservations")
        logging.info(f" * Removed: {stats.get('Removed', 0)} reservations")
    
    # Print summary (will go to both console and log file)
    logging.info("------------  Summary  ------------")
    logging.info(f"Total unchanged: {total_unchanged}")
    logging.info(f"Total new: {total_new}")
    logging.info(f"Total modified: {total_modified}")
    logging.info(f"Total removed: {total_removed}")
    logging.info("------------  End Summary  ------------")

# ---------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------
async def main_async():
    logging.info("Starting ICS sync run...")
    try:
        # Declare globals
        global today, lookback_threshold, future_start_threshold, future_end_threshold
        global ignore_past, ignore_future_start, ignore_future_end
        
        # Load environment variables from Config
        AIRTABLE_API_KEY = Config.get_airtable_api_key()
        AIRTABLE_BASE_ID = Config.get_airtable_base_id()
        AIRTABLE_TABLE_NAME = Config.get_airtable_table_name('reservations')
        PROPERTIES_TABLE_NAME = Config.get_airtable_table_name('properties')
        ICS_FEEDS_TABLE_NAME = Config.get_airtable_table_name('ics_feeds')
        ICS_CRON_TABLE_NAME = Config.get('ICS_CRON_TABLE_NAME', 'ICS Cron')

        # Check required environment variables
        missing_config = Config.validate_config()
        if missing_config:
            logging.error(f"Missing required configuration: {missing_config}")
            return

        api = Api(AIRTABLE_API_KEY)
        reservations_table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
        properties_table = api.table(AIRTABLE_BASE_ID, PROPERTIES_TABLE_NAME)
        ics_feeds_table = api.table(AIRTABLE_BASE_ID, ICS_FEEDS_TABLE_NAME)
        ics_cron_table = api.table(AIRTABLE_BASE_ID, ICS_CRON_TABLE_NAME)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 1) INITIALIZE DATE FILTERING THRESHOLDS
        # ═══════════════════════════════════════════════════════════════════════════
        today = date.today()
        logging.info(f"📅 Today's date: {today.isoformat()}")
        
        # ┌─── PAST EVENTS FILTERING ───────────────────────────────────────────────┐
        # │ DISABLED to match CSV processing: Only filter by check-in dates        │
        # └──────────────────────────────────────────────────────────────────────────┘
        ignore_past = False  # Disabled to match CSV processing behavior
        logging.info("🔄 Matching CSV processing: Only filtering by check-in dates (not check-out dates)")
        
        # ┌─── LOOKBACK THRESHOLD ───────────────────────────────────────────────────┐
        # │ How far back to include events (based on check-in date)                 │
        # │ Example: FETCH_RESERVATIONS_MONTHS_BEFORE=2 means include events        │
        # │          with check-in >= (today - 2 months)                            │
        # └──────────────────────────────────────────────────────────────────────────┘
        months_before = Config.get_fetch_months_before()
        if months_before > 0:
            lookback_threshold = today - relativedelta(months=months_before)
            logging.info(f"⏪ Including events starting after {lookback_threshold.isoformat()} ({months_before} months back)")
        else:
            lookback_threshold = None
            logging.info("⏪ No lookback limit - including events from any past date")
            
        # ┌─── FUTURE START THRESHOLD ───────────────────────────────────────────────┐
        # │ MATCH CSV PROCESSING: Use 3 months ahead (same as csvProcess.py)        │
        # │ This ensures ICS and CSV processing use identical date ranges           │
        # └──────────────────────────────────────────────────────────────────────────┘
        MONTHS_LOOKAHEAD = 3  # Match csvProcess.py exactly
        future_start_threshold = today + relativedelta(months=MONTHS_LOOKAHEAD)
        ignore_future_start = True
        logging.info(f"⏩ Ignoring events starting after {future_start_threshold.isoformat()} (>{MONTHS_LOOKAHEAD} months away - matches CSV processing)")

        # ┌─── FUTURE END THRESHOLD ─────────────────────────────────────────────────┐
        # │ Ignore events ending too far in the future (based on check-out date)    │
        # │ Example: IGNORE_EVENTS_ENDING_MONTHS_AWAY=6 means ignore events         │
        # │          with check-out > (today + 6 months)                            │
        # └──────────────────────────────────────────────────────────────────────────┘
        end_months = getenv_int("IGNORE_EVENTS_ENDING_MONTHS_AWAY", 0) or None
        if end_months is not None:
            future_end_threshold = today + relativedelta(months=end_months)
            ignore_future_end = True
            logging.info(f"⏭️  Ignoring events ending after {future_end_threshold.isoformat()} (>{end_months} months away)")
        else:
            future_end_threshold = None
            ignore_future_end = False
            logging.info("⏭️  No future end limit - including events ending any time in future")
        
        # ┌─── SUMMARY OF ACTIVE FILTERS ────────────────────────────────────────────┐
        # │ Show what date range will actually be processed                          │
        # └───────────────────────────────────────────────────────────────────────────┘
        start_date = lookback_threshold.isoformat() if lookback_threshold else "ANY PAST DATE"
        end_date = future_start_threshold.isoformat() if future_start_threshold else "ANY FUTURE DATE"
        logging.info(f"📊 PROCESSING EVENTS: Check-in dates from {start_date} to {end_date}")
        
        additional_filters = []
        if ignore_future_end:
            additional_filters.append(f"Skip events ending after {future_end_threshold.isoformat()}")
        
        if additional_filters:
            logging.info(f"📋 ADDITIONAL FILTERS: {' | '.join(additional_filters)}")
        else:
            logging.info("📋 FILTERING: Only using check-in date range (matches CSV processing)")
        

        # 1. Mark removed feeds as old
        mark_removed_feeds_old(reservations_table, ics_feeds_table)
        
        # 2. Get active ICS URLs and their property mappings
        url_to_prop_map = get_active_ics_urls_from_airtable(ics_feeds_table)
        if not url_to_prop_map:
            logging.warning("No active ICS URLs found. Exiting.")
            return
        
        # 2.1 Build a map from property ID to name for reporting
        id_to_name = {}
        try:
            prop_records = properties_table.all(fields=[Config.get('PROPERTIES_NAME_FIELD', 'Property Name')])
            for rec in prop_records:
                rec_id = rec["id"]
                name = rec["fields"].get(Config.get('PROPERTIES_NAME_FIELD', 'Property Name'), "")
                if name:
                    id_to_name[rec_id] = name
            logging.info(f"Loaded {len(id_to_name)} property names for reporting")
        except Exception as e:
            logging.warning(f"Could not load property names for reporting: {e}")
        
        # 3. Fetch all feeds concurrently
        urls_to_process = list(url_to_prop_map.keys())
        logging.info(f"Fetching {len(urls_to_process)} ICS feeds concurrently...")
        
        async with aiohttp.ClientSession() as session:
            # Create tasks for all URLs
            fetch_tasks = [fetch_ics_async(session, url) for url in urls_to_process]
            # Run all tasks concurrently
            fetch_results = await asyncio.gather(*fetch_tasks)
        
        # Create batch collectors for cron table
        cron_update_collector = BatchCollector(ics_cron_table, op="update")
        cron_create_collector = BatchCollector(ics_cron_table, op="create")

        # 4. Process feeds and prepare (but don't execute) cron table updates
        feed_results = {}
        for url, success, ics_text, err in fetch_results:
            if success and ics_text:
                # Parse ICS content in a thread pool
                with ThreadPoolExecutor() as executor:
                    total_vevents, processed_events = await asyncio.get_event_loop().run_in_executor(
                        executor, parse_ics, ics_text, url
                    )
                feed_results[url] = {
                    "success": True,
                    "err_msg": None,
                    "total_vevents": total_vevents, 
                    "events": processed_events,
                    "property_id": url_to_prop_map.get(url)
                }
                
                # Queue cron update (but don't execute yet)
                update_cron_table(
                    ics_cron_table,  # Pass the actual table for lookups
                    cron_update_collector,  # Pass the collector for updates
                    cron_create_collector,  # Pass the collector for creations 
                    feed_url=url, 
                    success=success,
                    error_msg=None, 
                    total_vevents=total_vevents,
                    processed_count=len(processed_events)
                )
            else:
                feed_results[url] = {
                    "success": False,
                    "err_msg": err,
                    "total_vevents": 0,
                    "events": [],
                    "property_id": url_to_prop_map.get(url)
                }
                
                # Queue failed feed update
                update_cron_table(
                    ics_cron_table,
                    cron_update_collector,  # For updates
                    cron_create_collector,  # For creations
                    feed_url=url, 
                    success=success,
                    error_msg=err, 
                    total_vevents=0,
                    processed_count=0
                )

        # Now flush all the cron updates at once
        logging.info(f"Executing {len(cron_update_collector.records)} ICS Cron updates in batch...")
        cron_update_count = cron_update_collector.done()
        logging.info(f"Executing {len(cron_create_collector.records)} ICS Cron creations in batch...")
        cron_create_count = cron_create_collector.done()
        logging.info(f"Processed {cron_update_count} cron updates and {cron_create_count} cron creations")
        
        # 5. Calculate flags for all events
        all_events = []
        for url, result in feed_results.items():
            if result["success"]:
                all_events.extend(result["events"])
        
        # If we have events to process, calculate overlaps and same-day turnovers
        if all_events:
            logging.info(f"Calculating flags for {len(all_events)} events...")
            all_events = calculate_flags(all_events, url_to_prop_map)
            
            # Update the events in feed_results with calculated flags
            events_by_url = defaultdict(list)
            for event in all_events:
                events_by_url[event["ics_url"]].append(event)
            
            for url, events in events_by_url.items():
                if url in feed_results and feed_results[url]["success"]:
                    feed_results[url]["events"] = events
        
        # 6. Load existing records ONCE with all needed fields
        existing_records = get_records_by_uid_feed(reservations_table)
        
        # 7. Process all feeds (batch collectors for updates)
        create_collector = BatchCollector(reservations_table, batch_size=10, op="create")
        update_collector = BatchCollector(reservations_table, batch_size=10, op="update")
        overall_stats = {}
        
        # Process each feed
        for url, result in feed_results.items():
            if result["success"]:
                stats = process_ics_feed(
                    url=url, 
                    events=result["events"],
                    existing_records=existing_records,
                    url_to_prop=url_to_prop_map,
                    table=reservations_table, 
                    create_batch=create_collector,
                    update_batch=update_collector
                )
                # Add property ID for reporting
                stats["property_id"] = result["property_id"]
                overall_stats[url] = stats
        
        # Make sure all remaining batches are processed
        create_count = create_collector.done()
        update_count = update_collector.done()
        logging.info(f"Processed {create_count} creations and {update_count} updates")
        
        # 8. Run post-processing
        update_property_id(reservations_table, ics_feeds_table)
        
        # 9. Generate report
        generate_report(overall_stats, id_to_name)
        
        # Log final completion message
        total_new = sum(stats.get("New", 0) for stats in overall_stats.values())
        total_modified = sum(stats.get("Modified", 0) for stats in overall_stats.values())
        total_unchanged = sum(stats.get("Unchanged", 0) for stats in overall_stats.values())
        total_removed = sum(stats.get("Removed", 0) for stats in overall_stats.values())
        
        logging.info(f"ICS Sync complete * created {total_new} * modified {total_modified} * "
                    f"unchanged {total_unchanged} * removed {total_removed}")
        
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)

def main():
    # Run the async main
    asyncio.run(main_async())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception in main execution: {e}", exc_info=True)