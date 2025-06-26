#!/usr/bin/env node

import { spawn } from 'child_process';

console.log('🧪 Testing HCP MCP Server Connection...');

const serverProcess = spawn('/usr/bin/node', [
  '/home/opc/automation/tools/hcp-mcp-dev/dist/hcp-mcp-dev/src/index.js'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});

serverProcess.stdout.on('data', (data) => {
  console.log('📤 Server stdout:', data.toString());
});

serverProcess.stderr.on('data', (data) => {
  console.log('❌ Server stderr:', data.toString());
});

serverProcess.on('close', (code) => {
  console.log(`🔚 Server process exited with code ${code}`);
});

// Give it a few seconds to start
setTimeout(() => {
  console.log('⏹️ Stopping test...');
  serverProcess.kill('SIGTERM');
}, 5000);