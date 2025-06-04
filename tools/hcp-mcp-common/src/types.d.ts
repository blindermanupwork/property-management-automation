/**
 * Core HousecallPro API Types
 * Shared between dev and prod MCP servers
 */
export interface PaginatedResponse<T> {
    data: T[];
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
}
export interface HCPAddress {
    id: string;
    street?: string;
    city?: string;
    state?: string;
    zip?: string;
    country?: string;
    type?: 'service' | 'billing';
    latitude?: number;
    longitude?: number;
}
export interface HCPContact {
    type: 'phone' | 'email' | 'other';
    value: string;
    is_primary?: boolean;
}
export interface HCPCustomer {
    id: string;
    first_name?: string;
    last_name?: string;
    company?: string;
    email?: string;
    mobile_number?: string;
    home_number?: string;
    work_number?: string;
    notifications_enabled?: boolean;
    lead_source?: string;
    addresses?: HCPAddress[];
    tags?: string[];
    notes?: string;
    created_at: string;
    updated_at: string;
}
export interface CreateCustomerData {
    first_name?: string;
    last_name?: string;
    company?: string;
    email?: string;
    mobile_number?: string;
    home_number?: string;
    work_number?: string;
    lead_source?: string;
    tags?: string[];
    notes?: string;
    addresses?: Omit<HCPAddress, 'id'>[];
}
export interface UpdateCustomerData extends Partial<CreateCustomerData> {
}
export interface ListCustomersParams {
    page?: number;
    per_page?: number;
    search?: string;
    created_after?: string;
    created_before?: string;
    tags?: string[];
}
export interface HCPEmployee {
    id: string;
    first_name: string;
    last_name: string;
    email?: string;
    mobile_number?: string;
    role: 'admin' | 'employee' | 'field_employee';
    is_active: boolean;
    color_hex?: string;
    tags?: string[];
    created_at: string;
    updated_at: string;
}
export interface CreateEmployeeData {
    first_name: string;
    last_name: string;
    email?: string;
    mobile_number?: string;
    role: 'admin' | 'employee' | 'field_employee';
    color_hex?: string;
    tags?: string[];
}
export interface UpdateEmployeeData extends Partial<CreateEmployeeData> {
    is_active?: boolean;
}
export interface ListEmployeesParams {
    page?: number;
    per_page?: number;
    is_active?: boolean;
    role?: string;
}
export interface HCPLineItem {
    id?: string;
    name: string;
    description?: string;
    unit_price: number;
    unit_cost?: number;
    quantity: number;
    kind: 'service' | 'product' | 'discount' | 'fee';
    taxable?: boolean;
    service_item_id?: string;
    service_item_type?: string;
}
export interface HCPJobSchedule {
    scheduled_start: string;
    scheduled_end: string;
    arrival_window?: number;
}
export interface HCPJob {
    id: string;
    customer_id: string;
    address_id: string;
    work_status: 'unscheduled' | 'scheduled' | 'in_progress' | 'completed' | 'canceled';
    schedule: HCPJobSchedule;
    assigned_employee_ids: string[];
    line_items: HCPLineItem[];
    job_fields?: {
        job_type_id?: string;
    };
    notes?: string;
    invoice_number?: number;
    total_amount?: number;
    description?: string;
    created_at: string;
    updated_at: string;
    appointments?: HCPAppointment[];
}
export interface CreateJobData {
    customer_id: string;
    address_id: string;
    schedule: HCPJobSchedule;
    assigned_employee_ids?: string[];
    line_items?: HCPLineItem[];
    job_type_id?: string;
    notes?: string;
    description?: string;
    work_status?: 'unscheduled' | 'scheduled';
}
export interface UpdateJobData {
    customer_id?: string;
    address_id?: string;
    schedule?: HCPJobSchedule;
    assigned_employee_ids?: string[];
    line_items?: HCPLineItem[];
    job_type_id?: string;
    notes?: string;
    description?: string;
    work_status?: 'unscheduled' | 'scheduled' | 'in_progress' | 'completed' | 'canceled';
}
export interface ListJobsParams {
    page?: number;
    per_page?: number;
    customer_id?: string;
    work_status?: string;
    scheduled_start_min?: string;
    scheduled_start_max?: string;
    assigned_employee_id?: string;
    job_type_id?: string;
}
export interface HCPJobType {
    id: string;
    name: string;
    description?: string;
    color_hex?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}
export interface CreateJobTypeData {
    name: string;
    description?: string;
    color_hex?: string;
}
export interface UpdateJobTypeData extends Partial<CreateJobTypeData> {
    is_active?: boolean;
}
export interface ListJobTypesParams {
    page?: number;
    per_page?: number;
    is_active?: boolean;
}
export interface HCPAppointment {
    id: string;
    job_id: string;
    scheduled_start: string;
    scheduled_end: string;
    assigned_employee_ids: string[];
    status: 'scheduled' | 'in_progress' | 'completed' | 'canceled';
    notes?: string;
    created_at: string;
    updated_at: string;
}
export interface CreateAppointmentData {
    job_id: string;
    scheduled_start: string;
    scheduled_end: string;
    assigned_employee_ids: string[];
    notes?: string;
}
export interface UpdateAppointmentData extends Partial<CreateAppointmentData> {
    status?: 'scheduled' | 'in_progress' | 'completed' | 'canceled';
}
export interface ListAppointmentsParams {
    job_id?: string;
    scheduled_start_min?: string;
    scheduled_start_max?: string;
    assigned_employee_id?: string;
    status?: string;
}
export interface HCPConfig {
    apiKey: string;
    baseUrl: string;
    environment: 'dev' | 'prod';
    employeeId?: string;
    rateLimit?: {
        requestsPerMinute: number;
        retryAfterMs: number;
    };
}
export interface HCPErrorResponse {
    message: string;
    code?: string;
    details?: any;
    status: number;
}
export declare class HCPError extends Error {
    status?: number | undefined;
    code?: string | undefined;
    details?: any | undefined;
    constructor(message: string, status?: number | undefined, code?: string | undefined, details?: any | undefined);
    static fromResponse(response: HCPErrorResponse): HCPError;
}
//# sourceMappingURL=types.d.ts.map