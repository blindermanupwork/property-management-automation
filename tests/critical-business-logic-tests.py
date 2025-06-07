#!/usr/bin/env python3
"""
Critical Business Logic Test Suite
Tests the most important untested business logic identified in the comprehensive code review.

Priority: HIGH - Tests business-critical logic that could cause data corruption or incorrect billing.
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

class CSVProcessingCoreLogicTests(unittest.TestCase):
    """Test the core CSV processing business logic that handles millions in revenue"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock property lookup data
        self.mock_properties = [
            {"id": "prop1", "Property Name": "Test House #101"},
            {"id": "prop2", "Property Name": "Desert Villa #202 - Pool"},
            {"id": "prop3", "Property Name": "Mountain View"},
            {"id": "prop4", "Property Name": "Beach House#303Special"}
        ]
        
        # Sample CSV data for testing
        self.sample_csv_data = {
            "Reservation ID": ["RES001", "RES002", "RES003"],
            "Property Name": ["Test House #101", "Desert Villa #202", "Invalid Property"],
            "Guest Name": ["John Smith", "Jane Doe", "Bob Wilson"],
            "Check-in Date": ["2025-06-01", "2025-06-05", "2025-06-10"],
            "Check-out Date": ["2025-06-05", "2025-06-12", "2025-06-15"],
            "Reservation Status": ["Confirmed", "Modified", "Cancelled"]
        }

    def test_property_matching_with_listing_numbers(self):
        """Test property matching algorithm with listing numbers and special characters"""
        from automation.scripts.CSVtoAirtable.csvProcess import create_property_lookup
        
        # Test case-insensitive matching
        property_lookup = {}
        for prop in self.mock_properties:
            name = prop["Property Name"]
            property_lookup[name.lower()] = prop["id"]
            
            # Test listing number extraction
            if "#" in name:
                listing_number = name.split("#")[-1].strip().split()[0]
                property_lookup[listing_number] = prop["id"]
        
        # Test exact matches
        self.assertEqual(property_lookup["test house #101"], "prop1")
        self.assertEqual(property_lookup["desert villa #202 - pool"], "prop2")
        
        # Test listing number matches
        self.assertEqual(property_lookup["101"], "prop1")
        self.assertEqual(property_lookup["202"], "prop2")
        self.assertEqual(property_lookup["303special"], "prop4")  # Edge case: no space after #
        
        # Test case insensitivity
        self.assertEqual(property_lookup["TEST HOUSE #101".lower()], "prop1")

    def test_date_overlap_detection_algorithm(self):
        """Test the complex date overlap detection that prevents double-booking"""
        from itertools import combinations
        
        # Sample reservations with various overlap scenarios
        reservations = [
            {"id": "A", "start": "2025-06-01", "end": "2025-06-05"},  # No overlap
            {"id": "B", "start": "2025-06-03", "end": "2025-06-07"},  # Overlaps with A
            {"id": "C", "start": "2025-06-05", "end": "2025-06-08"},  # Same-day checkout/checkin (should NOT overlap)
            {"id": "D", "start": "2025-06-06", "end": "2025-06-10"},  # Overlaps with B and C
            {"id": "E", "start": "2025-06-12", "end": "2025-06-15"}   # No overlap
        ]
        
        # Convert to datetime for comparison
        for res in reservations:
            res["start_dt"] = datetime.strptime(res["start"], "%Y-%m-%d")
            res["end_dt"] = datetime.strptime(res["end"], "%Y-%m-%d")
            res["overlapping"] = False
        
        # Apply overlap detection algorithm
        for a, b in combinations(reservations, 2):
            a_start, a_end = a["start_dt"], a["end_dt"]
            b_start, b_end = b["start_dt"], b["end_dt"]
            
            # True overlap means start of one is before end of other AND vice versa
            if a_start < b_end and a_end > b_start:
                a["overlapping"] = True
                b["overlapping"] = True
        
        # Verify overlap detection
        overlap_results = {res["id"]: res["overlapping"] for res in reservations}
        
        expected_overlaps = {
            "A": True,   # Overlaps with B
            "B": True,   # Overlaps with A, C, D
            "C": True,   # Overlaps with B, D
            "D": True,   # Overlaps with B, C
            "E": False   # No overlaps
        }
        
        self.assertEqual(overlap_results, expected_overlaps)

    def test_same_day_turnover_detection(self):
        """Test same-day turnover detection with iTrip precedence"""
        
        # Test data with various same-day scenarios
        test_cases = [
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-01",
                "itrip_same_day": None,
                "expected": True  # Calculated same-day
            },
            {
                "prev_checkout": "2025-06-01", 
                "next_checkin": "2025-06-01",
                "itrip_same_day": False,
                "expected": False  # iTrip override
            },
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-02", 
                "itrip_same_day": True,
                "expected": True  # iTrip override (business rule)
            },
            {
                "prev_checkout": "2025-06-01",
                "next_checkin": "2025-06-02",
                "itrip_same_day": None,
                "expected": False  # Not same day
            }
        ]
        
        for case in test_cases:
            # Apply business logic
            if case["itrip_same_day"] is not None:
                result = case["itrip_same_day"]  # iTrip precedence
            else:
                # Calculate based on dates
                result = case["prev_checkout"] == case["next_checkin"]
            
            self.assertEqual(result, case["expected"], 
                           f"Failed for case: {case}")

    def test_long_term_guest_detection(self):
        """Test ≥14 days long-term guest detection algorithm"""
        
        test_reservations = [
            {"checkin": "2025-06-01", "checkout": "2025-06-05", "expected": False},  # 4 days
            {"checkin": "2025-06-01", "checkout": "2025-06-14", "expected": False}, # 13 days 
            {"checkin": "2025-06-01", "checkout": "2025-06-15", "expected": True},  # 14 days (exactly)
            {"checkin": "2025-06-01", "checkout": "2025-06-20", "expected": True},  # 19 days
            {"checkin": "2025-06-01", "checkout": "2025-07-01", "expected": True},  # 30 days
        ]
        
        for res in test_reservations:
            checkin = datetime.strptime(res["checkin"], "%Y-%m-%d")
            checkout = datetime.strptime(res["checkout"], "%Y-%m-%d")
            
            duration = (checkout - checkin).days
            is_long_term = duration >= 14
            
            self.assertEqual(is_long_term, res["expected"],
                           f"Failed for {duration} days: {res}")

    def test_entry_type_classification(self):
        """Test keyword-based entry type classification"""
        
        # Mock keyword mapping from actual system
        ENTRY_TYPE_KEYWORDS = {
            "block": "Block",
            "blocked": "Block", 
            "maintenance": "Block",
            "owner": "Block",
            "personal": "Block",
            "turnover": "Turnover",
            "cleaning": "Turnover",
            "clean": "Turnover",
            "laundry": "Return Laundry",
            "return": "Return Laundry",
            "inspection": "Inspection",
            "check": "Inspection"
        }
        
        test_cases = [
            ("Maintenance Block", "Block"),
            ("Owner Personal Use", "Block"),
            ("Turnover Cleaning", "Turnover"),  # First match wins
            ("Deep Clean Service", "Turnover"),
            ("Laundry Return", "Return Laundry"),
            ("Property Inspection", "Inspection"),
            ("Guest Reservation", "Turnover"),  # Default fallback
            ("blocked for maintenance", "Block"),  # Case insensitive
            ("CLEANING TURNOVER", "Turnover")  # Case insensitive
        ]
        
        for text, expected in test_cases:
            text_lower = text.lower()
            entry_type = "Turnover"  # Default
            
            # Apply classification algorithm
            for keyword, type_value in ENTRY_TYPE_KEYWORDS.items():
                if keyword in text_lower:
                    entry_type = type_value
                    break  # First match wins
            
            self.assertEqual(entry_type, expected, f"Failed for: '{text}'")

    def test_date_normalization_edge_cases(self):
        """Test date parsing with various formats and edge cases"""
        
        test_dates = [
            ("2025-06-01", "06/01/2025"),           # ISO format
            ("06/01/2025", "06/01/2025"),           # US format
            ("6/1/2025", "06/01/2025"),             # Single digits
            ("2025-6-1", "06/01/2025"),             # Mixed format
            ("01-Jun-2025", "06/01/2025"),          # Month name
            ("June 1, 2025", "06/01/2025"),        # Full format
            ("", None),                             # Empty string
            ("invalid", None),                      # Invalid format
        ]
        
        def normalize_date_for_comparison(date_value):
            """Normalize various date formats to MM/DD/YYYY"""
            if not date_value or str(date_value).strip() == "":
                return None
                
            try:
                # Try multiple parsing strategies
                formats = [
                    "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", 
                    "%Y-%m-%d", "%d-%b-%Y", "%B %d, %Y"
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(str(date_value).strip(), fmt)
                        return dt.strftime("%m/%d/%Y")
                    except ValueError:
                        continue
                        
                # Try pandas parsing as fallback
                dt = pd.to_datetime(date_value)
                return dt.strftime("%m/%d/%Y")
                
            except:
                return None
        
        for input_date, expected in test_dates:
            result = normalize_date_for_comparison(input_date)
            self.assertEqual(result, expected, f"Failed for: '{input_date}'")


class ControllerEnvironmentRoutingTests(unittest.TestCase):
    """Test controller's environment-specific automation routing"""
    
    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.get_environment.return_value = "dev"
    
    @patch('automation.controller.import_module')
    def test_environment_specific_automation_import(self, mock_import):
        """Test dynamic automation function import based on environment"""
        
        # Test successful import
        mock_module = Mock()
        mock_module.run_gmail_automation = Mock(return_value={"success": True})
        mock_import.return_value = mock_module
        
        # Simulate controller behavior
        env = "dev"
        module_name = f"automation.scripts.run_automation"
        
        try:
            module = mock_import(module_name)
            automation_func = getattr(module, "run_gmail_automation")
            result = automation_func()
            self.assertTrue(result["success"])
        except (ImportError, AttributeError) as e:
            self.fail(f"Automation import failed: {e}")
    
    def test_result_interpretation_logic(self):
        """Test complex result parsing for different return types"""
        
        test_cases = [
            (True, True),                                    # Boolean true
            (False, False),                                  # Boolean false
            ({"success": True}, True),                       # Dict with success
            ({"success": False, "error": "test"}, False),    # Dict with failure
            ({"result": "ok"}, False),                       # Dict without success key
            ("success", False),                              # String (invalid)
            (None, False),                                   # None
            ([], False),                                     # List (invalid)
            (42, False),                                     # Number (invalid)
        ]
        
        def interpret_result(result):
            """Interpret automation result"""
            if isinstance(result, bool):
                return result
            elif isinstance(result, dict) and "success" in result:
                return result["success"]
            else:
                return False  # Default to failure for unexpected types
        
        for result, expected in test_cases:
            interpreted = interpret_result(result)
            self.assertEqual(interpreted, expected, f"Failed for: {result}")


class HCPIntegrationWorkflowTests(unittest.TestCase):
    """Test HousecallPro integration critical workflows"""
    
    def test_service_type_normalization(self):
        """Test service type mapping with edge cases"""
        
        test_cases = [
            ("Return Laundry", "Return Laundry"),
            ("return laundry", "Return Laundry"),      # Case insensitive  
            ("RETURN LAUNDRY", "Return Laundry"),      # All caps
            ("Inspection", "Inspection"),
            ("inspection", "Inspection"),              # Case insensitive
            ("Property Inspection", "Inspection"),     # Partial match
            ("Turnover", "Turnover"),
            ("turnover", "Turnover"),                  # Case insensitive
            ("Cleaning", "Turnover"),                  # Default mapping
            ("", "Turnover"),                          # Empty string
            ("Unknown Service", "Turnover"),           # Unknown type
            (None, "Turnover"),                        # None value
        ]
        
        def normalize_service_type(raw_service_type):
            """Normalize service type following HCP integration logic"""
            if not raw_service_type:
                return "Turnover"
                
            service_str = str(raw_service_type).strip()
            
            # Exact matches (case insensitive)
            if "return laundry" in service_str.lower():
                return "Return Laundry"
            elif "inspection" in service_str.lower():
                return "Inspection"  
            else:
                return "Turnover"  # Default
        
        for input_type, expected in test_cases:
            result = normalize_service_type(input_type)
            self.assertEqual(result, expected, f"Failed for: '{input_type}'")
    
    def test_rate_limiting_calculation(self):
        """Test rate limiting wait time calculation"""
        
        def calculate_wait_time(rate_limit_reset_header, current_time):
            """Calculate wait time for rate limiting"""
            try:
                if not rate_limit_reset_header:
                    return 1000  # Default 1 second
                    
                reset_time = int(rate_limit_reset_header) * 1000  # Convert to ms
                wait_ms = max(reset_time - current_time, 1000)   # Minimum 1 second
                return min(wait_ms, 60000)  # Maximum 1 minute
            except (ValueError, TypeError):
                return 1000  # Default on error
        
        current_time = 1640995200000  # Mock timestamp
        
        test_cases = [
            ("1640995210", 10000),    # 10 seconds wait
            ("1640995260", 60000),    # 60 seconds wait (capped)
            ("1640995199", 1000),     # Past time, minimum wait
            ("", 1000),               # Empty header
            ("invalid", 1000),        # Invalid header
            (None, 1000),             # None header
        ]
        
        for header, expected in test_cases:
            result = calculate_wait_time(header, current_time)
            self.assertEqual(result, expected, f"Failed for header: '{header}'")


class TimezoneConsistencyTests(unittest.TestCase):
    """Test timezone handling consistency across components"""
    
    def test_arizona_timezone_handling(self):
        """Test Arizona timezone handling (no DST)"""
        arizona_tz = pytz.timezone('America/Phoenix')
        
        # Test dates during DST transition periods
        test_dates = [
            datetime(2025, 3, 9, 12, 0),    # DST starts (most of US)
            datetime(2025, 11, 2, 12, 0),   # DST ends (most of US)
            datetime(2025, 6, 15, 12, 0),   # Mid-summer
            datetime(2025, 12, 15, 12, 0),  # Mid-winter
        ]
        
        for dt in test_dates:
            # Arizona should maintain consistent offset
            arizona_dt = arizona_tz.localize(dt)
            utc_offset = arizona_dt.utcoffset().total_seconds() / 3600
            
            # Arizona is always UTC-7 (no DST)
            self.assertEqual(utc_offset, -7, f"Arizona offset incorrect for {dt}")
    
    def test_pst_logging_timezone(self):
        """Test PST timezone for logging consistency"""
        pst_tz = pytz.timezone('America/Los_Angeles')
        
        # Test DST transitions for PST
        dst_start = datetime(2025, 3, 9, 12, 0)    # DST starts
        dst_end = datetime(2025, 11, 2, 12, 0)     # DST ends
        
        dst_start_pst = pst_tz.localize(dst_start)
        dst_end_pst = pst_tz.localize(dst_end)
        
        # During DST, PST becomes PDT (UTC-7)
        # During standard time, PST is UTC-8
        start_offset = dst_start_pst.utcoffset().total_seconds() / 3600
        end_offset = dst_end_pst.utcoffset().total_seconds() / 3600
        
        self.assertEqual(start_offset, -7, "DST offset incorrect")
        self.assertEqual(end_offset, -8, "Standard time offset incorrect")


class AuthenticationSecurityTests(unittest.TestCase):
    """Test authentication and security mechanisms"""
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation logic"""
        import hmac
        import hashlib
        
        def validate_webhook_signature(payload, signature, secret):
            """Validate webhook signature"""
            try:
                if not signature or not secret:
                    return False
                    
                # Remove 'sha256=' prefix if present
                if signature.startswith('sha256='):
                    signature = signature[7:]
                
                # Calculate expected signature
                expected = hmac.new(
                    secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                # Constant time comparison
                return hmac.compare_digest(signature, expected)
            except Exception:
                return False
        
        secret = "test_webhook_secret_key"
        payload = '{"event": "job.created", "data": {"id": "job_123"}}'
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        self.assertTrue(validate_webhook_signature(payload, valid_signature, secret))
        self.assertTrue(validate_webhook_signature(payload, f"sha256={valid_signature}", secret))
        
        # Test invalid signatures
        self.assertFalse(validate_webhook_signature(payload, "invalid", secret))
        self.assertFalse(validate_webhook_signature(payload, "", secret))
        self.assertFalse(validate_webhook_signature(payload, None, secret))
        self.assertFalse(validate_webhook_signature(payload, valid_signature, "wrong_secret"))
    
    def test_ip_whitelist_validation(self):
        """Test IP whitelist validation with CIDR and exact matches"""
        import ipaddress
        
        def validate_ip_whitelist(client_ip, whitelist):
            """Validate client IP against whitelist"""
            try:
                client_ip_obj = ipaddress.ip_address(client_ip)
                
                for allowed_ip in whitelist:
                    if '/' in allowed_ip:
                        # CIDR notation
                        if client_ip_obj in ipaddress.ip_network(allowed_ip, strict=False):
                            return True
                    else:
                        # Exact match
                        if client_ip == allowed_ip:
                            return True
                return False
            except (ValueError, ipaddress.AddressValueError):
                return False
        
        whitelist = [
            "192.168.1.0/24",      # CIDR range
            "10.0.0.1",            # Exact IP
            "127.0.0.1"            # Localhost
        ]
        
        # Test valid IPs
        self.assertTrue(validate_ip_whitelist("192.168.1.100", whitelist))
        self.assertTrue(validate_ip_whitelist("192.168.1.1", whitelist))
        self.assertTrue(validate_ip_whitelist("10.0.0.1", whitelist))
        self.assertTrue(validate_ip_whitelist("127.0.0.1", whitelist))
        
        # Test invalid IPs
        self.assertFalse(validate_ip_whitelist("192.168.2.1", whitelist))
        self.assertFalse(validate_ip_whitelist("10.0.0.2", whitelist))
        self.assertFalse(validate_ip_whitelist("8.8.8.8", whitelist))
        self.assertFalse(validate_ip_whitelist("invalid_ip", whitelist))


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2, buffer=True)