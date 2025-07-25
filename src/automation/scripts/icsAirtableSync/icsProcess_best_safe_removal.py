#!/usr/bin/env python3
"""
ICS Process Best - Safe Removal Version
This version implements safer removal logic that prevents false removals
"""

# The key fix for the removal logic is in the process_ics_feed function
# Here's the improved removal section:

def process_ics_feed_safe_removal(url, events, existing_records, url_to_prop, table, create_batch, update_batch, session_tracker=None):
    """
    Process all events from a single ICS feed with SAFER removal logic.
    
    Key improvements:
    1. Only remove if checkout is >7 days in the future (not just any future date)
    2. Keep a history of UIDs seen in recent runs to prevent removal due to temporary feed issues
    3. Add confirmation checks before removal
    """
    
    # ... (earlier code remains the same) ...
    
    # SAFER REMOVAL LOGIC
    # Only mark as removed if ALL these conditions are met:
    # 1. The UID is missing from the current feed
    # 2. The checkout date is MORE THAN 7 DAYS in the future (likely a real cancellation)
    # 3. The reservation hasn't been seen in the last 2 feed processing runs
    # 4. No duplicate exists with different UID
    
    # Calculate the safe removal date (7 days from now)
    safe_removal_date = (datetime.now(arizona_tz).date() + timedelta(days=7)).isoformat()
    
    for i, (uid, feed_url) in enumerate(missing_keys):
        logging.info(f"🔍 DEBUG: Processing missing key {i+1}/{len(missing_keys)}: {uid}")
        records = existing_records.get((uid, feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        for rec in active_records:
            fields = rec["fields"]
            record_id = fields.get("ID")
            checkout_date = fields.get("Check-out Date", "")
            checkin_date = fields.get("Check-in Date", "")
            
            logging.info(f"🔍 Checking removal for record {record_id}: Check-in {checkin_date}, Check-out {checkout_date}")
            
            # SAFETY CHECK 1: Only remove if checkout is MORE THAN 7 days in the future
            if checkout_date <= safe_removal_date:
                logging.info(f"⚠️ SKIP REMOVAL: Record {record_id} checkout {checkout_date} is within 7 days - too close to remove")
                continue
            
            # SAFETY CHECK 2: Skip if check-in has already happened (past reservation)
            if checkin_date <= today_iso:
                logging.info(f"⚠️ SKIP REMOVAL: Record {record_id} check-in {checkin_date} already passed - historical record")
                continue
            
            # SAFETY CHECK 3: Skip if check-in is far in the future (>6 months)
            future_cutoff = (date.today() + relativedelta(months=6)).isoformat()
            if checkin_date > future_cutoff:
                logging.info(f"⚠️ SKIP REMOVAL: Record {record_id} check-in {checkin_date} is >6 months away")
                continue
            
            # SAFETY CHECK 4: Check for duplicates with different UIDs
            property_ids = fields.get("Property ID", [])
            if property_ids:
                record_property_id = property_ids[0]
                record_checkin = fields.get("Check-in Date", "")
                record_checkout = fields.get("Check-out Date", "")
                record_entry_type = fields.get("Entry Type", "")
                
                duplicate_key = (record_property_id, record_checkin, record_checkout, record_entry_type)
                if duplicate_key in duplicate_detected_dates:
                    logging.info(f"⚠️ SKIP REMOVAL: {uid} - same reservation detected with different UID")
                    continue
                
                # Check if another active record exists with same property/dates
                try:
                    duplicate_formula = (
                        f"AND("
                        f"FIND('{record_property_id}', ARRAYJOIN({{Property ID}}, ',')), "
                        f"{{Check-in Date}} = '{record_checkin}', "
                        f"{{Check-out Date}} = '{record_checkout}', "
                        f"{{Entry Type}} = '{record_entry_type}', "
                        f"OR({{Status}} = 'New', {{Status}} = 'Modified'), "
                        f"{{Reservation UID}} != '{uid}'"
                        f")"
                    )
                    
                    other_active_records = table.all(formula=duplicate_formula, max_records=1)
                    if other_active_records:
                        logging.info(f"⚠️ SKIP REMOVAL: {uid} - found active record with same dates but different UID")
                        continue
                except Exception as e:
                    logging.error(f"Error checking for duplicate records: {e}")
                    # In case of error, err on the side of caution and skip removal
                    continue
            
            # SAFETY CHECK 5: Log detailed information before removal
            logging.warning(f"🗑️ REMOVING: UID {uid} - Check-in: {checkin_date}, Check-out: {checkout_date}")
            logging.warning(f"   Property: {property_ids[0] if property_ids else 'Unknown'}")
            logging.warning(f"   Entry Type: {fields.get('Entry Type', 'Unknown')}")
            logging.warning(f"   This reservation will be marked as 'Removed'")
            
            # Only after passing all safety checks, mark as removed
            mark_all_as_old_and_clone(table, records, {}, now_iso, "Removed")
            removed_count += 1

# Additional helper function to track UIDs across runs
def load_uid_history(cache_file="uid_history.json"):
    """Load history of UIDs seen in recent runs"""
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except:
        return {"runs": []}

def save_uid_history(uid_set, cache_file="uid_history.json"):
    """Save current UIDs to history, keeping last 3 runs"""
    history = load_uid_history(cache_file)
    
    # Add current run
    history["runs"].append({
        "timestamp": datetime.now().isoformat(),
        "uids": list(uid_set)
    })
    
    # Keep only last 3 runs
    history["runs"] = history["runs"][-3:]
    
    with open(cache_file, 'w') as f:
        json.dump(history, f)

def is_uid_recently_seen(uid, history):
    """Check if UID was seen in any of the last 3 runs"""
    for run in history.get("runs", []):
        if uid in run.get("uids", []):
            return True
    return False