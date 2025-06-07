// PRODUCTION Environment - Delete Job Schedule Script for Airtable
// Use this script for button fields on individual records

const API_URL = 'https://servativ.themomentcatchers.com/api/prod/jobs';
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

// Check if there's a job schedule to delete
const jobId = record.getCellValueAsString('Service Job ID');
if (!jobId) {
    output.text('❌ No Service Job ID found - nothing to delete');
    return;
}

try {
    output.text('🗑️ Deleting job schedule in PRODUCTION environment...');
    output.text(`Job ID: ${jobId}`);
    
    const response = await fetch(`${API_URL}/${recordId}`, {
        method: 'DELETE',
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
        output.text(`✅ PRODUCTION Job schedule deleted successfully!`);
        output.text(`📝 ${result.message}`);
        if (result.jobId) {
            output.text(`🗑️ Job ID: ${result.jobId}`);
        }
        output.text(`🔄 Airtable fields updated`);
        output.text(`📅 Schedule removed from HCP`);
        output.text(`🔖 Job ID retained: ${jobId}`);
        output.text(`🔄 Click "Create Job & Sync Status" to reschedule`);
    } else {
        output.text(`❌ Failed: ${result.error}`);
    }

} catch (error) {
    output.text(`❌ Network Error: ${error.message}`);
}