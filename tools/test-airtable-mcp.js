#!/usr/bin/env node

// Test script to verify Airtable MCP server connection
const { spawn } = require('child_process');
const path = require('path');

console.log('🔍 Testing Airtable MCP Server connection...');

const mcpPath = path.join(__dirname, 'airtable-mcp-server', 'dist', 'index.js');

const env = {
    ...process.env,
    AIRTABLE_API_KEY: 'patbrTH6yCjhAwd4i.972b74cbf7ea28c84e773759269c291628b5b4f4bfa11989ac4eff5d618f4003'
};

console.log('📡 Starting MCP server...');
console.log('🔑 Using API key:', env.AIRTABLE_API_KEY.substring(0, 10) + '...');
console.log('📂 MCP server path:', mcpPath);

// Test basic connectivity
const testConnection = spawn('node', [mcpPath], {
    env: env,
    stdio: ['pipe', 'pipe', 'pipe']
});

let output = '';
let errorOutput = '';

testConnection.stdout.on('data', (data) => {
    output += data.toString();
});

testConnection.stderr.on('data', (data) => {
    errorOutput += data.toString();
});

// Send a simple MCP request to test
setTimeout(() => {
    const testRequest = JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
            protocolVersion: "2024-11-05",
            capabilities: {},
            clientInfo: {
                name: "test-client",
                version: "1.0.0"
            }
        }
    }) + '\n';
    
    testConnection.stdin.write(testRequest);
    
    setTimeout(() => {
        testConnection.kill();
    }, 2000);
}, 1000);

testConnection.on('close', (code) => {
    console.log('📊 Test Results:');
    console.log('Exit code:', code);
    
    if (output) {
        console.log('✅ Output received:', output.substring(0, 200) + '...');
    }
    
    if (errorOutput) {
        console.log('⚠️  Errors:', errorOutput);
    }
    
    if (code === 0 || output.includes('"result"')) {
        console.log('🎉 MCP Server appears to be working!');
    } else {
        console.log('❌ MCP Server may have issues');
    }
});