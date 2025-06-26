#!/usr/bin/env python3
"""
Optimized job template finder using HCP MCP capabilities.
Finds and populates job template IDs for properties with better performance.
"""

import os
import sys
import csv
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parents[4]))
# from src.automation.config_prod import ConfigProd  # Not needed for this script

# Setup logging
log_dir = Path("/home/opc/automation/src/automation/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"job_template_finder_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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

# Job categorization patterns (compiled regex for performance)
TURNOVER_PATTERNS = [
    re.compile(r'\s+ng\s+', re.IGNORECASE),
    re.compile(r'next\s+guest', re.IGNORECASE),
    re.compile(r'same\s*day', re.IGNORECASE),
    re.compile(r'STR\s+SAME\s+DAY', re.IGNORECASE),
    re.compile(r'STR\s+Next\s+Guest', re.IGNORECASE)
]
INSPECTION_PATTERN = re.compile(r'inspection', re.IGNORECASE)
RETURN_LAUNDRY_PATTERN = re.compile(r'return\s+laundry', re.IGNORECASE)

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between customer API calls
CONCURRENT_LIMIT = 5    # max concurrent requests

class RateLimiter:
    """Handle rate limiting with exponential backoff."""
    def __init__(self):
        self.reset_time = None
        self.request_count = 0
        
    async def wait_if_needed(self):
        """Wait if rate limited."""
        if self.reset_time and time.time() < self.reset_time:
            wait_time = self.reset_time - time.time()
            logger.warning(f"Rate limited. Waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
            
    def update_from_headers(self, headers):
        """Update rate limit info from response headers."""
        if 'RateLimit-Reset' in headers:
            self.reset_time = int(headers['RateLimit-Reset'])

rate_limiter = RateLimiter()

async def fetch_jobs_for_customer(session: aiohttp.ClientSession, customer_id: str) -> List[Dict]:
    """Fetch all jobs for a customer asynchronously."""
    all_jobs = []
    page = 1
    
    headers = {
        "Authorization": f"Bearer {HCP_API_KEY}",
        "Content-Type": "application/json"
    }
    
    while True:
        await rate_limiter.wait_if_needed()
        
        url = f"{HCP_BASE_URL}/v1/jobs?customer_id={customer_id}&page={page}&page_size=100"
        
        try:
            async with session.get(url, headers=headers) as response:
                rate_limiter.update_from_headers(response.headers)
                
                if response.status == 429:
                    await rate_limiter.wait_if_needed()
                    continue
                    
                if response.status != 200:
                    logger.error(f"Error fetching jobs for {customer_id}: {response.status}")
                    break
                    
                data = await response.json()
                jobs = data.get('data', [])
                all_jobs.extend(jobs)
                
                if not data.get('has_more', False):
                    break
                    
                page += 1
                
        except Exception as e:
            logger.error(f"Error fetching jobs for {customer_id}: {e}")
            break
    
    return all_jobs

def categorize_job(description: str) -> Optional[str]:
    """Categorize job using compiled regex patterns."""
    # Priority: Return Laundry > Inspection > Turnover
    if RETURN_LAUNDRY_PATTERN.search(description):
        return 'return_laundry'
    
    if INSPECTION_PATTERN.search(description):
        return 'inspection'
    
    # Turnover must NOT contain inspection or return laundry
    if not INSPECTION_PATTERN.search(description) and not RETURN_LAUNDRY_PATTERN.search(description):
        for pattern in TURNOVER_PATTERNS:
            if pattern.search(description):
                return 'turnover'
    
    return None

def find_templates_for_address(jobs: List[Dict], address_id: str) -> Dict[str, Optional[str]]:
    """Find job templates for a specific address."""
    templates = {
        'turnover': None,
        'inspection': None,
        'return_laundry': None
    }
    
    # Filter jobs for this address
    address_jobs = [
        job for job in jobs 
        if job.get('address', {}).get('id') == address_id
        and job.get('work_status') not in ['canceled', 'deleted']
    ]
    
    # Categorize and find most recent
    categorized = {
        'turnover': [],
        'inspection': [],
        'return_laundry': []
    }
    
    for job in address_jobs:
        description = job.get('description', '')
        job_type = categorize_job(description)
        if job_type:
            categorized[job_type].append(job)
    
    # Get most recent of each type
    for job_type, jobs_list in categorized.items():
        if jobs_list:
            # Sort by created_at descending
            jobs_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            templates[job_type] = jobs_list[0].get('id')
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Found {job_type}: {templates[job_type]} - {jobs_list[0].get('description')[:50]}")
    
    return templates

async def process_customer_properties(session: aiohttp.ClientSession, 
                                    customer_id: str, 
                                    customer_properties: List[Dict]) -> List[Dict]:
    """Process all properties for a single customer."""
    logger.info(f"Processing customer {customer_id} with {len(customer_properties)} properties")
    
    # Fetch all jobs for this customer once
    jobs = await fetch_jobs_for_customer(session, customer_id)
    logger.info(f"Found {len(jobs)} total jobs for customer {customer_id}")
    
    # Process each property
    for prop in customer_properties:
        address_id = prop.get('HCP Address ID')
        if not address_id:
            continue
            
        # Skip if already has all templates
        if (prop.get('Turnover Job Template ID') and 
            prop.get('Inspection Job Template ID') and 
            prop.get('Return Laundry Job Template ID')):
            continue
        
        # Find templates for this address
        templates = find_templates_for_address(jobs, address_id)
        
        # Update property
        if templates['turnover']:
            prop['Turnover Job Template ID'] = templates['turnover']
        if templates['inspection']:
            prop['Inspection Job Template ID'] = templates['inspection']
        if templates['return_laundry']:
            prop['Return Laundry Job Template ID'] = templates['return_laundry']
    
    return customer_properties

async def process_all_properties(properties: List[Dict]) -> List[Dict]:
    """Process all properties grouped by customer for efficiency."""
    # Group properties by customer
    customer_groups = {}
    for prop in properties:
        customer_id = prop.get('HCP Customer ID')
        if customer_id and prop.get('HCP Address ID'):
            if customer_id not in customer_groups:
                customer_groups[customer_id] = []
            customer_groups[customer_id].append(prop)
    
    logger.info(f"Processing {len(customer_groups)} unique customers")
    
    # Process customers with rate limiting
    async with aiohttp.ClientSession() as session:
        for idx, (customer_id, customer_props) in enumerate(customer_groups.items(), 1):
            logger.info(f"\nProcessing customer {idx}/{len(customer_groups)}: {customer_id}")
            await process_customer_properties(session, customer_id, customer_props)
            
            # Rate limiting between customers
            if idx < len(customer_groups):
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    return properties

def load_properties_csv(file_path: str) -> List[Dict]:
    """Load properties from CSV file."""
    properties = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties

def save_results(properties: List[Dict], output_dir: Path, timestamp: str):
    """Save updated properties and generate reports."""
    # Save updated properties
    output_file = output_dir / f"Prod_Airtable_Properties_Updated_{timestamp}.csv"
    
    if properties:
        fieldnames = list(properties[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(properties)
    
    # Generate summary statistics
    total = len(properties)
    has_turnover = sum(1 for p in properties if p.get('Turnover Job Template ID'))
    has_inspection = sum(1 for p in properties if p.get('Inspection Job Template ID'))
    has_return_laundry = sum(1 for p in properties if p.get('Return Laundry Job Template ID'))
    has_all = sum(1 for p in properties 
                  if p.get('Turnover Job Template ID') and 
                     p.get('Inspection Job Template ID') and 
                     p.get('Return Laundry Job Template ID'))
    
    summary = f"""Job Template Extraction Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================
Total Properties: {total}

Templates Found:
- Turnover: {has_turnover}/{total} ({has_turnover/total*100:.1f}%)
- Inspection: {has_inspection}/{total} ({has_inspection/total*100:.1f}%)
- Return Laundry: {has_return_laundry}/{total} ({has_return_laundry/total*100:.1f}%)

Complete (all 3): {has_all}/{total} ({has_all/total*100:.1f}%)

Output: {output_file}
"""
    
    # Save summary
    with open(output_dir / f'job_template_summary_{timestamp}.txt', 'w') as f:
        f.write(summary)
    
    # Generate missing report
    missing = [p for p in properties 
               if not p.get('Turnover Job Template ID') or 
                  not p.get('Inspection Job Template ID') or 
                  not p.get('Return Laundry Job Template ID')]
    
    if missing:
        with open(output_dir / f'missing_templates_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Property Name', 'Customer ID', 'Address ID', 'Missing Types'])
            for prop in missing:
                missing_types = []
                if not prop.get('Turnover Job Template ID'):
                    missing_types.append('Turnover')
                if not prop.get('Inspection Job Template ID'):
                    missing_types.append('Inspection')
                if not prop.get('Return Laundry Job Template ID'):
                    missing_types.append('Return Laundry')
                
                writer.writerow([
                    prop.get('Property Name', ''),
                    prop.get('HCP Customer ID', ''),
                    prop.get('HCP Address ID', ''),
                    ', '.join(missing_types)
                ])
    
    logger.info(f"\n{summary}")
    return output_file

async def main():
    """Main execution."""
    start_time = time.time()
    logger.info("Starting optimized job template finder...")
    
    # Load properties
    input_file = "/home/opc/automation/export/Prod_Airtable_Properties.csv"
    properties = load_properties_csv(input_file)
    logger.info(f"Loaded {len(properties)} properties")
    
    # Process properties
    properties = await process_all_properties(properties)
    
    # Save results
    output_dir = Path("/home/opc/automation/export")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = save_results(properties, output_dir, timestamp)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed:.1f} seconds")
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())