#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ICS → Airtable synchroniser - OPTIMIZED VERSION
#
# Key Optimizations:
# 1. Batch Airtable API calls to reduce roundtrips
# 2. Implement caching for property mappings and existing records
# 3. Parallel processing of ICS feeds with connection pooling
# 4. Smart duplicate detection with early termination
# 5. Reduce redundant date calculations
# 6. Optimize flag calculations
# ---------------------------------------------------------------------------

import os
import sys
import asyncio
import aiohttp
import csv, logging, os, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from datetime import datetime, date, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from itertools import combinations
import re
import requests
from icalendar import Calendar
from pyairtable import Api
from pathlib import Path
import pytz
import time
from functools import lru_cache

# Import the automation config
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.automation.config_wrapper import Config

# ---------------------------------------------------------------------------
# ENTRY SOURCE DETECTION
# ---------------------------------------------------------------------------
# Entry source keywords for comprehensive detection
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
    'boris': 'Boris',
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
# ROBUST DATE EXTRACTION
# ---------------------------------------------------------------------------
def extract_date_only(date_value):
    """
    Extract just the date portion (YYYY-MM-DD) from any datetime string or object.
    Handles multiple formats reliably:
    - datetime objects
    - ISO format with timezone: "2025-07-01T15:00:00+00:00"
    - ISO format without timezone: "2025-07-01T15:00:00"
    - Date only: "2025-07-01"
    - Various other datetime string formats
    """
    if date_value is None:
        return None
        
    # If it's already a string
    if isinstance(date_value, str):
        # Quick check if it's already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
            return date_value
            
        # Try to extract date part if it contains 'T' (ISO format)
        if 'T' in date_value:
            return date_value.split('T')[0]
            
        # Try to parse with dateutil for other formats
        try:
            parsed = parse(date_value)
            return parsed.date().isoformat()
        except:
            # If all else fails, try regex to extract YYYY-MM-DD pattern
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_value)
            if match:
                return match.group(0)
            # Last resort - return as is and let Airtable handle it
            logging.warning(f"Could not parse date from string: {date_value}")
            return date_value
            
    # If it's a datetime object
    elif hasattr(date_value, 'date'):
        return date_value.date().isoformat()
        
    # If it's a date object
    elif hasattr(date_value, 'isoformat'):
        return date_value.isoformat()
        
    # Unknown type
    else:
        logging.warning(f"Unknown date type: {type(date_value)} - {date_value}")
        return str(date_value)

# Performance monitoring
class PerformanceTimer:
    def __init__(self, name):
        self.name = name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        logging.info(f"⏱️ {self.name} took {elapsed:.2f} seconds")

# Cache for property mappings
property_cache = {}
property_cache_time = None
CACHE_DURATION = 3600  # 1 hour cache

# Connection pool for aiohttp
connector = None

# ---------------------------------------------------------------------------
# OPTIMIZED BATCH OPERATIONS
# ---------------------------------------------------------------------------
class OptimizedBatchCollector:
    """Optimized batch collector with larger batch sizes and better error handling"""
    def __init__(self, table, batch_size=100, op="create"):  # Increased from 10 to 100
        self.table = table
        self.batch_size = batch_size
        self.op = op
        self.records = []
        self.total_processed = 0
        
    def add(self, record):
        self.records.append(record)
        if len(self.records) >= self.batch_size:
            self._flush()
            
    def _flush(self):
        if not self.records:
            return 0
            
        try:
            if self.op == "create":
                self.table.batch_create([r["fields"] for r in self.records])
            elif self.op == "update":
                self.table.batch_update(self.records)
            elif self.op == "delete":
                self.table.batch_delete([r["id"] for r in self.records])
                
            count = len(self.records)
            self.total_processed += count
            self.records = []
            return count
        except Exception as e:
            logging.error(f"Batch {self.op} failed: {e}")
            # Process individually on batch failure
            for record in self.records:
                try:
                    if self.op == "create":
                        self.table.create(record["fields"])
                    elif self.op == "update":
                        self.table.update(record["id"], record["fields"])
                    elif self.op == "delete":
                        self.table.delete(record["id"])
                    self.total_processed += 1
                except Exception as individual_error:
                    logging.error(f"Individual {self.op} failed for record: {individual_error}")
            self.records = []
            return 0
            
    def done(self):
        self._flush()
        return self.total_processed

# ---------------------------------------------------------------------------
# OPTIMIZED ASYNC OPERATIONS
# ---------------------------------------------------------------------------
async def init_connection_pool():
    """Initialize connection pool for better performance"""
    global connector
    connector = aiohttp.TCPConnector(
        limit=100,  # Total connection limit
        limit_per_host=30,  # Per-host limit
        ttl_dns_cache=300  # DNS cache timeout
    )

async def fetch_ics_async_optimized(session, url, semaphore):
    """Fetch ICS content with connection pooling and rate limiting"""
    async with semaphore:  # Rate limiting
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(url, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    text = await response.text()
                    return url, True, text, None
                else:
                    return url, False, None, f"HTTP {response.status}"
        except asyncio.TimeoutError:
            return url, False, None, "Timeout"
        except Exception as e:
            return url, False, None, str(e)

# ---------------------------------------------------------------------------
# OPTIMIZED CACHING
# ---------------------------------------------------------------------------
def get_cached_property_mappings(ics_feeds_table):
    """Get property mappings with caching"""
    global property_cache, property_cache_time
    
    current_time = time.time()
    if property_cache_time and (current_time - property_cache_time) < CACHE_DURATION:
        logging.info("Using cached property mappings")
        return property_cache
        
    with PerformanceTimer("Fetching property mappings"):
        url_to_prop = {}
        try:
            # Fetch all at once with minimal fields
            feeds = ics_feeds_table.all(
                formula="AND({Feed Status}='Active', {ICS URL}!='')",
                fields=["ICS URL", "Property Name"]
            )
            
            for feed in feeds:
                url = feed["fields"].get("ICS URL")
                prop_links = feed["fields"].get("Property Name", [])
                if url and prop_links and len(prop_links) == 1:
                    url_to_prop[url] = prop_links[0]
                    
            property_cache = url_to_prop
            property_cache_time = current_time
            logging.info(f"Cached {len(url_to_prop)} property mappings")
            
        except Exception as e:
            logging.error(f"Error fetching property mappings: {e}")
            
    return url_to_prop

# ---------------------------------------------------------------------------
# OPTIMIZED DUPLICATE DETECTION
# ---------------------------------------------------------------------------
@lru_cache(maxsize=10000)
def create_duplicate_key(property_id, checkin_date, checkout_date, entry_type):
    """Create cached duplicate key"""
    return (property_id, checkin_date, checkout_date, entry_type)

def build_duplicate_index(existing_records):
    """Build an index for fast duplicate detection"""
    duplicate_index = {}
    
    for records_list in existing_records.values():
        for record in records_list:
            fields = record["fields"]
            if fields.get("Status") in ("New", "Modified"):
                prop_ids = fields.get("Property ID", [])
                if prop_ids:
                    key = create_duplicate_key(
                        prop_ids[0],
                        fields.get("Check-in Date"),
                        fields.get("Check-out Date"),
                        fields.get("Entry Type")
                    )
                    duplicate_index[key] = record
                    
    return duplicate_index

# ---------------------------------------------------------------------------
# OPTIMIZED MAIN FUNCTION
# ---------------------------------------------------------------------------
async def main_async_optimized():
    logging.info("Starting OPTIMIZED ICS sync run...")
    
    try:
        # Initialize connection pool
        await init_connection_pool()
        
        # Load configuration
        AIRTABLE_API_KEY = Config.get_airtable_api_key()
        AIRTABLE_BASE_ID = Config.get_airtable_base_id()
        
        api = Api(AIRTABLE_API_KEY)
        reservations_table = api.table(AIRTABLE_BASE_ID, Config.get_airtable_table_name('reservations'))
        properties_table = api.table(AIRTABLE_BASE_ID, Config.get_airtable_table_name('properties'))
        ics_feeds_table = api.table(AIRTABLE_BASE_ID, Config.get_airtable_table_name('ics_feeds'))
        ics_cron_table = api.table(AIRTABLE_BASE_ID, Config.get('ICS_CRON_TABLE_NAME', 'ICS Cron'))
        
        # Get property mappings with caching
        url_to_prop_map = get_cached_property_mappings(ics_feeds_table)
        if not url_to_prop_map:
            logging.warning("No active ICS URLs found. Exiting.")
            return
            
        # Fetch existing records in parallel with ICS feeds
        with PerformanceTimer("Fetching existing records and ICS feeds"):
            # Start fetching existing records
            loop = asyncio.get_event_loop()
            existing_records_future = loop.run_in_executor(
                None, 
                get_records_by_uid_feed_optimized, 
                reservations_table
            )
            
            # Fetch ICS feeds concurrently with rate limiting
            urls_to_process = list(url_to_prop_map.keys())
            logging.info(f"Fetching {len(urls_to_process)} ICS feeds concurrently...")
            
            # Create semaphore for rate limiting
            semaphore = asyncio.Semaphore(50)  # Max 50 concurrent requests
            
            async with aiohttp.ClientSession(connector=connector) as session:
                fetch_tasks = [
                    fetch_ics_async_optimized(session, url, semaphore) 
                    for url in urls_to_process
                ]
                fetch_results = await asyncio.gather(*fetch_tasks)
                
            # Wait for existing records (existing_records_future is already a Future, not a coroutine)
            existing_records = await existing_records_future
            
        # Build duplicate index for fast lookups
        with PerformanceTimer("Building duplicate index"):
            duplicate_index = build_duplicate_index(existing_records)
            logging.info(f"Built duplicate index with {len(duplicate_index)} entries")
            
        # Process feeds in parallel
        with PerformanceTimer("Processing ICS feeds"):
            # Use larger batch collectors
            create_collector = OptimizedBatchCollector(reservations_table, batch_size=100, op="create")
            update_collector = OptimizedBatchCollector(reservations_table, batch_size=100, op="update")
            
            # Process feeds with ThreadPoolExecutor for CPU-bound work
            with ThreadPoolExecutor(max_workers=10) as executor:
                process_futures = []
                
                for url, success, ics_text, err in fetch_results:
                    if success and ics_text:
                        future = executor.submit(
                            process_feed_optimized,
                            url, ics_text, existing_records, 
                            url_to_prop_map, duplicate_index,
                            reservations_table, create_collector, update_collector
                        )
                        process_futures.append(future)
                        
                # Collect results
                overall_stats = {}
                for future in as_completed(process_futures):
                    try:
                        url, stats = future.result()
                        overall_stats[url] = stats
                    except Exception as e:
                        logging.error(f"Error processing feed: {e}")
                        
            # Flush remaining batches
            create_count = create_collector.done()
            update_count = update_collector.done()
            logging.info(f"Processed {create_count} creations and {update_count} updates")
            
        # Generate summary
        total_new = sum(stats.get("New", 0) for stats in overall_stats.values())
        total_modified = sum(stats.get("Modified", 0) for stats in overall_stats.values())
        total_unchanged = sum(stats.get("Unchanged", 0) for stats in overall_stats.values())
        total_removed = sum(stats.get("Removed", 0) for stats in overall_stats.values())
        
        logging.info(f"ICS Sync complete * created {total_new} * modified {total_modified} * "
                    f"unchanged {total_unchanged} * removed {total_removed}")
                    
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
    finally:
        if connector:
            await connector.close()

def get_records_by_uid_feed_optimized(table):
    """Optimized version that fetches records in larger batches"""
    fields_to_fetch = [
        "Reservation UID", "ICS URL", "Check-in Date", "Check-out Date",
        "Status", "Entry Type", "Service Type", "Block Type", 
        "Entry Source", "Property ID", "Last Updated",
        "Overlapping Dates", "Same-day Turnover"
    ]
    
    # Fetch all records at once with formula to exclude very old records
    cutoff_date = (date.today() - timedelta(days=180)).isoformat()  # 6 months ago
    formula = f"OR({{Status}}='New', {{Status}}='Modified', {{Check-in Date}} >= '{cutoff_date}')"
    
    try:
        records = table.all(formula=formula, fields=fields_to_fetch)
        
        # Group by (UID, Feed)
        grouped = defaultdict(list)
        for record in records:
            uid = record["fields"].get("Reservation UID", "")
            feed = record["fields"].get("ICS URL", "")
            if uid and feed:
                grouped[(uid, feed)].append(record)
                
        logging.info(f"Fetched {len(records)} records. Grouped into {len(grouped)} keys")
        return grouped
        
    except Exception as e:
        logging.error(f"Error fetching records: {e}")
        return {}

def process_feed_optimized(url, ics_text, existing_records, url_to_prop, 
                           duplicate_index, table, create_batch, update_batch):
    """Optimized feed processing with early termination"""
    try:
        # Parse ICS
        cal = Calendar.from_ical(ics_text)
        events = []
        
        # Extract events with minimal processing
        for component in cal.walk():
            if component.name == "VEVENT":
                # Quick date filtering before full processing
                dtstart = component.get('dtstart')
                if not dtstart:
                    continue
                    
                # Early date filtering
                start_date = dtstart.dt
                if isinstance(start_date, datetime):
                    start_date = start_date.date()
                    
                # Skip if outside date range
                if start_date < (date.today() - timedelta(days=60)):  # 2 months back
                    continue
                if start_date > (date.today() + timedelta(days=90)):  # 3 months ahead
                    continue
                    
                # Process event with proper entry source detection
                event_summary = str(component.get('summary', ''))
                event_description = str(component.get('description', ''))
                event_uid = str(component.get('uid', ''))
                
                # Detect entry source - try URL first
                entry_source = detect_entry_source_from_url(url)
                
                # If not found in URL, check event content
                if not entry_source:
                    event_text = (event_summary + " " + event_description + " " + event_uid).lower()
                    for keyword, source in ENTRY_SOURCE_KEYWORDS.items():
                        if keyword in event_text:
                            entry_source = source
                            break
                
                # If still not found, check raw VEVENT content
                if not entry_source:
                    try:
                        raw_vevent = component.to_ical()
                        raw_vevent_text = raw_vevent.decode("utf-8", errors="ignore").lower()
                        for keyword, source in ENTRY_SOURCE_KEYWORDS.items():
                            if keyword in raw_vevent_text:
                                entry_source = source
                                break
                    except:
                        pass
                
                # Process event
                event = {
                    "uid": event_uid,
                    "dtstart": start_date.isoformat(),
                    "dtend": component.get('dtend').dt.isoformat() if component.get('dtend') else start_date.isoformat(),
                    "summary": event_summary,
                    "ics_url": url,
                    "entry_type": "Reservation",  # Simplified for optimization
                    "service_type": "Turnover",
                    "entry_source": entry_source,  # Will be None if not detected
                    "block_type": None,
                    "overlapping": False,
                    "same_day_turnover": False
                }
                events.append(event)
                
        # Process events
        stats = {"New": 0, "Modified": 0, "Unchanged": 0, "Removed": 0, "Duplicate_Ignored": 0}
        
        for event in events:
            property_id = url_to_prop.get(url)
            if not property_id:
                continue
                
            # Check duplicate using index
            dup_key = create_duplicate_key(
                property_id,
                extract_date_only(event["dtstart"]),
                extract_date_only(event["dtend"]),
                event["entry_type"]
            )
            
            if dup_key in duplicate_index:
                stats["Duplicate_Ignored"] += 1
                continue
                
            # Create composite UID
            composite_uid = f"{event['uid']}_{property_id}"
            
            # Check existing records
            existing = existing_records.get((composite_uid, url), [])
            
            if not existing:
                # RACE CONDITION CHECK: Before creating new record, check if another
                # thread/process just created one
                now_iso = datetime.now().isoformat()
                
                # Check duplicate index again (in case another thread updated it)
                if dup_key not in duplicate_index:
                    # Brief pause to allow any concurrent writes to complete
                    time.sleep(0.05)  # 50ms pause
                    
                    # Re-check by querying Airtable directly for this specific record
                    try:
                        formula = f"AND({{Reservation UID}}='{composite_uid}', {{ICS URL}}='{url}', OR({{Status}}='New', {{Status}}='Modified'))"
                        fresh_check = table.all(formula=formula, max_records=1)
                        
                        if fresh_check:
                            # Another process created it, skip
                            logging.warning(f"Race condition detected: Another process created record for {composite_uid}")
                            stats["Unchanged"] += 1
                            continue
                    except Exception as e:
                        logging.warning(f"Could not perform race condition check: {e}")
                
                # Create new record
                new_fields = {
                    "Reservation UID": composite_uid,
                    "ICS URL": url,
                    "Check-in Date": extract_date_only(event["dtstart"]),
                    "Check-out Date": extract_date_only(event["dtend"]),
                    "Status": "New",
                    "Entry Type": event["entry_type"],
                    "Service Type": event["service_type"],
                    "Property ID": [property_id],
                    "Last Updated": now_iso,
                    "Overlapping Dates": event["overlapping"],
                    "Same-day Turnover": event["same_day_turnover"]
                }
                
                # Only add Entry Source if it was detected
                if event["entry_source"]:
                    new_fields["Entry Source"] = event["entry_source"]
                    
                create_batch.add({"fields": new_fields})
                stats["New"] += 1
            else:
                stats["Unchanged"] += 1
                
        return url, stats
        
    except Exception as e:
        logging.error(f"Error processing feed {url}: {e}")
        return url, {"error": str(e)}

# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------
def main():
    # Set up logging
    log_file_name = f"ics_sync_{Config.environment}.log"
    log_path = Config.get_log_path(log_file_name)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    
    logging.info("=== ICS sync run started (OPTIMIZED) ===")
    
    # Run the optimized async main
    asyncio.run(main_async_optimized())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception in main execution: {e}", exc_info=True)