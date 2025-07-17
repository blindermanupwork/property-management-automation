# Evolve Portal Scraping - Version History

## Version 1.0.0 (July 11, 2025)

### Initial Documentation Creation
- **Created by**: Claude AI Assistant
- **Reviewed by**: Pending
- **Changes**:
  - Documented all Evolve scraping business logic
  - Created comprehensive A-Z rules
  - Added 8 Mermaid flow diagrams
  - Documented browser automation patterns
  - Captured environment-specific behavior
  - Detailed sequential processing mode

### Key Business Rules Documented
- Environment variable must be set BEFORE Python starts
- Sequential mode prevents Chrome conflicts
- Headless mode required for server execution
- Two-tab export process (availability + reservations)
- Automatic retry logic (3 attempts)
- File movement to environment-specific directories

### Integration Points Documented
- Selenium WebDriver automation
- Chrome/ChromeDriver configuration
- Download management in /tmp
- CSV processor handoff
- Environment-based routing

---

## Historical Context

### Browser Automation Evolution
- Started with manual exports
- Moved to Selenium automation
- Added headless support for cron
- Implemented sequential mode for stability

### Key Improvements Over Time
1. **Sequential Processing**: Prevents Chrome crashes
2. **Environment Awareness**: Proper dev/prod separation
3. **Retry Logic**: Handles portal timeouts
4. **Download Management**: Reliable file detection
5. **Error Screenshots**: Better debugging

### Known Challenges
- Portal UI changes frequently
- Chrome/ChromeDriver version matching
- Download detection timing
- Session timeout management
- 2FA handling (if enabled)

---

## Technical Specifications

### Browser Requirements
- **Chrome Version**: 90+ recommended
- **ChromeDriver**: Must match Chrome major version
- **Memory**: 2GB minimum for headless
- **Disk Space**: 1GB for downloads

### Performance Metrics
- **Login Time**: ~5 seconds
- **Tab1 Export**: ~30 seconds
- **Tab2 Export**: ~30 seconds
- **Total Runtime**: ~2 minutes typical

### Command Line Usage
```bash
# Production
ENVIRONMENT=production python3 evolveScrape.py --headless --sequential

# Development  
ENVIRONMENT=development python3 evolveScrape.py --headless --sequential

# Debug Mode
ENVIRONMENT=development python3 evolveScrape.py --debug
```

---

## Migration Notes

### From Manual to Automated
- Eliminated daily manual exports
- Reduced human error
- Enabled 4-hour update frequency
- Improved data freshness

### Future Considerations
- Monitor for Evolve API availability
- Consider switching to API when available
- Update selectors quarterly
- Test with new Chrome versions

---

**Next Review Date**: August 11, 2025