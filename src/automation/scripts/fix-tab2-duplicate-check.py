#!/usr/bin/env python3
"""
Fix the Tab2 duplicate detection to check for ANY existing block, not just New/Modified.
This prevents creating duplicate blocks when Status might be Old, Removed, etc.
"""

# The fix is simple - modify the check_for_duplicate function to:
# 1. For Blocks, check for ANY existing record regardless of status
# 2. For Reservations, keep the current logic (only New/Modified)

# In csvProcess.py around line 843-851, change:

OLD_CODE = """
        formula = (
            f"AND("
            f"{{Property ID}} = '{property_id}', "
            f"{{Check-in Date}} = '{checkin_date}', "
            f"{{Check-out Date}} = '{checkout_date}', "
            f"{{Entry Type}} = '{entry_type}', "
            f"OR({{Status}} = 'New', {{Status}} = 'Modified')"
            f")"
        )
"""

NEW_CODE = """
        # For Blocks, check for ANY existing record to prevent duplicates
        # For Reservations, only check New/Modified to allow reactivation
        if entry_type == "Block":
            formula = (
                f"AND("
                f"{{Property ID}} = '{property_id}', "
                f"{{Check-in Date}} = '{checkin_date}', "
                f"{{Check-out Date}} = '{checkout_date}', "
                f"{{Entry Type}} = '{entry_type}'"
                f")"
            )
        else:
            formula = (
                f"AND("
                f"{{Property ID}} = '{property_id}', "
                f"{{Check-in Date}} = '{checkin_date}', "
                f"{{Check-out Date}} = '{checkout_date}', "
                f"{{Entry Type}} = '{entry_type}', "
                f"OR({{Status}} = 'New', {{Status}} = 'Modified')"
                f")"
            )
"""

print("To fix Tab2 duplicate blocks:")
print("1. Edit /home/opc/automation/src/automation/scripts/CSVtoAirtable/csvProcess.py")
print("2. Find the check_for_duplicate function (around line 843)")
print("3. Replace the formula building code with the NEW_CODE above")
print("\nThis will prevent creating duplicate blocks even if existing ones have Status='Old'")