#!/usr/bin/env node

/**
 * HousecallPro MCP Server - Development Environment
 * Entry point for the development MCP server
 */

import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { HCPService } from './hcpService.js';
import { HCPMCPServer } from './mcpServer.js';
import { HCPConfig } from '../../hcp-mcp-common/src/index.js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from dev config
const envPath = '/home/opc/automation/config/environments/dev/.env';
dotenv.config({ path: envPath });

console.log('🔧 Starting HCP MCP Server - Development Environment');
console.log(`📁 Loading config from: ${envPath}`);

// Validate required environment variables
const requiredEnvVars = [
  'DEV_HCP_TOKEN',
  'DEV_HCP_BASE_URL'
];

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    console.error(`❌ Missing required environment variable: ${envVar}`);
    process.exit(1);
  }
}

// Create HCP configuration
const config: HCPConfig = {
  apiKey: process.env.DEV_HCP_TOKEN!,
  baseUrl: process.env.DEV_HCP_BASE_URL || 'https://api.housecallpro.com',
  environment: 'dev',
  employeeId: process.env.DEV_HCP_EMPLOYEE_ID,
  rateLimit: {
    requestsPerMinute: parseInt(process.env.DEV_HCP_RATE_LIMIT || '60'),
    retryAfterMs: parseInt(process.env.DEV_HCP_RETRY_AFTER_MS || '1000')
  }
};

// Validate API key format
if (!config.apiKey || config.apiKey.length < 20) {
  console.error('❌ Invalid HCP API token format. Token should be at least 20 characters long.');
  process.exit(1);
}

console.log('✅ Configuration validated');
console.log(`🌐 API Base URL: ${config.baseUrl}`);
console.log(`⚡ Rate Limit: ${config.rateLimit?.requestsPerMinute || 60} requests/minute`);
if (config.employeeId) {
  console.log(`👤 Default Employee ID: ${config.employeeId}`);
}

// Create services
const hcpService = new HCPService(config);
const mcpServer = new HCPMCPServer(hcpService, 'dev');

// Set up graceful shutdown
const cleanup = () => {
  console.log('\n🛑 Shutting down HCP MCP Server...');
  process.exit(0);
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

// Start the server
async function main() {
  try {
    console.log('🚀 Starting MCP server transport...');
    
    const transport = new StdioServerTransport();
    await mcpServer.getServer().connect(transport);
    
    console.log('✅ HCP MCP Server (DEV) is running');
    console.log('📡 Ready to receive tool calls via MCP protocol');
    
    // Log status information
    const status = hcpService.getStatus();
    console.log('📊 Service Status:', JSON.stringify(status, null, 2));
    
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

main().catch((error) => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});