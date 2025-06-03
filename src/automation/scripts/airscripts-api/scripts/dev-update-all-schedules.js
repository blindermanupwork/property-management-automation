// DEV Environment - Update All Schedules Script for Airtable
// Use this script for updating all records with jobs

const API_URL = 'https://servativ.themomentcatchers.com/api/dev/schedules';
const API_KEY = 'airscripts-secure-key-2025';

try {
    output.text('🔄 Updating all schedules in DEV environment...');
    output.text('This may take a moment...');
    
    const response = await fetch(API_URL, {
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
        output.text(`✅ DEV Bulk schedule check completed!`);
        output.text(`📊 Total: ${result.summary.total}`);
        output.text(`✅ Synced: ${result.summary.synced}`);
        output.text(`⏰ Wrong Time: ${result.summary.wrongTime}`);
        output.text(`📅 Wrong Date: ${result.summary.wrongDate}`);
        output.text(`❌ Errors: ${result.summary.errors}`);
    } else {
        output.text(`❌ Failed: ${result.error}`);
    }

} catch (error) {
    output.text(`❌ Network Error: ${error.message}`);
}