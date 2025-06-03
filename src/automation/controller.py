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
            response = requests.get(url, headers=self.get_headers(), params=params)
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
        # First, get the record ID
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}"
        params = {
            "filterByFormula": f"{{Name}} = '{automation_name}'"
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                print(f"⚠️  Cannot update - automation '{automation_name}' not found in Airtable")
                return False
            
            record_id = records[0]["id"]
            
            # Prepare update data
            # Use Arizona timezone for Airtable data
            arizona_tz = pytz.timezone('America/Phoenix')
            run_time = start_time.isoformat() if start_time else datetime.now(arizona_tz).isoformat()
            status_icon = "✅" if success else "❌"
            sync_details = f"{status_icon} {details}"
            
            update_data = {
                "fields": {
                    'Last Ran': run_time,
                    'Sync Details': sync_details
                }
            }
            
            # Update the record
            update_url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}/{record_id}"
            response = requests.patch(update_url, headers=self.get_headers(), json=update_data)
            response.raise_for_status()
            
            print(f"📝 Updated status for '{automation_name}': {sync_details}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating automation status for '{automation_name}': {e}")
            return False
    
    def run_automation(self, automation_name, automation_func, *args, **kwargs):
        """Run an automation with status tracking"""
        print(f"\n🔍 Checking status for '{automation_name}'...")
        
        # Check if automation is active
        if not self.get_automation_status(automation_name):
            print(f"⏭️  Skipping '{automation_name}' - not active")
            return False
        
        arizona_tz = pytz.timezone('America/Phoenix')
        start_time = datetime.now(arizona_tz)
        print(f"🚀 Starting '{automation_name}' at {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        try:
            # Run the automation function
            result = automation_func(*args, **kwargs)
            
            end_time = datetime.now(arizona_tz)
            duration = end_time - start_time
            
            # Determine success based on result
            if isinstance(result, bool):
                success = result
                details = f"Completed in {duration.total_seconds():.1f}s"
            elif isinstance(result, dict) and "success" in result:
                success = result["success"]
                details = result.get("message", f"Completed in {duration.total_seconds():.1f}s")
            else:
                success = True
                details = f"Completed in {duration.total_seconds():.1f}s"
            
            if success:
                print(f"✅ '{automation_name}' completed successfully in {duration.total_seconds():.1f}s")
            else:
                print(f"❌ '{automation_name}' failed: {details}")
            
            # Update status in Airtable
            self.update_automation_status(automation_name, success, details, start_time)
            
            return success
            
        except Exception as e:
            end_time = datetime.now(arizona_tz)
            duration = end_time - start_time
            error_details = f"Error after {duration.total_seconds():.1f}s: {str(e)}"
            
            print(f"❌ '{automation_name}' failed with error: {e}")
            print(f"📝 Traceback: {traceback.format_exc()}")
            
            # Update status in Airtable
            self.update_automation_status(automation_name, False, error_details, start_time)
            
            return False
    
    def get_all_automations_status(self):
        """Get status of all automations"""
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.automation_table}"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            automations = {}
            for record in records:
                fields = record.get("fields", {})
                name = fields.get('Name', "")
                is_active = fields.get('Active', False)
                last_ran = fields.get('Last Ran', "Never")
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
            response = requests.get(url, headers=self.get_headers())
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
                last_ran = fields.get('Last Ran', "Never")
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
        from .scripts.run_automation import run_gmail_automation, run_evolve_automation, run_csv_automation, run_ics_automation, run_hcp_automation
        
        # Define automation mappings
        automations = [
            ("iTrip CSV Gmail", run_gmail_automation),
            ("Evolve", run_evolve_automation),
            ("CSV Files", run_csv_automation),
            ("ICS Calendar", run_ics_automation),
            ("Add/Sync Service Jobs", run_hcp_automation),
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
    
    def run_specific(self, automation_id):
        """Run a specific automation by ID
        
        Args:
            automation_id: The name/ID of the automation to run
        """
        # Import automation functions
        from .scripts.run_automation import run_gmail_automation, run_evolve_automation, run_csv_automation, run_ics_automation, run_hcp_automation
        
        # Map automation IDs to functions
        automation_map = {
            "iTrip CSV Gmail": run_gmail_automation,
            "Evolve": run_evolve_automation,
            "CSV Files": run_csv_automation,
            "ICS Calendar": run_ics_automation,
            "Add/Sync Service Jobs": run_hcp_automation,
        }
        
        if automation_id not in automation_map:
            print(f"❌ Unknown automation: {automation_id}")
            print("Available automations:")
            for name in automation_map:
                print(f"  - {name}")
            return False
        
        func = automation_map[automation_id]
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
        test_automations = ["iTrip CSV", "Gmail", "Evolve", "CSV Files", "ICS Calendar", "Add/Sync Service Jobs"]
        
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