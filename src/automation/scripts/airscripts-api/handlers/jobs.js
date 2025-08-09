const Airtable = require('airtable');
const fetch = require('node-fetch');
const { getArizonaTime, formatDate, formatTime } = require('../utils/datetime');
const { getAirtableConfig, getHCPConfig } = require('../utils/config');

// Import sync message builder for dev environment
let buildSyncMessage = null;

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
    
    // Determine environment from request
    const environment = req.forceEnvironment || (req.path.includes('/dev/') ? 'development' : 'production');
    
    // Load sync message builder and timestamp function
    let getArizonaTimestamp = null;
    if (!buildSyncMessage) {
      try {
        const syncMessageBuilder = require('../../shared/syncMessageBuilder');
        buildSyncMessage = syncMessageBuilder.buildSyncMessage;
        getArizonaTimestamp = syncMessageBuilder.getArizonaTimestamp;
        console.log('✅ Loaded sync message builder');
      } catch (e) {
        console.error('❌ Could not load sync message builder:', e.message);
        console.error('Full error:', e);
      }
    }
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

    // Get service type - preserve whatever is set in Airtable
    const serviceTypeObj = reservation.get('Service Type');
    const serviceType = (serviceTypeObj && serviceTypeObj.name) ? serviceTypeObj.name : 'Turnover';
    
    console.log(`Service Type from Airtable: "${serviceType}"`);
    
    // Determine which template/job type to use based on service type
    // We normalize for template selection but preserve the actual service type for display
    let templateServiceType;
    if (serviceType === 'Return Laundry') {
      templateServiceType = 'Return Laundry';
    } else if (serviceType === 'Inspection') {
      templateServiceType = 'Inspection';
    } else {
      // Everything else uses Turnover template (including Initial Service, Deep Clean, etc.)
      templateServiceType = 'Turnover';
    }

    // Get template ID and job type ID based on template service type
    let templateId, jobTypeId;
    
    if (templateServiceType === 'Return Laundry') {
      templateId = property.get('Return Laundry Job Template ID');
      jobTypeId = hcpConfig.jobTypes.returnLaundry;
    } else if (templateServiceType === 'Inspection') {
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
    const isNextEntryBlock = reservation.get('Next Entry Is Block');
    let serviceName;
    
    if (sameDay) {
      serviceName = `SAME DAY ${serviceType} STR`;
    } else {
      const checkOutDate = reservation.get('Check-out Date');
      if (serviceType === 'Turnover' && checkOutDate) {
        // Check both Next Guest Date fields - prioritize iTrip if available
        const nextGuestDate = reservation.get('Next Guest Date');
        const iTripNextGuestDate = reservation.get('iTrip Next Guest Date');
        const entrySource = reservation.get('Entry Source');
        
        console.log(`DEBUG: Checking Next Guest Date fields for record ${recordId}:`);
        console.log(`  - Next Guest Date: ${nextGuestDate || 'null/undefined'}`);
        console.log(`  - iTrip Next Guest Date: ${iTripNextGuestDate || 'null/undefined'}`);
        console.log(`  - Entry Source: ${entrySource ? entrySource.name : 'null/undefined'}`);
        
        // Use iTrip Next Guest Date first if available, otherwise fall back to general Next Guest Date
        const effectiveNextGuestDate = iTripNextGuestDate || nextGuestDate;
        
        if (effectiveNextGuestDate) {
          // Use the next guest date (either iTrip or general)
          const nextCheckIn = new Date(effectiveNextGuestDate + 'T12:00:00-07:00'); // Force Arizona time at noon
          const month = nextCheckIn.toLocaleString('en-US', { month: 'long', timeZone: 'America/Phoenix' });
          const day = parseInt(nextCheckIn.toLocaleDateString('en-US', { day: 'numeric', timeZone: 'America/Phoenix' }));
          
          if (isNextEntryBlock) {
            serviceName = `OWNER ARRIVING ${serviceType} STR ${month} ${day}`;
            console.log(`Next entry is a BLOCK (owner arriving)`);
          } else {
            serviceName = `${serviceType} STR Next Guest ${month} ${day}`;
          }
          console.log(`Using ${iTripNextGuestDate ? 'iTrip' : 'general'} Next Guest Date: ${effectiveNextGuestDate}`);
        } else {
          // Fall back to searching for next reservation
          const nextReservation = await findNextReservation(base, propertyLinks[0], checkOutDate);
          
          if (nextReservation) {
            const nextCheckInDate = nextReservation.get('Check-in Date');
            const nextCheckIn = new Date(nextCheckInDate + 'T12:00:00-07:00'); // Force Arizona time at noon
            const month = nextCheckIn.toLocaleString('en-US', { month: 'long', timeZone: 'America/Phoenix' });
            const day = parseInt(nextCheckIn.toLocaleDateString('en-US', { day: 'numeric', timeZone: 'America/Phoenix' }));
            serviceName = `${serviceType} STR Next Guest ${month} ${day}`;
          } else {
            serviceName = `${serviceType} STR Next Guest Unknown`;
          }
        }
      } else {
        serviceName = `${serviceType} STR Next Guest Unknown`;
      }
    }
    
    // Store base service name before modifications
    const baseSvcName = serviceName;
    
    // Check for long-term guest (2+ weeks) and modify service name accordingly
    let isLongTermGuest = false;
    const checkInDate = reservation.get('Check-in Date');
    const checkOutDate = reservation.get('Check-out Date');
    
    if (checkInDate && checkOutDate) {
      const checkIn = new Date(checkInDate);
      const checkOut = new Date(checkOutDate);
      const stayDurationDays = (checkOut - checkIn) / (1000 * 60 * 60 * 24);
      
      if (stayDurationDays >= 14) {
        isLongTermGuest = true;
        console.log(`DEBUG: Long-term guest detected - ${stayDurationDays} days stay`);
      }
    }
    
    // Build service line description with new hierarchy:
    // 1. Custom Instructions
    // 2. OWNER ARRIVING (if next entry is block)
    // 3. LONG TERM GUEST DEPARTING (if stay >= 14 days)
    // 4. Base service name
    
    const serviceLineCustomInstructions = reservation.get('Custom Service Line Instructions');
    console.log(`DEBUG: Custom Service Line Instructions: "${serviceLineCustomInstructions}"`);
    console.log(`DEBUG: Is Next Entry Block: ${isNextEntryBlock}`);
    console.log(`DEBUG: Is Long Term Guest: ${isLongTermGuest}`);
    
    let parts = [];
    
    // Add custom instructions if present
    if (serviceLineCustomInstructions && serviceLineCustomInstructions.trim()) {
      // Limit custom instructions length to prevent issues
      let customInstructions = serviceLineCustomInstructions.trim();
      const maxCustomLength = 200;
      
      if (customInstructions.length > maxCustomLength) {
        customInstructions = customInstructions.substring(0, maxCustomLength - 3) + '...';
        console.log(`DEBUG: Truncated custom instructions from ${serviceLineCustomInstructions.length} to ${customInstructions.length} characters`);
      }
      
      parts.push(customInstructions);
      console.log(`Added custom instructions: "${customInstructions}"`);
    }
    
    // Add LONG TERM GUEST DEPARTING if applicable (but not if owner is already in base name)
    // Note: OWNER ARRIVING is now part of the base service name when next entry is a block
    if (isLongTermGuest && !isNextEntryBlock) {
      parts.push("LONG TERM GUEST DEPARTING");
      console.log(`Added long-term guest flag`);
    }
    
    // Add base service name
    parts.push(baseSvcName);
    
    // Join all parts
    if (parts.length > 1) {
      serviceName = parts.join(" - ");
    } else {
      serviceName = parts[0];
    }
    
    console.log(`DEBUG: Final service name: "${serviceName}" (${serviceName.length} characters)`);

    // Check if job already exists
    let jobId = reservation.get('Service Job ID');
    let appointmentId = reservation.get('Service Appointment ID');
    let currentJobStatus = reservation.get('Job Status');
    let isJobCanceled = currentJobStatus && currentJobStatus.name === 'Canceled';

    if (!jobId) {
      // Create new job with COMPLETE data like original script
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
    } else if (isJobCanceled) {
      // Job exists but is canceled - reschedule it
      console.log(`Rescheduling canceled job ${jobId}`);
      
      // Update the job to scheduled status with new schedule
      const updateData = {
        work_status: 'scheduled',
        schedule: {
          scheduled_start: isoStart,
          scheduled_end: isoEnd,
          arrival_window: 0
        },
        assigned_employee_ids: [hcpConfig.employeeId]
      };
      
      console.log('Updating canceled job with new schedule:', JSON.stringify(updateData, null, 2));
      await hcpFetch(hcpConfig, `/jobs/${jobId}`, 'PATCH', updateData);
      
      // Give HCP time to process the update
      await delay(700);
      
      // Try to get appointment ID for the rescheduled job
      try {
        const jobDetails = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
        
        if (jobDetails.appointments && jobDetails.appointments.length > 0) {
          appointmentId = jobDetails.appointments[0].id;
          console.log('Found appointment ID after rescheduling:', appointmentId);
        } else {
          console.log('No appointments found after rescheduling, fetching separately...');
          await delay(500);
          const appointmentsResponse = await hcpFetch(hcpConfig, `/jobs/${jobId}/appointments`);
          
          if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
            appointmentId = appointmentsResponse.appointments[0].id;
            console.log('Found appointment ID via separate fetch after reschedule:', appointmentId);
          }
        }
      } catch (error) {
        console.log('Failed to fetch appointment ID after reschedule:', error.message);
      }
      
      // Update appointment ID if found
      if (appointmentId && !reservation.get('Service Appointment ID')) {
        await base('Reservations').update(recordId, {
          'Service Appointment ID': appointmentId
        });
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
    
    console.log(`🔍 Sync check - Environment: ${environment}, buildSyncMessage available: ${!!buildSyncMessage}`);
    
    if (buildSyncMessage && environment === 'development') {
      // Use clear messaging for dev environment
      if (!dateMatch) {
        syncStatus = 'Wrong Date';
        syncDetails = buildSyncMessage('WRONG_DATE', {
          airtableValue: schedStart.toISOString(),
          hcpValue: schedLive.toISOString()
        });
      } else if (!timeMatch) {
        syncStatus = 'Wrong Time';
        syncDetails = buildSyncMessage('WRONG_TIME', {
          airtableValue: schedStart.toISOString(),
          hcpValue: schedLive.toISOString()
        });
      } else {
        syncStatus = 'Synced';
        syncDetails = buildSyncMessage('SYNCED', {
          airtableValue: schedStart.toISOString()
        });
      }
    } else {
      // Fallback messaging with timestamps
      const timestamp = getArizonaTimestamp ? ` - ${getArizonaTimestamp()}` : '';
      if (!dateMatch) {
        syncStatus = 'Wrong Date';
        syncDetails = `Airtable shows ${azDate(schedStart)} at ${azTime(schedStart)} but HCP shows ${azDate(schedLive)} at ${azTime(schedLive)}${timestamp}`;
      } else if (!timeMatch) {
        syncStatus = 'Wrong Time';
        syncDetails = `Airtable shows ${azTime(schedStart)} but HCP shows ${azTime(schedLive)}${timestamp}`;
      } else {
        syncStatus = 'Synced';
        syncDetails = `Schedules in sync: ${azDate(schedLive)} at ${azTime(schedLive)}${timestamp}`;
      }
    }

    if (atStatus === 'Canceled') {
      const when = new Date(liveJob.updated_at || Date.now());
      if (buildSyncMessage && environment === 'development') {
        syncDetails = buildSyncMessage('JOB_CANCELED', {
          canceledAt: when.toISOString()
        });
      } else {
        syncDetails = `Job canceled on ${azDate(when)} at ${azTime(when)}.`;
      }
    }

    // Final update to Airtable with complete sync info
    // Use Schedule Sync Details for schedule synchronization messages
    const updateFields = {
      'Scheduled Service Time': schedLive.toISOString(),
      'Sync Status': syncStatus,
      'Schedule Sync Details': syncDetails,
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

// Delete job schedule (only action supported by HCP API)
async function cancelJob(req, res) {
  try {
    const { recordId } = req.params;
    
    // Get environment-specific config
    const environment = req.forceEnvironment || process.env.ENVIRONMENT || 'development';
    const airtableConfig = getAirtableConfig(environment);
    const hcpConfig = getHCPConfig(environment);
    const base = new Airtable({ apiKey: airtableConfig.apiKey }).base(airtableConfig.baseId);
    
    console.log(`Deleting job schedule for record ${recordId} in ${environment} environment`);
    
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
    
    // First check if job has a schedule
    let jobDetails;
    try {
      jobDetails = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
    } catch (error) {
      console.error(`Failed to get job details: ${error.message}`);
      return res.status(400).json({
        success: false,
        error: 'Failed to get job details from HCP'
      });
    }
    
    // Check if job has a schedule to delete
    if (!jobDetails.schedule || !jobDetails.schedule.scheduled_start) {
      console.warn(`Job ${jobId} has no schedule - nothing to delete`);
      
      // Update Airtable to reflect that there was no schedule
      // Use Service Sync Details for service status messages
      const updateFields = {
        'Service Sync Details': `Job has no schedule to delete. Already unscheduled. ${getArizonaTime()}`,
        'Sync Date and Time': getArizonaTime()
      };
      
      await base('Reservations').update(recordId, updateFields);
      
      return res.json({
        success: true,
        recordId,
        uid: reservationUID,
        jobId,
        message: 'Job has no schedule to delete - already unscheduled',
        environment: environment
      });
    }
    
    // Delete the job schedule using the only working HCP API endpoint
    try {
      await hcpFetch(hcpConfig, `/jobs/${jobId}/schedule`, 'DELETE');
      console.log(`Successfully deleted schedule for job ${jobId}`);
    } catch (error) {
      console.error(`Failed to delete job schedule: ${error.message}`);
      return res.status(400).json({
        success: false,
        error: `Failed to delete job schedule: ${error.message}`
      });
    }
    
    // Update Airtable to reflect schedule deletion
    // Use Service Sync Details for service status messages
    const updateFields = {
      'Service Sync Details': `Job schedule deleted from HCP on ${getArizonaTime()}`,
      'Sync Date and Time': getArizonaTime(),
      'Scheduled Service Time': null,
      'Service Appointment ID': null
    };
    
    await base('Reservations').update(recordId, updateFields);
    
    res.json({
      success: true,
      recordId,
      uid: reservationUID,
      jobId,
      message: 'Job schedule deleted successfully',
      environment: environment
    });
    
  } catch (error) {
    console.error('Error deleting job schedule:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

module.exports = {
  createJob,
  cancelJob
};