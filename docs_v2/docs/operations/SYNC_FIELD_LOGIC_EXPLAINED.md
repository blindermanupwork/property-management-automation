# Sync Field Logic Explained

## Overview
The sync fields track how well Airtable reservation data matches with HousecallPro (HCP) job data. Think of it as a "health check" that tells you if the cleaning job in HCP matches what's expected from the reservation.

## The Main Sync Fields

### 1. **Sync Status** - The Quick Health Check
This field shows at a glance if everything is aligned:
- **"Synced"** ✅ - Everything matches perfectly
- **"Wrong Date"** ⚠️ - The job exists but is scheduled for the wrong day
- **"Wrong Time"** ⚠️ - The job is on the right day but wrong time
- **"Not Created"** ❌ - No job exists in HCP yet

### 2. **Sync Date and Time** - When Last Checked
- Shows when the system last verified the sync status
- Always in Arizona time (MST)
- Updates every time the system checks or changes anything

### 3. **Sync Details** - The Explanation
- Human-readable message explaining what's happening
- Examples:
  - "Schedule matches expected time"
  - "Schedule date doesn't match: expected 2025-04-15, found 2025-04-16"
  - "Job not found in HCP"

## When Do These Fields Update?

### 1. **During Job Creation** (When you click "Create Job & Sync Status")
- System creates job in HCP
- Immediately checks if the schedule matches
- Updates all sync fields with results

### 2. **During Automated Sync Runs** (Every 4 hours)
- System scans all reservations with HCP jobs
- Compares schedules and updates sync status
- Runs separately for dev (test) and prod (live) environments

### 3. **When HCP Sends Updates** (Real-time webhooks)
- HCP notifies our system of changes (status updates, schedule changes, etc.)
- System updates sync timestamp and details
- Keeps Airtable in sync with HCP changes

### 4. **During Schedule Updates** (When you click "Add/Update Schedule")
- System updates the schedule in HCP
- Verifies the update worked
- Updates sync fields with new status

## Common Scenarios and What They Mean

### Scenario 1: Perfect Sync
```
Sync Status: Synced
Sync Details: Schedule matches expected time
```
**What it means**: The cleaning is scheduled in HCP exactly when expected based on the reservation.

### Scenario 2: Wrong Time
```
Sync Status: Wrong Time
Sync Details: Schedule time doesn't match: expected 10:00 AM, found 2:00 PM
```
**What it means**: The cleaning is on the right day but at the wrong time. Someone needs to adjust the schedule in HCP.

### Scenario 3: Wrong Date
```
Sync Status: Wrong Date
Sync Details: Schedule date doesn't match: expected 2025-04-15, found 2025-04-16
```
**What it means**: The cleaning is scheduled for the wrong day entirely. This needs immediate attention.

### Scenario 4: Not Created
```
Sync Status: Not Created
Sync Details: Job not found in HCP
```
**What it means**: No job exists in HCP yet. Click "Create Job & Sync Status" to create it.

## How the System Determines Sync Status

1. **Gets Expected Time**: Looks at "Final Service Time" in Airtable (the when cleaning should happen)
2. **Gets Actual Time**: Queries HCP for the job's scheduled time
3. **Compares**: 
   - Same date and time? → "Synced"
   - Same date, different time? → "Wrong Time"
   - Different date? → "Wrong Date"
   - No job found? → "Not Created"

## Important Notes for Operations

### Time Zones
- All times in Airtable are in **Arizona time (MST)**
- HCP also uses Arizona time
- No daylight saving time confusion!

### Update Frequency
- **Real-time**: Webhooks update immediately when HCP changes
- **Scheduled**: Full sync runs every 4 hours
- **Manual**: Updates when you click sync buttons

### What You Should Do

1. **Daily Check**: Filter for `Sync Status != "Synced"` to find problems
2. **Wrong Time/Date**: 
   - Check if "Custom Service Time" is set correctly
   - Click "Add/Update Schedule" to fix
   - Or manually adjust in HCP
3. **Not Created**: Click "Create Job & Sync Status" to create the job

### Environment Separation
- **Development** (test): Uses Boris's HCP account for testing
- **Production** (live): Uses the real HCP account with actual jobs
- Sync runs separately for each environment
- Check webhook logs:
  - Dev: `webhook_development.log`
  - Prod: `webhook.log`

## Troubleshooting Guide

### "Job shows as Not Created but I know it exists"
- Check if you're looking at the right environment (dev vs prod)
- The Service Job ID might be missing - check HCP directly

### "Sync Status is outdated"
- Click "Create Job & Sync Status" to force a refresh
- Check if automated sync is running (every 4 hours)

### "Schedule keeps showing wrong after I update it"
- Verify "Custom Service Time" is in correct format (YYYY-MM-DD HH:MM AM/PM)
- Check if the job has multiple appointments in HCP
- Look at webhook logs for errors

## Summary
The sync system is like a continuous health monitor between Airtable and HCP. It tells you:
- ✅ What's working correctly
- ⚠️ What needs adjustment
- ❌ What's missing entirely

By checking the Sync Status regularly and responding to issues, you ensure cleaners show up at the right place at the right time!