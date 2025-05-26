#!/bin/bash
# Development Environment Runner

export ENVIRONMENT=development
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source environments/dev/.env

echo "🔧 RUNNING IN DEVELOPMENT MODE"
echo "Environment: $ENVIRONMENT"
echo "Airtable Base: $AIRTABLE_BASE_ID"
echo "================================"

# Run with dev settings
./run_complete_automation.sh