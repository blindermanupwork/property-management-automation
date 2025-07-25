#!/usr/bin/env python3
"""
Automated Test Framework for Duplicate Detection
===============================================
This framework runs the 6 duplicate detection test cases and reports results to Airtable.
It can be integrated into ICS and CSV processing to ensure duplicate detection is working correctly.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directories to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from pyairtable import Api

# Import will be done dynamically to avoid circular imports

class AutomatedTestFramework:
    """Framework for running duplicate detection tests and reporting to Airtable."""
    
    TEST_SCENARIOS = [
        {
            "id": "scenario_1",
            "name": "New reservation",
            "description": "New UID and dates should be created",
            "method": "test_scenario_1_new_reservation"
        },
        {
            "id": "scenario_2", 
            "name": "Same UID modifications",
            "description": "Same UID with changes should update existing",
            "method": "test_scenario_2_same_uid_modification"
        },
        {
            "id": "scenario_3",
            "name": "UID removed (future)",
            "description": "Missing UID with future checkout marks as removed",
            "method": "test_scenario_3_uid_removed"
        },
        {
            "id": "scenario_4",
            "name": "Different UID same dates",
            "description": "Lodgify case - new UID but same dates ignores duplicate",
            "method": "test_scenario_4_different_uid_same_dates"
        },
        {
            "id": "scenario_5",
            "name": "Same UID different dates",
            "description": "Date change for same UID updates existing",
            "method": "test_scenario_5_different_dates_same_uid"
        },
        {
            "id": "scenario_6",
            "name": "Block vs Reservation",
            "description": "Different entry types are separate",
            "method": "test_scenario_6_block_vs_reservation"
        }
    ]
    
    def __init__(self, environment: str = None):
        """Initialize the test framework."""
        self.environment = environment or Config.environment
        self.config = Config
        self.api = Api(self.config.get_airtable_api_key())
        self.base = self.api.base(self.config.get_airtable_base_id())
        self.automation_table = self.base.table('Automation')
        self.test_results = {}
        self.timestamp = datetime.now()
        
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all test scenarios and return results."""
        logging.info("🧪 Running duplicate detection test suite...")
        
        # Dynamic import to avoid circular dependencies
        sys.path.insert(0, str(project_root))
        from test_ics_duplicate_detection import TestIcsDuplicateDetection
        
        results = {}
        
        for scenario in self.TEST_SCENARIOS:
            try:
                logging.info(f"\n🔍 Running {scenario['name']}...")
                
                # Create a fresh test instance for each test to avoid state sharing
                tester = TestIcsDuplicateDetection()
                
                # Get the test method
                test_method = getattr(tester, scenario['method'])
                
                # Run the test
                passed = test_method()
                results[scenario['id']] = passed
                
                if passed:
                    logging.info(f"✅ {scenario['name']}: PASSED")
                else:
                    logging.error(f"❌ {scenario['name']}: FAILED")
                    
            except Exception as e:
                logging.error(f"❌ {scenario['name']}: ERROR - {str(e)}")
                results[scenario['id']] = False
                
        self.test_results = results
        return results
        
    def format_test_results(self) -> str:
        """Format test results for Airtable display."""
        lines = [f"Test Results - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({self.environment})"]
        lines.append("=" * 50)
        
        all_passed = True
        for scenario in self.TEST_SCENARIOS:
            scenario_id = scenario['id']
            passed = self.test_results.get(scenario_id, False)
            icon = "✅" if passed else "❌"
            status = "PASS" if passed else "FAIL"
            
            lines.append(f"{icon} {scenario['name']}: {status}")
            
            if not passed:
                all_passed = False
                
        lines.append("=" * 50)
        lines.append(f"Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return "\n".join(lines)
        
    def update_airtable_test_results(self):
        """Update test results in Airtable Automation table."""
        try:
            # Find the "Duplicate Detection Tests" record or create it
            records = self.automation_table.all(formula="{Name} = 'Duplicate Detection Tests'")
            
            test_results_text = self.format_test_results()
            
            if records:
                # Update existing record
                record_id = records[0]['id']
                self.automation_table.update(record_id, {
                    'Last Ran Time': self.timestamp.isoformat(),
                    'Sync Details': test_results_text,
                    'Active': all(self.test_results.values())  # Check if all tests passed
                })
                logging.info(f"✅ Updated test results in Airtable record {record_id}")
            else:
                # Create new record
                new_record = self.automation_table.create({
                    'Name': 'Duplicate Detection Tests',
                    'Last Ran Time': self.timestamp.isoformat(),
                    'Sync Details': test_results_text,
                    'Active': all(self.test_results.values())
                })
                logging.info(f"✅ Created new test results record in Airtable: {new_record['id']}")
                
        except Exception as e:
            logging.error(f"❌ Failed to update Airtable test results: {e}")
            
    def create_test_result_fields(self):
        """Create individual test result fields in Automation table (optional)."""
        # This would create separate checkbox fields for each test
        # But using the Sync Details field is simpler and more flexible
        pass
        
    def integrate_with_processor(self, processor_type: str) -> bool:
        """Run tests as part of ICS or CSV processing."""
        logging.info(f"\n{'='*60}")
        logging.info(f"🧪 Running duplicate detection tests for {processor_type} processor")
        logging.info(f"{'='*60}")
        
        # Run tests
        results = self.run_all_tests()
        
        # Update Airtable
        self.update_airtable_test_results()
        
        # Return overall pass/fail
        all_passed = all(results.values())
        
        if all_passed:
            logging.info(f"✅ All duplicate detection tests passed for {processor_type}")
        else:
            logging.warning(f"⚠️ Some duplicate detection tests failed for {processor_type}")
            failed_tests = [name for name, passed in results.items() if not passed]
            logging.warning(f"Failed tests: {', '.join(failed_tests)}")
            
        return all_passed


def run_standalone():
    """Run tests standalone (for testing the framework)."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Determine environment
    import os
    env = os.environ.get('ENVIRONMENT', 'development')
    
    framework = AutomatedTestFramework(env)
    results = framework.run_all_tests()
    framework.update_airtable_test_results()
    
    # Print summary
    print("\n" + framework.format_test_results())
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    run_standalone()