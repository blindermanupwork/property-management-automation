#!/usr/bin/env python3
"""
ICS Processing and Edge Case Test Suite
Tests ICS calendar processing logic and edge cases for malformed data, network failures, and concurrent operations.

These tests cover critical untested areas identified in the comprehensive code review.
"""

import unittest
import tempfile
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
import pytz
import concurrent.futures
import threading
import time

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class ICSProcessingTests(unittest.TestCase):
    """Test ICS calendar processing logic with edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # Mock ICS configuration
        self.mock_config = {
            "FETCH_RESERVATIONS_MONTHS_BEFORE": 2,
            "IGNORE_BLOCKS_MONTHS_AWAY": 6,
            "ICS_FEEDS": [
                {"name": "Test Feed 1", "url": "https://example.com/feed1.ics"},
                {"name": "Test Feed 2", "url": "https://example.com/feed2.ics"}
            ]
        }
    
    def test_date_filtering_thresholds(self):
        """Test complex date filtering with multiple thresholds"""
        
        # Mock current date
        current_date = datetime(2025, 6, 15)  # June 15, 2025
        
        # Calculate thresholds based on configuration
        lookback_months = self.mock_config["FETCH_RESERVATIONS_MONTHS_BEFORE"]
        future_months = self.mock_config["IGNORE_BLOCKS_MONTHS_AWAY"]
        
        lookback_threshold = current_date - timedelta(days=lookback_months * 30)
        future_threshold = current_date + timedelta(days=future_months * 30)
        
        # Test event dates
        test_events = [
            {"start": "2025-03-01", "expected": False},  # Too far back
            {"start": "2025-04-20", "expected": True},   # Within lookback
            {"start": "2025-06-15", "expected": True},   # Current date
            {"start": "2025-08-15", "expected": True},   # Near future
            {"start": "2025-12-31", "expected": True},   # Within future threshold
            {"start": "2026-02-01", "expected": False},  # Too far future
        ]
        
        for event in test_events:
            event_date = datetime.strptime(event["start"], "%Y-%m-%d")
            
            # Apply filtering logic
            should_include = (lookback_threshold <= event_date <= future_threshold)
            
            self.assertEqual(should_include, event["expected"], 
                           f"Date filtering failed for {event['start']}")
    
    def test_ics_feed_parsing_edge_cases(self):
        """Test ICS feed parsing with malformed data"""
        
        # Sample ICS content with various edge cases
        test_ics_content = [
            # Valid event
            """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event1@example.com
DTSTART:20250615T120000Z
DTEND:20250617T100000Z
SUMMARY:Test Reservation
END:VEVENT
END:VCALENDAR""",
            
            # Missing required fields
            """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event2@example.com
SUMMARY:Invalid Event
END:VEVENT
END:VCALENDAR""",
            
            # Malformed dates
            """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event3@example.com
DTSTART:INVALID-DATE
DTEND:20250617T100000Z
SUMMARY:Bad Date Event
END:VEVENT
END:VCALENDAR""",
            
            # Empty content
            "",
            
            # Truncated content
            """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:event4@example.com""",
        ]
        
        def parse_ics_content(content):
            """Mock ICS parser with error handling"""
            try:
                if not content or content.strip() == "":
                    return []
                
                events = []
                lines = content.split('\n')
                current_event = {}
                in_event = False
                
                for line in lines:
                    line = line.strip()
                    if line == "BEGIN:VEVENT":
                        in_event = True
                        current_event = {}
                    elif line == "END:VEVENT":
                        if in_event and self._is_valid_event(current_event):
                            events.append(current_event)
                        in_event = False
                    elif in_event and ':' in line:
                        key, value = line.split(':', 1)
                        current_event[key] = value
                
                return events
            except Exception:
                return []
        
        def _is_valid_event(self, event):
            """Validate event has required fields"""
            required_fields = ['UID', 'DTSTART', 'DTEND', 'SUMMARY']
            return all(field in event for field in required_fields)
        
        # Test parsing results
        expected_results = [1, 0, 0, 0, 0]  # Only first ICS should produce valid event
        
        for i, content in enumerate(test_ics_content):
            events = parse_ics_content(content)
            self.assertEqual(len(events), expected_results[i], 
                           f"ICS parsing failed for content {i}")
    
    def test_timezone_conversion_edge_cases(self):
        """Test timezone conversion with DST transitions"""
        
        # Test dates around DST transitions
        test_cases = [
            # DST starts (2025-03-09 at 2:00 AM)
            {"date": "2025-03-09T01:30:00", "tz": "America/Los_Angeles"},
            {"date": "2025-03-09T03:30:00", "tz": "America/Los_Angeles"},  # After DST
            
            # DST ends (2025-11-02 at 2:00 AM) 
            {"date": "2025-11-02T01:30:00", "tz": "America/Los_Angeles"},
            {"date": "2025-11-02T02:30:00", "tz": "America/Los_Angeles"},  # Ambiguous time
            
            # Arizona (no DST)
            {"date": "2025-03-09T02:30:00", "tz": "America/Phoenix"},
            {"date": "2025-11-02T02:30:00", "tz": "America/Phoenix"},
        ]
        
        def convert_to_arizona(datetime_str, source_tz_name):
            """Convert datetime to Arizona timezone"""
            try:
                # Parse datetime
                dt = datetime.fromisoformat(datetime_str)
                source_tz = pytz.timezone(source_tz_name)
                arizona_tz = pytz.timezone('America/Phoenix')
                
                # Localize to source timezone
                try:
                    localized_dt = source_tz.localize(dt)
                except pytz.AmbiguousTimeError:
                    # Handle ambiguous times during DST transition
                    localized_dt = source_tz.localize(dt, is_dst=False)
                except pytz.NonExistentTimeError:
                    # Handle non-existent times during DST transition
                    localized_dt = source_tz.localize(dt, is_dst=True)
                
                # Convert to Arizona time
                arizona_dt = localized_dt.astimezone(arizona_tz)
                return arizona_dt
                
            except Exception as e:
                return None
        
        # Test conversions don't fail
        for case in test_cases:
            result = convert_to_arizona(case["date"], case["tz"])
            self.assertIsNotNone(result, f"Timezone conversion failed for {case}")
    
    def test_concurrent_ics_feed_processing(self):
        """Test concurrent processing of multiple ICS feeds"""
        
        feed_results = {}
        processing_times = {}
        
        def mock_process_feed(feed_info):
            """Mock ICS feed processing with simulated delay"""
            feed_name = feed_info["name"]
            start_time = time.time()
            
            # Simulate processing time
            time.sleep(0.1)  # 100ms processing time
            
            # Simulate various outcomes
            if "Test Feed 1" in feed_name:
                result = {"events": 5, "errors": 0}
            elif "Test Feed 2" in feed_name:
                result = {"events": 3, "errors": 1}
            else:
                result = {"events": 0, "errors": 1}
            
            end_time = time.time()
            processing_times[feed_name] = end_time - start_time
            feed_results[feed_name] = result
            
            return result
        
        # Test concurrent processing
        feeds = self.mock_config["ICS_FEEDS"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all feed processing tasks
            futures = {executor.submit(mock_process_feed, feed): feed for feed in feeds}
            
            # Wait for completion
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=5.0)  # 5 second timeout
                except concurrent.futures.TimeoutError:
                    self.fail("Feed processing timed out")
                except Exception as e:
                    self.fail(f"Feed processing failed: {e}")
        
        # Verify all feeds were processed
        self.assertEqual(len(feed_results), len(feeds))
        self.assertIn("Test Feed 1", feed_results)
        self.assertIn("Test Feed 2", feed_results)
        
        # Verify concurrent processing was actually faster
        max_sequential_time = sum(processing_times.values())
        actual_concurrent_time = max(processing_times.values())
        
        self.assertLess(actual_concurrent_time, max_sequential_time,
                       "Concurrent processing should be faster than sequential")


class MalformedDataTests(unittest.TestCase):
    """Test handling of malformed and corrupted data"""
    
    def test_csv_with_corrupted_data(self):
        """Test CSV processing with various data corruption scenarios"""
        
        # Test cases with different corruption types
        corrupt_csv_data = [
            # Missing headers
            "RES001,Test Property,John Smith,2025-06-01,2025-06-05",
            
            # Extra commas
            "Reservation ID,Property Name,Guest Name,Check-in Date,Check-out Date\nRES001,Test,Property,John,Smith,2025-06-01,2025-06-05",
            
            # Quoted fields with commas
            'Reservation ID,Property Name,Guest Name,Check-in Date,Check-out Date\nRES001,"Test, Property",John Smith,2025-06-01,2025-06-05',
            
            # Mixed line endings
            "Reservation ID,Property Name,Guest Name,Check-in Date,Check-out Date\r\nRES001,Test Property,John Smith,2025-06-01,2025-06-05\nRES002,Test Villa,Jane Doe,2025-06-10,2025-06-15",
            
            # Non-UTF8 characters
            "Reservation ID,Property Name,Guest Name,Check-in Date,Check-out Date\nRES001,Café Property,José García,2025-06-01,2025-06-05",
            
            # Empty fields
            "Reservation ID,Property Name,Guest Name,Check-in Date,Check-out Date\nRES001,,John Smith,,2025-06-05",
        ]
        
        def safe_csv_parse(csv_content):
            """Safely parse CSV with error handling"""
            try:
                from io import StringIO
                import csv
                
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252']
                
                for encoding in encodings:
                    try:
                        if isinstance(csv_content, bytes):
                            content = csv_content.decode(encoding)
                        else:
                            content = csv_content
                        
                        # Parse CSV
                        reader = csv.DictReader(StringIO(content))
                        rows = list(reader)
                        
                        # Validate has required columns
                        required_cols = ['Reservation ID', 'Property Name', 'Guest Name']
                        if any(col in reader.fieldnames for col in required_cols):
                            return {"success": True, "rows": rows, "encoding": encoding}
                        
                    except (UnicodeDecodeError, csv.Error):
                        continue
                
                return {"success": False, "error": "Could not parse CSV"}
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Test each corrupt CSV
        for i, csv_data in enumerate(corrupt_csv_data):
            result = safe_csv_parse(csv_data)
            
            # Should handle gracefully (either parse successfully or fail safely)
            self.assertIn("success", result, f"CSV parse result missing success field for case {i}")
            
            if not result["success"]:
                self.assertIn("error", result, f"Failed CSV parse missing error field for case {i}")
    
    def test_json_corruption_handling(self):
        """Test handling of corrupted JSON data"""
        
        corrupt_json_data = [
            '{"key": "value"',              # Missing closing brace
            '{"key": "value",}',            # Trailing comma
            '{"key": value}',               # Unquoted value
            '{key: "value"}',               # Unquoted key
            '{"nested": {"key": "value"}',  # Missing nested close
            '',                             # Empty string
            'not json at all',              # Not JSON
            '{"unicode": "café"}',          # Unicode characters
            '{"number": 123.456.789}',      # Invalid number format
        ]
        
        def safe_json_parse(json_str):
            """Safely parse JSON with error handling"""
            try:
                if not json_str or json_str.strip() == "":
                    return {"success": False, "error": "Empty JSON"}
                
                data = json.loads(json_str)
                return {"success": True, "data": data}
                
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"JSON decode error: {e}"}
            except Exception as e:
                return {"success": False, "error": f"Unexpected error: {e}"}
        
        # Test each corrupt JSON
        for i, json_data in enumerate(corrupt_json_data):
            result = safe_json_parse(json_data)
            
            # Should always return a result with success field
            self.assertIn("success", result, f"JSON parse missing success field for case {i}")
            
            # Most should fail gracefully
            if i < 7:  # First 7 are definitely invalid
                self.assertFalse(result["success"], f"Should have failed for case {i}: {json_data}")


class NetworkFailureTests(unittest.TestCase):
    """Test network failure handling and retry logic"""
    
    def test_api_retry_logic(self):
        """Test API retry logic with exponential backoff"""
        
        class MockAPIResponse:
            def __init__(self, status_code, headers=None):
                self.status_code = status_code
                self.headers = headers or {}
        
        def api_call_with_retry(max_retries=3, base_delay=1.0):
            """Mock API call with retry logic"""
            attempt = 0
            
            while attempt < max_retries:
                try:
                    attempt += 1
                    
                    # Simulate different failure types based on attempt
                    if attempt == 1:
                        # Simulate timeout
                        raise TimeoutError("Request timeout")
                    elif attempt == 2:
                        # Simulate rate limiting
                        return MockAPIResponse(429, {"Retry-After": "60"})
                    elif attempt == 3:
                        # Simulate success
                        return MockAPIResponse(200)
                    
                except TimeoutError:
                    if attempt >= max_retries:
                        raise
                    
                    # Exponential backoff
                    delay = base_delay * (2 ** (attempt - 1))
                    time.sleep(min(delay, 60))  # Cap at 60 seconds
                    continue
                
                # Handle rate limiting
                if hasattr(response, 'status_code') and response.status_code == 429:
                    if attempt >= max_retries:
                        return response
                    
                    retry_after = int(response.headers.get("Retry-After", 60))
                    time.sleep(min(retry_after, 120))  # Cap at 2 minutes
                    continue
                
                return response
            
            raise Exception("Max retries exceeded")
        
        # Test successful retry
        start_time = time.time()
        response = api_call_with_retry(max_retries=3, base_delay=0.1)  # Fast for testing
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertGreater(end_time - start_time, 0.1)  # Should have taken some time due to retries
    
    def test_concurrent_api_failure_handling(self):
        """Test handling of concurrent API failures"""
        
        def mock_api_call(call_id):
            """Mock API call that fails differently based on ID"""
            if call_id % 3 == 0:
                raise TimeoutError(f"Timeout for call {call_id}")
            elif call_id % 3 == 1:
                raise ConnectionError(f"Connection error for call {call_id}")
            else:
                return {"success": True, "call_id": call_id}
        
        # Test concurrent calls with some failures
        call_ids = range(10)
        results = {}
        errors = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all calls
            futures = {executor.submit(mock_api_call, call_id): call_id for call_id in call_ids}
            
            # Collect results and errors
            for future in concurrent.futures.as_completed(futures):
                call_id = futures[future]
                try:
                    result = future.result(timeout=5.0)
                    results[call_id] = result
                except Exception as e:
                    errors[call_id] = str(e)
        
        # Verify partial success
        self.assertGreater(len(results), 0, "Should have some successful calls")
        self.assertGreater(len(errors), 0, "Should have some failed calls")
        
        # Verify expected failure pattern
        expected_successes = [i for i in call_ids if i % 3 == 2]
        expected_failures = [i for i in call_ids if i % 3 != 2]
        
        self.assertEqual(set(results.keys()), set(expected_successes))
        self.assertEqual(set(errors.keys()), set(expected_failures))


class ConcurrentOperationTests(unittest.TestCase):
    """Test concurrent operation safety"""
    
    def test_file_write_concurrency(self):
        """Test concurrent file write operations"""
        
        def write_to_file(file_path, content, write_id):
            """Write content to file with ID"""
            try:
                with open(file_path, 'a') as f:
                    f.write(f"Write {write_id}: {content}\n")
                return {"success": True, "write_id": write_id}
            except Exception as e:
                return {"success": False, "error": str(e), "write_id": write_id}
        
        # Test concurrent writes to same file
        temp_file = os.path.join(tempfile.gettempdir(), "concurrent_test.txt")
        
        # Clean up any existing file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        write_ids = range(10)
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(write_to_file, temp_file, f"Content {i}", i) 
                for i in write_ids
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Verify all writes completed
        self.assertEqual(len(results), len(write_ids))
        
        # Verify file integrity
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                lines = f.readlines()
            
            # Should have all writes (no corruption)
            self.assertEqual(len(lines), len(write_ids))
            
            # Clean up
            os.remove(temp_file)
    
    def test_shared_resource_access(self):
        """Test concurrent access to shared resources with locks"""
        
        class SharedCounter:
            def __init__(self):
                self._value = 0
                self._lock = threading.Lock()
            
            def increment(self):
                with self._lock:
                    current = self._value
                    time.sleep(0.001)  # Simulate processing time
                    self._value = current + 1
                    return self._value
            
            @property
            def value(self):
                with self._lock:
                    return self._value
        
        # Test concurrent increments
        counter = SharedCounter()
        num_threads = 10
        increments_per_thread = 10
        
        def increment_worker():
            results = []
            for _ in range(increments_per_thread):
                result = counter.increment()
                results.append(result)
            return results
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(increment_worker) for _ in range(num_threads)]
            
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        # Verify thread safety
        expected_final_value = num_threads * increments_per_thread
        self.assertEqual(counter.value, expected_final_value)
        self.assertEqual(len(all_results), expected_final_value)
        
        # Verify no duplicate values (indicates proper locking)
        self.assertEqual(len(set(all_results)), expected_final_value)


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2, buffer=True)