"""
Safe Removal Logic for ICS Sync
Requires multiple consecutive missing syncs before marking as removed
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configuration
MISSING_SYNC_THRESHOLD = 3  # Number of consecutive syncs before removal
GRACE_PERIOD_HOURS = 12    # Hours to wait before starting removal count

def should_mark_as_removed(
    record: Dict,
    current_time: datetime,
    is_missing_from_feed: bool
) -> tuple[bool, Dict[str, any]]:
    """
    Determine if a record should be marked as removed based on multi-sync confirmation.
    
    Returns: (should_remove, fields_to_update)
    """
    fields = record.get("fields", {})
    record_id = fields.get("ID")
    missing_count = fields.get("Missing Count", 0)
    missing_since = fields.get("Missing Since")
    last_seen = fields.get("Last Seen")
    
    # Convert string dates to datetime if needed
    if missing_since and isinstance(missing_since, str):
        missing_since = datetime.fromisoformat(missing_since.replace('Z', '+00:00'))
    if last_seen and isinstance(last_seen, str):
        last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
    
    updates = {}
    
    if is_missing_from_feed:
        # Record is missing from current sync
        if missing_count == 0:
            # First time missing - start tracking
            logging.info(f"Record {record_id} missing for first time, starting tracking")
            updates["Missing Since"] = current_time.isoformat()
            updates["Missing Count"] = 1
            return False, updates
        else:
            # Already being tracked
            time_missing = current_time - missing_since if missing_since else timedelta(0)
            
            # Check if grace period has passed
            if time_missing.total_seconds() < GRACE_PERIOD_HOURS * 3600:
                logging.info(f"Record {record_id} in grace period ({time_missing.total_seconds()/3600:.1f} hours)")
                return False, {}
            
            # Increment missing count
            new_count = missing_count + 1
            updates["Missing Count"] = new_count
            
            if new_count >= MISSING_SYNC_THRESHOLD:
                # Threshold reached - mark for removal
                logging.warning(f"Record {record_id} missing {new_count} times - marking as removed")
                return True, updates
            else:
                logging.info(f"Record {record_id} missing {new_count} times (threshold: {MISSING_SYNC_THRESHOLD})")
                return False, updates
    else:
        # Record found in feed - reset tracking
        if missing_count > 0:
            logging.info(f"Record {record_id} found again after being missing {missing_count} times")
            updates["Missing Count"] = 0
            updates["Missing Since"] = None
            updates["Last Seen"] = current_time.isoformat()
        else:
            # Just update last seen
            updates["Last Seen"] = current_time.isoformat()
        
        return False, updates


def check_removal_exceptions(fields: Dict) -> Optional[str]:
    """
    Check if a record should never be removed regardless of missing status.
    Returns reason if removal should be blocked, None otherwise.
    """
    # Don't remove if there's an active HCP job
    if fields.get("Service Job ID") and fields.get("Job Status") in ["Scheduled", "In Progress"]:
        return "Active HCP job exists"
    
    # Don't remove recent reservations (checked in within last 7 days)
    checkin_date = fields.get("Check-in Date")
    if checkin_date:
        checkin = datetime.fromisoformat(checkin_date)
        if (datetime.now() - checkin).days < 7:
            return "Recent check-in (within 7 days)"
    
    # Don't remove if checkout is today or tomorrow
    checkout_date = fields.get("Check-out Date")
    if checkout_date:
        checkout = datetime.fromisoformat(checkout_date)
        days_until_checkout = (checkout - datetime.now()).days
        if 0 <= days_until_checkout <= 1:
            return "Checkout is imminent"
    
    return None


def process_missing_records(
    table,
    missing_records: List[Dict],
    current_time: datetime,
    mark_as_old_func
) -> Dict[str, int]:
    """
    Process records that are missing from the current ICS sync.
    """
    stats = {
        "tracked": 0,
        "removed": 0,
        "exceptions": 0,
        "reset": 0
    }
    
    for record in missing_records:
        fields = record.get("fields", {})
        record_id = fields.get("ID")
        
        # Check for removal exceptions
        exception_reason = check_removal_exceptions(fields)
        if exception_reason:
            logging.info(f"Record {record_id} exempted from removal: {exception_reason}")
            stats["exceptions"] += 1
            continue
        
        # Check if should be removed
        should_remove, updates = should_mark_as_removed(record, current_time, True)
        
        if should_remove:
            # Mark as removed
            mark_as_old_func(table, [record], {}, current_time.isoformat(), "Removed")
            stats["removed"] += 1
        elif updates:
            # Update tracking fields
            table.update(record["id"], updates)
            stats["tracked"] += 1
    
    return stats


def reset_found_records(table, found_records: List[Dict], current_time: datetime) -> int:
    """
    Reset tracking for records that were found in the feed.
    """
    reset_count = 0
    
    for record in found_records:
        fields = record.get("fields", {})
        if fields.get("Missing Count", 0) > 0:
            _, updates = should_mark_as_removed(record, current_time, False)
            if updates:
                table.update(record["id"], updates)
                reset_count += 1
    
    return reset_count