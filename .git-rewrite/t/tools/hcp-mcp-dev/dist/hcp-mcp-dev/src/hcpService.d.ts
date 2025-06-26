/**
 * HousecallPro API Service
 * Handles all API communication with rate limiting and error handling
 */
import { HCPConfig, HCPCustomer, HCPEmployee, HCPJob, HCPJobType, HCPAppointment, CreateCustomerData, UpdateCustomerData, ListCustomersParams, CreateEmployeeData, UpdateEmployeeData, ListEmployeesParams, CreateJobData, UpdateJobData, ListJobsParams, CreateJobTypeData, UpdateJobTypeData, ListJobTypesParams, CreateAppointmentData, UpdateAppointmentData, ListAppointmentsParams, PaginatedResponse, HCPLineItem, HCPJobSchedule, CachedResponse } from '../../hcp-mcp-common/src/index.js';
export declare class HCPService {
    private apiKey;
    private baseUrl;
    private environment;
    private rateLimiter;
    private cacheService;
    private analysisService;
    constructor(config: HCPConfig);
    private makeRequest;
    listCustomers(params?: ListCustomersParams): Promise<PaginatedResponse<HCPCustomer> | CachedResponse<PaginatedResponse<HCPCustomer>>>;
    getCustomer(id: string): Promise<HCPCustomer | CachedResponse<HCPCustomer>>;
    createCustomer(data: CreateCustomerData): Promise<HCPCustomer>;
    updateCustomer(id: string, data: UpdateCustomerData): Promise<HCPCustomer>;
    deleteCustomer(id: string): Promise<void>;
    getCustomerJobs(id: string, params?: ListJobsParams): Promise<PaginatedResponse<HCPJob> | CachedResponse<PaginatedResponse<HCPJob>>>;
    listEmployees(params?: ListEmployeesParams): Promise<PaginatedResponse<HCPEmployee> | CachedResponse<PaginatedResponse<HCPEmployee>>>;
    getEmployee(id: string): Promise<HCPEmployee | CachedResponse<HCPEmployee>>;
    createEmployee(data: CreateEmployeeData): Promise<HCPEmployee>;
    updateEmployee(id: string, data: UpdateEmployeeData): Promise<HCPEmployee>;
    getEmployeeSchedule(id: string, startDate?: string, endDate?: string): Promise<any | CachedResponse<any>>;
    listJobs(params?: ListJobsParams): Promise<PaginatedResponse<HCPJob> | CachedResponse<PaginatedResponse<HCPJob>>>;
    getJob(id: string): Promise<HCPJob | CachedResponse<HCPJob>>;
    createJob(data: CreateJobData): Promise<HCPJob>;
    updateJob(id: string, data: UpdateJobData): Promise<HCPJob>;
    deleteJob(id: string): Promise<void>;
    rescheduleJob(id: string, schedule: HCPJobSchedule): Promise<HCPJob>;
    getJobLineItems(id: string): Promise<HCPLineItem[] | CachedResponse<{
        data: HCPLineItem[];
    }>>;
    updateJobLineItems(id: string, lineItems: HCPLineItem[]): Promise<void>;
    createJobLineItem(jobId: string, lineItem: HCPLineItem): Promise<HCPLineItem>;
    getJobLineItem(jobId: string, lineItemId: string): Promise<HCPLineItem | CachedResponse<HCPLineItem>>;
    updateJobLineItem(jobId: string, lineItemId: string, lineItem: Partial<HCPLineItem>): Promise<HCPLineItem>;
    deleteJobLineItem(jobId: string, lineItemId: string): Promise<void>;
    listJobTypes(params?: ListJobTypesParams): Promise<PaginatedResponse<HCPJobType> | CachedResponse<PaginatedResponse<HCPJobType>>>;
    getJobType(id: string): Promise<HCPJobType | CachedResponse<HCPJobType>>;
    createJobType(data: CreateJobTypeData): Promise<HCPJobType>;
    updateJobType(id: string, data: UpdateJobTypeData): Promise<HCPJobType>;
    listAppointments(params?: ListAppointmentsParams): Promise<HCPAppointment[] | CachedResponse<{
        appointments: HCPAppointment[];
    }> | CachedResponse<PaginatedResponse<HCPAppointment>>>;
    getAppointment(id: string): Promise<HCPAppointment | CachedResponse<HCPAppointment>>;
    createAppointment(data: CreateAppointmentData): Promise<HCPAppointment>;
    updateAppointment(id: string, data: UpdateAppointmentData): Promise<HCPAppointment>;
    deleteAppointment(id: string): Promise<void>;
    searchAddresses(params: {
        street?: string;
        city?: string;
        state?: string;
        zip?: string;
        customer_name?: string;
        customer_id?: string;
    }): Promise<any[]>;
    getJobsByAddress(addressId: string, params?: {
        work_status?: string;
        scheduled_start_min?: string;
        scheduled_start_max?: string;
    }): Promise<any[]>;
    private createDetailedError;
    private matchesAddressFilter;
    searchCache(filePath: string, searchTerm: string, fieldPath?: string): Promise<any[]>;
    listCacheFiles(operation?: string): Promise<any[]>;
    cleanupCache(): Promise<number>;
    getCacheSummary(data: any, operation: string): string;
    analyzeLaundryJobs(): Promise<any>;
    analyzeServiceItems(itemPattern: string): Promise<any>;
    analyzeCustomerRevenue(customerId?: string): Promise<any>;
    analyzeJobStatistics(): Promise<any>;
    generateAnalysisReport(): Promise<any>;
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
        cache: {
            enabled: boolean;
            environment: "dev" | "prod";
        };
    };
}
//# sourceMappingURL=hcpService.d.ts.map