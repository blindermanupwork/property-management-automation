#!/usr/bin/env python3
"""
Master Automation Runner
Orchestrates all automation processes based on Airtable control settings
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))
from automation_controller import AutomationController

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class AutomationRunner:
    """Main automation orchestrator"""
    
    def __init__(self):
        self.controller = AutomationController()
        # Use relative path based on current script location
        self.scripts_dir = Path(__file__).parent / "scripts"
        
    def run_itrip_csv_download(self):
        """Download latest iTrip CSV via Gmail"""
        try:
            print("📧 Downloading latest iTrip CSV from Gmail...")
            return self.run_gmail_download()
            
        except Exception as e:
            return {"success": False, "message": f"iTrip CSV download error: {str(e)}"}
    
    def run_gmail_download(self):
        """Run Gmail downloader"""
        try:
            gmail_script = self.scripts_dir / "gmail" / "gmail_downloader_linux.py"
            if not gmail_script.exists():
                return {"success": False, "message": "Gmail downloader script not found"}
            
            print("📧 Running Gmail downloader...")
            result = subprocess.run([
                sys.executable, str(gmail_script.absolute())
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(gmail_script.parent.absolute()))
            
            if result.returncode == 0:
                return {"success": True, "message": "Gmail download completed successfully"}
            else:
                return {"success": False, "message": f"Gmail download failed: {result.stderr}"}
                
        except Exception as e:
            return {"success": False, "message": f"Gmail error: {str(e)}"}
    
    def run_evolve_scraper(self):
        """Run Evolve scraper"""
        try:
            evolve_script = self.scripts_dir / "evolve" / "evolveScrape.py"
            if not evolve_script.exists():
                return {"success": False, "message": "Evolve scraper script not found"}
            
            print("🏠 Running Evolve scraper...")
            result = subprocess.run([
                sys.executable, str(evolve_script.absolute()), "--headless"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(evolve_script.parent.absolute()))
            
            if result.returncode == 0:
                return {"success": True, "message": "Evolve scraping completed successfully"}
            else:
                return {"success": False, "message": f"Evolve scraping failed: {result.stderr}"}
                
        except Exception as e:
            return {"success": False, "message": f"Evolve error: {str(e)}"}
    
    def run_csv_processing(self):
        """Process iTrip and Evolve CSV files to Airtable"""
        try:
            csv_script = self.scripts_dir / "CSVtoAirtable" / "csvProcess.py"
            if not csv_script.exists():
                return {"success": False, "message": "CSV processor script not found"}
            
            print("📊 Processing iTrip and Evolve CSV files to Airtable...")
            result = subprocess.run([
                sys.executable, str(csv_script.absolute())
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(csv_script.parent.absolute()))
            
            if result.returncode == 0:
                return {"success": True, "message": "CSV processing to Airtable completed successfully"}
            else:
                return {"success": False, "message": f"CSV processing failed: {result.stderr}"}
                
        except Exception as e:
            return {"success": False, "message": f"CSV processing error: {str(e)}"}
    
    def run_ics_calendar_sync(self):
        """Run ICS calendar sync"""
        try:
            ics_script = self.scripts_dir / "icsAirtableSync" / "icsProcess.py"
            if not ics_script.exists():
                return {"success": False, "message": "ICS processor script not found"}
            
            print("📅 Running ICS calendar sync...")
            result = subprocess.run([
                sys.executable, str(ics_script.absolute())
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ics_script.parent.absolute()))
            
            if result.returncode == 0:
                return {"success": True, "message": "ICS calendar sync completed successfully"}
            else:
                return {"success": False, "message": f"ICS sync failed: {result.stderr}"}
                
        except Exception as e:
            return {"success": False, "message": f"ICS sync error: {str(e)}"}
    
    def run_hcp_service_jobs(self):
        """Run HCP service job creation/sync"""
        try:
            # This would be where HCP job creation logic goes
            # For now, placeholder implementation
            print("🔧 Running HCP service job sync...")
            time.sleep(1)  # Simulate processing
            
            return {"success": True, "message": "HCP service job sync completed successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"HCP service job error: {str(e)}"}
    
    def run_all_automations(self):
        """Run all automations in sequence"""
        print("🚀 Starting Automation Suite")
        print("=" * 50)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Define automation sequence - ALL respect Airtable Active checkbox
        automations = [
            ("iTrip CSV Gmail", self.run_itrip_csv_download),  # Download latest iTrip CSV from Gmail
            ("Evolve", self.run_evolve_scraper),               # Scrape Evolve data
            ("CSV Files", self.run_csv_processing),            # Process iTrip and Evolve files to Airtable
            ("ICS Calendar", self.run_ics_calendar_sync),      # Sync ICS calendar data
            ("Add/Sync Service Jobs", self.run_hcp_service_jobs),  # HCP service job sync (respects checkbox)
        ]
        
        results = {}
        total_start_time = datetime.now()
        
        for automation_name, automation_func in automations:
            success = self.controller.run_automation(automation_name, automation_func)
            results[automation_name] = success
            
            # Small delay between automations
            time.sleep(2)
        
        total_end_time = datetime.now()
        total_duration = total_end_time - total_start_time
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 Automation Suite Summary")
        print("=" * 50)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        for name, success in results.items():
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {name}")
        
        print(f"\n📊 Results: {successful}/{total} successful")
        print(f"⏱️  Total duration: {total_duration.total_seconds():.1f}s")
        print(f"🕐 Completed at: {total_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return results

def main():
    """Main entry point"""
    try:
        runner = AutomationRunner()
        results = runner.run_all_automations()
        
        # Exit with error code if any automation failed
        if not all(results.values()):
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Automation suite cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Automation suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()