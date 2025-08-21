// PRODUCTION Environment - Update Single Schedule Script for Airtable
// Use this script for button fields on individual records

const API_URL = `https://${process.env.API_DOMAIN || 'servativ.themomentcatchers.com'}/api/prod/schedules`;
const API_KEY = 'airscripts-secure-key-2025';

// Get the record from button field
const table = base.getTable('Reservations');
const record = await input.recordAsync('', table);

if (!record) {
    output.text('❌ No record selected');
    return;
}

const recordId = record.id;

if (!recordId) {
    output.text('❌ No record selected');
    return;
}

try {
    output.text('🔄 Updating schedule in PRODUCTION environment...');
    
    const response = await fetch(`${API_URL}/${recordId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
    });

    if (!response.ok) {
        const error = await response.text();
        output.text(`❌ Error: ${response.status} - ${error}`);
        return;
    }

    const result = await response.json();
    
    if (result.success) {
        output.text(`✅ PRODUCTION Schedule updated!`);
        output.text(`📊 Status: ${result.syncStatus}`);
        output.text(`📝 Details: ${result.syncDetails}`);
        if (result.jobId) {
            output.text(`🔗 Job ID: ${result.jobId}`);
        }
    } else {
        output.text(`❌ Failed: ${result.error}`);
    }

} catch (error) {
    output.text(`❌ Network Error: ${error.message}`);
}