#!/usr/bin/env python3
"""
CSV Processing Composite UID Fix
Fixes the mismatch between composite UID creation and searching
"""

import logging
from collections import defaultdict

def build_uid_lookup_fixed(existing_records):
    """
    Build a lookup that indexes records by BOTH base UID and composite UID.
    This fixes the issue where we create composite UIDs but only search by base.
    """
    uid_lookup = defaultdict(list)
    
    for record in existing_records:
        fields = record.get('fields', {})
        uid = fields.get('Reservation UID', '')
        
        if not uid:
            continue
        
        # Add record to lookup by full UID (could be composite or base)
        uid_lookup[uid].append(record)
        
        # If this is a composite UID, also index by base UID
        if '_' in uid:
            base_uid = uid.split('_')[0]
            uid_lookup[base_uid].append(record)
        
        # Log for debugging
        if uid in ['14516891', '14516891_recL6AiK5pINSbcnu']:
            logging.info(f"Indexed record ID {fields.get('ID')} with UID '{uid}' (base: '{base_uid if '_' in uid else uid}')")
    
    logging.info(f"Built UID lookup with {len(uid_lookup)} unique UIDs")
    return uid_lookup

def find_existing_reservation_fixed(uid, property_id, uid_lookup):
    """
    Find existing reservation using both base UID and composite UID.
    Returns the most relevant record (preferring exact composite match).
    """
    # First try composite UID (most specific)
    composite_uid = f"{uid}_{property_id}" if property_id else uid
    
    # Look for exact composite match
    composite_matches = uid_lookup.get(composite_uid, [])
    if composite_matches:
        # Return the most recent active record
        active_records = [r for r in composite_matches if r['fields'].get('Status') in ('New', 'Modified')]
        if active_records:
            return max(active_records, key=lambda r: r['fields'].get('Last Updated', ''))
    
    # Fall back to base UID search
    base_matches = uid_lookup.get(uid, [])
    if base_matches:
        # Filter for records with matching property
        property_matches = []
        for record in base_matches:
            record_property_ids = record['fields'].get('Property ID', [])
            if record_property_ids and property_id in record_property_ids:
                property_matches.append(record)
        
        if property_matches:
            # Return the most recent active record for this property
            active_records = [r for r in property_matches if r['fields'].get('Status') in ('New', 'Modified')]
            if active_records:
                return max(active_records, key=lambda r: r['fields'].get('Last Updated', ''))
    
    return None

def process_csv_with_fixed_uid_handling(csv_file_path, existing_records, properties_table, reservations_table):
    """
    Process CSV file with corrected UID handling.
    This replaces the original process_csv_files logic with proper composite UID support.
    """
    # Build the corrected UID lookup
    uid_lookup = build_uid_lookup_fixed(existing_records)
    
    # Read and process CSV
    reservations = []
    with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
        # Process CSV rows...
        # (CSV reading logic remains the same)
        pass
    
    # Process each reservation
    for res in reservations:
        uid = res.get('uid')
        property_id = res.get('property_id')
        
        if not uid:
            continue
        
        # Find existing record with fixed lookup
        existing = find_existing_reservation_fixed(uid, property_id, uid_lookup)
        
        if existing:
            # Check for changes
            if has_changes(res, existing):
                # Mark old as "Old" and create new "Modified"
                mark_as_old_and_create_modified(existing, res, reservations_table)
            else:
                # No changes - skip
                logging.debug(f"No changes for UID {uid}")
        else:
            # Create new record with composite UID
            create_new_reservation_with_composite_uid(res, property_id, reservations_table)

def create_new_reservation_with_composite_uid(reservation_data, property_id, table):
    """Create a new reservation with proper composite UID"""
    
    # Generate composite UID
    base_uid = reservation_data['uid']
    composite_uid = f"{base_uid}_{property_id}" if property_id else base_uid
    
    # Build record fields
    fields = {
        'Reservation UID': composite_uid,  # Use composite UID
        'Entry Type': reservation_data.get('entry_type', 'Reservation'),
        'Service Type': reservation_data.get('service_type', 'Turnover'),
        'Guest Name': reservation_data.get('guest_name'),
        'Check-in Date': reservation_data.get('dtstart_iso'),
        'Check-out Date': reservation_data.get('dtend_iso'),
        'Property ID': [property_id] if property_id else None,
        'Entry Source': reservation_data.get('entry_source'),
        'Status': 'New',
        'Same-day Turnover': reservation_data.get('same_day_turnover', False),
        'ICS URL': reservation_data.get('ics_url'),
        'Last Updated': datetime.now().isoformat(),
    }
    
    # Remove None values
    fields = {k: v for k, v in fields.items() if v is not None}
    
    # Create record
    table.create(fields)
    logging.info(f"Created new reservation with composite UID: {composite_uid}")

# Example of how to integrate this fix into the existing csvProcess.py:
"""
# In csvProcess.py, replace the existing UID lookup logic with:

from csv_uid_fix import build_uid_lookup_fixed, find_existing_reservation_fixed, create_new_reservation_with_composite_uid

# Then in process_csv_files():
# 1. Build the fixed lookup:
uid_lookup = build_uid_lookup_fixed(existing_reservations)

# 2. Use the fixed lookup when checking for existing records:
existing = find_existing_reservation_fixed(uid, property_id, uid_lookup)

# 3. Create records with composite UIDs:
create_new_reservation_with_composite_uid(reservation_data, property_id, reservations_table)
"""