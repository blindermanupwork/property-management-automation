# Duplicate Detection Documentation

## Overview

The Duplicate Detection feature prevents and manages reservation duplicates through sophisticated UID generation, validation, and cleanup processes. This feature ensures data integrity by detecting duplicate bookings while preserving historical records through status management.

## Quick Navigation

- **BusinessLogicAtoZ.md** - Complete business rules for UID generation and duplicate handling
- **SYSTEM_LOGICAL_FLOW.md** - Text-based operational flow descriptions
- **mermaid-flows.md** - Visual workflow diagrams
- **version-history.md** - Feature change tracking

## Key Capabilities

### 1. UID Generation System
- Create unique identifiers from reservation data
- Handle composite UIDs for property-date combinations  
- Support base UIDs for individual reservations
- Validate UID uniqueness across the system

### 2. Duplicate Detection Engine
- Identify potential duplicates during CSV import
- Check active reservations for conflicts
- Detect property-date combinations with multiple active UIDs
- Find orphaned records without matching UIDs

### 3. Status-Based Management
- Mark old duplicates as "Old" status instead of deletion
- Preserve historical data for audit trails
- Allow multiple "Old" records per UID
- Maintain single "Active" record per UID

### 4. Cleanup Automation
- Automated scripts for duplicate resolution
- Manual intervention options for edge cases
- Batch processing for large-scale cleanup
- Detailed logging of all cleanup actions

## Business Context

### Property Management Challenges
1. **Multiple Booking Sources**: Same reservation may appear from different channels
2. **Data Import Timing**: CSVs processed at different times may contain duplicates
3. **System Integration**: Evolve, Airbnb, VRBO bookings may overlap
4. **Historical Preservation**: Need to maintain audit trails

### Key Decision Points
- **UID Collision**: When two active records have same UID
- **Property-Date Conflicts**: Multiple reservations for same property/date
- **Source Authority**: Which record is considered authoritative
- **Status Updates**: When to mark records as "Old" vs keeping active

## UID Types and Structure

### Base UID Format
```
Property-Guest-CheckinDate-CheckoutDate
```
Example: `26208N43rd-SMITH-20250615-20250622`

### Composite UID Components
- **Property**: Normalized address (remove spaces, special chars)
- **Guest**: Last name in uppercase
- **Dates**: YYYYMMDD format
- **Separators**: Hyphens between components

### Special Cases
- Multiple guests: Use primary reservation holder
- Missing data: Generate partial UIDs with placeholders
- Character encoding: Handle Unicode characters appropriately

## Duplicate Detection Scenarios

### 1. Exact Duplicates
- Same UID, same property, same dates
- Same guest name and contact information
- Different source systems (CSV vs ICS vs manual entry)

### 2. Near Duplicates  
- Similar guest names (typos, variations)
- Slight date differences (check-in/out variations)
- Property address variations

### 3. Property-Date Conflicts
- Different guests, same property, overlapping dates
- Data entry errors causing double bookings
- System synchronization timing issues

### 4. Orphaned Records
- Records with UIDs not found in other systems
- Cancelled reservations not properly updated
- Data corruption or import failures

## Status Management Strategy

### Active Records
- Only one "Active" record allowed per UID
- Represents current, valid reservation
- Used for job creation and scheduling

### Old Records
- Multiple "Old" records allowed per UID
- Preserves historical information
- Maintains audit trail for compliance

### Processing Rules
```javascript
// Duplicate resolution logic
if (existingActiveRecord) {
    if (newRecord.isMoreRecent || newRecord.isMoreComplete) {
        existingRecord.status = "Old";
        newRecord.status = "Active";
    } else {
        newRecord.status = "Old";
    }
}
```

## Cleanup Script Operations

### 1. Find Duplicate Active UIDs
- Scan entire reservation table
- Group by UID where multiple "Active" records exist
- Generate cleanup recommendations

### 2. Fix UID Duplicates
- Identify authoritative record (newest, most complete)
- Mark others as "Old" status
- Log all status changes

### 3. Property-Date Analysis
- Find properties with multiple active reservations same date
- Check for legitimate vs problematic overlaps
- Suggest resolution strategies

### 4. Orphaned Record Detection
- Identify UIDs only appearing once
- Check for matching patterns in other systems
- Flag for manual review

## Error Handling

### Common Issues
1. **UID Generation Failures**: Missing required data
2. **Constraint Violations**: Database uniqueness conflicts
3. **Status Inconsistencies**: Multiple active records
4. **Data Quality**: Invalid dates, malformed names

### Resolution Strategies
1. Generate placeholder UIDs for incomplete data
2. Use timestamp-based tiebreakers
3. Escalate to manual review for complex cases
4. Maintain detailed error logs

## Integration Points

### 1. CSV Import Process
- UID generation during initial import
- Duplicate checking before insertion
- Status assignment based on existing records

### 2. ICS Feed Sync  
- Composite UID validation
- Cross-system duplicate detection
- Historical data preservation

### 3. Manual Data Entry
- Real-time duplicate checking
- User notification of potential conflicts
- Override options for legitimate duplicates

### 4. Job Creation System
- Only process "Active" status records
- Skip "Old" records for service creation
- Maintain UID references in job records

## Performance Considerations

### Optimization Strategies
- Index UID fields for fast lookups
- Batch duplicate detection operations
- Cache recent UID checks
- Use database constraints where possible

### Monitoring Points
- UID generation success rate
- Duplicate detection accuracy
- Cleanup operation performance
- Data integrity metrics

## Related Documentation

- See **BusinessLogicAtoZ.md** for detailed duplicate handling rules
- See **mermaid-flows.md** for visual duplicate detection workflows
- See **SYSTEM_LOGICAL_FLOW.md** for process descriptions

---

**Primary Code Location**: Multiple integration points
**Key Files**: 
- `/src/automation/scripts/find-duplicate-active-uids.py`
- `/src/automation/scripts/fix-uid-duplicates.py`
- `/src/automation/scripts/find-property-date-duplicates-active.py`
- `/src/automation/scripts/CSVtoAirtable/csvProcess.py`
**Last Updated**: July 12, 2025