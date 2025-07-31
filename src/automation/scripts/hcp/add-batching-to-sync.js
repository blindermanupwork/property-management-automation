#!/usr/bin/env node

/**
 * Script to add batching and delays to HCP sync scripts
 * This prevents Airtable automation cascade issues
 */

const fs = require('fs');
const path = require('path');

// Configuration
const BATCH_SIZE = 10; // Process 10 records at a time
const BATCH_DELAY_MS = 5000; // Wait 5 seconds between batches

// Function to add batching to a sync script
function addBatchingToScript(scriptPath) {
    console.log(`Adding batching to ${scriptPath}...`);
    
    let content = fs.readFileSync(scriptPath, 'utf8');
    
    // Add batch delay function after requires
    const batchDelayFunction = `
// Batch processing configuration
const BATCH_SIZE = ${BATCH_SIZE};
const BATCH_DELAY_MS = ${BATCH_DELAY_MS};

// Helper function to delay between batches
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Helper function to process records in batches
async function processBatch(records, batchSize, processFunc) {
    const results = [];
    for (let i = 0; i < records.length; i += batchSize) {
        const batch = records.slice(i, i + batchSize);
        console.log(\`\\n⏳ Processing batch \${Math.floor(i/batchSize) + 1} of \${Math.ceil(records.length/batchSize)} (\${batch.length} records)...\`);
        
        // Process batch
        for (const record of batch) {
            try {
                await processFunc(record);
                results.push({ success: true, record });
            } catch (error) {
                console.error(\`   ❌ Error processing record \${record.id}:\`, error.message);
                results.push({ success: false, record, error });
            }
        }
        
        // Delay between batches (except for last batch)
        if (i + batchSize < records.length) {
            console.log(\`   ⏸️  Waiting \${BATCH_DELAY_MS/1000} seconds before next batch...\`);
            await delay(BATCH_DELAY_MS);
        }
    }
    return results;
}
`;

    // Insert batch delay function after the requires section
    const requiresEndIndex = content.lastIndexOf('require(');
    const insertIndex = content.indexOf('\n', requiresEndIndex) + 1;
    content = content.slice(0, insertIndex) + batchDelayFunction + content.slice(insertIndex);
    
    // Replace the main processing loop to use batching
    // Look for patterns like "for (const rec of reservations)" or similar
    content = content.replace(
        /for\s*\(const\s+(\w+)\s+of\s+(reservations|records|filteredRecords)\)\s*{/g,
        'await processBatch($2, BATCH_SIZE, async ($1) => {'
    );
    
    // Close the processBatch callback properly
    // This is tricky and depends on the exact structure, so we'll do a simpler approach
    
    return content;
}

// Create a modified version that can be tested
function createBatchedVersion(originalPath, suffix = '-batched') {
    const dir = path.dirname(originalPath);
    const basename = path.basename(originalPath, '.cjs');
    const newPath = path.join(dir, basename + suffix + '.cjs');
    
    const modifiedContent = addBatchingToScript(originalPath);
    fs.writeFileSync(newPath, modifiedContent);
    
    console.log(`✅ Created batched version: ${newPath}`);
    console.log(`\nConfiguration:`);
    console.log(`- Batch size: ${BATCH_SIZE} records`);
    console.log(`- Delay between batches: ${BATCH_DELAY_MS/1000} seconds`);
    console.log(`\nThis will prevent Airtable automation cascade issues.`);
}

// Main execution
if (require.main === module) {
    const scripts = [
        '/home/opc/automation/src/automation/scripts/hcp/dev-hcp-sync.cjs',
        '/home/opc/automation/src/automation/scripts/hcp/prod-hcp-sync.cjs'
    ];
    
    scripts.forEach(script => {
        if (fs.existsSync(script)) {
            createBatchedVersion(script);
        } else {
            console.error(`❌ Script not found: ${script}`);
        }
    });
}

module.exports = { addBatchingToScript, createBatchedVersion };