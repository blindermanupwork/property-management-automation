import { HCPService } from './dist/hcp-mcp-dev/src/hcpService.js';

// Test the actual API call
const config = {
  apiKey: process.env.HCP_API_KEY_DEV || 'dummy-key',
  baseUrl: 'https://api.housecallpro.com', 
  environment: 'dev',
  cache: { enabled: false }  // Disable cache for this test
};

const service = new HCPService(config);

console.log('Testing listCustomers with q parameter...');
const params = { q: 'George Mevawala', page_size: 10 };
console.log('Input params:', params);

try {
  const result = await service.listCustomers(params);
  console.log('Result type:', typeof result);
  console.log('Result keys:', Object.keys(result));
  if (result._cached) {
    console.log('Cache metadata:', result._metadata);
  }
} catch (error) {
  console.error('Error:', error.message);
}