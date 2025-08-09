# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.16] - 2025-08-09

### Fixed
- **iTrip Automation Fix - Airtable Automation Scripts**
  - Fixed issue where Airtable automation was overwriting iTrip fields set by CSV processor
  - Issue: find-next-guest-date.js was searching database for iTrip reservations and clearing fields
  - Solution: Script now completely skips iTrip reservations (Entry Source = "iTrip")
  - iTrip fields (Next Guest Date, Same-day Turnover) now handled exclusively by CSV processor
  - update-service-line-description.js continues to work correctly for all reservations
  - Updated file: `src/automation/scripts/airtable-automations/find-next-guest-date.js`

- **ICS Processor Same-Day Turnover Bug for Owner Arrivals (Previous v2.2.16 fix from Aug 4)**
  - Fixed hourly duplicate record creation for properties with owner arrivals
  - Issue: When "Owner Arriving" = true and owner block starts on checkout day:
    - Airtable automation correctly sets "Same-day Turnover" = true
    - ICS processor calculated same_day_turnover = false (only checks reservations)
    - Every hour, ICS detected flag change (true → false) and created duplicate "Modified" records
  - Initial fix location was incorrect - moved to sync_ics_event() where it can access existing records
  - Solution: ICS processor now preserves existing same-day turnover value when "Owner Arriving" = true
  - Affected 3 properties that were being marked as modified every hour:
    - 11367 N 122nd St, Scottsdale, AZ
    - 825 W Monterey Pl, Chandler, AZ  
    - 1057 E Butler Dr, 1D, Phoenix, AZ
  - Result: These properties now correctly show as "unchanged" instead of "modified" each sync
  - Updated file: `src/automation/scripts/icsAirtableSync/icsProcess.py`

## [2.2.15] - 2025-07-31

### Fixed
- **Service Line Description Logic - All Flags Now Independent**
  - Fixed Airtable automation script to match expected behavior
  - All service line flags are now independent and shown when applicable:
    - Custom Instructions (if present)
    - OWNER ARRIVING (if owner is arriving - works for both same-day and regular)
    - LONG TERM GUEST DEPARTING (if stay >= 14 days)
    - Base service name (SAME DAY format or regular format)
  - Previous issues fixed:
    - ❌ "OWNER ARRIVING" was embedded in base name for non-same-day
    - ❌ "LONG TERM GUEST DEPARTING" was skipped when owner in base name
    - ❌ Same-day turnovers didn't check for owner arriving
  - Example outputs:
    - Same-day + all flags: `Check hot tub - OWNER ARRIVING - LONG TERM GUEST DEPARTING - SAME DAY Turnover STR`
    - Regular + owner + long-term: `OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 3`
    - Simple same-day: `SAME DAY Turnover STR`
  - Updated file: `src/automation/scripts/airtable-automations/update-service-line-description.js`

## [2.2.14] - 2025-07-30

### Fixed
- **Error Handling Improvements**
  - Fixed double status icon issue (❌❌) in sync details
    - Controller now strips existing status icons before adding new ones
    - Ensures all messages have exactly one status icon
  - Improved error messages with specific context
    - Replaced generic "Unknown error" with exit codes and output info
    - Better error details for troubleshooting
  - Changes applied to both development and production environments
  - Affected files:
    - `controller.py`: Status icon handling logic
    - `run_automation.py`: Error message formatting

## [2.2.13] - 2025-07-29

### Added
- **Automated Service Line Updates via Webhook**
  - Real-time synchronization of service line descriptions from Airtable to HCP
  - Webhook-triggered updates when "Service Line Description" changes
  - Pipe-separated format preserves manual notes: `"Manual notes | Auto-generated service line"`
  - Smart update logic:
    - Only updates when content actually changes
    - Preserves existing manual notes before pipe separator
    - Adds pipe separator automatically if none exists
    - Handles 200-character HCP limit with intelligent truncation
  - Safety features:
    - Currently limited to "Boris Blinderman Test Property" for testing
    - Comprehensive error handling and logging
    - Updates "Last Synced Service Line" field for tracking
  - Implementation:
    - Airtable automation script: `update-hcp-service-line.js`
    - API endpoint: `/api/prod/automation/update-service-line`
    - Uses standard API authentication
  - Solves the critical problem of stale next guest dates in HCP

### Fixed
- **Owner Arrival Same-Day Logic**
  - Owner arrivals (blocks checking in same/next day) are NO LONGER marked as same-day turnovers
  - Prevents creating false "modified" records due to same-day field mismatches
  - Service time should be set to 10:00 AM for owner arrivals (vs 10:15 AM default) via Airtable formula
  - Updated scripts:
    - `find-next-guest-date.js`: Special handling for owner blocks
    - `update-service-line-description.js`: Verified compatibility
  - Benefits:
    - Eliminates sync conflicts between ICS/CSV sources
    - Maintains accurate owner arrival detection
    - Preserves "OWNER ARRIVING" service line labeling
  - Test script: `test-owner-arrival-logic.js`
  - Documentation: `docs_v2/owner-arrival-logic.md`

## [2.2.12] - 2025-07-29

### Added
- **Safe ICS Removal System**
  - Prevents false removals when reservations temporarily disappear from ICS feeds
  - Requires 3 consecutive missing syncs before marking as "Removed" (configurable)
  - 12-hour grace period provides additional safety buffer
  - Automatic protection for:
    - Active HCP jobs (Scheduled/In Progress status)
    - Recent check-ins (within 7 days)
    - Imminent checkouts (today/tomorrow)
  - Automatic recovery: resets tracking when reservation reappears
  - New Airtable fields for tracking:
    - `Missing Count`: Number of consecutive syncs where missing (0-3)
    - `Missing Since`: Timestamp when first detected missing
    - `Last Seen`: Last timestamp when found in ICS feed
  - Comprehensive logging for monitoring removal decisions
  - Test framework and documentation included
  - Currently implemented but NOT ACTIVE (requires enabling `removal_safety.py`)

### Fixed
- **Record 45425 Restoration**
  - Fixed incorrectly removed reservation that was still active in ICS feed
  - Restored from "Removed" to "Modified" status
  - Added audit trail note to Service Sync Details

### Discovered
- **Duplicate Airtable Automations Issue** (July 28, 2025)
  - Identified that Airtable native automations are running at X:06-X:07 every hour
  - These automations fail and overwrite successful cron job results
  - Pattern: Cron runs successfully at X:00, Airtable automation fails at X:06-X:07
  - Symptoms:
    - Sync details show mangled success/failure combinations
    - Generic "Unknown error - check logs for details" messages
    - Airtable shows failures despite logs showing successful runs
  - Root cause: Likely obsolete Airtable automations using old webhook URLs or timing out
  - Resolution: Check Airtable web interface → Automations tab for hourly scheduled automations
  - Impact: Explains discrepancy between successful logs and failed Airtable status

## [2.2.11] - 2025-07-29

### Fixed
- **iTrip Same-Day Turnover Detection**
  - Fixed `update-service-lines-enhanced.py` to correctly detect same-day turnovers when using iTrip Next Guest Date
  - Script now compares checkout date with iTrip Next Guest Date to determine if it's a same-day turnover
  - Automatically updates the "Same-day Turnover" checkbox in Airtable when detected
  - Service lines now correctly show "SAME DAY Turnover STR" instead of "Turnover STR Next Guest Unknown"
  - Handles long-term guests properly: "LONG TERM GUEST DEPARTING - SAME DAY Turnover STR"
  - Fix applies to both development and production environments
  - Verified with comprehensive testing: 17 production records correctly updated

## [2.2.10] - 2025-07-21

### Added
- **Enhanced Sync Status Reporting**
  - Detailed breakdown of sync operations showing new/modified/removed counts
  - Separate counts for reservations and blocks in sync reports
  
### Fixed
- **iTrip Next Guest Date Override**
  - Service lines now correctly use iTrip-provided next guest dates when available
  - Prevents "Next Guest Unknown" when iTrip provides the next guest date
  
- **Single Error Symbol Display**
  - Fixed double ❌ display issue in error messages
  - Error messages now show single, clean error indicator

## [2.2.9] - 2025-07-01

### Added
- **Hybrid UID + Property/Dates/Type Duplicate Detection**
  - Implemented comprehensive duplicate detection combining UID and property/dates/type matching
  - Handles Lodgify's UID changes gracefully - new UIDs for same property/dates are ignored
  - Preserves data integrity while allowing legitimate UID updates
  - Test framework validates all duplicate detection scenarios automatically

## [2.2.8] - 2025-06-27

### Added
- **Enhanced Service Line Updates with Owner Detection**
  - New `update-service-lines-enhanced.py` script that detects owner arrivals automatically
  - Detects when a Block (owner) checks in same day or next day after reservation checkout
  - Automatically sets "Owner Arriving" field in Airtable without requiring Airtable automations
  - Adds "OWNER ARRIVING" to service line descriptions in correct hierarchy
  - Service line format: `[Custom Instructions] - OWNER ARRIVING - [LONG TERM GUEST] - [Base Service Name]`
  - Processes all reservations with active HCP jobs every 4 hours
  - No longer depends on Airtable automation scripts for owner detection

### Changed
- Updated `run_automation.py` to use enhanced service line update script
- Service line updates now handle owner detection internally in Python

## [2.2.7] - 2025-06-26

### Fixed
- **API Field Mapping Errors**
  - Fixed "Unknown field name: 'Sync Details'" error in production environment
  - Both dev and prod now use "Schedule Sync Details" and "Service Sync Details" field names
  - Affects job creation, schedule update endpoints, and webhook handlers
  - Fixed webhook handler field mapping in webhook.py
  
- **Next Guest Date Detection**
  - Fixed job creation using "Next Guest Unknown" when Next Guest Date field was populated
  - API now checks Airtable's "Next Guest Date" field first before searching for next reservation
  - Results in correct service names like "Turnover STR Next Guest July 3" instead of "Unknown"

## [2.2.6] - 2025-06-25

### Fixed
- **Schedule Sync Details Timezone Display**
  - Fixed timezone display in reconciliation script showing UTC times instead of Arizona timezone
  - Changed confusing message format from "Job scheduled for X but expected X" to "Airtable shows X but HCP shows Y"
  - Added `--force` flag to reconcile-jobs.py to allow updating records with existing job IDs but "Wrong Time" status
  - Updated 32 production records with corrected time display format

## [2.2.5] - 2025-06-24

### Added
- **HCP Job Reconciliation System**
  - Standalone script (`reconcile-jobs-dev.py`) for manual reconciliation
  - Webhook integration module for automatic reconciliation
  - Matches HCP jobs to Airtable reservations based on property, customer, and time
  - Supports dry-run mode for safe testing
  - Currently limited to dev environment (configurable)
  - Comprehensive documentation in `docs/features/job-reconciliation.md`

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