#!/bin/bash
# Production Environment Runner

export ENVIRONMENT=production
cd ~/automation
source environments/prod/.env

echo "🚀 RUNNING IN PRODUCTION MODE"
echo "Environment: $ENVIRONMENT"
echo "Airtable Base: $AIRTABLE_BASE_ID"
echo "================================"

# Run with production settings
./run_complete_automation.sh