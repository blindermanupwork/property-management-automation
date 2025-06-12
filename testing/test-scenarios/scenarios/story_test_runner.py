#!/usr/bin/env python3
"""
Story-Based Testing Framework Runner
Executes the comprehensive business logic testing scenarios for the property management automation system.

This script runs chapters 0-3 of the story-based testing framework:
- Chapter 0: Baseline (Clean State)
- Chapter 1: Initial Business Logic Setup  
- Chapter 2: Business Logic Stress Tests
- Chapter 3: Edge Cases & Removals

Each chapter tests specific business rules that affect revenue and prevent data corruption.
"""

import os
import sys
import shutil
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add automation src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from automation.config_wrapper import Config
    from automation.controller import AutomationController
except ImportError:
    print("⚠️  Warning: Could not import automation modules. Running in simulation mode.")
    Config = None
    AutomationController = None


class StoryTestRunner:
    """
    Manages execution of story-based testing scenarios with comprehensive business logic validation.
    """
    
    def __init__(self, dry_run: bool = False, user_verification: bool = True):
        self.dry_run = dry_run
        self.user_verification = user_verification
        self.scenarios_dir = Path(__file__).parent
        self.automation_root = project_root
        
        # Define scenario chapters (0-3 as per revised design)
        self.chapters = {
            "00_baseline": {
                "name": "Baseline - Clean State",
                "description": "Empty starting point with no active reservations",
                "files": [
                    "boris_itrip_00_baseline.csv",
                    "boris_evolve_00_baseline.csv", 
                    "boris_evolve_tab2_00_baseline.csv",
                    "boris_ics_00_baseline.ics"
                ],
                "expected_results": [
                    "All Airtable reservations cleared/archived",
                    "Clean slate for testing business logic"
                ]
            },
            "01_initial_bookings": {
                "name": "Initial Business Logic Setup",
                "description": "Test different business scenarios, not just basic bookings",
                "files": [
                    "boris_itrip_01_sameday.csv",     # Same-day turnover with iTrip flag
                    "boris_evolve_01_overlap.csv",    # Overlapping scenario
                    "boris_evolve_tab2_01_listing.csv", # Property matching edge case  
                    "boris_ics_01_block.ics"         # Entry type classification
                ],
                "expected_results": [
                    "Boris iTrip: Standard reservation created",
                    "Boris Evolve: Marked as overlapping with iTrip", 
                    "Boris iTrip: Also marked as overlapping with Evolve",
                    "Boris Evolve Tab2: Property correctly matched via listing number (202)",
                    "Boris ICS: Classified as 'Block' entry type (not Reservation)"
                ]
            },
            "02_date_changes": {
                "name": "Business Logic Stress Tests", 
                "description": "ONE customer modifies dates, others test complex business rules",
                "files": [
                    "boris_itrip_02_modified.csv",      # Date modification (Same Day flag changes)
                    "boris_evolve_02_turnover.csv",     # Same-day turnover reality
                    "boris_evolve_tab2_02_arrival.csv", # Same-day arrival  
                    "boris_ics_02_adjacent.ics"        # Adjacent not overlapping
                ],
                "expected_results": [
                    "Boris iTrip: Old record marked 'Old', new 'Modified' record created",
                    "Boris Evolve + Tab2: Both marked with same-day turnover flags",
                    "Boris ICS: Adjacent to Tab2 but NOT overlapping", 
                    "Service scheduling adjusted for same-day cleaning priority"
                ]
            },
            "03_cancellations": {
                "name": "Edge Cases & Removals",
                "description": "Test removal logic and extreme edge cases",
                "files": [
                    "boris_itrip_03_override.csv",      # Guest override scenario
                    "boris_evolve_03_cancelled.csv",    # Cancellation/removal
                    "boris_evolve_tab2_03_longterm.csv", # Long-term guest trigger
                    "boris_ics_03_invalid.ics"         # Property matching failure
                ],
                "expected_results": [
                    "Boris iTrip: Guest override logic tested (Smith Family pattern)",
                    "Boris Evolve: Status changed to 'Removed'",
                    "Boris Evolve Tab2: Long-term guest flags activated (16 nights)",
                    "Boris ICS: Processing error handled gracefully",
                    "Same-day turnover conflict resolved due to Evolve cancellation"
                ]
            }
        }
        
        # Processing destinations for each file type
        self.file_destinations = {
            "itrip": "src/automation/scripts/CSV_process_development/",
            "evolve": "src/automation/scripts/CSV_process_development/", 
            "evolve_tab2": "src/automation/scripts/CSV_process_development/",
            "ics": "config/environments/dev/"  # ICS files go to dev config (after isolation)
        }
        
        # Create isolated ICS directory
        self.test_ics_dir = self.automation_root / "test_data/scenarios/test_ics_isolated/"
        self.original_ics_backup_dir = self.automation_root / "test_data/scenarios/original_ics_backup/"
        
        self.results_log = []
        
    def log_result(self, message: str, level: str = "INFO"):
        """Log a result with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.results_log.append(log_entry)
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        if "itrip" in filename:
            return "itrip"
        elif "evolve_tab2" in filename:
            return "evolve_tab2"
        elif "evolve" in filename:
            return "evolve"
        elif filename.endswith(".ics"):
            return "ics"
        else:
            return "unknown"
    
    def copy_scenario_files(self, chapter: str) -> bool:
        """Copy scenario files to their processing destinations"""
        chapter_info = self.chapters[chapter]
        chapter_dir = self.scenarios_dir / chapter
        
        if not chapter_dir.exists():
            self.log_result(f"Chapter directory not found: {chapter_dir}", "ERROR")
            return False
        
        success = True
        
        for filename in chapter_info["files"]:
            source_file = chapter_dir / filename
            
            if not source_file.exists():
                self.log_result(f"Scenario file not found: {source_file}", "ERROR")
                success = False
                continue
            
            file_type = self.get_file_type(filename)
            if file_type == "unknown":
                self.log_result(f"Unknown file type: {filename}", "WARNING")
                continue
                
            dest_dir = self.automation_root / self.file_destinations[file_type]
            dest_file = dest_dir / filename
            
            if self.dry_run:
                self.log_result(f"DRY RUN: Would copy {source_file} → {dest_file}")
            else:
                try:
                    # Ensure destination directory exists
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(source_file, dest_file)
                    self.log_result(f"Copied: {filename} → {dest_dir.name}/")
                    
                except Exception as e:
                    self.log_result(f"Failed to copy {filename}: {e}", "ERROR")
                    success = False
        
        return success
    
    def setup_isolated_ics_environment(self) -> bool:
        """Setup isolated ICS environment that only processes test files"""
        if self.dry_run:
            self.log_result("DRY RUN: Would setup isolated ICS environment")
            return True
        
        try:
            # Create isolated directories
            self.test_ics_dir.mkdir(parents=True, exist_ok=True)
            self.original_ics_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup original dev ICS directory
            original_dev_ics = self.automation_root / "config/environments/dev/"
            
            # Find existing ICS files in dev directory (not our test files)
            existing_ics_files = [f for f in original_dev_ics.glob("*.ics") if not f.name.startswith("boris_")]
            
            if existing_ics_files:
                self.log_result(f"📦 Backing up {len(existing_ics_files)} existing ICS files")
                for ics_file in existing_ics_files:
                    backup_file = self.original_ics_backup_dir / ics_file.name
                    shutil.copy2(ics_file, backup_file)
                    # Remove from dev directory to isolate our test
                    ics_file.unlink()
                    self.log_result(f"Backed up and removed: {ics_file.name}")
            
            self.log_result("✅ ICS environment isolated for testing")
            return True
            
        except Exception as e:
            self.log_result(f"❌ Failed to setup isolated ICS environment: {e}", "ERROR")
            return False
    
    def restore_ics_environment(self) -> bool:
        """Restore original ICS environment after testing"""
        if self.dry_run:
            self.log_result("DRY RUN: Would restore original ICS environment")
            return True
        
        try:
            # Restore backed up ICS files
            if self.original_ics_backup_dir.exists():
                backup_files = list(self.original_ics_backup_dir.glob("*.ics"))
                if backup_files:
                    original_dev_ics = self.automation_root / "config/environments/dev/"
                    self.log_result(f"🔄 Restoring {len(backup_files)} original ICS files")
                    
                    for backup_file in backup_files:
                        restored_file = original_dev_ics / backup_file.name
                        shutil.copy2(backup_file, restored_file)
                        self.log_result(f"Restored: {backup_file.name}")
                    
                    # Clean up backup directory
                    shutil.rmtree(self.original_ics_backup_dir)
            
            # Clean up test ICS directory
            if self.test_ics_dir.exists():
                shutil.rmtree(self.test_ics_dir)
            
            self.log_result("✅ Original ICS environment restored")
            return True
            
        except Exception as e:
            self.log_result(f"❌ Failed to restore ICS environment: {e}", "ERROR")
            return False
    
    def run_automation_processing(self) -> bool:
        """Run the automation processing for development environment with ICS isolation"""
        if self.dry_run:
            self.log_result("DRY RUN: Would execute automation processing (with ICS skipped)")
            return True
        
        try:
            # Create a temporary script that runs automation without ICS processing
            temp_runner = self._create_isolated_automation_runner()
            
            # Run the isolated automation
            cmd = ["python3", str(temp_runner)]
            self.log_result(f"Executing: {' '.join(cmd)} (ICS processing skipped for testing)")
            
            result = subprocess.run(
                cmd,
                cwd=self.automation_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Clean up temp runner
            if temp_runner.exists():
                temp_runner.unlink()
            
            if result.returncode == 0:
                self.log_result("✅ Automation processing completed successfully (ICS skipped)")
                if result.stdout.strip():
                    self.log_result(f"Output: {result.stdout.strip()}")
                return True
            else:
                self.log_result(f"❌ Automation processing failed (exit code: {result.returncode})", "ERROR")
                if result.stderr.strip():
                    self.log_result(f"Error: {result.stderr.strip()}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_result("❌ Automation processing timed out", "ERROR")
            return False
        except Exception as e:
            self.log_result(f"❌ Failed to run automation: {e}", "ERROR")
            return False
    
    def _create_isolated_automation_runner(self) -> Path:
        """Create a temporary automation runner that skips ICS processing"""
        temp_runner = self.automation_root / "temp_story_test_runner.py"
        
        runner_content = '''#!/usr/bin/env python3
"""
Temporary Story Test Automation Runner - Skips ICS Processing
This script runs only CSV and other automations, excluding ICS processing
to prevent triggering all development ICS feeds during testing.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))

from automation.config_dev import DevConfig
from automation.controller import AutomationController
from automation.scripts.run_automation import (
    run_gmail_automation, 
    run_evolve_automation, 
    run_csv_automation,
    run_hcp_automation
)

def main():
    """Run development automation but SKIP ICS processing for testing"""
    print("🧪 Story Test Automation Runner (ICS Processing Disabled)")
    
    try:
        config = DevConfig()
        controller = AutomationController(config)
        
        # Only run these automations, skip ICS
        automations_to_run = [
            ("Gmail", run_gmail_automation),
            ("Evolve", run_evolve_automation), 
            ("CSV", run_csv_automation),
            ("HCP", run_hcp_automation)
        ]
        
        for name, automation_func in automations_to_run:
            if controller.get_automation_status(name):
                print(f"\\n🚀 Running {name} automation...")
                result = automation_func(config)
                
                if result["success"]:
                    print(f"✅ {name}: {result['message']}")
                    controller.update_automation_status(name, True, result["message"])
                else:
                    print(f"❌ {name}: {result['message']}")
                    controller.update_automation_status(name, False, result["message"])
            else:
                print(f"⏭️  {name} automation is disabled, skipping...")
        
        print("\\n🎉 Story test automation completed (ICS processing skipped)")
        
    except Exception as e:
        print(f"❌ Error running story test automation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(temp_runner, 'w') as f:
            f.write(runner_content)
        
        temp_runner.chmod(0o755)  # Make executable
        return temp_runner
    
    def wait_for_user_verification(self, chapter: str):
        """Wait for user to verify results in Airtable"""
        if not self.user_verification:
            return
        
        chapter_info = self.chapters[chapter]
        
        print(f"\n🔍 **Manual Verification Required for {chapter_info['name']}**")
        print(f"📋 Description: {chapter_info['description']}")
        print("\n📊 **Expected Results:**")
        for result in chapter_info["expected_results"]:
            print(f"   • {result}")
        
        print(f"\n🌐 **Please check Airtable Dev Base:**")
        print(f"   • Go to: https://airtable.com/app67yWFv0hKdl6jM")
        print(f"   • Check the Reservations table")
        print(f"   • Verify the expected results above")
        print(f"   • Look for status changes, overlapping flags, entry types, etc.")
        
        while True:
            response = input(f"\n✅ Have you verified the results? (y/n/s for skip): ").lower().strip()
            if response in ['y', 'yes']:
                self.log_result(f"✅ User verified results for {chapter}")
                break
            elif response in ['s', 'skip']:
                self.log_result(f"⏭️  User skipped verification for {chapter}")
                break
            elif response in ['n', 'no']:
                print("❌ Please check the results before continuing...")
            else:
                print("Please enter 'y' for yes, 'n' for no, or 's' to skip")
    
    def cleanup_processed_files(self, chapter: str):
        """Move processed files to done directory"""
        if self.dry_run:
            self.log_result("DRY RUN: Would cleanup processed files")
            return
        
        chapter_info = self.chapters[chapter]
        
        for filename in chapter_info["files"]:
            if filename.endswith(".ics"):
                continue  # ICS files don't get moved to done directory
                
            file_type = self.get_file_type(filename)
            source_dir = self.automation_root / self.file_destinations[file_type]
            source_file = source_dir / filename
            
            # Move to done directory
            done_dir = self.automation_root / "src/automation/scripts/CSV_done_development/"
            done_file = done_dir / filename
            
            if source_file.exists():
                try:
                    done_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(source_file, done_file)
                    self.log_result(f"Moved to done: {filename}")
                except Exception as e:
                    self.log_result(f"Failed to move {filename}: {e}", "WARNING")
    
    def run_chapter(self, chapter: str) -> bool:
        """Run a complete chapter of the story-based testing framework"""
        chapter_info = self.chapters[chapter]
        
        print(f"\n" + "="*80)
        print(f"🎬 **Chapter {chapter}: {chapter_info['name']}**")
        print(f"📋 Description: {chapter_info['description']}")
        print("="*80)
        
        try:
            # Step 1: Copy scenario files
            self.log_result(f"📁 Step 1: Copying scenario files for {chapter}")
            if not self.copy_scenario_files(chapter):
                self.log_result(f"❌ Failed to copy files for {chapter}", "ERROR")
                return False
            
            # Step 2: Run automation processing  
            self.log_result(f"⚙️  Step 2: Running automation processing")
            if not self.run_automation_processing():
                self.log_result(f"❌ Automation processing failed for {chapter}", "ERROR")
                return False
            
            # Step 3: User verification
            self.log_result(f"🔍 Step 3: User verification")
            self.wait_for_user_verification(chapter)
            
            # Step 4: Cleanup
            self.log_result(f"🧹 Step 4: Cleaning up processed files")
            self.cleanup_processed_files(chapter)
            
            self.log_result(f"✅ Chapter {chapter} completed successfully")
            return True
            
        except Exception as e:
            self.log_result(f"❌ Chapter {chapter} failed: {e}", "ERROR")
            return False
    
    def run_complete_story(self) -> bool:
        """Run the complete story-based testing framework (chapters 0-3)"""
        start_time = datetime.now()
        
        print("🚀 **Story-Based Testing Framework - Business Logic Validation**")
        print(f"📅 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"👤 User Verification: {'Enabled' if self.user_verification else 'Disabled'}")
        
        # Run each chapter in sequence
        chapters_to_run = ["00_baseline", "01_initial_bookings", "02_date_changes", "03_cancellations"]
        
        for chapter in chapters_to_run:
            if not self.run_chapter(chapter):
                self.log_result(f"❌ Story testing failed at {chapter}", "ERROR")
                return False
            
            # Brief pause between chapters
            if chapter != chapters_to_run[-1]:  # Not the last chapter
                self.log_result("⏳ Pausing 5 seconds before next chapter...")
                if not self.dry_run:
                    time.sleep(5)
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n" + "="*80)
        print(f"🎉 **Story-Based Testing Framework Complete!**")
        print(f"⏱️  Duration: {duration}")
        print(f"📊 Chapters Completed: {len(chapters_to_run)}")
        print("="*80)
        
        self.log_result("🎉 Complete story-based testing framework finished successfully!")
        return True
    
    def save_results_log(self):
        """Save the results log to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.scenarios_dir / f"story_test_results_{timestamp}.log"
        
        try:
            with open(log_file, 'w') as f:
                f.write("Story-Based Testing Framework Results\n")
                f.write("="*50 + "\n\n")
                for entry in self.results_log:
                    f.write(entry + "\n")
            
            self.log_result(f"📝 Results saved to: {log_file}")
            
        except Exception as e:
            self.log_result(f"Failed to save results log: {e}", "ERROR")


def main():
    """Main entry point for story test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Story-Based Testing Framework Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 story_test_runner.py                    # Run complete story with user verification
  python3 story_test_runner.py --dry-run          # Simulate without actual processing
  python3 story_test_runner.py --no-verification  # Run without user verification pauses
  python3 story_test_runner.py --chapter 01       # Run single chapter
        """
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Simulate the testing without actual file processing"
    )
    
    parser.add_argument(
        "--no-verification",
        action="store_true", 
        help="Skip user verification pauses between scenarios"
    )
    
    parser.add_argument(
        "--chapter",
        choices=["00", "01", "02", "03"],
        help="Run only a specific chapter (00=baseline, 01=initial, 02=stress, 03=edge)"
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = StoryTestRunner(
        dry_run=args.dry_run,
        user_verification=not args.no_verification
    )
    
    try:
        if args.chapter:
            # Run single chapter
            chapter_map = {
                "00": "00_baseline",
                "01": "01_initial_bookings", 
                "02": "02_date_changes",
                "03": "03_cancellations"
            }
            chapter = chapter_map[args.chapter]
            success = runner.run_chapter(chapter)
        else:
            # Run complete story
            success = runner.run_complete_story()
        
        # Save results
        runner.save_results_log()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        runner.log_result("❌ Testing interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        runner.log_result(f"❌ Unexpected error: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()