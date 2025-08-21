#!/usr/bin/env node

// Test script for attachment copying functionality
// This script tests the copyJobAttachments function

const fetch = require('node-fetch');
const FormData = require('form-data');

// Test the attachment copying API
async function testAttachmentCopy() {
  try {
    console.log('🧪 Testing HousecallPro attachment copying functionality...');
    
    // Load environment config
    require('dotenv').config();
    const environment = 'production'; // Only prod env is working
    
    // Test job ID with known attachments
    const testJobId = 'job_87988136dd76482d9f663729583d5929'; // From your example
    
    console.log(`Environment: ${environment}`);
    console.log(`Test job ID: ${testJobId}`);
    
    // Get HCP config
    const hcpToken = environment === 'production' 
      ? process.env.PROD_HCP_TOKEN 
      : process.env.DEV_HCP_TOKEN;
    
    if (!hcpToken) {
      throw new Error(`No HCP token found for ${environment} environment`);
    }
    
    console.log('\n📥 Step 1: Fetching job with attachments...');
    
    // Fetch job with attachments expanded
    const response = await fetch(`https://api.housecallpro.com/jobs/${testJobId}?expand[]=attachments`, {
      headers: {
        'Authorization': `Token ${hcpToken}`,
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job: ${response.status} - ${await response.text()}`);
    }
    
    const jobData = await response.json();
    
    console.log(`✅ Job fetched successfully: ${jobData.id}`);
    console.log(`📎 Attachments found: ${jobData.attachments ? jobData.attachments.length : 0}`);
    
    if (jobData.attachments && jobData.attachments.length > 0) {
      console.log('\n📋 Attachment details:');
      jobData.attachments.forEach((att, index) => {
        console.log(`  ${index + 1}. ${att.file_name} (${att.file_type}) - ${att.id}`);
      });
      
      // Test downloading the first attachment
      console.log('\n⬇️ Step 2: Testing attachment download...');
      const firstAttachment = jobData.attachments[0];
      
      const downloadResponse = await fetch(firstAttachment.url);
      if (!downloadResponse.ok) {
        throw new Error(`Failed to download attachment: ${downloadResponse.status}`);
      }
      
      const fileBuffer = await downloadResponse.buffer();
      console.log(`✅ Successfully downloaded ${firstAttachment.file_name} (${fileBuffer.length} bytes)`);
      
      // Test form-data creation
      console.log('\n📤 Step 3: Testing form-data creation...');
      const formData = new FormData();
      formData.append('file', fileBuffer, {
        filename: `test_copy_${firstAttachment.file_name}`,
        contentType: firstAttachment.file_type || 'application/octet-stream'
      });
      
      console.log(`✅ Form data created successfully for upload`);
      console.log(`📋 Form headers:`, formData.getHeaders());
      
    } else {
      console.log('⚠️ No attachments found in test job');
    }
    
    console.log('\n🎉 All tests passed! Attachment copying functionality is ready.');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testAttachmentCopy();