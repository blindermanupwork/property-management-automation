# Airtable View Operational Scenarios

This document outlines the different views in the Reservations table, their purposes, and real examples of records that appear in each view. These scenarios help understand the operational workflow and data states in the system.

## 📊 View Overview

The Reservations table contains 14 views that organize records by their operational status, source, and scheduling needs:

### 1. ⏰❌ Incomplete
**Purpose**: Shows jobs that are actively being worked on (In Progress or Scheduled) but haven't been completed yet.
**Filter Logic**: Job Status = "In Progress" OR "Scheduled" AND Check-out Date is today or in the past
**Operational Use**: Daily monitoring view to track jobs that need attention

**Example Records**:
- **rec recSizEoNw2LeTruk**: Job in progress for 2065 W 1st Pl, Mesa (Evolve property)
  - Status: In Progress
  - Assignee: Laundry User
  - Started: June 12, 2025 at 8:13 AM
  
- **rec recPCoMMmtENS4Lxt**: Scheduled job for 5020 N 86th Pl, Scottsdale (Airbnb)
  - Status: Scheduled
  - Due: June 10, 2025 at 10:15 AM
  - Next Guest: June 19

### 2. ⏰❓ Mismatch
**Purpose**: Identifies scheduling discrepancies between Airtable and HousecallPro
**Filter Logic**: Sync Status = "Wrong Date" OR "Wrong Time"
**Operational Use**: Quality control to fix scheduling conflicts

**Example Records**:
- **rec rec3CZ8y6mI1hzA3H**: Time mismatch for 6536 E 5th St, Scottsdale
  - Airtable shows: 10:15 AM
  - HCP shows: 12:00 PM
  - Assignee: Boris Blinderman
  - Action needed: Reschedule to correct time

### 3. ⏰🗑️ Removed
**Purpose**: Tracks canceled reservations that still have HCP jobs created
**Filter Logic**: Status = "Removed" AND Service Job ID is not empty
**Operational Use**: Cleanup view to cancel unnecessary HCP jobs

**Example Records**:
- **rec recikTsYUyy9F9HOS**: Canceled Airbnb reservation for June 14
  - Property: 19942 N 78th Ln, Glendale
  - Job Status: Still scheduled in HCP
  - Action needed: Cancel HCP job

### 4. ⏰⚠️ Modified
**Purpose**: Shows reservations with changed dates or details
**Filter Logic**: Status = "Modified"
**Operational Use**: Review changes and update schedules accordingly

**Example Records**:
- **rec recJYlbgAOCiIDNBi**: Modified Airbnb booking
  - Property: 7740 E Heatherbrae Ave, Scottsdale
  - Changes: Date or time adjustment
  - Current Status: Synced after modification

- **rec rec8vzWBfuoqS5b9N**: Modified iTrip reservation with same-day turnover
  - Property: 5244 E Hartford Ave, Scottsdale  
  - Special: Same-day turnover (10:00 AM service)
  - Note: "Owner Stay (Next Checkin)"

### 5. ⬆️🧹 Upcoming
**Purpose**: Active jobs scheduled for the near future (typically next 7-14 days)
**Filter Logic**: Job Status = "Scheduled" AND Check-out Date >= Today
**Operational Use**: Planning view for upcoming work

**Example Records**:
- **rec recsua9YBmVNowEAy**: Same-day turnover on June 12
  - Property: 8438 E Keim Dr, Scottsdale (Hospitable)
  - Time: 10:00 AM (expedited for same-day)
  - Assignee: Laundry User

- **rec recGTh6LWyPFpLzy4**: iTrip property with special instructions
  - Property: 6934 E Sandra Terrace, Scottsdale
  - Special note: "MAKE SURE NOTHING IS IN THE POOL EQUIPMENT AREA"
  - Owner stay next

### 6. 🏠🏠 Property Filter
**Purpose**: View specific property's reservations (filtered dynamically)
**Filter Logic**: Property ID = [Selected Property]
**Operational Use**: Property-specific management and history

**Example**: 5244 E Hartford Ave, Scottsdale
- Shows all reservations for this property
- Includes old, modified, and new reservations
- Useful for tracking property patterns

### 7. 🏠 iTrip
**Purpose**: All reservations from iTrip CSV imports
**Filter Logic**: Entry Source = "iTrip" OR ICS URL = "csv_itrip"
**Operational Use**: Monitor iTrip-specific bookings and their special requirements

**Example Records**:
- Properties with door codes and special instructions
- Work order numbers from iTrip system
- Owner stay notifications
- Special requirements (water softener, TV service, etc.)

### 8. 🏠 Evolve
**Purpose**: All reservations from Evolve portal
**Filter Logic**: Entry Source = "Evolve" OR ICS URL contains "evolve"
**Operational Use**: Track Evolve properties and blocks

**Example Records**:
- Many "Needs Review" blocks requiring classification
- Property: 5512 S Rocky Point Rd, Tempe (multiple blocks)
- Blocks from April 2025 still unprocessed

### 9. HCP Create Jobs
**Purpose**: Records ready for HCP job creation
**Filter Logic**: Service Job ID is empty AND (Service Type != "No Service" AND Service Type != "Canceled") AND Property ID is not empty
**Operational Use**: Daily job creation workflow

**Example Records**:
- New reservations needing job creation
- Modified reservations requiring new jobs
- Records with all prerequisites met (Property ID, dates, etc.)

### 10. Calendar Views

#### Job Schedule
**Purpose**: Calendar view of HCP job schedules
**Display**: Based on Scheduled Service Time field
**Use**: Visual job planning

#### Blocks
**Purpose**: Calendar view of property blocks
**Filter**: Entry Type = "Block"
**Use**: See when properties are unavailable

#### Reservation Schedule  
**Purpose**: Calendar of all guest reservations
**Filter**: Entry Type = "Reservation"
**Use**: Guest booking overview

#### All Schedule
**Purpose**: Combined calendar of everything
**Use**: Complete property timeline

### 11. All View
**Purpose**: Unfiltered view of all records
**Use**: Administrative access, troubleshooting

## 🔄 Operational Workflows by View

### Daily Operations Flow:
1. **Morning Check**: Start with ⏰❌ Incomplete to see active jobs
2. **Quality Control**: Review ⏰❓ Mismatch for scheduling issues
3. **Job Creation**: Use HCP Create Jobs view to create new jobs
4. **Planning**: Check ⬆️🧹 Upcoming for next few days

### Weekly Maintenance:
1. **Cleanup**: Review ⏰🗑️ Removed to cancel unneeded jobs
2. **Updates**: Process ⏰⚠️ Modified records
3. **Blocks Review**: Check Evolve view for "Needs Review" blocks

### Property-Specific Tasks:
- Use 🏠🏠 Property Filter to see all activity for a property
- Review patterns, recurring issues, owner stays

## 📝 Common Scenarios

### Scenario 1: Same-Day Turnover
- Appears in ⬆️🧹 Upcoming with Same-day Turnover = true
- Service time automatically set to 10:00 AM (instead of 10:15 AM)
- Priority handling required

### Scenario 2: Owner Stay
- iTrip includes "Owner Stay (Next Checkin)" in notes
- Requires extra attention to cleanliness
- May have special instructions

### Scenario 3: Modified Reservation
- Original marked as "Old"
- New version marked as "Modified"
- May require schedule adjustment

### Scenario 4: Property with Special Requirements
- Door codes, gate codes in iTrip Report Info
- TV service specifications
- Water softener notes
- Pool equipment restrictions

## 🚨 Action Items by View

### ⏰❌ Incomplete
- Monitor job progress
- Follow up on delayed completions
- Check assignee status

### ⏰❓ Mismatch
- Click "🔄 Reschedule" button
- Verify correct service times
- Confirm with cleaner if needed

### ⏰🗑️ Removed
- Cancel HCP jobs for removed reservations
- Archive completed cancellations

### ⏰⚠️ Modified
- Review changes
- Update schedules if needed
- Verify job details match new dates

### 🏠 Evolve (Blocks)
- Change "Needs Review" to appropriate Service Type
- Determine if block needs service
- Set Block Type (Owner Stay, Maintenance, etc.)