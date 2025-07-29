const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const router = express.Router();

// Helper function to capture detailed output from automation scripts
async function runAutomationScript(automationName, env) {
    return new Promise((resolve, reject) => {
        const projectRoot = path.join(__dirname, '../../../../..');
        const scriptPath = path.join(projectRoot, 'src/run_automation_' + env + '.py');
        const args = ['--run', automationName];
        
        console.log(`Running automation: ${automationName} in ${env} environment`);
        console.log(`Script path: ${scriptPath}`);
        console.log(`Args: ${args}`);
        
        let output = '';
        let errorOutput = '';
        
        // Set environment variable
        const processEnv = { ...process.env, ENVIRONMENT: env === 'prod' ? 'production' : 'development' };
        
        const pythonProcess = spawn('python3', [scriptPath, ...args], {
            cwd: projectRoot,
            env: processEnv
        });
        
        pythonProcess.stdout.on('data', (data) => {
            const text = data.toString();
            output += text;
            console.log(`[${automationName}] stdout:`, text);
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const text = data.toString();
            errorOutput += text;
            console.error(`[${automationName}] stderr:`, text);
        });
        
        pythonProcess.on('close', (code) => {
            console.log(`[${automationName}] Process exited with code ${code}`);
            
            if (code === 0) {
                // Extract sync details from output
                let syncDetails = extractSyncDetails(output);
                resolve({
                    success: true,
                    message: syncDetails,
                    output: output,
                    code: code
                });
            } else {
                // Extract error details
                let errorDetails = extractErrorDetails(output + errorOutput);
                resolve({
                    success: false,
                    message: errorDetails,
                    output: output,
                    error: errorOutput,
                    code: code
                });
            }
        });
        
        pythonProcess.on('error', (err) => {
            console.error(`[${automationName}] Failed to start process:`, err);
            reject({
                success: false,
                message: `Failed to start automation: ${err.message}`,
                error: err.message
            });
        });
    });
}

// Extract meaningful sync details from output
function extractSyncDetails(output) {
    const lines = output.split('\n');
    
    // Try to detect the automation type from output and extract relevant details
    
    // CSV Files automation
    if (output.includes('CSV processing') || output.includes('CSV files to process') || output.includes('CSV Processor') || output.includes("📊 Processing iTrip and Evolve CSV files")) {
        // First look for the status message from controller  
        // Pattern: "📝 Updated status for 'CSV Files': ✅ ✅ No valid reservations found in CSV files"
        const statusMatch = output.match(/📝 Updated status for 'CSV Files': ✅ (.+)/);
        if (statusMatch) {
            const status = statusMatch[1].trim();
            // Remove any double ✅ that might have been added
            return status.replace(/^✅\s*/, '');
        }
        
        // Look for the specific CSV Sync complete format:
        // "Sync complete * created 0 * updated 2 * unchanged 3 * removed 0"
        const csvSyncCompleteMatch = output.match(/Sync complete \* created (\d+) \* updated (\d+) \* unchanged (\d+) \* removed (\d+)/);
        if (csvSyncCompleteMatch) {
            const created = parseInt(csvSyncCompleteMatch[1]);
            const updated = parseInt(csvSyncCompleteMatch[2]);
            const unchanged = parseInt(csvSyncCompleteMatch[3]);
            const removed = parseInt(csvSyncCompleteMatch[4]);
            
            // Count files from earlier in the output if possible
            let fileCount = 0;
            const movedMatch = output.match(/Moved (\d+) of (\d+) processed files/);
            if (movedMatch) {
                fileCount = parseInt(movedMatch[2]);
            }
            
            if (fileCount > 0) {
                return `✅ ${fileCount} files — created ${created}, updated ${updated}, removed ${removed}`;
            } else {
                return `✅ CSV sync — created ${created}, updated ${updated}, unchanged ${unchanged}, removed ${removed}`;
            }
        }
        
        // Pattern 1: "Processing complete: X files — Total new: Y, Total modified: Z"
        const completeMatch = output.match(/Processing complete.*?(\d+) files.*?Total new: (\d+).*?Total modified: (\d+)/);
        if (completeMatch) {
            return `✅ ${completeMatch[1]} files — new ${completeMatch[2]}, modified ${completeMatch[3]}`;
        }
        
        // Pattern 2: Look for summary lines
        for (let i = lines.length - 1; i >= 0; i--) {
            if (lines[i].includes('Sync complete') || lines[i].includes('📊 CSV Processing Summary')) {
                // Look for the stats in nearby lines
                for (let j = i; j < Math.min(i + 10, lines.length); j++) {
                    if (lines[j].includes('Files processed:')) {
                        const statsMatch = lines[j].match(/Files processed: (\d+).*?New: (\d+).*?Modified: (\d+)/);
                        if (statsMatch) {
                            return `✅ ${statsMatch[1]} files — new ${statsMatch[2]}, modified ${statsMatch[3]}`;
                        }
                    }
                }
            }
            
            // Pattern 3: Total counts
            if (lines[i].includes('Total new:') || lines[i].includes('Total modified:')) {
                let stats = {files: 0, new: 0, modified: 0};
                for (let j = Math.max(0, i - 10); j <= Math.min(i + 10, lines.length - 1); j++) {
                    if (lines[j].includes('Total new:')) {
                        const match = lines[j].match(/Total new:\s*(\d+)/);
                        if (match) stats.new = parseInt(match[1]);
                    }
                    if (lines[j].includes('Total modified:')) {
                        const match = lines[j].match(/Total modified:\s*(\d+)/);
                        if (match) stats.modified = parseInt(match[1]);
                    }
                    if (lines[j].includes('CSV files to process:')) {
                        const match = lines[j].match(/CSV files to process:\s*(\d+)/);
                        if (match) stats.files = parseInt(match[1]);
                    }
                }
                if (stats.new > 0 || stats.modified > 0) {
                    return `✅ ${stats.files || 1} files — new ${stats.new}, modified ${stats.modified}`;
                }
            }
        }
        
        // Pattern 4: No files to process
        if (output.includes('No CSV files to process')) {
            return '✅ No CSV files to process';
        }
        
        // Pattern 5: No valid reservations
        if (output.includes('No valid reservations found')) {
            return '✅ No valid reservations found in CSV files';
        }
        
        // Fallback
        const csvMatch = output.match(/(\d+) files.*?(\d+) reservations.*?(\d+) blocks/);
        if (csvMatch) {
            return `✅ ${csvMatch[1]} files — ${csvMatch[2]} reservations, ${csvMatch[3]} blocks`;
        }
    }
    
    // ICS Calendar automation
    if (output.includes('ICS sync') || output.includes('ICS feeds') || output.includes('ICS Calendar')) {
            // Look for the specific ICS Sync complete format: 
            // "ICS Sync complete — new 0 (0 res, 0 block) — modified 1 (1 res, 0 block) — unchanged 574 — removed 0 (0 res, 0 block)"
            const icsSyncCompleteMatch = output.match(/ICS Sync complete — new (\d+) \((\d+) res, (\d+) block\) — modified (\d+) \((\d+) res, (\d+) block\) — unchanged (\d+) — removed (\d+) \((\d+) res, (\d+) block\)/);
            if (icsSyncCompleteMatch) {
                const totalNew = parseInt(icsSyncCompleteMatch[1]);
                const totalModified = parseInt(icsSyncCompleteMatch[4]);
                const totalUnchanged = parseInt(icsSyncCompleteMatch[7]);
                const totalRemoved = parseInt(icsSyncCompleteMatch[8]);
                const totalFeeds = totalNew + totalModified + totalUnchanged + totalRemoved;
                
                // Format like "✅ 334 feeds — new 0 (0 res, 0 block) — modified 1 (1 res, 0 block) — removed 0"
                return `✅ ${totalFeeds} feeds — new ${icsSyncCompleteMatch[1]} (${icsSyncCompleteMatch[2]} res, ${icsSyncCompleteMatch[3]} block) — modified ${icsSyncCompleteMatch[4]} (${icsSyncCompleteMatch[5]} res, ${icsSyncCompleteMatch[6]} block) — removed ${icsSyncCompleteMatch[8]}`;
            }
            
            // Look for ICS sync summary patterns
            // Pattern 1: "📊 ICS Sync Summary"
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('📊 ICS Sync Summary') || lines[i].includes('ICS sync complete')) {
                    // Look for stats in nearby lines
                    for (let j = i; j < Math.min(i + 10, lines.length); j++) {
                        if (lines[j].includes('Feeds processed:')) {
                            const statsMatch = lines[j].match(/Feeds processed: (\d+).*?New: (\d+).*?Modified: (\d+).*?Removed: (\d+)/);
                            if (statsMatch) {
                                return `✅ ${statsMatch[1]} feeds — new ${statsMatch[2]}, modified ${statsMatch[3]}, removed ${statsMatch[4]}`;
                            }
                        }
                    }
                }
                
                // Pattern 2: Look for individual stats
                if (lines[i].includes('Total stats:')) {
                    const totalMatch = lines[i].match(/new:(\d+).*?modified:(\d+).*?removed:(\d+)/);
                    if (totalMatch) {
                        // Look for feed count
                        let feedCount = 246; // Default for prod
                        for (let j = Math.max(0, i - 20); j < i; j++) {
                            const feedMatch = lines[j].match(/Processing (\d+) ICS feeds/);
                            if (feedMatch) {
                                feedCount = feedMatch[1];
                                break;
                            }
                        }
                        return `✅ ${feedCount} feeds — new ${totalMatch[1]}, modified ${totalMatch[2]}, removed ${totalMatch[3]}`;
                    }
                }
            }
            
            // Pattern 3: Standard format
            const icsMatch = output.match(/(\d+) feeds.*?new (\d+).*?modified (\d+).*?removed (\d+)/);
            if (icsMatch) {
                return `✅ ${icsMatch[0]}`;
            }
            
            // Pattern 4: Alternative format
            const feedsMatch = output.match(/Processing (\d+) ICS feeds/);
            const statsMatch = output.match(/new:(\d+).*?modified:(\d+).*?removed:(\d+)/);
            if (feedsMatch && statsMatch) {
                return `✅ ${feedsMatch[1]} feeds — new ${statsMatch[1]}, modified ${statsMatch[2]}, removed ${statsMatch[3]}`;
            }
            
            // Pattern 5: No changes
            if (output.includes('No changes detected')) {
                return '✅ No changes detected';
            }
    }
    
    // Evolve automation
    if (output.includes('Evolve') || output.includes('evolve_scraper')) {
        const evolveMatch = output.match(/(\d+) files.*?(\d+) reservations.*?(\d+) blocks/);
        if (evolveMatch) {
            return `✅ ${evolveMatch[1]} files — ${evolveMatch[2]} reservations, ${evolveMatch[3]} blocks`;
        }
    }
    
    // Sync Service Jobs automation
    if (output.includes('job sync') || output.includes('Service Jobs')) {
        const jobMatch = output.match(/verified (\d+)\/(\d+) jobs.*?created (\d+)/);
        if (jobMatch) {
            return `✅ verified ${jobMatch[1]}/${jobMatch[2]} jobs — created ${jobMatch[3]} new`;
        }
    }
    
    // Update Service Lines automation
    if (output.includes('service lines') || output.includes('Service Lines')) {
        const lineMatch = output.match(/updated (\d+)\/(\d+) service lines/);
        if (lineMatch) {
            return `✅ updated ${lineMatch[1]}/${lineMatch[2]} service lines`;
        }
    }
    
    // Job Reconciliation automation
    if (output.includes('Reconciliation') || output.includes('reconciliation')) {
        const reconMatch = output.match(/Reconciliation executed: (\d+)\/(\d+) jobs matched/);
        if (reconMatch) {
            return `✅ Reconciliation executed: ${reconMatch[1]}/${reconMatch[2]} jobs matched`;
        }
    }
    
    // Generic success if we can't find specific details
    if (output.includes('completed successfully')) {
        return `✅ Automation completed successfully`;
    }
    
    return `✅ Automation completed`;
}

// Extract error details from output
function extractErrorDetails(output) {
    // Check for specific error patterns
    if (output.includes('No CSV files to process')) {
        return '❌ No CSV files found in process directory';
    }
    if (output.includes('Unknown field name')) {
        const fieldMatch = output.match(/Unknown field name[: ]+["']([^"']+)["']/);
        if (fieldMatch) {
            return `❌ Airtable field '${fieldMatch[1]}' does not exist`;
        }
        return '❌ Airtable field configuration error';
    }
    if (output.includes('Missing property links')) {
        const countMatch = output.match(/(\d+) reservation/);
        if (countMatch) {
            return `❌ ${countMatch[1]} reservations have properties not found in Airtable`;
        }
        return '❌ Properties not found in Airtable';
    }
    if (output.includes('ConnectionError')) {
        return '❌ Network connection failed';
    }
    if (output.includes('PermissionError')) {
        return '❌ Permission denied accessing files';
    }
    if (output.includes('HTTPError')) {
        return '❌ HTTP request failed';
    }
    
    // Check for concurrent run issues
    if (output.includes('Resource temporarily unavailable') || output.includes('EAGAIN')) {
        return '❌ Resource conflict - another automation may be running';
    }
    if (output.includes('Cannot acquire lock') || output.includes('locked')) {
        return '❌ Database locked - another process is running';
    }
    
    // Python traceback
    if (output.includes('Traceback')) {
        const lines = output.split('\n');
        for (let i = lines.length - 1; i >= 0; i--) {
            if (lines[i].trim() && !lines[i].startsWith(' ')) {
                return `❌ ${lines[i].trim()}`;
            }
        }
    }
    
    // If no output at all
    if (!output || output.trim().length === 0) {
        return '❌ Automation failed to start or produce output';
    }
    
    return `❌ Automation failed - check logs for details`;
}

// Run specific automation
router.post('/run/:automation', async (req, res) => {
    const { automation } = req.params;
    // Use forceEnvironment from the middleware
    const env = req.forceEnvironment === 'development' ? 'dev' : 'prod';
    
    // Enhanced logging to find trigger source
    const triggerInfo = {
        timestamp: new Date().toISOString(),
        automation: automation,
        environment: env,
        method: req.method,
        path: req.path,
        fullUrl: req.originalUrl,
        headers: req.headers,
        ip: req.ip,
        userAgent: req.headers['user-agent'],
        referer: req.headers['referer'],
        origin: req.headers['origin'],
        apiKey: req.headers['x-api-key'] ? 'present' : 'missing',
        body: req.body
    };
    
    console.log('=== AUTOMATION TRIGGER DETECTED ===');
    console.log(JSON.stringify(triggerInfo, null, 2));
    console.log('===================================');
    
    // Log to a special file for trigger analysis
    const fs = require('fs');
    const triggerLogPath = '/home/opc/automation/src/automation/logs/automation_triggers.json';
    fs.appendFileSync(triggerLogPath, JSON.stringify(triggerInfo) + '\n');
    
    console.log(`Received request to run automation: ${automation} in ${env} environment`);
    
    try {
        // First, find the automation record by name
        const Airtable = require('airtable');
        const apiKeyVar = env === 'dev' ? 'DEV_AIRTABLE_API_KEY' : 'PROD_AIRTABLE_API_KEY';
        const baseIdVar = env === 'dev' ? 'DEV_AIRTABLE_BASE_ID' : 'PROD_AIRTABLE_BASE_ID';
        
        const base = new Airtable({ apiKey: process.env[apiKeyVar] })
            .base(process.env[baseIdVar]);
        
        const records = await base('Automation')
            .select({
                filterByFormula: `{Name} = '${automation}'`,
                maxRecords: 1
            })
            .firstPage();
        
        if (records.length === 0) {
            return res.status(404).json({
                success: false,
                message: `Automation '${automation}' not found`
            });
        }
        
        const automationRecordId = records[0].id;
        const automationName = records[0].fields.Name;
        console.log(`Found automation: ${automationName} (${automationRecordId})`);
        
        const result = await runAutomationScript(automationName, env);
        
        // Update the record with results
        try {
            console.log(`Updating Airtable record ${automationRecordId} with results:`, {
                success: result.success,
                message: result.message
            });
            
            if (result.success || result.message) {
                await base('Automation').update(automationRecordId, {
                    'Last Ran Time': new Date().toISOString(),
                    'Sync Details': result.message
                });
                console.log(`Successfully updated Airtable for ${automationName}`);
            }
        } catch (updateError) {
            console.error(`Failed to update Airtable for ${automationName}:`, updateError);
            // Don't fail the whole request, just log the error
            result.airtableUpdateError = updateError.message;
        }
        
        res.json({
            success: result.success,
            message: result.message,
            details: result.output ? result.output.substring(0, 1000) : undefined,
            error: result.error ? result.error.substring(0, 500) : undefined
        });
        
    } catch (error) {
        console.error('Error running automation:', error);
        res.status(500).json({
            success: false,
            message: `Failed to run automation: ${error.message}`,
            error: error.message
        });
    }
});

// Get automation status
router.get('/status/:automation', async (req, res) => {
    const { automation } = req.params;
    const env = req.forceEnvironment === 'development' ? 'dev' : 'prod';
    
    try {
        const Airtable = require('airtable');
        const apiKeyVar = env === 'dev' ? 'DEV_AIRTABLE_API_KEY' : 'PROD_AIRTABLE_API_KEY';
        const baseIdVar = env === 'dev' ? 'DEV_AIRTABLE_BASE_ID' : 'PROD_AIRTABLE_BASE_ID';
        
        const base = new Airtable({ apiKey: process.env[apiKeyVar] })
            .base(process.env[baseIdVar]);
        
        const records = await base('Automation')
            .select({
                filterByFormula: `{Name} = '${automation}'`,
                maxRecords: 1
            })
            .firstPage();
        
        if (records.length > 0) {
            res.json({
                success: true,
                automation: automation,
                active: records[0].fields['Active'] || false,
                lastRan: records[0].fields['Last Ran Time'],
                syncDetails: records[0].fields['Sync Details']
            });
        } else {
            res.status(404).json({
                success: false,
                message: `Automation '${automation}' not found`
            });
        }
        
    } catch (error) {
        console.error('Error getting automation status:', error);
        res.status(500).json({
            success: false,
            message: `Failed to get automation status: ${error.message}`,
            error: error.message
        });
    }
});

// Service line update webhook endpoint - simplified version
router.post('/update-service-line', async (req, res) => {
    try {
        const { recordId, propertyName, jobId, serviceLineDescription, lastSyncedServiceLine } = req.body;
        
        console.log(`Service line update webhook - Property: ${propertyName}, Job: ${jobId}`);
        
        // Safety check - only process test property
        if (propertyName !== 'Boris Blinderman Test Property') {
            return res.json({ 
                success: true, 
                message: 'Not test property - skipping',
                skipped: true
            });
        }
        
        if (!jobId) {
            return res.json({ 
                success: true, 
                message: 'No HCP job ID - skipping',
                skipped: true
            });
        }
        
        // Get HCP token
        const HCP_TOKEN = process.env.PROD_HCP_TOKEN;
        const axios = require('axios');
        
        // Get line items separately (HCP API doesn't always include them in job response)
        console.log(`Fetching line items for job ${jobId}`);
        const lineItemsResponse = await axios.get(
            `https://api.housecallpro.com/jobs/${jobId}/line_items`,
            {
                headers: {
                    'Authorization': `Token ${HCP_TOKEN}`,
                    'Accept': 'application/json'
                }
            }
        );
        console.log('Raw line items response status:', lineItemsResponse.status);
        console.log('Raw line items response data type:', typeof lineItemsResponse.data);
        console.log('Raw line items response data:', JSON.stringify(lineItemsResponse.data).substring(0, 500));
        
        // Handle HCP API response format - it returns {object: "list", data: [...]}
        let lineItems = lineItemsResponse.data;
        
        // If response has a data property (HCP API format), use that
        if (lineItems && lineItems.data && Array.isArray(lineItems.data)) {
            lineItems = lineItems.data;
        }
        // If response has an items property, use that
        else if (lineItems && lineItems.items && Array.isArray(lineItems.items)) {
            lineItems = lineItems.items;
        }
        // If response has a line_items property, use that
        else if (lineItems && lineItems.line_items && Array.isArray(lineItems.line_items)) {
            lineItems = lineItems.line_items;
        }
        
        if (!Array.isArray(lineItems) || lineItems.length === 0) {
            console.error('Line items structure:', JSON.stringify(lineItemsResponse.data));
            throw new Error('No line items found or unexpected response structure');
        }
        
        const lineItem = lineItems[0];
        if (!lineItem) {
            throw new Error('First line item is undefined');
        }
        
        const currentName = lineItem.name || '';
        
        // Build new name with pipe separator
        let finalName;
        const pipeIndex = currentName.indexOf(' | ');
        
        if (pipeIndex !== -1) {
            // Preserve manual notes
            const manualNotes = currentName.substring(0, pipeIndex);
            finalName = `${manualNotes} | ${serviceLineDescription}`;
        } else if (currentName.trim()) {
            // Add pipe separator
            finalName = `${currentName} | ${serviceLineDescription}`;
        } else {
            // Empty - just use service line
            finalName = serviceLineDescription;
        }
        
        // Truncate to 200 chars if needed
        if (finalName.length > 200) {
            finalName = finalName.substring(0, 197) + '...';
        }
        
        // Update line item
        await axios.put(
            `https://api.housecallpro.com/jobs/${jobId}/line_items/${lineItem.id}`,
            {
                name: finalName,
                description: lineItem.description,
                unit_price: lineItem.unit_price,
                quantity: lineItem.quantity,
                kind: lineItem.kind
            },
            {
                headers: {
                    'Authorization': `Token ${HCP_TOKEN}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            }
        );
        
        console.log(`Service line updated successfully for job ${jobId}`);
        
        return res.json({
            success: true,
            message: 'Service line updated',
            previousName: currentName,
            newName: finalName
        });
        
    } catch (error) {
        console.error('Service line update error:', error.message);
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

module.exports = router;