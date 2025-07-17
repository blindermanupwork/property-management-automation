# CSV Processing - Version History

## Version 1.0.0 (July 11, 2025)

### Initial Documentation Creation
- **Created by**: Claude AI Assistant
- **Reviewed by**: Pending
- **Changes**:
  - Documented all CSV processing business logic
  - Created comprehensive A-Z rules
  - Added 8 Mermaid flow diagrams
  - Documented iTrip and Evolve specific handling
  - Captured UID generation algorithm
  - Detailed duplicate detection logic

### Key Business Rules Documented
- UID format: `{source}_{property}_{checkin}_{checkout}_{lastname}`
- Date range: 6 months past, 12 months future
- Duplicate handling: Clone-mark-create pattern
- File movement: Only after successful processing
- Property matching: Exact name match required

### Integration Points Documented
- CloudMailin webhook integration
- Airtable synchronization
- File system management
- Error handling and recovery

---

## Migration Notes

### From Gmail OAuth to CloudMailin (Historical)
- Replaced Gmail OAuth with webhook approach
- More reliable email processing
- No authentication refresh needed
- Faster processing times

---

**Next Review Date**: August 11, 2025