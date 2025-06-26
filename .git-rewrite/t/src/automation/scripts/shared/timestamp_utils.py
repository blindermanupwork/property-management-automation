#!/usr/bin/env python3
"""
Unified timestamp utilities for consistent date/time formatting across the system.

This module provides a single source of truth for timestamp generation to fix
inconsistencies between webhook, CSV processing, and HCP sync timestamps.

Standard format: ISO 8601 with seconds precision and proper timezone
Example: 2025-06-11T23:42:05-07:00
"""

from datetime import datetime, timezone
import pytz

# Arizona timezone (MST, no daylight saving)
ARIZONA_TZ = pytz.timezone('America/Phoenix')

def get_arizona_timestamp():
    """
    Get current timestamp in Arizona timezone with consistent formatting.
    
    Returns:
        str: ISO 8601 formatted timestamp with seconds precision
             Example: "2025-06-11T23:42:05-07:00"
    """
    return datetime.now(ARIZONA_TZ).isoformat(sep='T', timespec='seconds')

def get_arizona_timestamp_space():
    """
    Get current timestamp with space separator (for backward compatibility).
    
    Returns:
        str: Timestamp with space separator and seconds precision
             Example: "2025-06-11 23:42:05-07:00"
    """
    return datetime.now(ARIZONA_TZ).isoformat(sep=' ', timespec='seconds')

def get_arizona_datetime():
    """
    Get current datetime object in Arizona timezone.
    
    Returns:
        datetime: Timezone-aware datetime object
    """
    return datetime.now(ARIZONA_TZ)

def format_timestamp_for_airtable(dt=None):
    """
    Format a datetime for Airtable consistency.
    
    Args:
        dt: datetime object (if None, uses current time)
        
    Returns:
        str: Formatted timestamp for Airtable
    """
    if dt is None:
        dt = get_arizona_datetime()
    elif not dt.tzinfo:
        # If naive datetime, assume it's in Arizona timezone
        dt = ARIZONA_TZ.localize(dt)
    elif dt.tzinfo != ARIZONA_TZ:
        # Convert to Arizona timezone if different
        dt = dt.astimezone(ARIZONA_TZ)
    
    # Use consistent format: ISO with 'T' separator and seconds precision
    return dt.isoformat(sep='T', timespec='seconds')

def parse_airtable_timestamp(timestamp_str):
    """
    Parse a timestamp from Airtable into a datetime object.
    
    Args:
        timestamp_str: String timestamp from Airtable
        
    Returns:
        datetime: Timezone-aware datetime object
    """
    # Handle various formats we might encounter
    if not timestamp_str:
        return None
    
    # Try parsing with dateutil for flexibility
    from dateutil.parser import parse
    dt = parse(timestamp_str)
    
    # Ensure timezone awareness
    if not dt.tzinfo:
        dt = ARIZONA_TZ.localize(dt)
    
    return dt

# JavaScript-compatible function for HCP sync
def get_arizona_timestamp_js():
    """
    Get timestamp in a format compatible with JavaScript Date.toISOString().
    Note: This returns proper Arizona time with correct timezone offset,
    not UTC with manual offset like the current JS implementation.
    
    Returns:
        str: ISO 8601 formatted timestamp
             Example: "2025-06-11T23:42:05-07:00"
    """
    return get_arizona_timestamp()

if __name__ == "__main__":
    # Test the functions
    print("Timestamp Utils Test:")
    print(f"Standard format: {get_arizona_timestamp()}")
    print(f"Space format:    {get_arizona_timestamp_space()}")
    print(f"JS compatible:   {get_arizona_timestamp_js()}")
    print(f"DateTime object: {get_arizona_datetime()}")
    
    # Test parsing
    test_timestamps = [
        "2025-06-11T23:42:05-07:00",
        "2025-06-11 23:42:05-07:00",
        "2025-06-11T23:42:05.123456-07:00",
        "2025-06-11T23:42:05Z"
    ]
    
    print("\nParsing tests:")
    for ts in test_timestamps:
        parsed = parse_airtable_timestamp(ts)
        print(f"  {ts} -> {parsed}")