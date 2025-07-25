# Operational Scenarios by Airtable View

**Version:** 1.0  
**Last Updated:** June 12, 2025  
**Purpose:** Daily operational scenarios organized by Airtable views, showing how Veronica uses each view to manage property cleaning services

---

## 🎯 **Daily Workflow by Views**

### Morning Routine (8:00 AM)
1. Start with **⏰❌ Incomplete** view
2. Check **⏰❓ Mismatch** for sync issues  
3. Review **⏰🗑️ Removed** for canceled jobs
4. Scan **⏰⚠️ Modified** for changes
5. Preview **⬆️🧹 Upcoming** for today's work

---

## ⏰❌ **Incomplete View - Jobs Not Finished**

### **Purpose**: Shows jobs from past dates that aren't marked "Completed" - these need immediate attention

### **Scenario 1: Job Still Shows "In Progress" from June 10**
**Real Example:** 2065 W 1st Pl, Mesa - Kathy Nelson property

**What Happens:**
- Job `job_2257dc087ad94e2b9a9ca57065bca91c` for June 10 checkout
- Status shows "In Progress" - cleaner started at 8:13 AM
- It's now June 12 and job not marked complete
- Next guest already checked in

**Resolution Using This View:**
1. Open **⏰❌ Incomplete** view first thing in morning
2. See record ID 31690 with "On My Way Time" from June 12 at 8:13 AM
3. Call Laundry User (assignee) - confirm if cleaning was completed
4. If complete, update HCP status to "Completed"
5. Add note: "Cleaner confirmed completion, app issue prevented status update"

**Why This View Helps:** Catches jobs stuck in progress before complaints arise

---

### **Scenario 2: Yesterday's Job Still "Scheduled"** 
**Real Example:** 5950 N 78th St #123, Scottsdale - iTrip property

**What Happens:**
- Job `job_4107597a416949b8b3870231a299c829` scheduled for June 10
- Special note: "Owner Stay - The owner is staying in their home"
- Job still shows "Scheduled" status on June 12
- Owner already in property expecting clean space

**Resolution:**
1. Filter **⏰❌ Incomplete** view for past checkouts
2. See critical note: "Be sure to send charges for it in Slack ask Phil how much"
3. Notice access details: "Gate code #0518; Door Code 75736"
4. Call cleaner urgently - may have had access issues
5. If not cleaned, dispatch immediately with apology to owner

---

## ⏰❓ **Mismatch View - Schedule Sync Issues**

### **Purpose**: Identifies jobs where HCP schedule doesn't match Airtable expectations

### **Scenario 3: Job Scheduled for Wrong Time**
**Real Example:** 6536 E 5th St, Scottsdale - Mandie Brice property

**What Happens:**
- Job `job_617778dbd0774b789fb84d5515427b3c` for July 20
- Airtable expects 10:15 AM service
- HCP shows 12:05 PM scheduled
- Schedule Sync Details: "⚠️ TIME MISMATCH: Airtable shows 10:15 AM but HCP shows 12:00 PM"

**Resolution Using This View:**
1. Open **⏰❓ Mismatch** view
2. See Sync Status = "Wrong Time" for record ID 31696
3. Check if late checkout was approved - verify with property notes
4. Update Custom Service Time to match HCP if change was intentional
5. Or click "Add/Update Schedule" to fix HCP if error

**Why This View Helps:** Prevents cleaners arriving at wrong times

---

## ⏰🗑️ **Removed View - Canceled Reservations with Active Jobs**

### **Purpose**: Shows canceled reservations that have jobs in HCP needing cancellation

### **Scenario 4: Guest Canceled But Job Still Active**
**Real Example:** 19942 N 78th Ln, Glendale - Ywxem Barrios property

**What Happens:**
- Airbnb reservation for June 10-14 canceled (record ID 32074)
- Job `job_fff5a658037f4ede93f3be9e48017d8d` already created
- Job Status still shows "Scheduled" in HCP
- Cleaner assigned (Laundry User) for June 14 at 10:15 AM
- Next guest arriving June 17 - still needs cleaning

**Resolution Using This View:**
1. Open **⏰🗑️ Removed** view each morning
2. See canceled reservation WITH Service Job ID
3. Click HCP job link to check current status
4. Cancel the June 14 job in HCP
5. Notify assigned cleaner not to go
6. Verify property still needs cleaning for June 17 arrival

**Why This View Helps:** Prevents cleaners from showing up to canceled reservations

---

### **Scenario 5: Removed View Shows Empty - Good News!**
**Real Example:** Only one removed reservation with active job today

**What Happens:**
- Most days the Removed view might be empty
- This means no active jobs need canceling
- Removed reservations without jobs don't appear here
- System working as designed

**Resolution:**
1. Check **⏰🗑️ Removed** view as part of morning routine
2. If empty, move on to next view
3. If records appear, each one needs HCP cancellation
4. After canceling in HCP, record disappears from this view
5. Document any cancellation fees if applicable

---

## ⏰⚠️ **Modified View - Changed Reservations**

### **Purpose**: Tracks reservations that changed after import (Status = "Modified")

### **Scenario 6: Same-Day Turnover Schedule Adjusted**
**Real Example:** 5244 E Hartford Ave, Scottsdale - iTrip property

**What Happens:**
- Job `job_0b2bf89c45594b35a7ccd9cefbc504c1` for June 22
- Status = "Modified" (record ID 32467)
- Same-day Turnover = true
- iTrip Report Info: "Owner Stay - The owner is staying in their home"
- Schedule was updated to 10:00 AM for same-day cleaning

**Resolution Using This View:**
1. **⏰⚠️ Modified** view shows all changed reservations
2. See it's already synced: "✅ Schedule is in sync"
3. Note special requirement: "Owner arriving - extra clean"
4. Verify experienced cleaner assigned for same-day + owner
5. Set reminder to check completion by noon

**Why This View Helps:** Tracks all changes that happened after initial import

---

### **Scenario 7: Extended Stay Date Changed**
**Real Example:** 7714 E Wilshire Dr, Scottsdale - Long-term stay modified

**What Happens:**
- Original checkout June 17, extended to July 16 (record ID 32602)
- Job `job_94a33105af854bd79fd97a4d9a5f6f8b` exists
- Status = "Modified" after date change
- Service still scheduled for original date (June 17)

**Resolution:**
1. Open **⏰⚠️ Modified** view
2. See checkout extended by a month
3. Decide: interim cleaning or wait until July?
4. If interim clean, keep June 17 service
5. Create additional job for July 16 final clean

---

## ⬆️🧹 **Upcoming View - Future Work Planning**

### **Purpose**: Shows all scheduled work for planning and preparation

### **Scenario 8: Planning Tomorrow's Routes**
**Real Example:** 15 cleanings scheduled for June 13

**What Happens:**
- Need to optimize cleaner routes
- Some properties are 20+ miles apart
- Multiple same-day turnovers

**Resolution Using This View:**
1. Open **⬆️🧹 Upcoming** filtered for tomorrow
2. Group by assignee to see workload
3. Notice 3 properties in North Scottsdale for one cleaner
4. Reassign South Phoenix property to different cleaner
5. Adjust times to account for drive distances

**Why This View Helps:** Enables proactive route planning

---

## 🏠 **Source-Specific Views (iTrip/Evolve)**

### **Purpose**: Filter by booking source (Entry Source) for platform-specific needs

### **Scenario 9: iTrip Special Instructions Need Attention**
**Real Example:** 6051 E Campo Bello Dr, Scottsdale - Timer check required

**What Happens:**
- iTrip Report Info shows: "MUST CHECK THE TIMER TO PATIO LIGHTS"
- Job `job_ca6dcb312994401bb1d92fed763fce63` for June 22
- Owner stay with specific requirement
- Critical instruction buried in notes

**Resolution Using iTrip View:**
1. Open **🏠 iTrip** view
2. Filter for upcoming checkouts
3. See record ID 32379 with special timer instruction
4. Add to cleaner checklist: "CHECK PATIO LIGHT TIMER - CRITICAL"
5. Set reminder to verify timer was checked after service

**Why This View Helps:** Catches platform-specific requirements that might be missed

---

### **Scenario 10: iTrip Owner Stay Premium Service**
**Real Example:** Multiple properties showing "Owner Stay" in June

**What Happens:**
- iTrip marks several June checkouts as "Owner Stay"
- 5244 E Hartford Ave: "Owner is staying - extra clean"
- 6051 E Campo Bello Dr: Same owner message
- These require premium service level

**Resolution Using iTrip View:**
1. Open **🏠 iTrip** view
2. Search iTrip Report Info for "Owner Stay"
3. Find all owner arrivals this week
4. Assign most experienced cleaners
5. Add premium supplies to these jobs
6. Set quality check reminders

---

### **Scenario 11: iTrip Hot Tub Property Special Care**
**Real Example:** 8334 E Whispering Wind Dr - Hot tub maintenance

**What Happens:**
- iTrip Report Info shows: "*Hot Tub" at end
- Job for June 14 (record ID 32359)
- Lockbox Code: 1290, TV: Dish Network
- Hot tub requires special cleaning protocol

**Resolution:**
1. Filter **🏠 iTrip** view by upcoming dates
2. Search notes for "Hot Tub" indicators
3. Add to job: "Check hot tub cover, clean surrounding area"
4. Verify cleaner knows hot tub protocols
5. May need extra time allocation

---

## 📋 **Blocks View - Owner/Maintenance Management**

### **Purpose**: Shows all blocked periods (Entry Type = "Block") for proactive service offerings

### **Scenario 11: 5-Day Advance Block Cleaning Offers**
**Real Example:** 4241 N 87th Pl, Scottsdale - VRBO block June 12-15

**What Happens:**
- Block showing for Anthony Guillory property (record ID 31934)
- Entry Type = "Block", Service Type = "Needs Review"
- No job created yet (Sync Status = "Not Created")
- Opportunity for mid-stay cleaning offer

**Daily Block Review Process:**
1. Open **Blocks** view each morning
2. Filter for blocks starting within 5 days
3. See block at 4241 N 87th Pl starting today (June 12)
4. Send message: "Hi, I see you have a block June 12-15. Would you like us to schedule a mid-stay refresh?"
5. If yes, create job with Service Type = "Refresh"
6. Add note: "Block period - coordinate with occupant"

**Why This Matters:** Converts non-revenue blocks into cleaning opportunities

---

### **Scenario 12: Multiple Blocks at Same Property**
**Real Example:** 825 W Monterey Pl, Chandler - Ashley Pritchett property

**What Happens:**
- Multiple VRBO blocks: June 29-30, July 14-15, August 21-22
- All show Entry Type = "Block", no jobs created
- Pattern suggests regular maintenance or owner use

**Resolution:**
1. Check **Blocks** view filtered by property
2. See recurring pattern at 825 W Monterey Pl
3. Reach out once: "I notice regular blocks at your property. Would you like standing cleaning orders?"
4. Set up recurring service if desired
5. Create template for future blocks

---

## 🏠 **Property Filter Usage Scenarios**

### **Purpose**: Filter by specific property for focused management

### **Scenario 13: Property-Specific Issue Investigation**
**Real Example:** Multiple complaints about 26208 N 43rd St #73

**What Happens:**
- Three guest complaints in two weeks
- Need to review all services at property
- May need quality control visit

**Resolution Using Property Filter:**
1. Filter any view by Property = "26208 N 43rd St #73"
2. Sort by Service Date descending
3. Review last 10 cleanings:
   - Check completion times
   - Read cleaner notes
   - Look for pattern in assignees
4. Schedule inspection visit
5. Consider cleaner retraining

**Why Property Filter Helps:** Isolates property-specific patterns

---

### **Scenario 14: Property Access Update**
**Real Example:** Door code changed at multiple units

**What Happens:**
- Property manager updates access codes
- Multiple upcoming reservations affected
- Need to update all future jobs

**Resolution:**
1. Filter by Property contains "N 43rd St"
2. Filter by Service Date >= TODAY()
3. Find all upcoming services
4. Bulk update access instructions
5. New code: "GARAGE: 1847 (changed 6/12)"

---

## 🆕 **HCP Create Jobs View**

### **Purpose**: Shows reservations with no Service Job ID but have Final Service Time - ready for job creation

### **Scenario 15: Block Needs Decision Before Job Creation**
**Real Example:** 825 W Monterey Pl, Chandler - VRBO block July 14-15

**What Happens:**
- Block for Ashley Pritchett property (record ID 32156)
- Has Final Service Time set (July 15 at 10:15 AM)
- Entry Type = "Block", Service Type = "Needs Review"
- No job created yet - needs service decision

**Resolution Using This View:**
1. Open **HCP Create Jobs** view
2. Filter for Entry Type = "Block"
3. See multiple blocks needing review
4. Contact property owner: "Do you want cleaning after your July 14-15 stay?"
5. If yes, change Service Type from "Needs Review" to "Turnover"
6. Then click "Create Job & Sync Status"

**Why This View Helps:** Catches blocks that need service decisions before job creation

---

### **Scenario 16: Future Reservation Ready for Early Job Creation**
**Real Example:** 11367 N 122nd St, Scottsdale - August 5-8 stay

**What Happens:**
- Airbnb reservation for August checkout (record ID 32290)
- Already has Final Service Time and next guest info
- Service Line Description: "Turnover STR Next Guest September 8"
- Owner wants jobs created early for planning

**Resolution:**
1. **HCP Create Jobs** view shows future reservations
2. See it's ready with all required fields
3. Property has HCP Customer/Address IDs
4. Click "Create Job & Sync Status"
5. Job created 2 months in advance for scheduling

---

## 📅 **Calendar View Usage**

### **Purpose**: Visual schedule management

### **Scenario 16: Weekly Schedule Conflict Resolution**
**Real Example:** Cleaner has 5 jobs on Thursday

**What Happens:**
- One cleaner overloaded
- Jobs spread across valley
- Timing will be impossible

**Resolution Using Calendar View:**
1. Open **Calendar - This Week** view
2. Visual shows Thursday clustering
3. Drag one job to different cleaner
4. Adjust times to allow travel
5. Confirm changes sync to HCP

**Why Calendar Helps:** Visual scheduling prevents conflicts

---

## 💡 **Pro Tips for View Management**

### Quick View Shortcuts:
1. **Start each day**: ⏰❌ Incomplete → ⏰❓ Mismatch → ⏰🗑️ Removed
2. **Mid-day check**: ⏰⚠️ Modified → ⬆️🧹 Upcoming (tomorrow)
3. **End of day**: ⏰❌ Incomplete → Calendar view for tomorrow

### View Combinations:
- **Same-day turnovers**: ⬆️🧹 Upcoming + filter "Same-day Turnover" = true
- **Problem properties**: Any view + Property filter for patterns
- **Platform issues**: 🏠 iTrip or 🏠 Evolve + Status filters

### Efficiency Hacks:
1. Save personal view filters for common searches
2. Use color coding to highlight urgent items
3. Group by Assignee in upcoming view for route planning
4. Sort by Sync Date and Time to see latest updates

---

## 🚨 **When to Use Which View**

| Situation | Primary View | Secondary View |
|-----------|--------------|----------------|
| Morning check | ⏰❌ Incomplete | ⏰❿ Mismatch |
| Schedule issues | ⏰❿ Mismatch | Calendar |
| Cancellations | ⏰🗑️ Removed | ⬆️🧹 Upcoming |
| Guest changes | ⏰⚠️ Modified | Property filter |
| Route planning | ⬆️🧹 Upcoming | Calendar |
| Platform requests | 🏠 iTrip/Evolve | Property filter |
| Owner services | Blocks | 🏠 Evolve |
| Job creation | HCP Create Jobs | ⏰❌ Incomplete |
| Quality issues | Property filter | ⏰❌ Incomplete |

---

## 📊 **Real Examples Summary**

### Jobs Needing Immediate Attention (June 12, 2025):
1. **2065 W 1st Pl** - Job still "In Progress" from June 10
2. **5950 N 78th St #123** - Owner stay job still "Scheduled" 
3. **6536 E 5th St** - July job has wrong time (12:05 PM vs 10:15 AM)

### Upcoming Special Requirements:
1. **6051 E Campo Bello Dr** - Must check patio light timer (June 22)
2. **5244 E Hartford Ave** - Same-day turnover + owner stay (June 22)
3. **8334 E Whispering Wind Dr** - Hot tub property (June 14)

### Blocks Needing Outreach:
1. **4241 N 87th Pl** - VRBO block June 12-15 (today!)
2. **825 W Monterey Pl** - Multiple blocks (June 29, July 14, Aug 21)
3. **3455 E Sharon Dr** - Removed block, no action needed

---

*This guide uses real examples from your dev environment to show exactly how each view helps manage daily operations. All property addresses, job IDs, and dates are actual data from June 12, 2025.*