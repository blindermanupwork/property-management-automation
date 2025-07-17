# Airtable Integration - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of Airtable integration including all UI fields, API operations, automation triggers, and MCP logic using exact field names and capturing all business workflows.

## Core Business Entities

### Airtable Tables and Their Purpose

#### **Main Table: "Reservations"**
**Purpose**: Central data store for all property reservations and blocks
**Key Fields**:
- **UID**: Unique identifier for deduplication
- **Property**: Linked record to Properties table
- **Check-in Date**: Guest arrival date (format: YYYY-MM-DD)
- **Check-out Date**: Guest departure date (format: YYYY-MM-DD)
- **Guest Name**: Full name of primary guest
- **Entry Type**: "Reservation" or "Block"
- **Status**: Processing status (New, Active, Modified, Old, Removed)
- **Source**: Data origin (iTrip, Evolve, ICS Feed, Manual)
- **HCP Job ID**: HousecallPro job identifier when created
- **HCP Customer ID**: HousecallPro customer identifier
- **Service Date**: Date when cleaning/service is scheduled
- **Service Time**: Time for service (HH:MM AM/PM)
- **Custom Service Time**: User-defined override
- **Same Day**: Boolean for same-day turnovers
- **Service Line Custom Instructions**: Custom text for HCP (200 char limit)
- **Schedule Sync Details**: Log of schedule updates
- **Service Sync Details**: Log of service operations
- **Job Status**: Current HCP job status
- **Scheduled Start**: HCP job start time
- **Scheduled End**: HCP job end time
- **Assigned Employee**: HCP cleaner assignment
- **Long Term Guest**: Boolean for 14+ day stays
- **Owner Arriving**: Boolean for owner arrivals
- **Next Guest Date**: Date of next arrival

#### **Configuration Table: "Automation Settings"**
**Purpose**: Store environment-specific configuration values
**Key Fields**:
- **Setting Name**: Configuration parameter name
- **Setting Value**: Configuration value
- **Environment**: dev/prod specification
- **Active**: Boolean for enabled settings
- **Category**: Setting category (API, Schedule, etc.)
- **Last Updated**: Modification timestamp

#### **Properties Table: "Property Directory"**
**Purpose**: Master list of all managed properties
**Key Fields**:
- **Property Name**: Official property name
- **Property Address**: Full street address
- **ICS Feed URL**: Calendar feed URL
- **Property Type**: Airbnb, VRBO, etc.
- **Management Company**: iTrip, Evolve, etc.
- **Active**: Boolean for active properties
- **Special Instructions**: Property-specific notes
- **Default Service Time**: Standard cleaning time
- **Service Duration**: Hours allocated for cleaning

#### **ICS Feeds Table: "ICS Feed Configuration"**
**Purpose**: Manage calendar feed URLs and sync status
**Key Fields**:
- **Feed URL**: Calendar feed endpoint
- **Property**: Linked to Properties table
- **Active**: Boolean for active feeds
- **Last Sync**: Timestamp of last successful sync
- **Sync Errors**: Error count
- **Feed Type**: Airbnb, VRBO, Booking.com, etc.

## Business Workflows

### 1. Data Ingestion from Multiple Sources

#### **CloudMailin Email Processing (Webhook-based)**
**Trigger**: Email received at specific addresses
**Business Logic**:
1. **Email Reception**:
   - CloudMailin receives emails at configured addresses
   - Extracts CSV attachments from iTrip emails
   - Sends webhook to automation system

2. **CSV Processing**:
   - Downloads CSV to `CSV_process_[environment]/`
   - Parses reservation data:
     - Guest names and contact info
     - Property addresses
     - Check-in/out dates
     - Service requirements
   - Generates UID: `{source}_{property}_{checkin}_{checkout}_{guest_lastname}`

3. **Airtable Creation**:
   - Checks for existing UID to prevent duplicates
   - Creates new Reservation record
   - Links to Property record
   - Sets Status to "New"
   - Moves CSV to `CSV_done_[environment]/`

#### **ICS Feed Processing**
**Trigger**: Automated every 4 hours via cron
**Business Logic**:
1. **Feed Collection**:
   - Processes 246 feeds (prod) / 255 feeds (dev)
   - Downloads .ics files from each URL
   - Handles various calendar formats

2. **Event Parsing**:
   - Extracts VEVENT blocks
   - Identifies check-in/out from DTSTART/DTEND
   - Parses SUMMARY for guest names
   - Handles timezone conversions to MST

3. **UID Generation**:
   - Creates composite UID: `{source}_{property}_{checkin}_{checkout}_{uid_hash}`
   - Uses last 6 chars of original UID for uniqueness
   - Prevents duplicates across multiple syncs

4. **Record Management**:
   - Updates existing records by UID
   - Creates new records for new events
   - Marks missing events as "Removed"
   - Maintains sync history

#### **Evolve Portal Scraping**
**Trigger**: Automated every 4 hours via cron
**Business Logic**:
1. **Browser Automation**:
   - Selenium Chrome driver in headless mode
   - Logs into Evolve portal
   - Navigates to reservations page

2. **Data Extraction**:
   - Scrapes upcoming reservations
   - Extracts guest details
   - Captures property information
   - Handles dynamic content loading

3. **Airtable Integration**:
   - Creates records with Source = "Evolve"
   - Links to existing properties
   - Updates reservation details
   - Maintains session for efficiency

### 2. API Operations and Integration Patterns

#### **REST API Authentication**
**Implementation**:
```python
headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}
```

#### **CRUD Operations**

**Create Operation**:
```python
def create_reservation(data):
    # Validate required fields
    required = ['Property', 'Check-in Date', 'Check-out Date', 'Guest Name']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Create record
    response = requests.post(
        f"{API_BASE}/Reservations",
        headers=headers,
        json={"fields": data}
    )
    return response.json()
```

**Read Operations**:
```python
def get_active_reservations():
    params = {
        'filterByFormula': "{Status} = 'Active'",
        'pageSize': 100,
        'view': 'Active Reservations'
    }
    return paginate_results('Reservations', params)
```

**Update Operations**:
```python
def update_reservation(record_id, updates):
    response = requests.patch(
        f"{API_BASE}/Reservations/{record_id}",
        headers=headers,
        json={"fields": updates}
    )
    return response.json()
```

**Delete (Soft Delete) Operations**:
```python
def soft_delete_reservation(record_id):
    # Never hard delete - update status instead
    return update_reservation(record_id, {"Status": "Removed"})
```

### 3. Rate Limiting and Performance Optimization

#### **Rate Limit Management**
**Business Logic**:
1. **Request Tracking**:
   - Monitor requests per second
   - Implement request queue
   - Track per-base limits

2. **Throttling Strategy**:
   ```python
   class RateLimiter:
       def __init__(self, max_per_second=5):
           self.max_per_second = max_per_second
           self.requests = []
       
       def wait_if_needed(self):
           now = time.time()
           self.requests = [r for r in self.requests if now - r < 1]
           if len(self.requests) >= self.max_per_second:
               sleep_time = 1 - (now - self.requests[0])
               time.sleep(sleep_time)
           self.requests.append(now)
   ```

3. **Batch Operations**:
   - Group create/update operations
   - Maximum 10 records per batch
   - 200ms delay between batches

#### **Error Handling Patterns**
**429 Rate Limit Error**:
```python
def handle_rate_limit(retry_count=0):
    wait_time = 2 ** retry_count  # Exponential backoff
    logger.warning(f"Rate limited, waiting {wait_time}s")
    time.sleep(wait_time)
    if retry_count < 3:
        return retry_operation(retry_count + 1)
    raise Exception("Max retries exceeded")
```

**422 Validation Error**:
```python
def handle_validation_error(error_response):
    errors = error_response.json()
    logger.error(f"Validation failed: {errors}")
    # Log specific field errors
    for field_error in errors.get('error', {}).get('field_errors', []):
        logger.error(f"Field {field_error['field']}: {field_error['message']}")
    return False
```

### 4. Field Type Management and Validation

#### **Field Type Enforcement**
**Date Fields**:
- Format: YYYY-MM-DD (ISO 8601)
- No time component for date-only fields
- Timezone handling for datetime fields

**Linked Records**:
- Format: Array of record IDs ["recXXX", "recYYY"]
- Must reference existing records
- Cannot link by name

**Select Fields**:
- Single Select: Exact string match required
- Multiple Select: Array of exact matches
- Case-sensitive matching

**Number Fields**:
- Numeric types only (int/float)
- No string representations
- Currency includes precision

#### **Schema Validation**
```python
FIELD_SCHEMAS = {
    'Reservations': {
        'Property': {'type': 'link', 'table': 'Properties', 'required': True},
        'Check-in Date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
        'Check-out Date': {'type': 'date', 'format': 'YYYY-MM-DD', 'required': True},
        'Guest Name': {'type': 'text', 'max_length': 255, 'required': True},
        'Entry Type': {'type': 'select', 'options': ['Reservation', 'Block'], 'required': True},
        'Status': {'type': 'select', 'options': ['New', 'Active', 'Modified', 'Old', 'Removed']},
        'Same Day': {'type': 'checkbox', 'default': False},
        'Service Line Custom Instructions': {'type': 'text', 'max_length': 200}
    }
}
```

### 5. Environment Management

#### **Environment Separation**
**Development Environment**:
- Base ID: `app67yWFv0hKdl6jM`
- API Endpoint: `https://api.airtable.com/v0/app67yWFv0hKdl6jM`
- CSV Directory: `CSV_*_development/`
- Log Files: `automation_dev*.log`

**Production Environment**:
- Base ID: `appZzebEIqCU5R9ER`
- API Endpoint: `https://api.airtable.com/v0/appZzebEIqCU5R9ER`
- CSV Directory: `CSV_*_production/`
- Log Files: `automation_prod*.log`

#### **Environment Configuration**
```python
def get_environment_config():
    env = os.getenv('ENVIRONMENT', 'development')
    configs = {
        'development': {
            'base_id': 'app67yWFv0hKdl6jM',
            'api_key': os.getenv('AIRTABLE_DEV_API_KEY'),
            'csv_dir': 'CSV_process_development'
        },
        'production': {
            'base_id': 'appZzebEIqCU5R9ER',
            'api_key': os.getenv('AIRTABLE_PROD_API_KEY'),
            'csv_dir': 'CSV_process_production'
        }
    }
    return configs[env]
```

### 6. Status Management and State Transitions

#### **Status State Machine**
**Valid Transitions**:
```
New → Active → Modified → Old
         ↓        ↓        ↓
      Removed  Removed  Removed
```

**Business Rules**:
1. **New**: Initial state for created records
2. **Active**: Currently valid reservation
3. **Modified**: Changed after becoming active
4. **Old**: Archived/historical record
5. **Removed**: Soft deleted record

**Transition Logic**:
```python
VALID_TRANSITIONS = {
    'New': ['Active', 'Removed'],
    'Active': ['Modified', 'Old', 'Removed'],
    'Modified': ['Active', 'Old', 'Removed'],
    'Old': ['Removed'],
    'Removed': []  # Terminal state
}

def can_transition(current_status, new_status):
    return new_status in VALID_TRANSITIONS.get(current_status, [])
```

### 7. Pagination and Large Dataset Handling

#### **Pagination Implementation**
```python
def paginate_all_records(table_name, filter_formula=None, view=None):
    all_records = []
    offset = None
    
    while True:
        params = {
            'pageSize': 100,
            'offset': offset
        }
        if filter_formula:
            params['filterByFormula'] = filter_formula
        if view:
            params['view'] = view
            
        response = requests.get(
            f"{API_BASE}/{table_name}",
            headers=headers,
            params=params
        )
        
        data = response.json()
        all_records.extend(data.get('records', []))
        
        offset = data.get('offset')
        if not offset:
            break
            
        # Rate limit protection
        time.sleep(0.2)
    
    return all_records
```

### 8. MCP Server Integration

#### **Airtable MCP Server Capabilities**
**Available Operations**:
- `list_records`: Paginated record retrieval
- `search_records`: Text search across fields
- `get_record`: Fetch specific record by ID
- `create_record`: Create new record
- `update_records`: Batch update up to 10
- `delete_records`: Soft delete records
- `list_bases`: Show available bases
- `list_tables`: Show tables in base
- `describe_table`: Get table schema

**Usage Examples**:
```javascript
// List active reservations
await mcp.list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "Reservations",
    filterByFormula: "{Status} = 'Active'",
    maxRecords: 100
});

// Search for guest
await mcp.search_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "Reservations",
    searchTerm: "John Smith"
});
```

### 9. Webhook Automation Integration

#### **Airtable Automation Triggers**
**Record Created**:
- Fires when new reservation added
- Sends webhook to create HCP job
- Includes all record fields in payload

**Record Updated**:
- Fires on specific field changes
- Filters by Status transitions
- Sends delta updates only

**Scheduled Automation**:
- Daily sync verification
- Orphan record cleanup
- Status reconciliation

### 10. Performance Optimization Strategies

#### **Caching Strategy**
```python
class AirtableCache:
    def __init__(self, ttl=300):  # 5 minute TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, key, data):
        self.cache[key] = (data, time.time())
```

#### **Bulk Operation Optimization**
```python
def bulk_create_reservations(reservations):
    # Sort by property for better performance
    sorted_reservations = sorted(reservations, key=lambda x: x.get('Property', [''])[0])
    
    # Process in batches of 10
    results = []
    for i in range(0, len(sorted_reservations), 10):
        batch = sorted_reservations[i:i+10]
        
        response = requests.post(
            f"{API_BASE}/Reservations",
            headers=headers,
            json={"records": [{"fields": r} for r in batch]}
        )
        
        results.extend(response.json().get('records', []))
        time.sleep(0.2)  # Rate limit protection
    
    return results
```

## Critical Business Rules

### Data Integrity Rules
1. **UID Uniqueness**: Every reservation must have unique UID
2. **Property Linking**: Reservations must link to valid property
3. **Date Validation**: Check-out must be after check-in
4. **Status Consistency**: Follow state machine transitions
5. **Soft Deletes Only**: Never hard delete records

### API Usage Rules
1. **Rate Limiting**: Maximum 5 requests per second per base
2. **Batch Limits**: Maximum 10 records per batch operation
3. **Payload Size**: Maximum 16MB per request
4. **Page Size**: Maximum 100 records per page
5. **Timeout**: 30-second request timeout

### Field Validation Rules
1. **Required Fields**: Property, Check-in Date, Check-out Date, Guest Name
2. **Date Format**: YYYY-MM-DD for all date fields
3. **Linked Records**: Must use record IDs, not names
4. **Select Options**: Must match exact option values
5. **Text Length**: Respect field-specific limits

### Environment Rules
1. **Complete Isolation**: No data sharing between dev/prod
2. **API Key Separation**: Different keys per environment
3. **Base ID Verification**: Always check base ID before operations
4. **Log Separation**: Environment-specific log files
5. **Configuration**: Environment-specific settings

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Scope**: Complete Airtable integration business logic
**API Version**: Airtable REST API v0