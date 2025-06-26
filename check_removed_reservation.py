#!/usr/bin/env python3
"""
Check if a removed reservation actually exists in the ICS feed
"""
import requests
from icalendar import Calendar
from datetime import datetime
import sys

def check_reservation_in_feed(ics_url, uid_to_find, check_in_date=None, check_out_date=None):
    """Check if a specific reservation exists in an ICS feed"""
    print(f"Fetching ICS feed: {ics_url}")
    
    try:
        # Fetch the ICS feed
        response = requests.get(ics_url, timeout=30)
        response.raise_for_status()
        
        # Parse the calendar
        cal = Calendar.from_ical(response.text)
        
        found_events = []
        all_uids = []
        
        for component in cal.walk():
            if component.name == "VEVENT":
                event_uid = str(component.get('UID', ''))
                all_uids.append(event_uid)
                
                # Check if this is our target event
                if uid_to_find in event_uid:
                    dtstart = component.get('DTSTART')
                    dtend = component.get('DTEND')
                    summary = str(component.get('SUMMARY', ''))
                    
                    found_events.append({
                        'uid': event_uid,
                        'summary': summary,
                        'start': dtstart.dt if dtstart else None,
                        'end': dtend.dt if dtend else None
                    })
                
                # Also check by dates if provided
                elif check_in_date and check_out_date:
                    dtstart = component.get('DTSTART')
                    dtend = component.get('DTEND')
                    if dtstart and dtend:
                        start_str = dtstart.dt.strftime('%Y-%m-%d') if hasattr(dtstart.dt, 'strftime') else str(dtstart.dt)
                        end_str = dtend.dt.strftime('%Y-%m-%d') if hasattr(dtend.dt, 'strftime') else str(dtend.dt)
                        
                        if start_str == check_in_date and end_str == check_out_date:
                            summary = str(component.get('SUMMARY', ''))
                            found_events.append({
                                'uid': event_uid,
                                'summary': summary,
                                'start': start_str,
                                'end': end_str,
                                'note': 'Found by date match'
                            })
        
        # Report findings
        print(f"\nTotal events in feed: {len(all_uids)}")
        
        if found_events:
            print(f"\n✅ FOUND {len(found_events)} matching event(s):")
            for event in found_events:
                print(f"  - UID: {event['uid']}")
                print(f"    Summary: {event['summary']}")
                print(f"    Start: {event['start']}")
                print(f"    End: {event['end']}")
                if 'note' in event:
                    print(f"    Note: {event['note']}")
        else:
            print(f"\n❌ Reservation NOT FOUND in feed")
            print(f"   Searched for UID containing: {uid_to_find}")
            if check_in_date and check_out_date:
                print(f"   Also searched for dates: {check_in_date} to {check_out_date}")
            
            # Show some sample UIDs for debugging
            print(f"\n   Sample UIDs in feed (first 5):")
            for uid in all_uids[:5]:
                print(f"     - {uid}")
                
        return found_events
        
    except Exception as e:
        print(f"Error fetching/parsing ICS feed: {e}")
        return None

# Check the specific reservation
if __name__ == "__main__":
    # The reservation we're looking for
    ics_url = "https://www.airbnb.com.au/calendar/ical/987228927156067958.ics?s=8f9a55479cc60b167e1c97adc65f57a2"
    uid_partial = "1418fb94e984-bc437be9cf94d92c7a3ee98251ccca8e"
    check_in = "2025-06-12"
    check_out = "2025-06-16"
    
    print("Checking if 'removed' reservation still exists in Airbnb feed...")
    print(f"Looking for UID: {uid_partial}")
    print(f"Dates: {check_in} to {check_out}")
    print("-" * 60)
    
    check_reservation_in_feed(ics_url, uid_partial, check_in, check_out)