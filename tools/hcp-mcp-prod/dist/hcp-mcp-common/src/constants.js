/**
 * HousecallPro API Constants
 */
export const HCP_API = {
    BASE_URL: 'https://api.housecallpro.com',
    VERSION: 'v1',
    // Rate limiting
    DEFAULT_RATE_LIMIT: {
        REQUESTS_PER_MINUTE: 60,
        RETRY_AFTER_MS: 1000,
        MAX_RETRIES: 3,
        BACKOFF_MULTIPLIER: 2
    },
    // Pagination
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    // Job statuses
    JOB_STATUSES: [
        'unscheduled',
        'scheduled',
        'in_progress',
        'completed',
        'canceled'
    ],
    // Employee roles
    EMPLOYEE_ROLES: [
        'admin',
        'employee',
        'field_employee'
    ],
    // Line item kinds
    LINE_ITEM_KINDS: [
        'service',
        'product',
        'discount',
        'fee'
    ],
    // Address types
    ADDRESS_TYPES: [
        'service',
        'billing'
    ],
    // Contact types
    CONTACT_TYPES: [
        'phone',
        'email',
        'other'
    ],
    // Appointment statuses
    APPOINTMENT_STATUSES: [
        'scheduled',
        'in_progress',
        'completed',
        'canceled'
    ]
};
export const MCP_TOOL_NAMES = {
    // Customer tools
    LIST_CUSTOMERS: 'list_customers',
    GET_CUSTOMER: 'get_customer',
    CREATE_CUSTOMER: 'create_customer',
    UPDATE_CUSTOMER: 'update_customer',
    DELETE_CUSTOMER: 'delete_customer',
    GET_CUSTOMER_JOBS: 'get_customer_jobs',
    // Employee tools
    LIST_EMPLOYEES: 'list_employees',
    GET_EMPLOYEE: 'get_employee',
    CREATE_EMPLOYEE: 'create_employee',
    UPDATE_EMPLOYEE: 'update_employee',
    GET_EMPLOYEE_SCHEDULE: 'get_employee_schedule',
    // Job tools
    LIST_JOBS: 'list_jobs',
    GET_JOB: 'get_job',
    CREATE_JOB: 'create_job',
    UPDATE_JOB: 'update_job',
    DELETE_JOB: 'delete_job',
    RESCHEDULE_JOB: 'reschedule_job',
    GET_JOB_LINE_ITEMS: 'get_job_line_items',
    UPDATE_JOB_LINE_ITEMS: 'update_job_line_items',
    CREATE_JOB_LINE_ITEM: 'create_job_line_item',
    GET_JOB_LINE_ITEM: 'get_job_line_item',
    UPDATE_JOB_LINE_ITEM: 'update_job_line_item',
    DELETE_JOB_LINE_ITEM: 'delete_job_line_item',
    // Job Type tools
    LIST_JOB_TYPES: 'list_job_types',
    GET_JOB_TYPE: 'get_job_type',
    CREATE_JOB_TYPE: 'create_job_type',
    UPDATE_JOB_TYPE: 'update_job_type',
    // Appointment tools
    LIST_APPOINTMENTS: 'list_appointments',
    GET_APPOINTMENT: 'get_appointment',
    CREATE_APPOINTMENT: 'create_appointment',
    UPDATE_APPOINTMENT: 'update_appointment',
    DELETE_APPOINTMENT: 'delete_appointment'
};
export const HTTP_METHODS = {
    GET: 'GET',
    POST: 'POST',
    PUT: 'PUT',
    PATCH: 'PATCH',
    DELETE: 'DELETE'
};
export const HTTP_STATUS = {
    OK: 200,
    CREATED: 201,
    NO_CONTENT: 204,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    TOO_MANY_REQUESTS: 429,
    INTERNAL_SERVER_ERROR: 500,
    SERVICE_UNAVAILABLE: 503
};
