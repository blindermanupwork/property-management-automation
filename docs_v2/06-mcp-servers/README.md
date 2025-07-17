# MCP Servers Documentation

## Overview

This folder contains comprehensive documentation for the Model Context Protocol (MCP) servers used in the property management automation system. These servers enable AI assistants like Claude to interact with external systems through a standardized protocol.

## Available MCP Servers

### 1. HousecallPro MCP Server (`hcp-mcp/`)
Provides complete integration with HousecallPro service management platform.

**Key Capabilities**:
- Job creation and management
- Customer and address operations  
- BULLETPROOF analysis tools (<10ms execution)
- Advanced search functionality
- Business intelligence dashboards
- Line item management
- Employee scheduling

**Environments**:
- Development: `hcp-mcp-dev`
- Production: `hcp-mcp-prod`

### 2. Airtable MCP Server (`airtable-mcp/`)
Enables full database access to Airtable bases for property management.

**Key Capabilities**:
- Database discovery and schema inspection
- Record CRUD operations
- Table and field management
- Advanced filtering with formulas
- Batch operations
- Property management workflows

**Environments**:
- Development: Base `app67yWFv0hKdl6jM`
- Production: Base `appZzebEIqCU5R9ER`

## Quick Navigation

Each MCP server folder contains:
- **README.md** - Overview and quick reference
- **BusinessLogicAtoZ.md** - Complete business logic documentation
- **SYSTEM_LOGICAL_FLOW.md** - Text-based operational flows
- **mermaid-flows.md** - Visual workflow diagrams
- **version-history.md** - Documentation change tracking

## Integration Architecture

```
AI Assistant (Claude)
        ↓
   MCP Protocol
     ↙     ↘
HCP MCP   Airtable MCP
    ↓          ↓
HousecallPro  Airtable
    API        API
```

## Common Use Cases

### Property Management Workflow
1. **Data Import**: Airtable MCP receives reservation data
2. **Validation**: Check for duplicates and required fields
3. **Job Creation**: HCP MCP creates service jobs
4. **Status Sync**: Webhook updates flow back to Airtable
5. **Analysis**: HCP MCP provides business intelligence

### AI Assistant Operations
1. **"Show me today's checkouts"**: Airtable MCP queries reservations
2. **"Create jobs for tomorrow"**: HCP MCP creates service jobs
3. **"Analyze towel usage"**: HCP MCP runs BULLETPROOF analysis
4. **"Update job status"**: Airtable MCP syncs webhook data

## Best Practices

### Security
- Use environment-specific API keys
- Never expose credentials in logs
- Validate permissions before operations
- Maintain audit trails

### Performance
- HCP MCP: Use customer_id filters to avoid pagination
- Airtable MCP: Leverage views and formulas
- Both: Implement proper rate limiting
- Both: Use batch operations when possible

### Data Integrity
- Always validate before creating
- Check for duplicates
- Maintain status lifecycles
- Preserve historical data

## Environment Configuration

### Development Setup
```json
{
  "mcpServers": {
    "airtable-dev": {
      "command": "npx",
      "args": ["-y", "airtable-mcp-server"],
      "env": {
        "AIRTABLE_API_KEY": "pat.dev.xxx"
      }
    },
    "hcp-dev": {
      "command": "node",
      "args": ["/path/to/hcp-mcp-dev/build/index.js"],
      "env": {
        "HCP_API_KEY": "dev_key_xxx"
      }
    }
  }
}
```

### Production Setup
Similar configuration with production API keys and paths.

## Troubleshooting

### Common Issues
1. **Connection failures**: Check API keys and network
2. **Permission errors**: Verify API key scopes
3. **Rate limiting**: Implement backoff strategies
4. **Data mismatches**: Validate against schemas

### Debug Process
1. Test MCP connection with simple operation
2. Verify environment variables are set
3. Check server logs for detailed errors
4. Use development environment for testing

## Related Documentation

- See individual server folders for detailed documentation
- Property management system docs: `../00-system-overview/`
- API server integration: `../07-api-server/`
- Webhook processing: `../13-webhook-system/`

---

**Created**: July 12, 2025  
**Purpose**: Navigation and overview for MCP server documentation  
**Primary Code**: `/tools/airtable-mcp-server/`, `/tools/hcp-mcp-dev/`, `/tools/hcp-mcp-prod/`