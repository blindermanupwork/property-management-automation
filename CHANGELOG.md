# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-05-29

### Added
- **Production Automation Controller**: Airtable-based automation control system
  - Centralized automation management via Airtable checkboxes
  - Production base ID: `appZzebEIqCU5R9ER`, table: `tblqQ1p0TknS23uqt`
  - Individual script control through `run_automation.py`
- **Environment-aware Configuration**: Dynamic production/development settings
  - ICS processing now respects `ENVIRONMENT=production` setting
  - Automatic base ID selection based on environment
- **Enhanced Evolve Scraper**: 
  - Fixed timezone handling - now uses Pacific Time consistently
  - Changed filter from "Check-In" to "Check-Out" for next 60 days
  - Dynamic path resolution for portability across environments
- **Improved CSV Processing**:
  - Separate feed URLs for blocks vs reservations (`csv_evolve_blocks` vs `csv_evolve`)
  - Fixed pyairtable API compatibility for newer versions
  - Enhanced debugging with detailed change logging
- **ICS URL Filtering**: Skip non-HTTP URLs (CSV feed identifiers) in ICS processing

### Changed
- **Consolidated Configuration**: Eliminated `config.py`, use only `.env` for all settings
- **Path Portability**: Removed all hardcoded paths, use dynamic resolution
- **Updated pyairtable API**: Migrated from `api.base().table()` to `api.table(base_id, table_name)`
- **CSV Directory Management**: All downloads now go to root `CSV_process`, then move to `CSV_done`

### Fixed
- **Timezone Consistency**: Evolve scraper now forces browser to use Pacific timezone
- **API Compatibility**: Fixed `'Api' object has no attribute 'table'` errors
- **Block Processing**: Separated Evolve blocks and reservations to prevent conflicts
- **Path Resolution**: Scripts work regardless of execution location

### Security
- **Credential Cleanup**: Removed exposed Airtable API keys from committed files
- **Environment Separation**: Clear distinction between production and development settings

### Removed
- **Legacy Files**: Deleted `config.py` and `gmail_downloader_linux.py`
- **Hardcoded Paths**: Eliminated system-specific path dependencies

## [1.0.0] - 2025-05-24

### Added
- Initial property management automation system
- Gmail CSV downloader integration
- Evolve portal scraping functionality  
- CSV to Airtable synchronization
- ICS calendar feed processing
- HousecallPro webhook integration
- Basic monitoring and logging

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>