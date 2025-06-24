#!/usr/bin/env python3
"""
Reconcile existing HCP jobs with Airtable reservations for DEV environment.
Matches jobs based on property, date/time, and customer.
Updates Airtable reservations with Service Job ID when a match is found.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import requests
from pyairtable import Api
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load dev environment
env_path = '/home/opc/automation/config/environments/dev/.env'
load_dotenv(env_path)

# Dev configuration
AIRTABLE_API_KEY = os.getenv('DEV_AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('DEV_AIRTABLE_BASE_ID')
HCP_TOKEN = os.getenv('DEV_HCP_TOKEN')

if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, HCP_TOKEN]):
    logger.error('Missing required DEV environment variables')
    sys.exit(1)

class HCPJobReconciler:
    def __init__(self):
        self.api = Api(AIRTABLE_API_KEY)
        self.base = self.api.base(AIRTABLE_BASE_ID)
        self.reservations_table = self.base.table('Reservations')
        self.properties_table = self.base.table('Properties')
        self.customers_table = self.base.table('Customers')
        
    def hcp_request(self, path, method='GET', params=None):
        """Make a request to HCP API with error handling."""
        url = f'https://api.housecallpro.com{path}'
        headers = {
            'Authorization': f'Token {HCP_TOKEN}',
            'Accept': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.request(method, url, headers=headers, json=params)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HCP API error: {e}")
            return None
            
    def get_reservations_without_jobs(self):
        """Fetch Airtable reservations that don't have Service Job IDs."""
        logger.info("Fetching reservations without Service Job IDs...")
        
        # Get reservations with no job ID and a final service time
        formula = "AND(NOT({Service Job ID}), {Final Service Time}, NOT({Status} = 'Old'))"
        
        reservations = self.reservations_table.all(formula=formula)
        logger.info(f"Found {len(reservations)} reservations without job IDs")
        
        return reservations
        
    def get_hcp_jobs(self, start_date=None, end_date=None):
        """Fetch all jobs from HCP within date range."""
        logger.info("Fetching jobs from HCP...")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = (datetime.now() + timedelta(days=90)).isoformat()
            
        all_jobs = []
        page = 1
        
        while True:
            params = {
                'page': page,
                'page_size': 100,
                'scheduled_start_min': start_date,
                'scheduled_start_max': end_date,
                'expand': 'customer,address,schedule'
            }
            
            result = self.hcp_request('/jobs', params=params)
            if not result or 'jobs' not in result:
                break
                
            jobs = result.get('jobs', [])
            if not jobs:
                break
                
            all_jobs.extend(jobs)
            logger.info(f"  Fetched page {page}: {len(jobs)} jobs")
            
            if len(jobs) < 100:  # Last page
                break
                
            page += 1
            
        logger.info(f"Total HCP jobs fetched: {len(all_jobs)}")
        return all_jobs
        
    def get_property_hcp_mappings(self):
        """Get mapping of Property IDs to HCP Customer/Address IDs."""
        logger.info("Building property to HCP mapping...")
        
        properties = self.properties_table.all()
        mapping = {}
        
        for prop in properties:
            prop_id = prop['id']
            fields = prop['fields']
            
            # Get HCP customer ID from linked customer record
            customer_links = fields.get('HCP Customer ID', [])
            if customer_links:
                try:
                    # Fetch the linked customer record
                    customer_record = self.customers_table.get(customer_links[0])
                    hcp_customer_id = customer_record['fields'].get('HCP Customer ID')
                    
                    mapping[prop_id] = {
                        'property_name': fields.get('Property Name'),
                        'hcp_customer_id': hcp_customer_id,
                        'hcp_address_id': fields.get('HCP Address ID')
                    }
                except Exception as e:
                    logger.error(f"Error fetching customer for property {prop_id}: {e}")
                    
        logger.info(f"Mapped {len(mapping)} properties to HCP IDs")
        return mapping
        
    def match_reservation_to_job(self, reservation, jobs, property_mapping):
        """Find matching HCP job for a reservation."""
        res_fields = reservation['fields']
        
        # Get property info
        prop_links = res_fields.get('Property ID', [])
        if not prop_links:
            return None
            
        prop_id = prop_links[0]
        if prop_id not in property_mapping:
            return None
            
        prop_info = property_mapping[prop_id]
        hcp_customer_id = prop_info['hcp_customer_id']
        hcp_address_id = prop_info['hcp_address_id']
        
        if not hcp_customer_id or not hcp_address_id:
            return None
            
        # Get reservation time
        final_time = res_fields.get('Final Service Time')
        if not final_time:
            return None
            
        res_datetime = datetime.fromisoformat(final_time.replace('Z', '+00:00'))
        
        # Find matching jobs
        matches = []
        
        for job in jobs:
            # Check customer match
            if job.get('customer', {}).get('id') != hcp_customer_id:
                continue
                
            # Check address match
            if job.get('address', {}).get('id') != hcp_address_id:
                continue
                
            # Check time match (within 1 hour window)
            job_start = job.get('schedule', {}).get('scheduled_start')
            if not job_start:
                continue
                
            job_datetime = datetime.fromisoformat(job_start.replace('Z', '+00:00'))
            time_diff = abs((job_datetime - res_datetime).total_seconds())
            
            if time_diff <= 3600:  # Within 1 hour
                matches.append({
                    'job': job,
                    'time_diff': time_diff
                })
                
        if not matches:
            return None
            
        # Return the closest time match
        matches.sort(key=lambda x: x['time_diff'])
        best_match = matches[0]['job']
        
        logger.info(f"  Found match: Job {best_match['id']} for reservation {reservation['id']}")
        logger.info(f"    Property: {prop_info['property_name']}")
        logger.info(f"    Time diff: {matches[0]['time_diff']/60:.1f} minutes")
        
        return best_match
        
    def update_reservation_with_job(self, reservation_id, job_id, job_status):
        """Update Airtable reservation with matched job ID."""
        try:
            self.reservations_table.update(reservation_id, {
                'Service Job ID': job_id,
                'Job Status': job_status,
                'Sync Status': 'Matched',
                'Sync Date and Time': datetime.now().isoformat(),
                'Schedule Sync Details': f"Matched existing HCP job {job_id} during reconciliation"
            })
            return True
        except Exception as e:
            logger.error(f"Error updating reservation {reservation_id}: {e}")
            return False
            
    def reconcile(self, dry_run=True):
        """Main reconciliation process."""
        logger.info("Starting HCP job reconciliation for DEV environment...")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        
        # Get data
        reservations = self.get_reservations_without_jobs()
        if not reservations:
            logger.info("No reservations to reconcile")
            return
            
        jobs = self.get_hcp_jobs()
        if not jobs:
            logger.info("No HCP jobs found")
            return
            
        property_mapping = self.get_property_hcp_mappings()
        
        # Match reservations to jobs
        matched_count = 0
        unmatched_count = 0
        
        logger.info("\nMatching reservations to jobs...")
        for reservation in reservations:
            res_uid = reservation['fields'].get('Reservation UID', reservation['id'])
            logger.info(f"\nProcessing reservation {res_uid}")
            
            matched_job = self.match_reservation_to_job(reservation, jobs, property_mapping)
            
            if matched_job:
                job_id = matched_job['id']
                job_status = matched_job.get('work_status', 'unknown')
                
                if dry_run:
                    logger.info(f"  ✓ Would update with job {job_id} (status: {job_status})")
                else:
                    if self.update_reservation_with_job(reservation['id'], job_id, job_status):
                        logger.info(f"  ✓ Updated with job {job_id} (status: {job_status})")
                        matched_count += 1
                    else:
                        logger.error(f"  ✗ Failed to update")
            else:
                logger.info(f"  ✗ No matching job found")
                unmatched_count += 1
                
        # Summary
        logger.info("\n" + "="*50)
        logger.info("RECONCILIATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total reservations processed: {len(reservations)}")
        logger.info(f"Matched: {matched_count}")
        logger.info(f"Unmatched: {unmatched_count}")
        
        if dry_run:
            logger.info("\n💡 To execute these updates, run with --execute flag")

def main():
    parser = argparse.ArgumentParser(description='Reconcile HCP jobs with Airtable reservations')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be updated without making changes (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform the updates (overrides --dry-run)')
    
    args = parser.parse_args()
    dry_run = not args.execute
    
    reconciler = HCPJobReconciler()
    reconciler.reconcile(dry_run)

if __name__ == '__main__':
    main()