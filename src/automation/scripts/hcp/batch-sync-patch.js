#!/usr/bin/env node

/**
 * Patch to add batching to HCP sync scripts
 * Prevents Airtable automation cascade by limiting updates per batch
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BATCH_SIZE = 10; // Process 10 records at a time
const BATCH_DELAY_MS = 3000; // Wait 3 seconds between batches

function patchSyncScript(scriptPath) {
    console.log(`Patching ${scriptPath}...`);
    
    let content = fs.readFileSync(scriptPath, 'utf8');
    
    // Add delay function and batch configuration after requires
    const delayCode = `
// Batch processing configuration to prevent Airtable automation cascade
const UPDATE_BATCH_SIZE = ${BATCH_SIZE};
const UPDATE_BATCH_DELAY_MS = ${BATCH_DELAY_MS};
let updateCounter = 0;

// Helper function to delay between batches
async function delayIfNeeded() {
    updateCounter++;
    if (updateCounter % UPDATE_BATCH_SIZE === 0) {
        console.log(\`   ⏸️  Processed \${updateCounter} records. Waiting \${UPDATE_BATCH_DELAY_MS/1000}s to prevent automation cascade...\`);
        await new Promise(resolve => setTimeout(resolve, UPDATE_BATCH_DELAY_MS));
    }
}
`;

    // Find where to insert (after all requires)
    const lastRequireIndex = content.lastIndexOf('require(');
    const insertPoint = content.indexOf('\n', content.indexOf(';', lastRequireIndex)) + 1;
    
    // Insert delay code
    content = content.slice(0, insertPoint) + delayCode + content.slice(insertPoint);
    
    // Add delay after each Airtable update
    // Look for patterns like "await base('Reservations').update" and add delay after
    content = content.replace(
        /(await base\('Reservations'\)\.update\([^)]+\);)/g,
        '$1\n        await delayIfNeeded();'
    );
    
    // Also add a summary at the end
    content = content.replace(
        /(console\.log\(`✅ Sync verification complete.*`\);)/g,
        `$1\n    console.log(\`📊 Total updates: \${updateCounter} (in batches of \${UPDATE_BATCH_SIZE})\`);`
    );
    
    return content;
}

// Create patched versions
function createPatchedVersion(originalPath) {
    const dir = path.dirname(originalPath);
    const basename = path.basename(originalPath, '.cjs');
    const patchedPath = path.join(dir, basename + '-batched.cjs');
    
    try {
        const patchedContent = patchSyncScript(originalPath);
        fs.writeFileSync(patchedPath, patchedContent);
        console.log(`✅ Created patched version: ${patchedPath}`);
        
        // Make it executable
        fs.chmodSync(patchedPath, '755');
        
        return patchedPath;
    } catch (error) {
        console.error(`❌ Failed to patch ${originalPath}:`, error.message);
        return null;
    }
}

// Apply patches to both scripts
const scripts = [
    '/home/opc/automation/src/automation/scripts/hcp/dev-hcp-sync.cjs',
    '/home/opc/automation/src/automation/scripts/hcp/prod-hcp-sync.cjs'
];

console.log('🔧 Patching HCP sync scripts to add batching...\n');
console.log(`Configuration:`);
console.log(`- Batch size: ${BATCH_SIZE} records`);
console.log(`- Delay between batches: ${BATCH_DELAY_MS/1000} seconds`);
console.log(`- This prevents Airtable automation cascade issues\n`);

scripts.forEach(script => {
    if (fs.existsSync(script)) {
        createPatchedVersion(script);
    } else {
        console.error(`❌ Script not found: ${script}`);
    }
});

console.log('\n📝 To use the patched versions:');
console.log('1. Test with: node dev-hcp-sync-batched.cjs --sync-only');
console.log('2. Update run_automation.py to use the -batched versions');
console.log('3. Monitor for cascade issues during next cron run');