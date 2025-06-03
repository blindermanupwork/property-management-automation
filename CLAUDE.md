# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Development
```bash
# Run the main automation (no installation required)
python src/run_anywhere.py

# Run with automatic dependency installation
python src/run_anywhere.py --auto-install

# List all available automations
python src/run_anywhere.py --list

# Run tests
pytest tests/
pytest tests/ --cov=automation  # with coverage

# Code formatting and linting
black src/ tests/
isort src/ tests/
mypy src/

# Build package
python -m build

# Install in development mode
pip install -e .
```

### Entry Points (after installation)
- `run-automation` - Main automation runner
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

- All file paths must use `Config` class methods for cross-platform compatibility
- Timezone handling: Use PST for logs, Arizona timezone for business data
- CSV processing maintains audit trail in `CSV_done/` directory
- Python handles core automation; JavaScript used for AI agent and HCP integration
- Logs are centralized in `src/automation/logs/` with specific files for each component
- Environment variables loaded from `.env` file at project root