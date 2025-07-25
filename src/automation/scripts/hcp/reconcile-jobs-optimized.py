#!/usr/bin/env python3
"""
Optimized HCP Job Reconciliation Script
Matches existing HCP jobs with Airtable reservations using batch operations,
caching, and concurrent processing for maximum performance.

Performance improvements:
- Batch Airtable operations
- Connection pooling for API requests  
- Smart caching of property mappings
- Concurrent job matching
- Indexed lookups for O(1) job searches
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
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib

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

class OptimizedHCPJobReconciler:
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
            
        logger.info(f"Initializing Optimized HCP Job Reconciler for {self.environment.upper()} environment")
        
        # Initialize Airtable API
        self.api = Api(self.AIRTABLE_API_KEY)
        self.base = self.api.base(self.AIRTABLE_BASE_ID)
        self.reservations_table = self.base.table('Reservations')
        self.properties_table = self.base.table('Properties')
        self.customers_table = self.base.table('Customers')
        
        # Connection pool for HCP API
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {self.HCP_TOKEN}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': f'HCP-Reconciliation-Optimized-{self.environment}/2.0.0'
        })
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Caches
        self._property_cache = {}
        self._customer_cache = {}
        self._job_index = {}  # For O(1) job lookups
        self._cache_stats = {
            'property_hits': 0,
            'property_misses': 0,
            'customer_hits': 0,
            'customer_misses': 0
        }
        
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
            
    def hcp_request(self, path, method='GET', params=None, retry_count=0, max_retries=3):
        """Make a request to HCP API with connection pooling and rate limit handling."""
        url = f'https://api.housecallpro.com{path}'
        
        try:
            logger.debug(f"HCP API Request: {method} {url}")
            if params and method == 'GET':
                logger.debug(f"Query params: {params}")
                
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.request(method, url, json=params, timeout=30)
            
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
            
    def get_reservations_without_jobs_batch(self, limit=None, offset=None, reservation_id=None, force=False):
        """Fetch Airtable reservations in batch with optimized formula."""
        
        if reservation_id:
            # Single reservation lookup
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
            
            # Fetch all matching records with batch optimization
            all_reservations = []
            
            # Use iterator for memory efficiency
            for page in self.reservations_table.iterate(formula=formula, page_size=100):
                all_reservations.extend(page)
                
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
        
    def get_hcp_jobs_optimized(self, start_date=None, end_date=None):
        """Fetch all jobs from HCP with parallel pagination."""
        logger.info("Fetching jobs from HCP with optimized pagination...")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = (datetime.now() + timedelta(days=90)).isoformat()
        
        # First request to get total count
        params = {
            'page': 1,
            'page_size': 100,
            'scheduled_start_min': start_date,
            'scheduled_start_max': end_date,
            'expand[]': ['customer', 'address', 'schedule', 'appointments']
        }
        
        first_result = self.hcp_request('/jobs', params=params)
        if not first_result or 'jobs' not in first_result:
            return []
        
        all_jobs = first_result.get('jobs', [])
        total_items = first_result.get('total_items', len(all_jobs))
        total_pages = (total_items + 99) // 100  # Ceiling division
        
        logger.info(f"Total jobs to fetch: {total_items} across {total_pages} pages")
        
        if total_pages <= 1:
            return all_jobs
        
        # Fetch remaining pages in parallel
        futures = []
        for page in range(2, total_pages + 1):
            page_params = params.copy()
            page_params['page'] = page
            future = self.executor.submit(self.hcp_request, '/jobs', params=page_params)
            futures.append((page, future))
        
        # Collect results
        for page, future in futures:
            try:
                result = future.result(timeout=60)
                if result and 'jobs' in result:
                    jobs = result.get('jobs', [])
                    all_jobs.extend(jobs)
                    logger.info(f"  Fetched page {page}: {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
        
        logger.info(f"Total HCP jobs fetched: {len(all_jobs)}")
        
        # Build job index for O(1) lookups
        self._build_job_index(all_jobs)
        
        return all_jobs
    
    def _build_job_index(self, jobs):
        """Build indexed data structures for efficient job lookups."""
        logger.info("Building job index for fast lookups...")
        
        self._job_index = {
            'by_customer': defaultdict(list),
            'by_address': defaultdict(list),
            'by_customer_address': defaultdict(list),
            'by_datetime': defaultdict(list)
        }
        
        for job in jobs:
            customer_id = job.get('customer', {}).get('id')
            address_id = job.get('address', {}).get('id')
            scheduled_start = job.get('schedule', {}).get('scheduled_start')
            
            if customer_id:
                self._job_index['by_customer'][customer_id].append(job)
            
            if address_id:
                self._job_index['by_address'][address_id].append(job)
            
            if customer_id and address_id:
                key = f"{customer_id}:{address_id}"
                self._job_index['by_customer_address'][key].append(job)
            
            if scheduled_start:
                # Index by date for time-based lookups
                job_date = scheduled_start.split('T')[0]
                self._job_index['by_datetime'][job_date].append(job)
        
        logger.info(f"Indexed {len(jobs)} jobs for fast lookup")
        
    def get_property_hcp_mappings_batch(self):
        """Get mapping of Property IDs to HCP Customer/Address IDs with batch operations."""
        logger.info("Building property to HCP mapping with batch operations...")
        
        # Check cache first
        cache_key = f"{self.environment}_property_mappings"
        if cache_key in self._property_cache:
            logger.info("Using cached property mappings")
            self._cache_stats['property_hits'] += 1
            return self._property_cache[cache_key]
        
        self._cache_stats['property_misses'] += 1
        
        # Fetch all properties
        properties = []
        for page in self.properties_table.iterate(page_size=100):
            properties.extend(page)
        
        # Collect all customer record IDs
        customer_ids_to_fetch = set()
        property_customer_map = {}
        
        for prop in properties:
            prop_id = prop['id']
            fields = prop['fields']
            customer_links = fields.get('HCP Customer ID', [])
            
            if customer_links:
                customer_id = customer_links[0]
                customer_ids_to_fetch.add(customer_id)
                property_customer_map[prop_id] = (prop, customer_id)
        
        logger.info(f"Need to fetch {len(customer_ids_to_fetch)} unique customers")
        
        # Batch fetch customers
        if customer_ids_to_fetch:
            # Airtable allows fetching multiple records by ID
            customer_records = {}
            
            # Process in batches of 100 (Airtable limit)
            customer_id_list = list(customer_ids_to_fetch)
            for i in range(0, len(customer_id_list), 100):
                batch = customer_id_list[i:i+100]
                
                # Build formula for batch fetch
                id_conditions = [f"RECORD_ID()='{cid}'" for cid in batch]
                formula = f"OR({','.join(id_conditions)})"
                
                try:
                    batch_results = self.customers_table.all(formula=formula)
                    for record in batch_results:
                        customer_records[record['id']] = record
                except Exception as e:
                    logger.error(f"Error fetching customer batch: {e}")
        
        # Build mapping
        mapping = {}
        for prop_id, (prop, customer_id) in property_customer_map.items():
            fields = prop['fields']
            
            if customer_id in customer_records:
                customer_record = customer_records[customer_id]
                hcp_customer_id = customer_record['fields'].get('HCP Customer ID')
                
                mapping[prop_id] = {
                    'property_name': fields.get('Property Name'),
                    'hcp_customer_id': hcp_customer_id,
                    'hcp_address_id': fields.get('HCP Address ID')
                }
        
        # Also add properties without customer links
        for prop in properties:
            if prop['id'] not in mapping:
                fields = prop['fields']
                mapping[prop['id']] = {
                    'property_name': fields.get('Property Name'),
                    'hcp_customer_id': None,
                    'hcp_address_id': fields.get('HCP Address ID')
                }
        
        logger.info(f"Mapped {len(mapping)} properties to HCP IDs")
        
        # Cache the result
        self._property_cache[cache_key] = mapping
        
        return mapping
        
    def match_reservation_to_job_fast(self, reservation, property_mapping):
        """Find matching HCP job for a reservation using indexed lookups."""
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
        
        # Use indexed lookup for jobs
        lookup_key = f"{hcp_customer_id}:{hcp_address_id}"
        candidate_jobs = self._job_index['by_customer_address'].get(lookup_key, [])
        
        if not candidate_jobs:
            # Fallback to customer-only lookup
            candidate_jobs = self._job_index['by_customer'].get(hcp_customer_id, [])
            # Filter by address
            candidate_jobs = [j for j in candidate_jobs if j.get('address', {}).get('id') == hcp_address_id]
        
        # Find matching jobs by date only (ignoring time)
        matches = []
        
        for job in candidate_jobs:
            # Check date match only
            job_start = job.get('schedule', {}).get('scheduled_start')
            if not job_start:
                continue
                
            job_datetime = datetime.fromisoformat(job_start.replace('Z', '+00:00'))
            
            # Compare dates only (ignore time)
            if job_datetime.date() == res_datetime.date():
                time_diff = abs((job_datetime - res_datetime).total_seconds())
                matches.append({
                    'job': job,
                    'time_diff': time_diff
                })
                
        if not matches:
            return None
            
        # Return the closest time match (in case there are multiple jobs on same date)
        matches.sort(key=lambda x: x['time_diff'])
        best_match = matches[0]['job']
        
        logger.info(f"  Found match: Job {best_match['id']} for reservation {reservation['id']}")
        logger.info(f"    Property: {prop_info['property_name']}")
        logger.info(f"    Date match: {job_datetime.date()} (time diff: {matches[0]['time_diff']/60:.1f} minutes)")
        
        return best_match
        
    def update_reservations_batch(self, updates):
        """Batch update reservations in Airtable."""
        if not updates:
            return 0
            
        logger.info(f"Batch updating {len(updates)} reservations...")
        
        # Airtable batch update limit is 10 records
        successful_updates = 0
        
        for i in range(0, len(updates), 10):
            batch = updates[i:i+10]
            
            try:
                # Format for batch update
                records = []
                for update in batch:
                    records.append({
                        'id': update['reservation_id'],
                        'fields': update['fields']
                    })
                
                # Batch update
                self.reservations_table.batch_update(records)
                successful_updates += len(batch)
                logger.info(f"  Successfully updated batch of {len(batch)} records")
                
            except Exception as e:
                logger.error(f"Error in batch update: {e}")
                # Fall back to individual updates
                for update in batch:
                    try:
                        self.reservations_table.update(update['reservation_id'], update['fields'])
                        successful_updates += 1
                    except Exception as e2:
                        logger.error(f"Error updating reservation {update['reservation_id']}: {e2}")
        
        return successful_updates
        
    def process_reservation_match(self, reservation, property_mapping):
        """Process a single reservation match (for parallel execution)."""
        matched_job = self.match_reservation_to_job_fast(reservation, property_mapping)
        
        if matched_job:
            job_id = matched_job['id']
            job_status = self._map_work_status(matched_job.get('work_status', 'unknown'))
            expected_time = reservation['fields'].get('Final Service Time')
            
            # Prepare update fields
            update_fields = self._prepare_update_fields(matched_job, job_id, job_status, expected_time)
            
            return {
                'reservation_id': reservation['id'],
                'fields': update_fields,
                'matched': True
            }
        else:
            return {
                'reservation_id': reservation['id'],
                'matched': False
            }
    
    def _prepare_update_fields(self, job_data, job_id, job_status, expected_time):
        """Prepare fields for updating reservation with job data."""
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
        
        # Extract work timestamps
        work_timestamps = job_data.get('work_timestamps', {})
        on_my_way_at = work_timestamps.get('on_my_way_at')
        started_at = work_timestamps.get('started_at') 
        completed_at = work_timestamps.get('completed_at')
        
        # Try to get appointment ID from job data
        if job_data.get('appointments') and len(job_data['appointments']) > 0:
            appointment_id = job_data['appointments'][0]['id']
        
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
        
        # Add optional fields
        if appointment_id:
            update_fields['Service Appointment ID'] = appointment_id
        if scheduled_time:
            update_fields['Scheduled Service Time'] = scheduled_time
        if assignee:
            update_fields['Assignee'] = assignee
        if on_my_way_at:
            update_fields['On My Way Time'] = on_my_way_at
        if started_at:
            update_fields['Job Started Time'] = started_at
        if completed_at:
            update_fields['Job Completed Time'] = completed_at
        
        return update_fields
        
    def reconcile(self, dry_run=True, limit=None, offset=None, reservation_id=None, force=False):
        """Main reconciliation process with parallel processing."""
        start_time = time.time()
        
        logger.info(f"Starting Optimized HCP job reconciliation for {self.environment.upper()} environment...")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        
        # CRITICAL DEBUGGING: Log exactly when reconciliation starts
        import datetime as dt
        logger.info(f"🔍 DEBUGGING: Job reconciliation starting at {dt.datetime.now().strftime('%H:%M:%S.%f')[:12]}") 
        if force:
            logger.info("FORCE MODE: Will process records with Wrong Time status")
        if offset is not None:
            logger.info(f"Offset: {offset}")
        
        if reservation_id:
            logger.info(f"Processing single reservation: {reservation_id}")
        
        # Get data with optimized methods
        reservations = self.get_reservations_without_jobs_batch(limit=limit, offset=offset, reservation_id=reservation_id, force=force)
        if not reservations:
            logger.info("No reservations to reconcile")
            return {'matched': 0, 'unmatched': 0, 'total': 0}
        
        jobs = self.get_hcp_jobs_optimized()
        if not jobs:
            logger.info("No HCP jobs found")
            return {'matched': 0, 'unmatched': 0, 'total': len(reservations)}
        
        property_mapping = self.get_property_hcp_mappings_batch()
        
        # Process reservations in parallel
        logger.info("\nMatching reservations to jobs in parallel...")
        
        futures = []
        for reservation in reservations:
            future = self.executor.submit(self.process_reservation_match, reservation, property_mapping)
            futures.append(future)
        
        # Collect results
        updates_to_process = []
        matched_count = 0
        unmatched_count = 0
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result['matched']:
                    matched_count += 1
                    if not dry_run:
                        updates_to_process.append(result)
                else:
                    unmatched_count += 1
            except Exception as e:
                logger.error(f"Error processing reservation: {e}")
                unmatched_count += 1
        
        # Batch update if not dry run
        if not dry_run and updates_to_process:
            successful_updates = self.update_reservations_batch(updates_to_process)
            logger.info(f"Successfully updated {successful_updates} reservations")
        
        # Summary
        elapsed_time = time.time() - start_time
        
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
        logger.info(f"⏱️ Total execution time: {elapsed_time:.2f} seconds")
        
        # Cache statistics
        logger.info("\nCache Statistics:")
        logger.info(f"  Property cache hits: {self._cache_stats['property_hits']}")
        logger.info(f"  Property cache misses: {self._cache_stats['property_misses']}")
        
        if dry_run:
            logger.info("\n💡 To execute these updates, run with --execute flag")
            
        return {
            'matched': matched_count,
            'unmatched': unmatched_count,
            'total': len(reservations),
            'environment': self.environment,
            'single_reservation': reservation_id if reservation_id else None,
            'execution_time': elapsed_time
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
        reconciler = OptimizedHCPJobReconciler(environment=environment)
        result = reconciler.reconcile(dry_run=not execute, limit=limit)
        
        return {
            'success': True,
            'environment': environment,
            'mode': 'execute' if execute else 'dry_run',
            'results': result,
            'message': f"Successfully {'executed' if execute else 'analyzed'} reconciliation in {result.get('execution_time', 0):.2f} seconds"
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
    parser = argparse.ArgumentParser(description='Optimized HCP job reconciliation with Airtable reservations')
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
        reconciler = OptimizedHCPJobReconciler(environment=args.env)
        reconciler.reconcile(dry_run=dry_run, limit=args.limit, offset=args.offset, 
                           reservation_id=args.reservation_id, force=args.force)


if __name__ == '__main__':
    main()