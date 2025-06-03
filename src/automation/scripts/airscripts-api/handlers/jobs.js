const Airtable = require('airtable');
const fetch = require('node-fetch');
const { getArizonaTime, formatDate, formatTime } = require('../utils/datetime');
const { getAirtableConfig, getHCPConfig } = require('../utils/config');

// HCP API helper with retry logic
async function hcpFetch(hcpConfig, path, method = 'GET', body = null) {
  const maxRetries = 3;
  let retry = 0;
  
  while (true) {
    const response = await fetch(`https://api.housecallpro.com${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Token ${hcpConfig.token}`
      },
      body: body ? JSON.stringify(body) : undefined
    });

    const raw = await response.text();
    
    if (response.status === 429 && retry < maxRetries) {
      retry++;
      const reset = response.headers.get('RateLimit-Reset');
      const wait = reset
        ? Math.max(new Date(reset) - new Date(), 1000)
        : 1000 * (2 ** retry);
      await new Promise(resolve => setTimeout(resolve, wait));
      continue;
    }

    if (!response.ok) {
      throw new Error(`HCP API Error: ${response.status} - ${raw}`);
    }

    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  }
}

// Delay helper
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// Find next reservation for a property (matches original AirScript logic)
async function findNextReservation(base, propertyId, checkOutDate) {
  const query = await base('Reservations').select({
    sorts: [{ field: 'Check-in Date', direction: 'asc' }]
  }).all();
  
  const potentialNext = query.filter(record => {
    if (!record.get('Property ID')) return false;
    const propLinks = record.get('Property ID');
    if (!propLinks.length || propLinks[0] !== propertyId) return false;
    
    const entryType = record.get('Entry Type');
    if (!entryType || entryType.name !== 'Reservation') return false;
    
    const status = record.get('Status');
    if (status && status.name === 'Old') return false;
    
    const checkInDate = record.get('Check-in Date');
    if (!checkInDate || new Date(checkInDate) <= new Date(checkOutDate)) return false;
    
    return true;
  });
  
  return potentialNext.length > 0 ? potentialNext[0] : null;
}

// Create job from reservation - COMPLETE implementation matching original
async function createJob(req, res) {
  try {
    const { recordId } = req.params;
    
    // Get environment-specific config
    const environment = req.forceEnvironment || process.env.ENVIRONMENT || 'development';
    const airtableConfig = getAirtableConfig(environment);
    const hcpConfig = getHCPConfig(environment);
    const base = new Airtable({ apiKey: airtableConfig.apiKey }).base(airtableConfig.baseId);
    
    console.log(`Creating job for record ${recordId} in ${environment} environment`);
    
    // Fetch reservation record
    const reservation = await base('Reservations').find(recordId);
    
    // Get Final Service Time
    const finalServiceTime = reservation.get('Final Service Time');
    if (!finalServiceTime) {
      throw new Error('No Final Service Time specified');
    }
    
    const schedStart = new Date(finalServiceTime);
    const schedEnd = new Date(schedStart.getTime() + 60 * 60 * 1000); // +1 hour
    const isoStart = schedStart.toISOString();
    const isoEnd = schedEnd.toISOString();
    
    // Get property details
    const propertyLinks = reservation.get('Property ID');
    if (!propertyLinks || propertyLinks.length === 0) {
      throw new Error('No linked property');
    }

    const property = await base('Properties').find(propertyLinks[0]);
    
    // Get HCP Customer ID (with proper lookup)
    const customerLinks = property.get('HCP Customer ID');
    if (!customerLinks || customerLinks.length === 0) {
      throw new Error('Property missing HCP Customer ID');
    }

    let customerId;
    if (typeof customerLinks[0] === 'object' && customerLinks[0].name) {
      customerId = customerLinks[0].name;
    } else {
      const customerRecordId = typeof customerLinks[0] === 'object' ? customerLinks[0].id : customerLinks[0];
      const customerRecord = await base('Customers').find(customerRecordId);
      customerId = customerRecord.get('HCP Customer ID') || 
                  customerRecord.get('Customer ID') || 
                  customerRecord.get('Name') || 
                  customerRecord.getName();
      
      if (!customerId || customerId.startsWith('rec')) {
        throw new Error('Customer record does not contain a valid HCP customer ID');
      }
    }

    // Get HCP Address ID
    const addressId = property.get('HCP Address ID');
    if (!addressId) {
      throw new Error('Property missing HCP Address ID');
    }

    // Get service type and normalize it
    const serviceTypeObj = reservation.get('Service Type');
    const rawServiceType = serviceTypeObj ? serviceTypeObj.name : '';
    
    let serviceType;
    if (rawServiceType === 'Return Laundry') {
      serviceType = 'Return Laundry';
    } else if (rawServiceType === 'Inspection') {
      serviceType = 'Inspection';
    } else {
      serviceType = 'Turnover';
    }

    // Get template ID and job type ID based on service type
    let templateId, jobTypeId;
    
    if (serviceType === 'Return Laundry') {
      templateId = property.get('Return Laundry Job Template ID');
      jobTypeId = hcpConfig.jobTypes.returnLaundry;
    } else if (serviceType === 'Inspection') {
      templateId = property.get('Inspection Job Template ID');  
      jobTypeId = hcpConfig.jobTypes.inspection;
    } else {
      templateId = property.get('Turnover Job Template ID');
      jobTypeId = hcpConfig.jobTypes.turnover;
    }

    if (!templateId) {
      throw new Error(`No ${serviceType} template ID found for property`);
    }

    // Determine service name based on next reservation
    const sameDay = reservation.get('Same-day Turnover');
    let serviceName;
    
    if (sameDay) {
      serviceName = `${serviceType} STR SAME DAY`;
    } else {
      const checkOutDate = reservation.get('Check-out Date');
      if (serviceType === 'Turnover' && checkOutDate) {
        const nextReservation = await findNextReservation(base, propertyLinks[0], checkOutDate);
        
        if (nextReservation) {
          const nextCheckIn = new Date(nextReservation.get('Check-in Date'));
          const month = nextCheckIn.toLocaleString('en-US', { month: 'long' });
          const day = nextCheckIn.getDate();
          serviceName = `${serviceType} STR Next Guest ${month} ${day}`;
        } else {
          serviceName = `${serviceType} STR Next Guest Unknown`;
        }
      } else {
        serviceName = `${serviceType} STR Next Guest Unknown`;
      }
    }
    
    // Add Service Line Custom Instructions if present
    const serviceLineCustomInstructions = reservation.get('Service Line Custom Instructions');
    console.log(`DEBUG: Service Line Custom Instructions: "${serviceLineCustomInstructions}"`);
    
    if (serviceLineCustomInstructions && serviceLineCustomInstructions.trim()) {
      // Limit custom instructions length to prevent issues
      let customInstructions = serviceLineCustomInstructions.trim();
      const maxCustomLength = 200; // Leave room for base service name
      
      if (customInstructions.length > maxCustomLength) {
        customInstructions = customInstructions.substring(0, maxCustomLength - 3) + '...';
        console.log(`DEBUG: Truncated custom instructions from ${serviceLineCustomInstructions.length} to ${customInstructions.length} characters`);
      }
      
      serviceName += ` - ${customInstructions}`;
      console.log(`DEBUG: Final service name with custom instructions: "${serviceName}"`);
      console.log(`DEBUG: Final service name length: ${serviceName.length} characters`);
    } else {
      console.log(`DEBUG: Final service name (no custom instructions): "${serviceName}"`);
    }

    // Check if job already exists
    let jobId = reservation.get('Service Job ID');
    let appointmentId = reservation.get('Service Appointment ID');

    if (!jobId) {
      // Create job with COMPLETE data like original script
      const jobData = {
        invoice_number: 0,
        customer_id: customerId,
        address_id: addressId,
        schedule: {
          scheduled_start: isoStart,
          scheduled_end: isoEnd,
          arrival_window: 0
        },
        assigned_employee_ids: [hcpConfig.employeeId],
        line_items: [],
        job_fields: {
          job_type_id: jobTypeId
        }
      };

      console.log('Creating HCP job with data:', JSON.stringify(jobData, null, 2));
      const jobResult = await hcpFetch(hcpConfig, '/jobs', 'POST', jobData);
      jobId = jobResult.id;
      console.log('Created job ID:', jobId);

      // Give HCP time to create the appointment
      await delay(700);

      // Capture appointment ID with multiple strategies (like original)
      try {
        const jobDetails = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
        
        if (jobDetails.appointments && jobDetails.appointments.length > 0) {
          appointmentId = jobDetails.appointments[0].id;
          console.log('Found appointment ID in job details:', appointmentId);
        } else {
          console.log('No appointments in job details, fetching separately...');
          await delay(500);
          const appointmentsResponse = await hcpFetch(hcpConfig, `/jobs/${jobId}/appointments`);
          
          if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
            appointmentId = appointmentsResponse.appointments[0].id;
            console.log('Found appointment ID via separate fetch:', appointmentId);
          } else {
            console.log('No appointment found for job', jobId);
          }
        }
      } catch (error) {
        console.log('Failed to fetch appointment ID:', error.message);
      }

      // Update Airtable with initial job info
      const initialUpdate = {
        'Service Job ID': jobId,
        'Job Creation Time': new Date().toISOString()
      };

      if (appointmentId) {
        initialUpdate['Service Appointment ID'] = appointmentId;
      }

      await base('Reservations').update(recordId, initialUpdate);

      // Copy template line items (like original script)
      try {
        const templateItems = await hcpFetch(hcpConfig, `/jobs/${templateId}/line_items`);
        const lineItems = (templateItems.data || []).map((item, index) => ({
          name: index === 0 ? serviceName : item.name,
          description: item.description || '',
          unit_price: item.unit_price,
          unit_cost: item.unit_cost,
          quantity: item.quantity,
          kind: item.kind,
          taxable: item.taxable,
          service_item_id: item.service_item_id || null,
          service_item_type: item.service_item_type || null
        }));

        if (lineItems.length > 0) {
          console.log(`DEBUG: Updating ${lineItems.length} line items for job ${jobId}`);
          console.log(`DEBUG: First line item name length: ${lineItems[0].name.length} characters`);
          console.log(`DEBUG: First line item name: "${lineItems[0].name.substring(0, 100)}${lineItems[0].name.length > 100 ? '...' : ''}"`);
          
          try {
            const updateResp = await hcpFetch(hcpConfig, `/jobs/${jobId}/line_items/bulk_update`, 'PUT', {
              line_items: lineItems
            });
            console.log('Successfully copied', lineItems.length, 'line items from template');
          } catch (updateError) {
            console.error(`ERROR updating line items: ${updateError.message}`);
            // Check if it's a length issue
            if (lineItems[0].name.length > 255) {
              console.log(`WARNING: Service name is ${lineItems[0].name.length} characters, may exceed HCP limit`);
              // Try with truncated name
              const truncatedName = lineItems[0].name.substring(0, 250) + '...';
              lineItems[0].name = truncatedName;
              console.log(`Retrying with truncated name: "${truncatedName}"`);
              
              try {
                await hcpFetch(hcpConfig, `/jobs/${jobId}/line_items/bulk_update`, 'PUT', {
                  line_items: lineItems
                });
                console.log('Successfully updated line items with truncated name');
              } catch (retryError) {
                console.error(`ERROR on retry: ${retryError.message}`);
              }
            }
          }
        }
      } catch (error) {
        console.log('Failed to copy line items:', error.message);
      }
    }

    // Fetch live job and sync Airtable (like original)
    await delay(700);
    const liveJob = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
    const schedLive = new Date(liveJob.schedule.scheduled_start);

    // Try to capture appointment ID if still missing
    if (!appointmentId) {
      console.log('Missing appointment ID, attempting to fetch during sync...');
      
      try {
        if (liveJob.appointments && liveJob.appointments.length > 0) {
          appointmentId = liveJob.appointments[0].id;
          console.log('Found appointment ID in sync job details:', appointmentId);
        } else {
          await delay(500);
          const appointmentsResponse = await hcpFetch(hcpConfig, `/jobs/${jobId}/appointments`);
          
          if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
            appointmentId = appointmentsResponse.appointments[0].id;
            console.log('Found appointment ID via sync separate fetch:', appointmentId);
          }
        }
      } catch (error) {
        console.log('Failed to fetch appointment ID during sync:', error.message);
      }
    }

    // Map HCP status to Airtable status
    function mapStatus(workStatus) {
      const ws = (workStatus || '').toLowerCase();
      if (ws.includes('cancel')) return 'Canceled';
      if (ws.includes('complete')) return 'Completed';
      if (ws.includes('in_progress')) return 'In Progress';
      if (ws.includes('scheduled')) return 'Scheduled';
      if (!ws || ws.includes('unscheduled')) return 'Unscheduled';
      return null;
    }

    const atStatus = mapStatus(liveJob.work_status);

    // Determine sync status (like original with timezone handling)
    const azDate = d => d.toLocaleDateString('en-US', {
      timeZone: 'America/Phoenix', month: 'long', day: 'numeric'
    });
    const azTime = d => d.toLocaleTimeString('en-US', {
      timeZone: 'America/Phoenix', hour: 'numeric', minute: '2-digit', hour12: true
    });

    const dateMatch = azDate(schedLive) === azDate(schedStart);
    const timeMatch = azTime(schedLive) === azTime(schedStart);

    let syncStatus, syncDetails;
    if (!dateMatch) {
      syncStatus = 'Wrong Date';
      syncDetails = `Final Service Time is **${azDate(schedStart)}** but service is **${azDate(schedLive)}**.`;
    } else if (!timeMatch) {
      syncStatus = 'Wrong Time';
      syncDetails = `Final Service Time is **${azTime(schedStart)}** but service is **${azTime(schedLive)}**.`;
    } else {
      syncStatus = 'Synced';
      syncDetails = `Service matches **${azDate(schedLive)} at ${azTime(schedLive)}**.`;
    }

    if (atStatus === 'Canceled') {
      const when = new Date(liveJob.updated_at || Date.now());
      syncDetails = `Job canceled on ${azDate(when)} at ${azTime(when)}.`;
    }

    // Final update to Airtable with complete sync info
    const updateFields = {
      'Scheduled Service Time': schedLive.toISOString(),
      'Sync Status': syncStatus,
      'Sync Details': syncDetails,
      'Sync Date and Time': getArizonaTime()
    };

    if (atStatus) {
      updateFields['Job Status'] = atStatus;
    }

    if (appointmentId && !reservation.get('Service Appointment ID')) {
      updateFields['Service Appointment ID'] = appointmentId;
    }

    await base('Reservations').update(recordId, updateFields);

    res.json({
      success: true,
      jobId: jobId,
      appointmentId: appointmentId,
      employeeId: hcpConfig.employeeId,
      scheduledTime: schedLive.toISOString(),
      syncStatus: syncStatus,
      syncDetails: syncDetails,
      environment: environment,
      serviceName: serviceName  // Add service name for debugging
    });

  } catch (error) {
    console.error('Error creating job:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

// Delete job schedule
async function deleteJob(req, res) {
  try {
    const { recordId } = req.params;
    
    // Get environment-specific config
    const environment = req.forceEnvironment || process.env.ENVIRONMENT || 'development';
    const airtableConfig = getAirtableConfig(environment);
    const hcpConfig = getHCPConfig(environment);
    const base = new Airtable({ apiKey: airtableConfig.apiKey }).base(airtableConfig.baseId);
    
    console.log(`Deleting job for record ${recordId} in ${environment} environment`);
    
    // Get reservation record
    const reservation = await base('Reservations').find(recordId);
    const jobId = reservation.get('Service Job ID');
    const reservationUID = reservation.get('Reservation UID');
    
    if (!jobId) {
      return res.status(400).json({
        success: false,
        error: 'No Service Job ID found for this reservation'
      });
    }
    
    console.log(`Deleting HCP job schedule: ${jobId}`);
    
    // Delete the job schedule in HCP
    try {
      await hcpFetch(hcpConfig, `/jobs/${jobId}/schedule`, 'DELETE');
      console.log(`Successfully deleted schedule for job ${jobId}`);
    } catch (hcpError) {
      console.warn(`Failed to delete HCP schedule: ${hcpError.message}`);
      // Continue with Airtable update even if HCP delete fails
    }
    
    // Update Airtable fields to clear the job
    const updateFields = {
      'Scheduled Service Time': null,
      'Service Job ID': null,
      'Service Appointment ID': null,
      'Sync Details': `HCP schedule deleted on ${getArizonaTime()}`,
      'Sync Date and Time': getArizonaTime()
    };
    
    // Try to set status fields with error handling
    try {
      updateFields['Sync Status'] = { name: 'Not Created' };
      updateFields['Service Type'] = { name: 'Canceled' };
      updateFields['Job Status'] = { name: 'Canceled' };
      
      await base('Reservations').update(recordId, updateFields);
    } catch (airtableError) {
      console.warn(`Airtable field error:`, airtableError.message);
      
      // Update without problematic fields
      const fallbackFields = { ...updateFields };
      
      if (airtableError.message.includes('Sync Status')) {
        delete fallbackFields['Sync Status'];
      }
      if (airtableError.message.includes('Service Type')) {
        delete fallbackFields['Service Type'];
      }
      if (airtableError.message.includes('Job Status')) {
        delete fallbackFields['Job Status'];
      }
      
      try {
        await base('Reservations').update(recordId, fallbackFields);
      } catch (secondError) {
        console.warn(`Second Airtable error, updating with minimal fields:`, secondError.message);
        
        // Update only essential fields
        const minimalFields = {
          'Sync Details': updateFields['Sync Details'],
          'Sync Date and Time': updateFields['Sync Date and Time'],
          'Scheduled Service Time': null,
          'Service Job ID': null,
          'Service Appointment ID': null
        };
        
        await base('Reservations').update(recordId, minimalFields);
      }
    }
    
    res.json({
      success: true,
      recordId,
      uid: reservationUID,
      jobId,
      message: 'Job schedule deleted successfully',
      environment: environment
    });
    
  } catch (error) {
    console.error('Error deleting job:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

module.exports = {
  createJob,
  deleteJob
};