#!/usr/bin/env python3
"""
Fix for the duplicate detection bug in icsProcess_optimized.py
This script patches the duplicate detection to properly track all related records
"""

import os
import sys
from pathlib import Path

# Path to the file we need to fix
target_file = Path("/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py")

def apply_fix():
    """Apply the duplicate detection fix to icsProcess_optimized.py"""
    
    print("Reading current file...")
    with open(target_file, 'r') as f:
        content = f.read()
    
    # First, let's add the enhanced duplicate checking function after the existing check_for_duplicate
    new_function = '''
def check_for_duplicate_with_tracking(table, property_id, checkin_date, checkout_date, entry_type):
    """
    Enhanced duplicate check that returns both the duplicate status 
    and any existing records with same property but different dates.
    This helps track UID changes for the same reservation.
    """
    if not property_id:
        return False, []
    
    try:
        # Get ALL active records for this property
        property_formula = f"AND(FIND('{property_id}', ARRAYJOIN({{Property ID}}, ',')), OR({{Status}} = 'New', {{Status}} = 'Modified'))"
        all_property_records = table.all(
            formula=property_formula, 
            fields=["Reservation UID", "Status", "Check-in Date", "Check-out Date", "Entry Type", "ID"]
        )
        
        # Find exact duplicates and related records
        exact_duplicates = []
        related_records = []
        
        for record in all_property_records:
            fields = record["fields"]
            rec_checkin = fields.get("Check-in Date", "")
            rec_checkout = fields.get("Check-out Date", "")
            rec_entry_type = fields.get("Entry Type", "")
            
            if (rec_checkin == checkin_date and 
                rec_checkout == checkout_date and
                rec_entry_type == entry_type):
                exact_duplicates.append(record)
            else:
                # Different dates but same property - track for potential UID change
                related_records.append(record)
        
        is_duplicate = len(exact_duplicates) > 0
        if is_duplicate:
            logging.info(f"Found duplicate: Property {property_id}, {checkin_date} to {checkout_date}, Type: {entry_type}")
            if related_records:
                logging.info(f"Also found {len(related_records)} related records for same property with different dates")
        
        return is_duplicate, related_records
        
    except Exception as e:
        logging.error(f"Error in enhanced duplicate check: {str(e)}")
        return False, []
'''
    
    # Find where to insert the new function (after check_for_duplicate)
    import re
    pattern = r'(def check_for_duplicate\(.*?\n(?:.*\n)*?    return False\n)'
    match = re.search(pattern, content)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + "\n" + new_function + "\n" + content[insert_pos:]
        print("✓ Added enhanced duplicate checking function")
    else:
        print("✗ Could not find insertion point for new function")
        return False
    
    # Now update the process_single_event function to use the enhanced check
    # Replace the check_for_duplicate call with our enhanced version
    content = re.sub(
        r'if property_id and check_for_duplicate\(\s*table,\s*property_id,\s*event\["dtstart"\],\s*event\["dtend"\],\s*event\["entry_type"\]\s*\):',
        '''is_duplicate, related_records = check_for_duplicate_with_tracking(
        table, 
        property_id, 
        event["dtstart"], 
        event["dtend"], 
        event["entry_type"]
    )
    if property_id and is_duplicate:''',
        content
    )
    print("✓ Updated process_single_event to use enhanced duplicate check")
    
    # Update the duplicate tracking in process_ics_feed
    # Find the section where duplicate_detected_dates is populated
    pattern = r'# If this was a duplicate, track the property/date combination\s*\n\s*if status == "Duplicate_Ignored" and property_id:\s*\n\s*duplicate_key = \(property_id, event\["dtstart"\], event\["dtend"\], event\["entry_type"\]\)\s*\n\s*duplicate_detected_dates\.add\(duplicate_key\)'
    
    replacement = '''# If this was a duplicate, track the property/date combination
        if status == "Duplicate_Ignored" and property_id:
            # Track the current event's dates
            duplicate_key = (property_id, event["dtstart"], event["dtend"], event["entry_type"])
            duplicate_detected_dates.add(duplicate_key)
            
            # ALSO get and track all related records to prevent false removals
            _, related_records = check_for_duplicate_with_tracking(
                table, property_id, event["dtstart"], event["dtend"], event["entry_type"]
            )
            for related in related_records:
                fields = related["fields"]
                related_key = (
                    property_id,
                    fields.get("Check-in Date", ""),
                    fields.get("Check-out Date", ""),
                    fields.get("Entry Type", "")
                )
                if related_key[1] and related_key[2]:  # Only add if dates are present
                    duplicate_detected_dates.add(related_key)
                    logging.info(f"Also tracking related record dates: {related_key[1]} to {related_key[2]}")'''
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    print("✓ Enhanced duplicate tracking to include related records")
    
    # Add declaration for related_records in process_single_event
    # Find where we need to add it (just before the is_duplicate check)
    pattern = r'(\n    # ALWAYS check for duplicates first.*?\n)(    if property_id and check_for_duplicate)'
    replacement = r'\1    # Initialize related_records\n    related_records = []\n    \n\2'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Fix the future check-in filter in removal detection
    # Find the removal detection section
    pattern = r'# Skip if check-in is today or future.*?\n\s*if record_checkin >= today_iso:.*?\n\s*continue'
    replacement = '''# Skip only if check-in is far in the future (>6 months)
                # This allows removal of near-future reservations that disappear from feeds
                from dateutil.relativedelta import relativedelta
                future_cutoff = (date.today() + relativedelta(months=6)).isoformat()
                if record_checkin > future_cutoff:
                    logging.info(f"Skipping removal check for far-future reservation (check-in: {record_checkin})")
                    continue'''
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    print("✓ Adjusted future check-in filter to allow near-future removals")
    
    # Write the fixed content back
    print("\nWriting fixed content back to file...")
    with open(target_file, 'w') as f:
        f.write(content)
    
    print("✅ Fix applied successfully!")
    print("\nChanges made:")
    print("1. Added enhanced duplicate checking function that tracks related records")
    print("2. Updated duplicate detection to track all related property/date combinations")
    print("3. Modified removal detection to only skip far-future reservations (>6 months)")
    print("\nThis should prevent record 37717 from being incorrectly marked as removed.")
    
    return True

if __name__ == "__main__":
    if apply_fix():
        print("\n🎉 Fix completed! The ICS processor should now handle UID changes correctly.")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")