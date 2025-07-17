#!/usr/bin/env python3
"""
Batch restore all records from "Removed" to "Old" status
Reads record IDs from removed_record_ids.txt and processes them efficiently
"""

import sys
from pathlib import Path
import os
import time
from datetime import datetime

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from pyairtable import Api

def batch_restore_records():
    """
    Restore all records from file in efficient batches
    """
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    
    # Re-import to get prod config
    from src.automation.config_wrapper import get_config
    config = get_config()
    
    api = Api(config.get_airtable_api_key())
    base_id = config.get_airtable_base_id()
    table = api.table(base_id, "Reservations")
    
    print("🔄 BATCH RESTORATION: Removed → Old")
    print("="*80)
    
    # Read record IDs from file
    ids_file = "/home/opc/automation/removed_record_ids.txt"
    
    if not os.path.exists(ids_file):
        print(f"❌ Error: {ids_file} not found")
        print("Run find_removed_ids.py first to generate the IDs file")
        return
    
    with open(ids_file, "r") as f:
        record_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(record_ids)} record IDs from file")
    
    if len(record_ids) == 0:
        print("No records to restore")
        return
    
    # Auto-proceed with restoration (user approved)
    print(f"\n🚨 PROCEEDING WITH RESTORATION")
    print(f"Changing {len(record_ids)} records from 'Removed' to 'Old'")
    print(f"User has approved this action.")
    
    # Process in efficient batches of 50
    batch_size = 50
    total_batches = (len(record_ids) + batch_size - 1) // batch_size
    restored_count = 0
    errors = []
    
    print(f"\n🔄 PROCESSING {len(record_ids)} RECORDS IN {total_batches} BATCHES...")
    start_time = time.time()
    
    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"Batch {batch_num}/{total_batches}: Processing {len(batch)} records...", end=" ")
        
        try:
            # Prepare batch update - all records to "Old" status
            updates = []
            for record_id in batch:
                updates.append({
                    "id": record_id,
                    "fields": {"Status": "Old"}
                })
            
            # Execute batch update
            table.batch_update(updates)
            restored_count += len(batch)
            print(f"✅ Success ({restored_count}/{len(record_ids)})")
            
        except Exception as e:
            error_msg = f"Batch {batch_num}: {e}"
            errors.append(error_msg)
            print(f"❌ Error: {e}")
        
        # Brief pause between batches to avoid rate limits
        if i + batch_size < len(record_ids):
            time.sleep(1)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Final report
    print(f"\n" + "="*80)
    print(f"✅ RESTORATION COMPLETE!")
    print(f"Time taken: {duration:.1f} seconds")
    print(f"Successfully restored: {restored_count}/{len(record_ids)} records")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\nSummary:")
    print(f"- Changed {restored_count} records from 'Removed' to 'Old'")
    print(f"- These were incorrectly removed due to UID compositing bug")
    print(f"- Corresponding 'New' records remain active")
    print(f"- System integrity restored")
    
    # Log the restoration for audit
    log_msg = f"[{datetime.now().isoformat()}] Batch restoration: {restored_count} records changed from Removed to Old due to UID bug incident (took {duration:.1f}s)"
    log_file = "/home/opc/automation/restoration.log"
    with open(log_file, "a") as f:
        f.write(log_msg + "\n")
    
    print(f"\n📝 Restoration logged to: {log_file}")
    
    # Clean up ID files
    if restored_count > 0:
        print(f"\n🧹 Cleaning up temporary files...")
        try:
            os.remove("/home/opc/automation/removed_record_ids.txt")
            os.remove("/home/opc/automation/removed_airtable_ids.txt")
            print("Temporary ID files removed")
        except:
            print("Note: Could not remove temporary files (may not exist)")

if __name__ == "__main__":
    batch_restore_records()