# Schedule Management - Version History

## Overview
This document tracks changes to the Schedule Management feature and its documentation over time.

## Version 2.2.8 (Current)
**Date**: June 2025
**Type**: Feature Enhancement

### Changes
- Added automatic owner arrival detection
- Enhanced schedule calculation with owner flags
- Improved conflict detection algorithms
- Added support for custom service instructions in schedules

### Business Impact
- Properties are prepared to premium standards for owners
- Scheduling conflicts are automatically resolved
- Service windows adapt to special circumstances

## Version 2.2.7
**Date**: May 2025
**Type**: Bug Fix

### Changes
- Fixed timezone calculation issues
- Corrected same-day turnover detection logic
- Improved schedule sync reliability

### Technical Details
- All times now properly convert to MST/Arizona
- Same-day detection accounts for edge cases
- Retry logic added for failed syncs

## Version 2.2.5
**Date**: April 2025
**Type**: Feature Addition

### Changes
- Implemented long-term guest detection (14+ days)
- Added "LONG TERM GUEST DEPARTING" service flags
- Enhanced service duration calculations

### Business Logic
- Stays >= 14 days trigger extended cleaning
- Service duration increased by 1 hour minimum
- Special instructions added for deep cleaning

## Version 2.2.0
**Date**: March 2025
**Type**: Major Update

### Changes
- Complete rewrite of schedule calculation engine
- Added property-specific default windows
- Implemented conflict resolution system

### New Features
- Automatic conflict detection
- Smart time shifting algorithms
- Resource reallocation logic

## Version 2.1.0
**Date**: February 2025
**Type**: Feature Enhancement

### Changes
- Added custom service time overrides
- Implemented "HH:MM AM/PM" parsing
- Added override validation

### User Experience
- Manual schedule adjustments via Airtable
- Clear error messages for invalid times
- Conflict warnings before override

## Version 2.0.0
**Date**: January 2025
**Type**: Major Release

### Changes
- Introduced same-day turnover detection
- Added urgency level calculations
- Implemented expedited service windows

### Business Rules
- Check-in before 2 PM = urgent (2-hour window)
- Check-in 2-4 PM = standard (3-hour window)
- Check-in after 4 PM = relaxed (3-hour window)

## Version 1.5.0
**Date**: December 2024
**Type**: Integration Update

### Changes
- Added HousecallPro appointment creation
- Implemented schedule synchronization
- Added arrival window support

### API Integration
- Create appointments with calculated times
- Update existing appointments
- Handle API rate limits

## Version 1.0.0
**Date**: November 2024
**Type**: Initial Release

### Changes
- Basic schedule calculation from checkout times
- Standard service windows implemented
- Initial Airtable field creation

### Initial Features
- 11 AM checkout → 12-4 PM service
- 4-hour default duration
- MST timezone handling

## Documentation History

### July 12, 2025
- Created comprehensive BusinessLogicAtoZ.md
- Added detailed SYSTEM_LOGICAL_FLOW.md
- Created visual mermaid-flows.md
- Established version tracking

### Key Documentation Updates
- Added long-term guest logic documentation
- Documented owner arrival detection process
- Created visual workflow diagrams
- Updated with current business rules

## Migration Notes

### From Version 1.x to 2.x
- New fields required in Airtable
- Updated time window calculations
- Enhanced conflict detection

### From Version 2.0 to 2.2
- Additional flags for special cases
- New override mechanisms
- Improved sync reliability

## Known Issues

### Current Limitations
- Maximum 6-hour service duration
- Business hours 7 AM - 8 PM only
- Single cleaner assignment per service

### Planned Improvements
- Multi-day service splitting
- Team assignment support
- Dynamic duration calculation

## Performance Metrics

### Version 2.2.8 Performance
- Average calculation time: 150ms
- Conflict detection: 80ms
- HCP sync time: 2-3 seconds
- Success rate: 99.2%

### Historical Performance
- v1.0: 500ms calculation time
- v2.0: 300ms with conflict detection
- v2.2: 150ms with full features

## Future Roadmap

### Version 2.3.0 (Planned)
- AI-powered schedule optimization
- Predictive conflict prevention
- Batch schedule processing

### Version 3.0.0 (Proposed)
- Real-time schedule updates
- Mobile app integration
- Advanced analytics

## Support Information

### Key Files
- `/src/automation/scripts/airtable-automations/calculate-service-time.js`
- `/src/automation/scripts/hcp/schedule-sync.js`
- `/src/automation/scripts/shared/scheduleHelpers.js`

### Configuration
- Default windows in `config/schedule-windows.json`
- Property overrides in Airtable
- Business hours in environment variables

---

**Last Updated**: July 12, 2025
**Maintained By**: Automation Team
**Review Cycle**: Monthly
**Next Review**: August 2025