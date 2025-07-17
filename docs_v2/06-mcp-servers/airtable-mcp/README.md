# Airtable MCP Server Documentation

## Overview

The Airtable MCP (Model Context Protocol) server provides AI assistants with complete read and write access to Airtable databases. This enables inspection of database schemas, reading records, creating new data, and managing table structures - all through a standardized protocol.

## Quick Navigation

- **BusinessLogicAtoZ.md** - Complete business logic and operations reference
- **SYSTEM_LOGICAL_FLOW.md** - Text-based operational flow descriptions
- **mermaid-flows.md** - Visual workflow diagrams
- **version-history.md** - Documentation change tracking

## Key Capabilities

### 1. Database Discovery
- List all accessible bases
- Get database schemas
- View table structures
- Discover field types

### 2. Record Operations
- List records with filtering
- Search across fields
- Create new records
- Update existing data
- Delete records

### 3. Table Management
- Create new tables
- Update table metadata
- Add/modify fields
- Schema validation

### 4. Advanced Features
- Formula-based filtering
- Multi-field search
- View-based queries
- Batch operations

## Common Use Cases

### Property Management Context
1. **Reservation Management**: Create and update reservation records
2. **Property Tracking**: Manage property database
3. **Job Creation**: Generate service jobs from reservations
4. **Status Updates**: Sync job status between systems
5. **Data Analysis**: Query and aggregate property data

### AI Assistant Workflows
1. **Data Inspection**: "Show me all reservations for next week"
2. **Record Creation**: "Create a new property record"
3. **Bulk Updates**: "Mark all June reservations as processed"
4. **Schema Discovery**: "What fields are in the Properties table?"

## Environment Configuration

### Development Environment
- Base ID: `app67yWFv0hKdl6jM`
- Used for testing and development
- Separate from production data

### Production Environment  
- Base ID: `appZzebEIqCU5R9ER`
- Live operational data
- Used for actual property management

## Security

### API Key Requirements
- Personal Access Token (PAT) required
- Minimum permissions:
  - `schema.bases:read`
  - `data.records:read`
  - `data.records:write` (for modifications)
  - `schema.bases:write` (for table creation)

### Environment Variables
```bash
AIRTABLE_API_KEY=pat123.abc123
```

## Integration with Property Management System

### Key Tables
1. **Reservations**: Guest bookings and property assignments
2. **Properties**: Property details and configurations
3. **Reservations History**: Historical tracking
4. **Automation Control**: System automation settings
5. **Job Templates**: Service job configurations

### Common Patterns
```javascript
// Search for today's checkouts
search_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations", 
    searchTerm: "2025-07-12",
    fieldIds: ["fldCheckOut"]
})

// Create new reservation
create_record({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    fields: {
        "Guest Name": "John Smith",
        "Property": ["recPropertyId"],
        "Check In": "2025-07-15",
        "Check Out": "2025-07-20"
    }
})
```

## Best Practices

### Performance
1. Use `filterByFormula` for complex queries
2. Limit `maxRecords` to reasonable values
3. Use view-based queries when possible
4. Leverage field IDs for targeted searches

### Data Integrity
1. Always validate before updates
2. Use batch operations carefully
3. Check for duplicates before creation
4. Maintain audit trails

### Error Handling
1. Handle rate limits gracefully
2. Validate field types
3. Check permissions before operations
4. Log all modifications

## Troubleshooting

### Common Issues
1. **"Invalid permissions"**: Check API key scopes
2. **"Table not found"**: Verify base and table IDs
3. **"Invalid field type"**: Match Airtable field types
4. **Rate limiting**: Implement backoff strategy

### Debug Steps
1. Verify API key is set correctly
2. Check base/table IDs match environment
3. Test with simple list operation first
4. Review field types in schema

## Related Documentation

- See **BusinessLogicAtoZ.md** for detailed operation documentation
- See **mermaid-flows.md** for visual workflows
- See **SYSTEM_LOGICAL_FLOW.md** for process descriptions

---

**Primary Code Location**: `/tools/airtable-mcp-server/`  
**NPM Package**: `airtable-mcp-server`  
**Protocol**: Model Context Protocol (MCP)  
**Last Updated**: July 12, 2025