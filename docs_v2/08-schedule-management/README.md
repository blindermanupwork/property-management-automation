# Schedule Management Documentation

## Overview

The Schedule Management feature handles all aspects of service scheduling, including standard turnover times, same-day turnovers, long-term guest detection, owner arrival coordination, and custom service time overrides. This feature ensures cleaning services are scheduled appropriately based on reservation patterns and special circumstances.

## Quick Navigation

- **BusinessLogicAtoZ.md** - Complete business rules for scheduling
- **SYSTEM_LOGICAL_FLOW.md** - Text-based operational flow descriptions
- **mermaid-flows.md** - Visual workflow diagrams
- **version-history.md** - Feature change tracking

## Key Capabilities

### 1. Automatic Schedule Generation
- Calculate service times based on checkout patterns
- Apply property-specific default times
- Handle timezone conversions (MST/Arizona)
- Generate Final Service Time for all reservations

### 2. Same-Day Turnover Detection
- Identify back-to-back reservations
- Apply expedited service windows
- Flag urgent turnovers
- Adjust service duration

### 3. Long-Term Guest Management
- Detect stays of 14+ days
- Add "LONG TERM GUEST DEPARTING" flags
- Adjust service expectations
- Track extended stay patterns

### 4. Owner Arrival Detection
- Identify owner blocks following reservations
- Add "OWNER ARRIVING" notifications
- Prioritize pre-owner services
- Coordinate with property management

### 5. Custom Time Overrides
- Allow manual schedule adjustments
- Parse "HH:MM AM/PM" format
- Update HCP appointments
- Maintain override history

## Business Context

### Property Management Workflow
1. **Reservation Import**: New bookings trigger schedule calculation
2. **Schedule Generation**: Automatic service time assignment
3. **Special Detection**: Flags for same-day, long-term, owner arrivals
4. **Manual Adjustments**: Custom times for special circumstances
5. **HCP Synchronization**: Push schedules to service provider

### Key Decision Points
- **Checkout Time**: Determines base service window
- **Next Guest**: Same-day detection for urgent turnovers
- **Stay Length**: Long-term threshold at 14 days
- **Entry Type**: Block entries trigger owner notifications
- **Custom Override**: Manual times take precedence

## Configuration

### Time Windows
```javascript
// Standard service windows by checkout time
const serviceWindows = {
  "10:00 AM": { start: "11:00 AM", duration: 4 },
  "11:00 AM": { start: "12:00 PM", duration: 4 },
  "12:00 PM": { start: "1:00 PM", duration: 4 },
  "3:00 PM": { start: "4:00 PM", duration: 3 },
  "4:00 PM": { start: "5:00 PM", duration: 3 }
};

// Same-day turnover adjustments
const sameDayWindows = {
  standard: { start: "12:00 PM", duration: 3 },
  expedited: { start: "11:00 AM", duration: 2 }
};
```

### Detection Thresholds
- **Long-Term Guest**: 14+ consecutive days
- **Same-Day Turnover**: Check-in date equals checkout date
- **Owner Arrival**: Block entry within 0-1 days of checkout
- **Schedule Conflict**: Overlapping service windows

## Integration Points

### 1. Airtable Fields
- **Check-in/out Dates**: Source data for calculations
- **Final Service Time**: Generated schedule
- **Custom Service Time**: Manual override
- **Same-day Turnover**: Boolean flag
- **Long Term Stay**: Auto-calculated
- **Owner Arriving**: Detection result

### 2. HousecallPro Integration
- Create appointments with calculated times
- Update schedules when changed
- Handle timezone conversions
- Sync employee assignments

### 3. Automation Triggers
- New reservation → Calculate schedule
- Date change → Recalculate times
- Custom time → Update appointment
- Status change → Adjust priority

## Common Scenarios

### Standard Turnover
- Guest checks out at 11 AM
- Service scheduled 12 PM - 4 PM
- Normal cleaning protocol
- Next guest arrives 4 PM+

### Same-Day Turnover
- Morning checkout at 10 AM
- Afternoon check-in at 4 PM
- Expedited service 11 AM - 2 PM
- Priority assignment

### Long-Term Departure
- 3-week stay ending
- Extra time allocated
- Deep cleaning protocol
- Special instructions added

### Owner Arrival
- Guest checkout Sunday
- Owner arrives Monday
- Premium service level
- Pre-arrival inspection

## Error Handling

### Common Issues
1. **Invalid Time Format**: Must be "HH:MM AM/PM"
2. **Schedule Conflicts**: Overlapping service windows
3. **Missing Dates**: Cannot calculate without check-in/out
4. **Timezone Mismatch**: MST vs system time

### Resolution Steps
1. Validate all time inputs
2. Check for existing appointments
3. Apply conflict resolution rules
4. Log all schedule changes

## Performance Considerations

### Optimization Strategies
- Cache property defaults
- Batch schedule calculations
- Minimize API calls
- Use database indexes

### Monitoring Points
- Schedule generation time
- Conflict detection rate
- Override frequency
- API response times

## Related Documentation

- See **BusinessLogicAtoZ.md** for detailed scheduling rules
- See **mermaid-flows.md** for visual workflows
- See **SYSTEM_LOGICAL_FLOW.md** for process descriptions

---

**Primary Code Location**: Various integration points
**Key Files**: 
- `/src/automation/scripts/airtable-automations/calculate-service-time.js`
- `/src/automation/scripts/hcp/schedule-sync.js`
- `/src/automation/scripts/shared/scheduleHelpers.js`
**Last Updated**: July 12, 2025