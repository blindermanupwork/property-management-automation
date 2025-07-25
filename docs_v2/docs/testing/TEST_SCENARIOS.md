# Test Scenarios Documentation

This document consolidates all test scenarios from:
- COMPLETE_TEST_SCENARIOS_A_TO_Z.md
- CSV_PROCESSING_SCENARIO_MATRIX.md  
- SYSTEM_SCENARIO_MATRIX.md
- test_data/scenarios/*/README.md

## Scenario Categories

### 1. Baseline Scenarios
- Initial system state
- Empty reservations
- Basic property setup

### 2. Initial Bookings
- First reservation creation
- Multiple property bookings
- Various booking sources

### 3. Date Changes
- Check-in/check-out modifications
- Overlapping date handling
- Same-day turnarounds

### 4. Cancellations
- Reservation cancellations
- Block removals
- Status updates

### 5. Rebookings
- Cancelled then rebooked
- Modified reservations
- Guest changes

### 6. Edge Cases
- Unicode characters
- Long descriptions
- Invalid data handling

See test_data/scenarios/ for actual test data files.
