/**
 * AirScript: Copy Job Attachments to Future Jobs
 * 
 * Copy this entire script into an Airtable Script block.
 * Create a button that runs this script.
 */

const API_BASE_URL = 'https://servativ.themomentcatchers.com';
const API_KEY = 'airscripts-secure-key-2025';

async function main() {
    output.text('🔧 Copy Job Attachments to Future Jobs');
    output.text('=====================================');
    
    // Get source job ID from user
    const sourceJobId = await input.textAsync('Enter the source job ID:');
    
    if (!sourceJobId?.trim()?.startsWith('job_')) {
        output.text('❌ Invalid job ID. Must start with "job_"');
        return;
    }
    
    output.text(`🚀 Processing job: ${sourceJobId.trim()}`);
    output.text('⏳ Please wait...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/prod/attachments/copy-to-future-jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ sourceJobId: sourceJobId.trim() })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API request failed');
        }
        
        // Show results
        output.text('🎉 Completed!');
        output.text('');
        output.text('📊 Summary:');
        output.text(`• Source attachments: ${result.sourceAttachments}`);
        output.text(`• Target jobs found: ${result.targetJobs}`);
        output.text(`• Jobs updated: ${result.jobsUpdated}`);
        output.text(`• Total attachments copied: ${result.totalAttachmentsCopied}`);
        
        if (result.message) {
            output.text(`• ${result.message}`);
        }
        
        if (result.results?.length > 0) {
            output.text('');
            output.text('📋 Updated jobs:');
            result.results.forEach((job, i) => {
                output.text(`  ${i+1}. ${job.jobId} - copied ${job.attachmentsCopied} attachments`);
            });
        }
        
    } catch (error) {
        output.text('❌ Error: ' + error.message);
    }
}

main();