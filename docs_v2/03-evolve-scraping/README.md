# Evolve Portal Scraping

## Purpose
Automated web scraping of the Evolve vacation rental portal to extract property availability, pricing, and reservation data. This feature uses Selenium WebDriver to navigate the portal, export data from multiple tabs, and sync with Airtable.

## Quick Start
1. Runs every 4 hours via cron (both dev and prod)
2. Requires Chrome browser and ChromeDriver
3. Uses Evolve login credentials from environment
4. Exports Tab1 (availability) and Tab2 (reservations)
5. Processes CSV files like regular CSV workflow

## Key Components
- **Selenium Automation**: Chrome browser control
- **Multi-Tab Export**: Availability and reservation data
- **Headless Mode**: Server execution without GUI
- **Sequential Processing**: Avoid Chrome conflicts
- **Auto-Retry Logic**: Handle portal timeouts

## Directory Structure
```
03-evolve-scraping/
├── README.md                    # This file
├── BusinessLogicAtoZ.md         # Evolve scraping rules
├── SYSTEM_LOGICAL_FLOW.md       # Scraping flow diagrams
├── version-history.md           # Change tracking
├── flows/
│   ├── login-flow.mmd          # Portal authentication
│   ├── navigation-flow.mmd     # Page navigation logic
│   ├── export-flow.mmd         # CSV export process
│   └── error-recovery.mmd      # Retry and recovery
└── examples/
    ├── chrome-options.json      # Browser configuration
    ├── element-selectors.txt    # CSS selectors used
    └── export-sequence.log      # Sample run output
```

## Script Location
- **Main Script**: `/home/opc/automation/src/automation/scripts/evolve/evolveScrape.py`
- **Logs**: `/home/opc/automation/src/automation/logs/evolve_scrape.log`
- **Downloads**: `/tmp/evolve_downloads/`
- **Final Location**: `CSV_process_[environment]/`

## Environment Configuration
```bash
# CRITICAL: Must be set BEFORE Python starts
ENVIRONMENT=production python3 evolveScrape.py --headless --sequential
ENVIRONMENT=development python3 evolveScrape.py --headless --sequential

# Environment Variables Required
EVOLVE_USERNAME=username
EVOLVE_PASSWORD=password
CHROME_DRIVER_PATH=/usr/local/bin/chromedriver
```

## Command Line Options
- `--headless`: Run without GUI (required on server)
- `--sequential`: Export tabs one at a time
- `--debug`: Enable verbose logging
- `--timeout`: Set page load timeout (default: 30s)

## Related Features
- [CSV Processing](../01-csv-processing/) - Processes exported CSVs
- [Automation Controller](../13-automation-controller/) - Scheduling
- [Environment Management](../14-environment-management/) - Dev/Prod separation
- [Duplicate Detection](../09-duplicate-detection/) - Handles Evolve UIDs

## Common Issues
1. **Chrome Crashes**: Use --sequential flag
2. **Login Failures**: Check credentials and 2FA
3. **Export Timeouts**: Portal may be slow, retry
4. **Missing Downloads**: Check /tmp permissions
5. **Wrong Environment**: Set ENVIRONMENT before Python

## Portal Navigation
1. Login page → Dashboard
2. Properties → Availability/Calendar
3. Export → Download CSV (Tab1)
4. Reports → Reservations
5. Export → Download CSV (Tab2)

## Maintenance Notes
- Update Chrome/ChromeDriver together
- Test login flow after portal updates
- Monitor download directory space
- Verify element selectors quarterly
- Check for portal API alternatives

## Version
Current: v1.0.0 (July 11, 2025)