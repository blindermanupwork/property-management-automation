#!/usr/bin/env node

/**
 * Debug script to test HCP API pagination directly
 * This will help isolate whether the issue is in our MCP layer or the API itself
 */

const https = require('https');
const url = require('url');

// Test configuration - you'll need to set these
const API_KEY = process.env.HCP_API_KEY_DEV || 'your-api-key-here';
const BASE_URL = 'https://api.housecallpro.com';

async function makeAPICall(endpoint, params = {}) {
  return new Promise((resolve, reject) => {
    const queryParams = new URLSearchParams(params);
    const fullUrl = `${BASE_URL}${endpoint}?${queryParams.toString()}`;
    
    console.log(`\n🔗 Making API call to: ${fullUrl}`);
    console.log(`📋 Query parameters:`, params);
    
    const parsedUrl = url.parse(fullUrl);
    
    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || 443,
      path: parsedUrl.path,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
        'User-Agent': 'HCP-MCP-Debug/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          console.log(`✅ Response status: ${res.statusCode}`);
          console.log(`📊 Response headers:`, res.headers);
          
          // Extract pagination info
          if (jsonData.page !== undefined) {
            console.log(`📄 Pagination info:`);
            console.log(`   - Page: ${jsonData.page}`);
            console.log(`   - Per page: ${jsonData.per_page}`);
            console.log(`   - Page size: ${jsonData.page_size}`);
            console.log(`   - Total: ${jsonData.total}`);
            console.log(`   - Data count: ${jsonData.data ? jsonData.data.length : 'N/A'}`);
          }
          
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: jsonData
          });
        } catch (error) {
          console.log(`❌ Failed to parse JSON response:`, error.message);
          console.log(`📄 Raw response:`, data);
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      console.log(`❌ Request error:`, error.message);
      reject(error);
    });

    req.end();
  });
}

async function testPagination() {
  console.log('🧪 Testing HCP API Pagination Directly');
  console.log('=====================================');
  
  if (!API_KEY || API_KEY === 'your-api-key-here') {
    console.log('❌ Error: Please set HCP_API_KEY_DEV environment variable');
    process.exit(1);
  }

  try {
    // Test 1: Default pagination
    console.log('\n1️⃣ Testing default pagination (no params)');
    const test1 = await makeAPICall('/customers');
    
    // Test 2: Small page size
    console.log('\n2️⃣ Testing page_size=5');
    const test2 = await makeAPICall('/customers', { page_size: 5 });
    
    // Test 3: Large page size
    console.log('\n3️⃣ Testing page_size=100');
    const test3 = await makeAPICall('/customers', { page_size: 100 });
    
    // Test 3.5: Very large page size to test API limits
    console.log('\n3️⃣.5 Testing page_size=200');
    const test3_5 = await makeAPICall('/customers', { page_size: 200 });
    
    // Test 4: Search with large page size (like user's example)
    console.log('\n4️⃣ Testing search with page_size=100');
    const test4 = await makeAPICall('/customers', { 
      search: 'Mevawala',
      page_size: 100 
    });
    
    // Test 5: Jobs endpoint with large page size
    console.log('\n5️⃣ Testing jobs endpoint with page_size=100');
    const test5 = await makeAPICall('/jobs', { page_size: 100 });
    
    console.log('\n🎯 Summary:');
    console.log('==========');
    console.log(`Test 1 (default): page_size = ${test1.data.page_size || test1.data.per_page || 'undefined'}`);
    console.log(`Test 2 (size=5): page_size = ${test2.data.page_size || test2.data.per_page || 'undefined'}`);
    console.log(`Test 3 (size=100): page_size = ${test3.data.page_size || test3.data.per_page || 'undefined'}`);
    console.log(`Test 3.5 (size=200): page_size = ${test3_5.data.page_size || test3_5.data.per_page || 'undefined'}`);
    console.log(`Test 4 (search+100): page_size = ${test4.data.page_size || test4.data.per_page || 'undefined'}`);
    console.log(`Test 5 (jobs+100): page_size = ${test5.data.page_size || test5.data.per_page || 'undefined'}`);
    
    if (test4.data.data && test4.data.data.length > 0) {
      console.log(`\n🔍 Found ${test4.data.data.length} customers matching "Mevawala"`);
      test4.data.data.forEach((customer, i) => {
        console.log(`   ${i+1}. ${customer.first_name} ${customer.last_name} (${customer.id})`);
      });
    }
    
  } catch (error) {
    console.log('\n❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testPagination();