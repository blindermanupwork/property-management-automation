#!/usr/bin/env python3
"""
Job Reconciliation Module for HCP Webhook
Matches unlinked HCP jobs to Airtable reservations based on property, date/time, and customer.
To be integrated into the webhook handler.
"""

import logging
from datetime import datetime, timedelta
from pyairtable import Table

logger = logging.getLogger(__name__)

class JobReconciler:
    """Handles matching of HCP jobs to Airtable reservations"""
    
    def __init__(self, reservations_table, properties_table, customers_table):
        self.reservations_table = reservations_table
        self.properties_table = properties_table
        self.customers_table = customers_table
        self._property_cache = {}  # Cache property mappings
        
    def _get_property_hcp_mapping(self, property_id):
        """Get HCP customer/address IDs for a property (with caching)"""
        if property_id in self._property_cache:
            return self._property_cache[property_id]
            
        try:
            prop = self.properties_table.get(property_id)
            fields = prop['fields']
            
            # Get HCP customer ID from linked customer record
            customer_links = fields.get('HCP Customer ID', [])
            hcp_customer_id = None
            
            if customer_links:
                try:
                    customer_record = self.customers_table.get(customer_links[0])
                    hcp_customer_id = customer_record['fields'].get('HCP Customer ID')
                except Exception as e:
                    logger.error(f"Error fetching customer for property {property_id}: {e}")
            
            mapping = {
                'property_name': fields.get('Property Name'),
                'hcp_customer_id': hcp_customer_id,
                'hcp_address_id': fields.get('HCP Address ID')
            }
            
            self._property_cache[property_id] = mapping
            return mapping
            
        except Exception as e:
            logger.error(f"Error getting property mapping for {property_id}: {e}")
            return None
    
    def find_matching_reservation(self, job_data):
        """
        Find a reservation that matches the HCP job based on:
        1. Property (customer/address match)
        2. Scheduled time (within 1 hour window)
        3. No existing Service Job ID
        """
        try:
            # Extract job details
            customer_id = job_data.get('customer', {}).get('id') or job_data.get('customer_id')
            address_id = job_data.get('address', {}).get('id') or job_data.get('address_id')
            
            if not customer_id or not address_id:
                logger.debug(f"Job missing customer/address IDs: customer={customer_id}, address={address_id}")
                return None
            
            # Get scheduled time
            schedule = job_data.get('schedule', {})
            scheduled_start = schedule.get('scheduled_start')
            if not scheduled_start:
                logger.debug("Job has no scheduled start time")
                return None
                
            # Parse job datetime
            try:
                job_datetime = datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
            except:
                logger.error(f"Invalid scheduled_start format: {scheduled_start}")
                return None
            
            # Define search window (1 hour before to 1 hour after)
            search_start = (job_datetime - timedelta(hours=1)).isoformat()
            search_end = (job_datetime + timedelta(hours=1)).isoformat()
            
            # Build Airtable formula to find potential matches
            # Look for reservations without job IDs in the time window
            formula = f"""AND(
                NOT({{Service Job ID}}),
                NOT({{Status}} = 'Old'),
                {{Final Service Time}},
                DATETIME_PARSE({{Final Service Time}}) >= DATETIME_PARSE('{search_start}'),
                DATETIME_PARSE({{Final Service Time}}) <= DATETIME_PARSE('{search_end}')
            )"""
            
            # Fetch potential matches
            potential_matches = self.reservations_table.all(formula=formula)
            logger.info(f"Found {len(potential_matches)} potential matches in time window")
            
            # Check each potential match for property alignment
            best_match = None
            best_time_diff = float('inf')
            
            for reservation in potential_matches:
                res_fields = reservation['fields']
                
                # Get property info
                prop_links = res_fields.get('Property ID', [])
                if not prop_links:
                    continue
                    
                prop_mapping = self._get_property_hcp_mapping(prop_links[0])
                if not prop_mapping:
                    continue
                
                # Check if HCP IDs match
                if (prop_mapping['hcp_customer_id'] == customer_id and 
                    prop_mapping['hcp_address_id'] == address_id):
                    
                    # Calculate time difference
                    res_time = res_fields.get('Final Service Time')
                    if res_time:
                        try:
                            res_datetime = datetime.fromisoformat(res_time.replace('Z', '+00:00'))
                            time_diff = abs((job_datetime - res_datetime).total_seconds())
                            
                            if time_diff < best_time_diff:
                                best_match = reservation
                                best_time_diff = time_diff
                                
                        except Exception as e:
                            logger.error(f"Error parsing reservation time: {e}")
            
            if best_match:
                logger.info(f"✅ Found matching reservation: {best_match['id']} "
                          f"(UID: {best_match['fields'].get('Reservation UID', 'unknown')}) "
                          f"with time diff: {best_time_diff/60:.1f} minutes")
                logger.info(f"  Property: {prop_mapping['property_name']}")
                return best_match
            else:
                logger.debug("No matching reservation found")
                return None
                
        except Exception as e:
            logger.error(f"Error in find_matching_reservation: {e}", exc_info=True)
            return None
    
    def reconcile_job(self, job_data, update_sync_info_func):
        """
        Attempt to reconcile an unmatched HCP job with a reservation.
        Returns True if reconciliation was successful.
        """
        try:
            job_id = job_data.get('id')
            if not job_id:
                return False
                
            logger.info(f"🔄 Attempting to reconcile job {job_id}")
            
            # Find matching reservation
            matching_reservation = self.find_matching_reservation(job_data)
            if not matching_reservation:
                logger.info(f"❌ No matching reservation found for job {job_id}")
                return False
            
            # Update the reservation with the job ID
            record_id = matching_reservation['id']
            work_status = job_data.get('work_status', 'unknown')
            
            update_data = {
                'Service Job ID': job_id,
                'Job Status': self._map_work_status(work_status),
                'Sync Status': 'Matched'
            }
            
            # Include assignee info if available
            employees = job_data.get('assigned_employees', [])
            if employees:
                assignee = self._format_employee_names(employees)
                update_data['Assignee'] = assignee
            
            # Update the record
            self.reservations_table.update(record_id, update_data)
            
            # Update sync info
            update_sync_info_func(
                record_id, 
                f"✅ Automatically matched to existing HCP job {job_id} via webhook reconciliation"
            )
            
            logger.info(f"✅ Successfully reconciled job {job_id} to reservation {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in reconcile_job: {e}", exc_info=True)
            return False
    
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
    
    def _format_employee_names(self, employees):
        """Format employee names from job data"""
        if not employees:
            return ""
        names = []
        for emp in employees:
            if isinstance(emp, dict):
                first = emp.get('first_name', '')
                last = emp.get('last_name', '')
                if first or last:
                    names.append(f"{first} {last}".strip())
        return ", ".join(names) if names else ""


# Integration function to add to webhook handler
def integrate_reconciliation(webhook_handler_module):
    """
    Add reconciliation capability to the webhook handler.
    This function should be called during webhook initialization.
    """
    # Create reconciler instance
    reconciler = JobReconciler(
        webhook_handler_module.reservations_table,
        webhook_handler_module.properties_table,
        webhook_handler_module.customers_table
    )
    
    # Store original process_webhook_async function
    original_process_webhook_async = webhook_handler_module.process_webhook_async
    
    # Create enhanced version with reconciliation
    def enhanced_process_webhook_async(webhook_data):
        """Enhanced webhook processing with job reconciliation"""
        try:
            event_type = webhook_data.get("event", "unknown")
            
            # For job events, check if we need reconciliation
            if not event_type.startswith("job.appointment."):
                job_data = webhook_data.get("job", {})
                if job_data:
                    job_id = job_data.get("id")
                    if job_id:
                        # Check if we have a matching reservation
                        existing_record = webhook_handler_module.find_reservation_by_job_id(job_id)
                        
                        # If no match found, attempt reconciliation
                        if not existing_record:
                            logger.info(f"🔍 No reservation linked to job {job_id}, attempting reconciliation...")
                            
                            # Only reconcile in dev environment for now
                            environment = webhook_handler_module.environment
                            if environment == 'development':
                                reconciled = reconciler.reconcile_job(
                                    job_data, 
                                    webhook_handler_module.update_sync_info
                                )
                                
                                if reconciled:
                                    # Re-fetch the record now that it's linked
                                    existing_record = webhook_handler_module.find_reservation_by_job_id(job_id)
                                    if existing_record:
                                        # Update webhook_data to continue normal processing
                                        webhook_data['_reconciled'] = True
                            else:
                                logger.info(f"ℹ️ Reconciliation is currently only enabled in dev environment")
        
        except Exception as e:
            logger.error(f"Error in reconciliation enhancement: {e}", exc_info=True)
        
        # Continue with original processing
        return original_process_webhook_async(webhook_data)
    
    # Replace the function
    webhook_handler_module.process_webhook_async = enhanced_process_webhook_async
    
    logger.info("✅ Job reconciliation integrated into webhook handler")
    return reconciler