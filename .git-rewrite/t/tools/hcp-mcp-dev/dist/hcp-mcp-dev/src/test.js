#!/usr/bin/env node
/**
 * Test Script for HCP MCP Server - Development Environment
 * Tests all MCP tools to validate functionality
 */
import { HCPService } from './hcpService.js';
import { HCPMCPServer } from './mcpServer.js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Load environment variables
const envPath = '/home/opc/automation/config/environments/dev/.env';
console.log(`📁 Attempting to load environment from: ${envPath}`);
const result = dotenv.config({ path: envPath });
console.log(`📁 Environment load result:`, result.error ? result.error.message : 'Success');
console.log(`🔑 DEV_HCP_TOKEN loaded:`, process.env.DEV_HCP_TOKEN ? 'Yes' : 'No');
console.log('🧪 HCP MCP Server Test Suite - Development Environment');
console.log('================================================');
// Validate environment variables first
console.log(`🔍 Checking DEV_HCP_TOKEN: ${process.env.DEV_HCP_TOKEN ? 'exists' : 'missing'}`);
if (process.env.DEV_HCP_TOKEN) {
    console.log(`🔍 Token length: ${process.env.DEV_HCP_TOKEN.length}`);
}
if (!process.env.DEV_HCP_TOKEN) {
    console.error('❌ Missing DEV_HCP_TOKEN environment variable');
    process.exit(1);
}
if (process.env.DEV_HCP_TOKEN.length < 20) {
    console.error(`❌ Invalid HCP API token format. Length: ${process.env.DEV_HCP_TOKEN.length}, Required: >=20`);
    process.exit(1);
}
// Test configuration
const config = {
    apiKey: process.env.DEV_HCP_TOKEN,
    baseUrl: process.env.DEV_HCP_BASE_URL || 'https://api.housecallpro.com',
    environment: 'dev',
    employeeId: process.env.DEV_HCP_EMPLOYEE_ID,
    rateLimit: {
        requestsPerMinute: parseInt(process.env.DEV_HCP_RATE_LIMIT || '60'),
        retryAfterMs: parseInt(process.env.DEV_HCP_RETRY_AFTER_MS || '1000')
    },
    cache: {
        enabled: false, // Disable caching for tests
        baseDir: '/tmp/cache',
        retentionHours: 24,
        maxSizeMB: 100,
        thresholds: {
            jobs: 50,
            customers: 50,
            lineItems: 50,
            characters: 50000
        }
    }
};
console.log('✅ Configuration loaded');
console.log(`🌐 Base URL: ${config.baseUrl}`);
console.log(`🔑 Token: ${config.apiKey.substring(0, 10)}...`);
const hcpService = new HCPService(config);
// Test results tracking
const testResults = [];
async function runTest(name, testFn) {
    const startTime = Date.now();
    try {
        console.log(`\n🔍 Running test: ${name}`);
        await testFn();
        const duration = Date.now() - startTime;
        testResults.push({ name, status: 'pass', duration });
        console.log(`✅ PASS: ${name} (${duration}ms)`);
    }
    catch (error) {
        const duration = Date.now() - startTime;
        testResults.push({ name, status: 'fail', message: error.message, duration });
        console.log(`❌ FAIL: ${name} (${duration}ms)`);
        console.log(`   Error: ${error.message}`);
    }
}
async function runAllTests() {
    console.log('\n🚀 Starting test suite...\n');
    // Test 1: Service Status
    await runTest('Service Status Check', async () => {
        const status = hcpService.getStatus();
        if (!status.environment || status.environment !== 'dev') {
            throw new Error('Invalid service status');
        }
    });
    // Test 2: List Customers (Basic API connectivity)
    await runTest('List Customers (API Connectivity)', async () => {
        const result = await hcpService.listCustomers({ page: 1, page_size: 5 });
        if (!result || typeof result !== 'object') {
            throw new Error('Invalid response format');
        }
        if (!('data' in result) || !Array.isArray(result.data)) {
            throw new Error('Response missing data array');
        }
        console.log(`   Found ${result.data.length} customers (total: ${result.total || 'unknown'})`);
    });
    // Test 3: List Employees
    await runTest('List Employees', async () => {
        const result = await hcpService.listEmployees({ page: 1, page_size: 5 });
        if (!result || typeof result !== 'object') {
            throw new Error('Invalid employees response format');
        }
        if (!('data' in result) || !Array.isArray(result.data)) {
            throw new Error('Invalid employees response');
        }
        console.log(`   Found ${result.data.length} employees`);
    });
    // Test 4: List Jobs
    await runTest('List Jobs', async () => {
        const result = await hcpService.listJobs({ page: 1, page_size: 5 });
        if (!result || typeof result !== 'object') {
            throw new Error('Invalid jobs response format');
        }
        if (!('data' in result) || !Array.isArray(result.data)) {
            throw new Error('Invalid jobs response');
        }
        console.log(`   Found ${result.data.length} jobs`);
    });
    // Test 5: List Job Types
    await runTest('List Job Types', async () => {
        const result = await hcpService.listJobTypes({ page: 1, page_size: 5 });
        if (!result || typeof result !== 'object') {
            throw new Error('Invalid job types response format');
        }
        if (!('data' in result) || !Array.isArray(result.data)) {
            throw new Error('Invalid job types response');
        }
        console.log(`   Found ${result.data.length} job types`);
    });
    // Test 6: Rate Limiter Status
    await runTest('Rate Limiter Status', async () => {
        const status = hcpService.getStatus();
        const rateLimiterStatus = status.rateLimiter;
        if (!rateLimiterStatus || typeof rateLimiterStatus !== 'object') {
            throw new Error('Rate limiter status unavailable');
        }
        console.log(`   Queue: ${rateLimiterStatus.queueLength}, Processing: ${rateLimiterStatus.processing}`);
        console.log(`   Recent requests: ${rateLimiterStatus.recentRequests}, Remaining: ${rateLimiterStatus.rateLimitRemaining}`);
    });
    // Test 7: MCP Server Tool Listing
    await runTest('MCP Server Tool Definitions', async () => {
        const mcpServer = new HCPMCPServer(hcpService, 'dev');
        const tools = mcpServer['getToolDefinitions'](); // Access private method for testing
        if (!Array.isArray(tools) || tools.length === 0) {
            throw new Error('No MCP tools defined');
        }
        const toolNames = tools.map(t => t.name);
        const expectedToolCount = 27; // Based on our implementation
        if (tools.length < expectedToolCount) {
            throw new Error(`Expected at least ${expectedToolCount} tools, got ${tools.length}`);
        }
        console.log(`   Found ${tools.length} MCP tools:`);
        toolNames.slice(0, 5).forEach(name => console.log(`     - ${name}`));
        if (tools.length > 5) {
            console.log(`     ... and ${tools.length - 5} more`);
        }
    });
    // Test 8: Error Handling
    await runTest('Error Handling (Invalid Customer ID)', async () => {
        try {
            await hcpService.getCustomer('invalid-customer-id');
            throw new Error('Should have thrown an error for invalid customer ID');
        }
        catch (error) {
            if (!error.message.includes('API request failed') && !error.message.includes('404')) {
                throw new Error(`Unexpected error type: ${error.message}`);
            }
            console.log(`   ✅ Correctly handled error: ${error.message.substring(0, 100)}...`);
        }
    });
    // Test 9: Get Specific Customer (if any exist)
    await runTest('Get First Customer (if available)', async () => {
        const customersResult = await hcpService.listCustomers({ page: 1, page_size: 1 });
        if (!customersResult.data || customersResult.data.length === 0) {
            console.log('   ⏭️ Skipping - no customers found');
            testResults[testResults.length - 1].status = 'skip';
            return;
        }
        const firstCustomer = customersResult.data[0];
        const customer = await hcpService.getCustomer(firstCustomer.id);
        if (!customer || customer.id !== firstCustomer.id) {
            throw new Error('Failed to retrieve specific customer');
        }
        console.log(`   Retrieved customer: ${customer.first_name || ''} ${customer.last_name || ''} (${customer.id})`);
    });
    // Test 10: Validate Environment Configuration
    await runTest('Environment Configuration Validation', async () => {
        if (config.environment !== 'dev') {
            throw new Error('Environment should be "dev"');
        }
        if (!config.baseUrl.includes('housecallpro.com')) {
            throw new Error('Invalid base URL');
        }
        if (config.rateLimit && config.rateLimit.requestsPerMinute < 1) {
            throw new Error('Invalid rate limit configuration');
        }
        console.log('   Environment configuration is valid');
    });
    // Print test summary
    console.log('\n📊 Test Summary');
    console.log('===============');
    const passed = testResults.filter(r => r.status === 'pass').length;
    const failed = testResults.filter(r => r.status === 'fail').length;
    const skipped = testResults.filter(r => r.status === 'skip').length;
    const totalDuration = testResults.reduce((sum, r) => sum + (r.duration || 0), 0);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`⏭️ Skipped: ${skipped}`);
    console.log(`⏱️ Total Duration: ${totalDuration}ms`);
    if (failed > 0) {
        console.log('\n❌ Failed Tests:');
        testResults
            .filter(r => r.status === 'fail')
            .forEach(r => console.log(`   - ${r.name}: ${r.message}`));
    }
    console.log('\n🎯 Test Results by Category:');
    const categoryResults = {
        'API Connectivity': testResults.filter(r => r.name.includes('List') || r.name.includes('API')),
        'Error Handling': testResults.filter(r => r.name.includes('Error')),
        'MCP Integration': testResults.filter(r => r.name.includes('MCP')),
        'Configuration': testResults.filter(r => r.name.includes('Configuration') || r.name.includes('Status'))
    };
    Object.entries(categoryResults).forEach(([category, results]) => {
        const categoryPassed = results.filter(r => r.status === 'pass').length;
        const categoryTotal = results.length;
        console.log(`   ${category}: ${categoryPassed}/${categoryTotal} passed`);
    });
    if (failed === 0) {
        console.log('\n🎉 All tests passed! HCP MCP Server (DEV) is ready for use.');
        return true;
    }
    else {
        console.log('\n⚠️ Some tests failed. Please check the configuration and try again.');
        return false;
    }
}
// Main execution
async function main() {
    try {
        const success = await runAllTests();
        process.exit(success ? 0 : 1);
    }
    catch (error) {
        console.error('❌ Test suite failed with fatal error:', error);
        process.exit(1);
    }
}
main().catch(console.error);
