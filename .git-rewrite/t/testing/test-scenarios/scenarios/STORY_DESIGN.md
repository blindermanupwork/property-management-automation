# Story-Based Testing Framework Design Document

## Overview
This document defines the complete story progression, guest characters, properties, and date timeline for the 6-chapter story-based testing framework. It ensures consistency across all test files and provides the blueprint for creating realistic reservation scenarios.

---

## Core Characters & Properties

### 1. Boris iTrip Customer (iTrip Data Source)
**Customer Profile:**
- **Platform**: iTrip email CSV processing
- **Customer Name**: Boris iTrip Test
- **Property**: Boris Test House
- **Address**: 123 Test Street, Phoenix, AZ 85001
- **Property Type**: Single Family Home
- **Guest Character**: Boris iTrip Guest
- **Contact**: boris.itrip@testguest.com | (602) 555-0101

**File Format Characteristics:**
- CSV format with "Property Name" header (identifies as iTrip)
- Email-based delivery simulation
- Standard iTrip field mappings

### 2. Boris Evolve Regular Customer (Evolve Regular Data Source)
**Customer Profile:**
- **Platform**: Evolve portal scraping (regular format)
- **Customer Name**: Boris Evolve Test
- **Property**: Boris Test Villa
- **Address**: 456 Villa Lane, Scottsdale, AZ 85002
- **Property Type**: Luxury Villa
- **Guest Character**: Boris Evolve Guest
- **Contact**: boris.evolve@testguest.com | (480) 555-0202

**File Format Characteristics:**
- CSV format without "Property Name" header (identifies as Evolve)
- Portal scraping simulation
- Standard Evolve field mappings

### 3. Boris Evolve Tab2 Customer (Evolve Tab2 Data Source)
**Customer Profile:**
- **Platform**: Evolve portal scraping (Tab2 format variant)
- **Customer Name**: Boris Evolve Tab2 Test
- **Property**: Boris Test Condo
- **Address**: 789 Condo Circle, Tempe, AZ 85003
- **Property Type**: Luxury Condo
- **Guest Character**: Boris Evolve Tab2 Guest
- **Contact**: boris.tab2@testguest.com | (623) 555-0303

**File Format Characteristics:**
- CSV format with Evolve Tab2 variant headers
- Special Tab2 field mappings
- Owner block detection capabilities

### 4. Boris ICS Customer (ICS Feed Data Source)
**Customer Profile:**
- **Platform**: ICS calendar feed processing
- **Customer Name**: Boris ICS Test
- **Property**: Boris Test Apartment
- **Address**: 321 Calendar Court, Mesa, AZ 85004
- **Property Type**: Executive Apartment
- **Guest Character**: Boris ICS Guest
- **Contact**: boris.ics@testguest.com | (480) 555-0404

**File Format Characteristics:**
- ICS calendar format (.ics files)
- Calendar event processing
- Timezone and datetime handling

---

## Chapter-by-Chapter Story Progression

### Chapter 0: Baseline - Clean State (Empty Files)
**Date Range**: N/A (clean state)
**Purpose**: Establish empty starting point

**File Contents:**
- `boris_itrip_baseline.csv`: Header only, no data rows
- `boris_evolve_baseline.csv`: Header only, no data rows  
- `boris_evolve_tab2_baseline.csv`: Header only, no data rows
- `boris_ics_baseline.ics`: Basic calendar structure, no events

**Expected Airtable State**: No active reservations for any Boris customers

### Chapter 1: Initial Bookings - First Reservations
**Date Range**: June 10-12, 2025 (2 nights for all)
**Purpose**: Test initial reservation creation across all platforms

**Reservations:**
- **Boris iTrip Guest**: June 10-12 @ Boris Test House
- **Boris Evolve Guest**: June 10-12 @ Boris Test Villa  
- **Boris Evolve Tab2 Guest**: June 10-12 @ Boris Test Condo
- **Boris ICS Guest**: June 10-12 @ Boris Test Apartment

**Expected Results**: 4 new "New" status reservations in Airtable

### Chapter 2: Date Changes - Modification Scenarios  
**Date Range**: Various modifications (June 12-15)
**Purpose**: Test reservation modification detection and processing

**Modifications:**
- **Boris iTrip Guest**: June 10-12 → June 12-14 (shifted 2 days later)
- **Boris Evolve Guest**: June 10-12 → June 12-15 (extended to 3 nights)
- **Boris Evolve Tab2 Guest**: June 10-12 → June 13-15 (shifted 3 days later)
- **Boris ICS Guest**: June 10-12 → June 12-14 (shifted 2 days later)

**Expected Results**: Original reservations marked "Old", new "Modified" reservations created

### Chapter 3: Cancellations - Removal Scenarios
**Purpose**: Test partial cancellation handling (50% cancellation rate)

**Status Changes:**
- **Boris iTrip Guest**: June 12-14 → CANCELLED (marked as "Removed")
- **Boris Evolve Guest**: June 12-15 → KEEPING (remains "Modified")
- **Boris Evolve Tab2 Guest**: June 13-15 → CANCELLED (marked as "Removed")  
- **Boris ICS Guest**: June 12-14 → KEEPING (remains "Modified")

**Expected Results**: 2 cancellations, 2 continuing reservations

### Chapter 4: Rebookings - Second Chance Scenarios
**Date Range**: June 15-18 (new bookings for cancelled customers)
**Purpose**: Test rebooking workflow for previously cancelled customers

**New Bookings:**
- **Boris iTrip Guest**: NEW booking June 15-17 @ Boris Test House
- **Boris Evolve Guest**: CONTINUING June 12-15 @ Boris Test Villa
- **Boris Evolve Tab2 Guest**: NEW booking June 16-18 @ Boris Test Condo
- **Boris ICS Guest**: CONTINUING June 12-14 @ Boris Test Apartment

**Expected Results**: 2 new "New" status reservations, 2 continuing "Modified"

### Chapter 5: Multiple Changes - Complex Modifications
**Purpose**: Test complex multi-field modifications

**Complex Changes:**
- **Boris iTrip Guest**: June 15-17 → June 15-19 + add family members + special instructions
- **Boris Evolve Guest**: June 12-15 @ Villa → June 12-15 @ House (property change)
- **Boris Evolve Tab2 Guest**: June 16-18 → June 14-20 (early arrival + late departure)
- **Boris ICS Guest**: June 12-14 → June 11-13 (last-minute change one day earlier)

**Expected Results**: All reservations show complex "Modified" status with multiple field changes

### Chapter 6: Edge Cases - Ultimate Stress Tests
**Purpose**: Test extreme edge cases and boundary conditions

**Edge Case Scenarios:**
- **Boris iTrip Guest**: June 20 (same-day check-in/out, 0 nights)
- **Boris Evolve Guest**: June 21 - August 5 (45+ day long-term stay)
- **Boris Evolve Tab2 Guest**: Back-to-back guests June 18-20 & June 20-22 (same-day turnover)
- **Boris ICS Guest**: December 31, 2025 - January 2, 2026 (year boundary)

**Expected Results**: All edge case business logic properly triggered and handled

---

## Business Logic Testing Matrix

### Cross-Chapter Testing Scenarios

**Reservation Lifecycle Patterns:**
- New → Modified → Removed → New (iTrip & Evolve Tab2)
- New → Modified → Modified → Modified (Evolve & ICS)

**Date Progression Complexity:**
- Simple shifts (2-3 days)
- Extensions (2 nights → 3+ nights)  
- Contractions (longer → shorter stays)
- Last-minute changes
- Far future changes (6+ months)
- Year boundary transitions

**Service Type Variations:**
- Standard turnovers (most scenarios)
- Same-day turnovers (Chapter 6)
- Long-term guest scenarios (14+ nights)
- Back-to-back turnovers (consecutive guests)

**Property Management:**
- Same property throughout (most scenarios)
- Property changes (Chapter 5)
- Property conflicts (potential in Chapter 6)

**Guest Data Complexity:**
- Single guests (most scenarios)
- Guest additions (Chapter 5)
- Guest substitutions (potential variations)

---

## File Naming Conventions

### Standard Naming Pattern
`boris_{platform}_{scenario}.{ext}`

**Platform Codes:**
- `itrip`: iTrip email processing
- `evolve`: Evolve regular format
- `evolve_tab2`: Evolve Tab2 format variant
- `ics`: ICS calendar feeds

**Scenario Codes:**
- `baseline`: Chapter 0 empty files
- `initial`: Chapter 1 first bookings
- `modified`: Chapter 2 date changes
- `cancelled`: Chapter 3 cancellations (for cancelled customers)
- `keeping`: Chapter 3 continuing (for keeping customers)
- `rebook`: Chapter 4 new bookings (for previously cancelled)
- `continuing`: Chapter 4 ongoing (for continuing customers)
- `complex`: Chapter 5 multi-field changes
- `edge`: Chapter 6 edge case scenarios

**Extensions:**
- `.csv`: CSV format files (iTrip, Evolve, Evolve Tab2)
- `.ics`: ICS calendar format files (ICS)

---

## Technical Implementation Details

### Reservation UID Strategy
- **Consistent UIDs**: Same UID used across modifications for same logical reservation
- **New UIDs**: Fresh UIDs for rebookings (Chapter 4) and edge cases (Chapter 6)
- **Format**: `BORIS_TEST_{PLATFORM}_{SEQUENCE}_{CHAPTER}`

### Service Date Calculation
- **Check-out Date**: Primary service date (day guest leaves)
- **Same-day Turnovers**: Special handling for immediate cleaning needs
- **Long-term Stays**: Different service frequency (weekly vs daily)

### Status Progression Logic
- **New**: First appearance of reservation
- **Modified**: Changes to existing reservation
- **Removed**: Cancelled reservations
- **Old**: Previous versions of modified reservations

### Custom Instructions Progression
- **Chapter 1**: Standard cleaning instructions
- **Chapter 2**: Modification-related instructions
- **Chapter 5**: Complex special requirements
- **Chapter 6**: Edge case specific instructions (same-day, long-term, etc.)

---

## Validation Success Criteria

### Per-Chapter Validation
Each chapter should demonstrate:
1. **Correct file detection** and platform identification
2. **Proper data parsing** for all reservation fields
3. **Accurate status management** (New/Modified/Removed/Old)
4. **Appropriate business logic** triggering
5. **Complete Airtable synchronization**

### End-to-End Story Validation
Complete story should show:
1. **Full lifecycle coverage** (creation through complex modifications)
2. **All business rules tested** (same-day, long-term, property changes, etc.)
3. **Cross-platform consistency** (all 4 data sources work identically)
4. **Data integrity maintained** throughout all changes
5. **Performance acceptable** under complex scenario load

### Business Intelligence Validation
Final state should provide:
1. **Complete guest history** for all Boris customers
2. **Service requirement analysis** across all property types
3. **Modification pattern insights** (frequency, types, timing)
4. **Edge case handling documentation**
5. **System resilience demonstration**

---

This design document serves as the master blueprint for implementing the complete story-based testing framework, ensuring consistency, completeness, and realistic business scenario coverage.