# CSV Processing

## Purpose
Process reservation CSV files received via email from iTrip and Evolve through CloudMailin webhook integration. This feature handles email parsing, CSV extraction, UID generation, duplicate detection, and Airtable synchronization.

## Quick Start
1. CloudMailin receives email with CSV attachment
2. Webhook triggers at `/webhooks/csv-email`
3. CSV saved to `CSV_process_[environment]/` directory
4. Automation controller runs `csvProcess.py`
5. Processed files moved to `CSV_done_[environment]/`

## Key Components
- **Email Reception**: CloudMailin webhook service
- **CSV Parsing**: Pandas-based processing with supplier detection
- **UID Generation**: Unique identifier creation for deduplication
- **Duplicate Detection**: Composite UID matching and history preservation
- **Airtable Sync**: Batch upsert with field mapping

## Directory Structure
```
01-csv-processing/
├── README.md                    # This file
├── BusinessLogicAtoZ.md         # CSV processing rules
├── SYSTEM_LOGICAL_FLOW.md       # Processing flow diagrams
├── version-history.md           # Change tracking
├── flows/
│   ├── cloudmailin-flow.mmd    # Email reception flow
│   ├── itrip-processing.mmd    # iTrip specific logic
│   ├── evolve-processing.mmd   # Evolve specific logic
│   └── duplicate-handling.mmd  # Deduplication flow
└── examples/
    ├── itrip-sample.csv        # Sample iTrip format
    ├── evolve-sample.csv       # Sample Evolve format
    └── webhook-payload.json    # CloudMailin webhook example
```

## File Processing Locations
- **Incoming**: `/home/opc/automation/src/automation/scripts/CSV_process_[development|production]/`
- **Processed**: `/home/opc/automation/src/automation/scripts/CSV_done_[development|production]/`
- **Scripts**: `/home/opc/automation/src/automation/scripts/CSVtoAirtable/csvProcess.py`

## Related Features
- [Webhook Processing](../12-webhook-processing/) - Handles CloudMailin webhooks
- [Duplicate Detection](../09-duplicate-detection/) - UID generation logic
- [Airtable Integration](../05-airtable-integration/) - Database sync
- [Automation Controller](../13-automation-controller/) - Process orchestration

## Common Issues
1. **Missing Property**: Property name in CSV must exactly match Airtable
2. **Date Parsing**: Various date formats handled automatically
3. **Duplicate Detection**: Check UID generation if duplicates appear
4. **File Permissions**: Ensure write access to process directories

## Configuration
```bash
# Environment Variables
AIRTABLE_API_KEY=your_key
AIRTABLE_BASE_ID=base_id
AIRTABLE_RESERVATIONS_TABLE=Reservations
CLOUDMAILIN_WEBHOOK_SECRET=secret
```

## Maintenance Notes
- Monitor CSV process directories for stuck files
- Clean CSV done directories monthly
- Verify property name mappings quarterly
- Test CloudMailin webhook after updates

## Version
Current: v1.0.0 (July 11, 2025)