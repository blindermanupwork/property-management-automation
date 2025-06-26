# Comprehensive Testing Checklist for Property Management Automation

## 📋 Complete End-to-End Testing Framework

This document provides a comprehensive checklist for testing all functionality in the property management automation system using the Boris test customer and dynamic test data generation.

---

## 🏗️ Test Infrastructure

### ✅ Setup Prerequisites
- [ ] Boris test customer exists in HCP dev (`cus_7fab445b03d34da19250755b48130eba`)
- [ ] Boris test customer exists in Airtable dev with properties
- [ ] Test properties configured with addresses
- [ ] Development environment properly configured
- [ ] MCP servers (HCP dev, Airtable dev) operational
- [ ] Test data generator script ready (`tests/dynamic-test-generator.py`)
- [ ] Comprehensive E2E test script ready (`tests/comprehensive-e2e-test.py`)

### ✅ Test Data Sources
- [ ] **Evolve CSV Format**: No "Property Name" header (identifies as Evolve)
- [ ] **iTrip CSV Format**: Has "Property Name" header (identifies as iTrip)  
- [ ] **ICS Calendar Format**: Calendar feed format for various platforms

---

## 🎯 Test Scenarios Matrix

### 1. Data Generation Tests

#### ✅ Mixed Sources Scenario
```bash
python3 tests/dynamic-test-generator.py --scenario mixed_sources --count 10
```
- [ ] **Evolve reservations**: Generated with correct format
- [ ] **iTrip reservations**: Generated with correct format  
- [ ] **ICS reservations**: Generated with correct format
- [ ] **Status variety**: New, modified, removed statuses
- [ ] **File validation**: All CSV/ICS files created successfully

#### ✅ Long-term Guest Scenario
```bash
python3 tests/dynamic-test-generator.py --scenario long_term_guests --count 5
```
- [ ] **Duration ≥14 days**: All reservations qualify as long-term
- [ ] **Custom instructions**: "Long-term guest - deep cleaning required"
- [ ] **Service name logic**: Should include "LONG TERM GUEST DEPARTING"
- [ ] **Business logic**: Proper detection in processing

#### ✅ Same-day Turnover Scenario
```bash
python3 tests/dynamic-test-generator.py --scenario same_day_turnovers --count 3
```
- [ ] **Checkout/checkin same day**: 11 AM checkout, 4 PM checkin
- [ ] **Priority cleaning**: Custom instructions reflect urgency
- [ ] **Next guest timing**: Proper next guest date calculation
- [ ] **Service coordination**: Both reservations linked properly

#### ✅ Modification Sequence Scenario
```bash
python3 tests/dynamic-test-generator.py --scenario modifications_sequence --count 5
```
- [ ] **Stage 1 - New**: Initial reservations created
- [ ] **Stage 2 - Modified**: Dates/guest info changed
- [ ] **Stage 3 - Removed**: Reservations cancelled
- [ ] **UID consistency**: Same reservation UID through all stages
- [ ] **Status tracking**: Proper status field values

#### ✅ Edge Cases Scenario
```bash
python3 tests/dynamic-test-generator.py --scenario edge_cases --count 5
```
- [ ] **Very short stays**: 1-day reservations
- [ ] **Very long stays**: 90+ day reservations  
- [ ] **Past dates**: Late entries for completed stays
- [ ] **Far future**: Advance bookings 6+ months out
- [ ] **Same-day use**: Check-in and check-out same day

#### ✅ Custom Instructions Variety
```bash
python3 tests/dynamic-test-generator.py --scenario custom_instructions_variety --count 10
```
- [ ] **Standard instructions**: Various cleaning requests
- [ ] **Special needs**: Pet-friendly, medical, VIP
- [ ] **Length testing**: 200+ character truncation
- [ ] **Unicode support**: Special characters, emojis
- [ ] **Business scenarios**: Late checkout, early checkin

---

## 🔄 Processing Workflow Tests

### 2. CSV Processing → Airtable Import

#### ✅ iTrip CSV Processing
- [ ] **File detection**: System identifies iTrip format (has "Property Name" header)
- [ ] **Data parsing**: All fields extracted correctly
- [ ] **Property matching**: Boris properties linked correctly
- [ ] **Guest data**: Guest information imported properly
- [ ] **Date handling**: Check-in/check-out dates in Arizona timezone
- [ ] **Status mapping**: iTrip statuses → Airtable statuses
- [ ] **Custom instructions**: Imported and truncated if needed
- [ ] **Next guest dates**: Calculated and stored properly
- [ ] **File archival**: Processed files moved to `CSV_done_development/`

#### ✅ Evolve CSV Processing  
- [ ] **File detection**: System identifies Evolve format (no "Property Name" header)
- [ ] **Data parsing**: All fields extracted correctly
- [ ] **Property matching**: Boris properties linked correctly
- [ ] **Guest data**: Guest information imported properly
- [ ] **Date handling**: Check-in/check-out dates in Arizona timezone
- [ ] **Status mapping**: Evolve statuses → Airtable statuses
- [ ] **Custom instructions**: Imported and truncated if needed
- [ ] **File archival**: Processed files moved to `CSV_done_development/`

#### ✅ Record Management Logic
- [ ] **New reservations**: Create new Airtable records
- [ ] **Modified reservations**: Update existing records, mark old as "Old"
- [ ] **Removed reservations**: Mark records as "Removed"
- [ ] **UID tracking**: Proper handling of reservation UIDs
- [ ] **History preservation**: Old versions preserved with "Old" status
- [ ] **Duplicate prevention**: No duplicate active records per UID

### 3. ICS Processing → Airtable Import

#### ✅ ICS Feed Processing
- [ ] **Feed parsing**: ICS calendar format parsed correctly
- [ ] **Event extraction**: Reservation events identified
- [ ] **Data mapping**: ICS fields → Airtable fields
- [ ] **Property matching**: Events linked to Boris properties
- [ ] **Date handling**: Timezone conversion handled properly
- [ ] **Status detection**: New/modified/cancelled events
- [ ] **Recurring events**: Single events vs recurring handled
- [ ] **Feed validation**: Invalid/malformed ICS handled gracefully

---

## 🏢 Job Management Tests

### 4. Job Creation Workflow

#### ✅ Airtable → HCP Job Creation
**Test via "Create Job & Sync Status" button in Airtable**

- [ ] **Job type selection**: Correct job type based on service type
  - [ ] **Turnover**: `jbt_3744a354599d4d2fa54041a4cda4bd13` (Dev Turnover)
  - [ ] **Inspection**: `jbt_7234d0af0a734f10bf155d2238cf92b7` (Dev Inspection)  
  - [ ] **Return Laundry**: `jbt_01d29f7695404f5bb57ed7e8c5708afc` (Dev Return Laundry)

- [ ] **Customer linkage**: Job linked to Boris HCP customer
- [ ] **Address selection**: Correct property address used
- [ ] **Service name generation**:
  - [ ] **Standard**: `{base_service_name}`
  - [ ] **With custom**: `{custom_instructions} - {base_service_name}`
  - [ ] **Long-term**: `LONG TERM GUEST DEPARTING {base_service_name}`
  - [ ] **Long-term + custom**: `{custom_instructions} - LONG TERM GUEST DEPARTING {base_service_name}`

- [ ] **Custom instructions processing**:
  - [ ] **Field detection**: "Custom Service Line Instructions" from Airtable
  - [ ] **Truncation**: 200-character limit enforced
  - [ ] **Unicode support**: Special characters handled
  - [ ] **Integration**: Instructions included in first line item name

- [ ] **Schedule setting**: 
  - [ ] **Date/time**: From "Final Service Time" field
  - [ ] **Timezone**: Arizona timezone conversion
  - [ ] **Window**: Appropriate arrival window set

- [ ] **Line items creation**:
  - [ ] **Service line item**: Primary service with custom instructions
  - [ ] **Pricing**: Appropriate unit price set
  - [ ] **Quantity**: Correct quantity (typically 1)
  - [ ] **Taxable**: Proper tax settings

- [ ] **Airtable sync back**:
  - [ ] **Service Job ID**: HCP job ID stored in Airtable
  - [ ] **Service Job Link**: Direct link to HCP job
  - [ ] **Sync Status**: "Synced" status set
  - [ ] **Sync Details**: Success message recorded
  - [ ] **Sync Date and Time**: Timestamp recorded

#### ✅ Long-term Guest Detection
- [ ] **Duration calculation**: `(check_out - check_in) >= 14 days`
- [ ] **Service name prefix**: "LONG TERM GUEST DEPARTING" added
- [ ] **Special handling**: Additional cleaning considerations
- [ ] **Documentation**: Long-term status noted in job details

#### ✅ Error Handling
- [ ] **Missing customer**: Graceful error handling
- [ ] **Invalid addresses**: Error messages and fallbacks  
- [ ] **API failures**: Retry logic and error reporting
- [ ] **Field validation**: Required field checks
- [ ] **Timeout handling**: Long API calls handled properly

### 5. Schedule Management

#### ✅ Schedule Updates
**Test via "Add/Update Schedule" button**

- [ ] **Time modification**: Update scheduled service time
- [ ] **Custom Service Time**: Use custom time if specified
- [ ] **Final Service Time**: Default fallback time
- [ ] **Timezone handling**: Arizona timezone maintained
- [ ] **HCP sync**: Schedule updated in HousecallPro
- [ ] **Airtable sync**: New schedule reflected in Airtable
- [ ] **Status tracking**: Update recorded in sync details

#### ✅ Schedule Validation
- [ ] **Past dates**: Prevent scheduling in past
- [ ] **Business hours**: Validate reasonable service times
- [ ] **Conflict detection**: Check for scheduling conflicts
- [ ] **Arrival windows**: Appropriate time windows set

### 6. Job Cancellation/Deletion

#### ✅ Job Cancellation (Dev Environment)
**Test via "Delete Job Schedule" button**

- [ ] **Pre-validation**: Check for existing Service Job ID
- [ ] **API call**: DELETE request to `/api/dev/jobs/{recordId}`
- [ ] **Authentication**: Proper API key used (`airscripts-secure-key-2025`)
- [ ] **HCP job cancellation**: Job cancelled in HousecallPro
- [ ] **Airtable cleanup**:
  - [ ] **Schedule removal**: Scheduled Service Time cleared
  - [ ] **Status update**: Job Status updated appropriately
  - [ ] **Sync details**: Cancellation recorded
  - [ ] **Job ID retention**: Service Job ID kept for reference

- [ ] **Re-scheduling capability**: Job can be recreated after cancellation
- [ ] **Error handling**: Graceful handling of missing/invalid job IDs
- [ ] **Status feedback**: Clear success/error messages

#### ✅ Complete Job Deletion
**Test via delete job script**

- [ ] **HCP job removal**: Job completely removed from HousecallPro
- [ ] **Airtable cleanup**: All job-related fields cleared
- [ ] **History preservation**: Action logged in sync details
- [ ] **Recovery prevention**: Deleted job cannot be recovered

---

## 🔄 Status Synchronization Tests

### 7. HCP → Airtable Status Sync

#### ✅ Job Status Mapping
- [ ] **Scheduled**: HCP "scheduled" → Airtable "Scheduled"
- [ ] **In Progress**: HCP "in_progress" → Airtable "In Progress"  
- [ ] **Completed**: HCP "completed" → Airtable "Completed"
- [ ] **Cancelled**: HCP "canceled" → Airtable "Cancelled"

#### ✅ Sync Process Validation
- [ ] **Automatic sync**: Regular sync via cron jobs
- [ ] **Manual sync**: On-demand sync capability
- [ ] **Conflict resolution**: Handle simultaneous updates
- [ ] **Error recovery**: Failed syncs retried appropriately
- [ ] **Audit trail**: All sync activities logged

#### ✅ Data Consistency Checks
- [ ] **Schedule alignment**: Times match between systems
- [ ] **Employee assignments**: Proper assignee sync
- [ ] **Job details**: Notes and descriptions consistent
- [ ] **Customer data**: Contact info synchronized

---

## 🧪 Business Logic Validation

### 8. Service Type Logic

#### ✅ Service Type Detection
- [ ] **Turnover**: Regular guest departure cleaning
- [ ] **Same-day turnover**: Guest departing same day as next arrival
- [ ] **Inspection**: Property inspection services
- [ ] **Return Laundry**: Laundry delivery services
- [ ] **Maintenance**: Property maintenance tasks

#### ✅ Service Name Generation
Test all combinations:
- [ ] **Base name only**: `"Turnover STR Next Guest March 15"`
- [ ] **With custom**: `"Extra cleaning - Turnover STR Next Guest March 15"`
- [ ] **Long-term only**: `"LONG TERM GUEST DEPARTING Turnover STR Next Guest March 15"`
- [ ] **Long-term + custom**: `"Extra cleaning - LONG TERM GUEST DEPARTING Turnover STR Next Guest March 15"`

#### ✅ Next Guest Date Logic
- [ ] **Calculation**: Based on next reservation check-in
- [ ] **Same-day handling**: Next guest same day as checkout
- [ ] **Gap analysis**: Days between guests calculated
- [ ] **Service timing**: Cleaning scheduled appropriately

### 9. Custom Instructions Processing

#### ✅ Instruction Handling
- [ ] **Field extraction**: From "Custom Service Line Instructions"
- [ ] **Length validation**: 200-character maximum enforced
- [ ] **Truncation logic**: Properly truncated with "..." if needed
- [ ] **Unicode support**: Special characters preserved
- [ ] **Empty handling**: Graceful handling of empty instructions
- [ ] **Whitespace**: Trimming and normalization

#### ✅ Integration Points
- [ ] **Service names**: Instructions included in HCP job names
- [ ] **Line items**: Instructions in first line item description
- [ ] **Job notes**: Additional details in job notes if needed
- [ ] **Airtable display**: Instructions visible in Airtable records

---

## 🚨 Error Scenarios & Edge Cases

### 10. Data Quality Tests

#### ✅ Invalid Data Handling
- [ ] **Malformed dates**: Invalid date formats handled
- [ ] **Missing required fields**: Graceful degradation
- [ ] **Invalid characters**: Special characters cleaned
- [ ] **Encoding issues**: UTF-8 encoding handled properly
- [ ] **Large datasets**: Performance with many reservations

#### ✅ System Integration Failures
- [ ] **HCP API downtime**: Retry logic and queuing
- [ ] **Airtable API limits**: Rate limiting handled
- [ ] **Network failures**: Connection error recovery
- [ ] **Authentication failures**: Token refresh/retry
- [ ] **Timeout scenarios**: Long-running operations handled

#### ✅ Concurrency Scenarios
- [ ] **Simultaneous updates**: Multiple users updating same record
- [ ] **Race conditions**: Proper locking and sequencing
- [ ] **Partial failures**: Rollback mechanisms
- [ ] **Duplicate prevention**: Idempotent operations

---

## 🏃‍♂️ Automated Test Execution

### Quick Test Run
```bash
# Generate all test scenarios with 5 reservations each
python3 tests/dynamic-test-generator.py --all-scenarios --count 5 --environment development

# Run comprehensive end-to-end test
python3 tests/comprehensive-e2e-test.py --environment development

# Clean up test data
python3 tests/dynamic-test-generator.py --cleanup
```

### Individual Scenario Testing
```bash
# Test specific scenarios
python3 tests/dynamic-test-generator.py --scenario long_term_guests --count 3
python3 tests/dynamic-test-generator.py --scenario same_day_turnovers --count 2
python3 tests/dynamic-test-generator.py --scenario custom_instructions_variety --count 5
```

### Manual Testing Workflow
1. **Generate test data** for specific scenario
2. **Run automation** to process CSV files
3. **Check Airtable** for imported reservations
4. **Test job creation** via "Create Job & Sync Status" button
5. **Verify HCP job** creation and details
6. **Test schedule updates** via "Add/Update Schedule" button
7. **Test job cancellation** via "Delete Job Schedule" button
8. **Verify status sync** between systems

---

## 📊 Test Results Validation

### ✅ Success Criteria
- [ ] **Data generation**: All test files created successfully
- [ ] **CSV processing**: 100% of test files processed without errors
- [ ] **Airtable import**: All reservations imported with correct data
- [ ] **Job creation**: Jobs created in HCP with proper details
- [ ] **Schedule management**: Updates and cancellations work correctly
- [ ] **Status sync**: Bidirectional sync maintains data consistency
- [ ] **Business logic**: All scenarios produce expected results
- [ ] **Error handling**: Graceful handling of edge cases

### ✅ Performance Benchmarks
- [ ] **Data generation**: < 30 seconds for 50 reservations
- [ ] **CSV processing**: < 60 seconds for 10 CSV files
- [ ] **Job creation**: < 10 seconds per job
- [ ] **Status sync**: < 30 seconds for full sync cycle
- [ ] **Memory usage**: No memory leaks during testing
- [ ] **Database performance**: No significant slowdowns

### ✅ Quality Metrics
- [ ] **Data accuracy**: 100% field mapping accuracy
- [ ] **Business logic**: 100% scenario coverage
- [ ] **Error handling**: 95%+ error scenarios handled gracefully
- [ ] **Performance**: All operations within acceptable time limits
- [ ] **User experience**: Clear feedback and error messages

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### Data Generation Issues
- **Problem**: Generator fails to create files
- **Solution**: Check permissions on CSV directories
- **Command**: `ls -la src/automation/scripts/CSV_process_development/`

#### CSV Processing Issues  
- **Problem**: Files not being processed
- **Solution**: Verify environment configuration and file formats
- **Command**: `python3 src/run_automation_dev.py --dry-run`

#### Job Creation Issues
- **Problem**: Jobs not created in HCP
- **Solution**: Check HCP API credentials and customer/address validity
- **Debug**: Review HCP sync script logs

#### Schedule Issues
- **Problem**: Schedule updates not syncing
- **Solution**: Verify timezone handling and API permissions
- **Debug**: Check Airtable sync status fields

#### Status Sync Issues
- **Problem**: Status not updating between systems
- **Solution**: Review sync scripts and API authentication
- **Debug**: Check sync details in Airtable records

---

## 📋 Test Checklist Summary

### Pre-Testing
- [ ] Environment setup complete
- [ ] Boris test customer configured
- [ ] Test scripts executable
- [ ] Dependencies installed

### Core Testing
- [ ] All 6 test scenarios generated and processed
- [ ] CSV → Airtable workflow tested
- [ ] ICS → Airtable workflow tested  
- [ ] Job creation workflow tested
- [ ] Schedule management tested
- [ ] Status synchronization tested
- [ ] Business logic scenarios validated
- [ ] Error handling tested

### Post-Testing
- [ ] Results documented
- [ ] Issues identified and logged
- [ ] Test data cleaned up
- [ ] Performance metrics recorded

### Sign-off
- [ ] **Development Environment**: All tests passing
- [ ] **Business Logic**: All scenarios validated
- [ ] **Error Handling**: Edge cases covered
- [ ] **Performance**: Acceptable response times
- [ ] **Documentation**: Testing process documented

---

**Testing completed by:** _______________ **Date:** _______________

**Environment tested:** Development ☐ Production ☐

**Overall test result:** Pass ☐ Fail ☐ Needs Review ☐

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________