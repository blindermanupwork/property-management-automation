import { Reservation, Property, Guest, Job, Employee, JobLineItem } from '../types'

// Mock Properties
export const mockProperties: Property[] = [
  {
    id: 'prop_001',
    name: 'Mevawala Desert Villa',
    address: {
      street: '26208 N 43rd Place',
      city: 'Phoenix',
      state: 'AZ',
      zipCode: '85050',
      fullAddress: '26208 N 43rd Place, Phoenix, AZ 85050'
    },
    coordinates: {
      latitude: 33.6846,
      longitude: -111.9703
    },
    isActive: true,
    createdAt: '2024-01-15T08:00:00Z',
    updatedAt: '2025-01-15T10:30:00Z'
  },
  {
    id: 'prop_002',
    name: 'Scottsdale Mountain Retreat',
    address: {
      street: '15742 E Desert Trail',
      city: 'Scottsdale',
      state: 'AZ',
      zipCode: '85262',
      fullAddress: '15742 E Desert Trail, Scottsdale, AZ 85262'
    },
    coordinates: {
      latitude: 33.4942,
      longitude: -111.9261
    },
    isActive: true,
    createdAt: '2024-02-10T09:15:00Z',
    updatedAt: '2025-01-10T14:20:00Z'
  },
  {
    id: 'prop_003',
    name: 'Paradise Valley Oasis',
    address: {
      street: '5821 E Lincoln Drive',
      city: 'Paradise Valley',
      state: 'AZ',
      zipCode: '85253',
      fullAddress: '5821 E Lincoln Drive, Paradise Valley, AZ 85253'
    },
    coordinates: {
      latitude: 33.5331,
      longitude: -111.9738
    },
    isActive: true,
    createdAt: '2024-03-05T11:45:00Z',
    updatedAt: '2025-01-08T16:10:00Z'
  }
]

// Mock Employees
export const mockEmployees: Employee[] = [
  {
    id: 'emp_001',
    fullName: 'Maria Rodriguez',
    firstName: 'Maria',
    lastName: 'Rodriguez',
    email: 'maria@servativ.com',
    phone: '(602) 555-0123',
    role: 'cleaner',
    isActive: true,
    colorHex: '#3B82F6',
    createdAt: '2024-01-20T09:00:00Z',
    updatedAt: '2025-01-15T11:30:00Z'
  },
  {
    id: 'emp_002',
    fullName: 'James Wilson',
    firstName: 'James',
    lastName: 'Wilson',
    email: 'james@servativ.com',
    phone: '(602) 555-0124',
    role: 'supervisor',
    isActive: true,
    colorHex: '#10B981',
    createdAt: '2024-01-25T10:30:00Z',
    updatedAt: '2025-01-12T09:45:00Z'
  }
]

// Mock Job Line Items
export const mockLineItems: JobLineItem[] = [
  {
    id: 'li_001',
    name: 'Standard Cleaning Service',
    description: 'Complete house cleaning including all rooms',
    quantity: 1,
    unitPrice: 12500, // $125.00 in cents
    unitCost: 8000,   // $80.00 in cents
    totalPrice: 12500,
    kind: 'service',
    taxable: true
  },
  {
    id: 'li_002',
    name: 'Premium Towels (Set of 4)',
    description: 'High-quality cotton towels',
    quantity: 2,
    unitPrice: 2500,  // $25.00 in cents
    unitCost: 1500,   // $15.00 in cents
    totalPrice: 5000, // $50.00 in cents
    kind: 'product',
    taxable: true
  },
  {
    id: 'li_003',
    name: 'Eco-Friendly Cleaning Supplies',
    description: 'Green cleaning products used during service',
    quantity: 1,
    unitPrice: 1500,  // $15.00 in cents
    unitCost: 800,    // $8.00 in cents
    totalPrice: 1500,
    kind: 'product',
    taxable: true
  }
]

// Mock Jobs
export const mockJobs: Job[] = [
  {
    id: 'job_001',
    hcpJobId: 'hcp_job_001',
    workStatus: 'scheduled',
    description: 'Post-checkout cleaning for upcoming guest',
    totalPrice: 19000, // $190.00 in cents
    lineItems: mockLineItems,
    assignedEmployees: [mockEmployees[0]],
    scheduledStart: '2025-06-08T14:00:00Z',
    scheduledEnd: '2025-06-08T17:00:00Z',
    workTimestamps: {
      created: '2025-06-07T10:00:00Z',
      assigned: '2025-06-07T11:30:00Z'
    },
    customInstructions: 'Extra attention to kitchen and bathrooms. Guest mentioned preference for lavender scent.',
    createdAt: '2025-06-07T10:00:00Z',
    updatedAt: '2025-06-07T11:30:00Z'
  },
  {
    id: 'job_002',
    hcpJobId: 'hcp_job_002',
    workStatus: 'in_progress',
    description: 'Deep cleaning service',
    totalPrice: 15000, // $150.00 in cents
    lineItems: [mockLineItems[0]],
    assignedEmployees: [mockEmployees[1]],
    scheduledStart: '2025-06-08T10:00:00Z',
    scheduledEnd: '2025-06-08T13:00:00Z',
    workTimestamps: {
      created: '2025-06-06T15:00:00Z',
      assigned: '2025-06-06T16:00:00Z',
      started: '2025-06-08T10:05:00Z'
    },
    createdAt: '2025-06-06T15:00:00Z',
    updatedAt: '2025-06-08T10:05:00Z'
  }
]

// Mock Guests
export const mockGuests: Guest[] = [
  {
    id: 'guest_001',
    fullName: 'Sarah Johnson',
    firstName: 'Sarah',
    lastName: 'Johnson',
    email: 'sarah.johnson@email.com',
    phone: '(555) 123-4567',
    emergencyContact: {
      name: 'Michael Johnson',
      phone: '(555) 123-4568',
      relationship: 'Spouse'
    }
  },
  {
    id: 'guest_002',
    fullName: 'Robert Chen',
    firstName: 'Robert',
    lastName: 'Chen',
    email: 'rchen@techcorp.com',
    phone: '(555) 987-6543'
  },
  {
    id: 'guest_003',
    fullName: 'Emily Davis',
    firstName: 'Emily',
    lastName: 'Davis',
    email: 'emily.davis@university.edu',
    phone: '(555) 246-8135'
  }
]

// Mock Reservations
export const mockReservations: Reservation[] = [
  {
    id: 'res_001',
    propertyId: 'prop_001',
    property: mockProperties[0],
    guest: mockGuests[0],
    checkIn: '2025-06-10T16:00:00Z',
    checkOut: '2025-06-15T11:00:00Z',
    duration: 5,
    numberOfGuests: {
      adults: 2,
      children: 1
    },
    status: 'confirmed',
    source: 'Airbnb',
    bookingReference: 'ABB123456789',
    job: mockJobs[0],
    serviceInstructions: 'Please use eco-friendly products only. Guest is allergic to strong fragrances.',
    specialRequests: [
      'Extra towels for pool area',
      'Stock fridge with complimentary beverages',
      'Ensure all windows are clean for mountain views'
    ],
    notes: 'VIP guest - returning customer with excellent reviews',
    createdAt: '2025-05-15T09:30:00Z',
    updatedAt: '2025-06-07T11:30:00Z'
  },
  {
    id: 'res_002',
    propertyId: 'prop_002',
    property: mockProperties[1],
    guest: mockGuests[1],
    checkIn: '2025-06-08T15:00:00Z',
    checkOut: '2025-06-12T10:00:00Z',
    duration: 4,
    numberOfGuests: {
      adults: 1,
      children: 0
    },
    status: 'checked_in',
    source: 'VRBO',
    bookingReference: 'VRBO987654321',
    job: mockJobs[1],
    serviceInstructions: 'Business traveler - minimal disruption preferred.',
    specialRequests: [
      'Early morning cleaning (before 8 AM)',
      'Extra coffee and tea supplies'
    ],
    createdAt: '2025-05-20T14:15:00Z',
    updatedAt: '2025-06-08T10:05:00Z'
  },
  {
    id: 'res_003',
    propertyId: 'prop_003',
    property: mockProperties[2],
    guest: mockGuests[2],
    checkIn: '2025-06-12T16:00:00Z',
    checkOut: '2025-06-16T11:00:00Z',
    duration: 4,
    numberOfGuests: {
      adults: 3,
      children: 2
    },
    status: 'pending',
    source: 'Booking.com',
    bookingReference: 'BDC456789123',
    serviceInstructions: 'Family with young children - child-safe cleaning products required.',
    specialRequests: [
      'Extra linens for sofa bed',
      'Child safety locks check',
      'Pool area safety inspection'
    ],
    createdAt: '2025-05-25T16:45:00Z',
    updatedAt: '2025-06-01T12:20:00Z'
  },
  {
    id: 'res_004',
    propertyId: 'prop_001',
    property: mockProperties[0],
    guest: {
      id: 'guest_004',
      fullName: 'The Smith Family',
      firstName: 'John',
      lastName: 'Smith',
      email: 'smithfamily@email.com',
      phone: '(555) 369-2580'
    },
    checkIn: '2025-06-20T16:00:00Z',
    checkOut: '2025-06-27T11:00:00Z',
    duration: 7,
    numberOfGuests: {
      adults: 4,
      children: 3
    },
    status: 'confirmed',
    source: 'Direct Booking',
    bookingReference: 'DIR789012345',
    job: {
      id: 'job_003',
      hcpJobId: 'hcp_job_003',
      workStatus: 'unscheduled',
      description: 'Thorough cleaning before large family arrival',
      totalPrice: 25000, // $250.00 in cents
      lineItems: [
        {
          ...mockLineItems[0],
          quantity: 2,
          totalPrice: 25000
        },
        mockLineItems[1]
      ],
      scheduledStart: '2025-06-20T12:00:00Z',
      scheduledEnd: '2025-06-20T16:00:00Z',
      createdAt: '2025-06-05T09:00:00Z',
      updatedAt: '2025-06-05T09:00:00Z'
    },
    serviceInstructions: 'Large family group - extra thorough cleaning required. Focus on common areas.',
    specialRequests: [
      'Extra bedding for all rooms',
      'Stock kitchen with basic supplies',
      'Ensure outdoor furniture is clean',
      'Check all appliances are working'
    ],
    notes: 'Annual family reunion - important booking',
    createdAt: '2025-05-10T11:20:00Z',
    updatedAt: '2025-06-05T09:00:00Z'
  },
  {
    id: 'res_005',
    propertyId: 'prop_002',
    property: mockProperties[1],
    guest: {
      id: 'guest_005',
      fullName: 'Dr. Amanda Wilson',
      firstName: 'Amanda',
      lastName: 'Wilson',
      email: 'a.wilson@medicalcenter.org',
      phone: '(555) 147-2589'
    },
    checkIn: '2025-06-25T15:00:00Z',
    checkOut: '2025-06-29T10:00:00Z',
    duration: 4,
    numberOfGuests: {
      adults: 2,
      children: 0
    },
    status: 'confirmed',
    source: 'Airbnb',
    bookingReference: 'ABB987123456',
    job: {
      id: 'job_004',
      hcpJobId: 'hcp_job_004',
      workStatus: 'completed',
      description: 'Post-checkout deep clean',
      totalPrice: 18000, // $180.00 in cents
      lineItems: mockLineItems,
      assignedEmployees: [mockEmployees[0]],
      scheduledStart: '2025-06-24T10:00:00Z',
      scheduledEnd: '2025-06-24T14:00:00Z',
      workTimestamps: {
        created: '2025-06-20T14:00:00Z',
        assigned: '2025-06-21T09:00:00Z',
        started: '2025-06-24T10:00:00Z',
        completed: '2025-06-24T13:45:00Z'
      },
      createdAt: '2025-06-20T14:00:00Z',
      updatedAt: '2025-06-24T13:45:00Z'
    },
    serviceInstructions: 'Medical professional - high cleanliness standards expected.',
    specialRequests: [
      'Sanitize all surfaces thoroughly',
      'Fresh linens and towels',
      'Check medical emergency information is posted'
    ],
    createdAt: '2025-05-30T08:45:00Z',
    updatedAt: '2025-06-24T13:45:00Z'
  }
]

// Mock API responses for development
export const mockApiResponses = {
  // Simulate API delay
  delay: (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Search reservations
  searchReservations: async (query: string) => {
    await mockApiResponses.delay()
    return mockReservations.filter(reservation =>
      reservation.property.name.toLowerCase().includes(query.toLowerCase()) ||
      reservation.guest.fullName.toLowerCase().includes(query.toLowerCase()) ||
      reservation.property.address.city.toLowerCase().includes(query.toLowerCase())
    )
  },
  
  // Get reservation by ID
  getReservation: async (id: string) => {
    await mockApiResponses.delay()
    return mockReservations.find(r => r.id === id) || null
  },
  
  // Send magic link (simulated)
  sendMagicLink: async (email: string) => {
    await mockApiResponses.delay(1000)
    console.log(`Magic link sent to: ${email}`)
    return { success: true, message: 'Magic link sent successfully' }
  },
  
  // Submit request (simulated)
  submitRequest: async (reservationId: string, type: 'late-checkout' | 'custom-cleaning', details: any) => {
    await mockApiResponses.delay(800)
    console.log(`Request submitted for reservation ${reservationId}:`, { type, details })
    return { success: true, message: 'Request submitted successfully' }
  }
}

// Export helper functions for filtering data
export const filterHelpers = {
  // Filter reservations by status
  byStatus: (reservations: Reservation[], status: string) => {
    switch (status) {
      case 'active':
        return reservations.filter(r => r.status === 'confirmed' || r.status === 'checked_in')
      case 'scheduled':
        return reservations.filter(r => r.job?.workStatus === 'scheduled' || r.job?.workStatus === 'in_progress')
      case 'done':
        return reservations.filter(r => r.job?.workStatus === 'completed' || r.status === 'checked_out')
      default:
        return reservations
    }
  },
  
  // Filter reservations by property
  byProperty: (reservations: Reservation[], propertyIds: string[]) => {
    if (propertyIds.length === 0) return reservations
    return reservations.filter(r => propertyIds.includes(r.propertyId))
  },
  
  // Filter reservations by date range
  byDateRange: (reservations: Reservation[], startDate?: string, endDate?: string) => {
    if (!startDate && !endDate) return reservations
    
    return reservations.filter(r => {
      const checkIn = new Date(r.checkIn)
      const checkOut = new Date(r.checkOut)
      
      if (startDate && endDate) {
        const start = new Date(startDate)
        const end = new Date(endDate)
        return (checkIn >= start && checkIn <= end) || (checkOut >= start && checkOut <= end)
      } else if (startDate) {
        const start = new Date(startDate)
        return checkIn >= start || checkOut >= start
      } else if (endDate) {
        const end = new Date(endDate)
        return checkIn <= end || checkOut <= end
      }
      
      return true
    })
  }
}