// Airtable Automation Script: Update HCP Service Line
// Purpose: Sends webhook to update HCP service line when it changes
// Trigger: When Service Line Description is updated
// Environment: PRODUCTION ONLY

// Get input from automation trigger
let inputConfig = input.config();
let recordId = inputConfig.recordId;

// Configuration
const WEBHOOK_URL = 'https://servativ.themomentcatchers.com/api/prod/automation/update-service-line';

// Get the record
let table = base.getTable('Reservations');
let record = await table.selectRecordAsync(recordId);

if (!record) {
    console.log('Error: Record not found');
    output.set('success', false);
    output.set('error', 'Record not found');
    throw new Error('Record not found');
}

// Get field values
let propertyIdField = record.getCellValue('Property ID');
let propertyName = propertyIdField && propertyIdField.length > 0 ? propertyIdField[0].name : 'Unknown';
let jobId = record.getCellValueAsString('Service Job ID');
let serviceLineDescription = record.getCellValueAsString('Service Line Description');
// Get Last Synced Service Line if it exists (field may not be created yet)
let lastSyncedServiceLine = '';
try {
    lastSyncedServiceLine = record.getCellValueAsString('Last Synced Service Line');
} catch (e) {
    console.log('Note: Last Synced Service Line field not found - proceeding without it');
}

console.log('=== Service Line Update ===');
console.log('Property:', propertyName);
console.log('Job ID:', jobId);
console.log('Current Service Line:', serviceLineDescription);
console.log('Last Synced:', lastSyncedServiceLine);

// Safety check - only process test property
if (propertyName !== 'Boris Blinderman Test Property') {
    console.log('❌ Skipping - not test property');
    output.set('success', true);
    output.set('message', 'Not test property - skipping');
    output.set('skipped', true);
} else if (!jobId) {
    console.log('❌ Skipping - no HCP job ID');
    output.set('success', true);
    output.set('message', 'No HCP job ID - skipping');
    output.set('skipped', true);
} else if (serviceLineDescription === lastSyncedServiceLine) {
    console.log('❌ Skipping - service line unchanged');
    output.set('success', true);
    output.set('message', 'Service line unchanged - skipping');
    output.set('skipped', true);
} else {
    // Send webhook to servativ server
    console.log('📤 Sending webhook to update HCP...');
    
    try {
        let response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'airscripts-secure-key-2025'
            },
            body: JSON.stringify({
                recordId: recordId,
                propertyName: propertyName,
                jobId: jobId,
                serviceLineDescription: serviceLineDescription,
                lastSyncedServiceLine: lastSyncedServiceLine
            })
        });

        let responseText = await response.text();
        let result;
        
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            console.log('Response is not JSON:', responseText);
            result = { message: responseText };
        }
        
        if (response.ok) {
            console.log('✅ Webhook sent successfully');
            console.log('Response:', JSON.stringify(result, null, 2));
            
            // Update Last Synced field
            await table.updateRecordAsync(recordId, {
                'Last Synced Service Line': serviceLineDescription
            });
            
            output.set('success', true);
            output.set('message', 'Service line updated in HCP');
            output.set('response', result);
        } else {
            console.error('❌ Webhook failed:', response.status);
            console.error('Error:', JSON.stringify(result, null, 2));
            
            output.set('success', false);
            output.set('error', result.error || 'Webhook failed');
            output.set('status', response.status);
        }
    } catch (error) {
        console.error('❌ Webhook error:', error.message);
        
        output.set('success', false);
        output.set('error', error.message);
    }
}

console.log('=========================');