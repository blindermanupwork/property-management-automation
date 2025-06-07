#!/usr/bin/env python3
"""
Script to process duplicate UIDs and keep only the most recently updated record for each
"""

# List of UIDs from user input
uid_list = [
    "14531316", "14380224", "14577683", "14618322", "14612250", "14516891", 
    "14594403", "14545399", "14173207", "14124351", "14237533", "14429708", 
    "14358148", "13909080", "14521975", "14402886", "14060873", "14450845", 
    "14358596", "14433146", "14358598", "14358602", "14358607", "14358616", 
    "14358622", "14358629", "14567208", "14384034", "14686645", "14531316", 
    "14380224", "14577683", "14618322", "14612250", "14516891", "14594403", 
    "14545399", "14173207", "14124351", "14237533", "14429708", "14358148", 
    "13909080", "14521975", "14402886", "14060873", "14450845", "14358596", 
    "14433146", "14358598", "14358602", "14358607", "14358616", "14358622", 
    "14358629", "14567208", "14384034", "14686645", "14686645", "14612250", 
    "14124351", "14577683", "14380224", "14618322", "14516891", "14531316", 
    "14594403", "14545399", "14173207", "14237533", "14429708", "13909080", 
    "14358148", "14521975", "14402886", "14060873", "14450845", "14358596", 
    "14433146", "14358598", "14358602", "14358607", "14358616", "14358622", 
    "14358629", "14567208", "14384034"
]

def count_duplicates(uid_list):
    """Count occurrences of each UID"""
    uid_count = {}
    for uid in uid_list:
        uid_count[uid] = uid_count.get(uid, 0) + 1
    return uid_count

def get_unique_uids(uid_list):
    """Get unique UIDs from the list"""
    return list(set(uid_list))

def main():
    # Count duplicates
    uid_counts = count_duplicates(uid_list)
    
    print("=== DUPLICATE UID ANALYSIS ===")
    print(f"Total UIDs in list: {len(uid_list)}")
    print(f"Unique UIDs: {len(set(uid_list))}")
    print()
    
    # Show duplicates
    duplicates = {uid: count for uid, count in uid_counts.items() if count > 1}
    print(f"UIDs with duplicates: {len(duplicates)}")
    for uid, count in sorted(duplicates.items()):
        print(f"  {uid}: {count} times")
    
    print()
    
    # Get unique list
    unique_uids = get_unique_uids(uid_list)
    unique_uids.sort()
    
    print("=== UNIQUE UID LIST ===")
    for uid in unique_uids:
        print(uid)
    
    # Save to file
    with open('/home/opc/automation/unique_uids_list.txt', 'w') as f:
        f.write("UNIQUE UIDs LIST (Duplicates Removed)\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total unique UIDs: {len(unique_uids)}\n\n")
        for uid in unique_uids:
            f.write(f"{uid}\n")
    
    print(f"\nUnique list saved to: /home/opc/automation/unique_uids_list.txt")

if __name__ == "__main__":
    main()