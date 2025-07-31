#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Fix the batched sync scripts
const scripts = [
    'dev-hcp-sync-batched.cjs',
    'prod-hcp-sync-batched.cjs'
];

scripts.forEach(scriptName => {
    const scriptPath = path.join(__dirname, scriptName);
    
    if (!fs.existsSync(scriptPath)) {
        console.error(`Script not found: ${scriptPath}`);
        return;
    }
    
    console.log(`Fixing ${scriptName}...`);
    
    let content = fs.readFileSync(scriptPath, 'utf8');
    
    // Find the main async function and move the delay function inside it
    // Look for "async function run()" or similar
    const mainFunctionMatch = content.match(/(async function \w+\([^)]*\)\s*{)/);
    
    if (mainFunctionMatch) {
        const insertPoint = mainFunctionMatch.index + mainFunctionMatch[0].length;
        
        // Add the delay function inside the main function
        const delayFunction = `
  // Batch processing configuration to prevent Airtable automation cascade
  const UPDATE_BATCH_SIZE = 10;
  const UPDATE_BATCH_DELAY_MS = 3000;
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
        
        // Remove the old declaration at the top level
        content = content.replace(/\/\/ Batch processing configuration[\s\S]*?}\n/m, '');
        
        // Insert inside the main function
        content = content.slice(0, insertPoint) + delayFunction + content.slice(insertPoint);
        
        // Save the fixed version
        fs.writeFileSync(scriptPath, content);
        console.log(`✅ Fixed ${scriptName}`);
    } else {
        console.error(`Could not find main function in ${scriptName}`);
    }
});

console.log('\nDone! The batched scripts should now work correctly.');