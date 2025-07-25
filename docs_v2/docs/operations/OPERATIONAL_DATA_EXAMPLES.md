# Operational Data Examples & Edge Cases

This document provides specific examples of reservation data, common patterns, and edge cases found in the Airtable dev environment.

## 📊 Data Patterns by Source

### iTrip Reservations

#### Standard iTrip Reservation
```
Record ID: recCZgMYp7TkcJGsV
Property: 5207 E Grovers Ave, Scottsdale, AZ, 85254
Check-in: June 4, 2025
Check-out: June 10, 2025
Work Order: #2859582
Door Code: 6969
Gate Code: 5858
Special Notes: *Water Softener
Next Guest: Owner Stay
```

#### iTrip with Complex Instructions
```
Record ID: recGTh6LWyPFpLzy4
Property: 6934 E Sandra Terrace, Scottsdale AZ 85254
Work Order: #2855365
Door Code: 8096
TV Service: YouTube TV Live
Critical Note: **MAKE SURE NOTHING IS IN THE POOL EQUIPMENT AREA NOT EVEN POOL BRUSH OR POOL NET
Next Guest: Owner Stay
```

#### iTrip with Building Access
```
Record ID: recbNIt6r0SWKA0LR
Property: 5104 N 32nd St, #148, Phoenix, AZ, 85018
Gate code: #1418
Parking: Underground Spot #18
Door Code: 4019
TV Service: Cable
Access: 1 key, 1 key fob, Building 3
```

### Airbnb Reservations

#### Standard Airbnb Booking
```
Record ID: recPCoMMmtENS4Lxt
UID: 1418fb94e984-8bf9767b239026dbb22c0d2947273c64@airbnb.com
Property: 5020 N 86th Pl, Scottsdale AZ 85250
Owner: George Mevawala
Status: Scheduled
Assignee: Laundry User
```

### Evolve Reservations

#### Evolve Guest Reservation
```
Record ID: recSizEoNw2LeTruk
Reservation ID: 14380224
Property: 2065 W 1st Pl, Mesa, AZ, 85201
Owner: Kathy Nelson
Job Status: In Progress
Started: June 12 at 8:13 AM
```

#### Evolve Blocks (Needs Review)
```
Multiple blocks for property: 5512 S Rocky Point Rd, Tempe, AZ
- April 17-21, 2025 (ID: 13909080)
- April 23-26, 2025 (ID: 14521975)
All marked as "Needs Review" - require classification
```

### Hospitable Reservations

#### Hospitable with Same-Day Turnover
```
Record ID: recsua9YBmVNowEAy
UID: c2593475-a55c-4872-ac90-68b8206f4e48@reservations.hospitable.com
Property: 8438 E Keim Dr, Scottsdale
Same-day Turnover: TRUE
Service Time: 10:00 AM (expedited)
```

## 🔄 State Transitions

### New Reservation → Scheduled Job
```
Initial State:
- Status: New
- Service Job ID: (empty)
- Sync Status: Not Created

After "Create Job & Sync Status":
- Service Job ID: job_xxxxx
- Job Status: Scheduled
- Sync Status: Synced
- Service Appointment ID: appt_xxxxx
```

### Modified Reservation Flow
```
Original Record:
- ID: 32381
- Status: Old
- UID: 4540434_recEx1JrPW31CtgX4

Modified Record:
- ID: 32467
- Status: Modified
- UID: 4540434_recEx1JrPW31CtgX4 (same)
- Same-day Turnover: true (changed)
```

### Schedule Mismatch Example
```
Record: rec3CZ8y6mI1hzA3H
Property: 6536 E 5th St, Scottsdale
Issue: TIME MISMATCH
- Airtable Final Service Time: 10:15 AM
- HCP Scheduled Time: 12:00 PM
- Sync Status: Wrong Time
Resolution: Use "🔄 Reschedule" button
```

## 📝 Special Cases & Edge Cases

### 1. Same-Day Turnovers
- Automatically detected when check-in = check-out date
- Service time changes from 10:15 AM to 10:00 AM
- Service Line Description: "Turnover STR SAME DAY"
- Requires expedited service

### 2. Owner Stays
Identified by iTrip note: "Owner Stay (Next Checkin)"
```
Example: rec2cQ3OIPaO33Xph
Special handling: "The owner is staying in their home. Please make sure it's extra clean and ready!"
```

### 3. Property with Multiple Active Reservations
```
Property: 5244 E Hartford Ave, Scottsdale
- Old reservation (ID: 32381) - Status: Old
- Modified reservation (ID: 32467) - Status: Modified, Same-day
- Future reservation (ID: 32468) - Status: New
```

### 4. Blocks Requiring Classification
```
Entry Type: Block
Service Type: Needs Review
Common for Evolve properties
Action Required: Manual classification to:
- Owner Stay
- Maintenance  
- Unavailable
- Other
```

### 5. Complex Access Instructions
```
Property: 15221 N Clubgate Dr #2036, Scottsdale
- Gate Code: 8881#
- Door Code: 6051
- Amenities: Cable-Cox, 1 garage remote, 1 key fob
- Special: "Check master bedroom nightstand drawer"
```

## 🚨 Data Quality Issues

### 1. Duplicate Evolve Blocks
Multiple records with same UID but different record IDs:
- Indicates re-import or sync issues
- Example: UID 13909080_recVn7GI5b9kdAUZk appears 3 times

### 2. Old Unprocessed Records
Records from April 2025 still showing:
- Service Job ID: empty
- Sync Status: Not Created
- Likely missed during initial processing

### 3. Missing Next Guest Dates
Many records show:
- Service Line Description: "Turnover STR Next Guest Unknown"
- Indicates gap in booking data

## 📊 Field Value Examples

### Service Types
- Turnover (most common)
- Inspection
- Return Laundry
- Touchup
- Needs Review (requires action)
- Canceled
- Initial Service
- Last Service
- Deep Clean
- Move-out Clean

### Job Statuses
- Unscheduled
- Scheduled
- In Progress
- Completed
- Canceled

### Sync Statuses
- Synced (all good)
- Wrong Date (date mismatch)
- Wrong Time (time mismatch)
- Not Created (no job yet)

### Entry Sources
- iTrip (CSV import)
- Evolve (CSV import)
- Airbnb (ICS feed)
- VRBO (ICS feed)
- Booking.com (ICS feed)
- Hospitable (ICS feed)
- Guesty (ICS feed)
- HostTools (ICS feed)

## 🔧 Automation Triggers

### Button Fields
1. **Create Job & Sync Status**: Creates HCP job
2. **Add/Update Schedule**: Updates appointment time
3. **Delete Job Schedule**: Removes appointment
4. **Service Job Link**: Opens HCP job page

### Webhook Updates
Fields updated via webhook:
- Job Status
- Assignee
- On My Way Time
- Job Started Time
- Job Completed Time
- Service Sync Details

### Calculated Fields
- Final Service Time (formula based on same-day flag)
- Next Guest Date (looked up from future reservations)
- Service Line Description (concatenated from multiple fields)