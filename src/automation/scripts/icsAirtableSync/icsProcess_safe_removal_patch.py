#!/usr/bin/env python3
"""
Patch for icsProcess.py to implement safe removal logic
This shows the changes needed to integrate multi-sync confirmation
"""

# Add this import at the top of icsProcess.py
from removal_safety import (
    should_mark_as_removed,
    check_removal_exceptions,
    process_missing_records,
    reset_found_records,
    MISSING_SYNC_THRESHOLD,
    GRACE_PERIOD_HOURS
)

# Replace the removal section (lines 1288-1331) with this code:
def process_ics_feed_safe_removal(url, table, events, existing_records, processed_uid_url_pairs, 
                                  duplicate_detected_dates, stats, arizona_tz):
    """
    Enhanced version of process_ics_feed with safe removal logic
    """
    now = datetime.now(arizona_tz)
    now_iso = now.isoformat(sep=" ", timespec="seconds")
    today_iso = date.today().isoformat()
    
    # Track removal statistics
    removal_stats = {
        "tracked": 0,
        "removed": 0,
        "exceptions": 0,
        "reset": 0
    }
    
    # Get all UIDs for this feed URL
    feed_keys = [(uid, feed_url) for uid, feed_url in existing_records.keys() if feed_url == url]
    logging.info(f"🔍 Found {len(feed_keys)} existing record keys for feed {url}")
    
    # Find pairs that exist in Airtable but weren't in this feed
    missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
    logging.info(f"🔍 Found {len(missing_keys)} records missing from current sync")
    
    for i, (uid, feed_url) in enumerate(missing_keys):
        logging.info(f"🔍 Processing missing record {i+1}/{len(missing_keys)}: {uid}")
        records = existing_records.get((uid, feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        for rec in active_records:
            fields = rec["fields"]
            record_id = fields.get("ID")
            
            # Skip if the stay is fully past
            if fields.get("Check-out Date", "") < today_iso:
                logging.info(f"Skipping record {record_id} - checkout date is in past")
                continue
            
            # Check if this record matches a duplicate that was detected
            property_ids = fields.get("Property ID", [])
            if property_ids:
                record_property_id = property_ids[0]
                record_checkin = fields.get("Check-in Date", "")
                record_checkout = fields.get("Check-out Date", "")
                record_entry_type = fields.get("Entry Type", "")
                
                duplicate_key = (record_property_id, record_checkin, record_checkout, record_entry_type)
                if duplicate_key in duplicate_detected_dates:
                    logging.info(f"Skipping removal of {uid} - same reservation detected with different UID")
                    continue
            
            # Check for removal exceptions (active jobs, recent check-ins, etc.)
            exception_reason = check_removal_exceptions(fields)
            if exception_reason:
                logging.info(f"Record {record_id} exempted from removal: {exception_reason}")
                removal_stats["exceptions"] += 1
                continue
            
            # Check if should be removed based on missing count
            should_remove, updates = should_mark_as_removed(rec, now, is_missing_from_feed=True)
            
            if should_remove:
                # Threshold reached - mark as removed
                logging.warning(f"🚨 Record {record_id} missing {updates.get('Missing Count', 0)} consecutive times - marking as REMOVED")
                mark_all_as_old_and_clone(table, records, {}, now_iso, "Removed")
                removal_stats["removed"] += 1
            elif updates:
                # Update tracking fields
                logging.info(f"📊 Updating tracking for record {record_id}: Missing Count = {updates.get('Missing Count', 0)}")
                table.update(rec["id"], updates)
                removal_stats["tracked"] += 1
    
    # Reset tracking for records that were found in this sync
    found_keys = [pair for pair in feed_keys if pair in processed_uid_url_pairs]
    for uid, feed_url in found_keys:
        records = existing_records.get((uid, feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        for rec in active_records:
            if rec["fields"].get("Missing Count", 0) > 0:
                _, updates = should_mark_as_removed(rec, now, is_missing_from_feed=False)
                if updates:
                    logging.info(f"✅ Record {rec['fields'].get('ID')} found again - resetting tracking")
                    table.update(rec["id"], updates)
                    removal_stats["reset"] += 1
    
    # Update stats
    stats["Removed"] = removal_stats["removed"]
    stats["Tracked"] = removal_stats["tracked"]
    stats["Exceptions"] = removal_stats["exceptions"]
    stats["Reset"] = removal_stats["reset"]
    
    logging.info(f"Feed {url} removal summary: "
                f"{removal_stats['removed']} removed (after {MISSING_SYNC_THRESHOLD} missing syncs), "
                f"{removal_stats['tracked']} being tracked, "
                f"{removal_stats['exceptions']} exempted, "
                f"{removal_stats['reset']} found again")
    
    return stats


# Also add this informational message when starting ICS sync:
def log_removal_safety_info():
    """Log information about removal safety settings"""
    logging.info("=" * 70)
    logging.info("🛡️  REMOVAL SAFETY ENABLED")
    logging.info(f"   • Consecutive missing syncs required: {MISSING_SYNC_THRESHOLD}")
    logging.info(f"   • Grace period: {GRACE_PERIOD_HOURS} hours")
    logging.info("   • Exceptions: Active HCP jobs, recent check-ins, imminent checkouts")
    logging.info("=" * 70)