import { HCPService } from './dist/hcp-mcp-dev/src/hcpService.js';

const config = {
  apiKey: process.env.HCP_API_KEY_DEV || 'test',
  baseUrl: 'https://api.housecallpro.com',
  environment: 'dev'
};

const service = new HCPService(config);

// Test URL generation
const params = { q: 'George Mevawala', page_size: 10 };
console.log('Testing URL generation with params:', params);

const searchParams = new URLSearchParams();
if (params.page) searchParams.set('page', params.page.toString());
if (params.page_size) searchParams.set('page_size', params.page_size.toString());
if (params.q) searchParams.set('q', params.q);

const query = searchParams.toString();
const path = `/customers${query ? `?${query}` : ''}`;

console.log('Generated path:', path);
console.log('Expected: /customers?page_size=10&q=George%20Mevawala');