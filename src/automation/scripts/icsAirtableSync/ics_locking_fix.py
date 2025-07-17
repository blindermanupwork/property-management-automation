#!/usr/bin/env python3
"""
ICS Processing with Distributed Locking Fix
Prevents race conditions when processing concurrent ICS feeds
"""

import asyncio
import aiohttp
from asyncio import Semaphore
from threading import Lock
from collections import defaultdict
import logging
from datetime import datetime

# Global lock manager for property/date combinations
class PropertyDateLockManager:
    """Thread-safe lock manager for preventing duplicate records"""
    
    def __init__(self):
        self._locks = defaultdict(Lock)
        self._manager_lock = Lock()
    
    def get_lock(self, property_id, checkin_date, checkout_date, entry_type):
        """Get or create a lock for a specific property/date combination"""
        key = (property_id, checkin_date, checkout_date, entry_type)
        
        with self._manager_lock:
            return self._locks[key]

# Global instance
property_date_locks = PropertyDateLockManager()

# Semaphore to limit concurrent feed processing
MAX_CONCURRENT_FEEDS = 10  # Adjust based on system capacity
feed_semaphore = Semaphore(MAX_CONCURRENT_FEEDS)

async def process_ics_feed_with_throttling(session, url, url_to_prop_map, existing_records, table, create_batch, update_batch, session_tracker):
    """Process a single ICS feed with throttling and locking"""
    
    async with feed_semaphore:  # Limit concurrent feeds
        try:
            # Fetch ICS content
            success, ics_text, err = await fetch_ics_async(session, url)
            
            if not success:
                return url, False, err, 0, 0
            
            # Parse ICS content
            total_vevents, events = parse_ics(ics_text, url)
            
            # Process each event with locking
            processed = 0
            for event in events:
                property_id = url_to_prop_map.get(url)
                if not property_id:
                    continue
                
                # Get lock for this property/date combination
                lock = property_date_locks.get_lock(
                    property_id,
                    event["dtstart"],
                    event["dtend"],
                    event["entry_type"]
                )
                
                # Process with lock held
                with lock:
                    result = sync_ics_event_with_lock(
                        event, existing_records, url_to_prop_map,
                        table, create_batch, update_batch, session_tracker
                    )
                    if result != "Duplicate_Ignored":
                        processed += 1
            
            return url, True, None, total_vevents, processed
            
        except Exception as e:
            logging.error(f"Error processing feed {url}: {e}")
            return url, False, str(e), 0, 0

def sync_ics_event_with_lock(event, existing_records, url_to_prop, table, create_batch, update_batch, session_tracker):
    """
    Enhanced sync_ics_event that assumes it's called with a lock held.
    This prevents race conditions during the check-and-create sequence.
    """
    original_uid = event["uid"]
    feed_url = event["ics_url"]
    property_id = url_to_prop.get(feed_url)
    now_iso = datetime.now().isoformat(sep=" ", timespec="seconds")
    
    # Create composite UID
    if property_id:
        composite_uid = f"{original_uid}_{property_id}"
    else:
        composite_uid = original_uid
    
    # Re-check for duplicates inside the lock
    # This is crucial - we must query the database again inside the lock
    formula = f"AND({{Property ID}} = '{property_id}', {{Check-in Date}} = '{event['dtstart']}', {{Check-out Date}} = '{event['dtend']}', {{Entry Type}} = '{event['entry_type']}', OR({{Status}} = 'New', {{Status}} = 'Modified'))"
    
    current_records = table.all(formula=formula)
    
    if current_records:
        # Record already exists - check if it's ours
        for record in current_records:
            if record['fields'].get('Reservation UID') == composite_uid:
                # It's our record - check for changes
                return handle_existing_record(record, event, table, now_iso)
            
        # Different UID but same property/dates - it's a duplicate
        logging.info(f"Duplicate detected (inside lock): {composite_uid} for property {property_id}")
        return "Duplicate_Ignored"
    
    # No duplicates - safe to create new record
    return create_new_record(event, composite_uid, feed_url, property_id, create_batch, now_iso)

async def process_all_ics_feeds_improved(urls_to_process, url_to_prop_map, existing_records, table):
    """Improved ICS feed processing with throttling and locking"""
    
    # Create batch collectors
    create_batch = BatchCollector(table, op="create")
    update_batch = BatchCollector(table, op="update")
    session_tracker = set()
    
    async with aiohttp.ClientSession() as session:
        # Process feeds with controlled concurrency
        tasks = []
        for url in urls_to_process:
            task = process_ics_feed_with_throttling(
                session, url, url_to_prop_map, existing_records,
                table, create_batch, update_batch, session_tracker
            )
            tasks.append(task)
        
        # Process all feeds
        results = await asyncio.gather(*tasks)
    
    # Execute batch operations
    create_batch.done()
    update_batch.done()
    
    return results

# Helper functions remain the same but are called within locks
def handle_existing_record(record, event, table, now_iso):
    """Handle updates to existing records"""
    # Implementation remains the same
    pass

def create_new_record(event, composite_uid, feed_url, property_id, create_batch, now_iso):
    """Create a new record in Airtable"""
    # Implementation remains the same
    pass