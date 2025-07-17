# Sync Field Business Rules & Operations Guide

## Overview

This document defines the complete business rules for how sync fields should be updated across all automation systems in the property management platform.

## Field Definitions

### **Schedule Sync Details** 🔍
**Purpose**: Alert field for schedule mismatches requiring user attention  
**Behavior**: Only populated when Airtable and HCP schedules are out of sync  
**Visual Cue**: Acts as a "sync alert" - empty means everything is in sync

### **Service Sync Details** ⚙️
**Purpose**: Activity log for all service operations and status updates  
**Behavior**: Continuously updated with operational status and progress  
**Visual Cue**: Shows latest service activity and current operational state

## Business Rules by Operation Type

### 🎯 **Schedule Operations**

#### **Schedule Synchronization Check**
- **When**: Automated sync processes compare Airtable vs HCP schedules
- **Schedule Sync Details**: ONLY updated if mismatch found
  - ❌ Wrong Date: `"Airtable shows July 30 but HCP shows July 31"`
  - ❌ Wrong Time: `"Airtable shows 8:00 AM but HCP shows 8:35 AM"`
  - ✅ In Sync: Field remains empty/unchanged
- **Service Sync Details**: Never updated by sync checks

#### **Manual Schedule Updates** (Add/Update Schedule Button)
- **When**: User clicks "Add/Update Schedule" button
- **Schedule Sync Details**: Only updated if final result shows mismatch
- **Service Sync Details**: ALWAYS updated with operation result
  - ✅ Success: `"Service updated to July 31 at 8:35 AM"`
  - ✅ Created: `"Schedule created for July 31 at 8:35 AM"`
  - ❌ Failed: `"Failed to update schedule: [error message]"`

#### **Schedule Deletion** (Delete Job Schedule Button)
- **When**: User clicks "Delete Job Schedule" button
- **Schedule Sync Details**: Never updated (deletion is not a sync operation)
- **Service Sync Details**: ALWAYS updated
  - ✅ Success: `"Job schedule deleted from HCP on [timestamp]"`
  - ❌ No Schedule: `"Job has no schedule to delete. Already unscheduled."`

### 🔄 **Webhook Events**

#### **Job Status Changes**
- **When**: HCP webhooks report job status changes
- **Schedule Sync Details**: Never updated
- **Service Sync Details**: ALWAYS updated
  - `"Job started at 2:15 PM"`
  - `"Job completed at 4:30 PM"`
  - `"Job canceled on July 15 at 3:45 PM"`

#### **Employee Assignment Changes**
- **When**: HCP webhooks report employee assignments
- **Schedule Sync Details**: Never updated
- **Service Sync Details**: ALWAYS updated
  - `"Assigned to John Smith at 1:45 PM"`
  - `"Unassigned from Jane Doe at 2:00 PM"`

#### **Appointment Scheduling** (From HCP)
- **When**: HCP webhooks report appointment creation/changes
- **Schedule Sync Details**: ONLY if schedule doesn't match expected time
- **Service Sync Details**: ALWAYS updated with appointment status
  - `"Appointment scheduled for July 31 at 8:35 AM"`
  - `"Appointment rescheduled from July 30 to July 31"`

### 🏗️ **Job Creation Operations**

#### **Create Job & Sync Status** (API/Button)
- **When**: User creates new HCP job from Airtable
- **Schedule Sync Details**: ONLY updated if created schedule differs from requested
- **Service Sync Details**: ALWAYS updated with creation result
  - ✅ Success: `"Job created successfully - Job ID: job_12345"`
  - ✅ Rescheduled: `"Canceled job rescheduled successfully"`

#### **Bulk HCP Sync** (Automated Scripts)
- **When**: dev-hcp-sync.cjs or prod-hcp-sync.cjs runs
- **Schedule Sync Details**: ONLY updated for schedule mismatches
- **Service Sync Details**: Never updated (these are sync verification scripts)

## Field Update Priority & Conflicts

### **Update Timing Rules**
1. **Immediate Operations**: API calls and button actions update immediately
2. **Webhook Updates**: Process within 30 seconds of HCP event
3. **Automated Sync**: Runs every 4 hours, only updates mismatches
4. **Manual Override**: User actions always take precedence

### **Conflict Resolution**
- **Same Field, Multiple Sources**: Last update wins (timestamp-based)
- **Different Fields, Same Time**: No conflict (each field has specific purpose)
- **Webhook vs User Action**: User action takes precedence if within 2 minutes

### **Message Formatting Standards**

#### **Timestamp Format & Positioning**
All sync messages include Arizona timezone timestamps positioned on the **right side**:
```
[operation details] - Jul 10, 3:45 PM
```

**Examples:**
- `Airtable shows July 15 at 10:15 AM but HCP shows July 16 at 2:30 PM - Jul 10, 3:45 PM`
- `Job completed successfully - Jul 10, 3:45 PM`
- `Schedule updated to July 20 at 8:00 AM - Jul 10, 3:45 PM`

#### **Markdown Compatibility**
- ✅ **Plain text formatting**: All messages use clean text without problematic markdown
- ❌ **Bold formatting removed**: No `**bold**` syntax that displays as literal asterisks in Airtable
- ✅ **Emoji support**: Uses standard emojis (✅ ❌ ⚠️ 🔄) for visual status indicators

## System Component Responsibilities

### **API Handlers** (`jobs.js`, `schedules.js`)
- ✅ Update Service Sync Details for operation results
- ✅ Update Schedule Sync Details only for mismatches
- ✅ Always include timestamps
- ✅ Handle both dev and prod environments

### **Webhook System** (`webhook.py`)
- ✅ Update Service Sync Details for job progression
- ✅ Update Schedule Sync Details only for HCP-initiated schedule changes
- ✅ Never overwrite user-initiated operations
- ✅ **REDUCED NOISE: Only update Service Sync Details for significant status changes** (In Progress, Completed, Canceled)

### **HCP Sync Scripts** (`dev-hcp-sync.cjs`, `prod-hcp-sync.cjs`)
- ✅ Update Schedule Sync Details only for mismatches
- ❌ Never update Service Sync Details
- ✅ Include job creation operations in Service Sync Details

### **Reconciliation Scripts** (`reconcile-jobs.py`)
- ✅ Update Schedule Sync Details for discovered mismatches
- ❌ Never update Service Sync Details

## User Experience Guidelines

### **What Users Should See**

#### **Schedule Sync Details Field**
- **Empty/Blank**: Everything is in sync ✅
- **Has Content**: Action required - schedule mismatch needs attention ⚠️
- **Use Case**: Quick visual indicator of sync health

#### **Service Sync Details Field**
- **Always Has Content**: Shows latest service activity
- **Continuously Updated**: Running log of service operations
- **Use Case**: Troubleshooting and status tracking

### **Button Behavior**

#### **"Add/Update Schedule" Button**
1. Updates schedule in HCP
2. Updates Service Sync Details with result
3. Only updates Schedule Sync Details if mismatch remains
4. Shows success/failure in Service Sync Details

#### **"Delete Job Schedule" Button**
1. Removes schedule from HCP
2. Updates Service Sync Details with deletion confirmation
3. Never touches Schedule Sync Details
4. Clears Scheduled Service Time and Appointment ID

#### **"Create Job & Sync Status" Button**
1. Creates job in HCP
2. Updates Service Sync Details with creation result
3. Updates Schedule Sync Details if schedule doesn't match
4. Populates all job-related fields

## Error Handling & Fallbacks

### **API Failures**
- Log error to Service Sync Details
- Preserve existing Schedule Sync Details
- Include timestamp and error details

### **Webhook Processing Errors**
- Log to application logs only
- Do not update Airtable fields on webhook errors
- Retry webhook processing if possible

### **Airtable Update Failures**
- Retry with essential fields only
- Log errors to system logs
- Never lose sync status information

## Monitoring & Alerting

### **Health Indicators**
- **Schedule Sync Details Population**: % of records with content (lower is better)
- **Service Sync Details Age**: How recent the last update was
- **Webhook Processing Time**: Should be under 30 seconds
- **API Response Times**: Should be under 5 seconds

### **Alert Conditions**
- **High Schedule Sync Details Population**: >10% of active jobs (sync issues)
- **Stale Service Sync Details**: No updates in 24+ hours (webhook issues)
- **Frequent API Failures**: >5% failure rate (system issues)

## Implementation Checklist

### **Phase 1: Webhook Optimization** ✅ **COMPLETED**
- [x] **REDUCED webhook updates to Service Sync Details for simple status changes**
- [x] Keep webhook updates only for significant events (assignment changes, major status changes)
- [x] Preserve webhook updates for Schedule Sync Details (HCP-initiated schedule changes)

### **Phase 2: Field Usage Audit** ✅ **COMPLETED**
- [x] API handlers use correct field separation
- [x] HCP sync scripts use correct field separation  
- [x] Reconciliation scripts use correct field separation
- [x] Webhook handlers use correct field separation ✅ **OPTIMIZED**

### **Phase 3: Message Formatting** ✅ **COMPLETED** 
- [x] **FIXED Airtable bold markdown formatting issues**
  - [x] Removed problematic `**bold**` formatting from all sync messages
  - [x] Fixed syncMessageBuilder.js (development environment)
  - [x] Fixed webhook.py sync messages
  - [x] Fixed jobs.js API handler fallback messages
  - [x] Fixed schedules.js API handler messages
  - [x] Fixed dev-hcp-sync.cjs script messages
  - [x] Fixed prod-hcp-sync.cjs script messages
- [x] **IMPROVED timestamp positioning**
  - [x] Moved timestamps from left to right side of messages
  - [x] Updated all sync systems for consistent formatting
  - [x] Applied to both development and production environments

### **Phase 4: User Experience**
- [ ] Update Airtable interface to show field purposes clearly
- [ ] Add help text explaining field meanings
- [ ] Create user training materials

### **Phase 5: Monitoring**
- [ ] Implement field population monitoring
- [ ] Set up alerting for sync health
- [ ] Create dashboard for sync status overview

---

## Quick Reference

| Operation | Schedule Sync Details | Service Sync Details |
|-----------|----------------------|---------------------|
| Sync Check | Only if mismatch | Never |
| Manual Schedule Update | Only if mismatch | Always (result) |
| Job Creation | Only if mismatch | Always (result) |
| Job Deletion | Never | Always (confirmation) |
| Webhook Status | Never | **REDUCED** ✅ |
| Webhook Assignment | Never | Always |
| Webhook Schedule Change | Always | Never |

**Key Principle**: Schedule Sync Details = "Alert when broken", Service Sync Details = "Log all activity"

## Technical Implementation Notes

### **Message Generation Systems**

#### **Development Environment**
- **syncMessageBuilder.js**: Centralized message builder for consistent formatting
- **buildSyncMessage()**: Function that generates standardized sync messages
- **Right-side timestamps**: All messages follow `[content] - [timestamp]` format

#### **Production Environment** 
- **Fallback messaging**: Direct string formatting in API handlers and sync scripts
- **Consistent formatting**: Same timestamp positioning as development
- **Cross-platform compatibility**: Works across all automation components

#### **Files Modified for Formatting Consistency**
1. **`/src/automation/scripts/shared/syncMessageBuilder.js`** - Development message builder
2. **`/src/automation/scripts/airscripts-api/handlers/jobs.js`** - Job creation API 
3. **`/src/automation/scripts/airscripts-api/handlers/schedules.js`** - Schedule update API
4. **`/src/automation/scripts/webhook/webhook.py`** - Webhook processing
5. **`/src/automation/scripts/hcp/dev-hcp-sync.cjs`** - Development sync script
6. **`/src/automation/scripts/hcp/prod-hcp-sync.cjs`** - Production sync script

### **Service Restart Requirements**
When sync message formatting is updated:
1. **API Service**: `sudo systemctl restart airscripts-api-https`
2. **Webhook Services**: `sudo systemctl restart webhook` and `sudo systemctl restart webhook-dev`
3. **Cron Scripts**: Changes apply automatically on next scheduled run