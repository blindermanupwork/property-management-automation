#!/usr/bin/env node

/**
 * Debug script to test the exact same parameters the MCP is using
 */

const https = require('https');
const url = require('url');

const API_KEY = 'c7f3c26c0c4347c080d3fb4dda1bd193';
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
        'Authorization': `Token ${API_KEY}`,  // Note: using Token instead of Bearer
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'HCP-MCP-dev/1.0.0'
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
          
          // Extract pagination info
          if (jsonData.page !== undefined) {
            console.log(`📄 Pagination info:`);
            console.log(`   - Page: ${jsonData.page}`);
            console.log(`   - Per page: ${jsonData.per_page}`);
            console.log(`   - Page size: ${jsonData.page_size}`);
            console.log(`   - Total: ${jsonData.total}`);
            console.log(`   - Total pages: ${jsonData.total_pages}`);
            console.log(`   - Total items: ${jsonData.total_items}`);
            console.log(`   - Data count: ${jsonData.customers ? jsonData.customers.length : jsonData.data ? jsonData.data.length : 'N/A'}`);
            
            if (jsonData.customers) {
              const mevawalaCustomers = jsonData.customers.filter(c => 
                (c.first_name && c.first_name.toLowerCase().includes('mevawala')) ||
                (c.last_name && c.last_name.toLowerCase().includes('mevawala'))
              );
              console.log(`🔍 Found ${mevawalaCustomers.length} Mevawala customers in response`);
              mevawalaCustomers.forEach((customer, i) => {
                console.log(`   ${i+1}. ${customer.first_name} ${customer.last_name} (${customer.id})`);
              });
            }
          }
          
          resolve(jsonData);
        } catch (error) {
          console.log(`❌ Failed to parse JSON response:`, error.message);
          console.log(`📄 Raw response:`, data.substring(0, 500));
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

async function testMCPLikeCall() {
  console.log('🧪 Testing MCP-like API Call');
  console.log('============================');
  
  try {
    // Test the exact same call that the MCP would make:
    // validatePaginationParams converts per_page: 100 to page_size: 100
    // hcpService adds search parameter
    console.log('\n1️⃣ Testing MCP-equivalent call (search=Mevawala, page_size=100)');
    const result = await makeAPICall('/customers', { 
      search: 'Mevawala',
      page_size: 100
    });
    
    console.log('\n2️⃣ Testing without search (page_size=100)');
    const result2 = await makeAPICall('/customers', { 
      page_size: 100
    });
    
    console.log('\n3️⃣ Testing with page_size=5 to verify parameter works');
    const result3 = await makeAPICall('/customers', { 
      search: 'Mevawala',
      page_size: 5
    });
    
  } catch (error) {
    console.log('\n❌ Test failed:', error.message);
    process.exit(1);
  }
}

testMCPLikeCall();