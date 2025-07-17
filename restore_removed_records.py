#!/usr/bin/env python3
"""
Restore records that were incorrectly marked as removed due to the UID bug
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from pyairtable import Api

def restore_incorrectly_removed():
    """
    Find records marked as removed today and check if they should be restored
    """
    
    config = Config
    
    # Get environment variables - use production
    import os
    os.environ["ENVIRONMENT"] = "production"
    
    api = Api(config.get_airtable_token())
    base_id = config.get_airtable_base_id()
    table = api.table(base_id, "Reservations")
    
    print("🔍 FINDING INCORRECTLY REMOVED RECORDS")
    print("="*80)
    
    # Find records marked as "Removed" today
    today_str = date.today().isoformat()
    
    formula = f"AND({{Status}} = 'Removed', DATESTR({{Last Updated}}) = '{today_str}')"
    removed_today = table.all(
        formula=formula,
        fields=["ID", "Reservation UID", "Check-in Date", "Check-out Date", 
               "Property ID", "Entry Type", "ICS URL", "Status"]
    )
    
    print(f"Found {len(removed_today)} records marked as Removed today")
    
    if len(removed_today) == 0:
        print("No records to restore")
        return
    
    # Group by UID for analysis
    uid_groups = {}
    for record in removed_today:
        uid = record["fields"].get("Reservation UID", "")
        if uid:
            if uid not in uid_groups:
                uid_groups[uid] = []
            uid_groups[uid].append(record)
    
    print(f"\\nFound {len(uid_groups)} unique UIDs among removed records")
    
    # Check if any of these UIDs exist as active records
    restore_candidates = []
    
    for uid, removed_records in uid_groups.items():
        # Check if this UID exists as New/Modified
        formula = f"AND({{Reservation UID}} = '{uid}', OR({{Status}} = 'New', {{Status}} = 'Modified'))"
        active_records = table.all(formula=formula, fields=["ID", "Status"])
        
        if active_records:
            print(f"\\n⚠️  UID {uid[:50]}...")
            print(f"   - {len(removed_records)} records marked as Removed")
            print(f"   - {len(active_records)} active records still exist")
            print(f"   - This suggests the removal was incorrect!")
            
            # These should be restored to their previous status
            for removed_rec in removed_records:
                restore_candidates.append(removed_rec)
    
    print(f"\\n📋 RESTORATION CANDIDATES: {len(restore_candidates)} records")
    
    if len(restore_candidates) == 0:
        print("No records need restoration")
        return
        
    print("\\nSample of records to restore:")
    for i, record in enumerate(restore_candidates[:5]):
        fields = record["fields"]
        print(f"  {i+1}. ID: {fields.get('ID')}")
        print(f"     UID: {fields.get('Reservation UID', '')[:50]}...")
        print(f"     Dates: {fields.get('Check-in Date')} to {fields.get('Check-out Date')}")
        print(f"     Type: {fields.get('Entry Type')}")
    
    # Ask for confirmation
    print(f"\\n🚨 RESTORE {len(restore_candidates)} RECORDS?")
    confirm = input("Type 'YES' to proceed with restoration: ")
    
    if confirm != "YES":
        print("Restoration cancelled")
        return
    
    # Restore records by setting status back to New
    print("\\n🔄 RESTORING RECORDS...")
    restored_count = 0
    
    for record in restore_candidates:
        try:
            table.update(record["id"], {"Status": "New"})
            restored_count += 1
            if restored_count % 10 == 0:
                print(f"   Restored {restored_count}/{len(restore_candidates)} records...")
        except Exception as e:
            print(f"   Error restoring record {record['id']}: {e}")
    
    print(f"\\n✅ RESTORATION COMPLETE!")
    print(f"Restored {restored_count} out of {len(restore_candidates)} records")
    print("\\nThese records are now marked as 'New' and will be processed normally in the next sync.")

if __name__ == "__main__":
    restore_incorrectly_removed()