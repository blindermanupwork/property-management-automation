#!/usr/bin/env python3
"""
Automation Controller
Manages automation status checking and logging via Airtable
"""

import requests
import json
from datetime import datetime, timezone
import sys
import os
from pathlib import Path
import time
import traceback
import pytz

class AutomationController:
    """Controls automation execution based on Airtable settings"""
    
    def __init__(self, config):
        """Initialize controller with a config instance
        
        Args:
            config: Instance of DevConfig or ProdConfig
        """
        self.config = config
        self.airtable_api_key = config.get_airtable_api_key()
        self.base_id = config.get_airtable_base_id()
        self.automation_table = config.get_airtable_table_name('automation_control')
        
        if not self.airtable_api_key:
            raise ValueError(f"{config.environment_name} Airtable API key not set")
    
    def send_failure_alert(self, failed_names, successful, total, duration_seconds):
        """Send push notification + email via ntfy.sh when automations fail"""
        import logging
        logger = logging.getLogger(__name__)
        try:
            env = self.config.environment_name
            alert_email = os.environ.get('ALERT_EMAIL', '')
            topic = "airscripts-api-monitor-liveitup278"

            failed_list = "\n".join(f"  - {name}" for name in failed_names)
            body = (
                f"Failed automations:\n{failed_list}\n\n"
                f"Results: {successful}/{total} successful\n"
                f"Duration: {duration_seconds:.0f}s\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            url = f"https://ntfy.sh/{topic}"
            headers = {
                "Title": f"Automation Alert: {len(failed_names)} of {total} failed ({env})",
                "Priority": "high",
                "Tags": "warning",
            }
            if alert_email:
                headers["Email"] = alert_email

            resp = requests.post(url, data=body.encode('utf-8'), headers=headers, timeout=10)
            if resp.status_code == 200:
                logger.info(f"Alert sent via ntfy.sh (email: {alert_email or 'none'})")
            else:
                logger.warning(f"ntfy.sh returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Failed to send failure alert: {e}")

    def get_headers(self):
        """Get Airtable API headers"""
        return {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }
    
    def get_automation_status(self, automation_name):
        """Check if a specific automation is active in Airtable"""
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}"
        params = {
            "filterByFormula": f"{{Name}} = '{automation_name}'"
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                print(f"⚠️  Automation '{automation_name}' not found in Airtable")
                return False
                
            record = records[0]
            fields = record.get("fields", {})
            is_active = fields.get('Active', False)
            
            print(f"📋 {automation_name}: {'✅ Active' if is_active else '❌ Inactive'}")
            return is_active
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking automation status for '{automation_name}': {e}")
            return False
    
    def update_automation_status(self, automation_name, success=True, details="", start_time=None):
        """Update automation run status in Airtable"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"📝 Updating automation status for '{automation_name}': success={success}, details='{details}'")
        
        # First, get the record ID
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}"
        params = {
            "filterByFormula": f"{{Name}} = '{automation_name}'"
        }
        
        try:
            logger.debug(f"Fetching record ID for '{automation_name}'")
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                logger.warning(f"⚠️  Cannot update - automation '{automation_name}' not found in Airtable")
                print(f"⚠️  Cannot update - automation '{automation_name}' not found in Airtable")
                return False
            
            record_id = records[0]["id"]
            logger.debug(f"Found record ID: {record_id}")
            
            # Prepare update data
            # Use Arizona timezone for Airtable data
            arizona_tz = pytz.timezone('America/Phoenix')
            run_time = start_time.isoformat() if start_time else datetime.now(arizona_tz).isoformat()
            
            # Fix double status icon issue by stripping existing icons first
            if details:
                # Remove any existing status icons and extra spaces
                clean_details = details.lstrip("❌✅ ")
                logger.debug(f"Cleaned details from '{details}' to '{clean_details}'")
                status_icon = "✅" if success else "❌"
                sync_details = f"{status_icon} {clean_details}"
            else:
                sync_details = "✅" if success else "❌"
            logger.debug(f"Final sync_details: '{sync_details}'")
            
            update_data = {
                "fields": {
                    'Last Ran Time': run_time,
                    'Sync Details': sync_details
                }
            }
            
            # Log trigger source
            import inspect
            import traceback
            caller_info = inspect.stack()
            
            # Special logging for X:06-X:09 triggers
            current_minute = datetime.now().minute
            if 6 <= current_minute <= 9:
                logger.warning(f"\n=== SUSPICIOUS TIMING DETECTED ===")
                logger.warning(f"Automation: {automation_name}")
                logger.warning(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.warning(f"Success: {success}, Details: {details}")
                logger.warning(f"Call stack:")
                for i, frame in enumerate(caller_info[:10]):
                    logger.warning(f"  {i}: {frame.filename}:{frame.lineno} in {frame.function}")
                logger.warning(f"Full traceback:")
                logger.warning(''.join(traceback.format_stack()))
                logger.warning(f"===================================")
            
            # Update the record
            update_url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}/{record_id}"
            logger.debug(f"Updating Airtable record at: {update_url}")
            logger.debug(f"Update data: {update_data}")
            
            response = requests.patch(update_url, headers=self.get_headers(), json=update_data, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Successfully updated status for '{automation_name}': {sync_details}")
            print(f"📝 Updated status for '{automation_name}': {sync_details}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error updating automation status: {e}")
            logger.error(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"Response text: {getattr(e.response, 'text', 'N/A')}")
            print(f"❌ Error updating automation status for '{automation_name}': {e}")
            return False
    
    def run_automation(self, automation_name, automation_func, *args, **kwargs):
        """Run an automation with status tracking"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 Starting automation: '{automation_name}'")
        print(f"\n🔍 Checking status for '{automation_name}'...")
        
        # Check if automation is active
        if not self.get_automation_status(automation_name):
            logger.info(f"Skipping '{automation_name}' - marked as inactive")
            print(f"⏭️  Skipping '{automation_name}' - not active")
            return False
        
        arizona_tz = pytz.timezone('America/Phoenix')
        start_time = datetime.now(arizona_tz)
        logger.info(f"▶️  Executing '{automation_name}' at {start_time}")
        print(f"🚀 Starting '{automation_name}' at {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        try:
            # Run the automation function
            result = automation_func(*args, **kwargs)
            
            logger.debug(f"Automation '{automation_name}' returned: {result}")
            
            end_time = datetime.now(arizona_tz)
            duration = end_time - start_time
            
            # Determine success based on result
            skip_sync_update = False
            if isinstance(result, bool):
                success = result
                details = f"Completed in {duration.total_seconds():.1f}s"
            elif isinstance(result, dict) and "success" in result:
                success = result["success"]
                details = result.get("message", f"Completed in {duration.total_seconds():.1f}s")
                skip_sync_update = result.get("skip_sync_update", False)
                logger.info(f"Automation '{automation_name}' result: success={success}, details='{details}', skip_sync_update={skip_sync_update}")
            else:
                success = True
                details = f"Completed in {duration.total_seconds():.1f}s"
                logger.info(f"Automation '{automation_name}' completed with default success")

            if success:
                print(f"✅ '{automation_name}' completed successfully in {duration.total_seconds():.1f}s")
            else:
                print(f"❌ '{automation_name}' failed: {details}")

            # Update status in Airtable (skip if flagged)
            if skip_sync_update:
                logger.info(f"Skipping Airtable sync update for '{automation_name}' - no files processed")
                print(f"⏭️  Skipping sync update for '{automation_name}' - no files to process")
                return success

            logger.info(f"Updating Airtable status for '{automation_name}'")
            update_result = self.update_automation_status(automation_name, success, details, start_time)
            if not update_result:
                logger.error(f"Failed to update Airtable status for '{automation_name}'")
            
            return success
            
        except Exception as e:
            end_time = datetime.now(arizona_tz)
            duration = end_time - start_time
            error_details = f"Error after {duration.total_seconds():.1f}s: {str(e)}"
            
            logger.error(f"❌ Automation '{automation_name}' failed with exception: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            print(f"❌ '{automation_name}' failed with error: {e}")
            print(f"📝 Traceback: {traceback.format_exc()}")
            
            # Update status in Airtable
            logger.info(f"Updating Airtable status for failed automation '{automation_name}'")
            update_result = self.update_automation_status(automation_name, False, error_details, start_time)
            if not update_result:
                logger.error(f"Failed to update Airtable status for failed automation '{automation_name}'")
            
            return False
    
    def get_all_automations_status(self):
        """Get status of all automations"""
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}"
        
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            automations = {}
            for record in records:
                fields = record.get("fields", {})
                name = fields.get('Name', "")
                is_active = fields.get('Active', False)
                last_ran = fields.get('Last Ran Time', "Never")
                sync_details = fields.get('Sync Details', "No details")
                
                automations[name] = {
                    "active": is_active,
                    "last_ran": last_ran,
                    "sync_details": sync_details
                }
            
            return automations
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching automation status: {e}")
            return {}
    
    def list_automations(self):
        """List all automations with their current status"""
        print("📋 Available Automations:")
        print("=" * 30)
        
        try:
            url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                print("No automations found in Airtable")
                return
            
            for record in records:
                fields = record.get("fields", {})
                name = fields.get('Name', "Unknown")
                is_active = fields.get('Active', False)
                last_ran = fields.get('Last Ran Time', "Never")
                sync_details = fields.get('Sync Details', "No details")
                
                status_icon = "✅" if is_active else "❌"
                print(f"{status_icon} {name}")
                print(f"   Last Run: {last_ran}")
                print(f"   Status: {'Active' if is_active else 'Inactive'}")
                if sync_details != "No details":
                    print(f"   Details: {sync_details}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing automations: {e}")
    
    def run_all(self, dry_run=False):
        """Run all active automations
        
        Args:
            dry_run: If True, show what would be run without executing
        """
        print("🚀 Starting Automation Suite")
        print("=" * 50)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📍 Environment: {self.config.environment_name}")
        print()
        
        if dry_run:
            print("🔍 DRY RUN MODE - No automations will be executed")
            print()
        
        # Import automation functions based on environment
        # These will be imported dynamically based on the config
        from .scripts.run_automation import run_gmail_automation, run_evolve_automation, run_csv_automation, run_ics_automation, run_hcp_automation, run_add_jobs_automation, run_sync_jobs_automation, run_job_reconciliation, run_service_line_updates, run_itrip_monitor_automation
        
        # Define automation mappings
        automations = [
            ("iTrip CSV Gmail", run_gmail_automation),
            ("iTrip Processing Monitor", run_itrip_monitor_automation),
            ("Evolve", run_evolve_automation),
            ("iTrip CSV File", run_csv_automation),
            ("ICS Calendar", run_ics_automation),
            ("Add Service Jobs", run_add_jobs_automation),
            ("Sync Service Jobs", run_sync_jobs_automation),
            ("Update Service Lines", run_service_line_updates),
        ]
        
        results = []
        start_time = datetime.now()
        
        for name, func in automations:
            if dry_run:
                is_active = self.get_automation_status(name)
                if is_active:
                    print(f"✅ Would run: {name}")
                else:
                    print(f"❌ Would skip: {name} (inactive)")
            else:
                # Pass config to the automation function
                success = self.run_automation(name, func, self.config)
                results.append((name, success))
        
        # Run job reconciliation after all main automations complete
        if not dry_run:
            reconciliation_name = "Job Reconciliation"
            if self.get_automation_status(reconciliation_name):
                print(f"\n🔄 Running post-automation job reconciliation...")
                # Always run in execute mode when triggered by automation
                success = self.run_automation(reconciliation_name, run_job_reconciliation, self.config, execute=True)
                results.append((reconciliation_name, success))
            else:
                print(f"\n⏭️  Skipping job reconciliation - not active")
        else:
            # In dry-run mode, check if reconciliation would run
            reconciliation_name = "Job Reconciliation"
            is_active = self.get_automation_status(reconciliation_name)
            if is_active:
                print(f"✅ Would run: {reconciliation_name} (after main automations)")
            else:
                print(f"❌ Would skip: {reconciliation_name} (inactive)")
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print()
        print("=" * 50)
        print("🎯 Automation Suite Summary")
        print("=" * 50)
        
        if not dry_run:
            successful = sum(1 for _, success in results if success)
            total = len(results)
            
            for name, success in results:
                icon = "✅" if success else "❌"
                print(f"{icon} {name}")
            
            print()
            print(f"📊 Results: {successful}/{total} successful")
        
        print(f"⏱️  Total duration: {duration.total_seconds():.1f}s")
        print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Send alert if any automations failed
        if not dry_run:
            failed_names = [name for name, success in results if not success]
            if failed_names:
                self.send_failure_alert(failed_names, successful, total, duration.total_seconds())

    def run_specific(self, automation_id, execute=False):
        """Run a specific automation by ID
        
        Args:
            automation_id: The name/ID of the automation to run
            execute: For reconciliation, whether to execute or dry-run
        """
        # Import automation functions
        from .scripts.run_automation import run_gmail_automation, run_evolve_automation, run_csv_automation, run_ics_automation, run_hcp_automation, run_add_jobs_automation, run_sync_jobs_automation, run_job_reconciliation, run_service_line_updates
        
        # Map automation IDs to functions
        automation_map = {
            "iTrip CSV Gmail": run_gmail_automation,
            "Evolve": run_evolve_automation,
            "iTrip CSV File": run_csv_automation,
            "ICS Calendar": run_ics_automation,
            "Add/Sync Service Jobs": run_hcp_automation,  # Legacy support
            "Add Service Jobs": run_add_jobs_automation,
            "Sync Service Jobs": run_sync_jobs_automation,
            "Job Reconciliation": run_job_reconciliation,
            "Update Service Lines": run_service_line_updates,
        }
        
        if automation_id not in automation_map:
            print(f"❌ Unknown automation: {automation_id}")
            print("Available automations:")
            for name in automation_map:
                print(f"  - {name}")
            return False
        
        func = automation_map[automation_id]
        
        # Handle special case for reconciliation
        if automation_id == "Job Reconciliation":
            return self.run_automation(automation_id, func, self.config, execute=execute)
        else:
            return self.run_automation(automation_id, func, self.config)

def test_automation_controller():
    """Test the automation controller"""
    print("🧪 Testing Automation Controller")
    print("=" * 40)
    
    try:
        # Import config for testing
        from .config_dev import DevConfig
        config = DevConfig()
        controller = AutomationController(config)
        
        # Test getting all automations status
        print("📋 All Automations Status:")
        automations = controller.get_all_automations_status()
        
        for name, status in automations.items():
            active_icon = "✅" if status["active"] else "❌"
            print(f"  {active_icon} {name}")
            print(f"     Last ran: {status['last_ran']}")
            print(f"     Details: {status['sync_details']}")
            print()
        
        # Test individual automation check
        print("🔍 Testing individual automation checks:")
        test_automations = ["iTrip CSV", "Gmail", "Evolve", "iTrip CSV File", "ICS Calendar", "Add/Sync Service Jobs"]
        
        for automation in test_automations:
            is_active = controller.get_automation_status(automation)
            print(f"  {automation}: {'Active' if is_active else 'Inactive'}")
        
        print("\n✅ Automation Controller test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Automation Controller test failed: {e}")
        return False

if __name__ == "__main__":
    test_automation_controller()