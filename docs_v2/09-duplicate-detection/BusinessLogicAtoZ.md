# Duplicate Detection - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Duplicate Detection system, including UID generation, duplicate identification, status-based resolution, and automated cleanup processes.

## Core Business Purpose

The Duplicate Detection system maintains data integrity by preventing reservation duplicates while preserving historical records. It handles complex scenarios involving multiple data sources, UID changes, and temporal variations.

## Business Workflows

### 1. UID Generation and Extraction

#### **CSV UID Extraction**
**Process**: Direct extraction from CSV files during import
**Business Logic**:
```python
# CSV UID column detection
COL_UID = {"reservationid", "reservation", "booking#", "booking #", "booking"}

def extract_csv_uid(row):
    # Find UID column using flexible matching
    for uid_col in row.keys():
        if uid_col.lower().strip() in COL_UID:
            uid_raw = row[uid_col].strip()
            
            # Clean and validate
            if uid_raw and uid_raw not in ["", "None", "null"]:
                return uid_raw
    
    # Generate placeholder if missing
    return f"CSV_{timestamp}_{row_index}"
```

#### **ICS UID Processing**
**Process**: Extract from VEVENT UID and create composite identifiers
**Business Logic**:
```python
def process_ics_uid(vevent_component, property_id=None):
    # Extract original UID from VEVENT
    original_uid = str(vevent_component.get("UID", "")).strip()
    
    # Create composite UID for multi-property feeds
    if property_id:
        composite_uid = f"{original_uid}_{property_id}"
    else:
        composite_uid = original_uid
    
    return {
        'original_uid': original_uid,
        'composite_uid': composite_uid,
        'property_suffix': property_id
    }
```

### 2. Duplicate Detection Engine

#### **CSV Duplicate Detection**
**Trigger**: During CSV file processing
**Detection Criteria**:
```python
def check_csv_duplicate(record):
    # Primary check: Exact UID match
    existing_by_uid = query_airtable(
        filter_by_formula=f"{{Reservation UID}} = '{record.uid}'"
    )
    
    if existing_by_uid:
        return handle_uid_duplicate(existing_by_uid, record)
    
    # Secondary check: Property + Date + Type combination
    duplicate_check_formula = f"""
    AND(
        {{Property ID}} = '{record.property_id}',
        {{Check-in Date}} = '{record.checkin}',
        {{Check-out Date}} = '{record.checkout}',
        {{Entry Type}} = '{record.entry_type}',
        OR(
            {{Status}} = 'New',
            {{Status}} = 'Modified'
        )
    )
    """
    
    existing_by_details = query_airtable(
        filter_by_formula=duplicate_check_formula
    )
    
    return len(existing_by_details) > 0
```

#### **ICS Duplicate Detection**
**Trigger**: During ICS feed processing
**Complex Logic**:
```python
def detect_ics_duplicates(events, existing_records):
    duplicates_found = set()
    
    for event in events:
        composite_uid = event['composite_uid']
        original_uid = event['original_uid']
        
        # Check 1: Exact composite UID match
        if composite_uid in existing_records:
            duplicates_found.add((composite_uid, event['dates']))
            continue
        
        # Check 2: Cross-property base UID check
        base_matches = find_base_uid_matches(original_uid, existing_records)
        if base_matches:
            for match in base_matches:
                if date_ranges_overlap(event['dates'], match['dates']):
                    duplicates_found.add((composite_uid, event['dates']))
        
        # Check 3: Property-date combination check
        property_date_matches = find_property_date_matches(
            event['property_id'], 
            event['dates'],
            existing_records
        )
        
        if property_date_matches:
            duplicates_found.add((composite_uid, event['dates']))
    
    return duplicates_found
```

### 3. Status-Based Duplicate Resolution

#### **Active Status Management**
**Business Rule**: Only ONE record per UID can have active status
**Active Statuses**: "New", "Modified", "Removed"
**Inactive Status**: "Old"

```python
def resolve_uid_conflict(existing_record, new_record):
    # Determine which record should remain active
    keep_existing = should_keep_existing(existing_record, new_record)
    
    if keep_existing:
        # Mark new record as old
        new_record['Status'] = 'Old'
        new_record['Duplication Reason'] = f"Duplicate of {existing_record.id}"
        
        # Update existing if data changed
        if has_significant_changes(existing_record, new_record):
            update_existing_record(existing_record, new_record)
            
    else:
        # Mark existing as old, keep new as active
        mark_records_as_old(
            [existing_record],
            f"Superseded by newer record {new_record.id}"
        )
        new_record['Status'] = 'New'
        
    return new_record
```

#### **Record Comparison Logic**
**Determining Authority**:
```python
def should_keep_existing(existing, new):
    # 1. Data completeness check
    existing_completeness = calculate_completeness(existing)
    new_completeness = calculate_completeness(new)
    
    if new_completeness > existing_completeness:
        return False  # New record more complete
    
    # 2. Recency check (Last Updated field)
    if new['Last Updated'] > existing['Last Updated']:
        return False  # New record more recent
    
    # 3. Source authority hierarchy
    source_priority = {
        'Airbnb': 1,
        'VRBO': 2, 
        'Evolve': 3,
        'CSV': 4,
        'Manual': 5
    }
    
    existing_priority = source_priority.get(existing['Source'], 999)
    new_priority = source_priority.get(new['Source'], 999)
    
    if new_priority < existing_priority:
        return False  # New source has higher authority
    
    # 4. Default: keep existing
    return True
```

### 4. Session Tracking for Real-Time Deduplication

#### **In-Process Duplicate Prevention**
**Purpose**: Prevent duplicates within single processing session
**Implementation**:
```python
class SessionDuplicateTracker:
    def __init__(self):
        self.processed_uids = set()
        self.property_date_combinations = set()
        self.duplicate_detected_dates = set()
    
    def check_session_duplicate(self, record):
        # Check UID uniqueness in session
        if record.uid in self.processed_uids:
            return True
        
        # Check property-date uniqueness
        property_date_key = (
            record.property_id,
            record.checkin_date,
            record.checkout_date,
            record.entry_type
        )
        
        if property_date_key in self.property_date_combinations:
            return True
        
        # Track for future checks
        self.processed_uids.add(record.uid)
        self.property_date_combinations.add(property_date_key)
        
        return False
    
    def mark_duplicate_detected(self, property_id, dates):
        # Prevents false removal during ICS processing
        self.duplicate_detected_dates.add((property_id, dates))
```

### 5. Automated Cleanup Processes

#### **Find Duplicate Active UIDs**
**Purpose**: Identify UIDs with multiple active records
**Business Logic**:
```python
def find_duplicate_active_uids():
    # Query all records grouped by UID
    all_records = fetch_all_reservations()
    uid_groups = group_by_uid(all_records)
    
    violations = []
    
    for uid, records in uid_groups.items():
        active_records = [r for r in records if r.status in ACTIVE_STATUSES]
        
        if len(active_records) > 1:
            violations.append({
                'uid': uid,
                'active_count': len(active_records),
                'records': active_records,
                'total_count': len(records)
            })
    
    return violations
```

#### **Fix UID Duplicates**
**Purpose**: Resolve multiple active records per UID
**Resolution Strategy**:
```python
def fix_uid_duplicates(violations, execute=False):
    fixes_applied = []
    
    for violation in violations:
        active_records = violation['records']
        
        # Sort by ID descending (newest first)
        active_records.sort(key=lambda r: r.id, reverse=True)
        
        # Keep newest, mark others as old
        keep_record = active_records[0]
        old_records = active_records[1:]
        
        if execute:
            mark_records_as_old(
                old_records,
                f"Duplicate UID resolved - keeping record {keep_record.id}"
            )
        
        fixes_applied.append({
            'uid': violation['uid'],
            'kept_record': keep_record.id,
            'marked_old': [r.id for r in old_records]
        })
    
    return fixes_applied
```

#### **Property-Date Duplicate Analysis**
**Purpose**: Find same property + date with different UIDs
**Business Logic**:
```python
def find_property_date_duplicates():
    # Group by property + check-in + check-out + entry type
    all_active = fetch_active_reservations()
    
    property_date_groups = {}
    for record in all_active:
        key = (
            record.property_id,
            record.checkin_date,
            record.checkout_date,
            record.entry_type
        )
        
        if key not in property_date_groups:
            property_date_groups[key] = []
        property_date_groups[key].append(record)
    
    # Find groups with multiple UIDs
    multi_uid_groups = {
        key: records for key, records in property_date_groups.items()
        if len(set(r.uid for r in records)) > 1
    }
    
    return analyze_multi_uid_conflicts(multi_uid_groups)
```

### 6. ICS Removal Detection Logic

#### **Missing Event Detection**
**Purpose**: Identify reservations removed from calendar feeds
**Business Logic**:
```python
def detect_removed_events(existing_records, current_events, feed_url):
    # Build map of what currently exists
    existing_map = {
        (record.composite_uid, record.feed_url): record
        for record in existing_records
        if record.feed_url == feed_url and record.status in ACTIVE_STATUSES
    }
    
    # Build map of what's in current feed
    current_map = {
        (event.composite_uid, feed_url): event
        for event in current_events
    }
    
    # Find missing keys
    missing_keys = set(existing_map.keys()) - set(current_map.keys())
    
    removal_candidates = []
    for missing_key in missing_keys:
        record = existing_map[missing_key]
        
        # Skip if checkout date is in the past
        if record.checkout_date < today():
            continue
        
        # Skip if duplicate was detected for this property-date
        if was_duplicate_detected(record.property_id, record.dates):
            continue
        
        # Mark as removal candidate
        removal_candidates.append(record)
    
    return removal_candidates
```

### 7. Orphaned Record Management

#### **Inactive Feed Orphan Detection**
**Purpose**: Find records from feeds no longer being processed
**Business Logic**:
```python
def find_inactive_feed_orphans():
    active_feeds = get_currently_processed_feeds()
    all_ics_records = fetch_ics_records()
    
    orphaned_records = []
    
    for record in all_ics_records:
        if record.feed_url not in active_feeds:
            # Check if feed was recently active
            if feed_inactive_for_days(record.feed_url) > 7:
                orphaned_records.append({
                    'record': record,
                    'reason': 'Feed no longer active',
                    'last_feed_activity': get_last_feed_activity(record.feed_url)
                })
    
    return orphaned_records
```

#### **UID Mismatch Pattern Detection**
**Purpose**: Find UIDs that don't match current feed patterns
**Business Logic**:
```python
def find_uid_mismatch_patterns():
    all_records = fetch_all_reservations()
    current_patterns = analyze_current_uid_patterns()
    
    mismatched_records = []
    
    for record in all_records:
        if record.source == 'ICS':
            expected_pattern = current_patterns.get(record.feed_url)
            if expected_pattern and not matches_pattern(record.uid, expected_pattern):
                mismatched_records.append({
                    'record': record,
                    'expected_pattern': expected_pattern,
                    'actual_uid': record.uid,
                    'mismatch_type': classify_mismatch(record.uid, expected_pattern)
                })
    
    return mismatched_records
```

### 8. Race Condition Handling

#### **Concurrent Processing Protection**
**Purpose**: Handle multiple processes updating same records
**Business Logic**:
```python
def mark_records_as_old_safely(records, reason):
    successful_updates = []
    failed_updates = []
    
    for record in records:
        try:
            # Re-fetch current record state
            current_record = fetch_record_by_id(record.id)
            
            # Check if still needs updating
            if current_record.status in ACTIVE_STATUSES:
                update_result = update_record(
                    record.id,
                    {
                        'Status': 'Old',
                        'Status Change Reason': reason,
                        'Status Changed At': datetime.now().isoformat()
                    }
                )
                successful_updates.append(update_result)
            else:
                # Already updated by another process
                skipped_updates.append({
                    'id': record.id,
                    'reason': 'Already updated by another process'
                })
                
        except Exception as e:
            failed_updates.append({
                'id': record.id,
                'error': str(e)
            })
    
    return {
        'successful': successful_updates,
        'failed': failed_updates,
        'skipped': skipped_updates
    }
```

## Critical Business Rules

### UID Management Rules
1. **Uniqueness**: Each UID must be unique within active records
2. **Persistence**: UIDs should remain stable across imports
3. **Composition**: ICS UIDs may include property suffixes
4. **Validation**: Empty/null UIDs generate placeholder values

### Status Management Rules
1. **Single Active**: Only one record per UID can have active status
2. **Status Hierarchy**: New > Modified > Removed > Old
3. **Preservation**: Old records maintain historical data
4. **Audit Trail**: All status changes logged with reasons

### Duplicate Resolution Rules
1. **Data Quality**: More complete records take precedence
2. **Recency**: Newer records preferred over older ones
3. **Source Authority**: Airbnb > VRBO > Evolve > CSV > Manual
4. **Safety**: Default to keeping existing when uncertain

### Cleanup Operation Rules
1. **Dry Run First**: Always test cleanup operations before execution
2. **Batch Limits**: Process in small batches to avoid API limits
3. **Error Recovery**: Continue processing despite individual failures
4. **Audit Logging**: Log all cleanup actions for review

### Race Condition Rules
1. **Re-fetch**: Always check current state before updates
2. **Concurrency**: Handle multiple processes gracefully
3. **Rollback**: Provide mechanisms to undo incorrect changes
4. **Monitoring**: Alert on unusual duplicate rates

## Duplicate Categories

### Type A: Exact Duplicates
- Same UID, property, dates, guest
- Different import sources or times
- **Resolution**: Keep newest, mark others as "Old"

### Type B: Data Variants
- Same core reservation, minor differences
- Typos in guest names, slight date variations
- **Resolution**: Merge data, prefer authoritative source

### Type C: UID Changes
- Same reservation, UID changed by source system
- Common with Airbnb UID modifications
- **Resolution**: Mark old UID as "Old", keep new as active

### Type D: System Conflicts
- Multiple systems claiming same property-date
- Data synchronization timing issues
- **Resolution**: Manual review required

### Type E: Orphaned Records
- Records from inactive feeds or removed sources
- No longer receiving updates
- **Resolution**: Mark as "Old" after verification period

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Duplicate Detection business logic
**Primary Code**: CSV and ICS processing modules