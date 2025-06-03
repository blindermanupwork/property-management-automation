// Production Environment - Create Job Script for Airtable
// Use this script in your PRODUCTION Airtable base

// PRODUCTION Environment - Create Job Script for Airtable
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

try {
    output.text('🔄 Creating job in PRODUCTION environment...');
    
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
        output.text(`✅ PRODUCTION Job created successfully!`);
        output.text(`🔗 Job ID: ${result.jobId}`);
        output.text(`👤 Employee: ${result.employeeId}`);
        output.text(`📅 Scheduled: ${result.scheduledTime}`);
        if (result.appointmentId) {
            output.text(`📋 Appointment: ${result.appointmentId}`);
        }
    } else {
        output.text(`❌ Failed: ${result.error}`);
    }

} catch (error) {
    output.text(`❌ Network Error: ${error.message}`);
}