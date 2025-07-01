#!/usr/bin/env python3
"""
Reconcile existing HCP jobs with Airtable reservations for both DEV and PROD environments.
Matches jobs based on property, date/time, and customer.
Updates Airtable reservations with Service Job ID when a match is found.

Can be run from command line or called from Airtable automation.
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
import pytz
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
try:
    from src.automation.config_wrapper import Config
except ImportError:
    # If that fails, try without src prefix (for running from within src directory)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from automation.config_wrapper import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HCPJobReconciler:
    def __init__(self, environment='dev'):
        self.environment = environment.lower()
        
        # Load environment-specific configuration
        if self.environment == 'prod' or self.environment == 'production':
            self.environment = 'production'
            env_path = '/home/opc/automation/config/environments/prod/.env'
            load_dotenv(env_path)
            self.AIRTABLE_API_KEY = os.getenv('PROD_AIRTABLE_API_KEY')
            self.AIRTABLE_BASE_ID = os.getenv('PROD_AIRTABLE_BASE_ID')
            self.HCP_TOKEN = os.getenv('PROD_HCP_TOKEN')
        else:
            self.environment = 'development'
            env_path = '/home/opc/automation/config/environments/dev/.env'
            load_dotenv(env_path)
            self.AIRTABLE_API_KEY = os.getenv('DEV_AIRTABLE_API_KEY')
            self.AIRTABLE_BASE_ID = os.getenv('DEV_AIRTABLE_BASE_ID')
            self.HCP_TOKEN = os.getenv('DEV_HCP_TOKEN')
        
        if not all([self.AIRTABLE_API_KEY, self.AIRTABLE_BASE_ID, self.HCP_TOKEN]):
            logger.error(f'Missing required {self.environment.upper()} environment variables')
            sys.exit(1)
            
        logger.info(f"Initializing HCP Job Reconciler for {self.environment.upper()} environment")
        
        # Initialize Airtable API
        self.api = Api(self.AIRTABLE_API_KEY)
        self.base = self.api.base(self.AIRTABLE_BASE_ID)
        self.reservations_table = self.base.table('Reservations')
        self.properties_table = self.base.table('Properties')
        self.customers_table = self.base.table('Customers')
        
        # Cache for property mappings
        self._property_cache = {}
        
    def hcp_request(self, path, method='GET', params=None, retry_count=0, max_retries=3):
        """Make a request to HCP API with rate limit handling."""
        # HCP API doesn't use /api/v1 prefix - just the direct path
        url = f'https://api.housecallpro.com{path}'
        headers = {
            'Authorization': f'Token {self.HCP_TOKEN}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': f'HCP-Reconciliation-{self.environment}/1.0.0'
        }
        
        try:
            logger.debug(f"HCP API Request: {method} {url}")
            if params and method == 'GET':
                logger.debug(f"Query params: {params}")
                
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.request(method, url, headers=headers, json=params)
            
            logger.debug(f"Response Status: {response.status_code}")
            
            # Check for rate limiting
            if response.status_code == 429:
                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) reached for rate limiting")
                    return None
                
                # Get the reset time from header
                reset_time = response.headers.get('RateLimit-Reset')
                retry_after = response.headers.get('Retry-After')
                
                if reset_time:
                    # Convert Unix timestamp to datetime
                    reset_datetime = datetime.fromtimestamp(int(reset_time))
                    wait_seconds = max(1, (reset_datetime - datetime.now()).total_seconds())
                    logger.warning(f"Rate limit hit. Waiting {wait_seconds:.1f}s until reset at {reset_datetime}")
                elif retry_after:
                    wait_seconds = int(retry_after)
                    logger.warning(f"Rate limit hit. Waiting {wait_seconds}s as requested")
                else:
                    # Default wait if no header provided
                    wait_seconds = 60
                    logger.warning(f"Rate limit hit. No reset time provided, waiting {wait_seconds}s")
                
                # Wait and retry
                time.sleep(wait_seconds)
                return self.hcp_request(path, method, params, retry_count + 1, max_retries)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HCP API HTTP error: {e}")
            logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return None
        except Exception as e:
            logger.error(f"HCP API error: {e}")
            return None
            
    def get_reservations_without_jobs(self, limit=None, offset=None, reservation_id=None, force=False):
        """Fetch Airtable reservations that don't have Service Job IDs (or all if force=True)."""
        
        if reservation_id:
            # Fetch specific reservation by ID
            logger.info(f"Fetching specific reservation ID: {reservation_id}")
            try:
                # First try by record ID
                try:
                    reservation = self.reservations_table.get(f"rec{reservation_id}" if not reservation_id.startswith('rec') else reservation_id)
                    return [reservation]
                except:
                    # If that fails, try by ID field
                    formula = f"{{ID}} = '{reservation_id}'"
                    reservations = self.reservations_table.all(formula=formula)
                    if reservations:
                        logger.info(f"Found reservation by ID field: {reservation_id}")
                        return reservations
                    else:
                        logger.error(f"Reservation {reservation_id} not found")
                        return []
            except Exception as e:
                logger.error(f"Error fetching reservation {reservation_id}: {e}")
                return []
        else:
            if force:
                # Force mode - get all reservations with jobs that have Wrong Time status
                logger.info("FORCE MODE: Fetching reservations with Wrong Time status...")
                formula = "AND({Service Job ID}, {Sync Status} = 'Wrong Time', NOT({Status} = 'Old'), {Entry Type} = 'Reservation')"
            else:
                # Normal flow - get all without jobs
                logger.info("Fetching reservations without Service Job IDs...")
                # Get reservations with no job ID and a final service time
                formula = "AND(NOT({Service Job ID}), {Final Service Time}, NOT({Status} = 'Old'), {Entry Type} = 'Reservation')"
            
            # Fetch all matching records first
            all_reservations = self.reservations_table.all(formula=formula)
            total_count = len(all_reservations)
            
            if force:
                logger.info(f"Found {total_count} total reservations with Wrong Time status")
            else:
                logger.info(f"Found {total_count} total reservations without job IDs")
            
            # Apply offset and limit
            if offset is not None:
                all_reservations = all_reservations[offset:]
                if all_reservations:
                    logger.info(f"Skipping first {offset} records")
            
            if limit is not None and all_reservations:
                all_reservations = all_reservations[:limit]
                logger.info(f"Processing {len(all_reservations)} records")
            
            return all_reservations
        
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
                'expand[]': ['customer', 'address', 'schedule', 'appointments']
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
        
    def update_reservation_with_job(self, reservation_id, job_id, job_status, job_data, expected_time):
        """Update Airtable reservation with matched job ID and sync status."""
        try:
            # Get appointment ID if it exists
            appointment_id = None
            scheduled_time = None
            
            # Get scheduled time from job
            if job_data.get('schedule', {}).get('scheduled_start'):
                scheduled_time = job_data['schedule']['scheduled_start']
            
            # Extract assignee information
            assignee = ""
            employees = job_data.get('assigned_employees', [])
            if employees:
                names = []
                for emp in employees:
                    if isinstance(emp, dict):
                        first = emp.get('first_name', '')
                        last = emp.get('last_name', '')
                        if first or last:
                            names.append(f"{first} {last}".strip())
                assignee = ", ".join(names) if names else ""
                if assignee:
                    logger.info(f"    Found assignee(s): {assignee}")
            
            # Extract work timestamps
            work_timestamps = job_data.get('work_timestamps', {})
            on_my_way_at = work_timestamps.get('on_my_way_at')
            started_at = work_timestamps.get('started_at') 
            completed_at = work_timestamps.get('completed_at')
            
            if any([on_my_way_at, started_at, completed_at]):
                logger.info(f"    Found work timestamps:")
                if on_my_way_at:
                    logger.info(f"      On my way: {on_my_way_at}")
                if started_at:
                    logger.info(f"      Started: {started_at}")
                if completed_at:
                    logger.info(f"      Completed: {completed_at}")
            
            # Try to get appointment ID from job data
            if job_data.get('appointments') and len(job_data['appointments']) > 0:
                appointment_id = job_data['appointments'][0]['id']
                logger.info(f"    Found appointment ID: {appointment_id}")
            else:
                # Try fetching appointments separately
                logger.info(f"    Fetching appointments for job {job_id}")
                try:
                    appointments_resp = self.hcp_request(f'/jobs/{job_id}/appointments')
                    if appointments_resp and appointments_resp.get('appointments'):
                        if len(appointments_resp['appointments']) > 0:
                            appointment_id = appointments_resp['appointments'][0]['id']
                            logger.info(f"    Found appointment ID via separate fetch: {appointment_id}")
                except Exception as e:
                    logger.warning(f"    Could not fetch appointments: {e}")
            
            # Compare scheduled time with expected time
            sync_status = 'Not Created'
            sync_details = f"Matched existing HCP job {job_id} during reconciliation"
            
            if scheduled_time and expected_time:
                # Parse times
                sched_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                expect_dt = datetime.fromisoformat(expected_time.replace('Z', '+00:00'))
                
                # Convert to Arizona timezone for display
                AZ_TZ = pytz.timezone('America/Phoenix')
                sched_dt_az = sched_dt.astimezone(AZ_TZ)
                expect_dt_az = expect_dt.astimezone(AZ_TZ)
                
                # Format for comparison
                sched_date = sched_dt_az.strftime('%Y-%m-%d')
                expect_date = expect_dt_az.strftime('%Y-%m-%d')
                
                sched_hour_min = sched_dt_az.strftime('%H:%M')
                expect_hour_min = expect_dt_az.strftime('%H:%M')
                
                if sched_date != expect_date:
                    sync_status = 'Wrong Date'
                    sync_details = f"Job scheduled for {sched_dt_az.strftime('%b %d at %I:%M %p')} but expected {expect_dt_az.strftime('%b %d at %I:%M %p')}"
                elif sched_hour_min != expect_hour_min:
                    sync_status = 'Wrong Time'
                    # Show both actual times instead of saying "scheduled for X but expected X"
                    sync_details = f"Airtable shows {expect_dt_az.strftime('%I:%M %p')} but HCP shows {sched_dt_az.strftime('%I:%M %p')}"
                else:
                    sync_status = 'Synced'
                    sync_details = f"Job {job_id} correctly scheduled for {expect_dt_az.strftime('%b %d at %I:%M %p')}"
            
            # Build update fields
            update_fields = {
                'Service Job ID': job_id,
                'Job Status': job_status,
                'Sync Status': sync_status,
                'Sync Date and Time': datetime.now().isoformat(),
                'Schedule Sync Details': sync_details
            }
            
            # Add appointment ID if found
            if appointment_id:
                update_fields['Service Appointment ID'] = appointment_id
            
            # Add scheduled time if available
            if scheduled_time:
                update_fields['Scheduled Service Time'] = scheduled_time
            
            # Add assignee if found
            if assignee:
                update_fields['Assignee'] = assignee
            
            # Add work timestamps if available
            if on_my_way_at:
                update_fields['On My Way Time'] = on_my_way_at
            if started_at:
                update_fields['Job Started Time'] = started_at
            if completed_at:
                update_fields['Job Completed Time'] = completed_at
            
            # Update Airtable
            self.reservations_table.update(reservation_id, update_fields)
            logger.info(f"    ✓ Updated Airtable with sync status: {sync_status}")
            
            return True
        except Exception as e:
            logger.error(f"Error updating reservation {reservation_id}: {e}")
            return False
            
    def reconcile(self, dry_run=True, limit=None, offset=None, reservation_id=None, force=False):
        """Main reconciliation process."""
        logger.info(f"Starting HCP job reconciliation for {self.environment.upper()} environment...")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        if force:
            logger.info("FORCE MODE: Will process records with Wrong Time status")
        if offset is not None:
            logger.info(f"Offset: {offset}")
        
        if reservation_id:
            logger.info(f"Processing single reservation: {reservation_id}")
        
        # Get data
        reservations = self.get_reservations_without_jobs(limit=limit, offset=offset, reservation_id=reservation_id, force=force)
        if not reservations:
            logger.info("No reservations to reconcile")
            return {'matched': 0, 'unmatched': 0, 'total': 0}
            
        jobs = self.get_hcp_jobs()
        if not jobs:
            logger.info("No HCP jobs found")
            return {'matched': 0, 'unmatched': 0, 'total': len(reservations)}
            
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
                job_status = self._map_work_status(matched_job.get('work_status', 'unknown'))
                expected_time = reservation['fields'].get('Final Service Time')
                
                if dry_run:
                    logger.info(f"  ✓ Would update with job {job_id} (status: {job_status})")
                    matched_count += 1
                else:
                    if self.update_reservation_with_job(reservation['id'], job_id, job_status, matched_job, expected_time):
                        logger.info(f"  ✓ Updated with job {job_id} (status: {job_status})")
                        matched_count += 1
                    else:
                        logger.error(f"  ✗ Failed to update")
                        unmatched_count += 1
            else:
                logger.info(f"  ✗ No matching job found")
                unmatched_count += 1
                
        # Summary
        logger.info("\n" + "="*50)
        logger.info("RECONCILIATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Environment: {self.environment.upper()}")
        if reservation_id:
            logger.info(f"Single reservation {reservation_id}: {'MATCHED' if matched_count > 0 else 'NO MATCH FOUND'}")
        else:
            logger.info(f"Total reservations processed: {len(reservations)}")
        logger.info(f"Matched: {matched_count}")
        logger.info(f"Unmatched: {unmatched_count}")
        
        if dry_run:
            logger.info("\n💡 To execute these updates, run with --execute flag")
            
        return {
            'matched': matched_count,
            'unmatched': unmatched_count,
            'total': len(reservations),
            'environment': self.environment,
            'single_reservation': reservation_id if reservation_id else None
        }
    
    def _map_work_status(self, work_status):
        """Map HCP work status to Airtable job status"""
        if not work_status:
            return ""
        work_status = work_status.lower()
        if "complete" in work_status:
            return "Completed"
        elif "cancel" in work_status:
            return "Canceled"
        elif "unscheduled" in work_status:
            return "Unscheduled"
        elif "needs scheduling" in work_status:
            return "Unscheduled"
        elif "scheduled" in work_status:
            return "Scheduled"
        elif "in progress" in work_status:
            return "In Progress"
        return work_status


def run_from_airtable(environment='dev', execute=False, limit=None):
    """
    Entry point for Airtable automation.
    Returns JSON response for Airtable to display.
    """
    try:
        reconciler = HCPJobReconciler(environment=environment)
        result = reconciler.reconcile(dry_run=not execute, limit=limit)
        
        return {
            'success': True,
            'environment': environment,
            'mode': 'execute' if execute else 'dry_run',
            'results': result,
            'message': f"Successfully {'executed' if execute else 'analyzed'} reconciliation"
        }
    except Exception as e:
        logger.error(f"Error in reconciliation: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'environment': environment,
            'mode': 'execute' if execute else 'dry_run'
        }


def main():
    parser = argparse.ArgumentParser(description='Reconcile HCP jobs with Airtable reservations')
    parser.add_argument('--env', choices=['dev', 'prod'], default='dev',
                        help='Environment to run in (default: dev)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be updated without making changes (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform the updates (overrides --dry-run)')
    parser.add_argument('--limit', type=int,
                        help='Limit number of reservations to process')
    parser.add_argument('--offset', type=int,
                        help='Skip first N reservations (for batch processing)')
    parser.add_argument('--reservation-id', type=str,
                        help='Process a specific reservation ID (e.g., 35369 or rec...)')
    parser.add_argument('--force', action='store_true',
                        help='Force update records that already have job IDs but Wrong Time status')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON (for Airtable integration)')
    
    args = parser.parse_args()
    dry_run = not args.execute
    
    if args.json:
        # JSON output for Airtable
        result = run_from_airtable(
            environment=args.env,
            execute=not dry_run,
            limit=args.limit
        )
        print(json.dumps(result, indent=2))
    else:
        # Regular console output
        reconciler = HCPJobReconciler(environment=args.env)
        reconciler.reconcile(dry_run=dry_run, limit=args.limit, offset=args.offset, 
                           reservation_id=args.reservation_id, force=args.force)


if __name__ == '__main__':
    main()