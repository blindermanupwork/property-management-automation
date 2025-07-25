#!/usr/bin/env node
/**
 * Test Script - Run Automation via API
 * Tests the new Run Now functionality
 */

require('dotenv').config();
const axios = require('axios');

const API_URL = 'http://localhost:3002';
const API_KEY = process.env.API_KEY;

async function testRunAutomation(env, automationName) {
  try {
    console.log(`\n🚀 Testing Run Now for ${automationName} in ${env} environment...`);
    
    const response = await axios.post(
      `${API_URL}/api/${env}/automation/run/${encodeURIComponent(automationName)}`,
      {},
      {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('✅ Success:', response.data);
    
    if (response.data.details) {
      console.log('\n📋 Output Preview:');
      console.log(response.data.details);
    }
    
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

async function testGetStatus(env, automationName) {
  try {
    console.log(`\n📊 Getting status for ${automationName} in ${env} environment...`);
    
    const response = await axios.get(
      `${API_URL}/api/${env}/automation/status/${encodeURIComponent(automationName)}`,
      {
        headers: {
          'X-API-Key': API_KEY
        }
      }
    );
    
    console.log('✅ Status:', response.data);
    
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

async function main() {
  // Test CSV Files automation
  await testGetStatus('prod', 'CSV Files');
  await testRunAutomation('prod', 'CSV Files');
  
  // Wait a bit for processing
  console.log('\n⏳ Waiting 10 seconds for processing...');
  await new Promise(resolve => setTimeout(resolve, 10000));
  
  // Check status again
  await testGetStatus('prod', 'CSV Files');
  
  // Test ICS Calendar automation
  console.log('\n' + '='.repeat(50) + '\n');
  await testGetStatus('prod', 'ICS Calendar');
  await testRunAutomation('prod', 'ICS Calendar');
}

main().catch(console.error);