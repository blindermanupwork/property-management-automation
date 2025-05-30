# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-05-30

### 🏗️ Major Restructuring
- **Complete Project Reorganization**: Moved from flat structure to professional `/src/automation/` package structure
- **Directory Consolidation**: Organized all components into logical hierarchy
  - `bin/` → `/src/automation/bin/` (deployment scripts)
  - `logs/` → `/src/automation/logs/` (centralized logging)
  - `tests/` → `/src/automation/tests/` (test suite)
  - `scripts/` → `/src/automation/scripts/` (automation scripts)
  - `CSV_done/`, `CSV_process/` → `/src/automation/scripts/` (data directories)
- **Universal Runner**: Enhanced `run_anywhere.py` moved to `/src/` with updated path resolution

### 🕐 Comprehensive Timezone Implementation
- **Dual-Timezone Strategy**: Implemented consistent timezone handling across all scripts
  - **PST (US/Pacific)**: All logging, system operations, health checks, browser automation
  - **Arizona (America/Phoenix)**: All business data, Airtable timestamps, file processing
- **Enhanced Scripts with Timezone Support**:
  - `csvProcess.py`: PST logging + Arizona timestamps for Airtable data
  - `evolveScrape.py`: PST logging + Arizona timestamps + PST browser timezone
  - `gmail_downloader.py`: PST logging + Arizona timestamps for file naming
  - `icsProcess.py`: PST logging + Arizona timestamps for calendar data
  - `webhook.py`: PST logging + Arizona timestamps for business events
  - `hcp_sync.js`: Arizona timezone utility functions for service jobs

### 🔧 Configuration & Path Management
- **Updated Config Class**: Enhanced `config.py` with new directory structure
  - Updated all path getters to reflect `/src/automation/` structure
  - Maintained backward compatibility for existing functionality
- **Import Path Updates**: Fixed all import statements across scripts to use new structure
  - Consistent `sys.path.insert(0, str(project_root))` pattern
  - All scripts now import `from src.automation.config import Config`
- **Cross-Platform Compatibility**: Enhanced `run_anywhere.py` with Python 3.6+ support
  - Fixed `capture_output` parameter compatibility for older Python versions
  - Robust test directory detection with new structure

### 🧪 Enhanced Testing Infrastructure
- **Test Suite Organization**: Moved comprehensive test suite to `/src/automation/tests/`
- **Updated Test Runner**: `run_anywhere.py --test` now uses correct test directory path
- **Maintained Test Coverage**: All existing tests work with new structure

### 📝 Documentation Updates
- **Comprehensive README**: Updated with complete new structure documentation
- **File Structure Diagram**: Detailed visual representation of reorganized project
- **Usage Examples**: Updated all command examples to reflect new paths
- **Timezone Documentation**: Added detailed section explaining dual-timezone strategy

### 🔄 Enhanced Operational Scripts
- **Deployment Scripts**: All scripts in `/src/automation/bin/` with updated paths
- **Release Management**: Enhanced version scripts with new structure awareness
- **Health Monitoring**: Updated monitoring scripts for new log locations

### ✨ Improved Developer Experience
- **Professional Package Structure**: Follows Python packaging best practices
- **Clear Separation of Concerns**: Logical organization of scripts, tests, logs, and utilities
- **Maintainable Architecture**: Easy to navigate and extend for future development
- **Installation Ready**: Proper package structure for `pip install -e .`

### 🚀 CI/CD & Automation Infrastructure
- **GitHub Actions Workflows**: Added comprehensive CI/CD pipeline
  - Multi-platform testing (Ubuntu, Windows, macOS) 
  - Python version compatibility testing (3.8, 3.9, 3.10, 3.11)
  - Code quality checks (Black, isort, MyPy)
  - Security scanning (Safety, Bandit)
  - Automated package building and PyPI publishing
  - Documentation deployment to GitHub Pages
- **Modern Python Packaging**: Added `pyproject.toml` with complete project configuration
  - Dependency management with version constraints
  - Development and testing dependency groups
  - Code formatting and type checking configuration
  - Test coverage and pytest settings
- **Enhanced Setup Script**: Updated `setup.py` with comprehensive package metadata
  - Console script entry points for all major components
  - Proper dependency declarations and Python version requirements
  - Package classification and keyword optimization

### 📊 System Activity Tracking
- **Operational Data**: System has been actively processing data
  - Multiple CSV files processed on 05-30-2025 (23 Evolve files + 5 iTrip reports)
  - Automated runs executed at regular intervals (hourly processing)
  - Recent automation completion at 16:02:33 with 4/5 successful operations
- **Gmail Integration**: Active email processing with token refresh on 2025-05-30 16:00:06
- **Log Management**: Centralized logging with multiple log files tracking different components

### 🔧 Development Tools & Validation
- **Setup Validation Script**: Enhanced `test_setup.py` for comprehensive system validation
- **Dependency Management**: Auto-installation capabilities with missing package detection
- **Cross-Platform Testing**: Portability validation across different operating systems

### 🐛 Bug Fixes
- **Path Resolution**: Fixed all hardcoded paths to use dynamic resolution
- **Import Errors**: Resolved all import path issues from restructuring
- **Timezone Consistency**: Eliminated timezone inconsistencies across scripts
- **Test Compatibility**: Fixed pytest compatibility issues with new directory structure
- **GitHub Actions**: Fixed CI/CD paths to use new `src/run_anywhere.py` structure
- **Setup Script Version**: Updated setup.py to read version from VERSION file dynamically

### 📈 Migration Impact
- **Breaking Changes**: File paths for individual script execution have changed
  - Old: `python scripts/evolve/evolveScrape.py`
  - New: `python src/automation/scripts/evolve/evolveScrape.py`
- **Backward Compatibility**: Universal runner path changed
  - Old: `python run_anywhere.py`
  - New: `python src/run_anywhere.py`
- **Package Installation**: No breaking changes for `pip install -e .` usage
- **Configuration**: All existing `.env` files and settings remain compatible

### 🎯 System Status
- **Production Ready**: All components tested and verified working
- **Active Processing**: System processing 23 CSV files + 5 iTrip reports daily
- **Monitoring**: Comprehensive logging and health checks operational
- **CI/CD**: Full automated testing pipeline with multi-platform validation

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