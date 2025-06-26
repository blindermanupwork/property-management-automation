#!/usr/bin/env python3
"""
Simple and efficient job template finder.
Uses direct API calls with proper error handling.
"""

import os
import csv
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Setup logging
log_dir = Path("/home/opc/automation/src/automation/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"job_template_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv('HCP_API_KEY_PROD')
if not API_KEY:
    logger.error("HCP_API_KEY_PROD not found in environment")
    exit(1)

BASE_URL = "https://api.housecallpro.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Job categorization patterns
def is_turnover(desc: str) -> bool:
    """Check if job is a turnover."""
    desc_lower = desc.lower()
    # Must not contain inspection or return laundry
    if 'inspection' in desc_lower or 'return laundry' in desc_lower:
        return False
    # Check for turnover patterns
    patterns = [' ng ', 'next guest', 'sameday', 'same day']
    return any(p in desc_lower for p in patterns)

def is_inspection(desc: str) -> bool:
    """Check if job is an inspection."""
    return 'inspection' in desc.lower()

def is_return_laundry(desc: str) -> bool:
    """Check if job is return laundry."""
    return 'return laundry' in desc.lower()

def get_jobs_for_address(address_id: str, limit: int = 200) -> List[Dict]:
    """Get recent jobs for a specific address using search."""
    all_jobs = []
    page = 1
    
    while len(all_jobs) < limit:
        try:
            # Use the jobs endpoint with pagination
            url = f"{BASE_URL}/jobs"
            params = {
                'page': page,
                'page_size': 100,
                'scheduled_start_min': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            
            if response.status_code == 429:
                # Rate limited
                reset_time = response.headers.get('RateLimit-Reset')
                if reset_time:
                    wait_time = int(reset_time) - int(time.time())
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time + 1)
                    continue
                else:
                    time.sleep(60)
                    continue
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                break
            
            data = response.json()
            jobs = data.get('data', [])
            
            # Filter for this address
            address_jobs = [
                job for job in jobs
                if job.get('address', {}).get('id') == address_id
            ]
            all_jobs.extend(address_jobs)
            
            # Check if more pages
            if not data.get('has_more', False) or not jobs:
                break
                
            page += 1
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            break
    
    return all_jobs

def find_templates_for_property(prop: Dict) -> Dict[str, Optional[str]]:
    """Find job templates for a single property."""
    address_id = prop.get('HCP Address ID')
    if not address_id:
        return {'turnover': None, 'inspection': None, 'return_laundry': None}
    
    # Skip if already has all templates
    if (prop.get('Turnover Job Template ID') and 
        prop.get('Inspection Job Template ID') and 
        prop.get('Return Laundry Job Template ID')):
        logger.info(f"Skipping {prop.get('Property Name')} - already has all templates")
        return {
            'turnover': prop.get('Turnover Job Template ID'),
            'inspection': prop.get('Inspection Job Template ID'),
            'return_laundry': prop.get('Return Laundry Job Template ID')
        }
    
    # Get jobs for this address
    jobs = get_jobs_for_address(address_id)
    logger.info(f"Found {len(jobs)} jobs for {prop.get('Property Name')}")
    
    # Categorize jobs
    turnover_jobs = []
    inspection_jobs = []
    return_laundry_jobs = []
    
    for job in jobs:
        # Skip canceled/deleted
        if job.get('work_status') in ['canceled', 'deleted']:
            continue
            
        desc = job.get('description', '')
        
        if is_return_laundry(desc):
            return_laundry_jobs.append(job)
        elif is_inspection(desc):
            inspection_jobs.append(job)
        elif is_turnover(desc):
            turnover_jobs.append(job)
    
    # Get most recent of each type
    templates = {'turnover': None, 'inspection': None, 'return_laundry': None}
    
    for job_type, job_list in [
        ('turnover', turnover_jobs),
        ('inspection', inspection_jobs),
        ('return_laundry', return_laundry_jobs)
    ]:
        if job_list:
            # Sort by created_at descending
            job_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            templates[job_type] = job_list[0].get('id')
            logger.info(f"  Found {job_type}: {templates[job_type]}")
    
    return templates

def main():
    """Main execution."""
    start_time = time.time()
    logger.info("Starting simple job template finder...")
    
    # Load properties
    input_file = "/home/opc/automation/export/Prod_Airtable_Properties.csv"
    properties = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        properties = list(reader)
    
    logger.info(f"Loaded {len(properties)} properties")
    
    # Process each property
    updated_count = 0
    for idx, prop in enumerate(properties, 1):
        property_name = prop.get('Property Name', 'Unknown')
        logger.info(f"\nProcessing {idx}/{len(properties)}: {property_name}")
        
        # Find templates
        templates = find_templates_for_property(prop)
        
        # Update property
        if templates['turnover'] and not prop.get('Turnover Job Template ID'):
            prop['Turnover Job Template ID'] = templates['turnover']
            updated_count += 1
        if templates['inspection'] and not prop.get('Inspection Job Template ID'):
            prop['Inspection Job Template ID'] = templates['inspection']
            updated_count += 1
        if templates['return_laundry'] and not prop.get('Return Laundry Job Template ID'):
            prop['Return Laundry Job Template ID'] = templates['return_laundry']
            updated_count += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"/home/opc/automation/export/Prod_Airtable_Properties_Final_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if properties:
            writer = csv.DictWriter(f, fieldnames=properties[0].keys())
            writer.writeheader()
            writer.writerows(properties)
    
    # Summary
    total = len(properties)
    has_turnover = sum(1 for p in properties if p.get('Turnover Job Template ID'))
    has_inspection = sum(1 for p in properties if p.get('Inspection Job Template ID'))
    has_return_laundry = sum(1 for p in properties if p.get('Return Laundry Job Template ID'))
    
    elapsed = time.time() - start_time
    
    summary = f"""
Job Template Extraction Complete
================================
Total Properties: {total}
Updates Made: {updated_count}

Templates Found:
- Turnover: {has_turnover}/{total} ({has_turnover/total*100:.1f}%)
- Inspection: {has_inspection}/{total} ({has_inspection/total*100:.1f}%)
- Return Laundry: {has_return_laundry}/{total} ({has_return_laundry/total*100:.1f}%)

Time Elapsed: {elapsed:.1f} seconds
Output: {output_file}
"""
    
    logger.info(summary)
    print(summary)
    
    # Save summary
    with open(f"/home/opc/automation/export/job_template_summary_{timestamp}.txt", 'w') as f:
        f.write(summary)

if __name__ == "__main__":
    main()