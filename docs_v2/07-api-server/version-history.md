# API Server - Version History

## Overview
This document tracks changes to the API Server feature and its documentation over time.

## Version 2.2.8 (Current)
**Date**: June 2025
**Type**: Feature Enhancement

### Changes
- Added automatic owner arrival detection
- Enhanced service line generation hierarchy
- Implemented 200-character truncation for HCP compatibility
- Added support for Unicode characters in custom instructions

### Business Impact
- Cleaners now see "OWNER ARRIVING" in job descriptions
- Property owners are properly notified of arrivals
- Custom instructions preserved with proper encoding

## Version 2.2.7
**Date**: May 2025
**Type**: Bug Fix

### Changes
- Fixed webhook field mapping for production environment
- Corrected Next Guest Date detection logic
- Updated sync message formatting for consistency

### Technical Details
- Webhook handler now properly maps HCP fields
- Next Guest Date uses Airtable field when available
- Standardized timestamp format across all sync messages

## Version 2.2.6
**Date**: April 2025
**Type**: Integration Update

### Changes
- Replaced embedded Airtable scripts with API endpoints
- Added environment-specific routing
- Implemented proper authentication

### Migration Notes
- All Airtable buttons updated to call API
- Removed scripting extension dependencies
- Added API key management

## Version 2.2.5
**Date**: March 2025
**Type**: Feature Addition

### Changes
- Added long-term guest detection (14+ days)
- Implemented "LONG TERM GUEST DEPARTING" flag
- Enhanced job template management

### Business Logic
- Stays of 14+ days trigger special handling
- Service line includes departure notification
- Template selection based on service type

## Version 2.2.0
**Date**: February 2025
**Type**: Major Refactor

### Changes
- Complete separation of dev/prod environments
- Added forceEnvironment parameter
- Implemented connection pooling

### Architecture Changes
- Separate endpoints for each environment
- Dynamic configuration loading
- Improved error handling

## Version 2.1.0
**Date**: January 2025
**Type**: Feature Enhancement

### Changes
- Added schedule management endpoints
- Implemented custom service time parsing
- Added appointment creation/update logic

### New Endpoints
- POST /api/{env}/schedules/add
- PUT /api/{env}/schedules/update
- DELETE /api/{env}/schedules/{id}

## Version 2.0.0
**Date**: December 2024
**Type**: Major Release

### Changes
- Initial API server implementation
- Basic job creation functionality
- Webhook receipt capability

### Initial Features
- Job creation from Airtable
- Status synchronization
- Basic error handling

## Version 1.0.0
**Date**: November 2024
**Type**: Initial Development

### Changes
- Proof of concept for API approach
- Basic Express server setup
- Minimal endpoint implementation

### Limitations
- No environment separation
- Limited error handling
- No authentication

## Documentation History

### July 12, 2025
- Created comprehensive BusinessLogicAtoZ.md
- Added detailed SYSTEM_LOGICAL_FLOW.md
- Created visual mermaid-flows.md
- Established version tracking

### July 11, 2025
- Initial documentation structure
- Basic README created
- Feature identified for documentation

## Future Planned Updates

### Version 2.3.0 (Planned)
- Batch job creation support
- Enhanced error recovery
- Performance optimizations

### Version 3.0.0 (Proposed)
- GraphQL API addition
- Real-time subscriptions
- Advanced caching layer

---

**Last Updated**: July 12, 2025
**Maintained By**: Automation Team
**Review Cycle**: Monthly