# CSV Processing - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of CSV processing for property management reservations, including CloudMailin webhook integration, file processing workflows, and Airtable synchronization.

## Core Business Purpose

The CSV processing system automatically converts email-attached reservation spreadsheets from property management companies (iTrip, Evolve) into structured Airtable records that can generate cleaning service jobs.

## Business Workflows

### 1. Email Receipt and Processing

#### **CloudMailin Webhook Integration**
**Endpoint**: `https://servativ.themomentcatchers.com/webhooks/csv-email`
**Trigger**: Email arrives at configured CloudMailin addresses
**Authentication**: CloudMailin signature verification

**Business Logic**:
1. **Email Reception**:
   - CloudMailin receives emails at environment-specific addresses
   - Extracts CSV attachments from email
   - Creates webhook payload with Base64-encoded attachment

2. **Webhook Processing**:
   ```python
   def process_cloudmail_webhook(request):
       # Verify CloudMailin signature
       if not verify_signature(request.headers, request.body):
           return 403  # But actually returns 200 to prevent disabling
       
       # Extract attachments
       for attachment in request.json['attachments']:
           if attachment['content_type'] == 'text/csv':
               process_csv_attachment(attachment)
   ```

3. **File Saving**:
   - Decode Base64 attachment content
   - Save to `CSV_process_[environment]/` directory
   - Filename: `{timestamp}_{original_filename}.csv`
   - Example: `20250711_143022_itrip_reservations.csv`

### 2. CSV Format Detection and Processing

#### **Supplier Detection Logic**
**Business Rules**:
1. **iTrip Detection**:
   - Filename contains 'itrip' OR
   - CSV has 'Company Use' column OR
   - Email from known iTrip addresses

2. **Evolve Detection**:
   - Filename contains 'evolve' OR
   - CSV has 'address' column (lowercase) OR
   - Specific column pattern matching

3. **Unknown Handling**:
   - Attempt best-effort parsing
   - Log warning for manual review
   - Process with generic mapping

#### **Column Mapping Strategy**
```python
# iTrip Standard Columns
ITRIP_COLUMNS = {
    'Property': 'Property Name',
    'Guest Name': 'Guest Full Name',
    'Check In': 'Check-in Date',
    'Check Out': 'Check-out Date',
    'Company Use': 'Confirmation Number',
    'Guest Phone': 'Phone Number',
    'Guest Email': 'Email Address'
}

# Evolve Standard Columns  
EVOLVE_COLUMNS = {
    'address': 'Property Name',
    'guestName': 'Guest Full Name',
    'checkIn': 'Check-in Date',
    'checkOut': 'Check-out Date',
    'confirmationCode': 'Confirmation Number',
    'listingNumber': 'Property ID'
}
```

### 3. Data Validation and Transformation

#### **Date Processing Rules**
**Business Logic**:
1. **Format Detection**:
   - iTrip: MM/DD/YYYY format
   - Evolve: YYYY-MM-DD format
   - Flexible parsing for variations

2. **Validation**:
   ```python
   def validate_dates(checkin, checkout):
       # Parse dates
       checkin_date = parse_date(checkin)
       checkout_date = parse_date(checkout)
       
       # Business rules
       if checkout_date <= checkin_date:
           raise ValueError("Check-out must be after check-in")
       
       # Date range limits
       today = datetime.now().date()
       if checkin_date < today - timedelta(days=180):
           raise ValueError("Check-in too far in past")
       
       if checkin_date > today + timedelta(days=365):
           raise ValueError("Check-in too far in future")
   ```

3. **Normalization**:
   - Convert all dates to YYYY-MM-DD format
   - Strip time components
   - Handle timezone issues

#### **Guest Name Processing**
**Business Logic**:
1. **Name Parsing**:
   ```python
   def parse_guest_name(full_name):
       if not full_name or full_name.strip() == '':
           return None, None  # Indicates Block entry
       
       parts = full_name.strip().split()
       if len(parts) >= 2:
           first_name = ' '.join(parts[:-1])
           last_name = parts[-1]
       else:
           first_name = parts[0]
           last_name = parts[0]  # Use first name as last
       
       return first_name, last_name
   ```

2. **Entry Type Determination**:
   - Has guest name → Entry Type = "Reservation"
   - No guest name → Entry Type = "Block"
   - Keywords override: 'owner', 'block', 'maintenance' → "Block"

### 4. UID Generation and Duplicate Detection

#### **UID Generation Algorithm**
**Format**: `{source}_{property_slug}_{checkin}_{checkout}_{guest_lastname}`

**Implementation**:
```python
def generate_uid(source, property_name, checkin, checkout, guest_name):
    # Extract last name
    _, last_name = parse_guest_name(guest_name)
    if not last_name:
        last_name = 'block'
    
    # Create property slug
    property_slug = property_name.lower()
    property_slug = re.sub(r'[^a-z0-9]+', '_', property_slug)
    property_slug = property_slug.strip('_')
    
    # Format dates
    checkin_str = checkin.strftime('%Y-%m-%d')
    checkout_str = checkout.strftime('%Y-%m-%d')
    
    # Build UID
    uid = f"{source}_{property_slug}_{checkin_str}_{checkout_str}_{last_name.lower()}"
    return uid
```

#### **Duplicate Detection Process**
**Business Logic**:
1. **UID Lookup**:
   - Search Airtable for existing UID
   - Use filterByFormula: `{UID} = 'generated_uid'`

2. **Duplicate Handling**:
   - If found: Update existing record
   - If not found: Create new record
   - Never create duplicate UIDs

3. **Composite UID Fix** (June 23, 2025):
   - Issue: Lookup used composite UID format
   - CSV generates base UID format
   - Solution: Normalize UID format for lookups

### 5. Property Matching and Validation

#### **Property Lookup Process**
**Business Logic**:
1. **Exact Match First**:
   ```python
   def find_property(property_name, airtable):
       # Try exact match
       formula = f"{{Property Name}} = '{property_name}'"
       matches = airtable.search('Properties', formula)
       
       if matches:
           return matches[0]['id']
   ```

2. **Fuzzy Matching Fallback**:
   - Calculate similarity scores
   - Suggest closest matches
   - Log for manual review

3. **Validation Requirements**:
   - Property must exist in Airtable
   - Property must be active
   - Property must have valid address

### 6. Airtable Record Creation/Update

#### **Record Creation Process**
**Business Logic**:
1. **Field Mapping**:
   ```python
   airtable_fields = {
       'UID': uid,
       'Property': [property_record_id],  # Linked record
       'Guest Name': guest_full_name,
       'Check-in Date': checkin_date,
       'Check-out Date': checkout_date,
       'Entry Type': entry_type,
       'Status': 'New',
       'Source': 'CSV',
       'Confirmation Number': confirmation,
       'Phone': guest_phone,
       'Email': guest_email,
       'Created Date': datetime.now().isoformat()
   }
   ```

2. **Linked Records**:
   - Property: Must link to existing Property record
   - Status starts as "New"
   - Source tracks origin

3. **Update Logic**:
   - Preserve certain fields on update
   - Update Last Modified timestamp
   - Log changes in notes

### 7. File Management and Archival

#### **File Movement Workflow**
**Business Logic**:
1. **Processing States**:
   - `CSV_process_[env]/`: Files awaiting processing
   - `CSV_done_[env]/`: Successfully processed files
   - Failed files remain in process folder

2. **Atomic Operations**:
   ```python
   def move_to_done(filepath):
       try:
           # Process complete
           done_dir = get_done_directory()
           filename = os.path.basename(filepath)
           done_path = os.path.join(done_dir, filename)
           
           # Atomic move
           shutil.move(filepath, done_path)
           logger.info(f"Moved {filename} to done folder")
       except Exception as e:
           logger.error(f"Failed to move file: {e}")
           # File remains for retry
   ```

3. **Retention Policy**:
   - Keep processed files for 30 days
   - Compress older files
   - Never delete source data

### 8. Error Handling and Recovery

#### **Error Types and Handling**
**Business Logic**:
1. **Validation Errors**:
   - Missing required fields
   - Invalid date formats
   - Property not found
   - Action: Skip record, log error, continue

2. **System Errors**:
   - Airtable API failures
   - File system errors
   - Memory issues
   - Action: Retry with backoff

3. **Recovery Process**:
   ```python
   def process_csv_with_recovery(filepath):
       try:
           process_csv_file(filepath)
           move_to_done(filepath)
       except ValidationError as e:
           logger.error(f"Validation error in {filepath}: {e}")
           # Keep in process folder for manual review
       except SystemError as e:
           logger.error(f"System error processing {filepath}: {e}")
           # Will retry on next run
       except Exception as e:
           logger.error(f"Unexpected error: {e}", exc_info=True)
           # Alert admin
   ```

## Environment-Specific Configuration

### Development Environment
- **CSV Directory**: `CSV_process_development/`
- **Archive Directory**: `CSV_done_development/`
- **CloudMailin Webhook**: Dev-specific URL
- **Airtable Base**: `app67yWFv0hKdl6jM`

### Production Environment  
- **CSV Directory**: `CSV_process_production/`
- **Archive Directory**: `CSV_done_production/`
- **CloudMailin Webhook**: Prod-specific URL
- **Airtable Base**: `appZzebEIqCU5R9ER`

## Critical Business Rules

### Data Integrity Rules
1. **UID Uniqueness**: Every reservation has unique identifier
2. **No Data Loss**: Failed files remain for retry
3. **Audit Trail**: All operations logged
4. **Soft Failures**: Individual record failures don't stop processing

### Processing Rules
1. **Date Validation**: 6 months past, 12 months future
2. **Property Required**: Must match existing property
3. **Entry Type Logic**: Guest name determines type
4. **Status Progression**: New → Active → Completed

### Format-Specific Rules
1. **iTrip**: MM/DD/YYYY dates, single guest name field
2. **Evolve**: YYYY-MM-DD dates, may include owner blocks
3. **Unknown**: Best-effort parsing with warnings

## Performance Metrics

### Processing Targets
- **File Processing**: < 30 seconds per 1000 records
- **Memory Usage**: < 500MB per file
- **API Calls**: Batch to respect rate limits
- **Success Rate**: > 98% record creation

### Monitoring Points
- Files in process folder age
- Processing time per file
- Error rate by supplier
- Duplicate detection hits

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Scope**: Complete CSV processing business logic
**Primary Code**: `/src/automation/scripts/CSVtoAirtable/csvProcess.py`