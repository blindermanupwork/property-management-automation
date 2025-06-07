# Property Management Operations Guide
## **How Your Daily Workflow Works**

*Veronica, this guide shows you exactly what the automation does and what you need to do each day.*

---

## 🎯 **What's Actually Automated (The Big Wins)**

### ✅ **Fully Automated - You Do Nothing:**
- **iTrip Email Processing**: Dozens of reservations processed automatically daily from email reports
  - All iTrip report data (guest name, check-in/out dates, property) automatically added to Airtable
- **Evolve Data**: Bookings and blocks scraped automatically from Evolve portal
- **Calendar Sync**: All ICS feeds (Airbnb, Booking.com, etc.) processed every 4 hours
- **Service Import**: New services appear in Airtable automatically

### 🔧 **Semi-Automated - You Click Buttons:**
- **Job Creation**: Services are imported, but you click "Create Job & Sync Status" button to make HCP jobs
- **Schedule Updates**: If you change times, you click "Add/Update Schedule" button to sync to HCP
- **Cleaner Assignment**: Cleaners assigned in HCP, then assignment appears in Airtable automatically

---

## 📋 **Your Actual Daily Workflow**

### **Morning Routine (8:00 AM):**

1. **Open Airtable** → **Reservations** table
2. **Go to "🧹 Upcoming Cleanings (Next 7 Days)" view**
3. **Look for new services** (they'll be there automatically)
4. **For each new service:**
   - Click the **"Create Job & Sync Status"** button
   - Wait for it to complete (button will show success)
   - Job now exists in HousecallPro

### **Assigning Cleaners:**
1. **Open HousecallPro** (not Airtable)
2. **Find the job** and assign cleaners
3. **Assignment automatically appears** in Airtable's "Assignee" field within seconds

### **Handling Late Checkouts or Rescheduling:**
1. **In Airtable**: Find the service
2. **Update "Custom Service Time" field** with new date and time
3. **Click "Add/Update Schedule" button** to sync to HCP
4. **Job time updated** in HousecallPro

---

## 🔍 **What Each Field Actually Does**

### **In Reservations Table:**

| Field | What It Does | How You Use It |
|-------|-------------|----------------|
| **Custom Service Time** | Override default cleaning time | Set this for late checkouts or rescheduling, then click update button |
| **Service Line Description** | Shows service type, priority, next guest date | Automatically filled for cleaners to see |
| **Service Line Custom Instructions** | Important cleaning instructions | Add "deep clean", "extra linens", etc. BEFORE creating job (cannot update after) |
| **Create Job & Sync Status** | Creates job in HCP | Click this for new services |
| **Add/Update Schedule** | Updates job time in HCP | Click after changing Custom Service Time |
| **Delete Job Schedule** | Removes job from HCP | Click if service cancelled |
| **Assignee** | Shows who's assigned | Populated automatically from HCP |
| **Job Status** | Current job progress | Updated automatically from HCP |

---

## 🚨 **Common Tasks - The Reality**

### **1. New Service Appears**
- ✅ **Auto**: Service imported from calendar/iTrip/Evolve
- 🔧 **You Do**: Click "Create Job & Sync Status" button
- ✅ **Auto**: Job appears in HousecallPro

### **2. Owner Requests Late Checkout**
- 🔧 **You Do**: Update "Custom Service Time" field in Airtable
- 🔧 **You Do**: Click "Add/Update Schedule" button
- ✅ **Auto**: HCP job time updated, cleaners notified

### **3. Service Didn't Happen Yesterday**
- 🔧 **You Do**: Update "Custom Service Time" to correct date and time
- 🔧 **You Do**: Click "Add/Update Schedule" button
- ✅ **Auto**: Job rescheduled in HCP

### **4. Special Cleaning Request**
- 🔧 **You Do**: Add to "Service Line Custom Instructions" field BEFORE creating job
- 🔧 **You Do**: Click "Create Job & Sync Status" button
- ✅ **Auto**: Instructions included in job's first line item name in HCP
- ⚠️ **Note**: Cannot update instructions after job creation (must edit in HCP directly)

### **5. Assign Cleaners**
- 🔧 **You Do**: Open HousecallPro and assign cleaners to job
- ✅ **Auto**: Assignment appears in Airtable "Assignee" field within seconds

### **6. Evolve Properties**
- ✅ **Auto**: Evolve scraped automatically every 4 hours
- ✅ **Auto**: Blocks and bookings imported automatically
- ✅ **Auto**: No manual entry needed

### **7. Cancelling/Removing Services**
- 🔧 **You Do**: If a job is marked as "removed" status in Airtable
- 🔧 **You Do**: Click "Delete Job Schedule" button to cancel in HousecallPro
- ✅ **Auto**: Job cancelled in HCP, cleaners notified

### **8. Adding New Properties**
- 🔧 **Manual Process**: Contact support to add new properties to the system
- ✅ **Auto**: Once added, all automation applies to new property

---

## 📊 **Your Daily Views in Airtable**

### **Use These Views:**
- **"🧹 Upcoming Cleanings (Next 7 Days)"** - Jobs needing creation/attention
- **"Need Review / Issues"** - Problems that need fixing
- **"HCP Create Jobs"** - Ready to sync to HousecallPro
- **"Job Schedule" (Calendar view)** - Visual timeline

### **Key Status Indicators:**
- **Red Status**: Needs your attention (click buttons, fix issues)
- **Empty Service Job ID**: Click "Create Job & Sync Status" button
- **Empty Assignee**: Go to HCP and assign cleaners

---

## ⚡ **Speed Tips**

### **Bulk Actions:**
- **Bulk job creation available** but doing manually first to verify accuracy
- Use Ctrl+Click to open multiple HCP jobs in tabs
- Filter by "Service Type" to batch similar jobs

### **Time-Savers:**
- **Same-day Turnover** checkbox automatically sets 10:00 AM MST time
- **Regular turnovers** default to 10:15 AM MST
- **Custom Service Time** overrides both defaults

### **Service Line Custom Instructions:**
- **Add special instructions** to the "Service Line Custom Instructions" field
- **Instructions appear first** in the job name: "Long Term Guest Departing - Turnover STR Next Guest Unknown"
- **Automatic truncation** to 200 characters for HousecallPro compatibility
- **Full character support** including accents, special characters, and emojis
- **Cannot be changed** after job creation (must edit in HCP directly)

---

## 🚫 **What Doesn't Work (Yet)**

### **Missing Features You Might Expect:**
- **No direct cleaner assignment in Airtable** (must use HCP)
- **No automatic late checkout detection** (you must update manually)
- **No automatic special request parsing** (you must add instructions)
- **Property addition** (contact support for now)

---

## 🔧 **Troubleshooting**

### **If Job Doesn't Sync:**
*[Contact support with specific error details]*

### **If Cleaner Assignment Doesn't Appear:**
*[Check timing and contact support if needed]*

### **If Late Checkout Not Working:**
*[Verify steps and contact support]*

---

## 📈 **What You've Gained**

### **Time Saved Daily:**
- Significant reduction in manual data entry and email processing
- Automated calendar monitoring and job creation
- Streamlined workflow with centralized management

---

## 🎯 **Daily Checklist**

### **Morning:**
*[Your morning routine tasks]*

### **Midday:**
*[Your midday routine tasks]*

### **End of Day:**
*[Your end of day routine tasks]*

---

**Remember**: The system does the heavy lifting, but you're still in control. The buttons give you control over when and how jobs are created and scheduled. All times are in MST (Mountain Standard Time).