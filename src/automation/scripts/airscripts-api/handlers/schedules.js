const Airtable = require('airtable');
const fetch = require('node-fetch');
const { getArizonaTime, formatDate, formatTime } = require('../utils/datetime');
const { getAirtableConfig, getHCPConfig } = require('../utils/config');

// Arizona timezone constants (matching original scripts)
const AZ_TZ = 'America/Phoenix';

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

// Arizona timezone formatting helpers (matching original scripts)
const azDate = d => d.toLocaleDateString('en-US', {
  timeZone: AZ_TZ, month: 'long', day: 'numeric'
});

const azTime = d => d.toLocaleTimeString('en-US', {
  timeZone: AZ_TZ, hour: 'numeric', minute: '2-digit', hour12: true
});

// Map HCP work status to Airtable status
function mapStatus(workStatus) {
  const ws = (workStatus || '').toLowerCase();
  if (ws.includes('cancel')) return 'Canceled';
  if (ws.includes('complete')) return 'Completed';
  if (ws.includes('in_progress')) return 'In Progress';
  if (ws.includes('scheduled')) return 'Scheduled';
  if (!ws || ws.includes('unscheduled')) return 'Unscheduled';
  return null;
}

// Check all schedules (read-only verification)
async function checkSchedules(req, res) {
  try {
    // Get environment-specific config
    const environment = req.forceEnvironment || process.env.ENVIRONMENT || 'development';
    const airtableConfig = getAirtableConfig(environment);
    const hcpConfig = getHCPConfig(environment);
    const base = new Airtable({ apiKey: airtableConfig.apiKey }).base(airtableConfig.baseId);
    
    console.log(`Checking schedules in ${environment} environment`);
    
    // Query active reservations with jobs (matching original pattern)
    const records = await base('Reservations')
      .select({
        filterByFormula: 'AND({Service Job ID} != "", OR({Status} = "New", {Status} = "Modified"))',
        fields: ['Reservation UID', 'Service Job ID', 'Final Service Time', 'Same-day Turnover', 'Service Appointment ID']
      })
      .all();

    const results = [];
    let checked = 0;
    let synced = 0;
    let wrongTime = 0;
    let wrongDate = 0;
    let errors = 0;

    for (const record of records) {
      try {
        const result = await checkSingleSchedule(base, hcpConfig, record.id);
        results.push(result);
        checked++;
        
        if (result.syncStatus === 'Synced') synced++;
        else if (result.syncStatus === 'Wrong Time') wrongTime++;
        else if (result.syncStatus === 'Wrong Date') wrongDate++;
        
        // Small delay to avoid rate limits
        await delay(100);
        
      } catch (error) {
        errors++;
        results.push({
          recordId: record.id,
          uid: record.get('Reservation UID'),
          error: error.message
        });
      }
    }

    res.json({
      success: true,
      summary: {
        total: checked,
        synced,
        wrongTime,
        wrongDate,
        errors
      },
      results,
      environment: environment
    });
  } catch (error) {
    console.error('Error checking schedules:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

// Update single schedule (with fixing capability)
async function updateSchedule(req, res) {
  try {
    const { recordId } = req.params;
    
    // Get environment-specific config
    const environment = req.forceEnvironment || process.env.ENVIRONMENT || 'development';
    const airtableConfig = getAirtableConfig(environment);
    const hcpConfig = getHCPConfig(environment);
    const base = new Airtable({ apiKey: airtableConfig.apiKey }).base(airtableConfig.baseId);
    
    console.log(`Updating schedule for record ${recordId} in ${environment} environment`);
    
    const result = await updateSingleSchedule(base, hcpConfig, recordId);
    
    res.json({
      success: true,
      ...result,
      environment: environment
    });
  } catch (error) {
    console.error('Error updating schedule:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
}

// Check single schedule (read-only)
async function checkSingleSchedule(base, hcpConfig, recordId) {
  const reservation = await base('Reservations').find(recordId);
  
  const jobId = reservation.get('Service Job ID');
  const finalServiceTime = reservation.get('Final Service Time');
  const reservationUID = reservation.get('Reservation UID');
  const sameDayTurnover = reservation.get('Same-day Turnover');
  
  if (!jobId) {
    throw new Error('No Service Job ID found');
  }
  
  if (!finalServiceTime) {
    throw new Error('No Final Service Time found');
  }

  // Fetch job from HCP
  const job = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
  
  // Get current schedule
  const schedStart = job.schedule?.scheduled_start ? new Date(job.schedule.scheduled_start) : null;
  const expectedTime = new Date(finalServiceTime);
  
  if (!schedStart) {
    // No schedule exists in HCP
    const updateFields = {
      'Sync Status': 'Not Created',
      'Sync Details': 'No schedule found in HCP',
      'Sync Date and Time': getArizonaTime()
    };
    
    const atStatus = mapStatus(job.work_status);
    if (atStatus) {
      updateFields['Job Status'] = atStatus;
    }
    
    await base('Reservations').update(recordId, updateFields);
    
    return {
      recordId,
      uid: reservationUID,
      jobId,
      syncStatus: 'Not Created',
      syncDetails: 'No schedule found in HCP'
    };
  }

  // Update Scheduled Service Time from HCP
  await base('Reservations').update(recordId, {
    'Scheduled Service Time': schedStart.toISOString()
  });

  // Compare times using Arizona timezone (matching original scripts)
  const dateMatch = azDate(schedStart) === azDate(expectedTime);
  const timeMatch = azTime(schedStart) === azTime(expectedTime);

  let syncStatus, syncDetails;
  const prefix = sameDayTurnover ? 'Same‑day Turnaround. ' : '';

  if (!dateMatch) {
    syncStatus = 'Wrong Date';
    syncDetails = `${prefix}Final Service Time is **${azDate(expectedTime)}** but service is **${azDate(schedStart)}**.`;
  } else if (!timeMatch) {
    syncStatus = 'Wrong Time';
    syncDetails = `${prefix}Final Service Time is **${azTime(expectedTime)}** but service is **${azTime(schedStart)}**.`;
  } else {
    syncStatus = 'Synced';
    syncDetails = `${prefix}Service matches **${azDate(schedStart)} at ${azTime(schedStart)}**.`;
  }

  const atStatus = mapStatus(job.work_status);
  if (atStatus === 'Canceled') {
    const when = new Date(job.updated_at || Date.now());
    syncDetails = `Job canceled on ${azDate(when)} at ${azTime(when)}.`;
  }

  // Try to get appointment ID if missing
  const existingAppointmentId = reservation.get('Service Appointment ID');
  let appointmentId = existingAppointmentId;
  
  if (!appointmentId) {
    try {
      const appointments = await hcpFetch(hcpConfig, `/jobs/${jobId}/appointments`);
      if (appointments.appointments && appointments.appointments.length > 0) {
        appointmentId = appointments.appointments[0].id;
      }
    } catch (err) {
      console.error('Failed to fetch appointment ID:', err);
    }
  }

  // Update Airtable with sync status (using string format)
  const updateFields = {
    'Sync Status': syncStatus,
    'Sync Details': syncDetails,
    'Sync Date and Time': getArizonaTime()
  };

  if (atStatus) {
    updateFields['Job Status'] = atStatus;
  }

  if (appointmentId && !existingAppointmentId) {
    updateFields['Service Appointment ID'] = appointmentId;
  }

  console.log(`Attempting to update Sync Status to: "${syncStatus}"`);
  console.log('Update fields:', JSON.stringify(updateFields, null, 2));
  
  try {
    await base('Reservations').update(recordId, updateFields);
    console.log(`Successfully updated Sync Status to: "${syncStatus}"`);
  } catch (airtableError) {
    console.warn(`Airtable field error updating Sync Status "${syncStatus}":`, airtableError.message);
    
    // Update without problematic fields
    const fallbackFields = { ...updateFields };
    
    if (airtableError.message.includes('Sync Status')) {
      delete fallbackFields['Sync Status'];
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
        'Sync Date and Time': updateFields['Sync Date and Time']
      };
      
      if (updateFields['Scheduled Service Time']) {
        minimalFields['Scheduled Service Time'] = updateFields['Scheduled Service Time'];
      }
      if (updateFields['Service Appointment ID']) {
        minimalFields['Service Appointment ID'] = updateFields['Service Appointment ID'];
      }
      
      await base('Reservations').update(recordId, minimalFields);
    }
  }

  return {
    recordId,
    uid: reservationUID,
    jobId,
    appointmentId,
    syncStatus,
    syncDetails,
    scheduledTime: schedStart.toISOString()
  };
}

// Update single schedule (with automatic fixing)
async function updateSingleSchedule(base, hcpConfig, recordId) {
  const reservation = await base('Reservations').find(recordId);
  
  const jobId = reservation.get('Service Job ID');
  const finalServiceTime = reservation.get('Final Service Time');
  const reservationUID = reservation.get('Reservation UID');
  const sameDayTurnover = reservation.get('Same-day Turnover');
  
  if (!jobId) {
    throw new Error('No Service Job ID found');
  }
  
  if (!finalServiceTime) {
    throw new Error('No Final Service Time found');
  }

  // Fetch job from HCP
  const job = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
  
  const expectedTime = new Date(finalServiceTime);
  const expectedEnd = new Date(expectedTime.getTime() + 60 * 60 * 1000); // +1 hour
  
  // Check if schedule needs to be created or updated
  const schedStart = job.schedule?.scheduled_start ? new Date(job.schedule.scheduled_start) : null;
  
  let needsUpdate = false;
  let syncStatus, syncDetails;
  const prefix = sameDayTurnover ? 'Same‑day Turnaround. ' : '';

  if (!schedStart) {
    needsUpdate = true;
    syncStatus = 'Creating Schedule';
    syncDetails = `${prefix}Creating schedule for **${azDate(expectedTime)} at ${azTime(expectedTime)}**.`;
  } else {
    // Compare times using Arizona timezone
    const dateMatch = azDate(schedStart) === azDate(expectedTime);
    const timeMatch = azTime(schedStart) === azTime(expectedTime);

    if (!dateMatch) {
      needsUpdate = true;
      syncStatus = 'Updating Date';
      syncDetails = `${prefix}Updating from **${azDate(schedStart)}** to **${azDate(expectedTime)}**.`;
    } else if (!timeMatch) {
      needsUpdate = true;
      syncStatus = 'Updating Time';
      syncDetails = `${prefix}Updating from **${azTime(schedStart)}** to **${azTime(expectedTime)}**.`;
    } else {
      syncStatus = 'Synced';
      syncDetails = `${prefix}Service matches **${azDate(schedStart)} at ${azTime(schedStart)}**.`;
    }
  }

  if (needsUpdate) {
    console.log(`Schedule needs update for job ${jobId}: ${syncDetails}`);
    
    try {
      if (!schedStart) {
        // Create new schedule (matching original script pattern)
        const schedulePayload = {
          start_time: expectedTime.toISOString(),
          end_time: expectedEnd.toISOString(),
          arrival_window_in_minutes: 60,
          notify: true,
          notify_pro: true,
          dispatched_employees: [{ employee_id: hcpConfig.employeeId }]
        };
        
        console.log('Creating schedule with data:', JSON.stringify(schedulePayload, null, 2));
        await hcpFetch(hcpConfig, `/jobs/${jobId}/schedule`, 'PUT', schedulePayload);
        
      } else {
        // Update existing schedule (matching original script pattern)
        const schedulePayload = {
          start_time: expectedTime.toISOString(),
          end_time: expectedEnd.toISOString(),
          arrival_window_in_minutes: 60,
          notify: true,
          notify_pro: true,
          dispatched_employees: [{ employee_id: hcpConfig.employeeId }]
        };
        
        console.log('Updating schedule with data:', JSON.stringify(schedulePayload, null, 2));
        await hcpFetch(hcpConfig, `/jobs/${jobId}/schedule`, 'PUT', schedulePayload);
      }
      
      // Give HCP time to process the update
      await delay(1000);
      
      // Re-fetch job to get updated schedule
      const updatedJob = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
      const newScheduledTime = new Date(updatedJob.schedule.scheduled_start);
      
      syncStatus = 'Synced';
      syncDetails = `${prefix}Service updated to **${azDate(newScheduledTime)} at ${azTime(newScheduledTime)}**.`;
      
      console.log(`Schedule successfully updated for job ${jobId}`);
      
    } catch (error) {
      console.error('Failed to update schedule:', error);
      syncStatus = 'Failed';
      syncDetails = `${prefix}Failed to update schedule: ${error.message}`;
    }
  }

  // Fetch final job state
  const finalJob = await hcpFetch(hcpConfig, `/jobs/${jobId}`);
  const finalScheduledTime = finalJob.schedule?.scheduled_start ? new Date(finalJob.schedule.scheduled_start) : null;
  
  // Try to get appointment ID if missing
  const existingAppointmentId = reservation.get('Service Appointment ID');
  let appointmentId = existingAppointmentId;
  
  if (!appointmentId) {
    try {
      const appointments = await hcpFetch(hcpConfig, `/jobs/${jobId}/appointments`);
      if (appointments.appointments && appointments.appointments.length > 0) {
        appointmentId = appointments.appointments[0].id;
      }
    } catch (err) {
      console.error('Failed to fetch appointment ID:', err);
    }
  }

  // Update Airtable with final state (using string format)
  const updateFields = {
    'Sync Status': syncStatus,
    'Sync Details': syncDetails,
    'Sync Date and Time': getArizonaTime()
  };

  if (finalScheduledTime) {
    updateFields['Scheduled Service Time'] = finalScheduledTime.toISOString();
  }

  const atStatus = mapStatus(finalJob.work_status);
  if (atStatus) {
    updateFields['Job Status'] = atStatus;
  }

  if (appointmentId && !existingAppointmentId) {
    updateFields['Service Appointment ID'] = appointmentId;
  }

  console.log(`Attempting to update Sync Status to: "${syncStatus}"`);
  console.log('Update fields:', JSON.stringify(updateFields, null, 2));
  
  try {
    await base('Reservations').update(recordId, updateFields);
    console.log(`Successfully updated Sync Status to: "${syncStatus}"`);
  } catch (airtableError) {
    console.warn(`Airtable field error updating Sync Status "${syncStatus}":`, airtableError.message);
    
    // Update without problematic fields
    const fallbackFields = { ...updateFields };
    
    if (airtableError.message.includes('Sync Status')) {
      delete fallbackFields['Sync Status'];
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
        'Sync Date and Time': updateFields['Sync Date and Time']
      };
      
      if (updateFields['Scheduled Service Time']) {
        minimalFields['Scheduled Service Time'] = updateFields['Scheduled Service Time'];
      }
      if (updateFields['Service Appointment ID']) {
        minimalFields['Service Appointment ID'] = updateFields['Service Appointment ID'];
      }
      
      await base('Reservations').update(recordId, minimalFields);
    }
  }

  return {
    recordId,
    uid: reservationUID,
    jobId,
    appointmentId,
    syncStatus,
    syncDetails,
    scheduledTime: finalScheduledTime ? finalScheduledTime.toISOString() : null,
    wasUpdated: needsUpdate
  };
}

module.exports = {
  checkSchedules,
  updateSchedule
};