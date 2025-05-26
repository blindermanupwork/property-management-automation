#!/bin/bash
# Production Environment Runner

export ENVIRONMENT=production
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source environments/prod/.env

echo "🚀 RUNNING IN PRODUCTION MODE"
echo "Environment: $ENVIRONMENT"
echo "Airtable Base: $AIRTABLE_BASE_ID"
echo "================================"

# Run with production settings
./run_complete_automation.sh