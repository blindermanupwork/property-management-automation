# System Overview

## Purpose
This feature provides a high-level understanding of the entire property management automation system, its architecture, and how all components work together.

## Quick Start
1. Read [BusinessLogicAtoZ.md](./BusinessLogicAtoZ.md) for core system rules
2. Review [SYSTEM_LOGICAL_FLOW.md](./SYSTEM_LOGICAL_FLOW.md) for visual architecture
3. Explore individual features via [FEATURE_MAP.md](../FEATURE_MAP.md)

## Key Components
- **Data Sources**: CloudMailin, ICS feeds, Evolve portal
- **Processing Engine**: Python automation controller
- **Storage**: Airtable database
- **Service Management**: HousecallPro integration
- **APIs**: REST API server, MCP servers
- **Environment**: Complete dev/prod separation

## Directory Structure
```
00-system-overview/
├── README.md                    # This file
├── BusinessLogicAtoZ.md         # System-wide business rules
├── SYSTEM_LOGICAL_FLOW.md       # Architecture diagrams
├── version-history.md           # Change log
├── flows/
│   ├── data-flow.mmd           # Overall data flow
│   ├── integration-map.mmd     # Component connections
│   └── deployment.mmd          # Infrastructure diagram
└── examples/
    └── typical-workflow.md     # Day in the life example
```

## Related Features
- [Environment Management](../14-environment-management/) - Dev/prod setup
- [Automation Controller](../13-automation-controller/) - Process orchestration
- [API Server](../07-api-server/) - External interfaces

## Common Issues
1. **Environment Confusion**: Always verify which environment you're in
2. **Integration Failures**: Check API keys and network connectivity
3. **Performance**: Monitor resource usage during peak hours

## Maintenance Notes
- Review architecture quarterly
- Update diagrams when adding features
- Keep integration map current
- Document all external dependencies

## Version
Current: v2.2.8 (July 11, 2025)