# Daily Operational Scenarios for Property Management

**Version:** 2.0  
**Last Updated:** June 12, 2025  
**Purpose:** Comprehensive operational scenarios covering all aspects of property management operations - from routine scheduling to emergency situations, with real examples and detailed resolution steps

---

## 🚨 **Most Common Daily Scenarios (Top Priority)**

### 1. **Late Checkout Request from iTrip**
**Example:** Property at 5244 E Hartford Ave has checkout on June 22 at 10:00 AM, but guest requests 2:00 PM late checkout

**What Happens:**
- iTrip emails request for late checkout
- Existing job scheduled for 10:00 AM needs to be moved
- Next guest might be checking in same day (same-day turnover)

**Resolution Steps:**
1. Find reservation in Airtable (search by property address or date)
2. Update "Custom Service Time" to "2025-06-22 2:00 PM"
3. Click "Add/Update Schedule" button
4. Check if same-day turnover exists - may need to notify next guest

**Real Example:**
- Job ID: `job_0b2bf89c45594b35a7ccd9cefbc504c1`
- Original time: 10:00 AM → Changed to: 2:00 PM
- Sync Status updates to show new time

---

### 2. **Special Cleaning Instructions Need to Be Added**
**Example:** Owner requests deep clean of kitchen appliances for their arrival

**What Happens:**
- Email received with special instructions
- Job already created but needs updated service details
- Instructions must be added before cleaner arrives

**Resolution Steps:**
1. Find reservation in Airtable
2. Add instructions to "Service Line Custom Instructions" field (200 char limit)
3. If job already exists, instructions can only be updated directly in HCP
4. For future jobs, add instructions before clicking "Create Job"

**Real Example:**
- iTrip Report Info: "The owner is staying in their home. Please make sure it's extra clean and ready!"
- Service Line becomes: "Deep clean appliances - Turnover STR Next Guest June 23"

---

### 3. **Reservation Modified After Job Created**
**Example:** Guest changes checkout from June 16 to June 17

**What Happens:**
- System marks reservation as "Modified" status
- Existing job in HCP is now on wrong date
- Sync Status shows "Wrong Date"

**Resolution Steps:**
1. System automatically detects change (every 4 hours)
2. Find record with Sync Status = "Wrong Date"
3. Update "Final Service Time" to new checkout date + 10:00 AM
4. Click "Add/Update Schedule" button
5. Verify Sync Status changes to "Synced"

**Real Example:**
- Job: `job_5fa097ea775d4b438ae1de1a85f03a4a`
- Sync Details: "Schedule date doesn't match: expected 2025-06-17, found 2025-06-16"

---

### 4. **Same-Day Turnover Detected**
**Example:** Checkout at 2065 W 1st Pl on June 22, new guest checking in same day

**What Happens:**
- System auto-detects same-day turnover
- Sets early morning time (8:00 AM) for cleaning
- High priority - limited time window

**Resolution Steps:**
1. Filter Airtable for "Same-day Turnover" = true
2. Verify early morning schedule (8:00 AM default)
3. Assign experienced cleaner who can work quickly
4. Monitor job progress closely
5. Alert if running late - affects check-in

**Real Example:**
- Customer: Kathy Nelson property
- Service Line: "Turnover STR SAME DAY"
- Must complete by 2:00 PM for 3:00 PM check-in

---

### 5. **Job Not Completed Yesterday**
**Example:** Cleaner couldn't access property, job remains incomplete

**What Happens:**
- Job Status stays "In Progress" or "Scheduled"
- New guest arriving today
- Urgent rescheduling needed

**Resolution Steps:**
1. Check webhook logs for job status updates
2. Filter Airtable: Job Status != "Completed" AND Service Date = yesterday
3. Contact cleaner for explanation
4. Create urgent job for today morning
5. Notify property manager of delay

**Log Check Example:**
```bash
grep "job_763e1ad5e7334979af6caf6893c168a2" /home/opc/automation/src/automation/logs/webhook.log
```

---

## 📅 **Schedule Management Scenarios**

### 6. **Cleaner Needs to Reschedule**
**Example:** Assigned cleaner calls in sick, need replacement

**What Happens:**
- HCP shows assigned employee unavailable
- Need to reassign to available cleaner
- Time might need adjustment

**Resolution Steps:**
1. Check current assignment in "Assignee" field
2. In HCP, reassign to available cleaner
3. Webhook automatically updates Airtable
4. Monitor "Sync Date and Time" for confirmation

---

### 7. **Owner Stay Requires Special Handling**
**Example:** Property owner staying after guest checkout

**What Happens:**
- iTrip marks as "Owner Stay"
- Requires premium service level
- Often has specific requirements

**Resolution Steps:**
1. Look for "Owner Stay" in iTrip Report Info
2. Add to Service Line Custom Instructions: "Owner arriving - extra attention to detail"
3. Assign most experienced cleaner
4. Set appropriate time (usually 11:00 AM)

---

## 🔄 **Sync and System Issues**

### 8. **Job Shows "Not Created" But Should Exist**
**Example:** Reservation imported but job creation failed
**View to Use:** HCP Create Jobs (shows all ready for job creation)

**What Happens:**
- Sync Status = "Not Created"
- No Service Job ID present
- Cleaning not scheduled

**Resolution Steps:**
1. Verify property has HCP Customer ID and Address ID
2. Ensure Final Service Time is set
3. Click "Create Job & Sync Status"
4. If fails, check error in Sync Details

**Common Errors:**
- "Property missing HCP Customer ID"
- "Invalid service time format"

---

### 9. **Duplicate Jobs Created**
**Example:** Same reservation has multiple jobs in HCP

**What Happens:**
- Multiple Service Job IDs for same checkout
- Cleaner confusion
- Billing issues

**Resolution Steps:**
1. Identify all duplicate Job IDs
2. Keep job with correct schedule
3. Cancel duplicates in HCP
4. Update Airtable to reference correct job

---

## 🏠 **Property-Specific Scenarios**

### 10. **New Property Needs Setup**
**Example:** New Airbnb property added to portfolio

**What Happens:**
- Property imported but missing HCP links
- Jobs cannot be created
- No customer/address in HCP

**Resolution Steps:**
1. Create customer in HCP first
2. Add property address in HCP
3. Update Properties table with HCP IDs
4. Test job creation

---

### 11. **Property Access Issues**
**Example:** Door code changed, cleaner locked out

**What Happens:**
- Job marked "In Progress" but stuck
- Cleaner waiting at property
- Guest arriving soon

**Resolution Steps:**
1. Check iTrip Report Info for access details
2. Contact property manager for new code
3. Update HCP job notes with new access info
4. Notify cleaner immediately

---

## 📊 **Reporting and Analysis Scenarios**

### 12. **End of Day Completion Check**
**Example:** Verify all scheduled cleanings completed

**What Happens:**
- Need status of all today's jobs
- Identify any incomplete services
- Plan for tomorrow

**Resolution Steps:**
1. Filter: Service Date = Today
2. Check Job Status column
3. For non-completed, check webhook logs
4. Follow up with assigned cleaners
5. Update status manually if needed

---

### 13. **Weekly Schedule Overview**
**Example:** Review upcoming week's workload

**What Happens:**
- Assess cleaner availability
- Identify busy days
- Plan resource allocation

**Resolution Steps:**
1. Filter: Service Date = This Week
2. Group by date and cleaner
3. Look for overloaded days
4. Redistribute if needed
5. Alert cleaners of busy periods

---

## 💡 **Tips for Efficient Operations**

### Airtable Views for Quick Access:
1. **⏰❌ Incomplete** - Jobs that aren't finished yet
2. **⏰❓ Mismatch** - Schedule sync issues needing attention  
3. **⏰🗑️ Removed** - Canceled reservations to review
4. **⏰⚠️ Modified** - Reservations that changed after job creation
5. **⬆️🧹 Upcoming** - Future cleanings to prepare for
6. **🏠 iTrip** / **🏠 Evolve** - Filter by booking source
7. **HCP Create Jobs** - Reservations ready for job creation

### Quick Filters to Save Daily:
1. **Urgent Today**: `AND({Check-out Date} = TODAY(), {Job Status} != "Completed")`
2. **Sync Issues**: `{Sync Status} != "Synced"`
3. **Same Day Rush**: `AND({Same-day Turnover} = TRUE, {Check-out Date} >= TODAY())`
4. **Modified Reservations**: `AND({Status} = "Modified", {Service Job ID} != "")`
5. **No Job Created**: `AND({Final Service Time} != "", {Service Job ID} = "")`

### Daily Checklist:
- [ ] 8:00 AM - Check same-day turnovers
- [ ] 9:00 AM - Review sync issues
- [ ] 12:00 PM - Verify morning completions
- [ ] 3:00 PM - Check afternoon schedules
- [ ] 5:00 PM - End of day review

### Emergency Contacts:
- **System Issues**: Check logs in `/src/automation/logs/`
- **Webhook Issues**: Boris (for dev) or System Admin (for prod)
- **API Errors**: Restart airscripts-api service

---

## 🛠️ **Troubleshooting Quick Reference**

| Problem | First Check | Quick Fix |
|---------|------------|-----------|
| Job won't create | Property HCP IDs | Verify in Properties table |
| Wrong sync status | Sync Date and Time | Click "Create Job & Sync Status" |
| Schedule won't update | Custom Service Time format | Use YYYY-MM-DD HH:MM AM/PM |
| Webhook not updating | Environment (dev/prod) | Check correct webhook endpoint |
| Can't find reservation | Multiple search fields | Try address, date, guest name |

---

---

## 🚫 **Guest Issues and Complaints**

### 14. **Guest Reports Cleanliness Issues**
**Example:** Guest arrives to find property not properly cleaned, complains to iTrip

**What Happens:**
- Guest calls/emails with complaints
- Photos of issues sent
- Risk of bad review
- May need immediate re-clean

**Resolution Steps:**
1. Document complaint in HCP job notes
2. Contact assigned cleaner for explanation
3. If valid, dispatch cleaner immediately for re-clean
4. Create new "Quality Control Fix" job in HCP
5. Add note to cleaner's performance record
6. Follow up with guest after resolution

**Real Example:**
- Property: 3625 N 36th St
- Issue: "Bathroom not cleaned, trash left in kitchen"
- Resolution: Same cleaner returned within 2 hours
- Added to Service Line: "URGENT - Guest complaint re-clean"

---

### 15. **Guest Damage Discovered**
**Frequency:** 3-4 times weekly  
**Example:** Cleaner finds broken furniture, stained carpets, missing items

**What Happens:**
- Cleaner reports damage during service
- Need documentation for claim
- May affect next guest
- Requires immediate action

**Resolution Steps:**
1. Cleaner takes photos via HCP mobile app
2. Add detailed notes to job in HCP
3. Create "Damage Assessment" tag in Airtable
4. Notify property manager immediately
5. If severe, may need to relocate next guest
6. Document for security deposit claim

**Documentation Required:**
- Photos attached to HCP job
- Itemized damage list
- Estimated repair costs
- Previous condition photos

---

## 👷 **Cleaner Management Issues**

### 16. **Cleaner No-Show (No Notice)**
**Example:** Cleaner doesn't arrive, doesn't answer phone

**What Happens:**
- Job remains "Scheduled" in HCP
- No webhook updates received
- Guest arriving in hours
- Emergency coverage needed

**Resolution Steps:**
1. Check HCP for last GPS location (if available)
2. Call backup cleaners immediately
3. Reassign job in HCP to available cleaner
4. Update expected arrival time
5. Add "No-show" note to original cleaner's record
6. Consider temporary suspension

**Emergency Protocol:**
```bash
# Quick check for cleaner's other jobs today
grep "employee_name" /home/opc/automation/src/automation/logs/webhook.log | grep "$(date +%Y-%m-%d)"
```

---

### 17. **Quality Control Failure**
**Frequency:** 4-5 times weekly  
**Example:** Random inspection finds substandard cleaning

**What Happens:**
- Inspector notes multiple issues
- Job marked "Completed" but inadequate
- Pattern of quality problems
- May need retraining

**Resolution Steps:**
1. Create "Quality Issue" tag in cleaner's profile
2. Document specific failures with photos
3. Schedule re-clean if guest arriving
4. Implement cleaner coaching plan:
   - Review standards checklist
   - Shadow experienced cleaner
   - Follow-up inspection required
5. Track improvement over 30 days

**Quality Metrics to Track:**
- Items missed (checklist)
- Time to complete
- Guest complaints
- Re-clean frequency

---

## 🏢 **Property Maintenance Scenarios**

### 18. **Emergency Maintenance During Cleaning**
**Example:** Cleaner discovers AC not working, water leak

**What Happens:**
- Immediate repair needed
- Guest arriving today
- Cleaning can't be completed
- Multiple vendors involved

**Resolution Steps:**
1. Cleaner reports via HCP mobile app
2. Add "URGENT MAINTENANCE" to job notes
3. Contact maintenance vendor immediately
4. Adjust cleaning schedule around repair
5. May need to delay guest check-in
6. Update iTrip with status
7. Coordinate cleaner return after repair

**Common Emergency Issues:**
- No hot water
- AC/Heat failure  
- Plumbing leaks
- Appliance breakdowns
- Lock/access failures

---

### 19. **Supply Shortage at Property**
**Frequency:** 5-6 times weekly  
**Example:** Cleaner arrives, no clean towels/sheets available

**What Happens:**
- Can't complete turnover
- Laundry service delayed
- Need emergency supplies
- Multiple properties affected

**Resolution Steps:**
1. Check supply inventory in HCP job notes
2. Dispatch runner with emergency supplies
3. Create "Supply Run" job in HCP
4. Bill as additional line item:
   ```
   Name: "Emergency Supply Delivery"
   Kind: "labor"
   Unit Price: $25
   ```
5. Update property's par levels
6. Schedule laundry service follow-up

**Supply Tracking:**
- Towels needed vs available
- Sheet sets by bed size
- Cleaning supplies status
- Paper products inventory

---

## 💰 **Billing and Payment Issues**

### 20. **Disputed Cleaning Charge**
**Frequency:** 3-4 times monthly  
**Example:** Property owner questions why cleaning took 4 hours instead of 2

**What Happens:**
- Invoice disputed in HCP
- Need to justify time/charges
- May affect payment
- Requires documentation

**Resolution Steps:**
1. Pull job details from HCP
2. Review cleaner's time logs
3. Check job notes for complications:
   - Extra dirty conditions
   - Additional requests
   - Supply runs needed
4. Compile evidence:
   - Before/after photos
   - Detailed task list
   - Time stamps
5. Adjust billing if warranted
6. Document resolution in HCP

---

### 21. **Wrong Service Level Billed**
**Example:** Deep clean performed but regular clean billed

**What Happens:**
- Revenue loss
- Cleaner underpaid
- Invoice needs correction
- Pattern may indicate training issue

**Resolution Steps:**
1. Compare Service Line to actual work
2. Review line items in HCP:
   ```javascript
   // Check line items
   get_job_line_items(job_id="job_123")
   ```
3. Update line items to reflect actual service:
   ```javascript
   update_job_line_item(
     job_id="job_123",
     line_item_id="li_456",
     name="Deep Clean - 3BR/2BA",
     unit_price=175
   )
   ```
4. Issue credit/additional charge
5. Update cleaner payroll

---

## 🗓️ **Complex Scheduling Scenarios**

### 22. **Multi-Property Same Cleaner Conflict**
**Example:** Same cleaner assigned to properties 10 miles apart with 30-min gap

**What Happens:**
- Physically impossible schedule
- One property will be late
- Cleaner stressed
- Guest impact likely

**Resolution Steps:**
1. Use HCP route optimization
2. Check drive times between properties
3. Reassign based on geography:
   - North side cleaners
   - South side cleaners
   - Central corridor cleaners
4. Adjust times allowing travel:
   - 30 min for 10+ miles
   - 15 min for 5-10 miles
5. Update both jobs in sequence

---

### 23. **Guest Early Arrival During Cleaning**
**Example:** Guest shows up at 2 PM while cleaning in progress

**What Happens:**
- Cleaner still working
- Guest wants immediate access
- Awkward situation
- Cleaning may be rushed

**Resolution Steps:**
1. Cleaner alerts via HCP mobile
2. Contact guest to manage expectations
3. Options:
   - Guest waits in common area
   - Provide estimated completion
   - Offer nearby amenity (coffee shop)
4. Prioritize essential areas:
   - Bathroom first
   - Bedroom next
   - Kitchen/living last
5. Note early arrival in job

---

## 🌪️ **Emergency and Weather Scenarios**

### 24. **Severe Weather Prevents Access**
**Example:** Flash flooding blocks road to mountain properties

**What Happens:**
- Multiple properties inaccessible
- Cleaners can't reach location
- Guests may be arriving
- Safety concerns paramount

**Resolution Steps:**
1. Check weather alerts for affected areas
2. Contact all assigned cleaners - safety first
3. Bulk reschedule affected jobs:
   - Filter by zip code/area
   - Move to next safe window
4. Notify property managers
5. Contact arriving guests with options:
   - Delay check-in
   - Offer alternate property
   - Full refund if needed
6. Document as "Weather - Act of God"

---

### 25. **Power Outage at Property**
**Example:** Area power outage, can't clean properly

**What Happens:**
- No lights for detailed cleaning
- No vacuum/equipment use
- Security system may be down
- Can't verify completion

**Resolution Steps:**
1. Check utility company outage map
2. Get estimated restoration time
3. If short (< 2 hours):
   - Do what's possible
   - Return when power restored
4. If long (> 4 hours):
   - Reschedule entirely
   - Notify next guest
5. Add line item for return trip:
   ```
   Name: "Return Trip - Power Outage"
   Kind: "labor"
   Unit Price: $50
   ```

---

## 📦 **Lost and Found Management**

### 26. **Guest Items Left Behind**
**Example:** Cleaner finds iPhone, jewelry, medications

**What Happens:**
- Valuable/personal items found
- Guest may be traveling
- Liability concerns
- Need secure handling

**Resolution Steps:**
1. Cleaner photos item in place
2. Secure item immediately:
   - Medications: Urgent contact
   - Electronics: Power off, secure
   - Valuables: Document and lock
3. Create Lost & Found record:
   - Property address
   - Item description
   - Found date/time
   - Cleaner name
4. Contact previous guest via iTrip
5. Arrange return shipping:
   - Guest pays shipping
   - Get tracking number
   - Document sent date
6. 30-day hold if unclaimed

**High Priority Items:**
- Medications
- IDs/Passports
- Electronics
- Jewelry
- Car keys

---

## 📊 **Performance and Training Issues**

### 27. **New Cleaner First Solo Assignment**
**Example:** Newly trained cleaner doing first turnover alone

**What Happens:**
- Higher error risk
- May take longer
- Needs monitoring
- Quality check required

**Resolution Steps:**
1. Assign simpler property first:
   - 1-2 bedroom
   - Standard turnover
   - Not same-day
2. Schedule with buffer time
3. Have supervisor on standby
4. Require photos of completed work:
   - Each room
   - Problem areas
   - Supply levels
5. Follow-up inspection within 2 hours
6. Provide immediate feedback
7. Graduate to complex properties after 5 successful solos

---

### 28. **Cleaner Requests Schedule Change**
**Example:** Cleaner has appointment, needs to swap shifts

**What Happens:**
- Multiple jobs need reassignment
- Other cleaners affected
- Domino effect possible
- Fair distribution needed

**Resolution Steps:**
1. List cleaner's assignments for requested date
2. Find willing swap partners
3. Check skill match:
   - Property knowledge
   - Quality rating
   - Travel distance
4. Update all affected jobs in HCP
5. Confirm with all parties
6. Monitor day-of for issues

---

## 🔄 **System Integration Failures**

### 29. **Webhook Stops Updating**
**Example:** HCP updates not reaching Airtable

**What Happens:**
- Job statuses outdated
- Sync Status incorrect
- Manual updates needed
- May miss completions

**Resolution Steps:**
1. Check webhook health:
   ```bash
   # Check last webhook activity
   tail -n 50 /home/opc/automation/src/automation/logs/webhook.log
   ```
2. Verify webhook service running:
   ```bash
   sudo systemctl status webhook
   ```
3. Test webhook endpoint:
   ```bash
   curl -X POST https://servativ.themomentcatchers.com/webhooks/hcp \
     -H "Content-Type: application/json" -d '{"test":true}'
   ```
4. If down, restart service:
   ```bash
   sudo systemctl restart webhook
   ```
5. Manually sync affected jobs

---

### 30. **Bulk Import Creates Duplicates**
**Example:** CSV import creates duplicate reservations

**What Happens:**
- Same checkout multiple times
- Duplicate jobs risk
- Cleaner confusion
- Billing errors

**Resolution Steps:**
1. Identify pattern:
   - Same property + date
   - Same confirmation number
   - Different import times
2. Filter Airtable for duplicates:
   ```
   AND(
     {Property} = {Property},
     {Checkout Date} = {Checkout Date},
     RECORD_ID() != RECORD_ID()
   )
   ```
3. Keep newest record (latest data)
4. Cancel duplicate HCP jobs
5. Add import timestamp checking

---

*This document covers the most common scenarios Veronica encounters daily. Each scenario includes real-world examples and step-by-step resolutions. Last updated with 30 comprehensive operational scenarios covering all aspects of property management operations.*