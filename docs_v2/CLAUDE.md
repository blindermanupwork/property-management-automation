# CLAUDE.md - Documentation v2 Guide

## Purpose
This folder contains the complete feature-based documentation for the property management automation system. Created on July 11, 2025, it represents a comprehensive reorganization of all system documentation.

## What's Different About docs_v2?

### Feature-Based Organization
Unlike the previous documentation which was organized by category (API, deployment, etc.), this structure is organized by **features**. Each major system capability has its own folder with standardized documentation.

### Standardized Documentation
Every feature folder contains:
1. **BusinessLogicAtoZ.md** - All business rules organized alphabetically
2. **SYSTEM_LOGICAL_FLOW.md** - Visual flow diagrams using Mermaid
3. **README.md** - Feature overview and navigation
4. **version-history.md** - Track changes to the feature

### Current Codebase Validation
All documentation has been validated against the actual codebase as of July 11, 2025. No assumptions or outdated information.

## Navigation Guide

### Start Here
1. **FEATURE_MAP.md** - Complete map of all features
2. **00-system-overview/** - High-level system understanding
3. Individual feature folders for deep dives

### Key Features Documented

#### Core Processing
- **01-csv-processing/** - How CSV files from emails become Airtable records
- **02-ics-feed-sync/** - Calendar feed processing from multiple sources
- **03-evolve-scraping/** - Web scraping property data

#### Integration Features
- **04-housecallpro-integration/** - Job creation and management
- **05-airtable-integration/** - Database synchronization
- **06-mcp-servers/** - AI analysis tools (separate docs for HCP and Airtable)
- **07-api-server/** - REST API for job creation and schedule management

#### Business Logic
- **08-schedule-management/** - Service times, same-day turnover, long-term guests
- **09-duplicate-detection/** - UID generation and history preservation
- **10-service-line-management/** - Custom instructions and special flags

## Documentation Standards

### Business Logic Format
- Alphabetically organized (A-Z)
- Each rule includes: condition, action, exceptions
- Code references included

### Flow Diagrams
- Main process flow (required)
- Error handling flow (required)
- Sub-process flows (as needed)
- Example scenarios with step-by-step walkthroughs

### Version Tracking
Each feature maintains its own version history tracking:
- What changed
- Why it changed
- Who changed it
- When it changed

## For AI Assistants

### When Updating Documentation
1. Always validate against current code
2. Update version history
3. Maintain alphabetical organization in BusinessLogicAtoZ
4. Test all examples before documenting
5. Update the TODO tracker

### Key Principles
- **Specificity**: No vague descriptions. Explain exactly what each feature does
- **Accuracy**: All information must match the current codebase
- **Completeness**: Document all business rules, not just the common ones
- **Visual**: Use Mermaid diagrams liberally
- **Searchable**: Maintain A-Z organization for quick lookups

## Important Notes

### MCP Servers Documentation
The MCP servers folder is split into:
- **hcp-mcp/** - HousecallPro MCP capabilities (analysis tools, search functions)
- **airtable-mcp/** - Airtable MCP capabilities (CRUD operations, schema access)

### API Server Specifics
The API server documentation specifically covers:
- Job creation endpoints for Airtable → HCP
- Schedule management and updates
- Webhook receipt and processing
- Environment-specific routing (dev/prod)

### Schedule Management Clarity
Includes all scheduling logic:
- Standard turnover times
- Same-day turnover special handling
- Long-term guest detection (14+ days)
- Owner arrival detection
- Custom service time overrides

## Maintenance

### Regular Updates Needed
1. When new features are added
2. When business rules change
3. When integrations are modified
4. During major version updates

### How to Update
1. Make code changes first
2. Update relevant BusinessLogicAtoZ.md
3. Update flow diagrams if needed
4. Add to version history
5. Update TODO tracker

---

**Created**: July 11, 2025
**Purpose**: Guide for maintaining docs_v2 documentation
**Version**: 1.0.0