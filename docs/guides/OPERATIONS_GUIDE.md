# Veronica's Complete Operations Guide
## From Manual Chaos to Automated Efficiency: Your New Property Management Workflow

### 🎯 **Welcome to Your New Reality**

**What You Used To Do** (The Old Way):
- ✋ Manually check 100+ FastMail calendar groups daily
- ✋ Download and process iTrip emails manually every day
- ✋ Manually scrape Evolve website property by property
- ✋ Create HousecallPro jobs one by one manually
- ✋ Track changes across multiple systems with no sync
- ✋ Constantly worry about missing reservations or schedule conflicts

**What Happens Automatically Now** (The New Way):
- ✅ **Every 4 Hours**: 246 ICS feeds processed automatically
- ✅ **Real-Time**: iTrip emails forwarded and CSVs processed instantly via CloudMailin
- ✅ **Every 4 Hours**: Evolve website scraped automatically for all properties
- ✅ **Real-Time**: HousecallPro jobs created via API with proper templates
- ✅ **Real-Time**: Status synced between all systems via webhooks
- ✅ **Automatic**: Same-day turnovers, overlaps, and conflicts detected

**Your New Role**: Exception Handler & Quality Assurance Specialist
- 🎯 Monitor automated processes for issues
- 🎯 Handle special cases (owner stays, long-term guests, maintenance)
- 🎯 Resolve sync issues between systems
- 🎯 Manage schedule conflicts and same-day turnovers
- 🎯 Provide quality oversight and customer service

---

## 📅 **DAILY WORKFLOW: Your New Morning Routine**

### **9:00 AM - Morning System Check** (15 minutes)

#### **STEP 1: Daily Operations Dashboard** 🏠
**Purpose**: Your mission control center - see everything needing attention

**What to do:**
1. Open Airtable → Reservations table → **"Daily Operations Dashboard"** view
2. Look for color-coded items:
   - 🔴 **Red items** = Sync issues (URGENT - fix first)
   - 🟡 **Yellow items** = New jobs need creation
   - 🟢 **Green items** = Everything synced properly

**Quick scan checklist:**
- Any red sync issues? → Fix immediately using Add/Update Schedule button
- Any yellow new jobs? → Add to Job Creation Queue for processing
- Any same-day turnovers today? → Check for special timing requirements

---

#### **STEP 2: Job Creation Queue** 🔧
**Purpose**: Create HousecallPro jobs for new reservations

**What to do:**
1. Switch to **"Job Creation Queue"** view
2. Filter for today's and tomorrow's checkouts
3. Review any custom service line instructions needed:
   - Long-term guests (>2 weeks) → Add "Long-term guest checkout"
   - Special requests → Add specific instructions
4. Click **"Create Job & Sync Status"** button for each reservation
5. Monitor for errors:
   - ❌ "Property missing HCP Customer ID" → Add property to Properties table first
   - ❌ "Template not found" → Use default turnover template
   - ✅ Success → Service Job ID appears automatically

**Pro tip**: Hold Ctrl+Click to open multiple job creation buttons in new tabs for efficiency

---

#### **STEP 3: Sync Issues Monitor** ⚠️
**Purpose**: Fix timing discrepancies between source data and HousecallPro

**Priority order:**
1. 🔴 **"Wrong Date"** - Most critical (service scheduled on wrong day)
2. 🟠 **"Wrong Time"** - Important (service at wrong time)
3. 🟡 **"Not Created"** - Needs job creation

**Resolution process:**
1. Open **"Sync Issues Monitor"** view
2. For each issue:
   - Compare **"Final Service Time"** vs **"Schedule Service Time"**
   - If **"Custom Service Time"** needed → Enter specific time
   - Click **"Add/Update Schedule"** button
   - Verify **"Sync Status"** changes to "Synced"

**Common scenarios:**
- Same-day turnover arrived late → Service time should be 10:00 AM (not 10:15 AM)
- Owner extended checkout → Use Custom Service Time for delayed service
- Multiple services same day → Stagger times (10:00 AM, 2:00 PM, etc.)

---

#### **STEP 4: Incomplete Jobs Tracker** 🚨
**Purpose**: Follow up on yesterday's unfinished work

**What to look for:**
- Jobs scheduled yesterday still showing "In Progress" or "Scheduled"
- Missing "Job Completed Time" for yesterday's services
- Assignees who didn't mark jobs complete

**Action steps:**
1. Check **"Incomplete Jobs Tracker"** view
2. Contact assignees directly for status updates
3. If job actually completed → Ask assignee to mark complete in HousecallPro
4. If job delayed → Reschedule in HousecallPro and note reason
5. If job cancelled → Mark as cancelled and handle customer communication

---

### **10:00 AM - Exception Handling** (20 minutes)

#### **STEP 5: Blocks Needing Review** 🔍
**Purpose**: Handle owner stays, maintenance blocks, and special situations

**Process:**
1. Open **"Blocks Needing Review"** view (Kanban style)
2. For each card in "Needs Review" column:

**Owner Stays:**
- Check if cleaning needed at end of stay
- If YES → Change Service Type to "Turnover" 
- If NO → Change Service Type to "Canceled"
- Add notes about owner preferences

**Maintenance Blocks:**
- Check if cleaning needed after maintenance
- Coordinate with maintenance schedule
- Usually change to "Canceled" unless specifically requested

**Long-term Reservations (>2 weeks):**
- Automatically flagged for review
- Add "Long-term guest checkout" to Custom Service Line Instructions
- Consider special cleaning requirements

3. Drag cards to appropriate columns to update Service Type

---

#### **STEP 6: Same Day Turnovers** ⚡
**Purpose**: Special attention for properties with tight turnaround times

**Critical timing:**
- Checkout service: **10:00 AM** (earlier than normal 10:15 AM)
- Check-in prep: Usually handled by checkout service
- Monitor closely for delays

**Process:**
1. Open **"Same Day Turnovers"** view
2. Verify service time is 10:00 AM (not 10:15 AM)
3. Check assignee capacity - can they handle tight turnaround?
4. Add priority notes: "SAME DAY TURNOVER - Complete by 2:00 PM"
5. Monitor throughout day for completion

**Red flags:**
- Assignee has multiple jobs same day
- Property has special challenges (large, complex)
- Previous delayed service at same property

---

### **10:30 AM - Change Management** (15 minutes)

#### **STEP 7: Recent Changes Monitor** 📈
**Purpose**: Handle modifications and cancellations from last 48 hours

**What to check:**
1. Open **"Recent Changes Monitor"** view
2. Review each "Modified" or "Removed" status item:

**Modified Reservations:**
- Date changed → Check if service already scheduled, reschedule if needed
- Guest changed → Update contact information in HousecallPro
- Duration changed → May affect service type (short stays vs long stays)

**Removed Reservations:**
- Cancellation → Cancel corresponding HousecallPro job
- Booking error → Verify with property manager before cancelling

**Action steps:**
- If service job exists → Click "Add/Update Schedule" to sync changes
- If job needs cancellation → Cancel in HousecallPro manually
- If major changes → Contact property manager for confirmation

---

## 📅 **WEEKLY WORKFLOW: Strategic Planning**

### **Monday Morning - Weekly Overview** (30 minutes)

#### **Long-term Guests Review**
1. Open **"Long-term Guests"** view
2. Review all stays >2 weeks checking out this week
3. Verify Custom Service Line Instructions include "Long-term guest checkout"
4. Consider special requirements:
   - Extra cleaning time needed
   - Assignee with experience in deep cleaning
   - Special equipment or supplies

#### **Service Completion Analysis**
1. Open **"Service Completion Report"** view
2. Review last week's completion rates by assignee
3. Identify any patterns:
   - Consistently late completions → Scheduling issue?
   - Missed jobs → Training need?
   - Customer complaints → Quality issue?

#### **Property Management Health Check**
1. Open **"Property Management Hub"** view (Properties table)
2. Verify all properties have:
   - HCP Customer ID
   - HCP Address ID  
   - Appropriate job templates
3. Add any missing properties from new bookings

---

## 🚨 **EMERGENCY PROCEDURES**

### **System Down Scenarios**

#### **Complete System Failure**
**Symptoms**: No data updating, automation stopped, can't access Airtable
**Action**:
1. Switch to manual backup mode immediately
2. Check latest CSV files in email
3. Create HousecallPro jobs manually for today's checkouts
4. Document all manual actions for later sync
5. Contact technical support: [emergency contact]

#### **Sync Failures (Mass Issues)**
**Symptoms**: All jobs showing "Wrong Date" or "Wrong Time"
**Action**:
1. Do NOT click mass "Add/Update Schedule" buttons
2. Check one property manually in HousecallPro
3. Document the pattern (all times off by X hours?)
4. Contact technical support with pattern details
5. Wait for fix before mass correction

#### **HousecallPro API Down**
**Symptoms**: "Create Job" buttons not working, sync failing
**Action**:
1. Document all reservations needing jobs
2. Create jobs manually in HousecallPro
3. When system recovers, manually add Service Job IDs to Airtable
4. Run sync to connect records

### **Property Setup Issues**

#### **New Property Missing from System**
**Symptoms**: Reservation appears but property not found
**Action**:
1. Open Properties table
2. Add new property record:
   - Property Name (exact match from reservation)
   - HCP Customer ID (from existing HousecallPro customer)
   - HCP Address ID (from HousecallPro address)
   - Job templates (copy from similar property)
3. Reprocess reservation after property setup

#### **Customer Missing from HousecallPro**
**Symptoms**: "Customer not found" error during job creation
**Action**:
1. Create customer in HousecallPro first
2. Add property address to customer
3. Update Properties table with new HCP Customer ID and Address ID
4. Retry job creation

---

## 💡 **MASTERY TIPS & EFFICIENCY HACKS**

### **Keyboard Shortcuts**
- `Ctrl+Click` → Open in new tab (great for bulk job creation)
- `Shift+Click` → Select multiple records
- `Tab` → Navigate between fields quickly
- `Enter` → Save field changes
- `Esc` → Cancel field editing

### **View Navigation**
**Create custom bookmark shortcuts:**
- Bookmark Daily Operations Dashboard for quick morning access
- Use browser tabs for common views
- Pin frequently used views in Airtable sidebar

### **Bulk Operations**
**Job Creation Efficiency:**
1. Open Job Creation Queue
2. Middle-click (or Ctrl+Click) each "Create Job" button → Opens in new tab
3. Process all tabs quickly without waiting for page reloads
4. Close tabs as jobs complete

**Sync Issue Resolution:**
1. Sort by issue type (handle all "Wrong Date" first)
2. Use Custom Service Time field for bulk time adjustments
3. Process similar issues together for efficiency

### **Advanced Filtering**
**Custom views for your specific needs:**
- Filter by specific assignees for workload management
- Filter by property groups for regional focus
- Filter by date ranges for specific planning periods

### **Quality Assurance Checks**
**Daily verification routine:**
1. Spot-check 3-5 jobs in HousecallPro match Airtable data
2. Verify next guest dates are calculating correctly
3. Check that custom instructions are appearing in job line items
4. Confirm same-day turnovers have proper timing

### **Customer Communication**
**When to contact customers directly:**
- Same-day turnover with potential delays
- Long-term guest with special requirements
- Service cancellation or major changes
- Quality issues or service problems

**Communication templates:**
- Same-day turnover: "We have a tight turnaround today, service will be completed by 2:00 PM"
- Long-term checkout: "Thank you for your extended stay, we'll provide thorough cleaning service"
- Delay notification: "Service delayed due to [reason], will complete by [time]"

---

## 📊 **REPORTING & ANALYTICS**

### **Daily Metrics to Track**
- New jobs created
- Sync issues resolved
- Same-day turnovers handled
- Blocks reviewed and processed

### **Weekly Performance Review**
- Service completion rates by assignee
- Average resolution time for sync issues
- Customer satisfaction feedback
- Property performance trends

### **Monthly Strategic Analysis**
- Growth in property count
- Automation efficiency improvements
- Cost savings vs manual process
- System enhancement opportunities

---

## 🎓 **TRAINING RESOURCES**

### **Video Tutorials** (Future Development)
- Daily workflow walkthrough
- Exception handling procedures
- Emergency response protocols
- Advanced Airtable techniques

### **Quick Reference Cards**
- View navigation shortcuts
- Emergency contact information
- Common error resolution steps
- Quality checklist items

### **Continuous Learning**
- Weekly system updates
- New feature training
- Best practice sharing
- Performance optimization tips

---

## 📞 **SUPPORT & ESCALATION**

### **Level 1: Self-Service**
- Check this operations guide
- Review error messages carefully
- Try basic troubleshooting steps
- Document issues for pattern recognition

### **Level 2: Technical Support**
- Contact: [technical support contact]
- Provide: Screenshots, error messages, affected properties
- Include: Date/time of issue, steps attempted
- Expected response: Within 2 hours during business hours

### **Level 3: Emergency Escalation**
- Use for: System down, mass failures, customer impact
- Contact: [emergency contact]
- Available: 24/7 for critical issues
- Expected response: Within 30 minutes

---

**Remember**: You've transformed from managing 100+ properties manually across multiple systems to being a strategic exception handler for an automated system. Your expertise is now focused on quality assurance, customer service, and handling the special cases that require human judgment.

**You've got this!** 🚀