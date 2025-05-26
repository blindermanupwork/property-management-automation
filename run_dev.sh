#!/bin/bash
# Development Environment Runner

export ENVIRONMENT=development
cd ~/automation
source environments/dev/.env

echo "🔧 RUNNING IN DEVELOPMENT MODE"
echo "Environment: $ENVIRONMENT"
echo "Airtable Base: $AIRTABLE_BASE_ID"
echo "================================"

# Run with dev settings
./run_complete_automation.sh