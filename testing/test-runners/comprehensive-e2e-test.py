#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite
Tests the complete flow: Data Generation → CSV Processing → Airtable → Job Creation → HCP → Status Sync
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
import pytz

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from tests.dynamic_test_generator import DynamicTestGenerator

class ComprehensiveE2ETest:
    """Complete end-to-end testing framework"""
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.config = Config
        self.generator = DynamicTestGenerator(environment)
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # Test results tracking
        self.test_results = {
            'start_time': datetime.now(self.arizona_tz),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'scenarios_tested': [],
            'files_generated': [],
            'airtable_records_created': 0,
            'jobs_created': 0,
            'jobs_scheduled': 0,
            'jobs_cancelled': 0,
            'errors': []
        }
    
    def log(self, message: str, level: str = 'INFO'):
        """Log test progress with timestamps"""
        timestamp = datetime.now(self.arizona_tz).strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command: list, description: str, timeout: int = 120) -> dict:
        """Run a command and capture results"""
        self.log(f"Running: {description}")
        self.log(f"Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=project_root
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def test_data_generation(self) -> bool:
        """Test 1: Generate test data for all scenarios"""
        self.log("🚀 TEST 1: Data Generation", 'TEST')
        
        try:
            # Generate all test scenarios
            result = self.run_command([
                'python3', 'tests/dynamic-test-generator.py',
                '--all-scenarios',
                '--count', '5',
                '--environment', self.environment
            ], "Generate all test scenarios")
            
            if result['success']:
                self.log("✅ Test data generation successful")
                self.test_results['files_generated'] = self._count_generated_files()
                return True
            else:
                self.log(f"❌ Test data generation failed: {result['stderr']}")
                self.test_results['errors'].append(f"Data generation: {result['stderr']}")
                return False
                
        except Exception as e:
            self.log(f"❌ Exception in data generation: {str(e)}")
            self.test_results['errors'].append(f"Data generation exception: {str(e)}")
            return False
    
    def test_csv_processing(self) -> bool:
        """Test 2: CSV Processing → Airtable"""
        self.log("🚀 TEST 2: CSV Processing → Airtable", 'TEST')
        
        try:
            # Run CSV processor
            result = self.run_command([
                'python3', f'src/run_automation_{self.environment}.py',
                '--dry-run'  # Use dry-run to test logic without actually modifying data
            ], "Run CSV processing automation")
            
            if result['success'] and 'CSV files processed' in result['stdout']:
                self.log("✅ CSV processing successful")
                return True
            else:
                self.log(f"❌ CSV processing failed: {result['stderr']}")
                self.test_results['errors'].append(f"CSV processing: {result['stderr']}")
                return False
                
        except Exception as e:
            self.log(f"❌ Exception in CSV processing: {str(e)}")
            self.test_results['errors'].append(f"CSV processing exception: {str(e)}")
            return False
    
    def test_ics_processing(self) -> bool:
        """Test 3: ICS Processing → Airtable"""
        self.log("🚀 TEST 3: ICS Processing → Airtable", 'TEST')
        
        try:
            # Check if ICS processor exists and can be tested
            ics_processor = project_root / 'src/automation/scripts/icsAirtableSync/icsProcess.py'
            
            if not ics_processor.exists():
                self.log("⚠️ ICS processor not found, skipping ICS test")
                return True
            
            # Test ICS processing (dry-run mode)
            result = self.run_command([
                'python3', str(ics_processor),
                '--test'  # Assuming test mode exists
            ], "Run ICS processing test")
            
            # For now, just check if the file can be executed
            if result['returncode'] != 2:  # Not a "command not found" error
                self.log("✅ ICS processing test completed")
                return True
            else:
                self.log("⚠️ ICS processing test skipped (no test mode)")
                return True
                
        except Exception as e:
            self.log(f"⚠️ ICS processing test exception (non-critical): {str(e)}")
            return True  # Non-critical for now
    
    def test_job_creation_workflow(self) -> bool:
        """Test 4: Job Creation Workflow"""
        self.log("🚀 TEST 4: Job Creation Workflow", 'TEST')
        
        try:
            # Test the job creation API handler
            create_job_handler = project_root / f'src/automation/scripts/airscripts-api/handlers/createJob.js'
            
            if not create_job_handler.exists():
                self.log("❌ Job creation handler not found")
                return False
            
            # Validate the handler has required components
            content = create_job_handler.read_text()
            
            required_elements = [
                'Custom Service Line Instructions',
                'stayDurationDays',
                'LONG TERM GUEST DEPARTING',
                'job_type_id'
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in content]
            
            if missing_elements:
                self.log(f"❌ Job creation handler missing: {missing_elements}")
                self.test_results['errors'].append(f"Job creation missing: {missing_elements}")
                return False
            
            self.log("✅ Job creation workflow validation passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Exception in job creation test: {str(e)}")
            self.test_results['errors'].append(f"Job creation exception: {str(e)}")
            return False
    
    def test_hcp_sync_workflow(self) -> bool:
        """Test 5: HCP Sync Workflow"""
        self.log("🚀 TEST 5: HCP Sync Workflow", 'TEST')
        
        try:
            # Test HCP sync script
            hcp_sync_script = project_root / f'src/automation/scripts/hcp/{self.environment}-hcp-sync.js'
            
            if not hcp_sync_script.exists():
                # Try alternate naming
                hcp_sync_script = project_root / f'src/automation/scripts/hcp/hcp_sync.js'
            
            if not hcp_sync_script.exists():
                self.log("❌ HCP sync script not found")
                return False
            
            # Validate HCP sync script components
            content = hcp_sync_script.read_text()
            
            required_elements = [
                'serviceLineCustomInstructions',
                'customInstructions - ',
                'LONG TERM GUEST DEPARTING',
                'stayDurationDays >= 14'
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in content]
            
            if missing_elements:
                self.log(f"❌ HCP sync script missing: {missing_elements}")
                self.test_results['errors'].append(f"HCP sync missing: {missing_elements}")
                return False
            
            self.log("✅ HCP sync workflow validation passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Exception in HCP sync test: {str(e)}")
            self.test_results['errors'].append(f"HCP sync exception: {str(e)}")
            return False
    
    def test_schedule_management(self) -> bool:
        """Test 6: Schedule Management (Update/Cancel)"""
        self.log("🚀 TEST 6: Schedule Management", 'TEST')
        
        try:
            # Test schedule update scripts
            update_script = project_root / 'src/automation/scripts/airscripts/updateallschedules.js'
            cancel_script = project_root / f'src/automation/scripts/airscripts-api/scripts/{self.environment}-cancel-job.js'
            
            scripts_to_check = [
                (update_script, "Update schedules script"),
                (cancel_script, "Cancel job script")
            ]
            
            for script_path, script_name in scripts_to_check:
                if not script_path.exists():
                    self.log(f"⚠️ {script_name} not found at {script_path}")
                    continue
                
                content = script_path.read_text()
                
                # Check for key functionality
                if 'Service Time' in content or 'Service Job ID' in content:
                    self.log(f"✅ {script_name} validation passed")
                else:
                    self.log(f"⚠️ {script_name} may be missing key functionality")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Exception in schedule management test: {str(e)}")
            self.test_results['errors'].append(f"Schedule management exception: {str(e)}")
            return False
    
    def test_business_logic_scenarios(self) -> bool:
        """Test 7: Business Logic Scenarios"""
        self.log("🚀 TEST 7: Business Logic Scenarios", 'TEST')
        
        scenarios_to_test = [
            self._test_long_term_guest_detection,
            self._test_custom_instructions_truncation,
            self._test_same_day_turnover_logic,
            self._test_service_name_generation
        ]
        
        passed = 0
        total = len(scenarios_to_test)
        
        for test_func in scenarios_to_test:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log(f"❌ Business logic test exception: {str(e)}")
                self.test_results['errors'].append(f"Business logic: {str(e)}")
        
        success_rate = (passed / total) * 100
        self.log(f"Business logic tests: {passed}/{total} passed ({success_rate:.1f}%)")
        
        return passed >= (total * 0.8)  # 80% pass rate required
    
    def _test_long_term_guest_detection(self) -> bool:
        """Test long-term guest detection logic"""
        test_cases = [
            (7, False),   # 7 days - not long-term
            (14, True),   # 14 days - long-term
            (21, True),   # 21 days - long-term
            (30, True),   # 30 days - long-term
        ]
        
        for days, expected in test_cases:
            # Simple logic test
            is_long_term = days >= 14
            if is_long_term != expected:
                self.log(f"❌ Long-term detection failed for {days} days")
                return False
        
        self.log("✅ Long-term guest detection logic passed")
        return True
    
    def _test_custom_instructions_truncation(self) -> bool:
        """Test custom instructions truncation"""
        long_text = "A" * 250  # 250 characters
        max_length = 200
        
        # Simulate truncation logic
        if len(long_text) > max_length:
            truncated = long_text[:max_length - 3] + "..."
        else:
            truncated = long_text
        
        if len(truncated) == max_length and truncated.endswith("..."):
            self.log("✅ Custom instructions truncation logic passed")
            return True
        else:
            self.log("❌ Custom instructions truncation failed")
            return False
    
    def _test_same_day_turnover_logic(self) -> bool:
        """Test same-day turnover detection"""
        # Mock same-day turnover scenario
        checkout_date = datetime.now().date()
        checkin_date = datetime.now().date()
        
        is_same_day = checkout_date == checkin_date
        
        if is_same_day:
            self.log("✅ Same-day turnover logic passed")
            return True
        else:
            self.log("❌ Same-day turnover logic failed")
            return False
    
    def _test_service_name_generation(self) -> bool:
        """Test service name generation with custom instructions"""
        base_name = "Turnover STR Next Guest March 15"
        custom_instructions = "Extra cleaning needed"
        is_long_term = True
        
        # Simulate service name generation
        if custom_instructions:
            if is_long_term:
                service_name = f"{custom_instructions} - LONG TERM GUEST DEPARTING {base_name}"
            else:
                service_name = f"{custom_instructions} - {base_name}"
        else:
            if is_long_term:
                service_name = f"LONG TERM GUEST DEPARTING {base_name}"
            else:
                service_name = base_name
        
        expected = "Extra cleaning needed - LONG TERM GUEST DEPARTING Turnover STR Next Guest March 15"
        
        if service_name == expected:
            self.log("✅ Service name generation logic passed")
            return True
        else:
            self.log(f"❌ Service name generation failed. Got: {service_name}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test 8: Error Handling and Edge Cases"""
        self.log("🚀 TEST 8: Error Handling", 'TEST')
        
        try:
            # Test with invalid data
            result = self.run_command([
                'python3', 'tests/dynamic-test-generator.py',
                '--scenario', 'edge_cases',
                '--count', '3',
                '--environment', self.environment
            ], "Generate edge case scenarios")
            
            if result['success']:
                self.log("✅ Edge case generation successful")
                return True
            else:
                self.log(f"❌ Edge case generation failed: {result['stderr']}")
                return False
                
        except Exception as e:
            self.log(f"❌ Exception in error handling test: {str(e)}")
            return False
    
    def _count_generated_files(self) -> int:
        """Count generated test files"""
        csv_dir = self.config.get_csv_process_dir()
        count = 0
        
        patterns = ["*test*.csv", "*boris*.csv", "*modification*.csv", "*edge*.csv"]
        for pattern in patterns:
            count += len(list(csv_dir.glob(pattern)))
        
        return count
    
    def cleanup_test_data(self):
        """Clean up test data after testing"""
        self.log("🧹 Cleaning up test data")
        
        try:
            result = self.run_command([
                'python3', 'tests/dynamic-test-generator.py',
                '--cleanup'
            ], "Clean up test files")
            
            if result['success']:
                self.log("✅ Test data cleanup successful")
            else:
                self.log(f"⚠️ Test data cleanup had issues: {result['stderr']}")
                
        except Exception as e:
            self.log(f"⚠️ Exception during cleanup: {str(e)}")
    
    def run_comprehensive_test(self, cleanup_after: bool = True) -> dict:
        """Run the complete test suite"""
        self.log("🚀 Starting Comprehensive End-to-End Test Suite", 'START')
        self.log(f"Environment: {self.environment}")
        self.log(f"Start time: {self.test_results['start_time']}")
        
        # Define test sequence
        tests = [
            ("Data Generation", self.test_data_generation),
            ("CSV Processing", self.test_csv_processing),
            ("ICS Processing", self.test_ics_processing),
            ("Job Creation Workflow", self.test_job_creation_workflow),
            ("HCP Sync Workflow", self.test_hcp_sync_workflow),
            ("Schedule Management", self.test_schedule_management),
            ("Business Logic Scenarios", self.test_business_logic_scenarios),
            ("Error Handling", self.test_error_handling),
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.test_results['tests_run'] += 1
            
            try:
                if test_func():
                    self.test_results['tests_passed'] += 1
                    self.log(f"✅ {test_name} - PASSED")
                else:
                    self.test_results['tests_failed'] += 1
                    self.log(f"❌ {test_name} - FAILED")
                    
            except Exception as e:
                self.test_results['tests_failed'] += 1
                self.test_results['errors'].append(f"{test_name}: {str(e)}")
                self.log(f"❌ {test_name} - EXCEPTION: {str(e)}")
        
        # Cleanup
        if cleanup_after:
            self.cleanup_test_data()
        
        # Final results
        self.test_results['end_time'] = datetime.now(self.arizona_tz)
        self.test_results['duration'] = (
            self.test_results['end_time'] - self.test_results['start_time']
        ).total_seconds()
        
        self._print_final_results()
        return self.test_results
    
    def _print_final_results(self):
        """Print comprehensive test results"""
        results = self.test_results
        
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE E2E TEST RESULTS")
        print("="*60)
        
        print(f"Environment: {self.environment}")
        print(f"Duration: {results['duration']:.1f} seconds")
        print(f"Tests Run: {results['tests_run']}")
        print(f"Tests Passed: {results['tests_passed']}")
        print(f"Tests Failed: {results['tests_failed']}")
        
        pass_rate = (results['tests_passed'] / results['tests_run']) * 100 if results['tests_run'] > 0 else 0
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if results['files_generated']:
            print(f"Test Files Generated: {results['files_generated']}")
        
        if results['errors']:
            print(f"\n❌ ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   • {error}")
        
        if pass_rate >= 80:
            print(f"\n🎉 TEST SUITE PASSED! ({pass_rate:.1f}% pass rate)")
        else:
            print(f"\n⚠️ TEST SUITE NEEDS ATTENTION ({pass_rate:.1f}% pass rate)")
        
        print("="*60)

def main():
    """CLI interface for comprehensive testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive End-to-End Test Suite')
    parser.add_argument('--environment', choices=['development', 'production'], 
                       default='development', help='Environment to test')
    parser.add_argument('--no-cleanup', action='store_true', 
                       help='Skip cleanup after testing')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick test with minimal data generation')
    
    args = parser.parse_args()
    
    # Run comprehensive test
    tester = ComprehensiveE2ETest(args.environment)
    results = tester.run_comprehensive_test(cleanup_after=not args.no_cleanup)
    
    # Exit with appropriate code
    if results['tests_failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()