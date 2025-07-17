# CSV Processing - Main Process Flow

**Feature:** 01-csv-processing  
**Purpose:** Visual representation of the complete CSV processing pipeline  
**Last Updated:** July 14, 2025

---

## 🔄 Main Process Flow

```mermaid
flowchart TB
    Start([CloudMailin Receives Email]) --> Parse{Parse Email<br/>Headers}
    
    Parse --> ValidSender{From iTrip?}
    ValidSender -->|No| Reject[Reject Email]
    ValidSender -->|Yes| ExtractCSV[Extract CSV Attachment]
    
    ExtractCSV --> Decode[Base64 Decode Content]
    Decode --> SaveFile[Save to CSV_process Directory<br/>with Timestamp Prefix]
    
    SaveFile --> LoadCSV[Load CSV into Memory]
    LoadCSV --> ValidateHeaders{Validate<br/>Required Headers}
    
    ValidateHeaders -->|Missing Headers| LogError1[Log Error & Skip File]
    ValidateHeaders -->|Valid| ProcessRows[Process Each Row]
    
    ProcessRows --> GenUID[Generate Composite UID<br/>ConfCode|PropID|CheckIn]
    
    GenUID --> CheckExisting{Check Existing<br/>Reservation}
    
    CheckExisting -->|Not Found| CreateNew[Create New Airtable Record<br/>Status: Active]
    CheckExisting -->|Found Active| CompareData{Compare<br/>Field Values}
    CheckExisting -->|Found Inactive| CheckDates{Same Dates?}
    
    CompareData -->|No Changes| MarkUnchanged[Mark as Unchanged]
    CompareData -->|Changes Found| UpdateRecord[Update Record<br/>Preserve History]
    
    CheckDates -->|Different Dates| CreateNew
    CheckDates -->|Same Dates| ReactivateRecord[Reactivate Record<br/>Update Fields]
    
    CreateNew --> AddMetadata[Add Import Metadata<br/>Date, Source, etc.]
    UpdateRecord --> AddMetadata
    ReactivateRecord --> AddMetadata
    MarkUnchanged --> AddMetadata
    
    AddMetadata --> NextRow{More Rows?}
    NextRow -->|Yes| ProcessRows
    NextRow -->|No| GenerateSummary[Generate Processing Summary]
    
    GenerateSummary --> MoveFile[Move CSV to<br/>CSV_done Directory]
    MoveFile --> UpdateStatus[Update Automation Status<br/>in Airtable]
    UpdateStatus --> End([Processing Complete])
    
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Reject fill:#FF6B6B
    style LogError1 fill:#FF6B6B
```

---

## 📝 Process Steps Explained

### 1. **Email Receipt & Validation**
- CloudMailin webhook receives email
- Validates sender is from @itrip.net domain
- Extracts CSV attachment from email payload

### 2. **File Processing**
- Base64 decodes the attachment content
- Saves with timestamp prefix: `YYYYMMDD_HHMMSS_filename.csv`
- Location: `/home/opc/automation/CSV_process_production/`

### 3. **CSV Parsing**
- Loads CSV using Python csv.DictReader
- Validates all required headers are present
- Handles UTF-8 encoding and special characters

### 4. **UID Generation**
```python
uid = f"{row['Confirmation Code']}|{row['Property ID']}|{checkin_date}"
```

### 5. **Reservation Processing**
- **New Reservations**: Create with "Active" status
- **Existing Active**: Compare and update if changed
- **Existing Inactive**: Reactivate if same dates, create new if different

### 6. **History Preservation**
```python
history_entry = f"{datetime.now()}: {field} changed from {old_value} to {new_value}"
```

### 7. **File Completion**
- Move processed file to CSV_done directory
- Generate summary statistics
- Update automation status in Airtable

---

## ⏱️ Timing Breakdown

| Step | Average Time | Max Time |
|------|-------------|----------|
| Email parsing | 100ms | 500ms |
| File save | 50ms | 200ms |
| CSV parsing (100 rows) | 2s | 5s |
| Airtable lookups | 3s | 10s |
| Record updates | 2s | 8s |
| File move | 20ms | 100ms |
| **Total** | **7.2s** | **24s** |

---

## 🔗 Related Flows
- [Error Handling Flow](./error-handling-flow.md)
- [Duplicate Detection Flow](./duplicate-detection-flow.md)
- [Integration Points](./integration-points.md)