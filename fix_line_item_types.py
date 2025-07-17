#!/usr/bin/env python3
"""
Quick script to fix line item types for job_12c41558bd834622bac63f461282ba25
Updates materials items that were incorrectly set to 'labor' type.
"""

import requests
import json
import os
from typing import List, Dict

# HCP API configuration
HCP_API_BASE = "https://api.housecallpro.com/v1"
API_KEY = os.getenv("HCP_PROD_API_KEY")

if not API_KEY:
    print("Error: HCP_PROD_API_KEY environment variable not set")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

JOB_ID = "job_12c41558bd834622bac63f461282ba25"

# Line items that should be 'materials' (currently set as 'labor')
MATERIALS_ITEMS = [
    "rli_a0c06d994b9240f6b0f8920553837221",  # King sheet sets (qty 1)
    "rli_925311cb95e24e4b8c92fe65de28ab90",  # Extra king-size pillow cases (qty 2)
    "rli_943fbcbae179410e89e471714be183ae",  # Queen sheet sets (qty 3)
    "rli_118fa0aa7dd643b6b0d0fdc8f74d55c0",  # Full sheet sets (qty 2)
    "rli_f6798cd5ef35441aad7761b4acadaad6",  # Twin sheet sets (qty 3)
    "rli_8d144215d12b44cd81c12437a233e4bf",  # Extra standard-size pillow cases (qty 13)
    "rli_8f3a225698c8446491399389192af5a9",  # Bath towel sets (qty 16)
    "rli_11ffd3fc3763422c9859c50ead4c8363",  # Extra bath towels (qty 2)
    "rli_f5898b4838554b33ad638026d2969756",  # Extra hand towels (qty 5)
    "rli_cdb3696fa2ed43148737ad43ed6c2d2e",  # Pool towels (qty 16)
    "rli_38516384ac014c9daedce1f9c6e47806",  # Bath mats (qty 2)
    "rli_af58de8ea0714ef984222b1c1edc0cbe",  # Kitchen towels (qty 2)
    "rli_abd46b85929b4d1480753fc8f1e173ad",  # Paper towel rolls (qty 2)
    "rli_fcafc7eba61d4a65b50744bcaab2c587",  # Toilet paper rolls (qty 12)
    "rli_b4da0d63c2d54e4ebc3430ffe6972f7d",  # Dishwasher pods (qty 10)
    "rli_6c3b3c554164477fb4808c1a5f3d4c3c",  # Laundry pods (qty 10)
    "rli_6fa22a1925764b19a73a190cbf9313b4",  # Kitchen sponge (qty 1)
    "rli_6bfdc2a1c97e4a3ca5f13b53ef866997",  # Kitchen-sized trash bags (qty 10)
    "rli_4753583b7c5143e6a5c39d0247c6a1cf",  # Shampoo, conditioner, and body wash
    "rli_515d833980fd4c19a29c1563b66c0e29",  # Hand and dish soap
]

def get_line_item(job_id: str, line_item_id: str) -> Dict:
    """Get current line item details"""
    # Get all line items and find the specific one
    url = f"{HCP_API_BASE}/jobs/{job_id}/line_items"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    data = response.json()
    for item in data.get("data", []):
        if item["id"] == line_item_id:
            return item
    
    raise ValueError(f"Line item {line_item_id} not found")

def update_line_item_type(job_id: str, line_item_id: str, line_item: Dict) -> bool:
    """Update line item to materials type"""
    url = f"{HCP_API_BASE}/jobs/{job_id}/line_items/{line_item_id}"
    
    # Prepare update payload with correct type
    payload = {
        "name": line_item["name"],
        "description": line_item["description"],
        "unit_price": line_item["unit_price"],
        "quantity": line_item["quantity"],
        "kind": "materials",  # This is what we're fixing
        "taxable": line_item["taxable"]
    }
    
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"✅ Updated {line_item['name']} to 'materials'")
        return True
    else:
        print(f"❌ Failed to update {line_item['name']}: {response.status_code} - {response.text}")
        return False

def main():
    """Fix all line item types"""
    print(f"Fixing line item types for job {JOB_ID}")
    print(f"Updating {len(MATERIALS_ITEMS)} items to 'materials' type...")
    print()
    
    success_count = 0
    failed_count = 0
    
    for line_item_id in MATERIALS_ITEMS:
        try:
            # Get current line item
            line_item = get_line_item(JOB_ID, line_item_id)
            
            # Update to materials type
            if update_line_item_type(JOB_ID, line_item_id, line_item):
                success_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error updating {line_item_id}: {e}")
            failed_count += 1
    
    print()
    print(f"Summary: {success_count} successful, {failed_count} failed")
    
    if failed_count == 0:
        print("🎉 All line item types fixed successfully!")
    else:
        print(f"⚠️  {failed_count} items failed to update")

if __name__ == "__main__":
    main()