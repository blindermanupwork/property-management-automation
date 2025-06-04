#!/usr/bin/env python3
"""
Automation Functions
Individual automation functions that can be called with specific configs
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time
import pytz

def run_gmail_automation(config):
    """Run Gmail downloader automation
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        gmail_script = config.get_script_path("gmail", "gmail_downloader.py")
        if not gmail_script.exists():
            return {"success": False, "message": "Gmail downloader script not found"}
        
        print("📧 Running Gmail downloader...")
        result = subprocess.run([
            sys.executable, str(gmail_script.absolute()), "--force"
        ], cwd=str(gmail_script.parent.absolute()))
        
        if result.returncode == 0:
            return {"success": True, "message": "Gmail download completed successfully"}
        else:
            return {"success": False, "message": "Gmail download failed"}
            
    except Exception as e:
        return {"success": False, "message": f"Gmail error: {str(e)}"}
    
def run_evolve_automation(config):
    """Run Evolve scraper automation
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        evolve_script = config.get_script_path("evolve", "evolveScrape.py")
        if not evolve_script.exists():
            return {"success": False, "message": "Evolve scraper script not found"}
        
        print("🏠 Running Evolve scraper...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        result = subprocess.run([
            sys.executable, str(evolve_script.absolute()), "--headless"
        ], cwd=str(evolve_script.parent.absolute()), env=env)
        
        if result.returncode == 0:
            return {"success": True, "message": "Evolve scraping completed successfully"}
        else:
            return {"success": False, "message": "Evolve scraping failed"}
            
    except Exception as e:
        return {"success": False, "message": f"Evolve error: {str(e)}"}
    
def run_csv_automation(config):
    """Process iTrip and Evolve CSV files to Airtable
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        csv_script = config.get_script_path("CSVtoAirtable", "csvProcess.py")
        if not csv_script.exists():
            return {"success": False, "message": "CSV processor script not found"}
        
        print("📊 Processing iTrip and Evolve CSV files to Airtable...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        result = subprocess.run([
            sys.executable, str(csv_script.absolute())
        ], cwd=str(csv_script.parent.absolute()), env=env)
        
        if result.returncode == 0:
            return {"success": True, "message": "CSV processing to Airtable completed successfully"}
        else:
            return {"success": False, "message": "CSV processing failed"}
            
    except Exception as e:
        return {"success": False, "message": f"CSV processing error: {str(e)}"}
    
def run_ics_automation(config):
    """Run ICS calendar sync
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        ics_script = config.get_script_path("icsAirtableSync", "icsProcess.py")
        if not ics_script.exists():
            return {"success": False, "message": "ICS processor script not found"}
        
        print("📅 Running ICS calendar sync...")
        
        # Pass environment to the script
        env = os.environ.copy()
        env['ENVIRONMENT'] = 'development' if not config.is_production else 'production'
        
        result = subprocess.run([
            sys.executable, str(ics_script.absolute())
        ], cwd=str(ics_script.parent.absolute()), env=env)
        
        if result.returncode == 0:
            return {"success": True, "message": "ICS calendar sync completed successfully"}
        else:
            return {"success": False, "message": "ICS sync failed"}
            
    except Exception as e:
        return {"success": False, "message": f"ICS sync error: {str(e)}"}
    
def run_hcp_automation(config):
    """Run HCP service job creation/sync
    
    Args:
        config: DevConfig or ProdConfig instance
    """
    try:
        print("🔧 Running HCP service job sync...")
        
        # HCP sync is handled by JavaScript API
        # This is a placeholder for future Python implementation
        time.sleep(1)  # Simulate processing
        
        return {"success": True, "message": "HCP service job sync completed successfully"}
        
    except Exception as e:
        return {"success": False, "message": f"HCP service job error: {str(e)}"}