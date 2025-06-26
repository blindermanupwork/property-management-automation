#!/usr/bin/env python3
"""
Find and populate job template IDs for properties by searching HCP job history.

For each property address, finds the most recent:
- Turnover job (contains " ng " or "next guest" or "sameday", excludes inspection/return laundry)
- Inspection job (contains "inspection")
- Return Laundry job (contains "return laundry")
"""

import os
import sys
import csv
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parents[4]))
# from src.automation.config_prod import ConfigProd  # Not needed for this script

# Setup logging
log_dir = Path("/home/opc/automation/src/automation/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"job_template_finder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HCP API Configuration
HCP_API_KEY = os.getenv('HCP_API_KEY_PROD')
HCP_BASE_URL = "https://api.housecallpro.com"
HCP_HEADERS = {
    "Authorization": f"Bearer {HCP_API_KEY}",
    "Content-Type": "application/json"
}

# Job categorization patterns
TURNOVER_PATTERNS = [" ng ", "next guest", "sameday", "same day", "STR SAME DAY", "STR Next Guest"]
INSPECTION_PATTERNS = ["inspection"]
RETURN_LAUNDRY_PATTERNS = ["return laundry"]

# Rate limiting
RATE_LIMIT_DELAY = 0.5  # seconds between API calls
MAX_RETRIES = 3

def load_properties_csv(file_path: str) -> List[Dict]:
    """Load properties from CSV file."""
    properties = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('HCP Address ID'):
                properties.append(row)
    return properties

def make_api_request(url: str, retry_count: int = 0) -> Optional[Dict]:
    """Make API request with retry logic and rate limit handling."""
    try:
        response = requests.get(url, headers=HCP_HEADERS)
        
        # Handle rate limiting
        if response.status_code == 429:
            reset_time = response.headers.get('RateLimit-Reset')
            if reset_time:
                wait_time = max(int(reset_time) - int(time.time()), 1)
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return make_api_request(url, retry_count)
            else:
                # Default wait if no reset time provided
                wait_time = 60
                logger.warning(f"Rate limited without reset time. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return make_api_request(url, retry_count)
        
        # Handle other errors
        if response.status_code != 200:
            if retry_count < MAX_RETRIES:
                logger.warning(f"Request failed with status {response.status_code}. Retrying...")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return make_api_request(url, retry_count + 1)
            else:
                logger.error(f"Request failed after {MAX_RETRIES} retries: {response.status_code}")
                return None
        
        return response.json()
    
    except Exception as e:
        logger.error(f"Request error: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(2 ** retry_count)
            return make_api_request(url, retry_count + 1)
        return None

def get_jobs_for_address(customer_id: str, address_id: str) -> List[Dict]:
    """Get all jobs for a specific address."""
    all_jobs = []
    page = 1
    
    while True:
        url = f"{HCP_BASE_URL}/v1/jobs?customer_id={customer_id}&page={page}&page_size=100"
        logger.debug(f"Fetching page {page} for customer {customer_id}")
        
        data = make_api_request(url)
        if not data or 'data' not in data:
            break
        
        # Filter jobs for this specific address
        address_jobs = [
            job for job in data['data']
            if job.get('address', {}).get('id') == address_id
        ]
        all_jobs.extend(address_jobs)
        
        # Check if there are more pages
        if not data.get('has_more', False):
            break
        
        page += 1
        time.sleep(RATE_LIMIT_DELAY)
    
    return all_jobs

def categorize_job(job: Dict) -> Optional[str]:
    """Determine job type based on description."""
    description = job.get('description', '').lower()
    
    # Priority order: Return Laundry > Inspection > Turnover
    for pattern in RETURN_LAUNDRY_PATTERNS:
        if pattern in description:
            return 'return_laundry'
    
    for pattern in INSPECTION_PATTERNS:
        if pattern in description:
            return 'inspection'
    
    # Turnover must NOT contain inspection or return laundry
    if 'inspection' not in description and 'return laundry' not in description:
        for pattern in TURNOVER_PATTERNS:
            if pattern in description:
                return 'turnover'
    
    return None

def find_job_templates(jobs: List[Dict]) -> Dict[str, Optional[str]]:
    """Find the most recent job of each type."""
    templates = {
        'turnover': None,
        'inspection': None,
        'return_laundry': None
    }
    
    # Group jobs by type
    categorized_jobs = {
        'turnover': [],
        'inspection': [],
        'return_laundry': []
    }
    
    for job in jobs:
        # Skip canceled or deleted jobs
        if job.get('work_status') in ['canceled', 'deleted']:
            continue
        
        job_type = categorize_job(job)
        if job_type:
            categorized_jobs[job_type].append(job)
    
    # Find most recent job of each type
    for job_type, job_list in categorized_jobs.items():
        if job_list:
            # Sort by created_at descending
            job_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            templates[job_type] = job_list[0].get('id')
            
            logger.info(f"Found {job_type} template: {templates[job_type]} - {job_list[0].get('description')[:50]}...")
    
    return templates

def process_properties(properties: List[Dict]) -> List[Dict]:
    """Process all properties and find job templates."""
    total = len(properties)
    
    for idx, prop in enumerate(properties, 1):
        property_name = prop.get('Property Name', 'Unknown')
        customer_id = prop.get('HCP Customer ID', '')
        address_id = prop.get('HCP Address ID', '')
        
        logger.info(f"\nProcessing {idx}/{total}: {property_name}")
        
        if not customer_id or not address_id:
            logger.warning(f"Skipping - missing customer_id or address_id")
            continue
        
        # Skip if already has all templates
        if (prop.get('Turnover Job Template ID') and 
            prop.get('Inspection Job Template ID') and 
            prop.get('Return Laundry Job Template ID')):
            logger.info(f"Skipping - already has all templates")
            continue
        
        # Get jobs for this address
        jobs = get_jobs_for_address(customer_id, address_id)
        logger.info(f"Found {len(jobs)} jobs for this address")
        
        if not jobs:
            continue
        
        # Find templates
        templates = find_job_templates(jobs)
        
        # Update property record
        if templates['turnover']:
            prop['Turnover Job Template ID'] = templates['turnover']
        if templates['inspection']:
            prop['Inspection Job Template ID'] = templates['inspection']
        if templates['return_laundry']:
            prop['Return Laundry Job Template ID'] = templates['return_laundry']
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
    
    return properties

def save_updated_csv(properties: List[Dict], output_path: str):
    """Save updated properties to CSV."""
    if not properties:
        return
    
    # Get all fieldnames from first property
    fieldnames = list(properties[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(properties)

def generate_summary_report(properties: List[Dict], output_dir: Path):
    """Generate summary report of findings."""
    total = len(properties)
    has_turnover = sum(1 for p in properties if p.get('Turnover Job Template ID'))
    has_inspection = sum(1 for p in properties if p.get('Inspection Job Template ID'))
    has_return_laundry = sum(1 for p in properties if p.get('Return Laundry Job Template ID'))
    has_all = sum(1 for p in properties 
                  if p.get('Turnover Job Template ID') and 
                     p.get('Inspection Job Template ID') and 
                     p.get('Return Laundry Job Template ID'))
    
    missing_any = [p for p in properties 
                   if not p.get('Turnover Job Template ID') or 
                      not p.get('Inspection Job Template ID') or 
                      not p.get('Return Laundry Job Template ID')]
    
    summary = f"""Job Template Extraction Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================
Total Properties Processed: {total}

Turnover Jobs Found: {has_turnover}/{total} ({has_turnover/total*100:.1f}%)
Inspection Jobs Found: {has_inspection}/{total} ({has_inspection/total*100:.1f}%)
Return Laundry Jobs Found: {has_return_laundry}/{total} ({has_return_laundry/total*100:.1f}%)

Properties with All 3 Types: {has_all} ({has_all/total*100:.1f}%)
Properties Missing Data: {len(missing_any)}
"""
    
    # Save summary
    with open(output_dir / 'job_template_summary.txt', 'w') as f:
        f.write(summary)
    
    # Save missing properties report
    if missing_any:
        with open(output_dir / 'missing_job_templates.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Property Name', 'HCP Customer ID', 'HCP Address ID', 
                         'Missing Turnover', 'Missing Inspection', 'Missing Return Laundry']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for prop in missing_any:
                writer.writerow({
                    'Property Name': prop.get('Property Name', ''),
                    'HCP Customer ID': prop.get('HCP Customer ID', ''),
                    'HCP Address ID': prop.get('HCP Address ID', ''),
                    'Missing Turnover': 'X' if not prop.get('Turnover Job Template ID') else '',
                    'Missing Inspection': 'X' if not prop.get('Inspection Job Template ID') else '',
                    'Missing Return Laundry': 'X' if not prop.get('Return Laundry Job Template ID') else ''
                })
    
    logger.info(f"\n{summary}")

def main():
    """Main execution."""
    logger.info("Starting job template finder...")
    
    # Input/output paths
    input_file = "/home/opc/automation/export/Prod_Airtable_Properties.csv"
    output_dir = Path("/home/opc/automation/export")
    output_file = output_dir / f"Prod_Airtable_Properties_Updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Load properties
    logger.info(f"Loading properties from {input_file}")
    properties = load_properties_csv(input_file)
    logger.info(f"Loaded {len(properties)} properties")
    
    # Process properties
    updated_properties = process_properties(properties)
    
    # Save results
    logger.info(f"Saving updated properties to {output_file}")
    save_updated_csv(updated_properties, str(output_file))
    
    # Generate summary
    generate_summary_report(updated_properties, output_dir)
    
    logger.info("Job template finder completed!")

if __name__ == "__main__":
    main()