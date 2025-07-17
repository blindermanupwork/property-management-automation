#!/usr/bin/env python3
"""
Test restoration of ONE record to verify the process works
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

def test_restore_one():
    """
    Test restore of just ONE record to verify process
    """
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    
    # Re-import to get prod config
    from src.automation.config_wrapper import get_config
    config = get_config()
    
    api = Api(config.get_airtable_api_key())
    base_id = config.get_airtable_base_id()
    table = api.table(base_id, "Reservations")
    
    print("🧪 TEST RESTORATION: One Record Only")
    print("="*80)
    
    # Read record IDs from file
    ids_file = "/home/opc/automation/removed_record_ids.txt"
    
    if not os.path.exists(ids_file):
        print(f"❌ Error: {ids_file} not found")
        print("Run find_removed_ids.py first to generate the IDs file")
        return
    
    with open(ids_file, "r") as f:
        record_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(record_ids)} total records in file")
    
    if len(record_ids) == 0:
        print("No records to test")
        return
    
    # Take just the FIRST record for testing
    test_record_id = record_ids[0]
    
    print(f"Testing with record ID: {test_record_id}")
    
    # Get current record details before update
    try:
        current_record = table.get(test_record_id)
        current_status = current_record["fields"].get("Status", "Unknown")
        airtable_id = current_record["fields"].get("ID", "Unknown")
        
        print(f"Record {airtable_id} current status: {current_status}")
        
    except Exception as e:
        print(f"❌ Error getting current record: {e}")
        return
    
    # Auto-proceed with test (script mode)
    print(f"\n🚨 PROCEEDING WITH TEST")
    print(f"Changing record {airtable_id} from '{current_status}' to 'Old'")
    
    # Update the record
    print(f"\n🔄 UPDATING RECORD...")
    
    try:
        result = table.update(test_record_id, {"Status": "Old"})
        print(f"✅ SUCCESS: Record {airtable_id} updated to 'Old'")
        print(f"API Response: {result['fields'].get('Status')}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return
    
    print(f"\n📋 VERIFICATION: Let's check with MCP...")
    return airtable_id

if __name__ == "__main__":
    test_id = test_restore_one()
    if test_id:
        print(f"\n✅ Test complete. Now verify record {test_id} status with MCP")