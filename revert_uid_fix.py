#!/usr/bin/env python3
"""
EMERGENCY REVERT: Fix the UID double-compositing bug
The existing records already have composite UIDs, we shouldn't composite them again!
"""

import re

# Read the file
with open("/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py", "r") as f:
    content = f.read()

print("🚨 EMERGENCY REVERT: Fixing double-compositing bug...")

# Revert back to using raw UIDs for existing records
old_code = '''res_uid = fields.get("Reservation UID")
            feed = fields.get("ICS URL")
            # Get property ID to create composite UID
            property_ids = fields.get("Property ID", [])
            property_id = property_ids[0] if property_ids else None
            
            if res_uid and feed:
                # Use composite UID for consistency with processing
                if property_id:
                    composite_uid = f"{res_uid}_{property_id}"
                else:
                    composite_uid = res_uid
                by_feed[(composite_uid, feed)].append(record)'''

new_code = '''res_uid = fields.get("Reservation UID")
            feed = fields.get("ICS URL")
            if res_uid and feed:
                by_feed[(res_uid, feed)].append(record)'''

content = content.replace(old_code, new_code)
print("✓ Reverted existing_records to use raw UIDs (as they're already composite)")

# Write the fixed content back
with open("/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py", "w") as f:
    f.write(content)

print("\n✅ EMERGENCY REVERT COMPLETE!")
print("\nThe bug was:")
print("- Existing records already have composite UIDs in Airtable")
print("- The fix tried to composite them again (double-composite)")
print("- This made existing UIDs never match processed UIDs")
print("- Result: ALL existing records marked as removed!")
print("\nReverted to original behavior where existing_records uses raw UIDs from Airtable.")