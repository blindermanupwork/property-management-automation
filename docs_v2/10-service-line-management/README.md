# Service Line Management Documentation

## Overview

The Service Line Management feature handles the creation, customization, and formatting of service line descriptions for cleaning jobs. This includes custom instructions, special flags for long-term guests and owner arrivals, character limits, and Unicode support for diverse content.

## Quick Navigation

- **BusinessLogicAtoZ.md** - Complete business rules for service line creation and formatting
- **SYSTEM_LOGICAL_FLOW.md** - Text-based operational flow descriptions
- **mermaid-flows.md** - Visual workflow diagrams
- **version-history.md** - Feature change tracking

## Key Capabilities

### 1. Custom Instructions Support
- Accept user-defined custom instructions in Airtable
- Support full Unicode character set (accents, emojis, special chars)
- Automatic truncation to 200 characters for HCP compatibility
- Preserve original instructions for audit trail

### 2. Special Flag Management
- "OWNER ARRIVING" flag for property owner returns
- "LONG TERM GUEST DEPARTING" flag for 14+ day stays
- "SAME DAY" prefix for urgent turnover situations
- Hierarchical flag ordering and combination rules

### 3. Service Name Generation
- Construct complete service line descriptions
- Combine custom instructions with system flags
- Generate base service names with dates
- Format output for HousecallPro job creation

### 4. Character Limit Enforcement
- Hard limit of 200 characters for HCP API compatibility
- Intelligent truncation preserving most important content
- Priority-based content inclusion (flags > custom > base)
- Warning system for content that exceeds limits

## Business Context

### Property Management Workflow
1. **Reservation Processing**: System detects special circumstances
2. **Flag Assignment**: Automatic flags based on business rules
3. **Custom Instructions**: User adds specific cleaning requirements
4. **Service Line Assembly**: All components combined with formatting
5. **HCP Job Creation**: Service line becomes first line item name

### Key Decision Points
- **Priority Order**: Which content takes precedence when space limited
- **Flag Conditions**: When to apply special flags automatically
- **Unicode Handling**: Support for international characters
- **Truncation Strategy**: How to preserve most important information

## Service Line Structure

### Hierarchical Format
```
[Custom Instructions] - [Special Flags] - [Base Service Name]
```

### Component Priority (High to Low)
1. **Special Flags**: OWNER ARRIVING, LONG TERM GUEST DEPARTING
2. **Custom Instructions**: User-defined cleaning requirements
3. **Same-Day Prefix**: SAME DAY indicator for urgent jobs
4. **Base Service Name**: Standard turnover description with date

### Example Outputs
```
// Full service line with all components
"Deep clean all surfaces - OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 15"

// With truncation applied
"Custom cleaning instructions - OWNER ARRIVING - Turnover STR Next Guest July 15"

// Same-day turnover
"SAME DAY Turnover STR Next Guest Today"
```

## Unicode and Internationalization

### Supported Characters
- **Latin Extensions**: Accented characters (á, é, ñ, ü)
- **Emoji Support**: ✅ 🏠 🧹 (cleaning-related emojis)
- **Special Symbols**: Bullets, arrows, currency symbols
- **International Names**: Guest names in various languages

### Encoding Handling
- UTF-8 encoding throughout the system
- Proper character counting for Unicode strings
- HousecallPro API compatibility validation
- Database storage optimization

## Flag Assignment Rules

### Owner Arriving Detection
**Trigger**: Property owner block starts 0-1 days after guest checkout
**Logic**: 
```javascript
// Detect owner blocks following reservations
const ownerBlock = findNextBlock(property, checkoutDate, 48hours);
if (ownerBlock && daysBetween(checkout, ownerBlock.checkin) <= 1) {
    addFlag("OWNER ARRIVING");
}
```

### Long-Term Guest Detection  
**Trigger**: Stay duration of 14+ consecutive days
**Logic**:
```javascript
const stayDuration = calculateDays(checkinDate, checkoutDate);
if (stayDuration >= 14) {
    addFlag("LONG TERM GUEST DEPARTING");
}
```

### Same-Day Turnover Detection
**Trigger**: Next guest checks in same day as current checkout
**Logic**:
```javascript
const nextGuest = findNextReservation(property, checkoutDate);
if (nextGuest && nextGuest.checkinDate === checkoutDate) {
    addPrefix("SAME DAY");
}
```

## Truncation Algorithm

### Priority-Based Truncation
1. **Preserve Flags**: Special flags always included
2. **Truncate Custom**: Cut custom instructions if needed
3. **Preserve Base**: Always keep base service name
4. **Smart Truncation**: Cut at word boundaries when possible

### Implementation
```javascript
function buildServiceLine(components, maxLength = 200) {
    // Required components (never truncated)
    const required = [
        components.ownerFlag,
        components.longTermFlag,
        components.baseServiceName
    ].filter(Boolean);
    
    // Optional components (truncated if needed)
    const optional = [
        components.customInstructions,
        components.sameDayPrefix
    ].filter(Boolean);
    
    // Build with truncation
    let result = required.join(' - ');
    const remainingSpace = maxLength - result.length;
    
    if (remainingSpace > 0 && optional.length > 0) {
        const optionalText = optional.join(' - ');
        if (optionalText.length <= remainingSpace) {
            result = `${optionalText} - ${result}`;
        } else {
            // Smart truncation at word boundaries
            const truncated = truncateAtWordBoundary(
                optionalText, 
                remainingSpace - 3
            ) + '...';
            result = `${truncated} - ${result}`;
        }
    }
    
    return result;
}
```

## Error Handling

### Common Issues
1. **Encoding Errors**: Invalid Unicode sequences
2. **Length Violations**: Exceeding 200 character limit
3. **Missing Data**: Empty or null custom instructions
4. **API Compatibility**: HCP field limitations

### Resolution Strategies
1. **Fallback Encoding**: Convert problematic characters to ASCII
2. **Progressive Truncation**: Remove components in priority order
3. **Validation**: Pre-check before HCP API calls
4. **User Feedback**: Warn when content is modified

## Integration Points

### 1. Airtable Fields
- **Service Line Custom Instructions**: User input field
- **Owner Arriving**: Auto-populated boolean flag
- **Long Term Stay**: Auto-calculated stay duration
- **Same-day Turnover**: Auto-detected boolean

### 2. HousecallPro Integration
- Service line becomes first line item name
- 200 character limit enforced by API
- Unicode support varies by HCP version
- Job creation includes full service description

### 3. Automation Triggers
- New reservation → Analyze for flags
- Date changes → Recalculate flags
- Custom instructions → Rebuild service line
- Job creation → Apply final formatting

## Performance Considerations

### Optimization Strategies
- Cache flag calculations for batch operations
- Pre-compile Unicode validation patterns
- Minimize string operations during assembly
- Batch service line updates

### Monitoring Points
- Custom instruction usage rates
- Truncation frequency
- Unicode processing errors
- HCP API rejection rates

## Related Documentation

- See **BusinessLogicAtoZ.md** for detailed service line rules
- See **mermaid-flows.md** for visual assembly workflows
- See **SYSTEM_LOGICAL_FLOW.md** for process descriptions

---

**Primary Code Location**: Multiple integration points
**Key Files**: 
- `/src/automation/scripts/airscripts-api/handlers/jobs.js`
- `/src/automation/scripts/hcp/dev-hcp-sync.cjs`
- `/src/automation/scripts/hcp/prod-hcp-sync.cjs`
- `/src/automation/scripts/airtable-automations/update-service-line-description.js`
**Last Updated**: July 12, 2025