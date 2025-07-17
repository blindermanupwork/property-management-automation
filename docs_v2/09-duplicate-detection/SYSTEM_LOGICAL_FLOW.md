# Duplicate Detection - Complete System Logical Flow

## Overview
This document describes the complete operational flow of the Duplicate Detection system, from UID generation through duplicate identification, status-based resolution, and automated cleanup processes.

## Primary Data Flow

### 1. UID Generation and Extraction Flow

#### CSV File UID Processing
When CSV files are imported into the system:
- System scans column headers for UID identifiers
- Flexible matching detects various UID column names
- Raw UID values are extracted and cleaned
- Missing UIDs trigger placeholder generation
- UIDs are stored directly in Airtable without modification

#### ICS Feed UID Processing  
When ICS calendar feeds are processed:
- VEVENT components provide original UIDs
- Property IDs from configuration create composite UIDs
- Dual indexing tracks both base and composite UIDs
- Multi-property feeds maintain UID uniqueness
- Composite format follows OriginalUID_PropertyID pattern

### 2. Duplicate Detection Operational Flow

#### Primary Detection Phase
During data import operations:
- System extracts UID from incoming record
- Database query checks for existing records with same UID
- Active status records take priority in matching
- Duplicate flags trigger resolution process
- Session tracking prevents within-batch duplicates

#### Secondary Detection Phase
When primary UID check passes:
- System builds property-date-type combination key
- Database searches for matching combinations
- Active status records evaluated for conflicts
- Multiple match scenarios escalate to resolution
- Clean records proceed to insertion

#### Cross-System Validation
For ICS feeds with complex scenarios:
- Base UID matching across property boundaries
- Date range overlap detection prevents double-bookings
- Source system authority determines precedence
- Historical UID changes tracked for continuity
- Feed-specific patterns validated against expectations

### 3. Status-Based Resolution Process

#### Conflict Analysis Phase
When duplicates are detected:
- System compares record completeness scores
- Last updated timestamps determine recency
- Source authority hierarchy applied
- Data quality metrics influence decisions
- User intervention thresholds evaluated

#### Resolution Decision Phase
Based on analysis results:
- Higher quality record designated as authoritative
- Lower quality records marked for status change
- Status change reasons documented
- Audit trail entries created
- Database updates executed with rollback capability

#### Status Update Execution
During resolution implementation:
- Active records updated to "Old" status
- Status change timestamps recorded
- Reason codes stored for audit purposes
- Related records cross-referenced
- System integrity checks validated

### 4. Session Tracking Management

#### Real-Time Deduplication
During active processing sessions:
- In-memory tracking maintains processed UID list
- Property-date combinations tracked for uniqueness
- Duplicate detection events recorded for later reference
- Session state persisted across processing batches
- Memory optimization prevents excessive resource usage

#### Batch Processing Coordination
For large import operations:
- Batch boundaries maintained for session tracking
- Cross-batch duplicate detection enabled
- Progress checkpoints allow resumption
- Error recovery preserves session state
- Completion validation ensures no missed duplicates

### 5. Automated Cleanup Operations

#### Active UID Violation Detection
System regularly scans for data integrity violations:
- Database queries group records by UID
- Active status counts calculated per UID
- Violations identified where count exceeds one
- Record details collected for resolution planning
- Priority scoring applied based on impact

#### Duplicate Resolution Execution
When violations are addressed:
- Newest records by ID determined as authoritative
- Older records marked for status changes
- Batch updates executed with error handling
- Success metrics tracked for monitoring
- Rollback capabilities maintained for safety

#### Property-Date Conflict Analysis
For complex duplicate scenarios:
- Property-date combinations analyzed for multiple UIDs
- Legitimate vs problematic conflicts classified
- Resolution strategies developed per conflict type
- Manual intervention queued for complex cases
- Automated fixes applied where safe

### 6. Orphaned Record Management

#### Feed Status Monitoring
System tracks feed health and activity:
- Active feed lists maintained in configuration
- Feed processing timestamps monitored
- Inactive feed detection triggers orphan identification
- Grace periods applied before marking orphans
- Feed reactivation detected to restore orphaned records

#### Pattern Mismatch Detection
For UID consistency validation:
- Current feed patterns analyzed from recent imports
- Historical records compared against current patterns
- Mismatched UIDs flagged for investigation
- Pattern evolution tracked to detect systematic changes
- False positive prevention through threshold tuning

#### Orphan Resolution Process
When orphaned records are identified:
- Verification periods allow for feed recovery
- Confirmation checks prevent premature cleanup
- Status updates applied with proper documentation
- Historical preservation maintained
- Recovery procedures documented for restoration

### 7. ICS Removal Detection Flow

#### Missing Event Identification
During ICS feed processing:
- Existing record inventory built from database
- Current feed event inventory collected
- Missing event detection through set operations
- Date-based filtering prevents false positives
- Duplicate tracking prevents incorrect removals

#### Removal Validation Process
Before marking events as removed:
- Checkout date validation prevents historical removals
- Duplicate detection tracking checked for conflicts
- Manual intervention flags respected
- Batch operation integrity maintained
- Reversal procedures available for mistakes

### 8. Race Condition Prevention

#### Concurrent Processing Protection
When multiple processes operate simultaneously:
- Record fetching includes current state validation
- Status checks performed immediately before updates
- Optimistic locking prevents conflicting changes
- Failed update detection triggers retry logic
- Success confirmation validates expected outcomes

#### Error Recovery Mechanisms
For handling processing failures:
- Individual record failures isolated from batch operations
- Retry logic with exponential backoff implemented
- Error classification enables appropriate responses
- Manual intervention queued for unresolvable conflicts
- System state restoration procedures available

## State Management Flow

### Record Status States
- **New**: Freshly imported, ready for processing
- **Modified**: Updated from original source
- **Removed**: Detected as missing from source
- **Old**: Superseded by newer/better record

### UID Tracking States
- **Unique**: Single active record per UID
- **Violated**: Multiple active records per UID
- **Orphaned**: UID from inactive source
- **Mismatched**: UID doesn't match current patterns

### Processing States
- **Importing**: Currently being processed
- **Analyzing**: Under duplicate detection analysis
- **Resolving**: Undergoing conflict resolution
- **Completed**: Processing finished successfully
- **Failed**: Processing encountered errors

## Error Handling Flows

### Import Error Recovery
- Malformed UID handling with placeholder generation
- Missing data compensation through pattern matching
- Source system timeout recovery with retry logic
- Data validation failures trigger manual review queues

### Duplicate Resolution Errors
- Ambiguous conflicts escalated to manual intervention
- Database constraint violations handled gracefully
- Status update failures trigger rollback procedures
- Audit trail corruption detected and repaired

### Cleanup Operation Errors
- Batch processing failures isolated per operation
- Individual record errors logged with context
- System resource limits respected during operations
- Recovery procedures restore system to known state

## Performance Optimization Flow

### Database Query Optimization
- UID indexes enable fast duplicate lookups
- Property-date composite indexes support conflict detection
- Status-based queries optimized for active record filtering
- Batch operations minimize database round trips

### Memory Management
- Session tracking uses efficient data structures
- Large batch operations employ streaming techniques
- Garbage collection optimized for long-running processes
- Resource monitoring prevents memory exhaustion

### Processing Efficiency
- Parallel processing for independent operations
- Early termination for obvious non-duplicates
- Caching strategies for frequently accessed data
- Lazy loading reduces unnecessary data retrieval

## Monitoring and Alerting

### Key Metrics Tracking
- Duplicate detection rate per source system
- Resolution success rate and timing
- Cleanup operation effectiveness
- System resource utilization during processing

### Alert Conditions
- Unusual spike in duplicate rates
- High failure rates in resolution processes
- Extended processing times indicating issues
- Resource exhaustion warnings

### Audit Trail Maintenance
- All status changes logged with context
- User actions tracked for accountability
- System operations documented for troubleshooting
- Historical data preserved for compliance

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Primary Code**: Distributed across CSV and ICS processing modules
**Related**: BusinessLogicAtoZ.md, mermaid-flows.md