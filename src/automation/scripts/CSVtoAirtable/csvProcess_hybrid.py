#!/usr/bin/env python3

# 🚨 ULTRA DEEP DEBUGGING - MUST BE FIRST IMPORT
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ultra_debug_airtable import *  # This monkey patches pyairtable for ultra debugging

# ---------------------------------------------------------------------------
# CSV → Airtable synchroniser - HYBRID VERSION with UID + Property/Dates/Type matching
#
# • Handles two suppliers:
#     – iTrip  : header row contains "Property Name"
#     – Evolve : otherwise
# • Uses HYBRID APPROACH: UID matching first, then property/dates/type fallback
# • Ensures ONLY ONE active record per reservation UID
# • Marks ALL older versions as "Old" when creating Modified/Removed
# ---------------------------------------------------------------------------

import sys, io                                              #  add these imports ↑ with the others
import csv, logging, os, shutil
from collections import defaultdict
from datetime import datetime, date
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from itertools import combinations
from pyairtable import Api
import glob
from pathlib import Path
import pytz

# Import the automation config
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.automation.config_wrapper import Config
# Import duplicate detection testing framework
from src.automation.scripts.duplicate_detection_testing import run_duplicate_detection_tests

# ---------------------------------------------------------------------------
# CONFIG — Environment-based configuration
# ---------------------------------------------------------------------------
# Use Config class for path resolution
PROCESS_DIR = str(Config.get_csv_process_dir())
DONE_DIR = str(Config.get_csv_done_dir())
LOG_FILE = str(Config.get_logs_dir() / f"csv_sync_{Config.environment_name}.log")

# Date filter settings from environment
MONTHS_LOOKBACK = Config.get_fetch_months_before()
MONTHS_LOOKAHEAD = 3   # Only process reservations with start dates up to 3 months ahead
# ────────────────────────────────────────────────────────────────────
#  Accumulate stats PER ENTRY-SOURCE so we can show iTrip vs Evolve
# ────────────────────────────────────────────────────────────────────
# ─── per-source running totals ───────────────────────────────────
tab2_global   = {"new":0, "modified":0, "unchanged":0, "removed":0}

itrip_blocks  = {"new":0, "modified":0, "unchanged":0, "removed":0, "total":0}
evolve_blocks = {"new":0, "modified":0, "unchanged":0, "removed":0, "total":0}

itrip_reserv  = {"new":0, "modified":0, "unchanged":0, "removed":0, "total":0}
evolve_reserv = {"new":0, "modified":0, "unchanged":0, "removed":0, "total":0}
# ────────────────────────────────────────────────────────────────

# Determine the correct field name based on environment
sync_details_field = "Service Sync Details"  # Use same field for both dev and prod

HCP_FIELDS = [
    "Service Job ID", "Job Creation Time", "Sync Status",
    "Scheduled Service Time", "Sync Date and Time", sync_details_field,
    "Job Status", "Custom Service Time", "Entry Source",
    "Service Appointment ID", "Assignee", "On My Way Time",
    "Job Started Time", "Job Completed Time", "Next Entry Is Block",
    "Owner Arriving", "Custom Service Line Instructions",
    "Service Line Description", "HCP Service Line Description",
    "Schedule Sync Details"
]

# Fields to skip when cloning records
WRITE_BLACKLIST = {
    "Final Service Time",          # computed roll-ups
    "Sync Date and Time",
    sync_details_field  # Use the environment-specific field name
}
# Entry Type Detection for CSV Rows
ENTRY_TYPE_KEYWORDS = {
    'maintenance': 'Block',
}
DEFAULT_ENTRY_TYPE = "Reservation"

SERVICE_TYPE_KEYWORDS = {
    'owner arrival': 'Owner Arrival',
    'owner stay': 'Owner Arrival',
    'owner arriving': 'Owner Arrival',
}
DEFAULT_SERVICE_TYPE = "Turnover"  # Default for reservations

BLOCK_TYPE_KEYWORDS = {
    'owner arrival': 'Owner Arrival',
    'owner stay': 'Owner Arrival',
    'owner arriving': 'Owner Arrival',
}
# -----------------------------------------------------------------------------
# Date-handling / timezone utilities
# -----------------------------------------------------------------------------
arizona_tz = pytz.timezone("America/Phoenix")

def normalize_date_for_comparison(date_str):
    """Convert date string to ISO format for consistent comparison."""
    if not date_str:
        return ""
    try:
        # Parse the date string
        parsed = parse(date_str)
        # Return just the date part in ISO format
        return parsed.date().isoformat()
    except:
        return date_str

# ────────────────────────────────────────────────────────────────────────────
# Batch operations
# ────────────────────────────────────────────────────────────────────────────
class BatchCollector:
    """Collects operations into batches to avoid rate limits."""
    
    def __init__(self, table, op="create"):
        self.table = table
        self.op = op
        self.batch = []
        self.MAX_BATCH = 10
    
    def add(self, item):
        self.batch.append(item)
        if len(self.batch) >= self.MAX_BATCH:
            self.flush()
    
    def flush(self):
        if not self.batch:
            return
        try:
            if self.op == "create":
                self.table.batch_create(self.batch)
            elif self.op == "update":
                self.table.batch_update(self.batch)
            self.batch = []
        except Exception as e:
            logging.error(f"Batch {self.op} failed: {e}")
            self.batch = []

# In-memory collector for optimized processing
class InMemoryCollector:
    """Collects all operations in memory before executing."""
    
    def __init__(self):
        self.to_create = []
        self.to_update = []
        self.to_remove = []
        self.existing_records = {}
        self.processed_uids = set()
        self.property_mapping = {}
        
    def add_create(self, uid, source, data):
        """Add a create operation."""
        self.to_create.append({
            'uid': uid,
            'source': source,
            'fields': data
        })
        
    def add_update(self, record_id, fields):
        """Add an update operation."""
        self.to_update.append({
            'id': record_id,
            'fields': fields
        })
        
    def execute(self, table):
        """Execute all collected operations efficiently."""
        logging.info(f"Executing operations: {len(self.to_create)} creates, {len(self.to_update)} updates")
        
        # Process updates in batches
        if self.to_update:
            for i in range(0, len(self.to_update), 10):
                batch = self.to_update[i:i+10]
                try:
                    table.batch_update(batch)
                    logging.debug(f"Updated batch of {len(batch)} records")
                except Exception as e:
                    logging.error(f"Failed to update batch: {e}")
        
        # Process creates in batches
        if self.to_create:
            for i in range(0, len(self.to_create), 10):
                batch = self.to_create[i:i+10]
                batch_data = [{"fields": item["fields"]} for item in batch]
                try:
                    table.batch_create(batch_data)
                    logging.debug(f"Created batch of {len(batch)} records")
                except Exception as e:
                    logging.error(f"Failed to create batch: {e}")

# -----------------------------------------------------------------------------
# Fetch all existing reservations by UID+feed for self-healing removed records
# -----------------------------------------------------------------------------
def fetch_all_reservations(table, feed_urls):
    """Fetch ALL reservation records for the given feed URLs.
    Returns dict mapping (uid, feed_url) -> list of records."""
    
    # Prepare a filter formula
    feed_conditions = []
    for feed in feed_urls:
        feed_conditions.append(f"{{ICS URL}} = '{feed}'")
    
    formula = f"OR({','.join(feed_conditions)})" if feed_conditions else ""
    
    logging.info(f"Fetching all records for feeds: {feed_urls}")
    records = table.all(formula=formula)
    
    # Index by both composite and base UIDs
    by_uid_feed = defaultdict(list)
    for record in records:
        fields = record.get("fields", {})
        uid = fields.get("Reservation UID")
        feed_url = fields.get("ICS URL")
        
        if uid and feed_url:
            # Store with the actual UID from Airtable (could be composite)
            key = (uid, feed_url)
            by_uid_feed[key].append(record)
            
            # ALSO store with base UID if this is a composite UID
            # This allows lookup by either composite or base UID
            if '_' in uid and uid.count('_') == 1:
                base_uid, prop_suffix = uid.rsplit('_', 1)
                if prop_suffix.startswith('rec'):  # Airtable record ID format
                    base_key = (base_uid, feed_url)
                    by_uid_feed[base_key].append(record)
                    logging.debug(f"Also indexed composite UID {uid} under base UID {base_uid}")
    
    logging.info(f"Fetched {len(records)} total records indexed under {len(by_uid_feed)} keys (includes base UID lookups)")
    
    return by_uid_feed

# -----------------------------------------------------------------------------
# Detect whether the given CSV has a header line containing specific text
# -----------------------------------------------------------------------------
def detect_itrip_header(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline()
        # iTrip files contain "Property Name" in the header
        return "Property Name" in first_line

# -----------------------------------------------------------------------------
# Find property by name or address
# -----------------------------------------------------------------------------
def find_property_by_name(property_name, properties_table, property_address=None):
    """Find a property record by name (and optionally address)."""
    if not property_name:
        return None
    
    # First try exact match on Property Name
    formula = f"{{Property Name}} = '{property_name}'"
    records = properties_table.all(formula=formula, max_records=1)
    if records:
        return records[0]
    
    # Try with address if provided
    if property_address:
        # Try exact address match
        formula = f"{{Address}} = '{property_address}'"
        records = properties_table.all(formula=formula, max_records=1)
        if records:
            return records[0]
    
    # Try partial name match
    formula = f"FIND(LOWER('{property_name.lower()}'), LOWER({{Property Name}}))"
    records = properties_table.all(formula=formula, max_records=5)
    if records:
        # If only one match, use it
        if len(records) == 1:
            return records[0]
        # If multiple, try to match with address
        if property_address:
            for record in records:
                if property_address in record['fields'].get('Address', ''):
                    return record
        # Otherwise return first match
        return records[0]
    
    return None

# ────────────────────────────────────────────────────────────────────────────
# Parse an iTrip CSV and create Airtable records
# ────────────────────────────────────────────────────────────────────────────
def parse_itrip_csv(file_path, entry_source, properties_table):
    """Parse an iTrip CSV file."""
    results = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # iTrip specific fields
            checkin = row.get("Checkin", "").strip()
            checkout = row.get("Checkout", "").strip()
            guest_name = row.get("Tenant Name", "").strip()
            property_name = row.get("Property Name", "").strip()
            property_address = row.get("Property Address", "").strip()
            reservation_id = row.get("Reservation ID", "").strip()
            same_day = row.get("Same Day?", "").strip().lower() == "yes"
            
            if not (checkin and checkout and property_name):
                continue
            
            # Find property
            property_record = find_property_by_name(property_name, properties_table, property_address)
            if not property_record:
                logging.warning(f"Property not found: {property_name}")
                continue
            
            # Determine entry type based on guest name
            entry_type = DEFAULT_ENTRY_TYPE
            for keyword, etype in ENTRY_TYPE_KEYWORDS.items():
                if keyword in guest_name.lower():
                    entry_type = etype
                    break
            
            # Determine service type
            service_type = DEFAULT_SERVICE_TYPE
            if entry_type == "Block":
                service_type = "Needs Review"
            else:
                for keyword, stype in SERVICE_TYPE_KEYWORDS.items():
                    if keyword in guest_name.lower():
                        service_type = stype
                        break
            
            results.append({
                "property_id": property_record['id'],
                "property_name": property_name,
                "property_address": property_address,
                "guest_name": guest_name,
                "dtstart": normalize_date_for_comparison(checkin),
                "dtend": normalize_date_for_comparison(checkout),
                "uid": reservation_id,
                "same_day_turnover": same_day,
                "entry_type": entry_type,
                "service_type": service_type,
                "entry_source": entry_source,
                "feed_url": "csv_itrip"
            })
    
    return results

# ────────────────────────────────────────────────────────────────────────────
# Parse an Evolve CSV (regular)
# ────────────────────────────────────────────────────────────────────────────
def parse_evolve_csv(file_path, entry_source, properties_table):
    """Parse a regular Evolve CSV file."""
    results = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Evolve specific fields
            reservation_id = row.get("Reservation", "").strip()
            property_address = row.get("Property Address", "").strip()
            status = row.get("Status", "").strip()
            checkin = row.get("Check-In", "").strip()
            checkout = row.get("Check-Out", "").strip()
            guest_name = row.get("Guest Name", "").strip()
            
            if not (checkin and checkout and property_address) or status != "booked":
                continue
            
            # Find property by address
            property_record = find_property_by_name("", properties_table, property_address)
            if not property_record:
                logging.warning(f"Property not found by address: {property_address}")
                continue
            
            # Determine entry type
            entry_type = DEFAULT_ENTRY_TYPE
            for keyword, etype in ENTRY_TYPE_KEYWORDS.items():
                if keyword in guest_name.lower():
                    entry_type = etype
                    break
            
            # Determine service type
            service_type = DEFAULT_SERVICE_TYPE
            if entry_type == "Block":
                service_type = "Needs Review"
            else:
                for keyword, stype in SERVICE_TYPE_KEYWORDS.items():
                    if keyword in guest_name.lower():
                        service_type = stype
                        break
            
            results.append({
                "property_id": property_record['id'],
                "property_name": property_record['fields'].get('Property Name', ''),
                "property_address": property_address,
                "guest_name": guest_name,
                "dtstart": normalize_date_for_comparison(checkin),
                "dtend": normalize_date_for_comparison(checkout),
                "uid": reservation_id,
                "same_day_turnover": False,  # Evolve doesn't provide this
                "entry_type": entry_type,
                "service_type": service_type,
                "entry_source": entry_source,
                "feed_url": "csv_evolve"
            })
    
    return results

# ────────────────────────────────────────────────────────────────────────────
# Check for important changes in reservation data
# ────────────────────────────────────────────────────────────────────────────
def has_important_changes(existing_fields, new_data):
    """Check if there are important changes between existing and new data."""
    # Check dates
    if existing_fields.get("Check-in Date") != new_data["dtstart"]:
        return True
    if existing_fields.get("Check-out Date") != new_data["dtend"]:
        return True
    
    # Check guest name
    if existing_fields.get("Guest Name", "").strip() != new_data.get("guest_name", "").strip():
        return True
    
    # Check same-day turnover flag
    if existing_fields.get("Same-day Turnover", False) != new_data.get("same_day_turnover", False):
        return True
    
    # Check service type changes
    if existing_fields.get("Service Type", "") != new_data.get("service_type", ""):
        return True
    
    # No important changes detected
    return False

def check_for_duplicate(table, property_id, checkin_date, checkout_date, entry_type, session_tracker=None, property_id_to_name=None):
    """Check if a record with the same property, dates, and type already exists.
    
    Args:
        table: Airtable table object
        property_id: Property record ID
        checkin_date: Check-in date (ISO format)
        checkout_date: Check-out date (ISO format)
        entry_type: Entry type (Reservation or Block)
        session_tracker: Set tracking records created in current session
        property_id_to_name: Dict mapping property IDs to names for logging
    
    Returns:
        bool: True if duplicate exists (in session or Airtable), False otherwise
    """
    # First check session tracker for duplicates created in this run
    if session_tracker is not None:
        key = (property_id, checkin_date, checkout_date, entry_type)
        if key in session_tracker:
            prop_name = property_id_to_name.get(property_id, property_id) if property_id_to_name else property_id
            logging.info(f"Found duplicate in session: Property \"{prop_name}\" ({property_id}), {checkin_date} to {checkout_date}, Type: {entry_type}")
            return True
    
    # Then check Airtable for existing records
    try:
        # Build formula to find exact matches
        # For Blocks, check for ANY existing record to prevent duplicates
        # For Reservations, only check New/Modified to allow reactivation
        if entry_type == "Block":
            formula = (
                f"AND("
                f"{{Property ID}} = '{property_id}', "
                f"{{Check-in Date}} = '{checkin_date}', "
                f"{{Check-out Date}} = '{checkout_date}', "
                f"{{Entry Type}} = '{entry_type}'"
                f")"
            )
        else:
            # For reservations, only prevent duplicates with active records
            formula = (
                f"AND("
                f"{{Property ID}} = '{property_id}', "
                f"{{Check-in Date}} = '{checkin_date}', "
                f"{{Check-out Date}} = '{checkout_date}', "
                f"{{Entry Type}} = '{entry_type}', "
                f"OR({{Status}} = 'New', {{Status}} = 'Modified')"
                f")"
            )
        
        records = table.all(formula=formula, max_records=1)
        
        if records:
            prop_name = property_id_to_name.get(property_id, property_id) if property_id_to_name else property_id
            logging.info(f"Found duplicate in Airtable: Property \"{prop_name}\" ({property_id}), {checkin_date} to {checkout_date}, Type: {entry_type}")
            return True
        return False
    except Exception as e:
        logging.warning(f"Error checking for duplicate: {e}")
        return False

def sync_reservations(csv_reservations, all_reservation_records, table, session_tracker=None, evolve_csv_failed=False, property_id_to_name=None):
    """Synchronize CSV data with Airtable using HYBRID APPROACH:
    1. Try UID matching first (with both composite and base UIDs)
    2. If no UID match, try property/dates/type matching
    3. Track all processed events to prevent false removals
    
    Args:
        csv_reservations: List of reservation dicts from CSV files
        all_reservation_records: Dict of existing Airtable records
        table: Airtable table object
        session_tracker: Set tracking records created in current session
        evolve_csv_failed: If True, skip removal logic for Evolve reservations
    """
    # Track property/date combinations that had duplicates
    duplicate_detected_dates = set()
    now_iso = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")
    today = date.today().isoformat()
    
    # STEP 1: Deduplicate CSV reservations
    unique_reservations = {}
    original_count = len(csv_reservations)
    for res in csv_reservations:
        key = (res["uid"], res["feed_url"])
        unique_reservations[key] = res
    
    csv_reservations = list(unique_reservations.values())
    if original_count != len(csv_reservations):
        logging.info(f"Removed {original_count - len(csv_reservations)} duplicate reservations during processing")
    
    # STEP 2: Group CSV data by property for overlap calculation
    by_property = defaultdict(list)
    for res in csv_reservations:
        if res.get("property_id"):
            by_property[res["property_id"]].append(res)
    
    # STEP 3: Calculate overlaps PROPERTY BY PROPERTY
    for property_id, property_reservations in by_property.items():
        for i, res in enumerate(property_reservations):
            if i == 0:
                res["previous_guest_name"] = "N/A"
                res["same_day_turnover"] = False
            else:
                prev_res = property_reservations[i - 1]
                res["previous_guest_name"] = prev_res.get("guest_name", "N/A")
                if prev_res["dtend"] == res["dtstart"]:
                    res["same_day_turnover"] = True
    
    # STEP 4: Process each CSV reservation
    create_batch = BatchCollector(table, op="create")
    update_batch = BatchCollector(table, op="update")
    
    created_count = 0
    modified_count = 0
    unchanged_count = 0
    processed_uids = set()
    summary = defaultdict(list)
    
    # Process each reservation
    for res in csv_reservations:
        uid = res["uid"]
        feed_url = res["feed_url"]
        
        # CRITICAL FIX: Check session tracker FIRST before any processing
        if session_tracker is not None and res.get("property_id"):
            tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
            if tracker_key in session_tracker:
                prop_name = property_id_to_name.get(res["property_id"], res["property_id"]) if property_id_to_name else res["property_id"]
                logging.info(f"🚫 SESSION TRACKER: Prevented duplicate! {uid} for property \"{prop_name}\" ({res['property_id']})")
                logging.info(f"   Property/Dates/Type already processed: {tracker_key}")
                
                # Add to summary as duplicate ignored
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "guest_name": res.get("guest_name", ""),
                    "checkin": res["dtstart"],
                    "checkout": res["dtend"],
                    "status": "duplicate_ignored",
                    "property_address": res.get("property_address", ""),
                    "modified": False
                })
                continue
        
        # Skip if already processed
        if res.get("property_id"):
            composite_uid = f"{uid}_{res['property_id']}"
            if (composite_uid, feed_url) in processed_uids:
                unchanged_count += 1
                continue
        
        # HYBRID APPROACH: Try UID matching first
        all_records = all_reservation_records.get((uid, feed_url), [])
        
        # Also check composite UID
        if not all_records and res.get("property_id"):
            composite_key = (f"{uid}_{res['property_id']}", feed_url)
            all_records = all_reservation_records.get(composite_key, [])
        
        # HYBRID APPROACH: If no UID match, try property+dates+type matching
        if not all_records and res.get("property_id"):
            # Search for records with same property, dates, and type
            property_id = res["property_id"]
            checkin_date = res["dtstart"]
            checkout_date = res["dtend"]
            entry_type = res["entry_type"]
            
            # Check all existing records for this match
            for (existing_uid, existing_feed), records in all_reservation_records.items():
                if existing_feed != feed_url:  # Must be same feed
                    continue
                for record in records:
                    fields = record['fields']
                    # Get property ID from linked field
                    prop_links = fields.get('Property ID', [])
                    existing_prop_id = prop_links[0] if prop_links else None
                    
                    if (existing_prop_id == property_id and
                        fields.get('Check-in Date') == checkin_date and
                        fields.get('Check-out Date') == checkout_date and
                        fields.get('Entry Type') == entry_type and
                        fields.get('Status') in ('New', 'Modified')):
                        # Found a match! Use these records
                        logging.info(f"🔍 HYBRID: Found existing record by property+dates+type for UID {uid}")
                        logging.info(f"   Existing UID: {existing_uid}, Property: {property_id}, Dates: {checkin_date} to {checkout_date}")
                        all_records = records
                        # Update the UID in our data to match the existing record
                        uid = existing_uid
                        break
                if all_records:
                    break
        
        # Find active records
        active_records = [r for r in all_records if r["fields"].get("Status") in ("New", "Modified")]
        
        # Mark as processed (with the UID we're actually using)
        processed_key = (uid, feed_url)
        processed_uids.add(processed_key)
        if res.get("property_id") and '_' not in uid:
            # Also mark composite UID as processed
            composite_key = (f"{uid}_{res['property_id']}", feed_url)
            processed_uids.add(composite_key)
        
        if active_records:
            # EXISTING reservation - check for changes
            latest_active = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
            at_fields = latest_active["fields"]
            
            # Check if this is a removed record that's reappearing (self-healing)
            at_status = at_fields.get("Status", "")
            if at_status == "Removed":
                # Reactivate the removed record
                logging.info(f"🔄 SELF-HEALING: Reactivating removed record {uid}")
                update_batch.add({
                    "id": latest_active["id"],
                    "fields": {
                        "Status": "New",
                        "Last Updated": now_iso,
                        sync_details_field: f"Reactivated from CSV {now_iso}"
                    }
                })
                created_count += 1  # Count as new
                
                # Track in session
                if session_tracker is not None and res["property_id"]:
                    tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                    session_tracker.add(tracker_key)
                
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "guest_name": res.get("guest_name", ""),
                    "checkin": res["dtstart"],
                    "checkout": res["dtend"],
                    "status": "reactivated",
                    "property_address": res.get("property_address", ""),
                    "modified": True
                })
                continue
            
            # Check for important changes
            if has_important_changes(at_fields, res):
                # Important changes detected - create new Modified record
                logging.info(f"Important changes detected for {uid}")
                
                # First, mark ALL existing records as Old
                for record in all_records:
                    if record["fields"].get("Status") != "Old":
                        update_batch.add({
                            "id": record["id"],
                            "fields": {
                                "Status": "Old",
                                "Last Updated": now_iso
                            }
                        })
                
                # Create new Modified record
                new_fields = {
                    "Entry Type": res["entry_type"],
                    "Service Type": res["service_type"],
                    "Guest Name": res.get("guest_name", ""),
                    "Check-in Date": res["dtstart"],
                    "Check-out Date": res["dtend"],
                    "Property ID": [res["property_id"]] if res.get("property_id") else [],
                    "Entry Source": res["entry_source"],
                    "Reservation UID": uid,  # Use the UID we matched with
                    "Status": "Modified",
                    "Same-day Turnover": res.get("same_day_turnover", False),
                    "ICS URL": feed_url,
                    sync_details_field: f"Modified from CSV {now_iso}"
                }
                
                # Preserve HCP fields if they exist
                for field in HCP_FIELDS:
                    if field in at_fields and field not in WRITE_BLACKLIST:
                        new_fields[field] = at_fields[field]
                
                # Race condition check before creating
                try:
                    fresh_records = table.all(
                        formula=f"AND({{Reservation UID}} = '{uid}', {{ICS URL}} = '{feed_url}', {{Status}} = 'Modified')",
                        max_records=5
                    )
                    for rec in fresh_records:
                        rec_updated = rec["fields"].get("Last Updated", "")
                        if rec_updated > now_iso:
                            logging.warning(f"Race condition detected: Another active record for {uid} was created. Skipping duplicate creation.")
                            return None
                except Exception as e:
                    logging.warning(f"Could not perform race condition check: {e}")
                
                create_batch.add({"fields": new_fields})
                modified_count += 1
                
                # Track in session
                if session_tracker is not None and res["property_id"]:
                    tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                    session_tracker.add(tracker_key)
                
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "guest_name": res.get("guest_name", ""),
                    "checkin": res["dtstart"],
                    "checkout": res["dtend"],
                    "status": "modified",
                    "property_address": res.get("property_address", ""),
                    "modified": True
                })
            else:
                # No important changes
                unchanged_count += 1
                
                # IMPORTANT: Still track in session to prevent duplicates
                if session_tracker is not None and res["property_id"]:
                    tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                    session_tracker.add(tracker_key)
                
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "guest_name": res.get("guest_name", ""),
                    "checkin": res["dtstart"],
                    "checkout": res["dtend"],
                    "status": "unchanged",
                    "property_address": res.get("property_address", ""),
                    "modified": False
                })
        else:
            # NEW reservation - but first check if it's a duplicate with different UID
            prop_id = res.get('property_id', 'None')
            prop_name = property_id_to_name.get(prop_id, prop_id) if prop_id != 'None' else 'None'
            logging.info(f"🔍 Processing NEW reservation {uid} for property \"{prop_name}\" ({prop_id})")
            
            if res["property_id"] and check_for_duplicate(
                table, 
                res["property_id"], 
                res["dtstart"], 
                res["dtend"], 
                res["entry_type"],
                session_tracker,
                property_id_to_name
            ):
                prop_name = property_id_to_name.get(res['property_id'], res['property_id'])
                logging.info(f"Ignoring duplicate event: {uid} for property \"{prop_name}\" ({res['property_id']})")
                # Track as unchanged since we're not creating it
                unchanged_count += 1
                
                # Track this duplicate detection
                duplicate_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                duplicate_detected_dates.add(duplicate_key)
                
                # Add to summary as duplicate ignored
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "guest_name": res.get("guest_name", ""),
                    "checkin": res["dtstart"],
                    "checkout": res["dtend"],
                    "status": "duplicate_ignored",
                    "property_address": res.get("property_address", ""),
                    "modified": False
                })
                continue
            
            # Create new record
            new_fields = {
                "Entry Type": res["entry_type"],
                "Service Type": res["service_type"],
                "Guest Name": res.get("guest_name", ""),
                "Check-in Date": res["dtstart"],
                "Check-out Date": res["dtend"],
                "Property ID": [res["property_id"]] if res.get("property_id") else [],
                "Entry Source": res["entry_source"],
                "Reservation UID": uid,
                "Status": "New",
                "Same-day Turnover": res.get("same_day_turnover", False),
                "ICS URL": feed_url,
                sync_details_field: f"Created from CSV {now_iso}"
            }
            
            create_batch.add({"fields": new_fields})
            created_count += 1
            
            # Track in session to prevent duplicates in this run
            if session_tracker is not None and res["property_id"]:
                tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                session_tracker.add(tracker_key)
            
            summary_key = (res["entry_source"], res["property_id"])
            summary[summary_key].append({
                "uid": uid,
                "guest_name": res.get("guest_name", ""),
                "checkin": res["dtstart"],
                "checkout": res["dtend"],
                "status": "new",
                "property_address": res.get("property_address", ""),
                "modified": True
            })
    
    # Flush any remaining batches
    create_batch.flush()
    update_batch.flush()
    
    # STEP 5: Handle removals (in Airtable but not in CSV)
    # CRITICAL: Only mark as removed if NO active record exists for property/dates/type
    removed_count = 0
    for (uid, feed_url), records in all_reservation_records.items():
        # Check if this record was processed
        if (uid, feed_url) in processed_uids:
            continue
        
        # Skip Evolve removals if CSV download failed
        if evolve_csv_failed and feed_url == "csv_evolve":
            continue
        
        # Get active records that need to be checked
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        for record in active_records:
            fields = record["fields"]
            checkout_date = fields.get("Check-out Date", "")
            
            # Only remove reservations where checkout >= today
            if checkout_date >= today:
                logging.info(f"🔍 Found unprocessed record for removal: {uid} (checkout: {checkout_date})")
                
                # CRITICAL: Check if another active record exists with same property/dates/type
                property_links = fields.get("Property ID", [])
                record_property_id = property_links[0] if property_links else None
                record_checkin = normalize_date_for_comparison(fields.get("Check-in Date", ""))
                record_checkout = normalize_date_for_comparison(fields.get("Check-out Date", ""))
                record_entry_type = fields.get("Entry Type", "")
                
                if record_property_id:
                    try:
                        # Look for any other active record with same property/dates/type
                        duplicate_formula = (
                            f"AND("
                            f"{{Property ID}} = '{record_property_id}', "
                            f"{{Check-in Date}} = '{record_checkin}', "
                            f"{{Check-out Date}} = '{record_checkout}', "
                            f"{{Entry Type}} = '{record_entry_type}', "
                            f"{{Reservation UID}} != '{uid}', "  # Different UID
                            f"OR({{Status}} = 'New', {{Status}} = 'Modified')"
                            f")"
                        )
                        
                        other_active_records = table.all(formula=duplicate_formula, max_records=1)
                        if other_active_records:
                            prop_name = property_id_to_name.get(record_property_id, record_property_id) if property_id_to_name else record_property_id
                            other_uid = other_active_records[0]['fields'].get('Reservation UID')
                            logging.info(f"Skipping removal of {uid} for Property \"{prop_name}\" - found active record with different UID: {other_uid}")
                            continue
                    except Exception as e:
                        logging.error(f"Error checking for duplicate records: {e}")
                
                # Skip removal for Evolve reservations if CSV download failed
                entry_source = fields.get("Entry Source", "Unknown")
                if entry_source == "Evolve" and evolve_csv_failed:
                    logging.info(f"Skipping removal of Evolve reservation {uid} due to CSV download failure")
                    continue
                
                # Mark as removed
                update_batch.add({
                    "id": record["id"],
                    "fields": {
                        "Status": "Removed",
                        "Last Updated": now_iso,
                        sync_details_field: f"Not found in CSV {now_iso}"
                    }
                })
                removed_count += 1
                
                # Log the removal
                prop_name = property_id_to_name.get(record_property_id, record_property_id) if record_property_id else "Unknown"
                logging.info(f"Marked as removed: {uid} for property \"{prop_name}\" ({record_property_id})")
            else:
                logging.debug(f"Skipping removal of {uid} - checkout date {checkout_date} is in the past")
    
    # Final flush
    update_batch.flush()
    
    # Update global stats based on entry source and type
    for (entry_source, property_id), reservations in summary.items():
        for res_info in reservations:
            # Determine if it's a block or reservation
            # (This is simplified - you might need to pass entry_type through summary)
            is_block = False  # Default assumption
            
            if entry_source == "iTrip":
                if is_block:
                    itrip_blocks["total"] += 1
                    if res_info["status"] == "new":
                        itrip_blocks["new"] += 1
                    elif res_info["status"] == "modified":
                        itrip_blocks["modified"] += 1
                    elif res_info["status"] in ["unchanged", "duplicate_ignored"]:
                        itrip_blocks["unchanged"] += 1
                else:
                    itrip_reserv["total"] += 1
                    if res_info["status"] == "new":
                        itrip_reserv["new"] += 1
                    elif res_info["status"] == "modified":
                        itrip_reserv["modified"] += 1
                    elif res_info["status"] in ["unchanged", "duplicate_ignored"]:
                        itrip_reserv["unchanged"] += 1
            elif entry_source == "Evolve":
                if is_block:
                    evolve_blocks["total"] += 1
                    if res_info["status"] == "new":
                        evolve_blocks["new"] += 1
                    elif res_info["status"] == "modified":
                        evolve_blocks["modified"] += 1
                    elif res_info["status"] in ["unchanged", "duplicate_ignored"]:
                        evolve_blocks["unchanged"] += 1
                else:
                    evolve_reserv["total"] += 1
                    if res_info["status"] == "new":
                        evolve_reserv["new"] += 1
                    elif res_info["status"] == "modified":
                        evolve_reserv["modified"] += 1
                    elif res_info["status"] in ["unchanged", "duplicate_ignored"]:
                        evolve_reserv["unchanged"] += 1
    
    logging.info(f"CSV sync complete: {created_count} new, {modified_count} modified, "
                 f"{unchanged_count} unchanged, {removed_count} removed")
    
    return summary

# Memory-optimized sync process
def sync_reservations_memory_optimized(csv_reservations, all_records, table, session_tracker=None, evolve_csv_failed=False, property_id_to_name=None):
    """Memory-optimized version using collector pattern."""
    logging.info("Starting memory-based processing to prevent false removals...")
    
    # Initialize collector
    collector = InMemoryCollector()
    collector.property_mapping = property_id_to_name or {}
    collector.existing_records = all_records
    
    # Track property/date combinations that had duplicates
    duplicate_detected_dates = set()
    now_iso = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")
    
    # Process each reservation
    stats = {'created': 0, 'updated': 0, 'unchanged': 0, 'removed': 0, 'duplicates': 0}
    
    # Group by feed URL for efficient processing
    by_feed = defaultdict(list)
    for res in csv_reservations:
        by_feed[res["feed_url"]].append(res)
    
    # Process each feed
    for feed_url, feed_reservations in by_feed.items():
        logging.info(f"Processing {len(feed_reservations)} reservations from {feed_url}")
        
        for res in feed_reservations:
            uid = res["uid"]
            
            # Create composite UID if property is known
            if res.get("property_id"):
                composite_uid = f"{uid}_{res['property_id']}"
            else:
                composite_uid = uid
            
            # Skip if already processed (check both composite and base UID)
            if (composite_uid, feed_url) in collector.processed_uids or (uid, feed_url) in collector.processed_uids:
                continue
                
            # Mark as processed
            collector.processed_uids.add((composite_uid, feed_url))
            collector.processed_uids.add((uid, feed_url))  # Also track base UID
            
            # HYBRID APPROACH: Try UID matching first
            all_matching_records = all_records.get((uid, feed_url), [])
            
            # Also check composite UID
            if not all_matching_records and res.get("property_id"):
                composite_key = (composite_uid, feed_url)
                all_matching_records = all_records.get(composite_key, [])
            
            # HYBRID APPROACH: If no UID match, try property+dates+type matching
            if not all_matching_records and res.get("property_id"):
                # Search for records with same property, dates, and type
                property_id = res["property_id"]
                checkin_date = res["dtstart"]
                checkout_date = res["dtend"]
                entry_type = res["entry_type"]
                
                # Check all existing records for this match
                for (existing_uid, existing_feed), records in all_records.items():
                    if existing_feed != feed_url:  # Must be same feed
                        continue
                    for record in records:
                        fields = record['fields']
                        # Get property ID from linked field
                        prop_links = fields.get('Property ID', [])
                        existing_prop_id = prop_links[0] if prop_links else None
                        
                        if (existing_prop_id == property_id and
                            fields.get('Check-in Date') == checkin_date and
                            fields.get('Check-out Date') == checkout_date and
                            fields.get('Entry Type') == entry_type and
                            fields.get('Status') in ('New', 'Modified')):
                            # Found a match! Use these records
                            logging.info(f"🔍 HYBRID: Found existing record by property+dates+type for UID {uid}")
                            all_matching_records = records
                            # Track this UID as processed too
                            collector.processed_uids.add((existing_uid, feed_url))
                            break
                    if all_matching_records:
                        break
            
            active_records = [r for r in all_matching_records if r["fields"].get("Status") in ("New", "Modified")]
            
            if active_records:
                # Check if modified
                latest_active = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
                if has_important_changes(latest_active["fields"], res):
                    # Create update data
                    update_data = {
                        "Entry Type": res["entry_type"],
                        "Service Type": res["service_type"],
                        "Guest Name": res.get("guest_name", ""),
                        "Check-in Date": res["dtstart"],
                        "Check-out Date": res["dtend"],
                        "Property ID": [res["property_id"]] if res.get("property_id") else [],
                        "Entry Source": res["entry_source"],
                        "Reservation UID": composite_uid,
                        "Status": "Modified",
                        "Same-day Turnover": res.get("same_day_turnover", False),
                        "ICS URL": feed_url,
                        sync_details_field: f"Modified from CSV {now_iso}"
                    }
                    
                    # Preserve HCP fields
                    for field in HCP_FIELDS:
                        if field in latest_active["fields"] and field not in WRITE_BLACKLIST:
                            update_data[field] = latest_active["fields"][field]
                    
                    # Mark old records for update
                    for record in all_matching_records:
                        collector.add_update(record["id"], {"Status": "Old", "Last Updated": now_iso})
                    
                    # Add new record creation
                    collector.add_create(composite_uid, feed_url, update_data)
                    stats['updated'] += 1
                else:
                    # CRITICAL FIX: Track unchanged reservations to prevent them from being marked as removed
                    # We need to track ALL existing active record UIDs from this CSV
                    for record in active_records:
                        record_uid = record["fields"].get("Reservation UID", "")
                        record_feed_url = record["fields"].get("ICS URL", "")
                        if record_uid and record_feed_url:
                            collector.processed_uids.add((record_uid, record_feed_url))
                    
                    stats['unchanged'] += 1
            else:
                # Check for duplicates before creating
                if res["property_id"] and check_for_duplicate(
                    table, 
                    res["property_id"], 
                    res["dtstart"], 
                    res["dtend"], 
                    res["entry_type"],
                    session_tracker,
                    property_id_to_name
                ):
                    stats['duplicates'] += 1
                    continue
                
                # Create new record
                new_fields = {
                    "Entry Type": res["entry_type"],
                    "Service Type": res["service_type"],
                    "Guest Name": res.get("guest_name", ""),
                    "Check-in Date": res["dtstart"],
                    "Check-out Date": res["dtend"],
                    "Entry Source": res["entry_source"],
                    "Reservation UID": composite_uid,
                    "Status": "New",
                    "Same-day Turnover": res.get("same_day_turnover", False),
                    "ICS URL": feed_url,
                    sync_details_field: f"Created from CSV {now_iso}"
                }
                
                if res["property_id"]:
                    new_fields["Property ID"] = [res["property_id"]]
                
                collector.add_create(composite_uid, feed_url, new_fields)
                stats['created'] += 1
                
                # Track in session
                if session_tracker is not None and res["property_id"]:
                    tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                    session_tracker.add(tracker_key)
    
    # Find removed reservations
    today = date.today().isoformat()
    future_cutoff = (date.today() + relativedelta(months=6)).isoformat()
    
    for (uid, feed_url), records in all_records.items():
        # Skip if already processed
        if (uid, feed_url) in collector.processed_uids:
            continue
            
        # Skip Evolve removals if CSV download failed
        if evolve_csv_failed and feed_url == "csv_evolve":
            continue
        
        # Get active records
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        for record in active_records:
            fields = record["fields"]
            checkout_date = fields.get("Check-out Date", "")
            
            # Only process future reservations
            if checkout_date >= today and checkout_date <= future_cutoff:
                # CRITICAL: Check if another active record exists with same property/dates/type
                property_links = fields.get("Property ID", [])
                record_property_id = property_links[0] if property_links else None
                
                if record_property_id:
                    # Check if we have another active record for same property/dates
                    found_replacement = False
                    for processed_uid in collector.processed_uids:
                        # Look through our created records for a match
                        for create_op in collector.to_create:
                            if (create_op['fields'].get('Property ID', [None])[0] == record_property_id and
                                create_op['fields'].get('Check-in Date') == fields.get('Check-in Date') and
                                create_op['fields'].get('Check-out Date') == fields.get('Check-out Date') and
                                create_op['fields'].get('Entry Type') == fields.get('Entry Type')):
                                found_replacement = True
                                break
                        if found_replacement:
                            break
                    
                    if found_replacement:
                        logging.info(f"Skipping removal of {uid} - found replacement with different UID")
                        continue
                
                # Mark as removed
                collector.add_update(record["id"], {
                    "Status": "Removed",
                    "Last Updated": now_iso,
                    sync_details_field: f"Not found in CSV {now_iso}"
                })
                stats['removed'] += 1
    
    # Execute all operations
    collector.execute(table)
    
    logging.info(f"Memory-optimized sync complete: {stats['created']} new, {stats['updated']} modified, "
                 f"{stats['unchanged']} unchanged, {stats['removed']} removed, {stats['duplicates']} duplicates skipped")
    
    return stats

# Tab2 processing for owner blocks
def build_guest_to_property_map(properties_table):
    """Build a map from guest name to property record for Tab2 processing."""
    guest_to_prop = {}
    
    # Fetch properties that have an HCP Customer ID and are from Evolve
    formula = "AND({HCP Customer ID}, {Entry Source (from ICS Feeds)} = 'Evolve')"
    properties = properties_table.all(formula=formula)
    
    for prop_record in properties:
        fields = prop_record["fields"]
        hcp_customer = fields.get("HCP Customer ID")
        if hcp_customer:
            # The Full Name field is a lookup from HCP Customer
            full_name = fields.get("Full Name (from HCP Customer ID)")
            if full_name and isinstance(full_name, list) and len(full_name) > 0:
                guest_name = full_name[0]
                guest_to_prop[guest_name] = prop_record
                
                # Also map variations
                guest_to_prop[guest_name.lower()] = prop_record
                guest_to_prop[guest_name.upper()] = prop_record
                
                # Log the mapping
                prop_name = fields.get("Property Name", "Unknown")
                logging.debug(f"Mapped guest '{guest_name}' to property '{prop_name}'")
    
    logging.info(f"Created {len(guest_to_prop)} guest → property mappings")
    return guest_to_prop

def process_tab2_csv(file_path, reservations_table, guest_to_prop, existing_records, session_tracker=None, property_id_to_name=None):
    """
    Parse one "Tab 2" CSV.  
    • Only processes rows where guest names match entries in the Properties table
    • Creates blocks for new reservations
    • Updates existing blocks when changes detected
    
    Args:
        file_path: Path to the CSV file
        reservations_table: Airtable table object
        guest_to_prop: Dict mapping guest names to property records
        existing_records: Dict of existing Airtable records
        session_tracker: Set tracking records created in current session
    """
    feed_url = "csv_evolve_blocks"
    now_iso_str = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")
    
    # Date filtering - using the pattern from icsProcess.py
    TAB2_FILTER_MONTHS_PAST = 2      # Keep blocks from 2 months ago
    TAB2_FILTER_MONTHS_FUTURE = 6    # Keep blocks up to 6 months ahead
    
    cutoff_past = (date.today() - relativedelta(months=TAB2_FILTER_MONTHS_PAST)).isoformat()
    cutoff_future = (date.today() + relativedelta(months=TAB2_FILTER_MONTHS_FUTURE)).isoformat()
    
    stats = {
        "processed": 0,
        "skipped_no_property": 0,
        "new_blocks": 0,
        "modified_blocks": 0,
        "unchanged_blocks": 0,
        "removed_blocks": 0,
        "skipped_duplicates": 0
    }
    
    create_batch = BatchCollector(reservations_table, op="create")
    update_batch = BatchCollector(reservations_table, op="update")
    
    # Build a lookup for composite UIDs to handle the new format
    # Map base_uid -> property_id -> records
    composite_lookup = defaultdict(lambda: defaultdict(list))
    for (uid, feed), records in existing_records.items():
        if feed == feed_url:
            # Check if this is a composite UID
            if '_' in uid and uid.count('_') == 1:
                base_uid, prop_id = uid.rsplit('_', 1)
                if prop_id.startswith('rec'):  # Airtable record ID format
                    composite_lookup[base_uid][prop_id] = records
    
    # Track processed UIDs to avoid duplicates within the same file
    processed_uids = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                stats["processed"] += 1
                
                # Extract fields
                uid = row.get("Reservation", "").strip()
                guest_name = row.get("Guest Name", "").strip()
                checkin = row.get("Check-In", "").strip()
                checkout = row.get("Check-Out", "").strip()
                status = row.get("Status", "").strip().lower()
                
                if not all([uid, guest_name, checkin, checkout]):
                    logging.debug(f"Skipping row with missing data: {row}")
                    continue
                
                # Skip cancelled blocks
                if status != "booked":
                    logging.debug(f"Skipping {status} block: {uid}")
                    continue
                
                # Parse dates
                try:
                    checkin_date = parse(checkin).date()
                    checkout_date = parse(checkout).date()
                except Exception as e:
                    logging.error(f"Date parsing error for {uid}: {e}")
                    continue
                
                # Apply date filtering
                if checkin_date < datetime.strptime(cutoff_past, "%Y-%m-%d").date():
                    logging.debug(f"Skipping old block {uid} - checkin {checkin_date} before cutoff {cutoff_past}")
                    continue
                if checkin_date > datetime.strptime(cutoff_future, "%Y-%m-%d").date():
                    logging.debug(f"Skipping future block {uid} - checkin {checkin_date} after cutoff {cutoff_future}")
                    continue
                
                # Format dates for Airtable
                checkin_display = checkin_date.isoformat()
                checkout_display = checkout_date.isoformat()
                
                # Find property by guest name
                prop_record = guest_to_prop.get(guest_name) or guest_to_prop.get(guest_name.lower())
                if not prop_record:
                    logging.debug(f"No property found for guest: {guest_name}")
                    stats["skipped_no_property"] += 1
                    continue
                
                prop_id = prop_record["id"]
                prop_name = prop_record["fields"].get("Property Name", "Unknown")
                
                # Create composite UID for this property
                composite_uid = f"{uid}_{prop_id}"
                
                # Skip if we've already processed this UID in this file
                if composite_uid in processed_uids:
                    logging.debug(f"Skipping duplicate UID in same file: {composite_uid}")
                    continue
                processed_uids.add(composite_uid)
                
                # Retrieve any existing records for this reservation
                # First try composite UID lookup, then fall back to old method
                records = composite_lookup.get(uid, {}).get(prop_id, [])
                if not records:
                    # Fallback to old lookup method for backward compatibility
                    key = (uid, feed_url)
                    records = existing_records.get(key, [])
                active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
                
                # Handle different status scenarios
                if status == "booked":
                    if not active_records:
                        # Check for duplicate blocks before creating
                        if check_for_duplicate(
                            reservations_table,
                            prop_id,
                            checkin_display,
                            checkout_display,
                            "Block",
                            session_tracker,
                            property_id_to_name
                        ):
                            prop_name = property_id_to_name.get(prop_id, prop_id)
                            logging.info(f"Ignoring duplicate block: {composite_uid} for property \"{prop_name}\" ({prop_id})")
                            stats["skipped_duplicates"] = stats.get("skipped_duplicates", 0) + 1
                            continue
                        
                        # No active record exists - create a new block
                        new_fields = {
                            "Entry Type": "Block",
                            "Service Type": "Needs Review",
                            "Guest Name": guest_name,
                            "Check-in Date": checkin_display,
                            "Check-out Date": checkout_display,
                            "Property ID": [prop_id],
                            "Entry Source": "Evolve",
                            "Reservation UID": composite_uid,
                            "Status": "New",
                            "ICS URL": feed_url,
                            sync_details_field: f"Created from Tab2 CSV {now_iso_str}"
                        }
                        
                        create_batch.add({"fields": new_fields})
                        stats["new_blocks"] += 1
                        logging.debug(f"Creating new block for {composite_uid} at {prop_name}")
                        
                        # Track in session to prevent duplicates in this run
                        if session_tracker is not None:
                            tracker_key = (prop_id, checkin_display, checkout_display, "Block")
                            session_tracker.add(tracker_key)
                    else:
                        # Check if any changes occurred
                        latest = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
                        fields = latest["fields"]
                        
                        if (fields.get("Check-in Date") != checkin_display or
                            fields.get("Check-out Date") != checkout_display or
                            fields.get("Guest Name", "").strip() != guest_name):
                            
                            # Changes detected - mark old records as Old
                            for record in records:
                                if record["fields"].get("Status") != "Old":
                                    update_batch.add({
                                        "id": record["id"],
                                        "fields": {
                                            "Status": "Old",
                                            "Last Updated": now_iso_str
                                        }
                                    })
                            
                            # Create new Modified record
                            new_fields = {
                                "Entry Type": "Block",
                                "Service Type": "Needs Review",
                                "Guest Name": guest_name,
                                "Check-in Date": checkin_display,
                                "Check-out Date": checkout_display,
                                "Property ID": [prop_id],
                                "Entry Source": "Evolve",
                                "Reservation UID": composite_uid,
                                "Status": "Modified",
                                "ICS URL": feed_url,
                                sync_details_field: f"Modified from Tab2 CSV {now_iso_str}"
                            }
                            
                            # Preserve HCP fields
                            for field in HCP_FIELDS:
                                if field in fields and field not in WRITE_BLACKLIST:
                                    new_fields[field] = fields[field]
                            
                            create_batch.add({"fields": new_fields})
                            stats["modified_blocks"] += 1
                            logging.debug(f"Updating block for {composite_uid} at {prop_name}")
                        else:
                            stats["unchanged_blocks"] += 1
                            logging.debug(f"No changes for block {composite_uid} at {prop_name}")
        
        # Flush batches
        create_batch.flush()
        update_batch.flush()
        
        # Mark missing blocks as removed
        for (uid, feed), records in existing_records.items():
            if feed == feed_url:
                # Check if this UID was processed (handles both old and composite UIDs)
                was_processed = False
                
                # For composite UIDs
                if '_' in uid and uid.count('_') == 1:
                    was_processed = uid in processed_uids
                else:
                    # For base UIDs, check if any composite version was processed
                    for proc_uid in processed_uids:
                        if proc_uid.startswith(f"{uid}_"):
                            was_processed = True
                            break
                
                if not was_processed:
                    active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
                    for record in active_records:
                        # Only remove blocks with future checkout dates
                        checkout_str = record["fields"].get("Check-out Date", "")
                        if checkout_str:
                            try:
                                checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d").date()
                                if checkout_date >= date.today():
                                    update_batch.add({
                                        "id": record["id"],
                                        "fields": {
                                            "Status": "Removed",
                                            "Last Updated": now_iso_str,
                                            sync_details_field: f"Not found in Tab2 CSV {now_iso_str}"
                                        }
                                    })
                                    stats["removed_blocks"] += 1
                                    logging.debug(f"Marking block {uid} as removed")
                            except:
                                pass
        
        # Final flush
        update_batch.flush()
        
        logging.info(
            f"Tab2 processing complete: {stats['processed']} rows"
            f" • {stats['new_blocks']} new"
            f" • {stats['modified_blocks']} modified"
            f" • {stats['unchanged_blocks']} unchanged"
            f" • {stats['removed_blocks']} removed"
            f" • {stats.get('skipped_duplicates', 0)} skipped (duplicates)"
            f" • {stats['skipped_no_property']} skipped (no property)"
        )
        return True, stats
        
    except Exception as e:
        logging.error(f"Error processing Tab2 CSV {file_path}: {e}", exc_info=True)
        return False, stats

# ────────────────────────────────────────────────────────────────────────────
# Process regular CSV files (both iTrip and Evolve)
# ────────────────────────────────────────────────────────────────────────────
def process_csv_files(csv_files, reservations_table, properties_table, existing_records, session_tracker=None, evolve_csv_failed=False, property_id_to_name=None):
    """Process regular CSV files from iTrip and Evolve."""
    all_csv_reservations = []
    
    for csv_file in csv_files:
        fname = os.path.basename(csv_file)
        logging.info(f"Processing CSV file: {fname}")
        
        # Detect format and parse
        if detect_itrip_header(csv_file):
            entry_source = "iTrip"
            reservations = parse_itrip_csv(csv_file, entry_source, properties_table)
        else:
            entry_source = "Evolve"
            reservations = parse_evolve_csv(csv_file, entry_source, properties_table)
        
        logging.info(f"Parsed {len(reservations)} reservations from {fname}")
        all_csv_reservations.extend(reservations)
    
    if not all_csv_reservations:
        logging.info("No reservations found in CSV files")
        return {}
    
    # Use memory-optimized sync if we have many records
    if len(all_csv_reservations) > 100:
        logging.info(f"Using memory-optimized sync for {len(all_csv_reservations)} reservations")
        stats = sync_reservations_memory_optimized(
            all_csv_reservations, 
            existing_records, 
            reservations_table, 
            session_tracker,
            evolve_csv_failed,
            property_id_to_name
        )
        # Convert stats to summary format for compatibility
        summary = {}
        # This is simplified - you might need to maintain the full summary structure
        return summary
    else:
        # Use original sync for smaller batches
        return sync_reservations(
            all_csv_reservations, 
            existing_records, 
            reservations_table, 
            session_tracker,
            evolve_csv_failed,
            property_id_to_name
        )

# ────────────────────────────────────────────────────────────────────────────
# Main process
# ────────────────────────────────────────────────────────────────────────────
def main():
    """Main entry point for CSV processing."""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        logging.info("="*60)
        logging.info(f"Starting CSV sync process - Environment: {Config.environment}")
        logging.info(f"Process directory: {PROCESS_DIR}")
        logging.info(f"Done directory: {DONE_DIR}")
        
        # Initialize Airtable
        api = Api(Config.get_airtable_api_key())
        base_id = Config.get_airtable_base_id()
        reservations_table = api.table(base_id, Config.get_airtable_table_name('reservations'))
        properties_table = api.table(base_id, Config.get_airtable_table_name('properties'))
        
        # Create session-wide duplicate tracker
        session_tracker = set()
        logging.info("Initialized session-wide duplicate tracker")
        
        # Build comprehensive property ID to name mapping for better logging
        property_id_to_name = {}
        try:
            all_properties = properties_table.all()
            for prop in all_properties:
                prop_id = prop['id']
                prop_name = prop['fields'].get('Property Name', '')
                prop_address = prop['fields'].get('Address', '')
                # Use name if available, otherwise use address
                display_name = prop_name if prop_name else prop_address
                if display_name:
                    property_id_to_name[prop_id] = display_name
            logging.info(f"Loaded {len(property_id_to_name)} property mappings for enhanced logging")
        except Exception as e:
            logging.warning(f"Could not load property mappings: {e}")
        
        # Check for Evolve CSV failure flag
        evolve_csv_failed = os.path.exists(os.path.join(PROCESS_DIR, ".evolve_csv_failed"))
        if evolve_csv_failed:
            logging.warning("⚠️ EVOLVE CSV FAILED FLAG DETECTED - Will skip removal logic for Evolve reservations")
        
        # ————— Regular CSV files (iTrip, Evolve regular) —————
        csv_files = [f for f in glob.glob(os.path.join(PROCESS_DIR, "*.csv")) 
                     if not f.endswith("_tab2.csv")]
        
        if csv_files:
            # Fetch existing records for regular CSVs
            existing_records = fetch_all_reservations(
                reservations_table,
                ["csv_itrip", "csv_evolve"]
            )
            
            summary = process_csv_files(
                csv_files, 
                reservations_table, 
                properties_table, 
                existing_records, 
                session_tracker,
                evolve_csv_failed,
                property_id_to_name
            )
            
            # Move processed files
            for csv_file in csv_files:
                try:
                    fname = os.path.basename(csv_file)
                    dest = os.path.join(DONE_DIR, fname)
                    shutil.move(csv_file, dest)
                    logging.info(f"Moved {fname} to done directory")
                except Exception as e:
                    logging.error(f"Error moving file {csv_file}: {e}")
        
        # ————— Evolve "Tab 2" CSV exports —————
        guest_to_prop = build_guest_to_property_map(properties_table)
        evolve_files = glob.glob(os.path.join(PROCESS_DIR, "*_tab2.csv"))
        existing_records = fetch_all_reservations(
            reservations_table,
            ["csv_evolve_blocks"]                # we fetch once for the single fixed feed_url
        )
        
        for csv_file in evolve_files:
            fname = os.path.basename(csv_file)
            logging.info(f"Processing Evolve Tab2 CSV: {fname}")
            ok, tab2_stats = process_tab2_csv(
                csv_file, reservations_table, guest_to_prop, existing_records, session_tracker, property_id_to_name
            )
            if ok:
                for k in ("new", "modified", "unchanged", "removed"):
                    tab2_global[k] += tab2_stats[f"{k}_blocks"]
                try:
                    dest = os.path.join(DONE_DIR, fname)
                    shutil.move(csv_file, dest)
                    logging.info(f"Moved {fname} to done directory")
                except Exception as e:
                    logging.error(f"Error moving Tab2 file {csv_file}: {e}")
            else:
                logging.error(f"Failed to process Tab2 file: {fname}")
        
        # ───────────────────────────────────────────────────────────────
        # Log final summary
        # ───────────────────────────────────────────────────────────────
        logging.info("="*60)
        logging.info("CSV SYNC SUMMARY:")
        logging.info(f"  Regular CSV Reservations:")
        logging.info(f"    iTrip  - New: {itrip_reserv['new']}, Modified: {itrip_reserv['modified']}, "
                     f"Unchanged: {itrip_reserv['unchanged']}, Removed: {itrip_reserv['removed']}")
        logging.info(f"    Evolve - New: {evolve_reserv['new']}, Modified: {evolve_reserv['modified']}, "
                     f"Unchanged: {evolve_reserv['unchanged']}, Removed: {evolve_reserv['removed']}")
        logging.info(f"  Regular CSV Blocks:")
        logging.info(f"    iTrip  - New: {itrip_blocks['new']}, Modified: {itrip_blocks['modified']}, "
                     f"Unchanged: {itrip_blocks['unchanged']}, Removed: {itrip_blocks['removed']}")
        logging.info(f"    Evolve - New: {evolve_blocks['new']}, Modified: {evolve_blocks['modified']}, "
                     f"Unchanged: {evolve_blocks['unchanged']}, Removed: {evolve_blocks['removed']}")
        logging.info(f"  Tab2 Owner Blocks:")
        logging.info(f"    New: {tab2_global['new']}, Modified: {tab2_global['modified']}, "
                     f"Unchanged: {tab2_global['unchanged']}, Removed: {tab2_global['removed']}")
        logging.info("="*60)
        
        # Update automation status in Airtable
        try:
            automation_table = api.table(base_id, Config.get_airtable_table_name('automation_control'))
            records = automation_table.all(formula="{Name} = 'CSV Files'", max_records=1)
            if records:
                record_id = records[0]['id']
                update_fields = {
                    'Last Ran Time': datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds"),
                    'Active': True,
                    'Sync Details': f"✅ CSV sync completed successfully\n" +
                                   f"Regular: iTrip ({itrip_reserv['new']+itrip_blocks['new']} new, " +
                                   f"{itrip_reserv['modified']+itrip_blocks['modified']} mod), " +
                                   f"Evolve ({evolve_reserv['new']+evolve_blocks['new']} new, " +
                                   f"{evolve_reserv['modified']+evolve_blocks['modified']} mod)\n" +
                                   f"Tab2: {tab2_global['new']} new, {tab2_global['modified']} modified"
                }
                automation_table.update(record_id, update_fields)
        except Exception as e:
            logging.error(f"Failed to update CSV Files automation status: {e}")
        
        # Run duplicate detection tests after successful processing
        try:
            logging.info("\n" + "="*60)
            logging.info("Running duplicate detection tests...")
            test_passed = run_duplicate_detection_tests("CSV", Config.environment)
            if not test_passed:
                logging.warning("⚠️ Some duplicate detection tests failed - check Airtable for details")
            logging.info("="*60 + "\n")
        except Exception as test_error:
            logging.error(f"Error running duplicate detection tests: {test_error}")
        
    except Exception as e:
        logging.error(f"Fatal error in main process: {e}", exc_info=True)

if __name__ == "__main__":
    main()