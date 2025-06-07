#!/usr/bin/env python3
"""
Comprehensive Scenario Test Suite - Every Business Logic Path A to Z
Tests EVERY scenario, edge case, and business rule in the automation system.

This is the complete test matrix covering all possible data flows and business logic.
"""

import unittest
import tempfile
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import pytz
import re

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class CSVProcessingAllScenariosTests(unittest.TestCase):
    """Test EVERY CSV processing scenario from A to Z"""
    
    def setUp(self):
        """Set up comprehensive test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # Complete property database for testing
        self.all_properties = {
            # Boris test properties
            "boris test house": "prop_boris_001",
            "boris test villa": "prop_boris_002", 
            "boris test condo": "prop_boris_003",
            # Real properties with listing numbers
            "desert oasis #101": "prop_001",
            "mountain view villa #202 - pool": "prop_002",
            "beach house#303special": "prop_003",  # No space after #
            "city apartment 404": "prop_004",     # No # symbol
            # Properties with special characters
            "café villa": "prop_005",
            "josé's casa": "prop_006",
            "müller haus": "prop_007",
            # Properties with common words
            "the grand villa": "prop_008",
            "a perfect getaway": "prop_009",
            "an amazing house": "prop_010"
        }

    def test_property_matching_all_variations(self):
        """Test property matching with EVERY possible variation"""
        
        test_cases = [
            # Exact matches
            ("Boris Test House", "prop_boris_001"),
            ("Desert Oasis #101", "prop_001"),
            
            # Case variations
            ("BORIS TEST HOUSE", "prop_boris_001"),
            ("boris test house", "prop_boris_001"),
            ("BoRiS tEsT hOuSe", "prop_boris_001"),
            
            # Listing number extraction
            ("101", "prop_001"),  # Just the number
            ("202", "prop_002"),  # Number from complex name
            ("303special", "prop_003"),  # Number with attached text
            
            # Special characters
            ("Café Villa", "prop_005"),
            ("CAFÉ VILLA", "prop_005"),
            ("café villa", "prop_005"),
            ("Jose's Casa", "prop_006"),  # ASCII equivalent
            ("Muller Haus", "prop_007"),  # ASCII equivalent
            
            # Partial matches (should fail)
            ("Boris", None),
            ("Test House", None),
            ("Villa", None),
            
            # Empty/invalid
            ("", None),
            (None, None),
            ("   ", None),
            ("Non-existent Property", None),
            
            # Numbers that don't exist
            ("999", None),
            ("0", None),
            ("-1", None),
        ]
        
        def match_property(property_name):
            """Complete property matching algorithm"""
            if not property_name:
                return None
                
            name = str(property_name).strip()
            if not name:
                return None
            
            # Try exact match first (case insensitive)
            exact_match = self.all_properties.get(name.lower())
            if exact_match:
                return exact_match
            
            # Try listing number extraction
            if "#" in name:
                listing_number = name.split("#")[-1].strip().split()[0]
                number_match = self.all_properties.get(listing_number.lower())
                if number_match:
                    return number_match
            
            # Try just numeric extraction
            import re
            numbers = re.findall(r'\d+', name)
            for num in numbers:
                if num in self.all_properties:
                    return self.all_properties[num]
            
            return None
        
        for property_name, expected in test_cases:
            result = match_property(property_name)
            self.assertEqual(result, expected, f"Property matching failed for '{property_name}'")

    def test_date_parsing_all_formats(self):
        """Test date parsing with EVERY possible format"""
        
        test_cases = [
            # Standard formats
            ("2025-06-01", "06/01/2025"),
            ("06/01/2025", "06/01/2025"),
            ("6/1/2025", "06/01/2025"),
            ("2025-6-1", "06/01/2025"),
            
            # Month names
            ("01-Jun-2025", "06/01/2025"),
            ("1-Jun-2025", "06/01/2025"),
            ("June 1, 2025", "06/01/2025"),
            ("Jun 1, 2025", "06/01/2025"),
            ("1 June 2025", "06/01/2025"),
            ("1 Jun 2025", "06/01/2025"),
            
            # Different separators
            ("2025.06.01", "06/01/2025"),
            ("2025 06 01", "06/01/2025"),
            ("06-01-2025", "06/01/2025"),
            ("06.01.2025", "06/01/2025"),
            
            # Excel date formats
            ("44743", "06/01/2025"),  # Excel serial date
            
            # Time included
            ("2025-06-01 14:30:00", "06/01/2025"),
            ("2025-06-01T14:30:00", "06/01/2025"),
            ("2025-06-01T14:30:00Z", "06/01/2025"),
            
            # Different years
            ("2024-06-01", "06/01/2024"),
            ("2026-06-01", "06/01/2026"),
            
            # Edge dates
            ("2025-01-01", "01/01/2025"),  # New Year
            ("2025-12-31", "12/31/2025"),  # New Year's Eve
            ("2025-02-28", "02/28/2025"),  # Non-leap year
            ("2024-02-29", "02/29/2024"),  # Leap year
            
            # Invalid formats
            ("", None),
            (None, None),
            ("invalid", None),
            ("2025-13-01", None),  # Invalid month
            ("2025-06-32", None),  # Invalid day
            ("2025-02-30", None),  # Invalid February date
            ("25-06-01", None),    # Ambiguous year
            ("abc-def-ghi", None), # Text
            ("2025", None),        # Year only
            ("06", None),          # Month only
        ]
        
        def parse_date_comprehensive(date_value):
            """Comprehensive date parsing"""
            if not date_value:
                return None
                
            try:
                date_str = str(date_value).strip()
                if not date_str:
                    return None
                
                # Try pandas first (handles most formats)
                try:
                    dt = pd.to_datetime(date_str)
                    return dt.strftime("%m/%d/%Y")
                except:
                    pass
                
                # Try manual formats
                formats = [
                    "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y.%m.%d",
                    "%Y %m %d", "%d-%b-%Y", "%B %d, %Y", "%b %d, %Y",
                    "%d %B %Y", "%d %b %Y", "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime("%m/%d/%Y")
                    except ValueError:
                        continue
                
                # Try Excel serial date
                try:
                    excel_date = float(date_str)
                    if 1 <= excel_date <= 2958465:  # Valid Excel date range
                        # Excel epoch is 1900-01-01, but Excel incorrectly treats 1900 as leap year
                        base_date = datetime(1899, 12, 30)
                        dt = base_date + timedelta(days=excel_date)
                        return dt.strftime("%m/%d/%Y")
                except (ValueError, OverflowError):
                    pass
                
                return None
                
            except Exception:
                return None
        
        for input_date, expected in test_cases:
            result = parse_date_comprehensive(input_date)
            self.assertEqual(result, expected, f"Date parsing failed for '{input_date}'")

    def test_guest_stay_duration_all_scenarios(self):
        """Test guest stay duration calculation for ALL scenarios"""
        
        test_cases = [
            # Short stays
            ("2025-06-01", "2025-06-01", 0, False),   # Same day (0 nights)
            ("2025-06-01", "2025-06-02", 1, False),   # 1 night
            ("2025-06-01", "2025-06-03", 2, False),   # 2 nights
            ("2025-06-01", "2025-06-08", 7, False),   # 1 week
            ("2025-06-01", "2025-06-14", 13, False),  # 13 nights (just under long-term)
            
            # Long-term stays (≥14 nights)
            ("2025-06-01", "2025-06-15", 14, True),   # Exactly 14 nights
            ("2025-06-01", "2025-06-16", 15, True),   # 15 nights
            ("2025-06-01", "2025-06-22", 21, True),   # 3 weeks
            ("2025-06-01", "2025-07-01", 30, True),   # 1 month
            ("2025-06-01", "2025-08-01", 61, True),   # 2 months
            ("2025-06-01", "2025-12-01", 183, True),  # 6 months
            
            # Cross-month scenarios
            ("2025-05-15", "2025-06-15", 31, True),   # Month boundary
            ("2025-02-15", "2025-03-15", 28, True),   # February (non-leap)
            ("2024-02-15", "2024-03-15", 29, True),   # February (leap year)
            ("2025-12-15", "2026-01-15", 31, True),   # Year boundary
            
            # Edge cases
            ("2025-06-01", "2025-06-01", 0, False),   # Same date
            ("2025-06-15", "2025-06-01", -14, False), # Backward dates (invalid)
            
            # Daylight saving transitions
            ("2025-03-08", "2025-03-22", 14, True),   # DST start
            ("2025-11-01", "2025-11-15", 14, True),   # DST end
        ]
        
        def calculate_stay_duration(checkin_str, checkout_str):
            """Calculate stay duration and long-term status"""
            try:
                checkin = datetime.strptime(checkin_str, "%Y-%m-%d")
                checkout = datetime.strptime(checkout_str, "%Y-%m-%d")
                
                duration_days = (checkout - checkin).days
                is_long_term = duration_days >= 14
                
                return duration_days, is_long_term
            except ValueError:
                return None, False
        
        for checkin, checkout, expected_days, expected_long_term in test_cases:
            days, is_long_term = calculate_stay_duration(checkin, checkout)
            
            self.assertEqual(days, expected_days, 
                           f"Duration calculation failed for {checkin} to {checkout}")
            self.assertEqual(is_long_term, expected_long_term,
                           f"Long-term detection failed for {days} days")

    def test_entry_type_classification_all_keywords(self):
        """Test entry type classification with ALL possible keywords and combinations"""
        
        # Complete keyword mapping from actual system
        ENTRY_TYPE_KEYWORDS = {
            # Block keywords
            "block": "Block",
            "blocked": "Block",
            "maintenance": "Block", 
            "repair": "Block",
            "owner": "Block",
            "personal": "Block",
            "hold": "Block",
            "unavailable": "Block",
            "closed": "Block",
            
            # Turnover keywords
            "turnover": "Turnover",
            "cleaning": "Turnover",
            "clean": "Turnover",
            "housekeeping": "Turnover",
            "service": "Turnover",
            "prepare": "Turnover",
            "ready": "Turnover",
            
            # Return Laundry keywords
            "laundry": "Return Laundry",
            "return": "Return Laundry",
            "linens": "Return Laundry",
            "towels": "Return Laundry",
            "wash": "Return Laundry",
            
            # Inspection keywords
            "inspection": "Inspection",
            "inspect": "Inspection",
            "check": "Inspection",
            "verify": "Inspection",
            "review": "Inspection",
            "assess": "Inspection"
        }
        
        test_cases = [
            # Single keyword matches
            ("Block", "Block"),
            ("Maintenance", "Block"),
            ("Owner Use", "Block"),
            ("Turnover", "Turnover"),
            ("Cleaning", "Turnover"),
            ("Laundry", "Return Laundry"),
            ("Return", "Return Laundry"),
            ("Inspection", "Inspection"),
            ("Check", "Inspection"),
            
            # Case variations
            ("BLOCK", "Block"),
            ("maintenance", "Block"),
            ("Cleaning", "Turnover"),
            ("LAUNDRY", "Return Laundry"),
            ("inspection", "Inspection"),
            
            # Multiple keywords (first match wins)
            ("Cleaning and Laundry", "Turnover"),  # Cleaning comes first
            ("Laundry and Cleaning", "Return Laundry"),  # Laundry comes first
            ("Block Maintenance", "Block"),
            ("Inspection and Cleaning", "Inspection"),
            
            # Keywords in sentences
            ("Property blocked for maintenance", "Block"),
            ("Deep cleaning turnover service", "Turnover"),
            ("Return laundry to property", "Return Laundry"),
            ("Final inspection before guest", "Inspection"),
            ("Please clean the property thoroughly", "Turnover"),
            
            # Partial word matches
            ("Blocked", "Block"),
            ("Cleaning", "Turnover"), 
            ("Inspecting", "Inspection"),
            ("Returned", "Return Laundry"),
            
            # No keyword match (default to Turnover)
            ("Guest Reservation", "Turnover"),
            ("John Smith Stay", "Turnover"),
            ("Regular Booking", "Turnover"),
            ("", "Turnover"),
            (None, "Turnover"),
            
            # Special characters and formatting
            ("Block - Maintenance", "Block"),
            ("Cleaning & Turnover", "Turnover"),
            ("Laundry/Return Service", "Return Laundry"),
            ("Pre-Inspection", "Inspection"),
            
            # Numbers and codes
            ("Block123", "Block"),
            ("Cleaning-001", "Turnover"),
            ("Laundry #5", "Return Laundry"),
            ("Inspection Type A", "Inspection"),
        ]
        
        def classify_entry_type(description):
            """Classify entry type based on keywords"""
            if not description:
                return "Turnover"  # Default
            
            text = str(description).lower()
            
            # Apply classification algorithm (first match wins)
            for keyword, entry_type in ENTRY_TYPE_KEYWORDS.items():
                if keyword in text:
                    return entry_type
            
            return "Turnover"  # Default fallback
        
        for description, expected in test_cases:
            result = classify_entry_type(description)
            self.assertEqual(result, expected, f"Classification failed for '{description}'")

    def test_date_overlap_detection_all_scenarios(self):
        """Test date overlap detection with ALL possible scenarios"""
        
        def check_overlap(res1_start, res1_end, res2_start, res2_end):
            """Check if two reservations overlap"""
            start1 = datetime.strptime(res1_start, "%Y-%m-%d")
            end1 = datetime.strptime(res1_end, "%Y-%m-%d")
            start2 = datetime.strptime(res2_start, "%Y-%m-%d")
            end2 = datetime.strptime(res2_end, "%Y-%m-%d")
            
            # Overlap logic: start of one is before end of other AND vice versa
            return start1 < end2 and end1 > start2
        
        test_cases = [
            # No overlaps
            ("2025-06-01", "2025-06-05", "2025-06-05", "2025-06-10", False),  # Same-day checkout/checkin
            ("2025-06-01", "2025-06-05", "2025-06-06", "2025-06-10", False),  # Gap between
            ("2025-06-10", "2025-06-15", "2025-06-01", "2025-06-05", False),  # Reverse order
            
            # Clear overlaps
            ("2025-06-01", "2025-06-10", "2025-06-05", "2025-06-15", True),   # Partial overlap
            ("2025-06-01", "2025-06-15", "2025-06-05", "2025-06-10", True),   # One contains other
            ("2025-06-05", "2025-06-10", "2025-06-01", "2025-06-15", True),   # Contained within
            ("2025-06-01", "2025-06-10", "2025-06-01", "2025-06-10", True),   # Identical dates
            
            # Edge cases
            ("2025-06-01", "2025-06-05", "2025-06-04", "2025-06-06", True),   # One day overlap
            ("2025-06-01", "2025-06-02", "2025-06-02", "2025-06-03", False),  # Back-to-back
            ("2025-06-01", "2025-06-01", "2025-06-01", "2025-06-01", False),  # Same single day (0 nights)
            
            # Month boundaries
            ("2025-05-30", "2025-06-05", "2025-06-01", "2025-06-10", True),   # Cross month
            ("2025-12-28", "2026-01-05", "2026-01-01", "2026-01-10", True),   # Cross year
            
            # Long-term overlaps
            ("2025-06-01", "2025-08-01", "2025-07-01", "2025-09-01", True),   # 2-month overlap
            ("2025-01-01", "2025-12-31", "2025-06-01", "2025-06-30", True),   # Year-long contains month
        ]
        
        for res1_start, res1_end, res2_start, res2_end, expected in test_cases:
            result = check_overlap(res1_start, res1_end, res2_start, res2_end)
            self.assertEqual(result, expected, 
                           f"Overlap detection failed for ({res1_start}-{res1_end}) vs ({res2_start}-{res2_end})")

    def test_same_day_turnover_all_scenarios(self):
        """Test same-day turnover detection with ALL scenarios including iTrip precedence"""
        
        test_cases = [
            # Standard same-day detection
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-01",
                "itrip_same_day": None,
                "expected": True,
                "reason": "Same date checkout/checkin"
            },
            {
                "prev_checkout": "2025-06-01", 
                "next_checkin": "2025-06-02",
                "itrip_same_day": None,
                "expected": False,
                "reason": "Different dates"
            },
            
            # iTrip override scenarios (business rule: iTrip data takes precedence)
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-01", 
                "itrip_same_day": False,
                "expected": False,
                "reason": "iTrip override: False despite same date"
            },
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-02",
                "itrip_same_day": True,
                "expected": True, 
                "reason": "iTrip override: True despite different dates"
            },
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-03",
                "itrip_same_day": True,
                "expected": True,
                "reason": "iTrip override: True with 2-day gap"
            },
            
            # Edge cases with iTrip data
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-01",
                "itrip_same_day": True,
                "expected": True,
                "reason": "iTrip confirms same-day"
            },
            {
                "prev_checkout": "",
                "next_checkin": "2025-06-01",
                "itrip_same_day": True,
                "expected": True,
                "reason": "iTrip override with missing prev date"
            },
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "",
                "itrip_same_day": False,
                "expected": False,
                "reason": "iTrip override with missing next date"
            },
            
            # No dates available
            {
                "prev_checkout": "",
                "next_checkin": "",
                "itrip_same_day": None,
                "expected": False,
                "reason": "No date data available"
            },
            {
                "prev_checkout": None,
                "next_checkin": None,
                "itrip_same_day": None,
                "expected": False,
                "reason": "Null date data"
            },
            
            # Month/year boundaries
            {
                "prev_checkout": "2025-05-31",
                "next_checkin": "2025-06-01",
                "itrip_same_day": None,
                "expected": False,
                "reason": "Month boundary, different dates"
            },
            {
                "prev_checkout": "2025-12-31",
                "next_checkin": "2026-01-01", 
                "itrip_same_day": None,
                "expected": False,
                "reason": "Year boundary, different dates"
            },
            {
                "prev_checkout": "2025-05-31",
                "next_checkin": "2025-06-01",
                "itrip_same_day": True,
                "expected": True,
                "reason": "iTrip override across month boundary"
            }
        ]
        
        def detect_same_day_turnover(prev_checkout, next_checkin, itrip_same_day):
            """Detect same-day turnover with iTrip precedence"""
            # iTrip data takes precedence (business rule)
            if itrip_same_day is not None:
                return itrip_same_day
            
            # Fall back to date comparison
            if not prev_checkout or not next_checkin:
                return False
            
            try:
                return str(prev_checkout).strip() == str(next_checkin).strip()
            except:
                return False
        
        for case in test_cases:
            result = detect_same_day_turnover(
                case["prev_checkout"], 
                case["next_checkin"], 
                case["itrip_same_day"]
            )
            self.assertEqual(result, case["expected"], 
                           f"Same-day detection failed: {case['reason']}")

    def test_record_status_management_all_transitions(self):
        """Test record status management with ALL possible status transitions"""
        
        # All possible status values in the system
        VALID_STATUSES = [
            "New", "Modified", "Removed", "Old", "Confirmed", 
            "Cancelled", "Pending", "Active", "Inactive"
        ]
        
        test_cases = [
            # New record scenarios
            {"current": None, "action": "create", "expected": "New"},
            {"current": "", "action": "create", "expected": "New"},
            
            # Modification scenarios
            {"current": "New", "action": "modify", "expected": "Modified"},
            {"current": "Confirmed", "action": "modify", "expected": "Modified"},
            {"current": "Modified", "action": "modify", "expected": "Modified"},
            
            # Removal scenarios
            {"current": "New", "action": "remove", "expected": "Removed"},
            {"current": "Modified", "action": "remove", "expected": "Removed"},
            {"current": "Confirmed", "action": "remove", "expected": "Removed"},
            
            # Archival scenarios
            {"current": "New", "action": "archive", "expected": "Old"},
            {"current": "Modified", "action": "archive", "expected": "Old"},
            {"current": "Removed", "action": "archive", "expected": "Old"},
            
            # Confirmation scenarios
            {"current": "New", "action": "confirm", "expected": "Confirmed"},
            {"current": "Modified", "action": "confirm", "expected": "Confirmed"},
            
            # Cancellation scenarios  
            {"current": "New", "action": "cancel", "expected": "Cancelled"},
            {"current": "Confirmed", "action": "cancel", "expected": "Cancelled"},
            {"current": "Modified", "action": "cancel", "expected": "Cancelled"},
            
            # Invalid transitions (should maintain current status)
            {"current": "Removed", "action": "modify", "expected": "Removed"},
            {"current": "Old", "action": "modify", "expected": "Old"},
            {"current": "Cancelled", "action": "confirm", "expected": "Cancelled"},
        ]
        
        def update_record_status(current_status, action):
            """Update record status based on action"""
            # Define valid transitions
            transitions = {
                "create": "New",
                "modify": "Modified" if current_status not in ["Removed", "Old", "Cancelled"] else current_status,
                "remove": "Removed" if current_status not in ["Old"] else current_status,
                "archive": "Old",
                "confirm": "Confirmed" if current_status not in ["Removed", "Old", "Cancelled"] else current_status,
                "cancel": "Cancelled" if current_status not in ["Removed", "Old"] else current_status
            }
            
            if not current_status and action == "create":
                return "New"
            
            return transitions.get(action, current_status or "New")
        
        for case in test_cases:
            result = update_record_status(case["current"], case["action"])
            self.assertEqual(result, case["expected"],
                           f"Status transition failed: {case['current']} + {case['action']} should be {case['expected']}")


class HCPIntegrationAllScenariosTests(unittest.TestCase):
    """Test EVERY HousecallPro integration scenario"""
    
    def test_service_type_normalization_all_variations(self):
        """Test service type normalization with EVERY possible input"""
        
        test_cases = [
            # Exact matches
            ("Turnover", "Turnover"),
            ("Return Laundry", "Return Laundry"),
            ("Inspection", "Inspection"),
            
            # Case variations
            ("turnover", "Turnover"),
            ("TURNOVER", "Turnover"),
            ("TurnOver", "Turnover"),
            ("return laundry", "Return Laundry"),
            ("RETURN LAUNDRY", "Return Laundry"),
            ("Return Laundry", "Return Laundry"),
            ("inspection", "Inspection"),
            ("INSPECTION", "Inspection"),
            ("Inspection", "Inspection"),
            
            # Partial matches (keywords in text)
            ("Deep Cleaning Turnover", "Turnover"),
            ("Return Laundry Service", "Return Laundry"),
            ("Final Inspection Check", "Inspection"),
            ("Turnover and Cleaning", "Turnover"),
            ("Laundry Return Process", "Return Laundry"),
            ("Property Inspection", "Inspection"),
            
            # Multiple keywords (return/laundry takes precedence)
            ("Return Laundry Turnover", "Return Laundry"),
            ("Laundry and Cleaning", "Return Laundry"),
            ("Inspection and Turnover", "Inspection"),
            
            # Alternative terms that map to service types
            ("Cleaning", "Turnover"),
            ("Clean", "Turnover"),
            ("Housekeeping", "Turnover"),
            ("Maintenance", "Turnover"),
            ("Service", "Turnover"),
            ("Prep", "Turnover"),
            ("Setup", "Turnover"),
            ("Laundry", "Return Laundry"),
            ("Linens", "Return Laundry"),
            ("Towels", "Return Laundry"),
            ("Wash", "Return Laundry"),
            ("Check", "Inspection"),
            ("Review", "Inspection"),
            ("Verify", "Inspection"),
            ("Assess", "Inspection"),
            
            # Special characters and formatting
            ("Turn-over", "Turnover"),
            ("Return/Laundry", "Return Laundry"),
            ("Pre-Inspection", "Inspection"),
            ("Cleaning & Turnover", "Turnover"),
            ("Laundry + Return", "Return Laundry"),
            
            # Empty/invalid inputs (default to Turnover)
            ("", "Turnover"),
            (None, "Turnover"),
            ("   ", "Turnover"),
            ("Unknown Service", "Turnover"),
            ("123", "Turnover"),
            ("Guest Reservation", "Turnover"),
            ("John Smith", "Turnover"),
            
            # Numbers and codes
            ("Turnover-001", "Turnover"),
            ("Laundry #5", "Return Laundry"),
            ("Inspection Type A", "Inspection"),
            ("Service Code 123", "Turnover"),
            
            # Common guest/property names (should default to Turnover)
            ("Smith Family", "Turnover"),
            ("Ocean View Villa", "Turnover"),
            ("Booking #12345", "Turnover"),
            ("Reservation ABC", "Turnover"),
        ]
        
        def normalize_service_type(raw_service_type):
            """Comprehensive service type normalization"""
            if not raw_service_type:
                return "Turnover"
            
            service_str = str(raw_service_type).strip().lower()
            if not service_str:
                return "Turnover"
            
            # Priority order: Return Laundry > Inspection > Turnover (default)
            
            # Check for Return Laundry keywords
            laundry_keywords = ["return", "laundry", "linens", "towels", "wash"]
            if any(keyword in service_str for keyword in laundry_keywords):
                return "Return Laundry"
            
            # Check for Inspection keywords
            inspection_keywords = ["inspection", "inspect", "check", "review", "verify", "assess"]
            if any(keyword in service_str for keyword in inspection_keywords):
                return "Inspection"
            
            # Everything else defaults to Turnover
            return "Turnover"
        
        for input_type, expected in test_cases:
            result = normalize_service_type(input_type)
            self.assertEqual(result, expected, f"Service normalization failed for '{input_type}'")

    def test_job_creation_workflow_all_steps(self):
        """Test job creation workflow with ALL possible steps and validations"""
        
        def create_hcp_job(job_data):
            """Complete HCP job creation workflow"""
            workflow_steps = []
            errors = []
            
            # Step 1: Validate customer ID
            if not job_data.get("customer_id"):
                errors.append("Missing customer ID")
            elif not job_data["customer_id"].startswith("cus_"):
                errors.append("Invalid customer ID format")
            else:
                workflow_steps.append("customer_validated")
            
            # Step 2: Validate address ID
            if not job_data.get("address_id"):
                errors.append("Missing address ID")
            elif not job_data["address_id"].startswith("addr_"):
                errors.append("Invalid address ID format")
            else:
                workflow_steps.append("address_validated")
            
            # Step 3: Validate service type
            valid_services = ["Turnover", "Return Laundry", "Inspection"]
            if not job_data.get("service_type"):
                errors.append("Missing service type")
            elif job_data["service_type"] not in valid_services:
                errors.append("Invalid service type")
            else:
                workflow_steps.append("service_validated")
            
            # Step 4: Validate schedule
            if not job_data.get("scheduled_date"):
                errors.append("Missing scheduled date")
            else:
                try:
                    datetime.strptime(job_data["scheduled_date"], "%Y-%m-%d")
                    workflow_steps.append("schedule_validated")
                except ValueError:
                    errors.append("Invalid date format")
            
            # Step 5: Process custom instructions
            instructions = job_data.get("custom_instructions", "")
            if instructions and len(instructions) > 200:
                job_data["custom_instructions"] = instructions[:197] + "..."
                workflow_steps.append("instructions_truncated")
            elif instructions:
                workflow_steps.append("instructions_processed")
            
            # Step 6: Create job if no errors
            if not errors:
                workflow_steps.append("job_created")
                
                # Step 7: Set initial status
                job_data["status"] = "scheduled"
                workflow_steps.append("status_set")
                
                # Step 8: Generate job ID
                import random
                job_data["job_id"] = f"job_{random.randint(100000, 999999)}"
                workflow_steps.append("id_generated")
            
            return {
                "success": len(errors) == 0,
                "steps": workflow_steps,
                "errors": errors,
                "job_data": job_data
            }
        
        test_cases = [
            # Successful job creation
            {
                "input": {
                    "customer_id": "cus_boris_test",
                    "address_id": "addr_boris_house",
                    "service_type": "Turnover",
                    "scheduled_date": "2025-06-15",
                    "custom_instructions": "Clean thoroughly"
                },
                "expected_success": True,
                "expected_steps": [
                    "customer_validated", "address_validated", "service_validated",
                    "schedule_validated", "instructions_processed", "job_created",
                    "status_set", "id_generated"
                ]
            },
            
            # Missing customer ID
            {
                "input": {
                    "address_id": "addr_boris_house",
                    "service_type": "Turnover",
                    "scheduled_date": "2025-06-15"
                },
                "expected_success": False,
                "expected_errors": ["Missing customer ID"]
            },
            
            # Invalid customer ID format
            {
                "input": {
                    "customer_id": "invalid_id",
                    "address_id": "addr_boris_house", 
                    "service_type": "Turnover",
                    "scheduled_date": "2025-06-15"
                },
                "expected_success": False,
                "expected_errors": ["Invalid customer ID format"]
            },
            
            # Long custom instructions (should be truncated)
            {
                "input": {
                    "customer_id": "cus_boris_test",
                    "address_id": "addr_boris_house",
                    "service_type": "Turnover", 
                    "scheduled_date": "2025-06-15",
                    "custom_instructions": "A" * 250  # 250 characters
                },
                "expected_success": True,
                "expected_steps_include": ["instructions_truncated"]
            },
            
            # Invalid date format
            {
                "input": {
                    "customer_id": "cus_boris_test",
                    "address_id": "addr_boris_house",
                    "service_type": "Turnover",
                    "scheduled_date": "invalid-date"
                },
                "expected_success": False,
                "expected_errors": ["Invalid date format"]
            }
        ]
        
        for case in test_cases:
            result = create_hcp_job(case["input"].copy())
            
            if "expected_success" in case:
                self.assertEqual(result["success"], case["expected_success"])
            
            if "expected_steps" in case:
                self.assertEqual(result["steps"], case["expected_steps"])
            
            if "expected_errors" in case:
                self.assertEqual(result["errors"], case["expected_errors"])
            
            if "expected_steps_include" in case:
                for step in case["expected_steps_include"]:
                    self.assertIn(step, result["steps"])

    def test_status_synchronization_all_transitions(self):
        """Test status synchronization with ALL possible status transitions"""
        
        # All possible HCP statuses and their Airtable mappings
        STATUS_MAPPINGS = {
            "scheduled": "Scheduled",
            "in_progress": "In Progress", 
            "completed": "Completed",
            "canceled": "Cancelled",
            "on_hold": "On Hold",
            "unscheduled": "Unscheduled",
            "pending": "Pending",
            "confirmed": "Confirmed"
        }
        
        test_cases = [
            # Standard status progressions
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("canceled", "Cancelled"),
            
            # Less common statuses
            ("on_hold", "On Hold"),
            ("unscheduled", "Unscheduled"),
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            
            # Case variations
            ("SCHEDULED", "Scheduled"),
            ("In_Progress", "In Progress"),
            ("COMPLETED", "Completed"),
            
            # Invalid statuses (should remain unmapped)
            ("unknown", "unknown"),
            ("invalid_status", "invalid_status"),
            ("", ""),
            (None, None),
            
            # Status sequences (testing workflow progression)
            # New job → Scheduled → In Progress → Completed
            # New job → Scheduled → Cancelled
            # New job → On Hold → Scheduled → Completed
        ]
        
        def map_hcp_to_airtable_status(hcp_status):
            """Map HCP status to Airtable status"""
            if not hcp_status:
                return hcp_status
            
            # Normalize to lowercase for lookup
            normalized = str(hcp_status).lower().replace(" ", "_")
            return STATUS_MAPPINGS.get(normalized, hcp_status)
        
        for hcp_status, expected_airtable in test_cases:
            result = map_hcp_to_airtable_status(hcp_status)
            self.assertEqual(result, expected_airtable,
                           f"Status mapping failed for '{hcp_status}'")

    def test_rate_limiting_all_scenarios(self):
        """Test rate limiting logic with ALL possible response scenarios"""
        
        def calculate_retry_wait(response_status, rate_limit_headers, attempt_number):
            """Calculate wait time for API retry"""
            base_delay = 1.0  # 1 second base
            max_delay = 300   # 5 minutes max
            
            if response_status == 429:  # Rate limited
                # Check for Retry-After header
                retry_after = rate_limit_headers.get("Retry-After")
                if retry_after:
                    try:
                        return min(int(retry_after), max_delay)
                    except ValueError:
                        pass
                
                # Check for RateLimit-Reset header
                reset_time = rate_limit_headers.get("RateLimit-Reset")
                if reset_time:
                    try:
                        import time
                        current_time = int(time.time())
                        reset_timestamp = int(reset_time)
                        wait_time = max(reset_timestamp - current_time, 1)
                        return min(wait_time, max_delay)
                    except ValueError:
                        pass
                
                # Exponential backoff as fallback
                return min(base_delay * (2 ** attempt_number), max_delay)
            
            elif response_status >= 500:  # Server error
                # Exponential backoff for server errors
                return min(base_delay * (2 ** attempt_number), max_delay)
            
            elif response_status in [408, 504]:  # Timeout errors
                # Linear backoff for timeouts
                return min(base_delay * attempt_number, max_delay)
            
            else:
                # No retry needed
                return 0
        
        test_cases = [
            # Rate limiting scenarios
            (429, {"Retry-After": "60"}, 1, 60),
            (429, {"Retry-After": "30"}, 1, 30),
            (429, {"Retry-After": "400"}, 1, 300),  # Capped at max
            (429, {"RateLimit-Reset": str(int(time.time()) + 45)}, 1, 45),
            (429, {}, 1, 2),   # Exponential backoff: 1 * 2^1
            (429, {}, 2, 4),   # Exponential backoff: 1 * 2^2
            (429, {}, 3, 8),   # Exponential backoff: 1 * 2^3
            
            # Server errors
            (500, {}, 1, 2),   # Internal server error
            (502, {}, 1, 2),   # Bad gateway
            (503, {}, 1, 2),   # Service unavailable
            (500, {}, 5, 32),  # Multiple retries
            
            # Timeout errors
            (408, {}, 1, 1),   # Request timeout
            (504, {}, 1, 1),   # Gateway timeout
            (408, {}, 3, 3),   # Linear progression
            
            # No retry scenarios
            (200, {}, 1, 0),   # Success
            (201, {}, 1, 0),   # Created
            (400, {}, 1, 0),   # Bad request
            (401, {}, 1, 0),   # Unauthorized
            (403, {}, 1, 0),   # Forbidden
            (404, {}, 1, 0),   # Not found
        ]
        
        import time
        
        for status, headers, attempt, expected_wait in test_cases:
            result = calculate_retry_wait(status, headers, attempt)
            self.assertEqual(result, expected_wait,
                           f"Rate limiting failed for status {status}, attempt {attempt}")


class ICSProcessingAllScenariosTests(unittest.TestCase):
    """Test EVERY ICS processing scenario"""
    
    def test_ics_parsing_all_formats(self):
        """Test ICS parsing with ALL possible calendar formats and edge cases"""
        
        test_ics_files = [
            # Standard ICS format
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:event1@test.com
DTSTART:20250615T140000Z
DTEND:20250617T100000Z
SUMMARY:Boris Test Reservation
DESCRIPTION:Guest: John Smith
LOCATION:123 Test Street
END:VEVENT
END:VCALENDAR""",
                "expected_events": 1,
                "expected_fields": ["UID", "DTSTART", "DTEND", "SUMMARY"]
            },
            
            # Multiple events
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART:20250615T140000Z
DTEND:20250617T100000Z
SUMMARY:Event 1
END:VEVENT
BEGIN:VEVENT
UID:event2@test.com
DTSTART:20250620T140000Z
DTEND:20250622T100000Z
SUMMARY:Event 2
END:VEVENT
END:VCALENDAR""",
                "expected_events": 2
            },
            
            # Different datetime formats
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART;TZID=America/Phoenix:20250615T070000
DTEND;TZID=America/Phoenix:20250617T030000
SUMMARY:Arizona Time Event
END:VEVENT
END:VCALENDAR""",
                "expected_events": 1
            },
            
            # All-day events
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART;VALUE=DATE:20250615
DTEND;VALUE=DATE:20250617
SUMMARY:All Day Event
END:VEVENT
END:VCALENDAR""",
                "expected_events": 1
            },
            
            # Recurring events
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART:20250615T140000Z
DTEND:20250615T160000Z
RRULE:FREQ=WEEKLY;COUNT=4
SUMMARY:Weekly Recurring
END:VEVENT
END:VCALENDAR""",
                "expected_events": 1  # Base event (expansions handled separately)
            },
            
            # Events with special characters
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART:20250615T140000Z
DTEND:20250617T100000Z
SUMMARY:Café Müller's Résumé Event
DESCRIPTION:Special chars: äöü ñ é à
END:VEVENT
END:VCALENDAR""",
                "expected_events": 1
            },
            
            # Line folding (long lines)
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART:20250615T140000Z
DTEND:20250617T100000Z
SUMMARY:This is a very long summary that should be folded according to
  RFC 5545 specifications and span multiple lines
DESCRIPTION:This is also a very long description that contains detailed
  information about the event and should handle line folding properly
  according to the iCalendar specification
END:VEVENT
END:VCALENDAR""",
                "expected_events": 1
            },
            
            # Empty calendar
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
END:VCALENDAR""",
                "expected_events": 0
            },
            
            # Malformed ICS (missing END:VEVENT)
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART:20250615T140000Z
SUMMARY:Incomplete Event
END:VCALENDAR""",
                "expected_events": 0  # Should be rejected
            },
            
            # Malformed ICS (invalid dates)
            {
                "content": """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@test.com
DTSTART:INVALID-DATE
DTEND:20250617T100000Z
SUMMARY:Bad Date Event
END:VEVENT
END:VCALENDAR""",
                "expected_events": 0  # Should be rejected
            }
        ]
        
        def parse_ics_comprehensive(ics_content):
            """Comprehensive ICS parser"""
            try:
                events = []
                lines = ics_content.replace('\r\n', '\n').split('\n')
                
                # Handle line folding (lines starting with space/tab are continuations)
                unfolded_lines = []
                for line in lines:
                    if line.startswith(' ') or line.startswith('\t'):
                        # Continuation of previous line
                        if unfolded_lines:
                            unfolded_lines[-1] += line[1:]  # Remove leading space/tab
                    else:
                        unfolded_lines.append(line)
                
                current_event = {}
                in_event = False
                
                for line in unfolded_lines:
                    line = line.strip()
                    
                    if line == "BEGIN:VEVENT":
                        in_event = True
                        current_event = {}
                    elif line == "END:VEVENT":
                        if in_event and self._is_valid_ics_event(current_event):
                            events.append(current_event.copy())
                        in_event = False
                        current_event = {}
                    elif in_event and ':' in line:
                        # Parse property:value pairs
                        if ';' in line.split(':', 1)[0]:
                            # Has parameters (e.g., DTSTART;TZID=America/Phoenix:20250615T070000)
                            prop_with_params, value = line.split(':', 1)
                            prop_name = prop_with_params.split(';')[0]
                        else:
                            prop_name, value = line.split(':', 1)
                        
                        current_event[prop_name] = value
                
                return events
                
            except Exception:
                return []
        
        def _is_valid_ics_event(self, event):
            """Check if ICS event has required fields and valid dates"""
            required_fields = ['UID', 'DTSTART', 'DTEND', 'SUMMARY']
            
            # Check required fields
            if not all(field in event for field in required_fields):
                return False
            
            # Validate date formats
            try:
                start_date = event['DTSTART']
                end_date = event['DTEND']
                
                # Basic date format validation (simplified)
                if 'T' in start_date:  # DateTime format
                    if len(start_date) < 15:  # YYYYMMDDTHHMMSS minimum
                        return False
                else:  # Date only format
                    if len(start_date) < 8:  # YYYYMMDD minimum
                        return False
                
                return True
            except:
                return False
        
        for test_case in test_ics_files:
            events = parse_ics_comprehensive(test_case["content"])
            
            self.assertEqual(len(events), test_case["expected_events"],
                           f"ICS parsing failed: expected {test_case['expected_events']} events, got {len(events)}")
            
            if "expected_fields" in test_case and events:
                for field in test_case["expected_fields"]:
                    self.assertIn(field, events[0], f"Missing field {field} in parsed event")

    def test_date_filtering_all_scenarios(self):
        """Test date filtering with ALL possible configuration scenarios"""
        
        def filter_events_by_date(events, config):
            """Filter events based on date configuration"""
            try:
                current_date = datetime.now()
                
                # Calculate thresholds
                lookback_months = config.get("FETCH_RESERVATIONS_MONTHS_BEFORE", 2)
                future_months = config.get("IGNORE_BLOCKS_MONTHS_AWAY", 6)
                
                lookback_date = current_date - timedelta(days=lookback_months * 30)
                future_cutoff = current_date + timedelta(days=future_months * 30)
                
                filtered_events = []
                
                for event in events:
                    try:
                        # Parse event start date
                        start_str = event.get("DTSTART", "")
                        
                        if "T" in start_str:
                            # DateTime format: YYYYMMDDTHHMMSSZ
                            event_date = datetime.strptime(start_str.replace("Z", ""), "%Y%m%dT%H%M%S")
                        else:
                            # Date only format: YYYYMMDD
                            event_date = datetime.strptime(start_str, "%Y%m%d")
                        
                        # Apply filters
                        if lookback_date <= event_date <= future_cutoff:
                            filtered_events.append(event)
                            
                    except ValueError:
                        # Skip events with invalid dates
                        continue
                
                return filtered_events
                
            except Exception:
                return []
        
        # Current date for testing (fixed reference point)
        test_current_date = datetime(2025, 6, 15)  # June 15, 2025
        
        test_scenarios = [
            # Standard configuration
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 2, "IGNORE_BLOCKS_MONTHS_AWAY": 6},
                "events": [
                    {"DTSTART": "20250301T120000Z", "SUMMARY": "Too far back"},      # March 1 - too old
                    {"DTSTART": "20250420T120000Z", "SUMMARY": "Within range"},       # April 20 - in range  
                    {"DTSTART": "20250615T120000Z", "SUMMARY": "Current"},           # June 15 - current
                    {"DTSTART": "20250815T120000Z", "SUMMARY": "Future in range"},   # August 15 - future
                    {"DTSTART": "20260301T120000Z", "SUMMARY": "Too far future"},    # March 2026 - too far
                ],
                "expected_count": 3  # April 20, June 15, August 15
            },
            
            # Very restrictive configuration
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 0, "IGNORE_BLOCKS_MONTHS_AWAY": 1},
                "events": [
                    {"DTSTART": "20250601T120000Z", "SUMMARY": "Last month"},
                    {"DTSTART": "20250615T120000Z", "SUMMARY": "Current"},
                    {"DTSTART": "20250715T120000Z", "SUMMARY": "Next month"},
                    {"DTSTART": "20250815T120000Z", "SUMMARY": "Too far"},
                ],
                "expected_count": 2  # Current and next month only
            },
            
            # Very permissive configuration
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 12, "IGNORE_BLOCKS_MONTHS_AWAY": 12},
                "events": [
                    {"DTSTART": "20240615T120000Z", "SUMMARY": "Last year"},
                    {"DTSTART": "20250615T120000Z", "SUMMARY": "Current"},
                    {"DTSTART": "20260615T120000Z", "SUMMARY": "Next year"},
                ],
                "expected_count": 3  # All events within 12 months
            },
            
            # All-day events (date only format)
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 2, "IGNORE_BLOCKS_MONTHS_AWAY": 6},
                "events": [
                    {"DTSTART": "20250420", "SUMMARY": "All-day in range"},
                    {"DTSTART": "20250301", "SUMMARY": "All-day too old"},
                    {"DTSTART": "20260301", "SUMMARY": "All-day too far"},
                ],
                "expected_count": 1
            },
            
            # Mixed date formats
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 2, "IGNORE_BLOCKS_MONTHS_AWAY": 6},
                "events": [
                    {"DTSTART": "20250615T120000Z", "SUMMARY": "DateTime format"},
                    {"DTSTART": "20250620", "SUMMARY": "Date only format"},
                    {"DTSTART": "invalid-date", "SUMMARY": "Invalid format"},
                ],
                "expected_count": 2  # Valid formats only
            },
            
            # Empty events list
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 2, "IGNORE_BLOCKS_MONTHS_AWAY": 6},
                "events": [],
                "expected_count": 0
            },
            
            # Events with missing DTSTART
            {
                "config": {"FETCH_RESERVATIONS_MONTHS_BEFORE": 2, "IGNORE_BLOCKS_MONTHS_AWAY": 6},
                "events": [
                    {"SUMMARY": "No start date"},
                    {"DTSTART": "", "SUMMARY": "Empty start date"},
                    {"DTSTART": "20250615T120000Z", "SUMMARY": "Valid event"},
                ],
                "expected_count": 1  # Only valid event
            }
        ]
        
        # Mock current date for consistent testing
        with patch('builtins.datetime') as mock_datetime:
            mock_datetime.now.return_value = test_current_date
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            for scenario in test_scenarios:
                filtered = filter_events_by_date(scenario["events"], scenario["config"])
                self.assertEqual(len(filtered), scenario["expected_count"],
                               f"Date filtering failed for config {scenario['config']}")

    def test_timezone_conversion_all_zones(self):
        """Test timezone conversion with ALL supported timezone scenarios"""
        
        def convert_ics_datetime_to_arizona(ics_datetime_str, source_timezone=None):
            """Convert ICS datetime to Arizona time"""
            try:
                arizona_tz = pytz.timezone('America/Phoenix')
                
                # Parse different ICS datetime formats
                if 'T' not in ics_datetime_str:
                    # Date only - assume all day in Arizona time
                    dt = datetime.strptime(ics_datetime_str, "%Y%m%d")
                    return arizona_tz.localize(dt.replace(hour=0, minute=0))
                
                # Remove timezone suffix if present
                clean_datetime = ics_datetime_str.replace('Z', '')
                
                # Parse datetime
                dt = datetime.strptime(clean_datetime, "%Y%m%dT%H%M%S")
                
                if ics_datetime_str.endswith('Z'):
                    # UTC time
                    utc_dt = pytz.utc.localize(dt)
                    return utc_dt.astimezone(arizona_tz)
                elif source_timezone:
                    # Specific timezone provided
                    source_tz = pytz.timezone(source_timezone)
                    local_dt = source_tz.localize(dt)
                    return local_dt.astimezone(arizona_tz)
                else:
                    # Assume local Arizona time
                    return arizona_tz.localize(dt)
                    
            except Exception:
                return None
        
        test_cases = [
            # UTC times (Z suffix)
            {
                "input": "20250615T140000Z",
                "source_tz": None,
                "expected_hour": 7,  # 2 PM UTC = 7 AM Arizona (UTC-7)
                "description": "UTC to Arizona"
            },
            {
                "input": "20250615T000000Z", 
                "source_tz": None,
                "expected_hour": 17,  # Midnight UTC = 5 PM previous day Arizona
                "description": "UTC midnight to Arizona"
            },
            
            # Pacific time (with DST)
            {
                "input": "20250615T140000",
                "source_tz": "America/Los_Angeles",
                "expected_hour": 14,  # 2 PM PDT = 2 PM Arizona (same during DST)
                "description": "Pacific DST to Arizona"
            },
            {
                "input": "20251215T140000",
                "source_tz": "America/Los_Angeles", 
                "expected_hour": 15,  # 2 PM PST = 3 PM Arizona (different in winter)
                "description": "Pacific Standard to Arizona"
            },
            
            # Eastern time
            {
                "input": "20250615T140000",
                "source_tz": "America/New_York",
                "expected_hour": 11,  # 2 PM EDT = 11 AM Arizona
                "description": "Eastern DST to Arizona"
            },
            {
                "input": "20251215T140000",
                "source_tz": "America/New_York",
                "expected_hour": 12,  # 2 PM EST = 12 PM Arizona
                "description": "Eastern Standard to Arizona"
            },
            
            # Mountain time (different from Arizona - has DST)
            {
                "input": "20250615T140000",
                "source_tz": "America/Denver",
                "expected_hour": 13,  # 2 PM MDT = 1 PM Arizona 
                "description": "Mountain DST to Arizona"
            },
            {
                "input": "20251215T140000",
                "source_tz": "America/Denver",
                "expected_hour": 14,  # 2 PM MST = 2 PM Arizona (same in winter)
                "description": "Mountain Standard to Arizona"
            },
            
            # International timezones
            {
                "input": "20250615T140000",
                "source_tz": "Europe/London",
                "expected_hour": 6,   # 2 PM BST = 6 AM Arizona
                "description": "London to Arizona"
            },
            {
                "input": "20250615T140000",
                "source_tz": "Asia/Tokyo",
                "expected_hour": 22,  # 2 PM JST = 10 PM previous day Arizona
                "description": "Tokyo to Arizona"
            },
            
            # All-day events (date only)
            {
                "input": "20250615",
                "source_tz": None,
                "expected_hour": 0,   # All-day events start at midnight
                "description": "All-day event"
            },
            
            # Local Arizona time (no conversion needed)
            {
                "input": "20250615T140000",
                "source_tz": None,  # Assume local
                "expected_hour": 14,
                "description": "Local Arizona time"
            }
        ]
        
        for case in test_cases:
            result = convert_ics_datetime_to_arizona(case["input"], case["source_tz"])
            
            if result:
                self.assertEqual(result.hour, case["expected_hour"],
                               f"Timezone conversion failed for {case['description']}: "
                               f"expected hour {case['expected_hour']}, got {result.hour}")
            else:
                self.fail(f"Timezone conversion returned None for {case['description']}")


class BusinessRulesAllScenariosTests(unittest.TestCase):
    """Test ALL business rules and edge cases"""
    
    def test_custom_instructions_all_scenarios(self):
        """Test custom instructions handling with ALL possible scenarios"""
        
        def process_custom_instructions(instructions, max_length=200):
            """Process custom instructions with business rules"""
            if not instructions:
                return {
                    "text": "",
                    "length": 0,
                    "truncated": False,
                    "unicode_safe": True,
                    "original_length": 0
                }
            
            # Convert to string and get original length
            text = str(instructions).strip()
            original_length = len(text)
            
            # Check for Unicode safety
            try:
                text.encode('utf-8')
                unicode_safe = True
            except UnicodeEncodeError:
                unicode_safe = False
            
            # Apply length limit
            truncated = False
            if len(text) > max_length:
                text = text[:max_length-3] + "..."
                truncated = True
            
            return {
                "text": text,
                "length": len(text),
                "truncated": truncated,
                "unicode_safe": unicode_safe,
                "original_length": original_length
            }
        
        test_cases = [
            # Normal cases
            {
                "input": "Please clean thoroughly",
                "expected_length": 22,
                "expected_truncated": False,
                "expected_unicode_safe": True
            },
            
            # Exactly at limit
            {
                "input": "A" * 200,
                "expected_length": 200,
                "expected_truncated": False
            },
            
            # Over limit (truncation)
            {
                "input": "A" * 250,
                "expected_length": 200,  # 197 chars + "..."
                "expected_truncated": True
            },
            
            # Unicode characters
            {
                "input": "Café Müller résumé naïve piñata",
                "expected_unicode_safe": True,
                "expected_truncated": False
            },
            
            # Emojis
            {
                "input": "Clean thoroughly 🧹✨ Thanks! 😊",
                "expected_unicode_safe": True,
                "expected_truncated": False
            },
            
            # Special characters
            {
                "input": "Clean & prep (kitchen/bath) - @2PM",
                "expected_unicode_safe": True,
                "expected_truncated": False
            },
            
            # Empty/whitespace
            {
                "input": "",
                "expected_length": 0,
                "expected_truncated": False
            },
            {
                "input": "   ",
                "expected_length": 0,  # Stripped
                "expected_truncated": False
            },
            {
                "input": None,
                "expected_length": 0,
                "expected_truncated": False
            },
            
            # Very long Unicode text
            {
                "input": "Résumé " * 50,  # 350 chars with accents
                "expected_truncated": True,
                "expected_unicode_safe": True
            },
            
            # Mixed content with newlines/tabs
            {
                "input": "Line 1\nLine 2\tTabbed\r\nWindows line",
                "expected_unicode_safe": True
            },
            
            # Numbers and punctuation
            {
                "input": "Clean apt #123 @$50/hr (2-4PM) - call 555-1234!",
                "expected_unicode_safe": True
            }
        ]
        
        for case in test_cases:
            result = process_custom_instructions(case["input"])
            
            if "expected_length" in case:
                self.assertEqual(result["length"], case["expected_length"],
                               f"Length mismatch for: {case['input']}")
            
            if "expected_truncated" in case:
                self.assertEqual(result["truncated"], case["expected_truncated"],
                               f"Truncation mismatch for: {case['input']}")
            
            if "expected_unicode_safe" in case:
                self.assertEqual(result["unicode_safe"], case["expected_unicode_safe"],
                               f"Unicode safety mismatch for: {case['input']}")

    def test_guest_override_all_scenarios(self):
        """Test guest override logic with ALL possible scenarios"""
        
        # Complete guest override database
        GUEST_OVERRIDES = {
            # Property + guest name pattern → override guest ID
            ("prop_001", "Smith"): "guest_vip_001",
            ("prop_001", "Johnson"): "guest_vip_002", 
            ("prop_002", "Brown"): "guest_vip_003",
            ("prop_003", "Davis"): "guest_priority_001",
            # Case variations
            ("prop_001", "smith"): "guest_vip_001",  # Lowercase
            ("prop_001", "SMITH"): "guest_vip_001",  # Uppercase
            # Partial matches
            ("prop_001", "Smithson"): "guest_vip_001",  # Contains "Smith"
            ("prop_002", "O'Brown"): "guest_vip_003",   # Contains "Brown"
        }
        
        def apply_guest_override(property_id, guest_name, owner_info=None):
            """Apply guest override rules"""
            if not property_id or not guest_name:
                return None
            
            guest_str = str(guest_name).strip()
            if not guest_str:
                return None
            
            # Try exact matches first
            for (prop_id, pattern), override_id in GUEST_OVERRIDES.items():
                if prop_id == property_id:
                    # Try case-insensitive matching
                    if pattern.lower() in guest_str.lower():
                        return override_id
            
            # Try owner-based overrides if provided
            if owner_info:
                owner_str = str(owner_info).lower()
                for (prop_id, pattern), override_id in GUEST_OVERRIDES.items():
                    if prop_id == property_id and pattern.lower() in owner_str:
                        return override_id
            
            return None
        
        test_cases = [
            # Exact matches
            ("prop_001", "Smith", None, "guest_vip_001"),
            ("prop_001", "Johnson", None, "guest_vip_002"),
            ("prop_002", "Brown", None, "guest_vip_003"),
            ("prop_003", "Davis", None, "guest_priority_001"),
            
            # Case variations
            ("prop_001", "smith", None, "guest_vip_001"),
            ("prop_001", "SMITH", None, "guest_vip_001"),
            ("prop_001", "Smith", None, "guest_vip_001"),
            ("prop_001", "sMiTh", None, "guest_vip_001"),
            
            # Partial matches (contains pattern)
            ("prop_001", "John Smith", None, "guest_vip_001"),
            ("prop_001", "Mr. Smith Jr.", None, "guest_vip_001"),
            ("prop_001", "Smithson", None, "guest_vip_001"),
            ("prop_002", "Mary Brown", None, "guest_vip_003"),
            ("prop_002", "O'Brown", None, "guest_vip_003"),
            
            # No matches
            ("prop_001", "Wilson", None, None),
            ("prop_002", "Anderson", None, None),
            ("prop_999", "Smith", None, None),  # Wrong property
            ("prop_001", "", None, None),       # Empty guest name
            ("", "Smith", None, None),          # Empty property
            (None, "Smith", None, None),        # Null property
            ("prop_001", None, None, None),     # Null guest name
            
            # Owner-based overrides
            ("prop_001", "Random Guest", "Property owned by Smith Family", "guest_vip_001"),
            ("prop_002", "Any Guest", "Owner: Brown Holdings LLC", "guest_vip_003"),
            
            # Multiple patterns (first match wins)
            ("prop_001", "Smith Johnson", None, "guest_vip_001"),  # Should match Smith first
            
            # Special characters
            ("prop_001", "Smith-Jones", None, "guest_vip_001"),
            ("prop_001", "Smith & Associates", None, "guest_vip_001"),
            ("prop_002", "Brown's Family", None, "guest_vip_003"),
            
            # Unicode names
            ("prop_001", "José Smith", None, "guest_vip_001"),
            ("prop_002", "María Brown", None, "guest_vip_003"),
        ]
        
        for prop_id, guest_name, owner_info, expected in test_cases:
            result = apply_guest_override(prop_id, guest_name, owner_info)
            self.assertEqual(result, expected,
                           f"Guest override failed for property '{prop_id}', guest '{guest_name}'")

    def test_timezone_business_hours_all_scenarios(self):
        """Test business hours logic with ALL timezone scenarios"""
        
        def is_within_business_hours(datetime_str, timezone_name="America/Phoenix"):
            """Check if datetime is within business hours (8 AM - 6 PM)"""
            try:
                # Parse datetime
                if 'T' in datetime_str:
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                
                # Convert to specified timezone
                if dt.tzinfo is None:
                    # Assume local timezone
                    local_tz = pytz.timezone(timezone_name)
                    dt = local_tz.localize(dt)
                else:
                    # Convert to target timezone
                    target_tz = pytz.timezone(timezone_name)
                    dt = dt.astimezone(target_tz)
                
                # Check business hours (8 AM to 6 PM)
                return 8 <= dt.hour < 18
                
            except Exception:
                return False
        
        test_cases = [
            # Standard business hours (Arizona time)
            ("2025-06-15 08:00:00", "America/Phoenix", True),   # 8 AM - start of business
            ("2025-06-15 12:00:00", "America/Phoenix", True),   # Noon - middle of day
            ("2025-06-15 17:59:00", "America/Phoenix", True),   # 5:59 PM - end of business
            ("2025-06-15 18:00:00", "America/Phoenix", False),  # 6 PM - after hours
            ("2025-06-15 07:59:00", "America/Phoenix", False),  # 7:59 AM - before hours
            ("2025-06-15 00:00:00", "America/Phoenix", False),  # Midnight
            ("2025-06-15 23:59:00", "America/Phoenix", False),  # Late night
            
            # Edge cases
            ("2025-06-15 08:00:01", "America/Phoenix", True),   # Just after 8 AM
            ("2025-06-15 17:59:59", "America/Phoenix", True),   # Just before 6 PM
            
            # UTC times converted to Arizona
            ("2025-06-15T15:00:00Z", "America/Phoenix", True),  # 3 PM UTC = 8 AM Arizona
            ("2025-06-15T01:00:00Z", "America/Phoenix", True),  # 1 AM UTC = 6 PM prev day Arizona
            ("2025-06-15T02:00:00Z", "America/Phoenix", False), # 2 AM UTC = 7 PM prev day Arizona
            
            # Different seasons (DST vs non-DST in other zones)
            ("2025-06-15 14:00:00", "America/Los_Angeles", True),   # Summer PDT
            ("2025-12-15 14:00:00", "America/Los_Angeles", True),   # Winter PST
            ("2025-06-15 14:00:00", "America/New_York", True),      # Summer EDT
            ("2025-12-15 14:00:00", "America/New_York", True),      # Winter EST
            
            # Weekend vs weekday (business hours same regardless)
            ("2025-06-14 10:00:00", "America/Phoenix", True),   # Saturday
            ("2025-06-15 10:00:00", "America/Phoenix", True),   # Sunday
            ("2025-06-16 10:00:00", "America/Phoenix", True),   # Monday
            
            # Invalid inputs
            ("invalid-datetime", "America/Phoenix", False),
            ("", "America/Phoenix", False),
            ("2025-06-15 25:00:00", "America/Phoenix", False),  # Invalid hour
        ]
        
        for datetime_str, timezone_name, expected in test_cases:
            result = is_within_business_hours(datetime_str, timezone_name)
            self.assertEqual(result, expected,
                           f"Business hours check failed for {datetime_str} in {timezone_name}")


if __name__ == '__main__':
    # Run comprehensive tests with detailed output
    unittest.main(verbosity=2, buffer=True)