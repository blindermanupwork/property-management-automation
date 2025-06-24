# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.4] - 2025-06-24

### Added
- **Duplicate Reservation Cleanup Script** (`cleanup-duplicate-reservations.py`)
  - Identifies duplicate reservations by Property ID, Check-in/out dates, Entry Type, and UID
  - Marks older duplicates as "Old" status while keeping newest record active
  - Supports both dev and prod environments
  - Includes dry-run mode for safe testing
  - Automatically excludes records already marked as "Old"

### Fixed
- **CSV Processing Duplicate Detection** (commit 545ac4b - June 23, 2025)
  - Fixed composite UID vs base UID lookup mismatch causing duplicates
  - Now correctly indexes by both composite UIDs (e.g., `14516891_recL6AiK5pINSbcnu`) and base UIDs (e.g., `14516891`)
  - Prevents creation of duplicate reservations from Evolve CSV processing
  - Applied to both `process_csv_files()` and `process_tab2_csv()` functions

## [2.2.3] - 2025-06-12

### Added
- **Long-term Guest Detection** - Automatic detection of 14+ day stays
  - Adds "LONG TERM GUEST DEPARTING" prefix to service names
  - Works in all job creation methods (dev/prod sync scripts, API)
  - Helps cleaners prepare for extended stay requirements
  - Format: `${customInstructions} - LONG TERM GUEST DEPARTING ${baseSvcName}`
- **Airtable Automation Reference Scripts** - Fixed and documented scripts for Airtable automations
  - `find-next-guest-date.js` - Finds next guest with same-day turnover detection
  - `update-service-line-description.js` - Builds service descriptions with long-term guest logic
  - Both scripts saved in `src/automation/scripts/airtable-automations/`
  - Fixed date comparison bug (changed > to >= for same-day detection)
- Comprehensive operational documentation suite for property management
  - `OPERATIONAL_SCENARIOS.md` - 30 real-world scenarios with step-by-step resolutions
  - `OPERATIONAL_SCENARIOS_BY_VIEW.md` - Scenarios organized by Airtable views with real examples
  - `SCENARIOS_QUICK_REFERENCE.md` - Quick reference guide for urgent situations
  - `OPERATIONAL_TRAINING_CHECKLIST.md` - 3-week training program for new operators
  - `OPERATIONAL_DATA_EXAMPLES.md` - Real data patterns and edge cases from production
  - `AIRTABLE_VIEW_SCENARIOS.md` - View-specific workflows and filters
- Role-playing scenarios for property management operations training
- View-based operational workflows using new Airtable views (⏰❌ Incomplete, ⏰❓ Mismatch, ⏰🗑️ Removed, etc.)
- Real examples from production data for training scenarios
- Emergency protocols and troubleshooting guides

### Changed
- Updated documentation to reflect current date (June 12, 2025)
- Enhanced operational procedures with real job IDs and property examples
- Updated Airtable "Service Line Description" field description to document long-term guest feature

### Fixed
- Corrected date references in documentation (was showing December 6, now June 12)
- Updated examples to use actual incomplete jobs from current date
- Fixed Removed view logic to show records WITH service job IDs (not without)
- Removed duplicate `handlers/createJob.js` file (was unused, actual handler is in `handlers/jobs.js`)
- **Fixed Airtable automation same-day detection** - Changed date comparison from > to >= to properly detect same-day turnovers

## [2.2.2] - 2025-06-09

### Added
- **HCP MCP Bulletproof Analysis System**
  - Native TypeScript analysis tools (eliminated bash script failures)
  - Ultra-fast performance (<10ms execution time)
  - Comprehensive business intelligence tools
  - Revenue tracking and customer analysis
  - Monthly trends and job statistics
- **CloudMailin Integration** - Replaced Gmail OAuth with webhook-based email processing
- **Enhanced Search Capabilities** - Address search, job filtering, revenue analysis
- **Service Line Custom Instructions** - Unicode support with 200-char truncation
- **Webhook Forwarding System** - Dual authentication support implemented
- **Real-time Console Output** - All automation processes show live progress
- **Environment-specific Webhook Logs** - Separate logs for dev and prod

### Changed
- Complete environment separation between dev and prod
- ICS processor configuration fixes
- Optimized cron scheduling (both environments run every 4 hours, staggered)

### Fixed
- ICS processor critical configuration issues
- Webhook authentication and forwarding
- Environment isolation issues

## [2.2.1] - 2025-06-01

### Added
- Initial HCP MCP implementation
- Basic analysis tools
- Address search functionality

## [2.2.0] - 2025-05-15

### Added
- Property management automation system
- CSV processing for iTrip and Evolve
- ICS feed processing
- HousecallPro integration
- Airtable synchronization

## [2.1.0] - 2025-04-01

### Added
- Initial system architecture
- Basic automation framework

## [2.0.0] - 2025-03-01

### Added
- Complete system rewrite
- New architecture design

## [1.0.0] - 2025-01-01

### Added
- Initial release
- Basic property management features