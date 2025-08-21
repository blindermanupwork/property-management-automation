const fetch = require('node-fetch');
const FormData = require('form-data');
const { getHCPConfig } = require('../utils/config');

// HCP API helper with retry logic
async function hcpFetch(hcpConfig, path, method = 'GET', body = null) {
  const maxRetries = 3;
  let retry = 0;
  
  while (true) {
    const options = {
      method,
      headers: {
        'Accept': 'application/json',
        'Authorization': `Token ${hcpConfig.token}`
      }
    };

    // Add body for non-GET requests
    if (body && method !== 'GET') {
      if (body instanceof FormData) {
        // For FormData, let fetch set the content-type with boundary
        options.body = body;
        delete options.headers['Content-Type'];
      } else {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
      }
    }

    const response = await fetch(`https://api.housecallpro.com${path}`, options);
    const raw = await response.text();
    
    if (response.status === 429 && retry < maxRetries) {
      retry++;
      const reset = response.headers.get('RateLimit-Reset');
      const wait = reset
        ? Math.max(new Date(reset) - new Date(), 1000)
        : 1000 * (2 ** retry);
      console.log(`⏳ Rate limited, waiting ${wait}ms...`);
      await new Promise(resolve => setTimeout(resolve, wait));
      continue;
    }

    if (!response.ok) {
      throw new Error(`HCP API Error: ${response.status} - ${raw}`);
    }

    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  }
}

// Delay helper
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// Copy attachments from source job to target job
async function copyJobAttachments(hcpConfig, sourceJobId, targetJobId, sourceAttachments) {
  try {
    console.log(`  📎 Copying ${sourceAttachments.length} attachments to job ${targetJobId}...`);
    
    let copiedCount = 0;
    let errors = [];
    
    // Copy each attachment
    for (const attachment of sourceAttachments) {
      try {
        console.log(`    ⬇️ Downloading: ${attachment.file_name}`);
        
        // Download the file from S3 URL
        const downloadResponse = await fetch(attachment.url);
        if (!downloadResponse.ok) {
          throw new Error(`Failed to download: ${downloadResponse.status}`);
        }
        
        const fileBuffer = await downloadResponse.buffer();
        
        // Create form data for upload
        const formData = new FormData();
        formData.append('file', fileBuffer, {
          filename: attachment.file_name,
          contentType: attachment.file_type || 'application/octet-stream'
        });
        
        // Upload to target job
        console.log(`    ⬆️ Uploading: ${attachment.file_name}`);
        await hcpFetch(hcpConfig, `/jobs/${targetJobId}/attachments`, 'POST', formData);
        
        copiedCount++;
        console.log(`    ✅ Successfully copied: ${attachment.file_name}`);
        
        // Small delay between uploads to avoid rate limits
        await delay(500);
        
      } catch (error) {
        console.error(`    ❌ Failed to copy ${attachment.file_name}: ${error.message}`);
        errors.push(`${attachment.file_name}: ${error.message}`);
      }
    }
    
    return {
      success: true,
      attachmentsCopied: copiedCount,
      totalAttachments: sourceAttachments.length,
      errors: errors.length > 0 ? errors : undefined
    };
    
  } catch (error) {
    console.error('❌ Error in copyJobAttachments:', error.message);
    return {
      success: false,
      error: error.message,
      attachmentsCopied: 0
    };
  }
}

// Main handler function
async function copyAttachmentsToFutureJobs(req, res) {
  try {
    const { sourceJobId } = req.body;
    
    if (!sourceJobId) {
      return res.status(400).json({
        success: false,
        error: 'Source job ID is required'
      });
    }
    
    // Determine environment from request
    const environment = req.forceEnvironment || (req.path.includes('/dev/') ? 'development' : 'production');
    const hcpConfig = getHCPConfig(environment);
    
    console.log(`🚀 Starting attachment copying process for job ${sourceJobId} in ${environment} environment`);
    
    // Step 1: Get source job details with attachments
    console.log('📥 Step 1: Fetching source job details...');
    const sourceJob = await hcpFetch(hcpConfig, `/jobs/${sourceJobId}?expand[]=attachments`);
    
    console.log(`✅ Source job found: ${sourceJob.id}`);
    console.log(`   Customer: ${sourceJob.customer.first_name} ${sourceJob.customer.last_name} (${sourceJob.customer.id})`);
    console.log(`   Address: ${sourceJob.address.street} (${sourceJob.address.id})`);
    console.log(`   Created: ${sourceJob.created_at}`);
    console.log(`   Attachments: ${sourceJob.attachments ? sourceJob.attachments.length : 0}`);
    
    if (!sourceJob.attachments || sourceJob.attachments.length === 0) {
      return res.json({
        success: true,
        message: 'No attachments found in source job. Nothing to copy.',
        sourceJob: sourceJob.id,
        sourceAttachments: 0,
        targetJobs: 0,
        jobsUpdated: 0,
        totalAttachmentsCopied: 0
      });
    }
    
    const sourceCustomerId = sourceJob.customer.id;
    const sourceAddressId = sourceJob.address.id;
    const sourceCreatedAt = new Date(sourceJob.created_at);
    
    // Step 2: Get all jobs for this customer
    console.log('🔍 Step 2: Finding all jobs for this customer...');
    const allJobs = await hcpFetch(hcpConfig, `/jobs/?expand[]=attachments&customer_id=${sourceCustomerId}&page_size=50`);
    
    console.log(`✅ Found ${allJobs.total_items} total jobs for customer`);
    
    // Step 3: Filter for future jobs with same address
    console.log('🎯 Step 3: Filtering for target jobs...');
    const targetJobs = allJobs.jobs.filter(job => {
      // Skip the source job itself
      if (job.id === sourceJobId) return false;
      
      // Must have same address
      if (job.address.id !== sourceAddressId) return false;
      
      // Must be created after source job
      const jobCreatedAt = new Date(job.created_at);
      if (jobCreatedAt <= sourceCreatedAt) return false;
      
      return true;
    });
    
    console.log(`✅ Found ${targetJobs.length} target jobs to update`);
    
    if (targetJobs.length === 0) {
      return res.json({
        success: true,
        message: 'No future jobs found with matching customer and address.',
        sourceJob: sourceJob.id,
        sourceAttachments: sourceJob.attachments.length,
        targetJobs: 0,
        jobsUpdated: 0,
        totalAttachmentsCopied: 0
      });
    }
    
    // Step 4: Copy attachments to each target job
    console.log('📤 Step 4: Copying attachments to target jobs...');
    
    let totalCopied = 0;
    let jobsUpdated = 0;
    const results = [];
    
    for (const targetJob of targetJobs) {
      console.log(`\n🎯 Processing job: ${targetJob.id}`);
      console.log(`   Description: ${targetJob.description}`);
      console.log(`   Current attachments: ${targetJob.attachments ? targetJob.attachments.length : 0}`);
      
      const result = await copyJobAttachments(hcpConfig, sourceJobId, targetJob.id, sourceJob.attachments);
      
      results.push({
        jobId: targetJob.id,
        description: targetJob.description,
        attachmentsCopied: result.attachmentsCopied,
        totalAttachments: result.totalAttachments,
        success: result.success,
        errors: result.errors
      });
      
      if (result.success && result.attachmentsCopied > 0) {
        totalCopied += result.attachmentsCopied;
        jobsUpdated++;
        console.log(`   ✅ Successfully copied ${result.attachmentsCopied}/${result.totalAttachments} attachments`);
        
        if (result.errors) {
          console.log(`   ⚠️ Errors: ${result.errors.length}`);
          result.errors.forEach(error => console.log(`      - ${error}`));
        }
      } else if (result.success) {
        console.log(`   ℹ️ No attachments copied (already exist or none to copy)`);
      } else {
        console.log(`   ❌ Failed to copy attachments: ${result.error}`);
      }
      
      // Delay between jobs to avoid rate limits
      await delay(1000);
    }
    
    // Summary
    console.log('\n🎉 Attachment copying completed!');
    console.log(`📊 Summary:`);
    console.log(`   • Source job: ${sourceJobId}`);
    console.log(`   • Source attachments: ${sourceJob.attachments.length}`);
    console.log(`   • Target jobs found: ${targetJobs.length}`);
    console.log(`   • Jobs updated: ${jobsUpdated}`);
    console.log(`   • Total attachments copied: ${totalCopied}`);
    
    res.json({
      success: true,
      message: 'Attachment copying completed successfully',
      sourceJob: sourceJob.id,
      sourceAttachments: sourceJob.attachments.length,
      targetJobs: targetJobs.length,
      jobsUpdated: jobsUpdated,
      totalAttachmentsCopied: totalCopied,
      results: results,
      environment: environment
    });
    
  } catch (error) {
    console.error('❌ Error in copyAttachmentsToFutureJobs:', error.message);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

module.exports = {
  copyAttachmentsToFutureJobs
};