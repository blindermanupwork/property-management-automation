// Production Environment - Create Job Script for Airtable
// Use this script in your PRODUCTION Airtable base

const API_URL = `https://${process.env.API_DOMAIN || 'servativ.themomentcatchers.com'}/api/prod/jobs`;
const API_KEY = 'airscripts-secure-key-2025';

// Get the record from button field
const table = base.getTable('Reservations');
const record = await input.recordAsync('', table);

if (!record) {
    output.text('❌ No record selected');
    return;
}

const recordId = record.id;
output.text(`📝 Record ID: ${recordId}`);

// Show some record details for debugging
const reservationUID = record.getCellValue('Reservation UID');
const serviceType = record.getCellValue('Service Type');
const propertyLink = record.getCellValue('Property ID');
const finalServiceTime = record.getCellValue('Final Service Time');
const serviceLineCustomInstructions = record.getCellValue('Custom Service Line Instructions');
const checkInDate = record.getCellValue('Check-in Date');
const checkOutDate = record.getCellValue('Check-out Date');
const sameDayTurnover = record.getCellValue('Same-day Turnover');

output.text(`📋 Reservation: ${reservationUID || 'No UID'}`);
output.text(`🔧 Service Type: ${serviceType ? serviceType.name : 'Not set'}`);
output.text(`🏠 Property: ${propertyLink ? propertyLink[0].name : 'Not linked'}`);
output.text(`⏰ Final Service Time: ${finalServiceTime || 'Not set'}`);
output.text(`📅 Check-in: ${checkInDate || 'Not set'} | Check-out: ${checkOutDate || 'Not set'}`);
output.text(`🔄 Same-day Turnover: ${sameDayTurnover ? 'YES' : 'NO'}`);
output.text(`📝 Service Line Custom Instructions: "${serviceLineCustomInstructions || 'Not set'}"`);
output.text(`📏 Instructions Length: ${serviceLineCustomInstructions ? serviceLineCustomInstructions.length : 0} characters`);

try {
    output.text('🔄 Creating job in PRODUCTION environment...');
    output.text(`🌐 API URL: ${API_URL}/${recordId}`);
    
    const response = await fetch(`${API_URL}/${recordId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
    });

    output.text(`📡 Response status: ${response.status}`);

    if (!response.ok) {
        const errorText = await response.text();
        output.text(`❌ Error ${response.status}: ${errorText}`);
        
        // Common error explanations
        if (response.status === 401) {
            output.text('🔒 Authentication failed - check API key');
        } else if (response.status === 404) {
            output.text('🔍 Endpoint not found - check API URL');
        } else if (response.status === 500) {
            output.text('💥 Server error - check logs');
        }
        return;
    }

    const result = await response.json();
    
    if (result.success) {
        output.text(`✅ PRODUCTION Job created successfully!`);
        output.text(`🔗 Job ID: ${result.jobId}`);
        output.text(`👤 Employee: ${result.employeeId}`);
        output.text(`📅 Scheduled: ${new Date(result.scheduledTime).toLocaleString()}`);
        if (result.appointmentId) {
            output.text(`📋 Appointment: ${result.appointmentId}`);
        }
        output.text(`🌍 Environment: ${result.environment || 'production'}`);
        
        // Debug: show what service name was used
        if (result.serviceName) {
            output.text(`🏷️ Service Name Used: "${result.serviceName}"`);
        }
        
        // Show raw response for debugging
        output.text(`\n🔍 Debug - Full Response:`);
        output.text(JSON.stringify(result, null, 2));
    } else {
        output.text(`❌ Failed: ${result.error}`);
        if (result.details) {
            output.text(`📝 Details: ${JSON.stringify(result.details)}`);
        }
        
        // Common error explanations
        if (result.error.includes('Customer not found')) {
            output.text('\n⚠️ This usually means:');
            output.text('1. The property needs HCP Customer ID and Address ID set');
            output.text('2. The HCP IDs might be from production but you\'re using prod environment');
            output.text('3. Check the Properties table for this reservation\'s property');
        }
    }

} catch (error) {
    output.text(`❌ Network Error: ${error.message}`);
    output.text(`📝 Error details: ${error.toString()}`);
    
    // More specific error guidance
    if (error.message.includes('Failed to fetch')) {
        output.text('\n⚠️ Possible causes:');
        output.text('1. Check if the API server is running');
        output.text(`2. Verify the domain is correct: ${process.env.API_DOMAIN || 'servativ.themomentcatchers.com'}`);
        output.text('3. Ensure HTTPS certificate is valid');
        output.text('4. Check if port 443 is open in firewall');
    }
}