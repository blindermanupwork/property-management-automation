/**
 * HousecallPro API Service
 * Handles all API communication with rate limiting and error handling
 */
import { HCPConfig, HCPCustomer, HCPEmployee, HCPJob, HCPJobType, HCPAppointment, CreateCustomerData, UpdateCustomerData, ListCustomersParams, CreateEmployeeData, UpdateEmployeeData, ListEmployeesParams, CreateJobData, UpdateJobData, ListJobsParams, CreateJobTypeData, UpdateJobTypeData, ListJobTypesParams, CreateAppointmentData, UpdateAppointmentData, ListAppointmentsParams, PaginatedResponse, HCPLineItem, HCPJobSchedule } from '../../hcp-mcp-common/src/index.js';
export declare class HCPService {
    private apiKey;
    private baseUrl;
    private environment;
    private rateLimiter;
    constructor(config: HCPConfig);
    private makeRequest;
    listCustomers(params?: ListCustomersParams): Promise<PaginatedResponse<HCPCustomer>>;
    getCustomer(id: string): Promise<HCPCustomer>;
    createCustomer(data: CreateCustomerData): Promise<HCPCustomer>;
    updateCustomer(id: string, data: UpdateCustomerData): Promise<HCPCustomer>;
    deleteCustomer(id: string): Promise<void>;
    getCustomerJobs(id: string, params?: ListJobsParams): Promise<PaginatedResponse<HCPJob>>;
    listEmployees(params?: ListEmployeesParams): Promise<PaginatedResponse<HCPEmployee>>;
    getEmployee(id: string): Promise<HCPEmployee>;
    createEmployee(data: CreateEmployeeData): Promise<HCPEmployee>;
    updateEmployee(id: string, data: UpdateEmployeeData): Promise<HCPEmployee>;
    getEmployeeSchedule(id: string, startDate?: string, endDate?: string): Promise<any>;
    listJobs(params?: ListJobsParams): Promise<PaginatedResponse<HCPJob>>;
    getJob(id: string): Promise<HCPJob>;
    createJob(data: CreateJobData): Promise<HCPJob>;
    updateJob(id: string, data: UpdateJobData): Promise<HCPJob>;
    deleteJob(id: string): Promise<void>;
    rescheduleJob(id: string, schedule: HCPJobSchedule): Promise<HCPJob>;
    getJobLineItems(id: string): Promise<HCPLineItem[]>;
    updateJobLineItems(id: string, lineItems: HCPLineItem[]): Promise<void>;
    createJobLineItem(jobId: string, lineItem: HCPLineItem): Promise<HCPLineItem>;
    getJobLineItem(jobId: string, lineItemId: string): Promise<HCPLineItem>;
    updateJobLineItem(jobId: string, lineItemId: string, lineItem: Partial<HCPLineItem>): Promise<HCPLineItem>;
    deleteJobLineItem(jobId: string, lineItemId: string): Promise<void>;
    listJobTypes(params?: ListJobTypesParams): Promise<PaginatedResponse<HCPJobType>>;
    getJobType(id: string): Promise<HCPJobType>;
    createJobType(data: CreateJobTypeData): Promise<HCPJobType>;
    updateJobType(id: string, data: UpdateJobTypeData): Promise<HCPJobType>;
    listAppointments(params?: ListAppointmentsParams): Promise<HCPAppointment[]>;
    getAppointment(id: string): Promise<HCPAppointment>;
    createAppointment(data: CreateAppointmentData): Promise<HCPAppointment>;
    updateAppointment(id: string, data: UpdateAppointmentData): Promise<HCPAppointment>;
    deleteAppointment(id: string): Promise<void>;
    getStatus(): {
        environment: "dev" | "prod";
        baseUrl: string;
        rateLimiter: {
            queueLength: number;
            processing: boolean;
            retryAfter: Date | null | undefined;
            recentRequests: number;
            rateLimitRemaining: number;
        };
    };
}
//# sourceMappingURL=hcpService.d.ts.map