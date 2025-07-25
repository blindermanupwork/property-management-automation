# Airtable Views Comprehensive Guide for Veronica

**Version:** 1.0  
**Created:** June 16, 2025  
**Purpose:** Complete guide to understanding all Airtable views, their purposes, and how to use them effectively for daily property management operations

---

## 🎯 Introduction: Why Views Matter

Views in Airtable are like different lenses through which you see your data. Each view is designed to answer specific questions and support specific workflows. This guide will help you understand:

1. **What each view shows** - The filtered data you see
2. **Why it was created** - The business problem it solves
3. **When to use it** - The operational scenarios
4. **How to use it** - Step-by-step instructions
5. **Key fields to watch** - Important columns for each view
6. **What might be missing** - Potential improvements

---

## 📊 Overview of All Views

### Daily Operation Views (Morning Routine)
1. **🚨❌ Incomplete** - Jobs that need completion
2. **🚨❓ Mismatch** - Schedule sync issues
3. **🚨🗑️ Removed** - Canceled reservations with active jobs
4. **⚠️ Modified** - Changed reservations

### Planning Views
5. **⬆️🧹 Upcoming Reservations** - Future work (reservations)
6. **⬆️🧹 Upcoming Blocks** - Future blocks
7. **HCP Create Jobs** - Ready for job creation

### Source-Specific Views
8. **🏠 iTrip** - iTrip reservations
9. **🏠 Evolve** - Evolve reservations

### Calendar Views
10. **Job Schedule** - Visual job timeline
11. **Blocks** - Property block calendar
12. **Reservation Schedule** - Guest reservation calendar
13. **All Schedule** - Combined calendar

### Utility Views
14. **🏠🏠 Property Filter** - Single property focus
15. **All View** - Everything unfiltered

---

## 🚨❌ Incomplete View

### Purpose
Shows jobs that haven't been completed yet but should have been. This is your "problem child" view - these jobs need immediate attention.

### Why Created
Without this view, incomplete jobs would get lost in the hundreds of records. Cleaners might mark jobs as "In Progress" but forget to complete them, leaving properties uncleaned for arriving guests.

### Filter Logic
- Job Status = "In Progress" OR "Scheduled"
- AND Check-out Date is today or in the past

### When to Use
- **First thing every morning** - Check for yesterday's incomplete jobs
- **End of day** - Verify today's jobs were completed
- **When guests complain** - First place to check if cleaning was done

### How to Use
1. Open view and sort by Check-out Date (oldest first)
2. Look at Job Status column - "In Progress" means cleaner started but didn't finish
3. Check "On My Way Time" and "Job Started Time" to see when cleaner was there
4. Call cleaner immediately if job shows incomplete
5. Update status in HCP once confirmed

### Key Fields to Watch
- **Job Status** - Should be "Completed" for past dates
- **Assignee** - Who was responsible
- **On My Way Time** - When cleaner left for property
- **Job Started Time** - When cleaning began
- **Check-out Date** - How overdue the job is
- **Property ID** - Which property needs attention
- **Next Guest Date** - Urgency level

### Real Example
Property at 2065 W 1st Pl, Mesa shows "In Progress" from June 10. It's now June 12. The cleaner (Laundry User) started at 8:13 AM but never marked complete. Next guest already checked in!

---

## 🚨❓ Mismatch View

### Purpose
Identifies when HousecallPro schedule doesn't match what Airtable expects. Prevents cleaners from arriving at wrong times.

### Why Created
Sometimes HCP and Airtable get out of sync - maybe someone changed the time in HCP directly, or a sync failed. This view catches these discrepancies before they cause problems.

### Filter Logic
- Sync Status = "Wrong Date" OR "Wrong Time"

### When to Use
- **After morning Incomplete check** - Second priority view
- **When cleaner says wrong time** - Check if system times don't match
- **After bulk schedule changes** - Verify all synced correctly

### How to Use
1. Look at "Schedule Sync Details" column for specifics
2. Compare "Final Service Time" (Airtable) vs HCP scheduled time
3. Decide which time is correct
4. Click "Add/Update Schedule" button to sync from Airtable to HCP
5. Or manually update in HCP if that time is correct

### Key Fields to Watch
- **Sync Status** - "Wrong Time" or "Wrong Date"
- **Schedule Sync Details** - Exact mismatch description
- **Final Service Time** - What Airtable thinks
- **Scheduled Service Time** - What HCP shows
- **Custom Service Time** - Any manual overrides
- **Same-day Turnover** - These are time-critical

### Real Example
Job for 6536 E 5th St shows "⚠️ TIME MISMATCH: Airtable shows 10:15 AM but HCP shows 12:00 PM". This could mean cleaner arrives 2 hours late!

---

## 🚨🗑️ Removed View

### Purpose
Shows canceled Airbnb/VRBO reservations that still have active HCP jobs. These jobs need to be canceled to prevent cleaners from going to empty properties.

### Why Created
When guests cancel, the reservation gets marked "Removed" but HCP jobs don't automatically cancel. Without this view, cleaners waste time going to properties with no guests.

### Filter Logic
- Status = "Removed"
- AND Service Job ID is not empty (has HCP job)

### When to Use
- **Daily morning check** - After Incomplete and Mismatch
- **When reservation canceled** - Immediately check if job exists
- **Before payroll** - Ensure no payment for canceled jobs

### How to Use
1. Click on Service Job Link to open in HCP
2. Cancel the job in HCP
3. Notify assigned cleaner not to go
4. Check if property still needs service for next guest
5. Job disappears from this view once canceled

### Key Fields to Watch
- **Service Job ID** - The HCP job to cancel
- **Job Status** - Current status in HCP
- **Assignee** - Cleaner to notify
- **Check-out Date** - When job was scheduled
- **Property ID** - Which property
- **Entry Source** - Platform that canceled

### Real Example
Guest canceled June 14 stay at 19942 N 78th Ln. Job still shows "Scheduled" with Laundry User assigned. Must cancel before cleaner drives there!

---

## ⚠️ Modified View

### Purpose
Tracks all reservations that changed after initial import. Shows what was modified so you can update accordingly.

### Why Created
Guests change dates, extend stays, or modify reservations. This view ensures we catch all changes and update our schedules to match.

### Filter Logic
- Status = "Modified"

### When to Use
- **Daily review** - Check for recent modifications
- **When confused about dates** - See if reservation was changed
- **For billing questions** - Track what changed when

### How to Use
1. Review what changed (dates, times, duration)
2. Check if job schedule needs updating
3. Verify cleaner availability for new dates
4. Update any special instructions
5. Confirm changes synced to HCP

### Key Fields to Watch
- **Status** - "Modified" means something changed
- **Last Updated** - When change detected
- **Check-in/Check-out Dates** - New dates
- **Same-day Turnover** - May have changed
- **Service Type** - Might need different service
- **iTrip Report Info** - Special notes that changed

### Real Example
Reservation at 5244 E Hartford Ave was modified to be same-day turnover with owner staying. Now needs 10:00 AM service instead of standard 10:15 AM.

---

## ⬆️🧹 Upcoming Reservations View

### Purpose
Shows all future scheduled cleanings for guest reservations. Your main planning view for upcoming work.

### Why Created
Need to see what's coming to plan routes, assign cleaners, and prepare for busy days. Separates active reservations from blocks.

### Filter Logic
- Entry Type = "Reservation"
- Job Status = "Scheduled"
- Check-out Date >= Today

### When to Use
- **Daily planning** - Review next 2-3 days
- **Route optimization** - Group nearby properties
- **Cleaner scheduling** - Balance workloads
- **Supply ordering** - See volume coming up

### How to Use
1. Filter by date range (next 3 days recommended)
2. Group by Assignee to see each cleaner's load
3. Sort by Service Time to optimize routes
4. Check for same-day turnovers (priority)
5. Review special instructions

### Key Fields to Watch
- **Final Service Time** - When cleaning scheduled
- **Same-day Turnover** - High priority (10:00 AM)
- **Assignee** - Who's assigned
- **Service Line Description** - What type of clean
- **Custom Service Line Instructions** - Special requirements
- **Next Guest Date** - Deadline for completion
- **Property ID** - Location for route planning

### Real Example
June 13 shows 15 cleanings with 3 same-day turnovers. One cleaner has 5 jobs spread across the valley - need to reassign for better routing.

---

## ⬆️🧹 Upcoming Blocks View

### Purpose
Shows future blocked periods at properties. These might need service or indicate maintenance/owner stays.

### Why Created
Blocks often represent opportunities for deep cleans, maintenance checks, or owner services. Separating from regular reservations helps identify these opportunities.

### Filter Logic
- Entry Type = "Block"
- Check-out Date >= Today

### When to Use
- **Weekly planning** - Identify service opportunities
- **Owner communication** - Offer cleaning during blocks
- **Maintenance scheduling** - Coordinate with property work
- **Revenue optimization** - Convert blocks to paid services

### How to Use
1. Review blocks starting in next 5 days
2. Check Block Type and Service Type
3. Contact owners about cleaning needs
4. Create jobs for confirmed services
5. Track conversion rate

### Key Fields to Watch
- **Block Type** - Owner Stay, Maintenance, etc.
- **Service Type** - "Needs Review" requires attention
- **Property ID** - Which property
- **Check-in/out Dates** - Block duration
- **Final Service Time** - If service scheduled

### Real Example
Multiple blocks at 825 W Monterey Pl suggest regular pattern. Opportunity to set up recurring service agreement with owner.

---

## HCP Create Jobs View

### Purpose
Shows all reservations ready for HCP job creation. These have all required information but no job yet.

### Why Created
Centralizes job creation workflow. Instead of hunting for records needing jobs, this view presents them ready to go.

### Filter Logic
- Service Job ID is empty (no job yet)
- Service Type != "No Service" AND != "Canceled"
- Property ID is not empty (required for job)
- Has Final Service Time

### When to Use
- **Multiple times daily** - Create jobs as they become ready
- **After imports** - New reservations appear here
- **After modifications** - Changed reservations need new jobs

### How to Use
1. Review each record has complete information
2. Check Service Type is appropriate
3. Verify Property has HCP Customer/Address
4. Click "Create Job & Sync Status" button
5. Job ID appears confirming creation

### Key Fields to Watch
- **Final Service Time** - When service needed
- **Service Type** - Type of cleaning
- **Custom Service Line Instructions** - Special notes
- **HCP Address** - Must have value
- **Full Name (Customer)** - Must have value
- **Entry Type** - Blocks need review first

### Real Example
Block at 825 W Monterey Pl shows "Needs Review" - must change Service Type before creating job. Contact owner first to confirm they want service.

---

## 🏠 iTrip View

### Purpose
Shows all reservations from iTrip email imports. These often have special instructions and door codes.

### Why Created
iTrip properties have unique requirements - work order numbers, door codes, owner stays. Grouping them helps ensure special instructions aren't missed.

### Filter Logic
- Entry Source = "iTrip"
- OR ICS URL = "csv_itrip"

### When to Use
- **Daily special instruction review** - Check for unique requirements
- **Door code updates** - Find access information
- **Owner stay identification** - Premium service needs
- **iTrip reporting** - Platform-specific metrics

### How to Use
1. Filter for upcoming dates
2. Read "iTrip Report Info" column carefully
3. Note door codes, special instructions
4. Identify owner stays for premium service
5. Add instructions to cleaner notes

### Key Fields to Watch
- **iTrip Report Info** - All special instructions
- **Custom Service Line Instructions** - What transfers to HCP
- **Service Line Description** - Auto-generated based on stay type
- **Property ID** - Match to property records

### Special iTrip Patterns
- "Owner Stay (Next Checkin)" - Premium clean required
- Door codes like "GARAGE: 3526"
- "MUST CHECK..." - Critical instructions
- "*Hot Tub" - Special cleaning needed
- TV service notes - Guest information

### Real Example
6051 E Campo Bello Dr shows "MUST CHECK THE TIMER TO PATIO LIGHTS - MAKE SURE IT IS SET FOR ON AT NIGHT". This critical instruction must be in cleaner checklist.

---

## 🏠 Evolve View

### Purpose
Shows all reservations and blocks from Evolve portal scraping. Many blocks need classification.

### Why Created
Evolve doesn't specify block reasons, so blocks import as "Needs Review". This view helps process Evolve-specific records.

### Filter Logic
- Entry Source = "Evolve"
- OR ICS URL contains "evolve"

### When to Use
- **After Evolve import** - Process new blocks
- **Block classification** - Determine service needs
- **Evolve metrics** - Platform performance
- **Pattern identification** - Recurring blocks

### How to Use
1. Filter for "Needs Review" service types
2. Research block reason (owner, maintenance)
3. Update Block Type appropriately
4. Change Service Type if service needed
5. Create job if confirmed

### Key Fields to Watch
- **Service Type** - Many show "Needs Review"
- **Block Type** - Needs classification
- **Entry Type** - Mix of blocks and reservations
- **Property ID** - For block patterns

### Real Example
5512 S Rocky Point Rd has multiple "Needs Review" blocks. Need to determine if these are owner stays or maintenance periods.

---

## 🏠🏠 Property Filter View

### Purpose
Dynamic view to focus on single property's complete history and upcoming schedule.

### Why Created
When issues arise at specific property, need to see patterns - recurring problems, frequent modifications, special requirements.

### Filter Logic
- Property ID = [Selected Property]
- No other filters - shows everything

### When to Use
- **Guest complaints** - Review property history
- **Quality issues** - Check cleaning patterns
- **Access problems** - Find door code history
- **Owner questions** - Complete property timeline

### How to Use
1. Click filter button for Property ID
2. Select property from dropdown
3. Sort by date to see chronologically
4. Look for patterns in issues
5. Review cleaner performance

### Key Fields to Watch
- **Job Status** - Completion patterns
- **Assignee** - Which cleaners work there
- **Job Completed Time** - How long cleanings take
- **Status** - Old, Modified, Active patterns
- **Service Type** - Types of services needed

### Real Example
Filtering for 26208 N 43rd St #73 after complaints shows pattern - same cleaner, jobs marked complete but taking only 45 minutes for 3-bedroom unit.

---

## 📅 Calendar Views

### Job Schedule View

**Purpose**: Visual calendar of HCP scheduled jobs  
**Why Created**: See job distribution across days/weeks  
**Based On**: Scheduled Service Time field  
**Use For**: Daily/weekly visual planning

### Blocks View

**Purpose**: Calendar showing only blocked periods  
**Why Created**: Visualize property availability  
**Filter**: Entry Type = "Block"  
**Use For**: Maintenance planning, owner stay patterns

### Reservation Schedule View

**Purpose**: Calendar of guest reservations only  
**Why Created**: See booking patterns and occupancy  
**Filter**: Entry Type = "Reservation"  
**Use For**: Revenue tracking, busy period planning

### All Schedule View

**Purpose**: Combined calendar of everything  
**Why Created**: Complete property timeline visualization  
**No Filters**: Shows all entries  
**Use For**: Comprehensive planning

---

## 🎯 Daily Workflow Using Views

### Morning Routine (8:00 AM)
1. **🚨❌ Incomplete** - Fix any incomplete jobs
2. **🚨❓ Mismatch** - Resolve schedule conflicts
3. **🚨🗑️ Removed** - Cancel unneeded jobs
4. **⚠️ Modified** - Review changes
5. **HCP Create Jobs** - Create new jobs

### Midday Check (12:00 PM)
1. **🚨❌ Incomplete** - Verify morning jobs done
2. **⬆️🧹 Upcoming** - Prepare for tomorrow
3. **HCP Create Jobs** - Create afternoon jobs

### End of Day (4:00 PM)
1. **🚨❌ Incomplete** - Final completion check
2. **Calendar Views** - Visual check for tomorrow
3. **🏠 iTrip** - Special instructions for tomorrow

---

## 🤔 Potential Missing Views

Based on operational needs, consider adding:

### 1. "⏰ Today's Work" View
- Filter: Check-out Date = TODAY()
- Purpose: Focus only on today's jobs
- Benefit: Less scrolling than Upcoming

### 2. "🔴 Urgent Issues" View
- Filter: Same-day Turnover = true OR special flags
- Purpose: High-priority jobs needing attention
- Benefit: Never miss critical cleans

### 3. "💰 Billing Review" View
- Filter: Job Status = "Completed" last 7 days
- Purpose: Review completed work for billing
- Benefit: Easier payroll processing

### 4. "📊 Cleaner Performance" View
- Group By: Assignee
- Purpose: See each cleaner's metrics
- Benefit: Performance management

### 5. "🏠 No HCP Setup" View
- Filter: Property without HCP IDs
- Purpose: Properties needing setup
- Benefit: Onboarding new properties

---

## 💡 Pro Tips for View Usage

### Keyboard Shortcuts
- **Ctrl+F**: Quick search within view
- **Space**: Check/uncheck checkboxes
- **Ctrl+C/V**: Copy/paste between records

### Personal Customizations
- Hide fields you don't use
- Reorder columns for your workflow
- Create personal views for specific needs
- Use color coding for visual cues

### Efficiency Hacks
1. **Bookmark key views** in browser
2. **Set up view notifications** for changes
3. **Use batch operations** when possible
4. **Create view groups** for related views

---

## 📝 Your Homework Assignment

1. **Spend 30 minutes exploring each view**
   - Click through the filters
   - Understand what appears/disappears
   - Note questions about each view

2. **Track your daily usage for one week**
   - Which views do you use most?
   - Which views do you never use?
   - What information is hard to find?

3. **Identify missing information**
   - What questions can't you answer with current views?
   - What would make your job easier?
   - What fields would help you work faster?

4. **Create one personal view**
   - Start with "All View"
   - Add filters for your specific needs
   - Name it "Veronica's [Purpose]"

5. **Document three scenarios**
   - Write down three real problems you solve
   - Note which views you used
   - Identify what was difficult

---

## 🚀 Next Steps

After reviewing this guide:

1. **Practice the morning routine** with all views
2. **Ask questions** about anything unclear
3. **Suggest improvements** based on your experience
4. **Share pain points** that views don't address
5. **Propose new views** that would help

Remember: Views are tools to make your job easier. If a view doesn't help you, we should change it or create a better one!

---

*This guide is your reference manual. Keep it handy and annotate it with your own notes as you learn the system.*