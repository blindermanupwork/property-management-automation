#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# CSV → Airtable synchroniser - Complete Version with Proper History Tracking
#
# • Handles two suppliers:
#     – iTrip  : header row contains "Property Name"
#     – Evolve : otherwise
# • Preserves complete history by cloning records for changes
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

# ---------------------------------------------------------------------------
# CONFIG — Environment-based configuration
# ---------------------------------------------------------------------------
# Use Config class for path resolution
PROCESS_DIR = str(Config.get_csv_process_dir())
DONE_DIR = str(Config.get_csv_done_dir())
LOG_FILE = str(Config.get_logs_dir() / "csv_sync.log")

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
sync_details_field = "Service Sync Details" if Config.environment == 'development' else "Sync Details"

HCP_FIELDS = [
    "Service Job ID", "Job Creation Time", "Sync Status",
    "Scheduled Service Time", "Sync Date and Time", sync_details_field,
    "Job Status", "Custom Service Time", "Entry Source"
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
    
}
DEFAULT_SERVICE_TYPE = "Turnover"  # Default for reservations

BLOCK_TYPE_KEYWORDS = {
   
}
DEFAULT_BLOCK_TYPE = ""  # Default for blocks
# --- LOGGING -----------------------------------------------------------

LOG_PATH = LOG_FILE
# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

for h in logger.handlers[:]:                    # remove old handlers
    logger.removeHandler(h)

# 1️⃣  FILE LOGGER with PST timezone
file_handler   = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Configure timezones: MST for logging, Arizona for Airtable data
mst = pytz.timezone('America/Phoenix')  # For logging
arizona_tz = pytz.timezone('America/Phoenix')  # For Airtable timestamps
class MSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=mst)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

file_handler.setFormatter(MSTFormatter("%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

# 2️⃣  CONSOLE LOGGER  – wrap stdout in a UTF-8 TextIOWrapper
stdout_utf8 = io.TextIOWrapper(
    sys.stdout.buffer,            # raw buffer
    encoding="utf-8",
    errors="replace",             # un-encodable chars → '?' so emit never fails
    line_buffering=True
)
console_handler = logging.StreamHandler(stdout_utf8)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))

# keep the filter you already had
class ExcludeDigestFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()

        # keep final-summary & property-summary lines ➜ drop *NOT* them
        if msg.startswith(("------------", " * ")):
            return True   # ⬅️ allow important summary lines

        if "Run digest" in msg:      return False
        if msg.startswith(("Evolve ->", "iTrip ->")): return False
        return True

console_handler.addFilter(ExcludeDigestFilter())
logger.addHandler(console_handler)

logging.info("=== CSV sync run started ===")


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
# Utility Functions
# ---------------------------------------------------------------------------
def normalize_date_for_comparison(date_value):
    """Convert any date format to MM/DD/YYYY for consistent comparison"""
    if not date_value:
        return ""
    try:
        dt = parse(date_value).date()
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return date_value

def convert_flag_value(value):
    """Convert Airtable flag values to bool for consistent comparison"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "checked", "t", "y", "1")
    return bool(value)

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
    
    # Mark ALL records as Old and prefix Service Job ID with "old_" to disconnect from webhooks
    for record in records:
        update_fields = {"Status": "Old", "Last Updated": now_iso}
        
        # Prefix Service Job ID with "old_" to prevent webhook updates
        service_job_id = record.get("fields", {}).get("Service Job ID")
        if service_job_id and not service_job_id.startswith("old_"):
            update_fields["Service Job ID"] = f"old_{service_job_id}"
        
        update_batch.add({
            "id": record["id"],
            "fields": update_fields
        })
    
    # Flush updates
    update_batch.done()
    
    # Build clone (copy everything except blacklist)
    clone = {k: v for k, v in old_f.items() if k not in WRITE_BLACKLIST}
    
    # IMPORTANT: Explicitly preserve ALL HCP fields from the latest record
    # This ensures they're carried forward even if some would normally be excluded
    for hcp_field in HCP_FIELDS:
        if hcp_field in old_f:
            # FORCE copy all HCP fields, except handle Service Job ID specially
            if hcp_field == "Service Job ID" and status == "Removed":
                # For removed reservations, clear the Service Job ID since no job exists
                clone[hcp_field] = None
            else:
                # For Modified records, preserve the original Service Job ID
                clone[hcp_field] = old_f[hcp_field]
    
    # Apply the changes and status
    clone.update(Status=status, **field_to_change, **{"Last Updated": now_iso})
    
    # Write new row
    return table.create(clone)

# ---------------------------------------------------------------------------
# Header → canonical name helpers
# ---------------------------------------------------------------------------
COL_UID       = {"reservationid", "reservation", "booking#", "booking #", "booking"}
COL_CHECKIN   = {"checkin", "check-in", "check_in"}
COL_CHECKOUT  = {"checkout", "check-out", "check_out"}
COL_PROP_NAME = {"propertyname", "property address", "address",
                 "listing#", "listing #", "listing"}

def norm(h):  # helper: strip, lowercase, kill spaces/hyphens
    return h.lower().strip().replace(" ", "").replace("-", "")

def normalise_headers(raw):
    """dict normalised → original header text"""
    return {norm(h): h for h in raw}

# ---------------------------------------------------------------------------
# CSV Processing Functions
# ---------------------------------------------------------------------------
def parse_row(row, hdr_map):
    """Extract and normalize data from a single CSV row"""
    pick = lambda keys: next((row[hdr_map[h]] for h in keys if h in hdr_map), "")

    uid_raw = pick(COL_UID).strip()
    cin_raw = pick(COL_CHECKIN).strip()
    cout_raw = pick(COL_CHECKOUT).strip()
    
    # Get tenant name for detecting block types
    
    contractor_info = ""
    property_address = ""
    
    tenant_name = ""
    tenant_name_keys = ["tenant name", "guest name", "guest"]
    for col in row:
        # Check if column name matches any of our tenant name keys after normalization
        if col.lower().strip() in tenant_name_keys or any(norm(col) == norm(key) for key in tenant_name_keys):
            tenant_name = row[col].strip()
            break
    
    # Get property address
    address_keys = ["Property Address", "property address", "Address", "address"]
    for key in address_keys:
        if key in row:
            property_address = row[key].strip()
            break
        elif key in hdr_map:
            property_address = row[hdr_map[key]].strip()
            break
    
    # Get contractor info if available (may contain block details)
    contractor_keys = ["Contractor Info", "contractor info", "Work Order"]
    for key in contractor_keys:
        if key in row:
            contractor_info = row[key].strip()
            break
        elif key in hdr_map:
            contractor_info = row[hdr_map[key]].strip()
            break
    
    # Get iTrip Same Day? flag if available
    itrip_same_day = None
    same_day_keys = ["Same Day?", "same day?", "Same Day", "same day"]
    for key in same_day_keys:
        if key in row:
            same_day_value = row[key].strip()
            if same_day_value.lower() in ["yes", "y", "true", "1"]:
                itrip_same_day = True
            elif same_day_value.lower() in ["no", "n", "false", "0"]:
                itrip_same_day = False
            break
    
    # Skip blank filler lines
    if not (uid_raw and cin_raw and cout_raw):
        return None

    # Parse dates safely
    try:
        cin_date = parse(cin_raw).date()
        cout_date = parse(cout_raw).date()
        
        # Store dates in both formats - ISO for calculations and formatted for Airtable
        dtstart_iso = cin_date.isoformat()
        dtend_iso = cout_date.isoformat()
        dtstart_display = cin_date.strftime("%m/%d/%Y")
        dtend_display = cout_date.strftime("%m/%d/%Y")
    except Exception:
        logging.warning(f"Row with UID={uid_raw} has unparsable dates "
                        f"({cin_raw!r}, {cout_raw!r}) – skipped")
        return None

    prop_name = pick(COL_PROP_NAME).strip()
    
    # Determine entry type, service type, and block type
    entry_type = DEFAULT_ENTRY_TYPE
    service_type = DEFAULT_SERVICE_TYPE
    block_type = None
    
    # Combine tenant name and contractor info for keyword detection
    text_to_check = (tenant_name + " " + contractor_info).lower()
    
    # Check for ENTRY_TYPE_KEYWORDS
    for keyword, type_value in ENTRY_TYPE_KEYWORDS.items():
        if keyword in text_to_check:
            entry_type = type_value
            # Use debug level instead of info to reduce console clutter
            logging.debug(f"UID: {uid_raw} - Detected as {type_value} (keyword: '{keyword}')")
            break
    
    # Set appropriate service type and block type based on entry type
    if entry_type == "Block":
        # Default for blocks if nothing more specific is found
        service_type = "Needs Review"
        block_type = ""  # Default block type
        
        # Look for more specific block type
        for keyword, block_type_value in BLOCK_TYPE_KEYWORDS.items():
            if keyword in text_to_check:
                block_type = block_type_value
                break
                
        # Look for service type
        for keyword, service_type_value in SERVICE_TYPE_KEYWORDS.items():
            if keyword in text_to_check:
                service_type = service_type_value
                break
    elif entry_type == "Reservation":
        # Default service type for reservations
        service_type = "Turnover"
    
    return {
        "uid": uid_raw,
        "dtstart_iso": dtstart_iso,
        "dtend_iso": dtend_iso,
        "dtstart": dtstart_display,
        "dtend": dtend_display,
        "property_name": prop_name,
        "property_address": property_address,  # Store the address
        "contractor_info": contractor_info,  # Store contractor info for iTrip Report Info field
        "entry_type": entry_type,
        "service_type": service_type,
        "block_type": block_type,
        "overlapping": False,
        "same_day_turnover": False,
        "itrip_same_day": itrip_same_day,  # Store iTrip's Same Day? value
        "feed_url": None,
        "property_id": None,
        "entry_source": None,
    }

def process_csv_files(property_lookup, guest_overrides=None):
    """Process all CSV files and return parsed reservations"""
    all_reservations = []
    csv_files = [f for f in os.listdir(PROCESS_DIR) if f.lower().endswith(".csv")]
    processed_files = []
    
    if not csv_files:
        logging.info(f"No CSV files to process in {PROCESS_DIR}")
        return all_reservations, processed_files
    
    if guest_overrides is None:
        guest_overrides = {}
    
    for fname in sorted(csv_files):
        path = os.path.join(PROCESS_DIR, fname)
        logging.info(f"Processing {fname}...")
        
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                sample = f.read(2048)
                f.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t"])
                except csv.Error:
                    dialect = csv.get_dialect("excel")

                reader = csv.DictReader(f, dialect=dialect)
                hdr_map = normalise_headers(reader.fieldnames)
                
                # Identify supplier
                supplier = "itrip" if "propertyname" in hdr_map else "evolve"
                feed_url = f"csv_{supplier}"
                entry_source = "iTrip" if supplier == "itrip" else "Evolve"
                
                # For Evolve, identify the listing column
                listing_col = None
                if supplier == "evolve":
                    for n in {"listing#", "listing #", "listing"}:
                        if n in hdr_map:
                            listing_col = hdr_map[n]
                            break
                
                # Parse all rows
                parsed_reservations = []
                missing_props = []
                
                for raw in reader:
                    res = parse_row(raw, hdr_map)
                    if res is None:
                        continue
                    
                    # Set feed URL and entry source
                    res["feed_url"] = feed_url
                    res["entry_source"] = entry_source
                    
                    # Link to property
                    pid = None
                    if supplier == "evolve" and listing_col:
                        listing_raw = raw.get(listing_col, "").strip()
                        pid = property_lookup.get(listing_raw)
                    else:  # iTrip
                        if res["property_name"]:
                            pid = property_lookup.get(res["property_name"].lower())
                    
                    if pid is None:
                        missing_props.append(res["uid"])
                        continue
                    
                    # Check for property owner overrides
                    if guest_overrides and supplier == "itrip":
                        # Get property owner name from the raw row
                        owner_name = ""
                        for col in raw:
                            if col.lower().strip() in ["property owner", "owner"]:
                                owner_name = raw[col].strip().lower()
                                break
                        
                        # Check if this property owner has an override for this property
                        for pattern in guest_overrides:
                            if pattern[0] == pid and pattern[1] in owner_name:
                                override_pid = guest_overrides[pattern]
                                logging.info(f"Applying property owner override for '{owner_name}' on property {pid} -> {override_pid}")
                                pid = override_pid
                                break
                    
                    res["property_id"] = pid
                    parsed_reservations.append(res)
                
                # Report any missing property links
                if missing_props:
                    logging.error(
                        f"❌ {os.path.basename(path)} – {len(missing_props)} reservation(s) missing Property mapping: "
                        f"{', '.join(missing_props)}"
                    )
                    raise ValueError(f"Missing property links for {len(missing_props)} reservations")
                
                # Count blocks and reservations
                block_count = sum(1 for res in parsed_reservations if res["entry_type"] == "Block")
                reservation_count = len(parsed_reservations) - block_count
                
                # File processed successfully
                all_reservations.extend(parsed_reservations)
                processed_files.append(path)
                logging.info(f"Successfully processed {fname} ({reservation_count} reservations and {block_count} blocks)")
        
        except Exception as e:
            logging.error(f"Error processing {fname}: {e}", exc_info=True)
            # File remains in PROCESS_DIR
    
    return all_reservations, processed_files

# ---------------------------------------------------------------------------
# Calculate Flags Locally
# ---------------------------------------------------------------------------
def calculate_flags(reservations):
    """Calculate overlapping dates and same-day turnover flags locally"""
    # Group by property_id
    by_property = defaultdict(list)
    for res in reservations:
        if res.get("property_id"):
            by_property[res["property_id"]].append(res)
    
    # Process each property
    for property_id, property_reservations in by_property.items():
        # Find overlaps (any pair of reservations where dates overlap)
        for a, b in combinations(property_reservations, 2):
            a_start = parse(a["dtstart_iso"]).date()
            a_end = parse(a["dtend_iso"]).date()
            b_start = parse(b["dtstart_iso"]).date()
            b_end = parse(b["dtend_iso"]).date()
            
            # Check for overlap: a starts before b ends AND a ends after b starts
            if a_start < b_end and a_end > b_start:
                a["overlapping"] = True
                b["overlapping"] = True
        
        # Find same-day turnovers
        checkin_dates = {parse(res["dtstart_iso"]).date() for res in property_reservations}
        
        for res in property_reservations:
            # Check if iTrip has already flagged this as same-day turnover
            if res.get("itrip_same_day") is not None:
                # Use iTrip's determination - it takes precedence
                res["same_day_turnover"] = res["itrip_same_day"]
            else:
                # Calculate same-day turnover locally for non-iTrip or when not specified
                checkout_date = parse(res["dtend_iso"]).date()
                checkin_date = parse(res["dtstart_iso"]).date()
                
                # If checkout date equals another reservation's check-in date (and not its own)
                if checkout_date in checkin_dates and checkout_date != checkin_date:
                    res["same_day_turnover"] = True

# ---------------------------------------------------------------------------
# Fetch Airtable Data
# ---------------------------------------------------------------------------
def build_property_lookup(properties_table):
    """Build a simplified property lookup dictionary"""
    property_lookup = {}
    id_to_name = {}  # Will store all property IDs to names for reporting
    
    for rec in properties_table.all(fields=["Property Name"]):
        name = rec["fields"].get("Property Name", "").strip()
        rid = rec["id"]
        if not name:
            continue
        
        # Store direct name mapping (lowercase for case-insensitive matching)
        property_lookup[name.lower()] = rid
        
        # Also store in reverse mapping (for reporting)
        id_to_name[rid] = name  # Store the original name, not lowercase
        
        # If name contains a listing number after "#", extract for direct lookup
        if "#" in name:
            listing_number = name.split("#")[-1].strip().split()[0]
            property_lookup[listing_number] = rid
    
    logging.info(f"Loaded {len(property_lookup)} property mappings")
    return property_lookup, id_to_name

def build_guest_overrides(overrides_table):
    """Build guest name -> property override mappings"""
    overrides = {}
    
    try:
        # Fetch all active overrides
        formula = "{Active} = TRUE()"
        records = overrides_table.all(
            formula=formula,
            fields=["Guest Name Pattern", "Original Property", "Override Property"]
        )
        
        for rec in records:
            fields = rec["fields"]
            pattern = fields.get("Guest Name Pattern", "").strip().lower()
            original_props = fields.get("Original Property", [])
            override_props = fields.get("Override Property", [])
            
            if pattern and original_props and override_props:
                # Store mapping: (original_property_id, guest_pattern) -> override_property_id
                for orig_id in original_props:
                    key = (orig_id, pattern)
                    overrides[key] = override_props[0]  # Use first override property
                    logging.debug(f"Loaded override: guest pattern '{pattern}' on property {orig_id} -> {override_props[0]}")
        
        logging.info(f"Loaded {len(overrides)} guest override mappings")
    except Exception as e:
        logging.warning(f"Could not load guest overrides: {e}")
        # Return empty dict if table doesn't exist or has issues
    
    return overrides

def fetch_all_reservations(table, feed_urls):
    """
    Fetch ALL reservations for the feed URLs we're processing, 
    including New, Modified, and Old status.
    Group by UID and feed URL for easy access.
    """
    if not feed_urls:
        return {}
    
    # Group records by UID + feed_url
    by_uid_feed = defaultdict(list)
    
    try:
        # Create a formula to fetch all reservations for these feed URLs
        url_conditions = [f"{{ICS URL}}='{url}'" for url in feed_urls]
        
        # Print the formula for debugging
        formula = f"OR({','.join(url_conditions)})"
        logging.info(f"Using Airtable formula: {formula}")
        
        fields = [
            "Reservation UID", "ICS URL", "Check-in Date", "Check-out Date",
            "Status", "Entry Type", "Service Type", "Entry Source",
            "Property ID", "Last Updated",
            "Overlapping Dates", "Same-day Turnover", "iTrip Report Info"
        ]  # Removed HCP_FIELDS to avoid API errors with non-existent fields
        
        # Fetch records with minimal filtering to see if we get any results
        records = table.all(fields=fields, formula=formula)
        
        # Group by UID and feed URL
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
        
    except Exception as e:
        # Log detailed error information
        logging.error(f"Error fetching records from Airtable: {e}", exc_info=True)
        logging.error(f"Feed URLs: {feed_urls}")
    
    return dict(by_uid_feed)

# ---------------------------------------------------------------------------
# Compare and Sync Functions
# ---------------------------------------------------------------------------
def has_changes(csv_record, airtable_record):
    """Carefully detect if any important fields have changed"""
    
    # Get fields from Airtable record
    at_fields = airtable_record["fields"]
    
    # 1. Check dates (normalize to MM/DD/YYYY for comparison)
    at_checkin = normalize_date_for_comparison(at_fields.get("Check-in Date", ""))
    at_checkout = normalize_date_for_comparison(at_fields.get("Check-out Date", ""))
    
    csv_checkin = csv_record["dtstart"]  # Already in MM/DD/YYYY
    csv_checkout = csv_record["dtend"]   # Already in MM/DD/YYYY
    
    if at_checkin != csv_checkin or at_checkout != csv_checkout:
        logging.info(f"Dates changed for {csv_record['uid']}: "
                    f"Check-in: {at_checkin} -> {csv_checkin}, "
                    f"Check-out: {at_checkout} -> {csv_checkout}")
        return True
    
    # 2. Check property link
    at_property_links = at_fields.get("Property ID", [])
    at_property_id = at_property_links[0] if at_property_links else None
    
    if at_property_id != csv_record["property_id"]:
        logging.info(f"Property changed for {csv_record['uid']}: "
                    f"{at_property_id} -> {csv_record['property_id']}")
        return True
    
    # 3. Check flags
    at_overlap = convert_flag_value(at_fields.get("Overlapping Dates"))
    at_sameday = convert_flag_value(at_fields.get("Same-day Turnover"))
    
    csv_overlap = csv_record["overlapping"]
    csv_sameday = csv_record["same_day_turnover"]
    
    if at_overlap != csv_overlap or at_sameday != csv_sameday:
        logging.info(f"Flags changed for {csv_record['uid']}: "
                    f"Overlap: {at_overlap} -> {csv_overlap}, "
                    f"Same-day: {at_sameday} -> {csv_sameday}")
        return True
    
    # No important changes detected
    return False

def check_for_duplicate(table, property_id, checkin_date, checkout_date, entry_type, session_tracker=None):
    """Check if a record with the same property, dates, and type already exists.
    
    Args:
        table: Airtable table object
        property_id: Property record ID
        checkin_date: Check-in date string
        checkout_date: Check-out date string  
        entry_type: 'Reservation' or 'Block'
        session_tracker: Dict tracking records created in current session
    
    Returns:
        bool: True if duplicate exists (in session or Airtable), False otherwise
    """
    # First check session tracker for duplicates created in this run
    if session_tracker is not None:
        key = (property_id, checkin_date, checkout_date, entry_type)
        if key in session_tracker:
            logging.info(f"Found duplicate in session: Property {property_id}, {checkin_date} to {checkout_date}, Type: {entry_type}")
            return True
    
    # Then check Airtable for existing records
    try:
        # Build formula to find exact matches
        formula = (
            f"AND("
            f"{{Property ID}} = '{property_id}', "
            f"{{Check-in Date}} = '{checkin_date}', "
            f"{{Check-out Date}} = '{checkout_date}', "
            f"{{Entry Type}} = '{entry_type}', "
            f"OR({{Status}} = 'New', {{Status}} = 'Modified')"
            f")"
        )
        
        # Check if any matching records exist
        records = table.all(formula=formula, max_records=1)
        
        if records:
            logging.info(f"Found duplicate in Airtable: Property {property_id}, {checkin_date} to {checkout_date}, Type: {entry_type}")
            return True
        return False
    except Exception as e:
        logging.warning(f"Error checking for duplicate: {e}")
        return False

def sync_reservations(csv_reservations, all_reservation_records, table, session_tracker=None):
    """Synchronize CSV data with Airtable following a simple logical approach:
    1. Pull all active records from iTrip/Evolve with checkin >= today
    2. Process CSV files to identify new/modified/removed reservations
    3. Apply the appropriate action for each category
    MODIFIED: Tracks duplicate detections and prevents false removals.
    
    Args:
        csv_reservations: List of reservation dicts from CSV files
        all_reservation_records: Dict of existing Airtable records
        table: Airtable table object
        session_tracker: Set tracking records created in current session
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
    
    # STEP 3: Create maps for faster lookups
    # Map Airtable records by (uid, feed_url)
    # IMPORTANT: Include ALL records, not just active ones, to prevent duplicate creation
    airtable_map = {}
    for key, records in all_reservation_records.items():
        if records:
            # Get the most recent record regardless of status
            latest = max(records, key=lambda r: r["fields"].get("Last Updated", ""))
            airtable_map[key] = latest
            
            # IMPORTANT: Also map by base UID if this is a composite UID
            # This ensures we find records regardless of how they're looked up
            uid, feed_url = key
            if '_' in uid and uid.count('_') == 1:
                base_uid, prop_suffix = uid.rsplit('_', 1)
                if prop_suffix.startswith('rec'):  # Airtable record ID format
                    base_key = (base_uid, feed_url)
                    if base_key not in airtable_map:  # Don't overwrite if base key already exists
                        airtable_map[base_key] = latest
                        logging.debug(f"Also mapped composite UID {uid} under base UID {base_uid}")
    
    # STEP 4: Calculate overlaps PROPERTY BY PROPERTY
    # (This ensures we consider all reservations for a property)
    for property_id, property_reservations in by_property.items():
        # Reset all flags first
        for res in property_reservations:
            res["overlapping"] = False
            res["same_day_turnover"] = False
        
        # Calculate overlaps for this property
        for a, b in combinations(property_reservations, 2):
            a_start = parse(a["dtstart_iso"]).date()
            a_end = parse(a["dtend_iso"]).date()
            b_start = parse(b["dtstart_iso"]).date()
            b_end = parse(b["dtend_iso"]).date()
            
            # Check for overlap: a starts before b ends AND a ends after b starts
            if a_start < b_end and a_end > b_start:
                a["overlapping"] = True
                b["overlapping"] = True
        
        # Calculate same-day turnovers
        checkin_dates = {parse(res["dtstart_iso"]).date() for res in property_reservations}
        
        for res in property_reservations:
            checkout_date = parse(res["dtend_iso"]).date()
            checkin_date = parse(res["dtstart_iso"]).date()
            
            # If checkout date equals another reservation's check-in date (and not its own)
            if checkout_date in checkin_dates and checkout_date != checkin_date:
                res["same_day_turnover"] = True
    
    # STEP 5: Process each reservation
    create_batch = BatchCollector(table, op="create")
    update_batch = BatchCollector(table, op="update")
    
    processed_uids = set()
    summary = defaultdict(list)
    created_count = updated_count = unchanged_count = removed_count = 0
    
    for res in csv_reservations:
        uid = res["uid"]
        feed_url = res["feed_url"]
        
        # Try to find existing records - check base UID first to catch ANY existing record
        original_key = (uid, feed_url)
        composite_key = (f"{uid}_{res['property_id']}", feed_url) if res.get('property_id') else None
        
        # IMPORTANT: Check base UID first to find ALL possible matches
        all_records = all_reservation_records.get(original_key, [])
        if all_records:
            # Found records with base UID - ANY existing record means this reservation exists
            # Get the actual UID from the most recent record (regardless of status)
            most_recent = max(all_records, key=lambda r: r["fields"].get("Last Updated", ""))
            existing_uid = most_recent["fields"].get("Reservation UID", uid)
            
            if existing_uid != uid:
                # The existing record has a composite UID
                key = (existing_uid, feed_url)
                logging.info(f"🔍 Found existing records for {uid} using base UID lookup, actual UID is {existing_uid}")
            else:
                key = original_key
                logging.info(f"🔍 Found existing records for {uid} using base UID")
                
            # Update all_records to use the correct key
            if key != original_key and key in all_reservation_records:
                all_records = all_reservation_records[key]
        elif composite_key and composite_key in all_reservation_records:
            # No base UID match, but found composite match
            all_records = all_reservation_records[composite_key]
            key = composite_key
            logging.info(f"🔍 Found existing records for {uid} using composite key")
        else:
            # No existing records found
            all_records = []
            key = composite_key if composite_key else original_key
            logging.info(f"🔍 No existing records found for {uid} (tried both base and composite)")
        
        processed_uids.add(key)
        
        # Is this a new or existing reservation?
        if key in airtable_map:
            # EXISTING reservation - check for changes
            airtable_record = airtable_map[key]
            at_fields = airtable_record["fields"]
            
            # IMPORTANT: Check if this UID is trying to create a duplicate
            # This handles cases where CSV has same reservation with different UIDs
            at_property_links = at_fields.get("Property ID", [])
            at_property_id = at_property_links[0] if at_property_links else None
            
            # If the property ID doesn't match, check if we'd be creating a duplicate
            if at_property_id != res["property_id"] and res["property_id"] and check_for_duplicate(
                table, 
                res["property_id"], 
                res["dtstart"], 
                res["dtend"], 
                res["entry_type"],
                session_tracker
            ):
                logging.info(f"Ignoring duplicate: UID {uid} would create duplicate for property {res['property_id']}")
                unchanged_count += 1
                
                # Track this duplicate detection
                duplicate_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                duplicate_detected_dates.add(duplicate_key)
                
                # Add to summary as duplicate ignored
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "old": "-",
                    "new": "Duplicate_Ignored",
                    "cin": res["dtstart"],
                    "cout": res["dtend"],
                    "overlap": res["overlapping"],
                    "sameday": res["same_day_turnover"],
                    "entry_type": res["entry_type"],
                    "property_address": res.get("property_address", ""),
                    "modified": False
                })
                continue
            
            # Compare critical fields
            at_checkin = normalize_date_for_comparison(at_fields.get("Check-in Date", ""))
            at_checkout = normalize_date_for_comparison(at_fields.get("Check-out Date", ""))
            at_property_links = at_fields.get("Property ID", [])
            at_property_id = at_property_links[0] if at_property_links else None
            at_overlap = convert_flag_value(at_fields.get("Overlapping Dates"))
            at_sameday = convert_flag_value(at_fields.get("Same-day Turnover"))
            at_entry_type = at_fields.get("Entry Type", "")
            at_service_type = at_fields.get("Service Type", "")
            at_itrip_info = at_fields.get("iTrip Report Info", "")
            
            # Check if anything important changed
            dates_changed = (at_checkin != res["dtstart"] or at_checkout != res["dtend"])
            property_changed = (at_property_id != res["property_id"])
            flags_changed = (at_overlap != res["overlapping"] or at_sameday != res["same_day_turnover"])
            entry_type_changed = (at_entry_type != res["entry_type"])
            service_type_changed = (at_service_type != res["service_type"])
            # REMOVED: itrip_info_changed - don't track contractor info changes
            
            if dates_changed or property_changed or flags_changed or entry_type_changed or service_type_changed:
                # Something changed - create modified record
                new_fields = {
                    "Check-in Date": res["dtstart"],
                    "Check-out Date": res["dtend"],
                    "Entry Type": res["entry_type"],  # Add this line
                    "Service Type": res["service_type"],  # Add this line
                    "Overlapping Dates": res["overlapping"],
                    "Same-day Turnover": res["same_day_turnover"],
                    "Property ID": [res["property_id"]]
                }
                # Add iTrip Report Info if from iTrip and has contractor info
                if res["entry_source"] == "iTrip" and res.get("contractor_info"):
                    new_fields["iTrip Report Info"] = res["contractor_info"]
                # Add Block Type if it exists
                if res.get("block_type"):
                    new_fields["Block Type"] = res["block_type"]
                # Log what changed with detailed comparison
                if dates_changed:
                    logging.info(f"🔍 DATES CHANGED for {uid}: "
                                f"Check-in: '{at_checkin}' vs '{res['dtstart']}', "
                                f"Check-out: '{at_checkout}' vs '{res['dtend']}'")
                if property_changed:
                    logging.info(f"🔍 PROPERTY CHANGED for {uid}: "
                                f"'{at_property_id}' vs '{res['property_id']}'")
                if flags_changed:
                    logging.info(f"🔍 FLAGS CHANGED for {uid}: "
                                f"Overlap: {at_overlap} ({type(at_overlap)}) vs {res['overlapping']} ({type(res['overlapping'])}), "
                                f"Same-day: {at_sameday} ({type(at_sameday)}) vs {res['same_day_turnover']} ({type(res['same_day_turnover'])})")
                if entry_type_changed:
                    logging.info(f"🔍 ENTRY TYPE CHANGED for {uid}: "
                                f"'{at_entry_type}' vs '{res['entry_type']}'")
                if service_type_changed:
                    logging.info(f"🔍 SERVICE TYPE CHANGED for {uid}: "
                                f"'{at_service_type}' vs '{res['service_type']}'")
                # REMOVED: itrip_info_changed logging since we no longer track it
                
                # Mark as old and create new record
                mark_all_as_old_and_clone(table, all_records, new_fields, now_iso, "Modified")
                updated_count += 1
                
                # Add to summary
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "old": "-",
                    "new": "Modified",
                    "cin": res["dtstart"],
                    "cout": res["dtend"],
                    "overlap": res["overlapping"],
                    "sameday": res["same_day_turnover"],
                    "entry_type": res["entry_type"],  # Make sure this is included
                    "property_address": res.get("property_address", ""),  # Include address
                    "modified": True
                })
            else:
                # No changes - don't update Airtable at all
                unchanged_count += 1
                
                # Add to summary
                # ⬇️ FIXED: mark record as UNCHANGED, not “New/modified”
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid"     : uid,
                    "old"     : "-",
                    "new"     : "Unchanged",     # ← was "New"
                    "cin"     : res["dtstart"],
                    "cout"    : res["dtend"],
                    "overlap" : res["overlapping"],
                    "sameday" : res["same_day_turnover"],
                    "entry_type"      : res["entry_type"],
                    "property_address": res.get("property_address", ""),
                    "modified": False            # ← was True
                })
        else:
            # NEW reservation - but first check if it's a duplicate with different UID
            # This prevents creating duplicates when CSV contains same reservation with different UIDs
            logging.info(f"🔍 Processing NEW reservation {uid} for property {res.get('property_id', 'None')}")
            
            if res["property_id"] and check_for_duplicate(
                table, 
                res["property_id"], 
                res["dtstart"], 
                res["dtend"], 
                res["entry_type"],
                session_tracker
            ):
                logging.info(f"Ignoring duplicate event: {uid} for property {res['property_id']}")
                # Track as unchanged since we're not creating it
                unchanged_count += 1
                
                # Track this duplicate detection
                duplicate_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                duplicate_detected_dates.add(duplicate_key)
                
                # Add to summary as duplicate ignored
                summary_key = (res["entry_source"], res["property_id"])
                summary[summary_key].append({
                    "uid": uid,
                    "old": "-",
                    "new": "Duplicate_Ignored",
                    "cin": res["dtstart"],
                    "cout": res["dtend"],
                    "overlap": res["overlapping"],
                    "sameday": res["same_day_turnover"],
                    "entry_type": res["entry_type"],
                    "property_address": res.get("property_address", ""),
                    "modified": False
                })
                continue
            
            # Create composite UID for new records
            if res["property_id"]:
                composite_uid = f"{uid}_{res['property_id']}"
            else:
                composite_uid = uid
            
            # NEW reservation - create it with composite UID
            new_fields = {
                "Reservation UID": composite_uid,  # Use composite UID
                "ICS URL": res["feed_url"],
                "Check-in Date": res["dtstart"],
                "Check-out Date": res["dtend"],
                "Status": "New",
                "Entry Type": res["entry_type"],
                "Service Type": res["service_type"],
                "Entry Source": res["entry_source"],
                "Last Updated": now_iso,
                "Overlapping Dates": res["overlapping"],
                "Same-day Turnover": res["same_day_turnover"],
            }
            # Add iTrip Report Info if from iTrip and has contractor info
            if res["entry_source"] == "iTrip" and res.get("contractor_info"):
                new_fields["iTrip Report Info"] = res["contractor_info"]
            # Add Block Type if it exists
            if res.get("block_type"):
                new_fields["Block Type"] = res["block_type"]

            if res["property_id"]:
                new_fields["Property ID"] = [res["property_id"]]
            
            # Mark any existing ACTIVE records as Old (don't re-mark already-Old records)
            if all_records:
                active_to_mark = [r for r in all_records if r["fields"].get("Status") in ("New", "Modified")]
                for record in active_to_mark:
                    update_batch.add({
                        "id": record["id"],
                        "fields": {"Status": "Old", "Last Updated": now_iso}
                    })
                if active_to_mark:
                    logging.info(f"🔍 Marking {len(active_to_mark)} active records as Old for new reservation {uid}")
                else:
                    logging.info(f"🔍 No active records to mark as Old for new reservation {uid}")
            
            # Create the new record
            create_batch.add({"fields": new_fields})
            created_count += 1
            
            # Track in session to prevent duplicates in this run
            if session_tracker is not None and res["property_id"]:
                tracker_key = (res["property_id"], res["dtstart"], res["dtend"], res["entry_type"])
                session_tracker.add(tracker_key)
            
            # Add to summary
            summary_key = (res["entry_source"], res["property_id"])
            summary[summary_key].append({
                "uid"     : uid,
                "old"     : "-",
                "new"     : "New",
                "cin"     : res["dtstart"],
                "cout"    : res["dtend"],
                "overlap" : res["overlapping"],
                "sameday" : res["same_day_turnover"],
                "entry_type"      : res["entry_type"],
                "property_address": res.get("property_address", ""),
                "modified": False
            })
    
    # STEP 6: Handle removals (in Airtable but not in CSV)
    for (uid, feed_url), records in all_reservation_records.items():
        # Check if this record was processed using either composite or original UID
        was_processed = (uid, feed_url) in processed_uids
        
        # For composite UIDs, also check if the base UID was processed
        if not was_processed and '_' in uid and uid.count('_') == 1:
            base_uid = uid.rsplit('_', 1)[0]
            was_processed = (base_uid, feed_url) in processed_uids
        
        if not was_processed:
            logging.info(f"🔍 Found unprocessed record for removal: {uid}")
            # Get active records that need to be removed
            active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
            
            if active_records:
                latest = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
                fields = latest["fields"]
                
                # Get check-in date
                checkin = fields.get("Check-in Date", "")
                checkin_iso = normalize_date_for_comparison(checkin)
                
                try:
                    checkin_date = parse(checkin_iso).date().isoformat()
                    
                    # Only remove future reservations (checkin >= today)
                    if checkin_date >= today:
                        # NEW: Check if this record matches a duplicate that was detected
                        # If so, don't mark it as removed - it's the same reservation with a different UID
                        property_links = fields.get("Property ID", [])
                        if property_links:
                            record_property_id = property_links[0]
                            record_checkin = normalize_date_for_comparison(fields.get("Check-in Date", ""))
                            record_checkout = normalize_date_for_comparison(fields.get("Check-out Date", ""))
                            record_entry_type = fields.get("Entry Type", "")
                            
                            duplicate_key = (record_property_id, record_checkin, record_checkout, record_entry_type)
                            if duplicate_key in duplicate_detected_dates:
                                logging.info(f"Skipping removal of {uid} - same reservation detected with different UID")
                                continue
                        
                        # Mark as removed
                        mark_all_as_old_and_clone(table, records, {}, now_iso, "Removed")
                        removed_count += 1
                        
                        # Add to summary
                        prop_links = fields.get("Property ID", [])
                        prop_id = prop_links[0] if prop_links else None
                        entry_source = fields.get("Entry Source", "Unknown")
                        
                        if prop_id:
                            summary_key = (entry_source, prop_id)
                            summary[summary_key].append({
                                "uid": uid,
                                "old": fields.get("Status", "-"),
                                "new": "Removed",
                                "cin": fields.get("Check-in Date", "-"),
                                "cout": fields.get("Check-out Date", "-"),
                                "overlap": convert_flag_value(fields.get("Overlapping Dates")),
                                "sameday": convert_flag_value(fields.get("Same-day Turnover")),
                                "modified": True
                            })
                except Exception:
                    logging.warning(f"Couldn't parse dates for removal check on record {uid}")
    
    # Finalize batch operations
    update_batch.flush()
    create_batch.flush()
    
    updated_count += update_batch.count
    created_count += create_batch.count
    
    return {
        "created": created_count,
        "updated": updated_count, 
        "unchanged": unchanged_count,
        "removed": removed_count,
        "summary": summary
    }
# ---------------------------------------------------------------------------
# Generate Report
# ---------------------------------------------------------------------------
def generate_report(results, id_to_name):
    """Generate detailed and summary reports"""
    summary = results["summary"]
    
    # Skip if no reservations processed
    if not summary:
        logging.info("No reservations processed.")
        return
    

    
    # Log run digest (only goes to log file due to filter)
    logging.info("------------  Run digest  ------------")
    
    # Process all properties and collect stats
    for (entry_src, prop_id), rows in summary.items():
        # Get property name, use property ID if name not found
        prop_name = id_to_name.get(prop_id, str(prop_id))
        
        # Find property address (use first non-empty address found for this property)
        prop_address = "Address not available"
        for row in rows:
            if row.get("property_address"):
                prop_address = row.get("property_address")
                break
        
        # Separate blocks and reservations
        blocks = [r for r in rows if r.get("entry_type") == "Block"]
        reservations = [r for r in rows if r.get("entry_type") != "Block"]
        
        # Count by status for blocks
        blocks_new       = [r for r in blocks if r["new"] == "New"]
        blocks_modified  = [r for r in blocks if r["new"] == "Modified"]
        blocks_removed   = [r for r in blocks if r["new"] == "Removed"]
        blocks_unchanged = [r for r in blocks if r["new"] == "Unchanged"]
                
        # Count by status for reservations
        res_new       = [r for r in reservations if r["new"] == "New"]
        res_modified  = [r for r in reservations if r["new"] == "Modified"]
        res_removed   = [r for r in reservations if r["new"] == "Removed"]
        res_unchanged = [r for r in reservations if r["new"] == "Unchanged"]
        
        target_blk = itrip_blocks  if entry_src.lower() == "itrip"  else evolve_blocks
        target_res = itrip_reserv  if entry_src.lower() == "itrip"  else evolve_reserv

        target_blk["unchanged"] += len(blocks_unchanged)
        target_blk["new"]       += len(blocks_new)
        target_blk["modified"]  += len(blocks_modified)
        target_blk["removed"]   += len(blocks_removed)
        target_blk["total"]     += len(blocks)

        target_res["unchanged"] += len(res_unchanged)
        target_res["new"]       += len(res_new)
        target_res["modified"]  += len(res_modified)
        target_res["removed"]   += len(res_removed)
        target_res["total"]     += len(reservations)
        
        # Log detailed property information
        header = f"Entry Source -> {entry_src} Property -> {prop_name} Address -> {prop_address}"
        logging.info(header)
        
        # Log counts with both reservations and blocks
        logging.info(f" * New: {len(res_new)} reservations and {len(blocks_new)} blocks")
        logging.info(f" * Modified: {len(res_modified)} reservations and {len(blocks_modified)} blocks")
        logging.info(f" * Unchanged: {len(res_unchanged)} reservations and {len(blocks_unchanged)} blocks")
        logging.info(f" * Removed: {len(res_removed)} reservations and {len(blocks_removed)} blocks")

    # ----------  iTrip Blocks Summary  ----------
    logging.info("------------  iTrip Blocks Summary  ------------")
    for k in ("unchanged", "new", "modified", "removed", "total"):
        logging.info(f"Total {k}: {itrip_blocks[k]}")

    # ----------  Evolve Blocks Summary (Tab2) ----------
    logging.info("------------  Evolve Blocks Summary  ------------")
    logging.info(f"Total unchanged: {tab2_global['unchanged']}")
    logging.info(f"Total new      : {tab2_global['new']}")
    logging.info(f"Total modified : {tab2_global['modified']}")
    logging.info(f"Total removed  : {tab2_global['removed']}")
    logging.info(f"Total blocks processed: "
                f"{tab2_global['unchanged'] + tab2_global['new'] + tab2_global['modified'] + tab2_global['removed']}")

    # ----------  Reservations Summary  ----------
    def _dump(label, d):
        logging.info(f"{label:<7}  unchanged:{d['unchanged']:>4}  new:{d['new']:>4}  "
                    f"modified:{d['modified']:>4}  removed:{d['removed']:>4}  total:{d['total']:>4}")

    logging.info("------------  Reservations Summary  ------------")
    _dump("iTrip",   itrip_reserv)
    _dump("Evolve",  evolve_reserv)

    total_blocks = itrip_blocks['total'] + tab2_global['unchanged'] \
            + tab2_global['new'] + tab2_global['modified'] + tab2_global['removed']

    total_reserv = itrip_reserv['total'] + evolve_reserv['total']
    total_processed = total_blocks + total_reserv
    # Print summary (will go to both console and log file)
    # place this just **before** the final "End Summary" block

    total_unchanged = itrip_blocks['unchanged'] \
                    + tab2_global['unchanged'] \
                    + itrip_reserv['unchanged'] + evolve_reserv['unchanged']

    total_new       = itrip_blocks['new'] \
                    + tab2_global['new'] \
                    + itrip_reserv['new'] + evolve_reserv['new']

    total_modified  = itrip_blocks['modified'] \
                    + tab2_global['modified'] \
                    + itrip_reserv['modified'] + evolve_reserv['modified']

    total_removed   = itrip_blocks['removed'] \
                    + tab2_global['removed'] \
                    + itrip_reserv['removed'] + evolve_reserv['removed']

    logging.info("------------  End Summary  ------------")
    logging.info(f"Total unchanged: {total_unchanged}")
    logging.info(f"Total new: {total_new}")
    logging.info(f"Total modified: {total_modified}")
    logging.info(f"Total removed: {total_removed}")
    logging.info(f"Total records processed: {total_processed}")

# ---------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------
def apply_date_filter(reservations):
    """Filter reservations to those within our date window"""
    today = date.today()
    lookback = today - relativedelta(months=MONTHS_LOOKBACK)
    lookahead = today + relativedelta(months=MONTHS_LOOKAHEAD)
    
    # Count before filtering
    blocks_before = sum(1 for res in reservations if res["entry_type"] == "Block")
    reservations_before = len(reservations) - blocks_before
    
    logging.info(f"Filtering reservations to range: {lookback.isoformat()} to {lookahead.isoformat()}")
    
    filtered = []
    for res in reservations:
        try:
            checkin_date = parse(res["dtstart_iso"]).date()
            # Keep if check-in date is within our range
            if checkin_date >= lookback and checkin_date <= lookahead:
                filtered.append(res)
        except Exception:
            continue
    
    # Count after filtering
    blocks_after = sum(1 for res in filtered if res["entry_type"] == "Block")
    reservations_after = len(filtered) - blocks_after
    
    logging.info(f"After date filtering: {reservations_after} of {reservations_before} reservations and {blocks_after} of {blocks_before} blocks kept")
    
    # Add total filtered count
    total_before = len(reservations)
    total_after = len(filtered)
    logging.info(f"Total filtered: {total_after} of {total_before} records kept ({total_before - total_after} filtered out)")
    
    return filtered

# ---------------------------------------------------------------------------
# EVOLVE BLOCK PROCESS
# ---------------------------------------------------------------------------
def build_guest_to_property_map(properties_table):
    """
    Query the Properties table for Entry Source = "Evolve" and return
    a dict mapping each Full Name → Property record ID and name.
    """
    guest_to_prop = {}
    
    # Get all Evolve properties
    formula = "{Entry Source (from ICS Feeds)} = 'Evolve'"
    records = properties_table.all(
        formula=formula,
        fields=["Full Name (from HCP Customer ID)", "Property Name"]
    )
    
    logging.info(f"Found {len(records)} Evolve properties in Properties table")
    
    for rec in records:
        prop_name = rec["fields"].get("Property Name", "Unknown Property")
        names = rec["fields"].get("Full Name (from HCP Customer ID)", [])
        
        # Airtable returns a list for linked/multi-fields
        if isinstance(names, list):
            for n in names:
                if n:
                    guest_name = n.strip()
                    guest_to_prop[guest_name.lower()] = {
                        "id": rec["id"],
                        "name": prop_name
                    }
                    logging.debug(f"Mapped guest '{guest_name}' to property '{prop_name}'")
        elif isinstance(names, str) and names:
            guest_name = names.strip()
            guest_to_prop[guest_name.lower()] = {
                "id": rec["id"],
                "name": prop_name
            }
            logging.debug(f"Mapped guest '{guest_name}' to property '{prop_name}'")
    
    logging.info(f"Created {len(guest_to_prop)} guest → property mappings")
    return guest_to_prop

def process_tab2_csv(file_path, reservations_table, guest_to_prop, existing_records, session_tracker=None):
    """
    Parse one "Tab 2" CSV.  
    • Only processes rows where guest names match entries in the Properties table
    • Creates blocks for new reservations
    • Updates existing blocks when changes detected
    • Marks blocks as removed when cancelled
    • Returns True when everything finished cleanly  
    • Returns False (and leaves the file in PROCESS_DIR) on any error
    
    Args:
        file_path: Path to the CSV file
        reservations_table: Airtable table object
        guest_to_prop: Dict mapping guest names to property records
        existing_records: Dict of existing Airtable records
        session_tracker: Set tracking records created in current session
    """
    feed_url = "csv_evolve_blocks"
    now_iso_str = datetime.now(arizona_tz).isoformat(sep=" ", timespec="seconds")

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
                    composite_lookup[base_uid][prop_id].extend(records)
            else:
                # Non-composite UID - add to all properties (legacy support)
                for rec in records:
                    prop_links = rec["fields"].get("Property ID", [])
                    if prop_links:
                        composite_lookup[uid][prop_links[0]].extend([rec])

    # Track statistics
    stats = {
        "total_rows": 0,
        "skipped_no_property": 0,
        "new_blocks": 0,
        "modified_blocks": 0,
        "removed_blocks": 0,
        "unchanged_blocks": 0
    }
    
    # Track processed UIDs to avoid duplicates within the same file
    processed_uids = set()

    try:
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t"])
            except csv.Error:
                dialect = csv.get_dialect("excel")

            reader = csv.DictReader(f, dialect=dialect)
            hdr_map = normalise_headers(reader.fieldnames)

            def col(name):          # resolve column, return None if missing
                return hdr_map.get(norm(name))

            res_key = col("Reservation")
            guest_key = col("Guest Name")
            status_key = col("Status")
            checkin_key = col("Check-In")
            checkout_key = col("Check-Out")

            # Abort if any essential column is missing
            if None in (res_key, guest_key, status_key, checkin_key, checkout_key):
                logging.error(
                    f"❌ {os.path.basename(file_path)} is missing required columns "
                    f"(Reservation / Guest Name / Status / Check-In / Check-Out)"
                )
                # Return False with empty stats to match expected return signature
                return False, {"new_blocks": 0, "modified_blocks": 0, "unchanged_blocks": 0, "removed_blocks": 0}

            for row in reader:
                stats["total_rows"] += 1
                uid = row[res_key].strip()
                guest = row[guest_key].strip()
                status = row[status_key].strip().lower()
                
                try:
                    checkin_date = parse(row[checkin_key]).date()
                    checkout_date = parse(row[checkout_key]).date()
                    
                    # Format dates for Airtable
                    checkin = checkin_date.isoformat()
                    checkout = checkout_date.isoformat()
                    checkin_display = checkin_date.strftime("%m/%d/%Y")
                    checkout_display = checkout_date.strftime("%m/%d/%Y")
                except Exception as e:
                    logging.error(f"Bad dates in row {uid} ({os.path.basename(file_path)}): {e}")
                    continue

                # Look up property by guest name (case insensitive)
                prop_info = guest_to_prop.get(guest.lower())
                if not prop_info:       
                    # Guest not mapped to any property - skip this row
                    stats["skipped_no_property"] += 1
                    logging.debug(f"Skipping row with guest '{guest}' - no property mapping found")
                    continue

                prop_id = prop_info["id"]
                prop_name = prop_info["name"]
                
                # Create the composite UID for tracking
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
                            session_tracker
                        ):
                            logging.info(f"Ignoring duplicate block: {composite_uid} for property {prop_id}")
                            stats["skipped_duplicates"] = stats.get("skipped_duplicates", 0) + 1
                            continue
                        
                        # No active record exists - create a new block
                        create_batch.add({
                            "fields": {
                                "Reservation UID": composite_uid,  # Use composite UID
                                "ICS URL": feed_url,
                                "Check-in Date": checkin_display,
                                "Check-out Date": checkout_display,
                                "Status": "New",
                                "Entry Type": "Block",
                                "Service Type": "Needs Review",
                                "Entry Source": "Evolve",
                                "Property ID": [prop_id],
                                "Last Updated": now_iso_str
                            }
                        })
                        stats["new_blocks"] += 1
                        logging.debug(f"Creating new block for {composite_uid} at {prop_name}")
                        
                        # Track in session to prevent duplicates in this run
                        if session_tracker is not None:
                            tracker_key = (prop_id, checkin_display, checkout_display, "Block")
                            session_tracker.add(tracker_key)
                    else:
                        # Check if anything changed in the existing block
                        latest = max(active_records, key=lambda r: r["fields"].get("Last Updated", ""))
                        fields = latest["fields"]
                        
                        # Check for changes
                        at_checkin = normalize_date_for_comparison(fields.get("Check-in Date", ""))
                        at_checkout = normalize_date_for_comparison(fields.get("Check-out Date", ""))
                        at_property_links = fields.get("Property ID", [])
                        at_property_id = at_property_links[0] if at_property_links else None
                        
                        # Convert new dates to MM/DD/YYYY for comparison
                        new_checkin = checkin_date.strftime("%m/%d/%Y")
                        new_checkout = checkout_date.strftime("%m/%d/%Y")
                        
                        # Check if any important fields changed
                        dates_changed = (at_checkin != new_checkin or at_checkout != new_checkout)
                        property_changed = (at_property_id != prop_id)
                        
                        if dates_changed or property_changed:
                            # Something changed - create modified record
                            new_fields = {
                                "Check-in Date": checkin_display,
                                "Check-out Date": checkout_display,
                                "Entry Type": "Block",
                                "Service Type": "Needs Review",
                                "Property ID": [prop_id]
                            }
                            
                            # Mark all existing records as old and create a modified version
                            mark_all_as_old_and_clone(
                                reservations_table,
                                records,
                                new_fields,
                                now_iso_str,
                                "Modified"
                            )
                            stats["modified_blocks"] += 1
                            logging.debug(f"Modified block for {composite_uid} at {prop_name}")
                        else:
                            # No changes - don't update Airtable at all
                            stats["unchanged_blocks"] += 1
                            logging.debug(f"Unchanged block for {composite_uid} at {prop_name}")
                
                elif status == "cancelled" and active_records:
                    # Mark as removed
                    mark_all_as_old_and_clone(
                        reservations_table,
                        records,
                        {},
                        now_iso_str,
                        "Removed"
                    )
                    stats["removed_blocks"] += 1
                    logging.debug(f"Marked block as removed for {composite_uid} at {prop_name}")

        # Flush batches only if file parsed without fatal error
        create_batch.done()
        update_batch.done()
        
        # Log results
        logging.info(
            f"Tab2 CSV processed: {stats['total_rows']} rows"
            f" • {stats['new_blocks']} new blocks"
            f" • {stats['modified_blocks']} modified"
            f" • {stats['unchanged_blocks']} unchanged"
            f" • {stats['removed_blocks']} removed"
            f" • {stats.get('skipped_duplicates', 0)} skipped (duplicates)"
            f" • {stats['skipped_no_property']} skipped (no property)"
        )
        return True, stats

    except Exception as e:
        logging.error(f"Unhandled error while reading {os.path.basename(file_path)}: {e}", exc_info=True)
        return False, stats

def main():
    try:
        # Ensure folders exist
        os.makedirs(PROCESS_DIR, exist_ok=True)
        os.makedirs(DONE_DIR, exist_ok=True)
        
        # Initialize Airtable API
        api = Api(Config.get_airtable_api_key())
        base_id = Config.get_airtable_base_id()
        reservations_table = api.table(base_id, Config.get_airtable_table_name('reservations'))
        properties_table = api.table(base_id, Config.get_airtable_table_name('properties'))
        
        # Create session-wide duplicate tracker
        session_tracker = set()
        logging.info("Initialized session-wide duplicate tracker")
        
        # Try to load guest overrides table (may not exist in all environments)
        guest_overrides = {}
        try:
            overrides_table = api.table(base_id, "Property Guest Overrides")
            guest_overrides = build_guest_overrides(overrides_table)
        except Exception as e:
            logging.info("Property Guest Overrides table not found or accessible - proceeding without overrides")
        
        # ————— Evolve “Tab 2” CSV exports —————
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
                csv_file, reservations_table, guest_to_prop, existing_records, session_tracker
            )

            if ok:
                for k in ("new", "modified", "unchanged", "removed"):
                    tab2_global[k] += tab2_stats[f"{k}_blocks"]
                shutil.move(csv_file, os.path.join(DONE_DIR, fname))
                logging.info(f"✅  Moved {fname} to {DONE_DIR}")
            else:
                logging.warning(f"❌  Kept {fname} in {PROCESS_DIR} due to errors")

        # ————— end Tab 2 processing —————


        # 1. Build property lookup
        property_lookup, id_to_name = build_property_lookup(properties_table)
        
        # 2. Process all CSV files
        all_reservations, processed_paths = process_csv_files(property_lookup, guest_overrides)
        
        if not all_reservations:
            logging.info("No valid reservations found in any CSV files")
            return
        
        # 3. Apply date filters
        filtered_reservations = apply_date_filter(all_reservations)
        
        if not filtered_reservations:
            logging.info("No reservations within the date filter range")
            return
        
        # 4. Calculate overlap and same-day turnovers locally
        calculate_flags(filtered_reservations)
        
        # 5. Fetch ALL existing Airtable records (including Old)
        feed_urls = {res["feed_url"] for res in filtered_reservations}
        all_records = fetch_all_reservations(reservations_table, feed_urls)
        
        # 6. Sync reservations - properly marking ALL records as Old when creating Modified/Removed
        results = sync_reservations(filtered_reservations, all_records, reservations_table, session_tracker)
        
        # 7. Generate report
        generate_report(results, id_to_name)
        
        # 8. Move processed files
        success_count = 0
        for path in processed_paths:
            try:
                if os.path.exists(path):  # Check if file still exists
                    dest = os.path.join(DONE_DIR, os.path.basename(path))
                    shutil.move(path, dest)
                    logging.info(f"Moved {os.path.basename(path)} to {DONE_DIR}")
                    success_count += 1
                else:
                    logging.warning(f"File not found for moving: {path}")
            except Exception as e:
                logging.error(f"Error moving file {path}: {e}")

        logging.info(f"Moved {success_count} of {len(processed_paths)} processed files")
        
        # Log final completion message
        logging.info(f"Sync complete * created {results['created']} * updated {results['updated']} * "
                    f"unchanged {results['unchanged']} * removed {results['removed']}")
        
    except Exception as e:
        logging.error(f"Fatal error in main process: {e}", exc_info=True)




if __name__ == "__main__":
    main()