#!/usr/bin/env node

import dotenv from 'dotenv';

console.log('Simple test starting...');

// Load environment
const envPath = '/home/opc/automation/config/environments/dev/.env';
console.log(`Loading from: ${envPath}`);

const result = dotenv.config({ path: envPath });
console.log(`Load result:`, result.error ? result.error.message : 'Success');

console.log(`Token exists:`, !!process.env.DEV_HCP_TOKEN);
console.log(`Token length:`, process.env.DEV_HCP_TOKEN ? process.env.DEV_HCP_TOKEN.length : 'N/A');
console.log(`Token preview:`, process.env.DEV_HCP_TOKEN ? process.env.DEV_HCP_TOKEN.substring(0, 10) + '...' : 'N/A');

if (process.env.DEV_HCP_TOKEN && process.env.DEV_HCP_TOKEN.length >= 20) {
  console.log('✅ Token validation passed');
} else {
  console.log('❌ Token validation failed');
}