# Operational Training Checklist

**Purpose:** Step-by-step training program for new property management operators

---

## 📚 **Week 1: Foundation Skills**

### Day 1: System Overview
- [ ] Tour of Airtable interface
- [ ] Understanding the 4 main tables:
  - [ ] Reservations (bookings & cleaning jobs)
  - [ ] Properties (locations & HCP links)
  - [ ] Customers (property owners in HCP)
  - [ ] ICS Feeds (calendar sources)
- [ ] Basic navigation and filtering
- [ ] Practice: Find 5 reservations for tomorrow

### Day 2: Understanding Statuses
- [ ] Learn reservation statuses:
  - [ ] New = Just imported
  - [ ] Modified = Changed after import
  - [ ] Removed = Cancelled/deleted
  - [ ] Old = Historical/replaced
- [ ] Learn sync statuses:
  - [ ] Synced = All good ✅
  - [ ] Wrong Date = Schedule mismatch
  - [ ] Wrong Time = Time mismatch
  - [ ] Not Created = No HCP job yet
- [ ] Practice: Filter for each status type

### Day 3: Basic Job Creation
- [ ] Understand prerequisites:
  - [ ] Property must have HCP IDs
  - [ ] Must have Final Service Time
  - [ ] Service Type determines template
- [ ] Create first job (supervised):
  1. Find reservation without Service Job ID
  2. Verify Property ID linked
  3. Check Final Service Time set
  4. Click "Create Job & Sync Status"
  5. Verify job created in HCP
- [ ] Practice: Create 3 more jobs

### Day 4: Schedule Management
- [ ] Understanding time fields:
  - [ ] Final Service Time = Default schedule
  - [ ] Custom Service Time = Override
  - [ ] Scheduled Service Time = What's in HCP
- [ ] Rescheduling process:
  1. Update Custom Service Time
  2. Click "Add/Update Schedule"
  3. Check Sync Status updates
  4. Verify in HCP
- [ ] Practice: Reschedule 5 jobs

### Day 5: Common Issues & Assessment
- [ ] Handle late checkout request
- [ ] Process special instructions
- [ ] Deal with sync mismatch
- [ ] Find and fix "Not Created" job
- [ ] **Quiz**: Identify correct actions for 10 scenarios

---

## 🚀 **Week 2: Advanced Operations**

### Day 6: HousecallPro Integration
- [ ] Login to HCP (dev environment)
- [ ] Navigate job details
- [ ] Understanding line items:
  - [ ] Service types
  - [ ] Pricing structure
  - [ ] Custom instructions
- [ ] Assign/reassign cleaners
- [ ] Practice: Make 5 HCP updates

### Day 7: Handling Modifications
- [ ] Identify modified reservations
- [ ] Understand what triggers "Modified"
- [ ] Resolution process:
  1. Check what changed
  2. Update schedule if needed
  3. Verify sync status
  4. Check for conflicts
- [ ] Practice: Process all modified reservations

### Day 8: Same-Day Turnovers
- [ ] Identify same-day flags
- [ ] Understand timing criticality
- [ ] Special handling:
  - [ ] 8:00 AM start time
  - [ ] Experienced cleaner only
  - [ ] Monitor closely
  - [ ] Guest communication
- [ ] Practice: Plan tomorrow's same-days

### Day 9: Emergency Responses
- [ ] Guest locked out simulation
- [ ] Cleaner no-show drill
- [ ] System outage procedure
- [ ] Damage discovery protocol
- [ ] **Timed Test**: Resolve 5 urgent scenarios in 30 minutes

### Day 10: Quality Control
- [ ] Review completed jobs
- [ ] Check cleaner notes
- [ ] Verify photos/documentation
- [ ] Handle complaints process
- [ ] Practice: Full day's completions review

---

## 🎯 **Week 3: Mastery & Independence**

### Day 11: Bulk Operations
- [ ] Multi-property updates
- [ ] Bulk schedule changes
- [ ] Holiday adjustments
- [ ] Cleaner route optimization
- [ ] Practice: Next week's schedule optimization

### Day 12: System Troubleshooting
- [ ] Check webhook logs
- [ ] Restart services
- [ ] Manual sync processes
- [ ] API error resolution
- [ ] Practice: Debug 3 system issues

### Day 13: Reporting & Analytics
- [ ] Daily completion reports
- [ ] Weekly workload analysis
- [ ] Cleaner performance metrics
- [ ] Revenue tracking basics
- [ ] Create: Tomorrow's schedule report

### Day 14: Communication Mastery
- [ ] Guest communication templates
- [ ] Cleaner instructions clarity
- [ ] Property manager updates
- [ ] Escalation protocols
- [ ] Role-play: 10 difficult conversations

### Day 15: Final Assessment
- [ ] Solo morning operations (supervised)
- [ ] Handle all issues independently
- [ ] Make scheduling decisions
- [ ] Complete documentation
- [ ] **Certification Test**: Full day simulation

---

## 🏆 **Proficiency Levels**

### 🟢 **Basic Operator** (After Week 1)
Can handle:
- Simple job creation
- Basic rescheduling
- Status monitoring
- Following procedures

Time standards:
- Create job: < 2 minutes
- Reschedule: < 3 minutes
- Find reservation: < 1 minute

### 🟡 **Intermediate Operator** (After Week 2)  
Can handle:
- All basic tasks
- Modifications & conflicts
- Emergency situations
- Guest communications
- HCP navigation

Time standards:
- Resolve conflict: < 10 minutes
- Emergency response: < 15 minutes
- Bulk updates: < 20 minutes

### 🔴 **Advanced Operator** (After Week 3)
Can handle:
- All operational scenarios
- System troubleshooting  
- Training others
- Process improvements
- Decision making

Time standards:
- Any scenario: < 5 minutes
- System recovery: < 30 minutes
- Daily operations: < 2 hours

### ⭐ **Lead Operator** (3+ Months)
Additional skills:
- Create new processes
- Modify automations
- Advanced reporting
- Vendor management
- Strategic planning

---

## 📋 **Daily Operation Checklist**

### Morning (8:00 AM)
- [ ] Check overnight automations ran
- [ ] Review today's same-day turnovers
- [ ] Verify all jobs have cleaners assigned
- [ ] Check for any "Not Created" jobs
- [ ] Resolve any sync issues

### Midday (12:00 PM)
- [ ] Check morning job completions
- [ ] Handle any guest issues
- [ ] Process new reservations
- [ ] Update afternoon schedules
- [ ] Verify cleaner check-ins

### Afternoon (3:00 PM)
- [ ] Review afternoon progress
- [ ] Prepare tomorrow's schedule
- [ ] Handle any modifications
- [ ] Check supply levels
- [ ] Process special requests

### End of Day (5:00 PM)
- [ ] Verify all jobs completed
- [ ] Document any issues
- [ ] Update tomorrow's priorities
- [ ] Check webhook health
- [ ] Send shift summary

---

## 🛠️ **Essential Tools to Master**

### Airtable Views
1. **Today's Jobs**: Service Date = TODAY()
2. **Sync Issues**: Sync Status != "Synced"  
3. **Unscheduled**: Job Status = "Unscheduled"
4. **Tomorrow Prep**: Service Date = TOMORROW()
5. **Weekly Overview**: Service Date = THIS WEEK()

### Key Formulas
```
// Time until service
DATETIME_DIFF({Final Service Time}, NOW(), 'hours')

// Days since created  
DATETIME_DIFF(NOW(), {Created}, 'days')

// Overdue jobs
AND({Service Date} < TODAY(), {Job Status} != "Completed")
```

### Quick Commands
```bash
# Today's automation log
cat /home/opc/automation/src/automation/logs/automation_prod_$(date +%Y-%m-%d).log

# Recent webhooks
tail -n 100 /home/opc/automation/src/automation/logs/webhook.log | grep -i error

# Service status
sudo systemctl status webhook airscripts-api
```

---

## 🎓 **Certification Requirements**

### Written Test (50 questions)
- System knowledge: 20 questions
- Scenario handling: 20 questions  
- Troubleshooting: 10 questions
- Passing score: 85%

### Practical Test (4 hours)
- Handle live morning operations
- Resolve 10 random scenarios
- Complete daily checklist
- No critical errors allowed

### Ongoing Training
- Monthly scenario reviews
- New feature training
- System update briefings
- Performance feedback

---

*This training program ensures consistent, high-quality operations across all team members.*