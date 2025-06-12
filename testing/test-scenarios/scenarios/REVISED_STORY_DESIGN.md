# Revised Story-Based Testing Framework Design
## Business Logic Focus | Date Range: June 5-12, 2025 | Chapters 0-3 Only

## Core Business Logic Testing Objectives

Based on comprehensive code analysis, this framework tests the **actual business rules** that drive revenue and prevent data corruption:

### 1. **Same-Day Turnover Logic** (Revenue Critical)
- **iTrip Precedence Rule**: iTrip "Same Day?" flag overrides date calculation
- **Cross-Platform Detection**: Same-day across different data sources
- **Service Scheduling Impact**: Priority cleaning for same-day turnovers

### 2. **Overlapping Reservation Detection** (Overbooking Prevention)
- **True Overlap Logic**: `a_start < b_end AND a_end > b_start`
- **Adjacent Reservations**: Checkout = Checkin should NOT overlap
- **Block vs Reservation**: Only reservations overlap (blocks don't count)

### 3. **Property Matching Algorithm** (Data Integrity)
- **Exact Name Matching**: Case-insensitive full property name
- **Listing Number Extraction**: "Desert Villa #202" matches "202"
- **Edge Cases**: "Beach House#303Special" (no space after #)

### 4. **Entry Type Classification** (Business Categorization)
- **Keyword Detection**: "maintenance" → Block, "guest" → Reservation
- **Data Source Handling**: iTrip vs Evolve vs ICS behavior differences
- **Owner vs Guest**: Different business rules for each

### 5. **Status Management Lifecycle** (History Preservation)
- **Single Active Record**: Only one active record per UID
- **History Preservation**: Old records marked "Old", never deleted
- **HCP Field Preservation**: Service Job IDs preserved through changes

---

## Revised Story Progression (Chapters 0-3)

### Chapter 0: Baseline - Clean State
**Purpose**: Empty starting point
**Files**: Header-only CSV files, empty ICS calendar
**Expected**: No active reservations in Airtable

### Chapter 1: Initial Business Logic Setup
**Date Range**: June 5-7, 2025 (2 nights for all)
**Purpose**: Test different business scenarios, not just basic bookings

#### Boris iTrip Customer - **SAME-DAY TURNOVER SETUP**
- **Dates**: June 5-7, 2025
- **Property**: Boris Test House
- **Special**: CSV includes "Same Day? = Yes" flag
- **Purpose**: Test iTrip same-day precedence logic

#### Boris Evolve Customer - **OVERLAPPING SCENARIO SETUP**
- **Dates**: June 6-8, 2025 (overlaps with iTrip June 5-7)
- **Property**: Boris Test House (SAME PROPERTY as iTrip)
- **Purpose**: Test overlapping detection algorithm

#### Boris Evolve Tab2 Customer - **PROPERTY MATCHING EDGE CASE**
- **Dates**: June 9-11, 2025
- **Property Ref**: "202" (should match "Boris Test Villa #202")
- **Purpose**: Test listing number extraction logic

#### Boris ICS Customer - **ENTRY TYPE CLASSIFICATION**
- **Dates**: June 10-12, 2025
- **Event Title**: "Maintenance Block - Property Repairs"
- **Purpose**: Test keyword-based classification (should be "Block", not "Reservation")

**Expected Results**:
- Boris iTrip: Standard reservation
- Boris Evolve: Marked as overlapping with iTrip
- Boris iTrip: Also marked as overlapping with Evolve
- Boris Evolve Tab2: Property correctly matched via listing number
- Boris ICS: Classified as "Block" entry type

### Chapter 2: Business Logic Stress Tests
**Purpose**: ONE customer modifies dates, others test complex business rules

#### Boris iTrip Customer - **DATE MODIFICATION** (The ONE modification)
- **Original**: June 5-7, 2025
- **New**: June 8-10, 2025
- **Same Day Flag**: Changes from "Yes" to "No"
- **Purpose**: Test modification detection + same-day flag precedence change

#### Boris Evolve Customer - **SAME-DAY TURNOVER REALITY**
- **Dates**: June 7-9, 2025 (checkout June 9)
- **Purpose**: Creates REAL same-day turnover with next customer
- **Business Logic**: Should be detected as same-day with Boris Evolve Tab2

#### Boris Evolve Tab2 Customer - **SAME-DAY ARRIVAL**
- **Dates**: June 9-11, 2025 (checkin June 9, same as Evolve checkout)
- **Purpose**: Tests same-day turnover detection across different data sources
- **Service Impact**: Should trigger priority cleaning scheduling

#### Boris ICS Customer - **ADJACENT NOT OVERLAPPING**
- **Dates**: June 11-12, 2025 (checkin = Evolve Tab2 checkout)
- **Purpose**: Tests that adjacent reservations are NOT marked overlapping
- **Business Rule**: Checkout day = checkin day should be allowed

**Expected Results**:
- Boris iTrip: Old record marked "Old", new "Modified" record created
- Boris Evolve + Tab2: Both marked with same-day turnover flags
- Boris ICS: Adjacent to Tab2 but NOT overlapping
- Service scheduling adjusted for same-day cleaning priority

### Chapter 3: Edge Cases & Removals
**Purpose**: Test removal logic and extreme edge cases

#### Boris iTrip Customer - **GUEST OVERRIDE SCENARIO**
- **Guest Name**: "Smith Family Vacation"
- **Purpose**: Test guest override logic (if guest pattern matches property override)
- **Dates**: June 8-10, 2025 (unchanged from Chapter 2)

#### Boris Evolve Customer - **CANCELLATION/REMOVAL**
- **Status**: Reservation cancelled
- **Purpose**: Test removal detection and status management
- **Business Impact**: Frees up same-day turnover conflict

#### Boris Evolve Tab2 Customer - **LONG-TERM GUEST TRIGGER**
- **Dates**: June 9 - June 25, 2025 (16 nights - exceeds 14-day threshold)
- **Purpose**: Test long-term guest business logic
- **Service Impact**: Different cleaning schedule, special pricing

#### Boris ICS Customer - **PROPERTY MATCHING FAILURE**
- **Property Ref**: "Nonexistent Property #999"
- **Purpose**: Test graceful handling of invalid property references
- **Expected**: Processing should fail gracefully with clear error

**Expected Results**:
- Boris iTrip: Guest override logic tested (if applicable)
- Boris Evolve: Status changed to "Removed"
- Boris Evolve Tab2: Long-term guest flags activated
- Boris ICS: Processing error handled gracefully
- Same-day turnover conflict resolved due to Evolve cancellation

---

## Business Logic Testing Matrix

### Chapter 1 Tests:
✅ **Same-day turnover detection** (iTrip flag precedence)
✅ **Overlapping reservation logic** (same property, overlapping dates)
✅ **Property matching algorithm** (listing number extraction)
✅ **Entry type classification** (keyword-based classification)

### Chapter 2 Tests:
✅ **Modification detection** (same UID, different data)
✅ **Cross-platform same-day** (different sources, same dates)
✅ **Adjacent reservation logic** (checkout = checkin, not overlapping)
✅ **Status management** (Old → Modified workflow)

### Chapter 3 Tests:
✅ **Removal/cancellation logic** (status transitions)
✅ **Long-term guest detection** (14+ day threshold)
✅ **Property matching failures** (graceful error handling)
✅ **Guest override scenarios** (special customer handling)

---

## File Naming Convention

**Pattern**: `boris_{platform}_{chapter}_{scenario}.{ext}`

### Chapter 0 (Baseline):
- `boris_itrip_00_baseline.csv`
- `boris_evolve_00_baseline.csv`
- `boris_evolve_tab2_00_baseline.csv`
- `boris_ics_00_baseline.ics`

### Chapter 1 (Business Logic Setup):
- `boris_itrip_01_sameday.csv`
- `boris_evolve_01_overlap.csv`
- `boris_evolve_tab2_01_listing.csv`
- `boris_ics_01_block.ics`

### Chapter 2 (Stress Tests):
- `boris_itrip_02_modified.csv`
- `boris_evolve_02_turnover.csv`
- `boris_evolve_tab2_02_arrival.csv`
- `boris_ics_02_adjacent.ics`

### Chapter 3 (Edge Cases):
- `boris_itrip_03_override.csv`
- `boris_evolve_03_cancelled.csv`
- `boris_evolve_tab2_03_longterm.csv`
- `boris_ics_03_invalid.ics`

---

## Success Criteria

### Business Logic Validation:
1. **Same-day detection works correctly** with iTrip precedence
2. **Overlapping logic prevents overbooking** while allowing adjacent bookings
3. **Property matching handles edge cases** (numbers, special chars, case)
4. **Entry type classification** correctly categorizes blocks vs reservations
5. **Status management preserves history** while maintaining single active records
6. **Cross-platform integration** works consistently across all data sources

### Data Integrity:
1. **No data corruption** during complex business logic scenarios
2. **All modifications tracked** with complete audit trail
3. **Service scheduling adapts** to business logic outcomes
4. **Error handling graceful** for invalid data scenarios

This framework tests the **actual business logic** that affects revenue, prevents overbooking, and maintains data integrity - much more valuable than simple date modifications!