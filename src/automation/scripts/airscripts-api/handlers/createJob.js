import { getHCPClient } from '../services/hcp.js';
import { getAirtableClient } from '../services/airtable.js';
import { logger } from '../utils/logger.js';
import { validateCreateJobRequest } from '../validators/index.js';

// Arizona timezone helpers
const AZ_TZ = "America/Phoenix";
const azDate = d => d.toLocaleDateString("en-US", {
  timeZone: AZ_TZ, month: "long", day: "numeric"
});
const azTime = d => d.toLocaleTimeString("en-US", {
  timeZone: AZ_TZ, hour: "numeric", minute: "2-digit", hour12: true
});

export async function createJob(req, res) {
  try {
    // Validate request
    const { error, value } = validateCreateJobRequest(req.body);
    if (error) {
      return res.status(400).json({ 
        error: 'Invalid request', 
        details: error.details 
      });
    }
    
    const { recordId, baseId } = value;
    logger.info('Creating job', { recordId, baseId });
    
    // Initialize clients
    const airtable = getAirtableClient();
    const hcp = getHCPClient();
    const base = airtable.base(baseId);
    
    // Fetch reservation record
    const reservation = await base('Reservations').find(recordId);
    const reservationUID = reservation.fields['Reservation UID'] || recordId;
    
    // Check if job already exists
    const existingJobId = reservation.fields['Service Job ID'];
    if (existingJobId) {
      logger.warn('Job already exists', { reservationUID, jobId: existingJobId });
      return res.json({ 
        success: true, 
        jobId: existingJobId,
        message: 'Job already exists'
      });
    }
    
    // Get Final Service Time
    const finalServiceTime = reservation.fields['Final Service Time'];
    if (!finalServiceTime) {
      return res.status(400).json({ 
        error: 'No Final Service Time set for this reservation' 
      });
    }
    
    const finalTime = new Date(finalServiceTime);
    const schedStart = finalTime;
    const schedEnd = new Date(finalTime.getTime() + 60 * 60 * 1000);
    
    // Get property details
    const propertyLinks = reservation.fields['Property ID'] || [];
    if (!propertyLinks.length) {
      return res.status(400).json({ 
        error: 'No linked property' 
      });
    }
    
    const property = await base('Properties').find(propertyLinks[0].id);
    
    // Get HCP Customer ID
    const custLinks = property.fields['HCP Customer ID'] || [];
    let custId = '';
    if (custLinks.length) {
      const custRecordId = typeof custLinks[0] === 'object' ? custLinks[0].id : custLinks[0];
      const custRecord = await base('Customers').find(custRecordId);
      custId = custRecord.fields['HCP Customer ID'];
    }
    
    const addrId = property.fields['HCP Address ID'];
    
    if (!custId || !addrId) {
      return res.status(400).json({ 
        error: 'Property missing HCP Customer ID or Address ID' 
      });
    }
    
    // Determine service type and template
    const serviceTypeObj = reservation.fields['Service Type'];
    const serviceType = serviceTypeObj?.name || 'Turnover';
    const sameDayTurnover = reservation.fields['Same-day Turnover'];
    
    let templateId, jobTypeId;
    
    if (serviceType === 'Return Laundry') {
      templateId = property.fields['Return Laundry Job Template ID'];
      jobTypeId = "jbt_01d29f7695404f5bb57ed7e8c5708afc";
    } else if (serviceType === 'Inspection') {
      templateId = property.fields['Inspection Job Template ID'];
      jobTypeId = "jbt_7234d0af0a734f10bf155d2238cf92b7";
    } else {
      templateId = property.fields['Turnover Job Template ID'];
      jobTypeId = "jbt_3744a354599d4d2fa54041a4cda4bd13";
    }
    
    if (!templateId) {
      return res.status(400).json({ 
        error: `No template found for ${serviceType} service type` 
      });
    }
    
    // Create HCP job
    const jobData = await hcp.createJob({
      invoice_number: 0,
      customer_id: custId,
      address_id: addrId,
      schedule: { 
        scheduled_start: schedStart.toISOString(), 
        scheduled_end: schedEnd.toISOString(), 
        arrival_window: 0 
      },
      assigned_employee_ids: [process.env.HCP_DEFAULT_EMPLOYEE_ID || "pro_78945c979905480996c6c85d7a925eb9"],
      line_items: [],
      job_fields: { job_type_id: jobTypeId }
    });
    
    const jobId = jobData.id;
    
    // Copy template line items
    const templateItems = await hcp.getJobLineItems(templateId);
    
    // Determine service name
    let serviceName;
    const customServiceLine = reservation.fields['Custom Service Line Description'];
    
    if (customServiceLine?.trim()) {
      serviceName = customServiceLine.trim();
    } else if (sameDayTurnover) {
      serviceName = `${serviceType} STR SAME DAY`;
    } else {
      // Find next reservation logic here...
      serviceName = `${serviceType} STR Next Guest Unknown`;
    }
    
    // Update line items
    await hcp.updateJobLineItems(jobId, 
      templateItems.map((item, i) => ({
        name: i === 0 ? serviceName : item.name,
        description: item.description || '',
        unit_price: item.unit_price,
        unit_cost: item.unit_cost,
        quantity: item.quantity,
        kind: item.kind,
        taxable: item.taxable,
        service_item_id: item.service_item_id || null,
        service_item_type: item.service_item_type || null
      }))
    );
    
    // Get appointment ID
    let appointmentId = null;
    try {
      const jobDetails = await hcp.getJob(jobId);
      if (jobDetails.appointments?.length > 0) {
        appointmentId = jobDetails.appointments[0].id;
      }
    } catch (err) {
      logger.warn('Failed to get appointment ID', { jobId, error: err.message });
    }
    
    // Update Airtable record
    const updateFields = {
      'Service Job ID': jobId,
      'Job Creation Time': new Date().toISOString()
    };
    
    if (appointmentId) {
      updateFields['Service Appointment ID'] = appointmentId;
    }
    
    await base('Reservations').update(recordId, updateFields);
    
    // Sync status
    await syncJobStatus(base, reservation, jobId, finalTime, sameDayTurnover);
    
    logger.info('Job created successfully', { 
      reservationUID, 
      jobId, 
      appointmentId 
    });
    
    res.json({ 
      success: true, 
      jobId,
      appointmentId,
      message: `Job ${jobId} created successfully`
    });
    
  } catch (error) {
    logger.error('Error creating job', { error: error.message, stack: error.stack });
    res.status(500).json({ 
      error: 'Failed to create job', 
      details: error.message 
    });
  }
}

async function syncJobStatus(base, reservation, jobId, expectedTime, sameDayTurnover) {
  const hcp = getHCPClient();
  const job = await hcp.getJob(jobId);
  
  const schedStart = new Date(job.schedule.scheduled_start);
  const prefix = sameDayTurnover ? 'Same-day Turnaround. ' : '';
  
  let syncStatus, syncDetails;
  
  if (expectedTime.toDateString() !== schedStart.toDateString()) {
    syncStatus = 'Wrong Date';
    syncDetails = `${prefix}Final Service Time is ${azDate(expectedTime)} but service is ${azDate(schedStart)}.`;
  } else if (expectedTime.getHours() !== schedStart.getHours() || 
             expectedTime.getMinutes() !== schedStart.getMinutes()) {
    syncStatus = 'Wrong Time';
    syncDetails = `${prefix}Final Service Time is ${azTime(expectedTime)} but service is ${azTime(schedStart)}.`;
  } else {
    syncStatus = 'Synced';
    syncDetails = `${prefix}Service matches ${azDate(schedStart)} at ${azTime(schedStart)}.`;
  }
  
  const statusMap = {
    'unscheduled': 'Unscheduled',
    'scheduled': 'Scheduled',
    'in_progress': 'In Progress',
    'completed': 'Completed',
    'canceled': 'Canceled'
  };
  
  const jobStatus = statusMap[job.work_status?.toLowerCase()] || null;
  
  const updates = {
    'Scheduled Service Time': schedStart.toISOString(),
    'Sync Status': { name: syncStatus },
    'Sync Details': syncDetails,
    'Sync Date and Time': new Date().toISOString()
  };
  
  if (jobStatus) {
    updates['Job Status'] = { name: jobStatus };
  }
  
  await base('Reservations').update(reservation.id, updates);
}