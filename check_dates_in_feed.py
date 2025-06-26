#!/usr/bin/env python3
"""
Check all events in a date range from ICS feed
"""
import requests
from icalendar import Calendar
from datetime import datetime, date
import sys

def check_events_in_date_range(ics_url, start_date, end_date):
    """Check all events in a date range"""
    print(f"Fetching ICS feed: {ics_url}")
    
    try:
        # Fetch the ICS feed
        response = requests.get(ics_url, timeout=30)
        response.raise_for_status()
        
        # Parse the calendar
        cal = Calendar.from_ical(response.text)
        
        events_in_range = []
        
        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('DTSTART')
                dtend = component.get('DTEND')
                
                if dtstart and dtend:
                    # Convert to date strings for comparison
                    start_str = dtstart.dt.strftime('%Y-%m-%d') if hasattr(dtstart.dt, 'strftime') else str(dtstart.dt)
                    end_str = dtend.dt.strftime('%Y-%m-%d') if hasattr(dtend.dt, 'strftime') else str(dtend.dt)
                    
                    # Check if event overlaps with our date range
                    if (start_str <= end_date and end_str >= start_date):
                        event_uid = str(component.get('UID', ''))
                        summary = str(component.get('SUMMARY', ''))
                        
                        events_in_range.append({
                            'uid': event_uid,
                            'summary': summary,
                            'start': start_str,
                            'end': end_str
                        })
        
        # Report findings
        print(f"\nEvents overlapping {start_date} to {end_date}:")
        
        if events_in_range:
            for event in events_in_range:
                print(f"\n  Event:")
                print(f"    UID: {event['uid']}")
                print(f"    Summary: {event['summary']}")
                print(f"    Dates: {event['start']} to {event['end']}")
        else:
            print(f"  No events found in this date range")
                
        return events_in_range
        
    except Exception as e:
        print(f"Error fetching/parsing ICS feed: {e}")
        return None

# Check the specific dates
if __name__ == "__main__":
    ics_url = "https://www.airbnb.com.au/calendar/ical/987228927156067958.ics?s=8f9a55479cc60b167e1c97adc65f57a2"
    
    print("Checking all events around June 12-16, 2025...")
    print("-" * 60)
    
    check_events_in_date_range(ics_url, "2025-06-10", "2025-06-20")