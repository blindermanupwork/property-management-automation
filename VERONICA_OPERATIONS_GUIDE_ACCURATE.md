# Property Management Operations Guide
## **How Your Workflow Really Works**

*Veronica, this guide shows you exactly what the automation does and what you need to do each day.*

---

## 🎯 **What's Actually Automated (The Big Wins)**

### ✅ **Fully Automated - You Do Nothing:**
- **iTrip Email Processing**: All 100+ iTrip emails processed automatically daily
- **Evolve Data**: Reservations and blocks scraped automatically from Evolve portal
- **Calendar Sync**: All ICS feeds (Airbnb, Booking.com, etc.) processed every 30 minutes
- **Reservation Import**: New reservations appear in Airtable automatically

### 🔧 **Semi-Automated - You Click Buttons:**
- **Job Creation**: Reservations are imported, but you click "Create Job & Sync Status" button to make HCP jobs
- **Schedule Updates**: If you change times, you click "Add/Update Schedule" button to sync to HCP
- **Cleaner Assignment**: Cleaners assigned in HCP, then webhook updates Airtable automatically

---

## 📋 **Your Actual Daily Workflow**

### **Morning Routine (8:00 AM):**

1. **Open Airtable** → **Reservations** table
2. **Go to "🧹 Upcoming Cleanings (Next 7 Days)" view**
3. **Look for new reservations** (they'll be there automatically)
4. **For each new reservation:**
   - Click the **"Create Job & Sync Status"** button
   - Wait for it to sync (Sync Status will show "Synced")
   - Job now exists in HousecallPro

### **Assigning Cleaners:**
1. **Open HousecallPro** (not Airtable)
2. **Find the job** and assign cleaners
3. **Assignment automatically appears** in Airtable's "Assignee" field via webhook

### **Handling Late Checkouts:**
1. **In Airtable**: Find the reservation
2. **Update "Custom Service Time" field** with new time
3. **Click "Add/Update Schedule" button** to sync to HCP
4. **Check "Sync Status"** field shows "Synced"

---

## 🔍 **What Each Field Actually Does**

### **In Reservations Table:**

| Field | What It Does | How You Use It |
|-------|-------------|----------------|
| **Custom Service Time** | Override default cleaning time | Set this for late checkouts, then click update button |
| **Service Line Description** | First line shown to cleaners | Shows checkout/checkin info + priority |
| **Service Line Custom Instructions** | Special instructions for cleaners | Add "deep clean", "extra linens", etc. |
| **Create Job & Sync Status** | Creates job in HCP | Click this for new reservations |
| **Add/Update Schedule** | Updates job time in HCP | Click after changing Custom Service Time |
| **Delete Job Schedule** | Removes job from HCP | Click if reservation cancelled |
| **Assignee** | Shows who's assigned | Populated automatically from HCP webhook |
| **Sync Status** | Shows if job synced properly | Check this after clicking buttons |
| **Job Status** | Current job progress | Updated by HCP webhook |

---

## 🚨 **Common Tasks - The Reality**

### **1. New Reservation Appears**
- ✅ **Auto**: Reservation imported from calendar/iTrip/Evolve
- 🔧 **You Do**: Click "Create Job & Sync Status" button
- ✅ **Auto**: Job appears in HousecallPro

### **2. Owner Requests Late Checkout**
- 🔧 **You Do**: Update "Custom Service Time" field in Airtable
- 🔧 **You Do**: Click "Add/Update Schedule" button
- ✅ **Auto**: HCP job time updated, cleaners notified

### **3. Special Cleaning Request**
- 🔧 **You Do**: Add to "Service Line Custom Instructions" field
- 🔧 **You Do**: Click "Add/Update Schedule" button (if job already exists)
- ✅ **Auto**: Instructions appear in cleaner's HCP app

### **4. Assign Cleaners**
- 🔧 **You Do**: Open HousecallPro and assign cleaners to job
- ✅ **Auto**: Assignment appears in Airtable "Assignee" field within minutes

### **5. Evolve Properties**
- ✅ **Auto**: Evolve scraped automatically twice daily
- ✅ **Auto**: Blocks and reservations imported automatically
- ✅ **Auto**: No manual entry needed

---

## 📊 **Your Daily Views in Airtable**

### **Use These Views:**
- **"🧹 Upcoming Cleanings (Next 7 Days)"** - Jobs needing creation/attention
- **"Need Review / Issues"** - Problems that need fixing
- **"HCP Create Jobs"** - Ready to sync to HousecallPro
- **"Job Schedule" (Calendar view)** - Visual timeline

### **Key Status Indicators:**
- **Red Status**: Needs your attention (click buttons, fix issues)
- **"Not Created"** in Sync Status: Click "Create Job & Sync Status" button
- **"Wrong Time"** in Sync Status: Check times, click "Add/Update Schedule"
- **Empty Assignee**: Go to HCP and assign cleaners

---

## ⚡ **Speed Tips**

### **Bulk Actions:**
- Sort by "Sync Status" to find all jobs needing creation
- Use Ctrl+Click to open multiple HCP jobs in tabs
- Filter by "Service Type" to batch similar jobs

### **Time-Savers:**
- **Same-day Turnover** checkbox automatically sets 5:00 PM time
- **Regular turnovers** default to 5:15 PM
- **Custom Service Time** overrides both defaults

---

## 🚫 **What Doesn't Work (Yet)**

### **Missing Features You Might Expect:**
- **No direct cleaner assignment in Airtable** (must use HCP)
- **No automatic late checkout detection** (you must update manually)
- **No automatic special request parsing** (you must add instructions)
- **No bulk job creation** (must click button for each reservation)

---

## 🔧 **Troubleshooting**

### **If Job Doesn't Sync:**
1. Check "Sync Status" field for error message
2. Verify property has valid HCP Customer ID and Address ID
3. Try clicking button again
4. Check HCP for duplicate jobs

### **If Cleaner Assignment Doesn't Appear:**
1. Assignment made in HCP? (not Airtable)
2. Wait 2-3 minutes for webhook
3. Check webhook logs if still missing

### **If Late Checkout Not Working:**
1. Did you set "Custom Service Time" field?
2. Did you click "Add/Update Schedule" button?
3. Check "Sync Status" shows "Synced"

---

## 📈 **What You've Gained**

### **Time Saved Daily:**
- **iTrip Processing**: ~2-3 hours saved
- **Calendar Checking**: ~1 hour saved  
- **Manual Data Entry**: ~1-2 hours saved
- **Total**: 4-6 hours per day saved

### **What You Still Do:**
- Review imported reservations (5-10 minutes)
- Click job creation buttons (10-15 minutes)
- Handle special requests (varies)
- Assign cleaners in HCP (15-20 minutes)
- **Total Daily Work**: ~30-45 minutes

---

## 🎯 **Daily Checklist**

### **Morning (8:00 AM):**
- [ ] Check "Upcoming Cleanings" view
- [ ] Click "Create Job & Sync Status" for new reservations
- [ ] Review "Need Review / Issues" view
- [ ] Assign cleaners in HCP for urgent jobs

### **Midday (12:00 PM):**
- [ ] Handle any late checkout requests
- [ ] Check for special cleaning requests
- [ ] Assign remaining cleaners in HCP

### **End of Day (5:00 PM):**
- [ ] Verify tomorrow's jobs have cleaners assigned
- [ ] Check all sync statuses are "Synced"

---

**Remember**: The system does the heavy lifting, but you're still the boss. The buttons give you control over when and how jobs are created and scheduled.