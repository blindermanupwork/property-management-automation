# Comprehensive Airtable Views Guide - Operational Manual

**Version:** 1.1.0  
**Updated:** July 15, 2025  
**Purpose:** Simplified operational guide for Airtable views with real button names and examples

---

## Table of Contents
1. [Overview](#overview)
2. [🚨❌ Incomplete View](#incomplete-view) - Past jobs not completed
3. [🚨❓ Mismatch View](#mismatch-view) - Schedule conflicts between Airtable and HCP
4. [🚨🗑️ Removed View](#removed-view) - Canceled reservations with active jobs
5. [⬆️🧹 Upcoming Reservations View](#upcoming-reservations-view) - Future planning
6. [Summary: Daily Workflow](#summary-daily-workflow-using-views)

---

## Overview - Why Views Matter {#overview}

Views are pre-configured filters that help you quickly find specific records without manually setting up complex searches each time. Think of them as saved searches that answer specific operational questions.

**Key Concepts:**
- **Filters**: Define which records appear in the view
- **Sorting**: Determines the order of records
- **Grouping**: Organizes records into sections
- **Auto-sort**: Keeps records organized as data changes

---

## 🚨❌ Incomplete View {#incomplete-view}

### Why does it show up?
Job is in the past.

### How do we know?
Scheduled Service Time is in the past.

### How do we fix it?

#### If the job is in the past and needs to be updated to today:
1. Update "Custom Service Time" field to the correct date/time
2. Click "Add/Update Schedule" button to update HCP's schedule

#### If it was completed:
Have the cleaner update HCP to "Completed". That will remove it from the list.

### Example Scenario
```
**THIS IS A FAKE EXAMPLE**
Property: 1234 Fake Street, Phoenix, AZ 85001
Scheduled Service Time: July 14 at 10:15 AM
Today: July 15, 2025
Job Status: In Progress
```


---

## 🚨❓ Mismatch View {#mismatch-view}

### Why does it show up?
It can be wrong date/wrong time meaning Airtable and HCP schedule times are different.

### How do we fix it?

#### If Airtable is right:
Click "Add/Update Schedule" button to update HCP

#### If HCP is correct:
1. Update "Custom Service Time" to HCP's scheduled date/time
2. That's it - the automatic sync job will work in 4 hours
3. OR you can click "Create Job & Sync Status" button

### Example Scenarios

#### Wrong Time
```
**THIS IS A FAKE EXAMPLE**
Property: 5678 Imaginary Lane, Scottsdale, AZ 85250
Airtable shows: July 20 at 10:15 AM
HCP shows: July 20 at 12:05 PM
Sync Status: Wrong Time
```

#### Wrong Date
```
**THIS IS A FAKE EXAMPLE**
Property: 9999 Fictional Ave #45, Phoenix, AZ 85020
Airtable shows: July 18 at 10:15 AM
HCP shows: July 19 at 10:15 AM
Sync Status: Wrong Date
```


---

## 🚨🗑️ Removed View {#removed-view}

### Why does it show up?
These are canceled reservations with a service HCP schedule still not in canceled status.

### How do we fix it?
We need to delete the HCP job by clicking "Delete Job Schedule" button.

### Example Scenario
```
**THIS IS A FAKE EXAMPLE**
Property: 2468 Pretend Place, Glendale, AZ 85301
Status: Removed (canceled reservation)
Job Status: Scheduled (still active in HCP)
```


---

## ⬆️🧹 Upcoming Reservations View {#upcoming-reservations-view}

### What does it show?
Mainly to see which reservations say "Sync Status" is "Not Created" - then you know job hasn't been created. Also to see upcoming reservations to make sure nothing is missing.

### Example Scenario
```
**THIS IS A FAKE EXAMPLE**
▼ Check-out Date: July 20, 2025 (8 records)
  Property: 4321 Example Boulevard, Tempe, AZ 85281
  Service Job ID: job_fake456example
  Sync Status: Synced
  
  Property: 8765 Sample Street, Phoenix, AZ 85015
  Service Job ID: (empty)
  Sync Status: Not Created
```

When "Sync Status" is "Not Created" - click "Create Job & Sync Status" button.


---

## Summary: Daily Workflow Using Views

### Morning Routine (Recommended Order)

1. **🚨❌ Incomplete** - Past jobs not completed
   - Update "Custom Service Time" and click "Add/Update Schedule" if rescheduling
   - Have cleaner mark complete in HCP if done

2. **🚨❓ Mismatch** - Schedule conflicts
   - Click "Add/Update Schedule" if Airtable is correct
   - Update "Custom Service Time" if HCP is correct

3. **🚨🗑️ Removed** - Canceled reservations
   - Click "Delete Job Schedule" to cancel job
   - Check for next guests first

4. **⬆️🧹 Upcoming Reservations** - Future planning
   - Click "Create Job & Sync Status" for missing jobs
   - Review assignee distribution