#!/bin/bash
cd ~/automation

# Load .env file
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found in ~/automation"
    exit 1
fi

# Environment detection and variable mapping
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Using PRODUCTION Airtable environment"
    export AIRTABLE_API_KEY="$PROD_AIRTABLE_API_KEY"
    export AIRTABLE_BASE_ID="$PROD_AIRTABLE_BASE_ID"
    export AIRTABLE_TABLE_ID="$PROD_AIRTABLE_TABLE_ID"
else
    echo "Using DEVELOPMENT Airtable environment"
    export AIRTABLE_API_KEY="$DEV_AIRTABLE_API_KEY"
    export AIRTABLE_BASE_ID="$DEV_AIRTABLE_BASE_ID"
    export AIRTABLE_TABLE_NAME="$DEV_AIRTABLE_TABLE_NAME"
fi

# Verify required variables are set
if [ -z "$AIRTABLE_API_KEY" ]; then
    echo "Error: AIRTABLE_API_KEY not set for environment: $ENVIRONMENT"
    exit 1
fi

if [ -z "$AIRTABLE_BASE_ID" ]; then
    echo "Error: AIRTABLE_BASE_ID not set for environment: $ENVIRONMENT"
    exit 1
fi

echo "Base ID: $AIRTABLE_BASE_ID"
echo "Environment: $ENVIRONMENT"

# Start the MCP server
exec airtable-mcp-server "$@"
