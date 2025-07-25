# CSV Processing System - Complete Technical Guide

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Key Components](#key-components)
4. [Data Flow](#data-flow)
5. [CSV Sources & Formats](#csv-sources--formats)
6. [Duplicate Detection Strategy](#duplicate-detection-strategy)
7. [Configuration](#configuration)
8. [Execution Flow](#execution-flow)
9. [Error Handling](#error-handling)
10. [Monitoring & Logging](#monitoring--logging)
11. [Common Issues & Solutions](#common-issues--solutions)
12. [Testing](#testing)
13. [Maintenance](#maintenance)

## Overview

The CSV Processing System is a core component of the property management automation suite that processes reservation data from multiple sources, primarily iTrip daily reports and Evolve property data. It handles CSV files delivered via CloudMailin webhooks (replacing the deprecated Gmail OAuth system) and processes them into Airtable with sophisticated duplicate detection and data transformation.

### Key Features
- **Multi-source Support**: Processes CSVs from iTrip, Evolve, and custom formats
- **CloudMailin Integration**: Webhook-based email attachment processing
- **Hybrid Duplicate Detection**: Handles both UID-based and property/dates/type matching
- **Environment Isolation**: Complete separation between development and production
- **Automated Processing**: Files move through defined directories with audit trails
- **Property Name Mapping**: Human-readable logging with property addresses

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CSV Processing Pipeline                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Email Receipt (CloudMailin)                             │
│     └─> Webhook → CSV saved to CSV_process/                │
│                                                             │
│  2. Controller (controller.py)                              │
│     └─> Checks "CSV Files" automation status               │
│                                                             │
│  3. CSV Processor Selection                                 │
│     └─> csvProcess_enhanced.py (wrapper)                   │
│         └─> csvProcess_hybrid.py (core processor v2.2.9)   │
│                                                             │
│  4. File Processing Loop                                    │
│     ├─> Read CSV file                                      │
│     ├─> Parse and validate data                            │
│     ├─> Transform to Airtable format                       │
│     ├─> Hybrid duplicate detection                         │
│     └─> Create/Update records                              │
│                                                             │
│  5. File Management                                         │
│     └─> Move to CSV_done_{environment}/                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Main Processor (`csvProcess_hybrid.py`)
Location: `/home/opc/automation/src/automation/scripts/CSVtoAirtable/csvProcess_hybrid.py`

**Core Responsibilities:**
- CSV file discovery and parsing
- Data validation and transformation
- Hybrid duplicate detection
- Airtable record creation/updates
- File movement and archival

**Key Features:**
```python
# Property name mapping for readable logs
self.property_mapping = self._load_property_mapping()

# Hybrid duplicate detection
def find_existing_record(self, res, all_reservation_records):
    """HYBRID APPROACH: Try UID first, then property+dates+type"""
    # Step 1: Try UID matching (with composite UID support)
    # Step 2: Fallback to property+dates+type matching
```

### 2. Enhanced Wrapper (`csvProcess_enhanced.py`)
Location: `/home/opc/automation/src/automation/scripts/CSVtoAirtable/csvProcess_enhanced.py`

**Purpose:** Provides compatibility layer and enhanced logging for the controller.

### 3. Legacy Processors
- `csvProcess.py`: Original processor (deprecated)
- `csvProcess_best.py`: Previous best version before hybrid

### 4. Configuration
- Environment detection via `ENVIRONMENT` variable
- Separate directories for dev/prod processing
- API keys and base IDs from environment

## Data Flow

### 1. CSV File Receipt
```
CloudMailin Webhook → /api/prod/csv-upload → CSV_process_production/
                  → /api/dev/csv-upload  → CSV_process_development/
```

### 2. File Processing
```python
# Discover CSV files
csv_files = glob.glob(os.path.join(csv_process_dir, "*.csv"))

# Process each file
for csv_file in csv_files:
    process_csv_file(csv_file)
    move_to_done_directory(csv_file)
```

### 3. Data Transformation
```python
# iTrip CSV → Airtable format
{
    "Property ID": [property_record_id],
    "Check-in Date": check_in_date,
    "Check-out Date": check_out_date,
    "Event Name": f"{first_name} {last_name}",
    "Entry Type": "Reservation",
    "Source": "iTrip",
    "UID": unique_identifier,
    "Guest First Name": first_name,
    "Guest Last Name": last_name,
    "Guest Email": email,
    "Guest Phone": phone
}
```

## CSV Sources & Formats

### 1. iTrip Format
**File Pattern**: `*Checkouts-Report*.csv` or timestamped files

**Key Fields:**
- `Address of Property` - Property address
- `Check-In` - Arrival date (M/D/YYYY format)
- `Check-Out` - Departure date (M/D/YYYY format)  
- `First` - Guest first name
- `Last` - Guest last name
- `Email` - Guest email
- `Phone` - Guest phone
- `Confirmation Code` - Booking reference

**UID Generation**: Based on confirmation code or property+dates+name hash

### 2. Evolve Format
**File Pattern**: `*_tab2.csv` (Tab 2 from Evolve portal)

**Key Fields:**
- `Property` - Property name
- `Check-in` - Arrival date
- `Checkout` - Departure date
- `Guest name` - Full guest name
- `Confirmation` - Booking reference
- `Status` - Reservation status

### 3. Custom Format Support
The system can handle custom CSV formats with mapping configuration.

## Duplicate Detection Strategy

### The Challenge
Different reservation systems handle unique identifiers differently:
- **iTrip**: Confirmation codes that may change
- **Evolve**: Dynamic references that regenerate
- **Manual entries**: No consistent UID

### The Solution: Hybrid Detection (v2.2.9)

```python
def find_existing_record(self, res, all_reservation_records):
    """Find existing record using HYBRID approach"""
    
    # Extract composite UID if present
    uid_parts = res.get("UID", "").split("_")
    base_uid = uid_parts[0]
    
    # HYBRID APPROACH: Try UID matching first
    all_records = []
    for (record_uid, source), records in all_reservation_records.items():
        record_uid_base = record_uid.split("_")[0]
        if record_uid_base == base_uid and source == res.get("Source"):
            all_records.extend(records)
    
    # Also check exact composite UID
    if res.get("property_id"):
        composite_uid = f"{base_uid}_{res['property_id']}"
        exact_match = all_reservation_records.get((composite_uid, res.get("Source")), [])
        if exact_match and exact_match not in all_records:
            all_records.extend(exact_match)
    
    # HYBRID APPROACH: If no UID match, try property+dates+type
    if not all_records and res.get("property_id"):
        checkin = res.get("Check-in Date")
        checkout = res.get("Check-out Date")
        entry_type = res.get("Entry Type", "Reservation")
        
        for (uid, source), records in all_reservation_records.items():
            for record in records:
                fields = record.get("fields", {})
                if (fields.get("Property ID") == [res["property_id"]] and
                    fields.get("Check-in Date") == checkin and
                    fields.get("Check-out Date") == checkout and
                    fields.get("Entry Type") == entry_type and
                    fields.get("Status") in ["New", "Modified"]):
                    logging.info(f"🔍 HYBRID: Found by property+dates+type")
                    return record
    
    # Find best match from all_records
    return self._find_best_match(all_records)
```

### Session-Based Duplicate Prevention
```python
# Track processed records within session
self.processed_in_session = set()

# Prevent duplicates within same CSV batch
key = (property_name, check_in_date, check_out_date, guest_name)
if key in self.processed_in_session:
    logging.warning(f"Skipping duplicate within session")
    continue
```

## Configuration

### Environment Setup
```bash
# Required environment variables
ENVIRONMENT=production|development
AIRTABLE_API_KEY_PROD=your_prod_key
AIRTABLE_API_KEY_DEV=your_dev_key
AIRTABLE_BASE_ID_PROD=appZzebEIqCU5R9ER
AIRTABLE_BASE_ID_DEV=app67yWFv0hKdl6jM
```

### Directory Structure
```
src/automation/scripts/
├── CSV_process_production/      # Incoming production CSVs
├── CSV_process_development/     # Incoming development CSVs
├── CSV_done_production/         # Processed production CSVs
├── CSV_done_development/        # Processed development CSVs
└── CSVtoAirtable/              # Processing scripts
```

### CloudMailin Webhook Configuration
```
Production: https://servativ.themomentcatchers.com/api/prod/csv-upload
Development: https://servativ.themomentcatchers.com/api/dev/csv-upload
```

## Execution Flow

### 1. Automation Controller
```python
# controller.py checks automation status
automation = get_automation_record("CSV Files")
if automation['Active']:
    run_csv_processor()
```

### 2. Main Processing
```python
def main():
    # 1. Setup environment
    environment = os.getenv('ENVIRONMENT', 'production')
    config = load_config(environment)
    
    # 2. Load property mapping
    property_mapping = load_property_mapping()
    
    # 3. Get existing reservations
    existing_records = get_all_reservations()
    
    # 4. Process CSV files
    for csv_file in get_csv_files():
        process_csv_file(csv_file, existing_records)
        move_to_done(csv_file)
    
    # 5. Update automation status
    update_automation_status(stats)
```

### 3. CSV Processing Logic
```python
def process_csv_file(filepath):
    # 1. Detect format
    format_type = detect_csv_format(filepath)
    
    # 2. Parse CSV
    with open(filepath, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # 3. Transform data
            reservation = transform_row(row, format_type)
            
            # 4. Find property
            property_id = find_property(reservation['address'])
            
            # 5. Check for existing
            existing = find_existing_record(reservation)
            
            # 6. Create or update
            if existing:
                update_reservation(existing['id'], reservation)
            else:
                create_reservation(reservation)
```

## Error Handling

### File-Level Error Handling
```python
try:
    process_csv_file(filepath)
except Exception as e:
    logging.error(f"Failed to process {filepath}: {e}")
    # Move to error directory instead of done
    move_to_error(filepath)
```

### Row-Level Error Handling
```python
for row_num, row in enumerate(reader, start=2):
    try:
        process_row(row)
    except Exception as e:
        logging.error(f"Row {row_num} error: {e}")
        stats['errors'].append({
            'file': filename,
            'row': row_num,
            'error': str(e)
        })
```

### Property Matching Error Handling
```python
def find_property_record(address):
    # Try exact match
    if address in property_address_map:
        return property_address_map[address]
    
    # Try normalized match
    normalized = normalize_address(address)
    if normalized in normalized_map:
        return normalized_map[normalized]
    
    # Log unmapped property
    logging.warning(f"No property found for: {address}")
    return None
```

## Monitoring & Logging

### Log Files
- **Production**: `/home/opc/automation/src/automation/logs/csv_sync_Production.log`
- **Development**: `/home/opc/automation/src/automation/logs/csv_sync_Development.log`

### Log Format with Property Names
```
2025-07-23 09:15:45 INFO: 🔍 Property "2065 W 1st Pl, Mesa, AZ" (recsKzsYIlFCXXmg5)
2025-07-23 09:15:45 INFO: 📅 Check-in: 2025-08-15, Check-out: 2025-08-20
2025-07-23 09:15:45 INFO: ✅ Created new reservation for John Smith
```

### Key Metrics
- Files processed
- Records created/updated/skipped
- Properties without mappings
- Processing time per file
- Error counts by type

## Common Issues & Solutions

### 1. Property Not Found
**Problem**: CSV contains property address not in Airtable

**Solution**: 
1. Check address formatting
2. Add property to Airtable
3. Update property mapping cache

### 2. Date Format Issues
**Problem**: Different date formats across sources

**Solution**:
```python
def parse_date(date_str):
    formats = [
        "%m/%d/%Y",    # M/D/YYYY
        "%Y-%m-%d",    # YYYY-MM-DD
        "%m-%d-%Y",    # MM-DD-YYYY
        "%d/%m/%Y"     # D/M/YYYY
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {date_str}")
```

### 3. Character Encoding Issues
**Problem**: Special characters in guest names

**Solution**:
```python
# Read with BOM handling
with open(filepath, 'r', encoding='utf-8-sig') as file:
    # Process file
```

### 4. Duplicate Records
**Problem**: Same reservation appearing multiple times

**Solution**: Hybrid duplicate detection with session tracking

## Testing

### Unit Tests
```python
# Test duplicate detection
def test_hybrid_duplicate_detection():
    processor = CSVProcessor()
    
    # Test UID matching
    existing = {"UID": "12345_rec123", "Property ID": ["rec123"]}
    new = {"UID": "12345", "property_id": "rec123"}
    assert processor.find_existing_record(new, records) == existing
    
    # Test property+dates matching
    existing = {
        "Property ID": ["rec123"],
        "Check-in Date": "2025-07-20",
        "Check-out Date": "2025-07-25"
    }
    new = {
        "property_id": "rec123",
        "Check-in Date": "2025-07-20",
        "Check-out Date": "2025-07-25"
    }
    assert processor.find_existing_record(new, records) == existing
```

### Integration Tests
```bash
# Test with sample file
ENVIRONMENT=development python3 csvProcess_hybrid.py \
    --test-file samples/itrip_sample.csv

# Dry run mode
ENVIRONMENT=production python3 csvProcess_hybrid.py --dry-run
```

### Test Data
Location: `/home/opc/automation/testing/test-scenarios/`
- `test_itrip_reservations.csv`
- `test_evolve_reservations.csv`
- `test_evolve_tab2.csv`

## Maintenance

### Regular Tasks

#### 1. Archive Processed Files
```bash
# Archive CSV_done files older than 30 days
find CSV_done_production -name "*.csv" -mtime +30 -exec gzip {} \;

# Move to archive directory
mkdir -p archives/$(date +%Y%m)
mv CSV_done_production/*.gz archives/$(date +%Y%m)/
```

#### 2. Clean Error Files
```bash
# Review and clean error directory
ls -la CSV_errors/
# Manually review and reprocess or archive
```

#### 3. Update Property Mappings
```python
# Refresh property cache
python3 update_property_mappings.py
```

### Performance Optimization

#### 1. Batch Processing
```python
# Process multiple records before API calls
batch = []
for row in reader:
    batch.append(transform_row(row))
    if len(batch) >= 100:
        process_batch(batch)
        batch = []
```

#### 2. Property Cache
```python
# Cache property lookups
@lru_cache(maxsize=1000)
def find_property_cached(address):
    return find_property_record(address)
```

### Troubleshooting Guide

#### Issue: "File not moving to done directory"
1. Check file permissions
2. Verify done directory exists
3. Check for process crashes during move

#### Issue: "Duplicate records created"
1. Check UID generation logic
2. Verify session tracking
3. Review hybrid detection logs

#### Issue: "CloudMailin webhook failing"
1. Check webhook URL configuration
2. Verify API endpoint is running
3. Check nginx routing rules

## Code Structure

```
CSVtoAirtable/
├── csvProcess_hybrid.py        # Main processor (v2.2.9)
├── csvProcess_enhanced.py      # Wrapper for controller
├── csvProcess.py              # Original version
├── csvProcess_best.py         # Previous best version
├── csv_formats.py             # Format detection logic
├── property_mapper.py         # Property matching utilities
└── test_csv_processor.py      # Test suite
```

## CloudMailin Integration

### Webhook Handler
```python
@app.route('/api/prod/csv-upload', methods=['POST'])
def handle_csv_upload():
    # Extract attachments
    for attachment in request.files:
        if attachment.filename.endswith('.csv'):
            # Save to process directory
            filepath = os.path.join(CSV_PROCESS_DIR, attachment.filename)
            attachment.save(filepath)
            
    return jsonify({"status": "accepted"}), 200
```

### Email Processing Flow
1. Email sent to designated address
2. CloudMailin receives email
3. Webhook triggered with attachments
4. CSV saved to process directory
5. Next automation run processes file

## Best Practices

1. **Always specify environment**: `ENVIRONMENT=production python3 script.py`
2. **Validate CSV format**: Check headers before processing
3. **Use property names in logs**: Makes debugging easier
4. **Archive processed files**: Maintain audit trail
5. **Monitor error rates**: Set alerts for high error counts

## Security Considerations

1. **File Validation**: Validate file types and sizes
2. **Input Sanitization**: Clean data before Airtable updates
3. **API Key Security**: Use environment variables
4. **Directory Permissions**: Restrict access to CSV directories
5. **Webhook Authentication**: Verify CloudMailin signatures

## Version History

- **v2.2.9** (July 2025): Hybrid duplicate detection matching ICS approach
- **v2.2.5** (July 2025): Property name logging enhancement
- **v2.2.0** (June 2025): CloudMailin integration
- **v2.1.0** (June 2025): Environment separation
- **v2.0.0** (May 2025): Complete rewrite

## Future Enhancements

1. **Format Auto-Detection**: ML-based format detection
2. **Data Validation Rules**: Configurable validation
3. **Real-time Processing**: Process on webhook receipt
4. **API Integration**: Direct API imports from sources
5. **Conflict Resolution**: Smart merge strategies

---

This documentation represents the complete CSV processing system as of v2.2.9. For questions or issues, refer to the troubleshooting guide or check the logs for detailed error messages.