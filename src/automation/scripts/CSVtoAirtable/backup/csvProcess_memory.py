#!/usr/bin/env python3
"""
CSV Processor with In-Memory Collection and UID Change Detection
==============================================================
Enhanced version that collects all operations in memory before execution.
This prevents creating records then marking them old later.

Key Features:
1. Collects all operations in memory first
2. Cross-references removals with additions to detect UID changes
3. Only sends real changes to Airtable
4. Prevents duplicate creation from sources with unstable UIDs
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
import pytz
from collections import defaultdict
import csv
import os

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import configuration
from src.automation.config_wrapper import Config

# Set up logging
log_dir = Config.get_logs_dir()
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"csv_sync_{Config.environment}_memory.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class InMemoryCollector:
    """Collects all operations in memory before execution."""
    
    def __init__(self):
        self.to_create = []
        self.to_update = []
        self.to_remove = []
        self.existing_records = {}
        self.processed_uids = set()
        self.property_mapping = {}
        
    def add_create(self, uid, data):
        """Add a create operation."""
        self.to_create.append({
            'uid': uid,
            'data': data,
            'property_id': data['Property ID'][0] if data['Property ID'] else None,
            'checkin': data['Check-in Date'],
            'checkout': data['Check-out Date'],
            'entry_type': data['Entry Type']
        })
        self.processed_uids.add(uid)
        
    def add_update(self, record_id, data):
        """Add an update operation."""
        self.to_update.append({
            'record_id': record_id,
            'data': data,
            'property_id': data['Property ID'][0] if data['Property ID'] else None,
            'checkin': data['Check-in Date'],
            'checkout': data['Check-out Date'],
            'entry_type': data['Entry Type']
        })
        
    def add_remove(self, record):
        """Add a remove operation."""
        fields = record['fields']
        self.to_remove.append({
            'record': record,
            'uid': fields.get('Reservation UID', ''),
            'property_id': fields.get('Property ID', [None])[0],
            'checkin': fields.get('Check-in Date', ''),
            'checkout': fields.get('Check-out Date', ''),
            'entry_type': fields.get('Entry Type', '')
        })
        
    def cross_reference_operations(self):
        """Cross-reference removals with additions to detect UID changes."""
        
        logger.info("=" * 80)
        logger.info("🔍 CROSS-REFERENCING OPERATIONS FOR UID CHANGES")
        logger.info("=" * 80)
        
        # Build lookup for removals by property/dates/type
        removal_lookup = defaultdict(list)
        for removal in self.to_remove:
            key = (
                removal['property_id'],
                removal['checkin'],
                removal['checkout'],
                removal['entry_type']
            )
            removal_lookup[key].append(removal)
        
        # Check each addition against removals
        uid_changes_detected = []
        filtered_creates = []
        filtered_removes = []
        
        for create in self.to_create:
            key = (
                create['property_id'],
                create['checkin'],
                create['checkout'],
                create['entry_type']
            )
            
            # Check if there's a removal for the same property/dates/type
            matching_removals = removal_lookup.get(key, [])
            
            if matching_removals:
                # UID change detected!
                for removal in matching_removals:
                    uid_changes_detected.append({
                        'old_uid': removal['uid'],
                        'new_uid': create['uid'],
                        'property': self.property_mapping.get(create['property_id'], create['property_id']),
                        'dates': f"{create['checkin']} to {create['checkout']}",
                        'type': create['entry_type']
                    })
                    filtered_removes.append(removal)
                    
                prop_name = self.property_mapping.get(create['property_id'], 'Unknown')
                logger.info(f"🔄 UID CHANGE DETECTED: {prop_name}")
                logger.info(f"   Dates: {create['checkin']} to {create['checkout']}")
                logger.info(f"   Old UID: {matching_removals[0]['uid']}")
                logger.info(f"   New UID: {create['uid']}")
            else:
                # No UID change, keep the create
                filtered_creates.append(create)
        
        # Filter out matched removals
        removal_ids_to_skip = {r['record']['id'] for r in filtered_removes}
        filtered_removes_final = [
            r for r in self.to_remove 
            if r['record']['id'] not in removal_ids_to_skip
        ]
        
        # Log statistics
        logger.info("\n📊 UID CHANGE DETECTION SUMMARY:")
        logger.info(f"   Original creates: {len(self.to_create)}")
        logger.info(f"   Original removes: {len(self.to_remove)}")
        logger.info(f"   UID changes detected: {len(uid_changes_detected)}")
        logger.info(f"   Filtered creates: {len(filtered_creates)}")
        logger.info(f"   Filtered removes: {len(filtered_removes_final)}")
        
        # Update operations
        self.to_create = filtered_creates
        self.to_remove = filtered_removes_final
        
        return uid_changes_detected

def load_property_mapping(properties_table):
    """Load property lookup mapping (name/listing -> record ID)."""
    property_lookup = {}
    id_to_name = {}
    
    for page in properties_table.iterate(page_size=100, fields=['Property Name', 'Street 1', 'City', 'State']):
        for record in page:
            fields = record['fields']
            name = fields.get('Property Name', '').strip()
            rid = record['id']
            
            if not name:
                continue
            
            # Store direct name mapping (lowercase for case-insensitive matching)
            property_lookup[name.lower()] = rid
            
            # For Evolve properties, the name IS the listing number
            property_lookup[name] = rid  # Also store exact case
            
            # Build human-readable name for logging
            street = fields.get('Street 1', '')
            city = fields.get('City', '')
            state = fields.get('State', '')
            if street and city:
                display_name = f"{street}, {city}, {state}" if state else f"{street}, {city}"
            else:
                display_name = name
            
            # Store in reverse mapping for display
            id_to_name[rid] = display_name
    
    logger.info(f"Loaded {len(property_lookup)} property mappings")
    return property_lookup, id_to_name

def process_csv_with_memory(api, base, config):
    """Process CSV files with in-memory collection."""
    
    # Initialize collector
    collector = InMemoryCollector()
    
    # Get tables
    reservations_table = base.table('Reservations')
    properties_table = base.table('Properties')
    
    # Load property mapping
    logger.info("📋 Loading property mapping...")
    property_lookup, id_to_name = load_property_mapping(properties_table)
    collector.property_mapping = id_to_name  # For display purposes
    
    # Get CSV processing directory
    csv_dir = Config.get_csv_process_dir()
    if not csv_dir.exists():
        logger.info(f"CSV directory does not exist: {csv_dir}")
        return
    
    # Process CSV files
    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        logger.info("No CSV files to process")
        return
    
    logger.info(f"\n📊 Found {len(csv_files)} CSV files to process")
    
    # Fetch existing reservations
    logger.info("\n📊 Fetching existing reservations...")
    existing_reservations = {}
    existing_by_constraint = defaultdict(list)
    existing_by_source = defaultdict(set)
    
    for page in reservations_table.iterate(
        page_size=100,
        fields=['Reservation UID', 'Property ID', 'Check-in Date', 'Check-out Date', 
                'Entry Type', 'Status', 'Entry Source', 'ID']
    ):
        for record in page:
            fields = record['fields']
            uid = fields.get('Reservation UID', '')
            source = fields.get('Entry Source', '')
            
            if uid:
                existing_reservations[uid] = record
                
                # Track UIDs by source
                if source:
                    existing_by_source[source].add(uid)
                
                # Index by constraint for duplicate detection
                prop_ids = fields.get('Property ID', [])
                checkin = fields.get('Check-in Date', '')
                checkout = fields.get('Check-out Date', '')
                entry_type = fields.get('Entry Type', '')
                
                for prop_id in prop_ids:
                    key = (prop_id, checkin, checkout, entry_type)
                    existing_by_constraint[key].append(record)
    
    logger.info(f"Found {len(existing_reservations)} existing reservations")
    
    # Process each CSV file
    for csv_file in csv_files:
        logger.info(f"\n🔄 Processing: {csv_file.name}")
        
        # Initial source detection from filename
        initial_source = None
        if 'evolve' in csv_file.name.lower():
            initial_source = 'Evolve'
        elif 'itrip' in csv_file.name.lower():
            initial_source = 'iTrip'
        
        # Read CSV
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                rows = list(reader)
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            continue
        
        # Normalize headers for easier access
        header_map = {}
        for h in headers:
            normalized = h.lower().strip().replace(' ', '').replace('-', '')
            header_map[normalized] = h
        
        # Detect CSV format by headers
        is_evolve = False
        listing_col = None
        entry_source = initial_source  # Start with filename-based detection
        
        # Check for iTrip-specific columns to confirm format
        if 'propertyname' in header_map:
            is_evolve = False
            entry_source = 'iTrip'
        else:
            # Check for Evolve-specific columns
            for pattern in ['listing#', 'listing', 'listingnumber']:
                if pattern in header_map:
                    listing_col = header_map[pattern]
                    is_evolve = True
                    entry_source = 'Evolve'
                    break
        
        # If we still don't know, default based on columns
        if entry_source is None:
            entry_source = 'Evolve' if is_evolve else 'iTrip'
        
        feed_url = f"csv_{entry_source.lower()}"
        logger.info(f"  Detected format: {entry_source} (feed_url: {feed_url})")
        
        # Process each row
        for row in rows:
            # Generate UID based on source
            if is_evolve:
                uid = f"Evolve_{row.get('Reservation', '')}"
            else:
                uid = f"iTrip_{row.get('Reservation ID', row.get('Reservation', ''))}"
            
            # Skip if already processed in this run
            if uid in collector.processed_uids:
                continue
            
            # Parse dates
            checkin = row.get('Check-In', row.get('Checkin', ''))
            checkout = row.get('Check-Out', row.get('Checkout', ''))
            
            # Find property
            property_id = None
            
            if is_evolve and listing_col:
                # For Evolve, use the listing number
                listing_num = row.get(listing_col, '').strip()
                if listing_num:
                    property_id = property_lookup.get(listing_num) or property_lookup.get(listing_num.lower())
                    if not property_id:
                        logger.warning(f"Property not found for Evolve listing: {listing_num}")
            else:
                # For iTrip, use property name
                property_name = row.get('Property Name', '').strip()
                if property_name:
                    property_id = property_lookup.get(property_name.lower())
                    if not property_id:
                        logger.warning(f"Property not found for iTrip: {property_name}")
            
            if not property_id:
                continue
            
            # Prepare data
            data = {
                'Entry Type': 'Reservation',
                'Service Type': 'Turnover',
                'Check-in Date': checkin,
                'Check-out Date': checkout,
                'Property ID': [property_id],
                'Entry Source': entry_source,
                'Reservation UID': uid,
                'ICS URL': feed_url
            }
            
            # Guest Name is used for processing logic but not stored in Airtable
            
            # Check if exists
            if uid in existing_reservations:
                existing_record = existing_reservations[uid]
                existing_fields = existing_record['fields']
                
                # Check if modified
                if (existing_fields.get('Check-in Date') != checkin or
                    existing_fields.get('Check-out Date') != checkout):
                    
                    data['Status'] = 'Modified'
                    collector.add_update(existing_record['id'], data)
            else:
                # Check for duplicates
                constraint_key = (property_id, checkin, checkout, 'Reservation')
                duplicates = existing_by_constraint.get(constraint_key, [])
                active_duplicates = [
                    d for d in duplicates 
                    if d['fields'].get('Status') in ['New', 'Modified']
                ]
                
                if not active_duplicates:
                    data['Status'] = 'New'
                    collector.add_create(uid, data)
    
    # Find removed reservations for each source
    logger.info("\n🔍 Finding removed reservations...")
    
    for source, existing_uids in existing_by_source.items():
        # Only check CSV sources
        if source not in ['iTrip', 'Evolve']:
            continue
            
        for uid in existing_uids:
            if uid not in collector.processed_uids:
                record = existing_reservations.get(uid)
                if record and record['fields'].get('Status') not in ['Removed', 'Old']:
                    collector.add_remove(record)
    
    # Cross-reference operations
    uid_changes = collector.cross_reference_operations()
    
    # Execute operations
    logger.info("\n📤 EXECUTING OPERATIONS...")
    
    # Create new reservations
    if collector.to_create:
        logger.info(f"\n✨ Creating {len(collector.to_create)} new reservations...")
        create_data = [c['data'] for c in collector.to_create]
        # Batch create
        for i in range(0, len(create_data), 10):
            batch = create_data[i:i+10]
            reservations_table.batch_create(batch)
    
    # Update existing reservations
    if collector.to_update:
        logger.info(f"\n📝 Updating {len(collector.to_update)} reservations...")
        update_data = [
            {'id': u['record_id'], 'fields': u['data']} 
            for u in collector.to_update
        ]
        # Batch update
        for i in range(0, len(update_data), 10):
            batch = update_data[i:i+10]
            reservations_table.batch_update(batch)
    
    # Mark as removed
    if collector.to_remove:
        logger.info(f"\n🗑️ Marking {len(collector.to_remove)} reservations as removed...")
        # Update status to Removed
        remove_updates = [
            {'id': r['record']['id'], 'fields': {'Status': 'Removed'}}
            for r in collector.to_remove
        ]
        for i in range(0, len(remove_updates), 10):
            batch = remove_updates[i:i+10]
            reservations_table.batch_update(batch)
    
    # Move processed files
    logger.info("\n📁 Moving processed files...")
    done_dir = Config.get_csv_done_dir()
    done_dir.mkdir(exist_ok=True)
    
    for csv_file in csv_files:
        dest = done_dir / csv_file.name
        csv_file.rename(dest)
        logger.info(f"   Moved: {csv_file.name}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ CSV SYNC COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Files processed: {len(csv_files)}")
    logger.info(f"New reservations: {len(collector.to_create)}")
    logger.info(f"Updated reservations: {len(collector.to_update)}")
    logger.info(f"Removed reservations: {len(collector.to_remove)}")
    logger.info(f"UID changes detected: {len(uid_changes)}")
    
    if uid_changes:
        logger.info("\n🔄 UID CHANGES PREVENTED:")
        for change in uid_changes[:5]:  # Show first 5
            logger.info(f"   {change['property']} - {change['dates']}")
            logger.info(f"     Old: {change['old_uid'][:30]}...")
            logger.info(f"     New: {change['new_uid'][:30]}...")

def main():
    """Main entry point."""
    logger.info("=== CSV sync run started (MEMORY version with UID change detection) ===")
    logger.info(f"Environment: {Config.environment}")
    
    try:
        # Initialize API
        from pyairtable import Api
        api = Api(Config.get_airtable_api_key())
        base = api.base(Config.get_airtable_base_id())
        
        # Process with memory collection
        process_csv_with_memory(api, base, Config)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())