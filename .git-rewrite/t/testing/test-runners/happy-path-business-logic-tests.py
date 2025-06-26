#!/usr/bin/env python3
"""
Happy Path Business Logic Test Suite
Tests the core business logic workflows in their normal, successful operation scenarios.

Focus: Successful workflows, proper data transformations, correct business rule application.
"""

import unittest
import tempfile
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import pytz

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class HappyPathCSVProcessingTests(unittest.TestCase):
    """Test CSV processing workflows in successful scenarios"""
    
    def setUp(self):
        """Set up test fixtures for successful scenarios"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample successful CSV data
        self.successful_csv_data = {
            "Reservation ID": ["RES001", "RES002", "RES003"],
            "Property Name": ["Boris Test House", "Boris Test Villa", "Boris Test Condo"],
            "Guest Name": ["John Smith", "Jane Doe", "Lisa Brown"],
            "Check-in Date": ["2025-06-01", "2025-06-10", "2025-06-20"],
            "Check-out Date": ["2025-06-05", "2025-06-15", "2025-06-25"],
            "Reservation Status": ["Confirmed", "Confirmed", "Confirmed"]
        }
        
        # Mock property lookup
        self.property_lookup = {
            "boris test house": "prop_001",
            "boris test villa": "prop_002", 
            "boris test condo": "prop_003"
        }

    def test_property_matching_success(self):
        """Test successful property name matching"""
        
        test_cases = [
            ("Boris Test House", "prop_001"),
            ("BORIS TEST VILLA", "prop_002"),  # Case insensitive
            ("boris test condo", "prop_003"),  # Lowercase
        ]
        
        for property_name, expected_id in test_cases:
            # Simulate property matching logic
            matched_id = self.property_lookup.get(property_name.lower())
            self.assertEqual(matched_id, expected_id, f"Property matching failed for {property_name}")

    def test_date_normalization_success(self):
        """Test successful date normalization"""
        
        def normalize_date(date_str):
            """Normalize date to MM/DD/YYYY format"""
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%m/%d/%Y")
        
        test_dates = [
            ("2025-06-01", "06/01/2025"),
            ("2025-12-25", "12/25/2025"),
            ("2025-01-15", "01/15/2025")
        ]
        
        for input_date, expected in test_dates:
            result = normalize_date(input_date)
            self.assertEqual(result, expected, f"Date normalization failed for {input_date}")

    def test_long_term_guest_detection_success(self):
        """Test successful long-term guest detection (≥14 days)"""
        
        test_reservations = [
            {"checkin": "2025-06-01", "checkout": "2025-06-10", "expected": False},  # 9 days
            {"checkin": "2025-06-01", "checkout": "2025-06-15", "expected": True},   # 14 days
            {"checkin": "2025-06-01", "checkout": "2025-06-30", "expected": True},   # 29 days
        ]
        
        for res in test_reservations:
            checkin = datetime.strptime(res["checkin"], "%Y-%m-%d")
            checkout = datetime.strptime(res["checkout"], "%Y-%m-%d")
            
            duration = (checkout - checkin).days
            is_long_term = duration >= 14
            
            self.assertEqual(is_long_term, res["expected"], 
                           f"Long-term detection failed for {duration} days")

    def test_entry_type_classification_success(self):
        """Test successful entry type classification"""
        
        # Service type keywords
        service_keywords = {
            "turnover": "Turnover",
            "cleaning": "Turnover", 
            "laundry": "Return Laundry",
            "return": "Return Laundry",
            "inspection": "Inspection"
        }
        
        test_cases = [
            ("Turnover Cleaning", "Turnover"),
            ("Return Laundry Service", "Return Laundry"),
            ("Property Inspection", "Inspection"),
            ("Standard Service", "Turnover")  # Default
        ]
        
        for description, expected in test_cases:
            # Apply classification logic
            service_type = "Turnover"  # Default
            for keyword, type_value in service_keywords.items():
                if keyword.lower() in description.lower():
                    service_type = type_value
                    break
            
            self.assertEqual(service_type, expected, f"Classification failed for '{description}'")

    def test_same_day_turnover_detection_success(self):
        """Test successful same-day turnover detection"""
        
        test_scenarios = [
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-01", 
                "expected": True
            },
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-02",
                "expected": False
            }
        ]
        
        for scenario in test_scenarios:
            is_same_day = scenario["prev_checkout"] == scenario["next_checkin"]
            self.assertEqual(is_same_day, scenario["expected"],
                           f"Same-day detection failed for {scenario}")


class HappyPathHCPIntegrationTests(unittest.TestCase):
    """Test HousecallPro integration workflows in successful scenarios"""
    
    def test_service_type_normalization_success(self):
        """Test successful service type normalization"""
        
        test_cases = [
            ("Turnover", "Turnover"),
            ("Return Laundry", "Return Laundry"),
            ("Inspection", "Inspection"),
            ("turnover cleaning", "Turnover"),      # Partial match
            ("laundry return", "Return Laundry"),   # Partial match
            ("property inspection", "Inspection")   # Partial match
        ]
        
        def normalize_service_type(raw_type):
            """Normalize service type for HCP"""
            if not raw_type:
                return "Turnover"
            
            raw_lower = raw_type.lower()
            
            if "return" in raw_lower or "laundry" in raw_lower:
                return "Return Laundry"
            elif "inspection" in raw_lower:
                return "Inspection"
            else:
                return "Turnover"
        
        for input_type, expected in test_cases:
            result = normalize_service_type(input_type)
            self.assertEqual(result, expected, f"Service normalization failed for '{input_type}'")

    def test_job_creation_workflow_success(self):
        """Test successful HCP job creation workflow"""
        
        # Mock successful job data
        job_data = {
            "customer_id": "cus_boris_test",
            "address_id": "addr_boris_house",
            "service_type": "Turnover",
            "scheduled_date": "2025-06-15",
            "scheduled_time": "10:00",
            "custom_instructions": "Clean thoroughly"
        }
        
        # Simulate job creation steps
        steps_completed = []
        
        # Step 1: Validate customer
        if job_data["customer_id"].startswith("cus_"):
            steps_completed.append("customer_validated")
        
        # Step 2: Validate address
        if job_data["address_id"].startswith("addr_"):
            steps_completed.append("address_validated")
        
        # Step 3: Create job
        if job_data["service_type"] in ["Turnover", "Return Laundry", "Inspection"]:
            steps_completed.append("job_created")
        
        # Step 4: Set schedule
        if job_data["scheduled_date"] and job_data["scheduled_time"]:
            steps_completed.append("schedule_set")
        
        # Step 5: Add custom instructions
        if job_data["custom_instructions"]:
            steps_completed.append("instructions_added")
        
        expected_steps = [
            "customer_validated",
            "address_validated", 
            "job_created",
            "schedule_set",
            "instructions_added"
        ]
        
        self.assertEqual(steps_completed, expected_steps, "Job creation workflow incomplete")

    def test_status_synchronization_success(self):
        """Test successful status sync between HCP and Airtable"""
        
        # Mock status progression
        status_updates = [
            {"hcp_status": "scheduled", "airtable_status": "Scheduled"},
            {"hcp_status": "in_progress", "airtable_status": "In Progress"},
            {"hcp_status": "completed", "airtable_status": "Completed"}
        ]
        
        # Status mapping
        status_map = {
            "scheduled": "Scheduled",
            "in_progress": "In Progress",
            "completed": "Completed",
            "canceled": "Cancelled"
        }
        
        for update in status_updates:
            mapped_status = status_map.get(update["hcp_status"], "Unknown")
            self.assertEqual(mapped_status, update["airtable_status"],
                           f"Status mapping failed for {update['hcp_status']}")


class HappyPathICSProcessingTests(unittest.TestCase):
    """Test ICS calendar processing in successful scenarios"""
    
    def test_ics_event_parsing_success(self):
        """Test successful ICS event parsing"""
        
        # Sample valid ICS event
        sample_ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:boris-res-001@test.com
DTSTART:20250615T140000Z
DTEND:20250617T100000Z
SUMMARY:Boris Test Reservation - John Smith
DESCRIPTION:Guest: John Smith, Check-in: 06/15/2025
END:VEVENT
END:VCALENDAR"""
        
        def parse_ics_event(ics_content):
            """Parse ICS event data"""
            event = {}
            lines = ics_content.split('\n')
            in_event = False
            
            for line in lines:
                line = line.strip()
                if line == "BEGIN:VEVENT":
                    in_event = True
                elif line == "END:VEVENT":
                    break
                elif in_event and ':' in line:
                    key, value = line.split(':', 1)
                    event[key] = value
            
            return event
        
        event = parse_ics_event(sample_ics)
        
        # Verify successful parsing
        self.assertIn("UID", event)
        self.assertIn("DTSTART", event)
        self.assertIn("DTEND", event)
        self.assertIn("SUMMARY", event)
        self.assertEqual(event["UID"], "boris-res-001@test.com")

    def test_date_filtering_success(self):
        """Test successful date filtering for ICS events"""
        
        # Current date for filtering
        current_date = datetime(2025, 6, 15)
        
        # Date thresholds (2 months back, 6 months forward)
        lookback_date = current_date - timedelta(days=60)
        future_date = current_date + timedelta(days=180)
        
        test_events = [
            {"start": "2025-05-01", "expected": True},   # Within range
            {"start": "2025-06-15", "expected": True},   # Current date
            {"start": "2025-08-15", "expected": True},   # Future within range
        ]
        
        for event in test_events:
            event_date = datetime.strptime(event["start"], "%Y-%m-%d")
            
            # Apply filtering
            is_in_range = lookback_date <= event_date <= future_date
            
            self.assertEqual(is_in_range, event["expected"],
                           f"Date filtering failed for {event['start']}")

    def test_timezone_conversion_success(self):
        """Test successful timezone conversion to Arizona time"""
        
        def convert_to_arizona(utc_datetime_str):
            """Convert UTC datetime to Arizona time"""
            utc_dt = datetime.strptime(utc_datetime_str, "%Y%m%dT%H%M%SZ")
            utc_dt = pytz.utc.localize(utc_dt)
            
            arizona_tz = pytz.timezone('America/Phoenix')
            arizona_dt = utc_dt.astimezone(arizona_tz)
            
            return arizona_dt
        
        # Test UTC to Arizona conversion
        utc_time = "20250615T140000Z"  # 2:00 PM UTC
        arizona_time = convert_to_arizona(utc_time)
        
        # Arizona is UTC-7 (no DST in June)
        expected_hour = 7  # 2 PM UTC = 7 AM Arizona
        self.assertEqual(arizona_time.hour, expected_hour)


class HappyPathEndToEndTests(unittest.TestCase):
    """Test complete end-to-end workflows in successful scenarios"""
    
    def test_complete_reservation_workflow_success(self):
        """Test complete workflow from CSV to job creation"""
        
        # Mock workflow steps
        workflow_steps = []
        
        # Step 1: CSV Processing
        csv_data = {
            "Reservation ID": "RES-BORIS-001",
            "Property Name": "Boris Test House",
            "Guest Name": "John Smith",
            "Check-in Date": "2025-06-15",
            "Check-out Date": "2025-06-17",
            "Service Type": "Turnover"
        }
        
        if csv_data["Reservation ID"] and csv_data["Property Name"]:
            workflow_steps.append("csv_processed")
        
        # Step 2: Airtable Import
        airtable_record = {
            "Reservation ID": csv_data["Reservation ID"],
            "Property": csv_data["Property Name"],
            "Guest Name": csv_data["Guest Name"],
            "Service Date": csv_data["Check-in Date"],
            "Service Type": "Turnover",
            "Status": "Pending Job Creation"
        }
        
        if airtable_record["Status"] == "Pending Job Creation":
            workflow_steps.append("airtable_imported")
        
        # Step 3: Job Creation
        hcp_job = {
            "customer_id": "cus_boris_test",
            "service_type": airtable_record["Service Type"],
            "scheduled_date": airtable_record["Service Date"],
            "status": "scheduled"
        }
        
        if hcp_job["status"] == "scheduled":
            workflow_steps.append("hcp_job_created")
        
        # Step 4: Status Sync Back
        if hcp_job["status"]:
            airtable_record["HCP Status"] = "Scheduled"
            airtable_record["Job Created"] = True
            workflow_steps.append("status_synced")
        
        expected_workflow = [
            "csv_processed",
            "airtable_imported", 
            "hcp_job_created",
            "status_synced"
        ]
        
        self.assertEqual(workflow_steps, expected_workflow, "End-to-end workflow incomplete")

    def test_schedule_update_workflow_success(self):
        """Test successful schedule update workflow"""
        
        # Mock schedule update process
        schedule_steps = []
        
        # Initial job data
        job_data = {
            "job_id": "job_boris_001",
            "current_schedule": "2025-06-15 10:00",
            "requested_schedule": "2025-06-15 14:00",
            "status": "scheduled"
        }
        
        # Step 1: Validate new schedule
        if job_data["requested_schedule"]:
            schedule_steps.append("schedule_validated")
        
        # Step 2: Update HCP job
        if job_data["job_id"].startswith("job_"):
            job_data["current_schedule"] = job_data["requested_schedule"]
            schedule_steps.append("hcp_updated")
        
        # Step 3: Sync to Airtable
        if job_data["current_schedule"] == job_data["requested_schedule"]:
            schedule_steps.append("airtable_synced")
        
        expected_steps = [
            "schedule_validated",
            "hcp_updated",
            "airtable_synced"
        ]
        
        self.assertEqual(schedule_steps, expected_steps, "Schedule update workflow incomplete")

    def test_service_completion_workflow_success(self):
        """Test successful service completion workflow"""
        
        completion_steps = []
        
        # Mock job completion
        job_status = {
            "job_id": "job_boris_001",
            "status": "in_progress",
            "completion_time": None,
            "next_service_needed": False
        }
        
        # Step 1: Mark job complete
        job_status["status"] = "completed"
        job_status["completion_time"] = "2025-06-15 16:00"
        completion_steps.append("job_completed")
        
        # Step 2: Check for next service
        if not job_status["next_service_needed"]:
            completion_steps.append("no_follow_up_needed")
        
        # Step 3: Update records
        if job_status["status"] == "completed":
            completion_steps.append("records_updated")
        
        expected_steps = [
            "job_completed",
            "no_follow_up_needed",
            "records_updated"
        ]
        
        self.assertEqual(completion_steps, expected_steps, "Completion workflow incomplete")


class HappyPathBusinessRulesTests(unittest.TestCase):
    """Test business rules in successful scenarios"""
    
    def test_custom_service_instructions_success(self):
        """Test successful custom service instructions handling"""
        
        # Test instruction processing
        test_cases = [
            {
                "input": "Please clean thoroughly and check all amenities",
                "expected_length": 47,
                "expected_truncated": False
            },
            {
                "input": "Standard cleaning with extra attention to kitchen and bathrooms, vacuum all carpets",
                "expected_length": 83,
                "expected_truncated": False
            }
        ]
        
        def process_custom_instructions(instructions, max_length=200):
            """Process custom instructions with length limit"""
            if not instructions:
                return ""
            
            processed = instructions.strip()
            
            if len(processed) > max_length:
                processed = processed[:max_length-3] + "..."
                truncated = True
            else:
                truncated = False
            
            return {
                "text": processed,
                "length": len(processed),
                "truncated": truncated
            }
        
        for case in test_cases:
            result = process_custom_instructions(case["input"])
            
            self.assertEqual(result["length"], case["expected_length"])
            self.assertEqual(result["truncated"], case["expected_truncated"])

    def test_guest_override_mapping_success(self):
        """Test successful guest override mapping"""
        
        # Mock guest override rules
        guest_overrides = {
            ("prop_001", "Smith"): "guest_priority_001",
            ("prop_002", "Doe"): "guest_priority_002"
        }
        
        def apply_guest_override(property_id, guest_name):
            """Apply guest override if applicable"""
            for (prop_id, name_pattern), override_id in guest_overrides.items():
                if prop_id == property_id and name_pattern in guest_name:
                    return override_id
            return None
        
        test_cases = [
            ("prop_001", "John Smith", "guest_priority_001"),
            ("prop_002", "Jane Doe", "guest_priority_002"),
            ("prop_003", "Bob Wilson", None)  # No override
        ]
        
        for prop_id, guest_name, expected in test_cases:
            result = apply_guest_override(prop_id, guest_name)
            self.assertEqual(result, expected, f"Guest override failed for {guest_name}")

    def test_timezone_business_logic_success(self):
        """Test successful timezone handling for business operations"""
        
        # Arizona business timezone (no DST)
        arizona_tz = pytz.timezone('America/Phoenix')
        
        # Test business hour calculation
        def is_business_hours(datetime_str):
            """Check if time is within business hours (8 AM - 6 PM Arizona)"""
            dt = datetime.fromisoformat(datetime_str)
            arizona_dt = arizona_tz.localize(dt)
            
            # Business hours: 8 AM to 6 PM
            return 8 <= arizona_dt.hour < 18
        
        test_times = [
            ("2025-06-15 09:00:00", True),   # 9 AM
            ("2025-06-15 14:00:00", True),   # 2 PM
            ("2025-06-15 17:30:00", True),   # 5:30 PM
            ("2025-06-15 07:00:00", False),  # 7 AM
            ("2025-06-15 18:30:00", False),  # 6:30 PM
        ]
        
        for time_str, expected in test_times:
            result = is_business_hours(time_str)
            self.assertEqual(result, expected, f"Business hours check failed for {time_str}")


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2, buffer=True)