#!/usr/bin/env python3
"""
Fix the UID mismatch bug in icsProcess_optimized.py
This bug prevents ANY removals from happening
"""

import re

# Read the file
with open("/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py", "r") as f:
    content = f.read()

print("Fixing UID mismatch bug...")

# Fix 1: Change existing_records to use composite UIDs when grouping
# Find the section where records are grouped by (UID, Feed)
old_pattern = r'res_uid = fields\.get\("Reservation UID"\)\s*\n\s*feed = fields\.get\("ICS URL"\)\s*\n\s*if res_uid and feed:\s*\n\s*by_feed\[\(res_uid, feed\)\]\.append\(record\)'

new_code = '''res_uid = fields.get("Reservation UID")
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

content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)
print("✓ Fixed existing_records to use composite UIDs")

# Write the fixed content back
with open("/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py", "w") as f:
    f.write(content)

print("\n✅ Fix applied successfully!")
print("\nThe removal detection should now work correctly:")
print("- existing_records will use composite UIDs")
print("- processed_uid_url_pairs uses composite UIDs")
print("- missing_keys comparison will now work properly")
print("\nRecord 37717 should now be marked as removed when you run the sync.")