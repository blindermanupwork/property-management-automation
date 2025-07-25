# Story-Based Testing Framework for Reservation Processing

## Overview

This document outlines a comprehensive story-based testing framework for testing reservation processing across all platforms (iTrip, Evolve Regular, Evolve Tab2, ICS) using real Boris test customers. The framework simulates realistic guest booking journeys from initial booking through cancellations and rebookings.

## Framework Architecture

### **Test Characters (Real Boris Customers)**

1. **Boris iTrip** (`cus_e15a41df1dcf4187872f9f0acebcb7ae`)
   - **Platform**: iTrip email CSV processing
   - **Property**: 123 Test iTrip, Phoenix, AZ
   - **Test Format**: iTrip CSV with full headers

2. **Boris Evolve Regular** (`cus_7fab445b03d34da19250755b48130eba`)
   - **Platform**: Evolve regular guest bookings
   - **Property**: 123 Test Dev Street, Phoenix, AZ
   - **Test Format**: Evolve CSV (guest reservations)

3. **Boris Evolve Tab2** (`cus_089a1dea457a466a8494a7c79334da99`)
   - **Platform**: Evolve tab2 owner blocks
   - **Property**: 123 Test Evolve Tab2, Phoenix, AZ
   - **Test Format**: Evolve tab2 CSV (owner blocks)

4. **Boris ICS** (`cus_af06528bb0bc4b3b93cf7560d821d27d`)
   - **Platform**: ICS calendar feed processing
   - **Property**: 123 Test ics, Phoenix, AZ
   - **Test Format**: ICS calendar feed

### **Story Structure (6 Chapters)**

```
📖 Chapter 0: Baseline (Clean Slate)
📖 Chapter 1: Initial Bookings (Everyone books June 10-12)
📖 Chapter 2: Date Changes (Everyone shifts to June 12-14/15)
📖 Chapter 3: Cancellations (Half cancel their reservations)
📖 Chapter 4: Rebookings (Cancelled guests book new dates)
📖 Chapter 5: Multiple Changes (Complex modification scenarios)
📖 Chapter 6: Edge Cases (Same day turnover, long stays)
```

## File Structure

```
test_data/
├── scenarios/
│   ├── 00_baseline/
│   │   ├── test_itrip_reservations.csv
│   │   ├── test_evolve_regular.csv
│   │   ├── test_evolve_tab2.csv
│   │   └── test_calendar.ics
│   ├── 01_initial_bookings/
│   │   ├── test_itrip_reservations.csv
│   │   ├── test_evolve_regular.csv
│   │   ├── test_evolve_tab2.csv
│   │   └── test_calendar.ics
│   ├── 02_date_changes/
│   │   └── [same structure]
│   ├── 03_cancellations/
│   │   └── [same structure]
│   ├── 04_rebookings/
│   │   └── [same structure]
│   ├── 05_multiple_changes/
│   │   └── [same structure]
│   └── 06_edge_cases/
│       └── [same structure]
├── story_test_runner.py
└── STORY_BASED_TESTING_FRAMEWORK.md (this file)
```

## Detailed Story Progression

### **Chapter 0: Baseline (Clean Slate)**
- **Purpose**: Establish clean starting state
- **Expected Result**: No active reservations for any Boris customers
- **Files**: Empty or minimal data files
- **Airtable Result**: Clean slate for testing

### **Chapter 1: Initial Bookings**
- **Story**: All Boris customers make their first bookings
- **Dates**: June 10-12, 2025
- **Service Types**: All Turnover services
- **Expected Result**: 4 new "New" records created
- **Test Points**:
  - iTrip: Creates "Reservation" with "Turnover" service
  - Evolve Regular: Creates "Reservation" with "Turnover" service
  - Evolve Tab2: Creates "Block" with "Needs Review" service
  - ICS: Creates "Reservation" with "Turnover" service

### **Chapter 2: Date Changes**
- **Story**: All customers modify their check-in/check-out dates
- **New Dates**: June 12-14, 2025 (iTrip, Evolve) / June 12-15, 2025 (Tab2, ICS)
- **Expected Result**: 4 "Modified" records, originals marked "Old"
- **Test Points**:
  - Same reservation UIDs but different dates
  - Previous records marked with Status = "Old"
  - New records created with Status = "Modified"

### **Chapter 3: Cancellations**
- **Story**: Boris iTrip and Boris Tab2 cancel their reservations
- **Action**: Remove these reservations from data files
- **Expected Result**: 2 "Removed" records, 2 "Unchanged"
- **Test Points**:
  - Missing UIDs create "Removed" status records
  - Remaining customers stay "Unchanged"
  - Historical records preserved

### **Chapter 4: Rebookings**
- **Story**: Previously cancelled customers book new dates
- **New Dates**: June 15-17, 2025
- **New UIDs**: Different reservation UIDs (new bookings)
- **Expected Result**: 2 new "New" records, 2 "Unchanged"
- **Test Points**:
  - New UIDs create fresh "New" records
  - Previous "Removed" records remain in history
  - Active customers remain "Unchanged"

### **Chapter 5: Multiple Changes**
- **Story**: Customers make multiple date modifications
- **Actions**: 
  - Boris Evolve Regular: Changes dates twice in same scenario
  - Boris ICS: Changes from Turnover to Return Laundry service
- **Expected Result**: Complex modification chain with multiple versions
- **Test Points**:
  - Multiple "Modified" records for same customer
  - Service type changes handled correctly
  - Complete audit trail maintained

### **Chapter 6: Edge Cases**
- **Story**: Test special scenarios and edge cases
- **Scenarios**:
  - Same day turnover (checkout = next checkin)
  - Long stay reservations (14+ days)
  - Back-to-back bookings
  - Holiday date scenarios
- **Expected Result**: Special flags and handling triggered
- **Test Points**:
  - Same-day turnover detection works
  - Long-term guest flags applied
  - Date validation edge cases

## Test Runner Implementation

### **Core Functions**

#### `run_scenario(scenario_name)`
```python
def run_scenario(scenario_name):
    """Run a complete test scenario"""
    print(f"🎭 Running Story Chapter: {scenario_name}")
    
    # 1. Setup Phase
    copy_scenario_files(scenario_name)
    
    # 2. Processing Phase  
    run_ics_processing()
    run_csv_processing()
    
    # 3. Reporting Phase
    report = generate_change_report()
    print_scenario_results(report)
    
    # 4. Verification Phase
    input("✅ Check Airtable and press Enter to continue...")
```

#### `copy_scenario_files(scenario)`
- Copy scenario files to processing locations
- ICS: Update web-served test calendar
- CSV: Copy to `CSV_process_development/` directories

#### `run_ics_processing()`
- Execute ICS processing for test calendar
- Capture output and processing results

#### `run_csv_processing()`  
- Execute CSV processing for all test files
- Handle both regular and tab2 processing

#### `generate_change_report()`
- Query Airtable before/after processing
- Identify New/Modified/Removed/Unchanged records
- Generate summary statistics

### **Change Detection Logic**

#### **Before Processing Snapshot**
```python
def capture_baseline():
    """Capture current state before processing"""
    boris_reservations = query_boris_reservations()
    return {
        'total_records': len(boris_reservations),
        'by_customer': group_by_customer(boris_reservations),
        'by_status': group_by_status(boris_reservations),
        'active_uids': extract_active_uids(boris_reservations)
    }
```

#### **After Processing Comparison**
```python
def compare_results(before, after):
    """Compare before/after states"""
    return {
        'new_records': find_new_records(before, after),
        'modified_records': find_modified_records(before, after),
        'removed_records': find_removed_records(before, after),
        'unchanged_records': find_unchanged_records(before, after)
    }
```

## Expected Results Matrix

| Chapter | Boris iTrip | Boris Evolve | Boris Tab2 | Boris ICS | Total New | Total Modified | Total Removed |
|---------|------------|--------------|------------|-----------|-----------|----------------|---------------|
| 0 | Clean | Clean | Clean | Clean | 0 | 0 | 0 |
| 1 | New | New | New (Block) | New | 4 | 0 | 0 |
| 2 | Modified | Modified | Modified | Modified | 0 | 4 | 0 |
| 3 | Removed | Unchanged | Removed | Unchanged | 0 | 0 | 2 |
| 4 | New | Unchanged | New (Block) | Unchanged | 2 | 0 | 0 |
| 5 | Modified | Modified×2 | Unchanged | Modified | 0 | 4 | 0 |
| 6 | Edge Cases | Edge Cases | Edge Cases | Edge Cases | Variable | Variable | Variable |

## File Format Specifications

### **iTrip CSV Format**
```csv
Checkin,Checkout,"Date Booked","Tenant Name","Tenant Phone","Property Name","Property Address","Property Owner",BR/BA,Size,"Next Booking","Next Tenant Name","Next Tenant Phone","Same Day?","Contractor Info","Reservation ID"
```

### **Evolve Regular CSV Format**
```csv
Reservation,Property Address,Property Owner,Status,Check-In,Check-Out,Guest Name
```

### **Evolve Tab2 CSV Format** 
```csv
Reservation,Property Address,Property Owner,Status,Check-In,Check-Out,Guest Name
```
*Note: Guest Name = Property Owner for owner blocks*

### **ICS Calendar Format**
```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Boris Test Calendar//EN
X-WR-CALNAME:Boris Test Property Calendar
BEGIN:VEVENT
SUMMARY:Service Type - Boris Property - Guest Name
DESCRIPTION:Boris test property - Service description
UID:boris_test_uid@test.com
DTSTART:20250610T140000Z
DTEND:20250612T110000Z
END:VEVENT
END:VCALENDAR
```

## Validation Checkpoints

### **Chapter 1 Validation**
- [ ] 4 new reservations created in Airtable
- [ ] iTrip reservation has correct iTrip format data
- [ ] Evolve regular creates "Reservation" entry
- [ ] Evolve tab2 creates "Block" entry with "Needs Review"
- [ ] ICS reservation has "Boris" entry source
- [ ] All have Status = "New"

### **Chapter 2 Validation**
- [ ] 4 modified reservations created
- [ ] Original records marked Status = "Old"
- [ ] New records have Status = "Modified"
- [ ] Same reservation UIDs maintained
- [ ] New dates reflected correctly

### **Chapter 3 Validation**
- [ ] 2 removed reservations (iTrip + Tab2)
- [ ] 2 unchanged reservations (Evolve + ICS)
- [ ] Removed records have Status = "Removed"
- [ ] Historical data preserved

### **Continuing Validation Pattern**
Each chapter includes specific validation points to ensure the story progression works correctly.

## Usage Instructions

### **Running Complete Story**
```bash
cd /home/opc/automation/test_data
python3 story_test_runner.py --full-story
```

### **Running Single Chapter**
```bash
python3 story_test_runner.py --chapter 01_initial_bookings
```

### **Reset to Baseline**
```bash
python3 story_test_runner.py --reset-baseline
```

## Benefits of Story-Based Testing

1. **Realistic Scenarios**: Tests mirror real guest booking behaviors
2. **Complete Coverage**: Tests all status transitions (New→Modified→Removed)
3. **Historical Validation**: Ensures data history is preserved correctly
4. **Cross-Platform**: Tests all platforms simultaneously
5. **Incremental Verification**: Allows manual checking between scenarios
6. **Repeatable**: Can reset and re-run complete story arc
7. **Comprehensive**: Covers both regular reservations and owner blocks

## Implementation Tasks

### **High Priority**
- [ ] Create scenario directory structure
- [ ] Build story progression data for all 6 chapters
- [ ] Implement test runner script with file management
- [ ] Add Airtable change detection and reporting

### **Medium Priority**  
- [ ] Add user verification pauses between scenarios
- [ ] Create comprehensive validation checkpoints
- [ ] Build edge case scenarios
- [ ] Add cleanup and reset functionality

### **Low Priority**
- [ ] Add performance timing metrics
- [ ] Create visual reporting dashboard
- [ ] Add automated screenshot capture
- [ ] Build regression testing suite

This framework provides comprehensive testing of the entire reservation processing pipeline using realistic, story-driven scenarios that mirror actual guest booking behaviors.