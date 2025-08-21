/**
 * AirScript: Copy Job Attachments to Future Jobs
 * 
 * This script copies attachments from a source HCP job to all future jobs
 * that match the same customer and address.
 * 
 * Usage in Airtable:
 * 1. Add this script to a Script block
 * 2. Create a button in your interface
 * 3. Enter the source job ID when prompted
 * 4. The script will copy attachments to all qualifying future jobs
 */

const API_BASE_URL = 'https://servativ.themomentcatchers.com';
const API_KEY = 'airscripts-secure-key-2025';

// Use production endpoint (since dev environment is no longer working)
const ENVIRONMENT = 'prod';

async function copyAttachmentsToFutureJobs() {
    // Get source job ID from user input
    const sourceJobId = await input.textAsync('Enter the source job ID (e.g., job_a1857505201f45d78616250a3e483ffa):');
    
    if (!sourceJobId || !sourceJobId.trim()) {
        output.text('❌ No job ID provided. Script cancelled.');
        return;
    }
    
    const trimmedJobId = sourceJobId.trim();
    
    // Validate job ID format
    if (!trimmedJobId.startsWith('job_')) {
        output.text('❌ Invalid job ID format. Job IDs should start with "job_"');
        return;
    }
    
    output.text(`🚀 Starting attachment copying process for job: ${trimmedJobId}`);
    output.text('⏳ This may take a few moments...');
    
    try {
        // Call the API endpoint
        const response = await fetch(`${API_BASE_URL}/api/${ENVIRONMENT}/attachments/copy-to-future-jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({
                sourceJobId: trimmedJobId
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`API Error: ${response.status} - ${errorData.error || 'Unknown error'}`);
        }
        
        const result = await response.json();
        
        // Display results
        output.text('🎉 Attachment copying completed!');
        output.text('');
        output.text('📊 Summary:');
        output.text(`• Source job: ${result.sourceJob}`);
        output.text(`• Source attachments: ${result.sourceAttachments}`);
        output.text(`• Target jobs found: ${result.targetJobs}`);
        output.text(`• Jobs updated: ${result.jobsUpdated}`);
        output.text(`• Total attachments copied: ${result.totalAttachmentsCopied}`);
        output.text(`• Environment: ${result.environment}`);
        
        if (result.message) {
            output.text('');
            output.text(`ℹ️ ${result.message}`);
        }
        
        if (result.results && result.results.length > 0) {
            output.text('');
            output.text('📋 Detailed results:');
            
            result.results.forEach((jobResult, index) => {
                const status = jobResult.success ? '✅' : '❌';
                output.text(`  ${index + 1}. ${status} ${jobResult.jobId}`);
                output.text(`     Description: ${jobResult.description}`);
                output.text(`     Attachments copied: ${jobResult.attachmentsCopied}/${jobResult.totalAttachments}`);
                
                if (jobResult.errors && jobResult.errors.length > 0) {
                    output.text(`     Errors: ${jobResult.errors.length}`);
                    jobResult.errors.forEach(error => {
                        output.text(`       - ${error}`);
                    });
                }
            });
        }
        
    } catch (error) {
        output.text('❌ Error occurred:');
        output.text(error.message);
        output.text('');
        output.text('💡 Troubleshooting tips:');
        output.text('• Verify the job ID is correct and exists in HCP');
        output.text('• Check that the API service is running');
        output.text('• Ensure the API key is correctly configured');
    }
}

// Main execution
output.text('🔧 Copy Job Attachments to Future Jobs');
output.text('=====================================');
output.text('');
output.text('This script will copy all attachments from a source job to future jobs');
output.text('that have the same customer and address.');
output.text('');

copyAttachmentsToFutureJobs();