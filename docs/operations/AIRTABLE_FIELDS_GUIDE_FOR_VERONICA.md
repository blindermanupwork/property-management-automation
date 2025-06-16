# Essential Airtable Fields Guide for Daily Operations

**Version:** 1.0  
**Created:** June 16, 2025  
**Purpose:** Detailed guide to understanding critical fields in the Reservations table and their operational importance

---

## 🎯 Introduction: Why Fields Matter

Each field in Airtable serves a specific purpose in the cleaning workflow. Understanding what each field means and when to use it is crucial for smooth operations. This guide explains:

1. **What the field contains** - The type of data
2. **Why it exists** - The problem it solves
3. **When it updates** - Automatic vs manual
4. **How to use it** - Operational context
5. **Common issues** - What can go wrong

---

## 📊 Field Categories

### 🔑 Core Identification Fields

#### ID (Record ID)
- **What**: Unique Airtable record identifier (like rec123...)
- **Why**: Internal reference for troubleshooting
- **Updates**: Automatically when record created
- **Use**: Reference when reporting issues
- **Note**: Different from Reservation UID

#### Reservation UID
- **What**: Unique identifier from booking platform
- **Why**: Links to original Airbnb/VRBO/iTrip booking
- **Updates**: On import from platform
- **Use**: Cross-reference with platform support
- **Example**: "HMAFNHNHB2" from Airbnb

#### Property ID
- **What**: Links to Properties table
- **Why**: Connects all property information
- **Updates**: On import or manual selection
- **Use**: **CRITICAL** - Must have value for job creation
- **Issue**: Missing = can't create HCP job

---

### 📅 Date & Time Fields

#### Check-in Date
- **What**: Guest arrival date
- **Why**: Helps identify same-day turnovers
- **Updates**: From booking platform
- **Use**: Calculate service urgency
- **Note**: Same day as checkout = rush clean

#### Check-out Date
- **What**: Guest departure date
- **Why**: Determines service date
- **Updates**: From booking platform
- **Use**: **PRIMARY** scheduling reference
- **Critical**: Past date with incomplete job = problem

#### Custom Service Time
- **What**: Manual override for service time
- **Why**: Handle special scheduling needs
- **Updates**: **YOU SET THIS** manually
- **Use**: Override default 10:15 AM time
- **Example**: "11:30 AM" for late checkout

#### Final Service Time
- **What**: Calculated actual service time
- **Why**: What gets sent to HCP
- **Updates**: Automatically from rules
- **Logic**: Custom > Same-day (10:00) > Default (10:15)
- **Use**: This is THE scheduling time

#### Scheduled Service Time
- **What**: What HCP actually shows
- **Why**: Confirms sync worked
- **Updates**: After HCP sync
- **Use**: Compare to Final Service Time
- **Issue**: Mismatch = sync problem

#### Next Guest Date
- **What**: When next guest arrives
- **Why**: Deadline for cleaning completion
- **Updates**: From calendar/platform
- **Use**: Urgency indicator
- **Critical**: Today/tomorrow = HIGH PRIORITY

---

### 👷 Job Management Fields

#### Service Job ID
- **What**: HousecallPro job identifier
- **Why**: Links Airtable to HCP
- **Updates**: When job created
- **Use**: Click to open in HCP
- **Empty**: Means no job created yet
- **Format**: "job_abc123..."

#### Job Status
- **What**: Current status from HCP
- **Why**: Track work progress
- **Updates**: Real-time from HCP
- **Values**: 
  - "Scheduled" - Assigned, not started
  - "In Progress" - Cleaner working
  - "Completed" - Job done
- **Critical**: Past jobs not "Completed" = PROBLEM

#### Service Type
- **What**: Type of cleaning needed
- **Why**: Determines service level
- **Updates**: On import or manual
- **Values**:
  - "Turnover" - Standard guest clean
  - "Refresh" - Mid-stay clean
  - "Deep Clean" - Detailed service
  - "Needs Review" - **YOU DECIDE**
  - "No Service" - Skip cleaning
  - "Canceled" - Was needed, now not
- **Use**: Must be set before job creation

#### Entry Type
- **What**: Reservation vs Block
- **Why**: Different handling needed
- **Values**:
  - "Reservation" - Guest booking
  - "Block" - Owner/maintenance
- **Use**: Blocks need Service Type decision

#### Block Type (for blocks only)
- **What**: Reason for block
- **Why**: Helps decide if cleaning needed
- **Values**:
  - "Owner Stay" - Usually needs clean
  - "Maintenance" - Maybe needs clean
  - "Unknown" - **INVESTIGATE**
- **Updates**: YOU SET based on research

---

### 🔄 Sync & Status Fields

#### Sync Status
- **What**: HCP synchronization state
- **Why**: Identifies sync problems
- **Updates**: After each sync attempt
- **Values**:
  - "✅ Schedule is in sync" - All good
  - "Wrong Time" - Time mismatch
  - "Wrong Date" - Date mismatch
  - "Not Scheduled" - Missing in HCP
  - "Not Created" - No job yet
- **Action**: Non-✅ = needs attention

#### Schedule Sync Details
- **What**: Specific sync information
- **Why**: Explains exact problem
- **Updates**: With Sync Status
- **Example**: "⚠️ TIME MISMATCH: Airtable shows 10:15 AM but HCP shows 12:00 PM"
- **Use**: Tells you what to fix

#### Status
- **What**: Reservation lifecycle state
- **Why**: Track changes over time
- **Values**:
  - "Active" - Current reservation
  - "Old" - Replaced by modification
  - "Modified" - Changed after import
  - "Removed" - Canceled
- **Use**: "Removed" + Job ID = cancel job

#### Sync Date and Time
- **What**: Last sync timestamp
- **Why**: Know data freshness
- **Updates**: Every sync cycle
- **Use**: Old timestamp = stale data
- **Note**: Uses PST timezone

---

### 👤 Assignment Fields

#### Assignee
- **What**: Cleaner assigned in HCP
- **Why**: Know who's responsible
- **Updates**: From HCP assignment
- **Use**: Contact for issues
- **Empty**: No cleaner assigned yet
- **Common**: "Boris Blinderman", "Laundry User"

#### HCP Address (from Property)
- **What**: Property's HCP address record
- **Why**: Required for job creation
- **Updates**: From Properties table
- **Use**: Must exist to create jobs
- **Issue**: Empty = setup needed

#### Full Name (from HCP Customer)
- **What**: Property's HCP customer
- **Why**: Required for job creation
- **Updates**: From Properties table
- **Use**: Must exist to create jobs
- **Issue**: Empty = setup needed

---

### 📝 Instruction Fields

#### Service Line Description
- **What**: Auto-generated service description
- **Why**: Tells cleaner the service type
- **Updates**: Automatically from rules
- **Examples**:
  - "Turnover"
  - "Turnover STR Next Guest June 15"
  - "Turnover - Long-Stay Departure"
- **Use**: Shows in HCP job details

#### Custom Service Line Instructions
- **What**: Special instructions YOU add
- **Why**: Custom requirements for property
- **Updates**: **YOU SET THIS**
- **Limit**: 200 characters max
- **Examples**:
  - "Check patio light timer"
  - "Extra towels for hot tub"
  - "Owner arriving - deep clean"
- **Shows**: In HCP job line item

#### iTrip Report Info
- **What**: All text from iTrip email
- **Why**: Contains door codes, instructions
- **Updates**: On iTrip import
- **Contains**:
  - Door codes: "GARAGE: 1234"
  - Instructions: "CHECK TIMER"
  - Notes: "Owner Stay"
- **Critical**: Read for every iTrip job

---

### 🕐 Time Tracking Fields

#### On My Way Time
- **What**: When cleaner left for job
- **Why**: Track response time
- **Updates**: From HCP when cleaner starts travel
- **Use**: Know cleaner is en route
- **Missing**: Cleaner hasn't left yet

#### Job Started Time
- **What**: When cleaning began
- **Why**: Track work duration
- **Updates**: When cleaner arrives
- **Use**: Calculate cleaning time
- **Issue**: Started but not completed = check

#### Job Completed Time
- **What**: When cleaning finished
- **Why**: Confirm job done
- **Updates**: When cleaner finishes
- **Use**: **CRITICAL** - Proves work done
- **Missing**: Job not complete

#### Job Creation Time
- **What**: When HCP job was created
- **Why**: Track lead time
- **Updates**: On job creation
- **Use**: Audit trail
- **Note**: Some jobs created weeks early

---

### 🔧 Action Button Fields

#### Create Job & Sync Status
- **What**: Button to create HCP job
- **Why**: One-click job creation
- **When**: Shows when no job exists
- **Requirements**:
  - Property has HCP IDs
  - Service Type selected
  - Final Service Time set
- **Result**: Creates job, returns Job ID

#### Add/Update Schedule
- **What**: Button to sync schedule
- **Why**: Fix time mismatches
- **When**: Job exists but wrong time
- **Action**: Sends Final Service Time to HCP
- **Use**: After setting Custom Service Time

#### Delete Job Schedule
- **What**: Button to remove schedule
- **Why**: Handle special cases
- **When**: Rarely used
- **Caution**: Removes scheduling only
- **Note**: Doesn't delete job itself

---

### 🚨 Special Indicator Fields

#### Same-day Turnover
- **What**: Checkbox for rush cleans
- **Why**: Automatically adjusts time
- **Logic**: True = 10:00 AM service
- **Updates**: Auto-calculated
- **Formula**: Check-in = Check-out
- **Critical**: HIGH PRIORITY jobs

#### Overlapping Dates
- **What**: Flags booking conflicts
- **Why**: Identifies problems
- **Updates**: Auto-calculated
- **Use**: Investigate conflicts
- **Action**: May need manual resolution

#### Entry Source
- **What**: Where booking came from
- **Why**: Platform-specific handling
- **Values**:
  - "iTrip" - Email CSV import
  - "Evolve" - Portal scraping
  - "ICS" - Calendar feeds
- **Use**: Filter by platform

#### ICS URL
- **What**: Calendar feed source
- **Why**: Track import source
- **Updates**: On ICS import
- **Contains**: Feed URL or platform
- **Example**: "airbnb_com" for Airbnb

---

## 🎯 Field Priority for Daily Operations

### Must Monitor Daily
1. **Job Status** - Incomplete jobs
2. **Sync Status** - Schedule problems
3. **Final Service Time** - When service happens
4. **Assignee** - Who's responsible
5. **Same-day Turnover** - Rush jobs

### Check When Creating Jobs
1. **Property ID** - Must have value
2. **Service Type** - Must be selected
3. **HCP Address/Customer** - Must exist
4. **Custom Instructions** - Add if needed
5. **Entry Type** - Block vs Reservation

### Review for Issues
1. **Schedule Sync Details** - What's wrong
2. **On My Way/Started/Completed** - Progress tracking
3. **Status** - Modified/Removed
4. **iTrip Report Info** - Special instructions
5. **Next Guest Date** - Urgency level

---

## 💡 Common Field-Related Issues

### "Can't Create Job"
- Check: Property ID populated?
- Check: HCP Address/Customer linked?
- Check: Service Type selected?
- Fix: Update Properties table with HCP IDs

### "Wrong Time in HCP"
- Check: Final Service Time correct?
- Check: Sync Status shows mismatch?
- Fix: Click Add/Update Schedule

### "Job Not Completing"
- Check: Job Started Time exists?
- Check: Assignee field shows who?
- Fix: Contact cleaner directly

### "Missing Special Instructions"
- Check: iTrip Report Info field
- Check: Custom Instructions empty?
- Fix: Add to Custom Service Line Instructions

---

## 📝 Your Field Homework

1. **Pick 5 records** and trace all fields
   - Note which are empty
   - Understand the relationships
   - See how fields connect

2. **Practice setting Custom fields**
   - Custom Service Time
   - Custom Instructions
   - Service Type for blocks

3. **Document field questions**
   - Which fields confuse you?
   - What additional fields would help?
   - Which fields seem redundant?

---

*Keep this guide handy when working in Airtable. Understanding fields prevents mistakes and speeds up your workflow!*