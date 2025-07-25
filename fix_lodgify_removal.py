#!/usr/bin/env python3
"""
Fix for Lodgify removal detection - prevent marking records as removed
when the same reservation exists with a different UID in the current feed
"""

import sys
import os
sys.path.insert(0, '/home/opc/automation')

def show_fix_location():
    """Show where to add the fix in icsProcess_best.py"""
    
    print("LODGIFY REMOVAL FIX")
    print("=" * 80)
    print("\nThe issue: Lodgify changes UIDs on every sync, causing an endless add/remove cycle")
    print("\nThe root cause: Removal detection happens BEFORE new UIDs are processed")
    print("\nThe fix: Check if the current feed contains a reservation with same property/dates/type")
    print("\nAdd this code in icsProcess_best.py around line 1635 (after duplicate_detected_dates check):")
    print("\n" + "-" * 80)
    
    fix_code = '''
                # LODGIFY FIX: Check if this feed has a NEW event with same property/dates/type
                # This handles the case where Lodgify changed the UID but it's the same reservation
                found_in_current_feed = False
                for feed_event in events:
                    event_property_id = feed_event.get('property_id')
                    if (event_property_id == record_property_id and
                        feed_event.get('dtstart') == record_checkin and
                        feed_event.get('dtend') == record_checkout and
                        feed_event.get('entry_type') == record_entry_type):
                        # Found a matching event in the current feed!
                        logging.info(f"🔍 LODGIFY FIX: Found matching event in current feed with UID {feed_event.get('uid')}")
                        logging.info(f"   Skipping removal of {uid} - same reservation exists with different UID")
                        found_in_current_feed = True
                        break
                
                if found_in_current_feed:
                    continue
'''
    
    print(fix_code)
    print("-" * 80)
    print("\nThis fix:")
    print("1. Before marking a record as removed")
    print("2. Checks if the CURRENT FEED contains an event with same property/dates/type")
    print("3. If found, skips removal (it's the same reservation with a new UID)")
    print("\nThis prevents the add/remove cycle for Lodgify feeds!")

if __name__ == "__main__":
    show_fix_location()