// Core data types based on existing system (READ ONLY)
// These types mirror the existing Airtable/HCP data structure

export interface Property {
  id: string
  name: string
  address: {
    street: string
    city: string
    state: string
    zipCode: string
    fullAddress: string
  }
  location: {
    latitude?: number
    longitude?: number
  }
  propertyType: string
  isActive: boolean
  managedBy?: string
  notes?: string
  tags?: string[]
}

export interface Guest {
  id: string
  firstName: string
  lastName: string
  fullName: string
  email?: string
  phone?: string
  homePhone?: string
  workPhone?: string
  emergencyContact?: {
    name: string
    phone: string
    relationship: string
  }
}

export interface Reservation {
  id: string
  propertyId: string
  property: Property
  guestId: string
  guest: Guest
  
  // Dates and timing
  checkIn: string // ISO date string
  checkOut: string // ISO date string
  duration: number // nights
  createdAt: string
  updatedAt: string
  
  // Reservation details
  numberOfGuests: {
    adults: number
    children: number
    total: number
  }
  
  // Service requirements
  serviceInstructions?: string
  specialRequests?: string[]
  
  // Related job information
  jobId?: string
  job?: Job
  
  // Status
  status: 'confirmed' | 'checked_in' | 'checked_out' | 'cancelled'
  
  // Source information
  source: 'itrip' | 'evolve' | 'ics' | 'manual'
  sourceReservationId?: string
  
  // Financial
  totalAmount?: number
  currency?: string
}

export interface Employee {
  id: string
  firstName: string
  lastName: string
  fullName: string
  email?: string
  phone?: string
  role: 'admin' | 'employee' | 'field_employee'
  isActive: boolean
  colorHex?: string
  tags?: string[]
  
  // Availability and scheduling
  availability?: {
    monday: boolean
    tuesday: boolean
    wednesday: boolean
    thursday: boolean
    friday: boolean
    saturday: boolean
    sunday: boolean
  }
  
  // Performance metrics (read-only)
  stats?: {
    totalJobsCompleted: number
    averageRating?: number
    onTimePercentage?: number
  }
}

export interface JobLineItem {
  id: string
  name: string
  description?: string
  quantity: number
  unitPrice: number // in cents
  unitCost?: number // in cents
  total: number // in cents (quantity * unitPrice)
  kind: 'service' | 'product' | 'discount' | 'fee'
  serviceItemId?: string
  taxable: boolean
  category?: string
}

export interface Job {
  id: string
  reservationId?: string
  customerId: string
  addressId: string
  
  // Job details
  description?: string
  notes?: string
  jobTypeId?: string
  jobType?: {
    id: string
    name: string
    description?: string
    colorHex?: string
    isActive: boolean
  }
  
  // Scheduling
  schedule?: {
    scheduledStart: string // ISO datetime
    scheduledEnd: string // ISO datetime
    arrivalWindow?: number // minutes
  }
  
  // Assignment
  assignedEmployeeIds: string[]
  assignedEmployees: Employee[]
  
  // Status and tracking
  workStatus: 'unscheduled' | 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  
  // Work timestamps
  workTimestamps?: {
    created: string
    assigned?: string
    on_my_way?: string
    started?: string
    completed?: string
    cancelled?: string
  }
  
  // Line items and pricing
  lineItems: JobLineItem[]
  totalCost: number // in cents
  totalPrice: number // in cents
  
  // Service line custom instructions (new feature)
  serviceLineInstructions?: string
  
  // Dates
  createdAt: string
  updatedAt: string
  
  // Related data
  customer?: {
    id: string
    name: string
    email?: string
    phone?: string
  }
  
  address?: {
    id: string
    street: string
    city: string
    state: string
    zipCode: string
    fullAddress: string
  }
}

export interface Request {
  id: string
  type: 'late_checkout' | 'custom_cleaning_time' | 'special_service' | 'maintenance'
  reservationId: string
  reservation: Reservation
  
  // Request details
  title: string
  description?: string
  reason?: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  
  // Timing
  requestedDate?: string // ISO date
  requestedTime?: string // ISO time
  currentSchedule?: {
    date: string
    time: string
  }
  
  // Status and workflow
  status: 'pending' | 'approved' | 'denied' | 'completed' | 'cancelled'
  
  // Approval workflow
  submittedBy: string
  submittedAt: string
  reviewedBy?: string
  reviewedAt?: string
  approvalNotes?: string
  
  // Impact assessment
  impactAssessment?: {
    affectsNextGuest: boolean
    additionalCosts?: number
    timeRequired?: number // minutes
    resourcesNeeded?: string[]
  }
}

export interface UserProfile {
  id: string
  email: string
  firstName: string
  lastName: string
  fullName: string
  phone?: string
  role: 'property_manager' | 'admin' | 'viewer'
  
  // Managed properties
  managedProperties: Property[]
  
  // Preferences
  preferences: {
    notifications: {
      jobStatusUpdates: boolean
      guestRequests: boolean
      systemMaintenance: boolean
      marketingUpdates: boolean
    }
    theme: 'light' | 'dark' | 'system'
    timezone: string
    language: string
  }
  
  // Account info
  memberSince: string
  lastLoginAt?: string
  isActive: boolean
}

// Search and filter types
export interface SearchFilters {
  query: string
  propertyIds: string[]
  dateRange: {
    start?: string
    end?: string
  }
  jobStatuses: Job['workStatus'][]
  reservationStatuses: Reservation['status'][]
  locations: string[]
  employeeIds: string[]
}

export interface SearchHistory {
  id: string
  query: string
  filters: Partial<SearchFilters>
  timestamp: string
  resultCount: number
}

// API Response types
export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
  pagination?: {
    page: number
    per_page: number
    total_pages: number
    total_count: number
  }
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    per_page: number
    total_pages: number
    total_count: number
  }
}

// Error types
export interface ApiError {
  error: string
  message: string
  code?: string
  details?: Record<string, any>
}

// Real-time update types
export interface RealtimeUpdate {
  type: 'job_status_change' | 'new_request' | 'request_approved' | 'request_denied'
  data: {
    jobId?: string
    requestId?: string
    newStatus?: string
    timestamp: string
    message?: string
  }
}

// Navigation types
export type RootStackParamList = {
  Auth: undefined
  Main: undefined
  ReservationDetail: { reservationId: string }
  JobDetail: { jobId: string }
  Search: { initialQuery?: string }
  Profile: undefined
  RequestForm: { 
    type: Request['type']
    reservationId: string
  }
}

export type MainTabParamList = {
  Dashboard: undefined
  Search: undefined
  Requests: undefined
  Profile: undefined
}

// Status badge configurations
export interface StatusConfig {
  label: string
  color: string
  textColor: string
  icon?: string
}

export const JOB_STATUS_CONFIGS: Record<Job['workStatus'], StatusConfig> = {
  unscheduled: {
    label: 'Unscheduled',
    color: '#64748B',
    textColor: '#FFFFFF',
    icon: 'calendar-x'
  },
  scheduled: {
    label: 'Scheduled', 
    color: '#0066CC',
    textColor: '#FFFFFF',
    icon: 'calendar-check'
  },
  in_progress: {
    label: 'In Progress',
    color: '#FF6B35', 
    textColor: '#FFFFFF',
    icon: 'play-circle'
  },
  completed: {
    label: 'Completed',
    color: '#22C55E',
    textColor: '#FFFFFF', 
    icon: 'check-circle'
  },
  cancelled: {
    label: 'Cancelled',
    color: '#EF4444',
    textColor: '#FFFFFF',
    icon: 'x-circle'
  }
}

export const RESERVATION_STATUS_CONFIGS: Record<Reservation['status'], StatusConfig> = {
  confirmed: {
    label: 'Confirmed',
    color: '#0066CC',
    textColor: '#FFFFFF',
    icon: 'calendar-check'
  },
  checked_in: {
    label: 'Checked In',
    color: '#FF6B35',
    textColor: '#FFFFFF',
    icon: 'log-in'
  },
  checked_out: {
    label: 'Checked Out',
    color: '#22C55E',
    textColor: '#FFFFFF',
    icon: 'log-out'
  },
  cancelled: {
    label: 'Cancelled',
    color: '#EF4444',
    textColor: '#FFFFFF',
    icon: 'x-circle'
  }
}