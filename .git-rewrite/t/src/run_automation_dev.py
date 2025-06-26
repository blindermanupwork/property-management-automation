#!/usr/bin/env python3
"""
Development Automation Runner
This script runs the automation suite in development environment
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from automation.config_dev import DevConfig
from automation.controller import AutomationController

def setup_logging(config):
    """Set up logging configuration"""
    log_file = config.get_log_path('automation_dev.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main entry point for development automation"""
    parser = argparse.ArgumentParser(description='Run development automation suite')
    parser.add_argument('--list', action='store_true', help='List all available automations')
    parser.add_argument('--run', type=str, help='Run a specific automation by ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be run without executing')
    parser.add_argument('--force', action='store_true', help='Force run even if environment seems wrong')
    
    args = parser.parse_args()
    
    # Safety check: warn if running in production-like environment
    if not args.force:
        hostname = os.environ.get('HOSTNAME', '').lower()
        if 'prod' in hostname or 'production' in hostname:
            print("⚠️  WARNING: You appear to be on a production system!")
            print("   Use --force if you really want to run DEVELOPMENT automation here.")
            print("   Consider using run_automation_prod.py instead.")
            sys.exit(1)
    
    # Initialize development configuration
    config = DevConfig()
    
    # Validate configuration
    errors = config.validate_config()
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    
    # Ensure directories exist
    config.ensure_directories()
    
    # Set up logging
    logger = setup_logging(config)
    
    # Log startup
    logger.info("=" * 50)
    logger.info("🚀 Starting DEVELOPMENT Automation Suite")
    logger.info(f"🏠 Project Root: {config.root_dir}")
    logger.info(f"📁 CSV Process Dir: {config.csv_process_dir}")
    logger.info(f"🗂️  Airtable Base: {config.get_airtable_base_id()}")
    logger.info("=" * 50)
    
    # Initialize controller with config
    controller = AutomationController(config)
    
    # Handle command line options
    if args.list:
        controller.list_automations()
    elif args.run:
        controller.run_specific(args.run)
    else:
        # Run all active automations
        controller.run_all(dry_run=args.dry_run)
    
    logger.info("✅ Development automation suite completed")

if __name__ == "__main__":
    main()