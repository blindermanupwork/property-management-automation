/**
 * Real Data Service for Property Management App
 * Fetches real data from development Airtable and HousecallPro via MCP
 */

class RealDataService {
  constructor() {
    // This would be implemented as a backend API that uses MCP
    // For now, we'll return transformed real data
  }

  // Transform Airtable reservation data to app format
  transformAirtableReservation(airtableRecord) {
    const fields = airtableRecord.fields
    
    return {
      id: airtableRecord.id,
      reservationUID: fields['Reservation UID'] || '',
      property: fields['HCP Address (from Property ID)'] ? fields['HCP Address (from Property ID)'][0] : 'Unknown Address',
      guest: fields['Full Name (from HCP Customer ID) (from Property ID)'] ? fields['Full Name (from HCP Customer ID) (from Property ID)'][0] : 'Unknown Guest',
      checkin: fields['Check-in Date'] || '',
      checkout: fields['Check-out Date'] || '',
      status: this.mapAirtableStatus(fields['Status']),
      jobType: fields['Service Type'] || 'Unknown',
      hcpJobId: fields['Service Job ID'] || null,
      syncStatus: fields['Sync Status'] || 'Unknown',
      serviceTime: fields['Final Service Time'] || fields['Scheduled Service Time'] || '',
      assignee: fields['Assignee'] || null,
      notes: fields['Service Line Description'] || '',
      entrySource: fields['Entry Source'] || '',
      entryType: fields['Entry Type'] || '',
      lastUpdated: fields['Last Updated'] || ''
    }
  }

  // Transform HCP job data to app format
  transformHCPJob(hcpJob) {
    return {
      id: hcpJob.id,
      invoiceNumber: hcpJob.invoice_number,
      description: hcpJob.description,
      customer: hcpJob.customer,
      address: hcpJob.address,
      workStatus: hcpJob.work_status,
      scheduledStart: hcpJob.schedule?.scheduled_start,
      scheduledEnd: hcpJob.schedule?.scheduled_end,
      totalAmount: hcpJob.total_amount / 100, // Convert cents to dollars
      outstandingBalance: hcpJob.outstanding_balance / 100,
      assignedEmployees: hcpJob.assigned_employees || [],
      jobType: hcpJob.job_fields?.job_type?.name || 'Unknown',
      workTimestamps: hcpJob.work_timestamps,
      createdAt: hcpJob.created_at,
      updatedAt: hcpJob.updated_at
    }
  }

  // Map Airtable status to app status
  mapAirtableStatus(airtableStatus) {
    switch (airtableStatus?.toLowerCase()) {
      case 'new':
        return 'scheduled'
      case 'old':
      case 'removed':
        return 'completed'
      default:
        return 'scheduled'
    }
  }

  // Map HCP work status to app status
  mapHCPStatus(hcpStatus) {
    switch (hcpStatus?.toLowerCase()) {
      case 'scheduled':
        return 'scheduled'
      case 'in_progress':
        return 'in_progress'
      case 'completed':
        return 'completed'
      case 'canceled':
        return 'cancelled'
      default:
        return 'scheduled'
    }
  }

  // Combine Airtable and HCP data
  combineReservationData(airtableRecord, hcpJob = null) {
    const baseData = this.transformAirtableReservation(airtableRecord)
    
    if (hcpJob) {
      const hcpData = this.transformHCPJob(hcpJob)
      return {
        ...baseData,
        hcpJobId: hcpJob.id,
        status: this.mapHCPStatus(hcpJob.work_status),
        totalCost: hcpData.totalAmount,
        employeeAssigned: hcpData.assignedEmployees.length > 0 ? 
          `${hcpData.assignedEmployees[0].first_name} ${hcpData.assignedEmployees[0].last_name}` : null,
        scheduledStart: hcpData.scheduledStart,
        scheduledEnd: hcpData.scheduledEnd,
        workTimestamps: hcpData.workTimestamps
      }
    }

    return {
      ...baseData,
      totalCost: this.estimateJobCost(baseData.jobType),
      employeeAssigned: null
    }
  }

  // Estimate job cost based on type
  estimateJobCost(jobType) {
    switch (jobType?.toLowerCase()) {
      case 'turnover':
        return 250.00
      case 'needs review':
        return 200.00
      default:
        return 150.00
    }
  }

  // Get real reservation data (this would call MCP in a real backend)
  async getRealReservations() {
    // Sample of real transformed data based on your actual Airtable records
    return [
      {
        id: "rec06uaETwXIatgWa",
        reservationUID: "14618322",
        property: "3551 E Terrace Ave, Gilbert, AZ, 85234, US",
        guest: "Chad Jenkins",
        checkin: "2025-06-19",
        checkout: "2025-06-26",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: "job_4711673fa7ce464ea7934d7207e5d95a",
        totalCost: 274.00,
        employeeAssigned: "Laundry User",
        notes: "Turnover STR Next Guest June 27",
        entrySource: "Evolve",
        entryType: "Reservation",
        serviceTime: "2025-06-26T17:15:00.000Z",
        syncStatus: "Synced",
        lastUpdated: "2025-06-04T17:37:29.000Z"
      },
      {
        id: "rec09Xmb9DO3yYTzW",
        reservationUID: "695b24f5-c3a7-4cd0-aac3-3c7d66e4e83e",
        property: "2824 N 82nd St, Scottsdale, AZ, 85257, US",
        guest: "Teresa Mayes",
        checkin: "2025-05-22",
        checkout: "2025-05-25",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: null,
        totalCost: 250.00,
        employeeAssigned: null,
        notes: "Turnover STR Next Guest May 30",
        entrySource: "Lodgify",
        entryType: "Reservation",
        serviceTime: "2025-05-25T17:15:00.000Z",
        syncStatus: "Not Created",
        lastUpdated: "2025-06-08T11:11:24.000Z"
      },
      {
        id: "rec0CB1Jpc7aBI7SH",
        reservationUID: "e591777a-775b-4086-8bb8-bcb18b670e00",
        property: "2824 N 82nd St, Scottsdale, AZ, 85257, US",
        guest: "Teresa Mayes",
        checkin: "2025-04-10",
        checkout: "2025-04-13",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: null,
        totalCost: 250.00,
        employeeAssigned: null,
        notes: "Turnover STR Next Guest April 27",
        entrySource: "Lodgify",
        entryType: "Reservation",
        serviceTime: "2025-04-13T17:15:00.000Z",
        syncStatus: "Not Created",
        lastUpdated: "2025-05-25T15:57:36.000Z"
      },
      {
        id: "rec0G5DimeZ3dlX8k",
        reservationUID: "7f662ec65913-3da301408831abb095d757f14cecd3a6@airbnb.com",
        property: "5921 E Sweetwater Ave, Scottsdale, AZ, 85254, US",
        guest: "Tyler Grady",
        checkin: "2025-05-22",
        checkout: "2025-05-23",
        status: "scheduled",
        jobType: "Needs Review",
        hcpJobId: null,
        totalCost: 200.00,
        employeeAssigned: null,
        notes: "Block entry requires review",
        entrySource: "Airbnb",
        entryType: "Block",
        serviceTime: "2025-05-23T17:15:00.000Z",
        syncStatus: "Not Created",
        lastUpdated: "2025-05-24T23:46:13.000Z"
      },
      {
        id: "rec0H56EnWVZoOkAC",
        reservationUID: "5bc99d4b-5ca0-4544-88e7-0aa801e602fe",
        property: "1377 E Detroit St, Chandler AZ 85225",
        guest: "Ashley Pritchett",
        checkin: "2025-05-29",
        checkout: "2025-06-12",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: null,
        totalCost: 250.00,
        employeeAssigned: null,
        notes: "Turnover STR Next Guest June 15",
        entrySource: "HostTools",
        entryType: "Reservation",
        serviceTime: "2025-06-12T17:15:00.000Z",
        syncStatus: "Not Created",
        lastUpdated: "2025-06-05T23:11:30.000Z"
      },
      {
        id: "rec02iBSCbGxONaDx",
        reservationUID: "7f662ec65913-8b0a21ff798d93d0c0e285592800f8b7@airbnb.com",
        property: "7625 E Camelback Rd 346B, Scottsdale AZ 85251",
        guest: "Erfan Haroon",
        checkin: "2025-05-31",
        checkout: "2025-06-05",
        status: "completed",
        jobType: "Needs Review",
        hcpJobId: null,
        totalCost: 200.00,
        employeeAssigned: null,
        notes: "Needs Review STR Next Guest June 9",
        entrySource: "Airbnb",
        entryType: "Block",
        serviceTime: "2025-06-05T17:15:00.000Z",
        syncStatus: "Not Created",
        lastUpdated: "2025-06-04T19:09:12.000Z"
      },
      {
        id: "rec03oQpf1MHmoIz8",
        reservationUID: "7f662ec65913-e54919f570c8fa25068ff296fb1fc824@airbnb.com",
        property: "1604 E Windjammer Way, Tempe, AZ, 85283, US",
        guest: "Alexander Drachev",
        checkin: "2025-06-03",
        checkout: "2025-06-13",
        status: "completed",
        jobType: "Needs Review",
        hcpJobId: null,
        totalCost: 200.00,
        employeeAssigned: null,
        notes: "Needs Review STR Next Guest Unknown",
        entrySource: "Airbnb",
        entryType: "Block",
        serviceTime: "2025-06-13T17:15:00.000Z",
        syncStatus: "Not Created",
        lastUpdated: "2025-06-06T03:11:32.000Z"
      },
      // Add some with HCP jobs for variety
      {
        id: "hcp_job_e623f77847224586b0b4352049caaf55",
        reservationUID: "HCP-Generated",
        property: "825 W Monterey Pl, Chandler, AZ, 85225, US",
        guest: "Ashley Pritchett",
        checkin: "2025-06-13",
        checkout: "2025-06-13",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: "job_e623f77847224586b0b4352049caaf55",
        totalCost: 274.00,
        employeeAssigned: "Laundry User",
        notes: "Turnover STR Next Guest Unknown. Contact: jacob@_hcp_devtesting.test",
        entrySource: "HousecallPro",
        entryType: "Direct Job",
        serviceTime: "2025-06-13T17:15:00Z",
        syncStatus: "Active HCP Job",
        lastUpdated: "2025-06-09T07:13:53Z"
      },
      {
        id: "hcp_job_5c0b62f3f8174541b8a85c31cb1733b5",
        reservationUID: "HCP-Generated",
        property: "1652 E Tulsa St, Chandler, AZ, 85225, US",
        guest: "Annie Schwartz",
        checkin: "2025-06-25",
        checkout: "2025-06-25",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: "job_5c0b62f3f8174541b8a85c31cb1733b5",
        totalCost: 210.54,
        employeeAssigned: "Laundry User",
        notes: "Turnover STR Next Guest Unknown. Contact: annies3jnp@_hcp_devtesting.test",
        entrySource: "HousecallPro",
        entryType: "Direct Job",
        serviceTime: "2025-06-25T17:15:00Z",
        syncStatus: "Active HCP Job",
        lastUpdated: "2025-06-09T07:13:46Z"
      },
      {
        id: "hcp_job_4d17d1c15bf9417086d9178ae19b9863",
        reservationUID: "HCP-Generated",
        property: "2824 N 82nd St, Scottsdale, AZ, 85257, US",
        guest: "Teresa Mayes",
        checkin: "2025-06-09",
        checkout: "2025-06-09",
        status: "scheduled",
        jobType: "Turnover",
        hcpJobId: "job_4d17d1c15bf9417086d9178ae19b9863",
        totalCost: 285.00,
        employeeAssigned: "Laundry User",
        notes: "Turnover STR Next Guest Unknown. Contact: teresamayes24@_hcp_devtesting.test",
        entrySource: "HousecallPro",
        entryType: "Direct Job",
        serviceTime: "2025-06-09T17:15:00Z",
        syncStatus: "Active HCP Job",
        lastUpdated: "2025-06-09T07:13:45Z"
      }
    ]
  }

  // Search and filter real reservations
  async searchReservations(query = '', userEmail = null) {
    const allReservations = await this.getRealReservations()
    
    let filteredReservations = allReservations

    // Apply user email filtering
    if (userEmail) {
      filteredReservations = allReservations.filter(reservation => {
        return reservation.notes.toLowerCase().includes(userEmail.toLowerCase()) ||
               reservation.guest.toLowerCase().includes(userEmail.split('@')[0].toLowerCase())
      })
      
      // If no matches found for the email, return empty array
      if (filteredReservations.length === 0) {
        throw new Error('User not found in system. No reservations available for your email.')
      }
    }

    // Apply text search if provided
    if (query && query.trim()) {
      const searchTerm = query.toLowerCase()
      filteredReservations = filteredReservations.filter(reservation =>
        reservation.guest.toLowerCase().includes(searchTerm) ||
        reservation.property.toLowerCase().includes(searchTerm) ||
        reservation.jobType.toLowerCase().includes(searchTerm) ||
        reservation.entrySource.toLowerCase().includes(searchTerm) ||
        reservation.notes.toLowerCase().includes(searchTerm) ||
        (reservation.employeeAssigned && reservation.employeeAssigned.toLowerCase().includes(searchTerm))
      )
    }

    return filteredReservations
  }
}

export default new RealDataService()