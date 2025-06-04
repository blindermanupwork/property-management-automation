# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Development
```bash
# Environment-specific runners (PREFERRED)
python3 src/run_automation_dev.py --dry-run     # Test development automation
python3 src/run_automation_dev.py              # Run development automation
python3 src/run_automation_prod.py --dry-run   # Test production automation  
python3 src/run_automation_prod.py             # Run production automation

# Universal runner (auto-detects environment)
python3 src/run_anywhere.py --info             # Show system information
python3 src/run_anywhere.py --test             # Run system tests
python3 src/run_anywhere.py --list             # List available automations
python3 src/run_anywhere.py                    # Run automation

# Setup and validation
python3 test_setup.py                          # Validate setup

# Testing
pytest tests/ -v                               # Run tests with verbose output
pytest tests/ --cov=automation                 # Run tests with coverage

# Code quality
black src/ tests/                              # Format code
isort src/ tests/                              # Sort imports  
mypy src/                                      # Type checking

# Build and install
python3 -m build                               # Build package
pip3 install -e .                              # Install in development mode
```

### TypeScript/Node.js Development
```bash
# Airtable MCP Server
cd tools/airtable-mcp-server
npm install && npm run build                   # Build airtable MCP server
npm test                                       # Run tests
npm run lint                                   # Lint TypeScript

# HousecallPro MCP Servers
cd tools/hcp-mcp-dev
npm install && npm run build                   # Build dev MCP server
cd tools/hcp-mcp-prod  
npm install && npm run build                   # Build prod MCP server

# Test MCP connections
node tools/test-mcp-connection.js              # Test MCP server connectivity
```

### Environment Management
```bash
# Cron setup
./cron_setup_dev.sh                           # Setup development cron (30min)
./cron_setup_prod.sh                          # Setup production cron (4hr)
./cron_remove.sh                              # Remove old cron jobs

# View logs
tail -f src/automation/logs/automation_dev*.log     # Development logs
tail -f src/automation/logs/automation_prod*.log    # Production logs

# Check cron status
crontab -l                                     # View current cron jobs
```

### Entry Points (after installation)
- `run-automation-dev` - Development automation runner
- `run-automation-prod` - Production automation runner  
- `run-automation` - Universal automation runner
- `evolve-scraper` - Evolve property scraper  
- `csv-processor` - CSV processing tool
- `ics-sync` - Calendar synchronization
- `gmail-downloader` - Gmail CSV downloader

## Architecture Overview

This is a comprehensive property management automation system that orchestrates multiple data flows:

1. **Data Sources**:
   - Gmail: Downloads iTrip reservation CSVs via OAuth
   - Evolve: Scrapes property data using Selenium
   - ICS Feeds: Syncs calendar data from property management systems
   - Webhooks: Real-time updates from external services

2. **Core Processing**:
   - **Config System** (`src/automation/config.py`): Centralized configuration managing all paths, timezone handling (PST for logs, Arizona for business data), and environment variables
   - **Controller** (`src/automation/controller.py`): Orchestrates automations based on Airtable settings with error handling and logging
   - **CSV Workflow**: Files move from `CSV_process/` → processing → `CSV_done/` with detailed tracking

3. **Integrations**:
   - **Airtable**: Central data store with two-way sync
   - **HousecallPro**: Service job management via JavaScript integration
   - **AI Agent**: OpenAI-powered interface for data queries (Node.js/Express)

4. **Key Design Patterns**:
   - Universal runner (`run_anywhere.py`) works without installation
   - Cross-platform path handling using `pathlib`
   - Modular script organization by function
   - Dual-timezone strategy for accurate business operations
   - Environment-aware configuration (dev/prod)

## Important Project Conventions

### Environment Separation
- **Complete isolation** between development and production environments
- Use `run_automation_dev.py` for development (Airtable: `app67yWFv0hKdl6jM`)
- Use `run_automation_prod.py` for production (Airtable: `appZzebEIqCU5R9ER`)
- Environment-specific configuration files: `config/environments/dev/.env` and `config/environments/prod/.env`
- CSV directories: `CSV_*_development/` vs `CSV_*_production/`
- Logs: `automation_dev*.log` vs `automation_prod*.log`

### File and Path Handling
- Always use `python3` command (not `python`) for execution
- All file paths must use `Config` class methods for cross-platform compatibility
- CSV processing maintains audit trail in environment-specific `CSV_done/` directories
- Logs centralized in `src/automation/logs/` with environment-specific files

### Data and Timezone Management  
- Timezone handling: Use PST for logs, Arizona timezone for business data
- Environment variables loaded from environment-specific `.env` files
- API endpoints separated by environment (`/api/dev/*` vs `/api/prod/*`)

### Technology Stack
- **Python**: Core automation logic, universal runners, data processing
- **JavaScript/TypeScript**: AI agent (OpenAI integration), HousecallPro API, MCP servers
- **MCP (Model Context Protocol)**: Airtable and HousecallPro integrations for Claude
- **Cron**: Automated scheduling (30min dev, 4hr prod intervals)

### MCP Server Integration
- `airtable-mcp-server`: Provides Claude access to Airtable data
- `hcp-mcp-dev` / `hcp-mcp-prod`: Environment-specific HousecallPro API access
- Use `airtable-dev` or `airtable-prod` MCP server based on context
- Test MCP connectivity with `node tools/test-mcp-connection.js`