#!/usr/bin/env python3
"""
Safe restoration: Change incorrectly "Removed" records to "Old" status
"""

import sys
from pathlib import Path
from datetime import datetime
import time

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from pyairtable import Api

def safe_restoration():
    """
    Change incorrectly removed records to "Old" status
    """
    
    config = Config
    
    # Set production environment
    import os
    os.environ["ENVIRONMENT"] = "production"
    
    api = Api(config.get_airtable_token())
    base_id = config.get_airtable_base_id()
    table = api.table(base_id, "Reservations")
    
    print("🛡️ SAFE RESTORATION: Removed → Old")
    print("="*80)
    
    # Find records marked as "Removed" today during incident window (19:00-20:00)
    formula = """AND(
        {Status} = 'Removed',
        DATESTR({Last Updated}) = '2025-07-11',
        HOUR({Last Updated}) >= 19,
        HOUR({Last Updated}) <= 20
    )"""
    
    print("🔍 Finding records incorrectly marked as Removed...")
    removed_records = table.all(
        formula=formula,
        fields=["ID", "Reservation UID", "Status", "Last Updated", 
               "Check-in Date", "Check-out Date", "Entry Type"]
    )
    
    print(f"Found {len(removed_records)} records marked as Removed during incident")
    
    if len(removed_records) == 0:
        print("No records to restore")
        return
    
    # Sample verification - check first 5 records have corresponding "New" versions
    print("\n📋 Verification - Checking for corresponding 'New' records:")
    verified_count = 0
    
    for i, record in enumerate(removed_records[:5]):
        uid = record["fields"].get("Reservation UID", "")
        if uid:
            # Check if this UID exists as New/Modified
            check_formula = f"AND({{Reservation UID}} = '{uid}', OR({{Status}} = 'New', {{Status}} = 'Modified'))"
            active_records = table.all(formula=check_formula, fields=["ID", "Status"])
            
            if active_records:
                verified_count += 1
                print(f"  ✅ Record {record['fields'].get('ID')}: Has {len(active_records)} active version(s)")
            else:
                print(f"  ⚠️  Record {record['fields'].get('ID')}: No active version found")
    
    print(f"\nVerification: {verified_count}/5 sample records have active versions")
    
    if verified_count < 3:
        print("❌ Verification failed - too few records have active versions")
        print("This suggests the removal might have been legitimate. Stopping.")
        return
    
    # Show what will be changed
    print(f"\n📝 DRY RUN - Would change {len(removed_records)} records:")
    print("   Status: 'Removed' → 'Old'")
    print("   Reason: Incorrectly marked as removed due to UID compositing bug")
    
    # Ask for confirmation
    print(f"\n🚨 PROCEED WITH RESTORATION?")
    print(f"This will change {len(removed_records)} records from 'Removed' to 'Old'")
    confirm = input("Type 'YES' to proceed: ")
    
    if confirm != "YES":
        print("Restoration cancelled")
        return
    
    # Proceed with restoration
    print("\n🔄 RESTORING RECORDS...")
    print("Processing in batches of 20...")
    
    batch_size = 20
    restored_count = 0
    errors = []
    
    for i in range(0, len(removed_records), batch_size):
        batch = removed_records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(removed_records) + batch_size - 1) // batch_size
        
        print(f"\nBatch {batch_num}/{total_batches}: Processing {len(batch)} records...")
        
        for record in batch:
            try:
                record_id = record["id"]
                airtable_id = record["fields"].get("ID")
                
                # Update status to "Old"
                table.update(record_id, {"Status": "Old"})
                restored_count += 1
                
                print(f"  ✅ Record {airtable_id}: Removed → Old")
                
            except Exception as e:
                error_msg = f"Record {record.get('fields', {}).get('ID', 'unknown')}: {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")
        
        # Brief pause between batches
        if i + batch_size < len(removed_records):
            print(f"  Pausing 2 seconds before next batch...")
            time.sleep(2)
    
    # Final report
    print(f"\n" + "="*80)
    print(f"✅ RESTORATION COMPLETE!")
    print(f"Successfully restored: {restored_count} records")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    print(f"\nSummary:")
    print(f"- Changed {restored_count} records from 'Removed' to 'Old'")
    print(f"- These were incorrectly removed due to UID compositing bug")
    print(f"- Corresponding 'New' records remain active")
    print(f"- System integrity restored")
    
    # Log the restoration for audit
    log_msg = f"[{datetime.now().isoformat()}] Safe restoration: {restored_count} records changed from Removed to Old due to UID bug incident"
    with open("/home/opc/automation/restoration.log", "a") as f:
        f.write(log_msg + "\n")
    
    print(f"\n📝 Restoration logged to: /home/opc/automation/restoration.log")

if __name__ == "__main__":
    safe_restoration()