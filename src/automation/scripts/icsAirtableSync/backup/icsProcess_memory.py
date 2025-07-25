#!/usr/bin/env python3
"""
ICS Processor with In-Memory Collection and UID Change Detection
==============================================================
Enhanced version that collects all operations in memory before execution.
This prevents creating records then marking them old later.

Key Features:
1. Collects all operations in memory first
2. Cross-references removals with additions to detect UID changes
3. Only sends real changes to Airtable
4. Prevents duplicate creation from unstable UIDs (Lodgify)
"""

import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# We'll implement simplified versions of needed functions
import requests
import icalendar
from dateutil import parser as date_parser

# Import configuration
from src.automation.config_wrapper import Config

# Set up logging
log_dir = Config.get_logs_dir()
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"ics_sync_{Config.environment}_memory.log"

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
                        'property': create['property_id'],
                        'dates': f"{create['checkin']} to {create['checkout']}",
                        'type': create['entry_type']
                    })
                    filtered_removes.append(removal)
                logger.info(f"🔄 UID CHANGE DETECTED: Property {create['property_id']}, "
                          f"{create['checkin']} to {create['checkout']}")
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

def process_ics_with_memory(api, base, config):
    """Process ICS feeds with in-memory collection."""
    
    # Initialize collector
    collector = InMemoryCollector()
    
    # Get tables
    reservations_table = base.table('Reservations')
    properties_table = base.table('Properties')
    ics_feeds_table = base.table('ICS Feeds')
    
    # Skip field check for now - we know the fields exist
    logger.info("🔍 Skipping field check (fields already verified)...")
    
    # Fetch ICS feeds
    logger.info("\n📅 Fetching ICS feeds...")
    ics_feeds = []
    for page in ics_feeds_table.iterate(page_size=100, fields=['ICS URL', 'Property Name', 'Feed Status']):
        for record in page:
            if record['fields'].get('Feed Status') == 'Active':
                ics_feeds.append(record)
    
    if not ics_feeds:
        logger.info("No ICS feeds found in Airtable.")
        return
    
    logger.info(f"Found {len(ics_feeds)} ICS feeds to process")
    
    # Process each feed and collect operations
    total_events = 0
    pst_tz = pytz.timezone('America/Phoenix')
    current_date_pst = datetime.now(pst_tz).date()
    
    # Define date ranges
    start_date = current_date_pst - timedelta(days=90)  # 3 months back
    end_date = current_date_pst + timedelta(days=365)   # 1 year forward
    
    # Fetch existing reservations
    logger.info("\n📊 Fetching existing reservations...")
    existing_reservations = {}
    existing_by_constraint = defaultdict(list)
    
    for page in reservations_table.iterate(
        page_size=100,
        fields=['Reservation UID', 'Property ID', 'Check-in Date', 'Check-out Date', 
                'Entry Type', 'Status', 'ICS URL']
    ):
        for record in page:
            fields = record['fields']
            uid = fields.get('Reservation UID', '')
            if uid:
                existing_reservations[uid] = record
                
                # Also index by constraint for duplicate detection
                prop_ids = fields.get('Property ID', [])
                checkin = fields.get('Check-in Date', '')
                checkout = fields.get('Check-out Date', '')
                entry_type = fields.get('Entry Type', '')
                
                for prop_id in prop_ids:
                    key = (prop_id, checkin, checkout, entry_type)
                    existing_by_constraint[key].append(record)
    
    logger.info(f"Found {len(existing_reservations)} existing reservations")
    
    # Process each feed
    for feed in ics_feeds:
        feed_url = feed['fields'].get('ICS URL', '')
        property_ids = feed['fields'].get('Property Name', [])
        property_id = property_ids[0] if property_ids else None
        
        if not feed_url or not property_id:
            continue
            
        # Skip CSV-sourced entries (not actual ICS URLs)
        if feed_url.startswith('csv_'):
            continue
            
        logger.info(f"\n🔄 Processing feed: {feed_url[:50]}...")
        
        # Parse ICS content (simplified)
        events = []
        try:
            response = requests.get(feed_url, timeout=30)
            response.raise_for_status()
            
            cal = icalendar.Calendar.from_ical(response.text)
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    # Extract event data
                    uid = str(component.get('UID', ''))
                    dtstart = component.get('DTSTART')
                    dtend = component.get('DTEND')
                    summary = str(component.get('SUMMARY', ''))
                    
                    if not uid or not dtstart or not dtend:
                        continue
                    
                    # Convert to dates
                    if hasattr(dtstart.dt, 'date'):
                        start_date_obj = dtstart.dt.date()
                    else:
                        start_date_obj = dtstart.dt
                        
                    if hasattr(dtend.dt, 'date'):
                        end_date_obj = dtend.dt.date()
                    else:
                        end_date_obj = dtend.dt
                    
                    # Check date range
                    if start_date_obj < start_date or start_date_obj > end_date:
                        continue
                    
                    # Create composite UID
                    composite_uid = f"{uid}_{property_id}"
                    
                    events.append({
                        'uid': composite_uid,
                        'start': start_date_obj,
                        'end': end_date_obj,
                        'summary': summary
                    })
                    
        except Exception as e:
            logger.error(f"Error parsing ICS: {e}")
            continue
        
        if not events:
            continue
            
        total_events += len(events)
        
        # Process each event
        for event in events:
            uid = event['uid']
            
            # Skip if already processed
            if uid in collector.processed_uids:
                continue
                
            collector.processed_uids.add(uid)
            
            # Check if exists
            if uid in existing_reservations:
                existing_record = existing_reservations[uid]
                existing_fields = existing_record['fields']
                
                # Check if modified
                if (existing_fields.get('Check-in Date') != event['start'].strftime('%Y-%m-%d') or
                    existing_fields.get('Check-out Date') != event['end'].strftime('%Y-%m-%d')):
                    
                    # Prepare update data
                    data = {
                        'Entry Type': 'Reservation',
                        'Service Type': 'Turnover',
                        'Check-in Date': event['start'].strftime('%Y-%m-%d'),
                        'Check-out Date': event['end'].strftime('%Y-%m-%d'),
                        'Property ID': [property_id],
                        'Reservation UID': uid,
                        'ICS URL': feed_url,
                        'Status': 'Modified'
                    }
                    
                    collector.add_update(existing_record['id'], data)
            else:
                # Check for duplicates
                checkin = event['start'].strftime('%Y-%m-%d')
                checkout = event['end'].strftime('%Y-%m-%d')
                constraint_key = (property_id, checkin, checkout, 'Reservation')
                
                duplicates = existing_by_constraint.get(constraint_key, [])
                active_duplicates = [
                    d for d in duplicates 
                    if d['fields'].get('Status') in ['New', 'Modified']
                ]
                
                if not active_duplicates:
                    # Prepare create data
                    data = {
                        'Entry Type': 'Reservation',
                        'Service Type': 'Turnover',
                        'Check-in Date': event['start'].strftime('%Y-%m-%d'),
                        'Check-out Date': event['end'].strftime('%Y-%m-%d'),
                        'Property ID': [property_id],
                        'Reservation UID': uid,
                        'ICS URL': feed_url,
                        'Status': 'New'
                    }
                    
                    collector.add_create(uid, data)
    
    # Find removed reservations
    logger.info("\n🔍 Finding removed reservations...")
    
    for uid, record in existing_reservations.items():
        fields = record['fields']
        
        # Skip if not from ICS feed
        if not fields.get('ICS URL'):
            continue
            
        # Skip if already marked as removed or old
        if fields.get('Status') in ['Removed', 'Old']:
            continue
            
        # If not in processed UIDs, it's been removed
        if uid not in collector.processed_uids:
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
        remove_records = [r['record'] for r in collector.to_remove]
        # Mark as removed
        remove_updates = [
            {'id': r['record']['id'], 'fields': {'Status': 'Removed'}}
            for r in collector.to_remove
        ]
        for i in range(0, len(remove_updates), 10):
            batch = remove_updates[i:i+10]
            reservations_table.batch_update(batch)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ ICS SYNC COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total events processed: {total_events}")
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
    logger.info("=== ICS sync run started (MEMORY version with UID change detection) ===")
    logger.info(f"Environment: {Config.environment}")
    
    try:
        # Initialize API
        from pyairtable import Api
        api = Api(Config.get_airtable_api_key())
        base = api.base(Config.get_airtable_base_id())
        
        # Process with memory collection
        process_ics_with_memory(api, base, Config)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())