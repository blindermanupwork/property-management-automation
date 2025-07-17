#!/usr/bin/env python3
"""
Quick script to check for service line differences in Airtable
"""

import os
import sys
from pathlib import Path
from pyairtable import Api

# Add parent directories to path
automation_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(automation_root))

try:
    from src.automation.config_prod import ProdConfig
except ImportError:
    # Alternative path when run from different context
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from automation.config_prod import ProdConfig

def check_differences():
    config = ProdConfig()
    
    # Initialize Airtable
    api_key = config.get_airtable_api_key()
    base_id = config.get_airtable_base_id()
    api = Api(api_key)
    base = api.base(base_id)
    table = base.table('Reservations')
    
    # Find records where HCP content differs from system
    formula = 'AND({Service Job ID} != "", {HCP Service Line Current} != "", {Service Line Description} != {HCP Service Line Current})'
    
    print("🔍 Checking for service line differences...\n")
    
    differences = []
    for page in table.iterate(formula=formula, fields=['Service Job ID', 'Property ID', 'Service Line Description', 'HCP Service Line Current']):
        for record in page:
            differences.append(record['fields'])
    
    if not differences:
        print("No differences found yet. The download might still be in progress.")
        
        # Check how many have been downloaded
        downloaded_formula = 'AND({Service Job ID} != "", {HCP Service Line Current} != "")'
        downloaded_count = sum(1 for page in table.iterate(formula=downloaded_formula, fields=['Service Job ID']) for _ in page)
        
        total_formula = '{Service Job ID} != ""'
        total_count = sum(1 for page in table.iterate(formula=total_formula, fields=['Service Job ID']) for _ in page)
        
        print(f"\n📊 Progress: {downloaded_count}/{total_count} jobs downloaded ({downloaded_count/total_count*100:.1f}%)")
    else:
        print(f"Found {len(differences)} records with differences:\n")
        
        for i, diff in enumerate(differences[:10]):  # Show first 10
            print(f"{i+1}. Job: {diff['Service Job ID']}")
            print(f"   Property: {diff.get('Property ID', ['Unknown'])[0] if diff.get('Property ID') else 'Unknown'}")
            print(f"   System: {diff['Service Line Description']}")
            print(f"   HCP:    {diff['HCP Service Line Current']}")
            
            # Analyze the difference
            system = diff['Service Line Description'].strip()
            hcp = diff['HCP Service Line Current'].strip()
            
            if hcp.startswith(system):
                user_added = hcp[len(system):].strip()
                print(f"   User added: '{user_added}'")
            elif system in hcp:
                print(f"   User modified the text")
            else:
                print(f"   Major differences")
            print()

if __name__ == '__main__':
    check_differences()