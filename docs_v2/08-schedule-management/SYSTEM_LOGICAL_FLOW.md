# Schedule Management - Complete System Logical Flow

## Overview
This document describes the complete operational flow of the Schedule Management system, from initial reservation creation through schedule calculation, special case detection, manual overrides, and synchronization with service providers.

## Primary Data Flow

### 1. Schedule Calculation Triggers
The schedule management system activates through multiple pathways:
- New reservation created in Airtable
- Check-in or check-out dates modified
- Property assignment changed
- Manual schedule recalculation requested
- Custom service time entered

### 2. Initial Schedule Generation
When a reservation requires scheduling:
- System reads check-out date and time
- Default service windows are loaded from configuration
- Property-specific overrides are checked
- Base service time is calculated using checkout + offset
- Timezone conversion ensures MST/Arizona time

### 3. Special Case Detection Flow

#### Same-Day Turnover Detection
1. **Query Next Reservation**
   - Search for reservations at same property
   - Match where check-in date equals current checkout date
   - Exclude cancelled or old status records
   - Must be type "Reservation" not "Block"

2. **Calculate Urgency Level**
   - Compare next guest check-in time
   - Before 2 PM = "urgent" (2-hour window)
   - 2-4 PM = "standard" (3-hour window)
   - After 4 PM = "relaxed" (3-hour window)

3. **Adjust Service Window**
   - Reduce total duration to enable turnover
   - Start service earlier in the day
   - Flag as high priority for assignment
   - Add "SAME DAY" prefix to service name

#### Long-Term Guest Detection
1. **Calculate Stay Duration**
   - Subtract check-in from check-out date
   - Convert to days (accounting for timezone)
   - Apply thresholds: 14+ days = long-term
   - Further categorize: weekly/extended/monthly

2. **Apply Service Modifications**
   - Add 1 hour to standard cleaning time
   - Include deep cleaning requirements
   - Add "LONG TERM GUEST DEPARTING" flag
   - Update service instructions with special tasks

#### Owner Arrival Detection
1. **Search for Blocks**
   - Query blocks at same property
   - Look within 48 hours after checkout
   - Check block type and status
   - Calculate days between checkout and block

2. **Validate Owner Arrival**
   - Block must start 0-1 days after checkout
   - Confirm block represents owner (not maintenance)
   - Check for any intervening reservations
   - Set owner arrival flag if confirmed

3. **Enhance Service Requirements**
   - Upgrade to premium service level
   - Extend minimum duration to 4 hours
   - Add "OWNER ARRIVING" to service name
   - Include detailed inspection checklist

### 4. Schedule Conflict Resolution

#### Conflict Detection Process
1. **Define Service Window**
   - Start time from calculation or override
   - End time based on duration
   - Include buffer periods (30 min)
   - Account for travel time between properties

2. **Query Existing Schedules**
   - Get all services for the property/date
   - Include scheduled and in-progress jobs
   - Check assigned employee availability
   - Identify overlapping time windows

3. **Classify Conflicts**
   - Full overlap (complete conflict)
   - Partial overlap (adjustment possible)
   - Resource conflict (same cleaner)
   - Travel time conflict (sequential properties)

#### Automatic Resolution
1. **Time Shifting Strategy**
   - Try earlier slot (minimum 7 AM)
   - Try later slot (maximum 8 PM)
   - Maintain service quality requirements
   - Respect same-day constraints

2. **Duration Adjustment**
   - Reduce non-critical services
   - Split across multiple days if possible
   - Maintain minimum service standards
   - Document any reductions

3. **Resource Reallocation**
   - Assign alternate cleaner
   - Check cleaner property familiarity
   - Balance workload across team
   - Update assignment records

### 5. Custom Time Override Processing

#### Input Validation
1. **Parse Time Format**
   - Expect "HH:MM AM/PM" format
   - Validate hour range (1-12)
   - Validate minute range (0-59)
   - Confirm AM/PM designation

2. **Convert to System Time**
   - Apply timezone rules
   - Create full datetime object
   - Validate against business hours
   - Check for logical errors

3. **Conflict Checking**
   - Run standard conflict detection
   - Show conflicts to user
   - Require confirmation to proceed
   - Log override decision

#### Override Application
1. **Update Schedule Fields**
   - Set Custom Service Time
   - Flag as manually overridden
   - Record override user and timestamp
   - Preserve original calculated time

2. **Trigger Synchronization**
   - Push to HousecallPro immediately
   - Update any dependent schedules
   - Notify assigned cleaners
   - Log all changes

### 6. HousecallPro Synchronization

#### Initial Sync
1. **Prepare Schedule Data**
   - Format times in ISO 8601
   - Include arrival window
   - Add schedule notes
   - Set job references

2. **API Communication**
   - Check for existing appointment
   - Create or update as needed
   - Handle rate limiting
   - Retry on failures

3. **Response Processing**
   - Store appointment ID
   - Update sync status
   - Log sync timestamp
   - Handle error responses

#### Ongoing Synchronization
1. **Change Detection**
   - Monitor schedule field changes
   - Compare with last sync state
   - Identify material changes
   - Queue for synchronization

2. **Incremental Updates**
   - Send only changed fields
   - Preserve HCP-side changes
   - Merge conflicts appropriately
   - Maintain audit trail

## State Management

### Schedule States
- **Pending**: Awaiting calculation
- **Calculated**: Time determined
- **Confirmed**: Manually reviewed
- **Synced**: Pushed to HCP
- **Modified**: Changed after sync
- **Completed**: Service finished

### Flag States
- **Same-Day**: Back-to-back bookings
- **Long-Term**: 14+ day stays
- **Owner-Arriving**: Owner follow-up
- **Rush**: Urgent service needed
- **Deep-Clean**: Extended service

### Sync States
- **Not-Synced**: Never sent to HCP
- **Synced**: Matches HCP
- **Out-of-Sync**: Local changes pending
- **Sync-Error**: Failed to sync
- **Sync-Conflict**: HCP modified

## Error Handling Flows

### Calculation Errors
- Missing required dates returns clear error
- Invalid property configuration flagged
- Timezone conversion failures logged
- Default to standard window on error

### Conflict Errors
- Unresolvable conflicts escalated
- Multiple conflicts shown to user
- Suggestions provided for resolution
- Manual intervention required

### Sync Errors
- Network failures trigger retry
- API errors logged with details
- Rate limits handled gracefully
- Queue for later processing

### Data Integrity
- Preserve original values
- Log all modifications
- Enable rollback capability
- Audit trail maintenance

## Performance Optimization

### Calculation Performance
- Cache property defaults
- Batch related calculations
- Minimize database queries
- Use indexed lookups

### Conflict Detection
- Efficient date range queries
- Pre-filter obvious non-conflicts
- Cache cleaner schedules
- Optimize overlap algorithms

### Synchronization
- Batch multiple updates
- Async processing where possible
- Implement circuit breakers
- Monitor API usage

## Monitoring Points

### Key Metrics
- Schedule calculation time
- Conflict detection rate
- Override frequency
- Sync success rate
- API response times

### Alert Conditions
- High conflict rates
- Sync failures
- Unusual override patterns
- Performance degradation

### Audit Requirements
- All schedule changes logged
- Override reasons captured
- Sync history maintained
- Error details preserved

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Primary Code**: Distributed across multiple modules
**Related**: BusinessLogicAtoZ.md, mermaid-flows.md