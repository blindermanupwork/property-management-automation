#!/bin/bash

# Start Trello MCP Server
cd /home/opc/automation/tools/trello-mcp-server

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Start the server
echo "Starting Trello MCP Server..."
npm start