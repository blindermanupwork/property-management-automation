# Logging Architecture v2.2.8

## Overview
Environment-specific logging system implemented to provide complete separation between development and production operations.

## Log File Structure

### Environment-Specific Logs
```
src/automation/logs/
├── csv_sync_Development.log      # Dev CSV processing logs
├── csv_sync_Production.log       # Prod CSV processing logs
├── ics_sync_dev.log              # Dev ICS processing logs  
├── ics_sync_prod.log             # Prod ICS processing logs
├── automation_dev*.log           # Dev automation runner logs
├── automation_prod*.log          # Prod automation runner logs
├── webhook_development.log       # Dev webhook processing
└── webhook.log                   # Prod webhook processing
```

### Archived Logs
```
src/automation/logs/
├── csv_sync_archive_YYYYMMDD_HHMMSS.log
└── ics_sync_archive_YYYYMMDD_HHMMSS.log
```

## Implementation Details

### CSV Processing Logs
- **File**: `csv_sync_{environment_name}.log`
- **Location**: `src/automation/scripts/CSVtoAirtable/csvProcess.py:37`
- **Content**: CSV file processing, duplicate detection, property mapping, Airtable sync
- **Format**: `LOG_FILE = str(Config.get_logs_dir() / f"csv_sync_{Config.environment_name}.log")`

### ICS Processing Logs  
- **File**: `ics_sync_{dev|prod}.log`
- **Location**: `src/automation/scripts/icsAirtableSync/icsProcess.py:155`
- **Content**: Calendar feed processing, reservation sync, schedule updates
- **Format**: `LOG_FILE = str(Config.get_logs_dir() / f"ics_sync{environment_suffix}.log")`

### Webhook Processing Logs
- **Dev**: `webhook_development.log` (port 5001)
- **Prod**: `webhook.log` (port 5000)
- **Content**: HCP webhook events, job status updates, field mapping

### Automation Runner Logs
- **Dev**: `automation_dev*.log`
- **Prod**: `automation_prod*.log`  
- **Content**: Overall automation orchestration, error handling, execution summaries

## Environment Detection

### CSV Processing
Uses `Config.environment_name` which resolves to:
- `"Development"` when `ENVIRONMENT=development`
- `"Production"` when `ENVIRONMENT=production`

### ICS Processing
Uses conditional logic:
```python
environment_suffix = "_dev" if Config.environment == 'development' else "_prod"
```

## Log Management Best Practices

### Regular Archiving
- Archive logs monthly or when they exceed 50MB
- Use timestamp format: `YYYYMMDD_HHMMSS`
- Keep archived logs for 6 months minimum

### Monitoring Commands
```bash
# Monitor development logs
tail -f src/automation/logs/csv_sync_Development.log
tail -f src/automation/logs/ics_sync_dev.log
tail -f src/automation/logs/webhook_development.log

# Monitor production logs  
tail -f src/automation/logs/csv_sync_Production.log
tail -f src/automation/logs/ics_sync_prod.log
tail -f src/automation/logs/webhook.log

# Check log sizes
ls -lh src/automation/logs/*.log
```

### Search Patterns
```bash
# Find specific UIDs across environments
grep "14855810" src/automation/logs/csv_sync_*.log

# Check webhook activity for specific job
grep "job_abc123" src/automation/logs/webhook*.log

# Monitor error patterns
grep -i "error\|exception\|failed" src/automation/logs/*.log
```

## Benefits

### Complete Environment Isolation
- No log pollution between dev and prod operations
- Clear separation for debugging and troubleshooting
- Independent log rotation and archival

### Enhanced Debugging
- Environment-specific context in all log entries
- Easier correlation of issues to specific deployments
- Simplified root cause analysis

### Operational Safety
- Prevents accidentally debugging prod issues with dev logs
- Clear audit trail for each environment
- Simplified monitoring and alerting setup

## Migration Notes

### Archived Files (July 11, 2025)
- `csv_sync_archive_20250711_134640.log` - 1.6MB of historical data
- `ics_sync_archive_20250711_134640.log` - Empty file (0 bytes)

### Breaking Changes
- Legacy `csv_sync.log` and `ics_sync.log` files no longer used
- Scripts now create environment-specific files automatically
- Update any monitoring or log aggregation systems accordingly