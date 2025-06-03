#!/bin/bash

# Airtable MCP Server Launcher
# This script starts the Airtable MCP server with your environment variables

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$SCRIPT_DIR/airtable-mcp-server"

# Load environment variables from main automation .env file
if [ -f "$SCRIPT_DIR/../.env" ]; then
    source "$SCRIPT_DIR/../.env"
fi

# Set additional environment variables if needed
export AIRTABLE_API_KEY="${AIRTABLE_API_KEY:-patbrTH6yCjhAwd4i.972b74cbf7ea28c84e773759269c291628b5b4f4bfa11989ac4eff5d618f4003}"

echo "🔍 Starting Airtable MCP Server..."
echo "🔑 Using API key: ${AIRTABLE_API_KEY:0:10}..."
echo "📂 MCP server path: $MCP_DIR"

cd "$MCP_DIR"
exec node dist/index.js "$@"