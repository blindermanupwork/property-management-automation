// Airtable Automation Script: Webhook Service Line Updater
// Purpose: Sends webhook to update HCP service line when it changes
// Trigger: When Service Line Description is updated
// Author: Automation System

// Get input from automation trigger
let inputConfig = input.config();
let recordId = inputConfig.recordId;

// Configuration - CHANGE THESE VALUES
const API_KEY = 'YOUR_API_KEY_HERE'; // Get from .env file
const ENVIRONMENT = 'development'; // or 'production'
const BASE_URL = ENVIRONMENT === 'production' 
    ? 'https://servativ.themomentcatchers.com/api/prod/automation/update-service-line'
    : 'https://servativ.themomentcatchers.com/api/dev/automation/update-service-line';

// Get the record
let table = base.getTable('Reservations');
let record = await table.selectRecordAsync(recordId);

if (!record) {
    console.log('Error: Record not found');
    output.set('success', false);
    output.set('error', 'Record not found');
    throw new Error('Record not found');
}

// Check if this is Boris Test Property
let propertyName = record.getCellValueAsString('Property Name');
let jobId = record.getCellValueAsString('Service Job ID');
let serviceLineDescription = record.getCellValueAsString('Service Line Description');
let lastSyncedServiceLine = record.getCellValueAsString('Last Synced Service Line');

console.log('Property:', propertyName);
console.log('Job ID:', jobId);
console.log('Service Line:', serviceLineDescription);
console.log('Last Synced:', lastSyncedServiceLine);

// Safety check - only process test property
if (propertyName !== 'Boris Blinderman Test Property') {
    console.log('Skipping - not test property');
    output.set('success', true);
    output.set('message', 'Not test property - skipping');
    output.set('skipped', true);
} else if (!jobId) {
    console.log('Skipping - no HCP job ID');
    output.set('success', true);
    output.set('message', 'No HCP job ID - skipping');
    output.set('skipped', true);
} else if (serviceLineDescription === lastSyncedServiceLine) {
    console.log('Skipping - service line unchanged');
    output.set('success', true);
    output.set('message', 'Service line unchanged - skipping');
    output.set('skipped', true);
} else {
    // Send webhook
    console.log('Sending webhook to update HCP...');
    
    try {
        let response = await fetch(BASE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({
                recordId: recordId,
                environment: ENVIRONMENT
            })
        });

        let result = await response.json();
        
        if (response.ok) {
            console.log('✅ Webhook sent successfully');
            console.log('Response:', JSON.stringify(result, null, 2));
            
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