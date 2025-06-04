/**
 * HousecallPro API Service
 * Handles all API communication with rate limiting and error handling
 */

import fetch from 'node-fetch';
import { RateLimiter } from './rateLimiter.js';
import {
  HCPConfig,
  HCPError,
  HCPCustomer,
  HCPEmployee,
  HCPJob,
  HCPJobType,
  HCPAppointment,
  CreateCustomerData,
  UpdateCustomerData,
  ListCustomersParams,
  CreateEmployeeData,
  UpdateEmployeeData,
  ListEmployeesParams,
  CreateJobData,
  UpdateJobData,
  ListJobsParams,
  CreateJobTypeData,
  UpdateJobTypeData,
  ListJobTypesParams,
  CreateAppointmentData,
  UpdateAppointmentData,
  ListAppointmentsParams,
  PaginatedResponse,
  HCPLineItem,
  HCPJobSchedule,
  CachedResponse
} from '../../hcp-mcp-common/src/index.js';
import { CacheService } from '../../hcp-mcp-common/src/cacheService.js';
import { AnalysisService } from '../../hcp-mcp-common/src/analysisService.js';

export class HCPService {
  private apiKey: string;
  private baseUrl: string;
  private environment: 'dev' | 'prod';
  private rateLimiter: RateLimiter;
  private cacheService: CacheService;
  private analysisService: AnalysisService;

  constructor(config: HCPConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl;
    this.environment = config.environment;
    this.rateLimiter = new RateLimiter(config.rateLimit?.requestsPerMinute || 60);
    this.cacheService = new CacheService(config.cache);
    this.analysisService = new AnalysisService(config.environment);
  }

  private async makeRequest<T>(
    path: string,
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
    body?: any,
    retries = 3,
    operationName?: string
  ): Promise<T | CachedResponse<T>> {
    return this.rateLimiter.execute(async () => {
      for (let attempt = 0; attempt < retries; attempt++) {
        try {
          const url = `${this.baseUrl}${path}`;
          const headers: Record<string, string> = {
            'Authorization': `Token ${this.apiKey}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': `HCP-MCP-${this.environment}/1.0.0`
          };

          console.log(`[${this.environment}] ${method} ${url}`);
          console.log(`[${this.environment}] Full URL: ${url}`);

          const response = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
          });

          const responseText = await response.text();
          
          if (!response.ok) {
            const error = new HCPError(
              `API request failed: ${response.status} ${response.statusText}`,
              response.status,
              undefined,
              responseText
            );

            // Add headers to error for rate limit handling
            (error as any).headers = Object.fromEntries(response.headers.entries());

            throw error;
          }

          // Handle empty responses
          if (!responseText || responseText.trim() === '') {
            return {} as T;
          }

          try {
            const data = JSON.parse(responseText) as T;
            
            // Check if response should be cached (only for GET requests)
            if (method === 'GET' && operationName && this.cacheService.shouldCache(data, operationName)) {
              try {
                const cachedResponse = await this.cacheService.cacheResponse(
                  data, 
                  operationName, 
                  this.environment,
                  { path, method }
                );
                console.log(`[${this.environment}] Cached large response: ${this.cacheService.getSummary(data, operationName)}`);
                return cachedResponse;
              } catch (cacheError) {
                console.warn(`[${this.environment}] Cache write failed:`, cacheError);
                // Continue with normal response if caching fails
                return data;
              }
            }
            
            return data;
          } catch (parseError) {
            throw new HCPError(`Failed to parse response: ${parseError}`, 500);
          }

        } catch (error: any) {
          if (attempt === retries - 1) throw error;

          // Only retry on certain errors
          const shouldRetry = 
            error.status === 429 || // Rate limit
            error.status === 503 || // Service unavailable
            error.status === 502 || // Bad gateway
            error.code === 'ECONNRESET' ||
            error.code === 'ETIMEDOUT';

          if (!shouldRetry) throw error;

          const backoffMs = Math.pow(2, attempt) * 1000;
          console.log(`Attempt ${attempt + 1} failed, retrying in ${backoffMs}ms...`);
          await new Promise(resolve => setTimeout(resolve, backoffMs));
        }
      }
      throw new Error('Max retries exceeded');
    });
  }

  // Customer methods
  async listCustomers(params: ListCustomersParams = {}): Promise<PaginatedResponse<HCPCustomer> | CachedResponse<PaginatedResponse<HCPCustomer>>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.q) searchParams.set('q', params.q);
    if (params.search) searchParams.set('search', params.search);
    if (params.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params.sort_direction) searchParams.set('sort_direction', params.sort_direction);
    if (params.created_after) searchParams.set('created_after', params.created_after);
    if (params.created_before) searchParams.set('created_before', params.created_before);
    if (params.tags) searchParams.set('tags', params.tags.join(','));

    const query = searchParams.toString();
    const path = `/customers${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPCustomer>>(path, 'GET', undefined, 3, 'list_customers');
  }

  async getCustomer(id: string): Promise<HCPCustomer | CachedResponse<HCPCustomer>> {
    return this.makeRequest<HCPCustomer>(`/customers/${id}`, 'GET', undefined, 3, 'get_customer');
  }

  async createCustomer(data: CreateCustomerData): Promise<HCPCustomer> {
    return this.makeRequest<HCPCustomer>('/customers', 'POST', data) as Promise<HCPCustomer>;
  }

  async updateCustomer(id: string, data: UpdateCustomerData): Promise<HCPCustomer> {
    return this.makeRequest<HCPCustomer>(`/customers/${id}`, 'PATCH', data) as Promise<HCPCustomer>;
  }

  async deleteCustomer(id: string): Promise<void> {
    return this.makeRequest<void>(`/customers/${id}`, 'DELETE') as Promise<void>;
  }

  async getCustomerJobs(id: string, params: ListJobsParams = {}): Promise<PaginatedResponse<HCPJob> | CachedResponse<PaginatedResponse<HCPJob>>> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    
    const query = searchParams.toString();
    const path = `/customers/${id}/jobs${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPJob>>(path, 'GET', undefined, 3, 'get_customer_jobs');
  }

  // Employee methods
  async listEmployees(params: ListEmployeesParams = {}): Promise<PaginatedResponse<HCPEmployee> | CachedResponse<PaginatedResponse<HCPEmployee>>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.is_active !== undefined) searchParams.set('is_active', params.is_active.toString());
    if (params.role) searchParams.set('role', params.role);

    const query = searchParams.toString();
    const path = `/employees${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPEmployee>>(path, 'GET', undefined, 3, 'list_employees');
  }

  async getEmployee(id: string): Promise<HCPEmployee | CachedResponse<HCPEmployee>> {
    return this.makeRequest<HCPEmployee>(`/employees/${id}`, 'GET', undefined, 3, 'get_employee');
  }

  async createEmployee(data: CreateEmployeeData): Promise<HCPEmployee> {
    return this.makeRequest<HCPEmployee>('/employees', 'POST', data) as Promise<HCPEmployee>;
  }

  async updateEmployee(id: string, data: UpdateEmployeeData): Promise<HCPEmployee> {
    return this.makeRequest<HCPEmployee>(`/employees/${id}`, 'PATCH', data) as Promise<HCPEmployee>;
  }

  async getEmployeeSchedule(id: string, startDate?: string, endDate?: string): Promise<any | CachedResponse<any>> {
    const searchParams = new URLSearchParams();
    if (startDate) searchParams.set('start_date', startDate);
    if (endDate) searchParams.set('end_date', endDate);
    
    const query = searchParams.toString();
    const path = `/employees/${id}/schedule${query ? `?${query}` : ''}`;
    
    return this.makeRequest<any>(path, 'GET', undefined, 3, 'get_employee_schedule');
  }

  // Job methods
  async listJobs(params: ListJobsParams = {}): Promise<PaginatedResponse<HCPJob> | CachedResponse<PaginatedResponse<HCPJob>>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.customer_id) searchParams.set('customer_id', params.customer_id);
    if (params.work_status) searchParams.set('work_status', params.work_status);
    if (params.scheduled_start_min) searchParams.set('scheduled_start_min', params.scheduled_start_min);
    if (params.scheduled_start_max) searchParams.set('scheduled_start_max', params.scheduled_start_max);
    if (params.assigned_employee_id) searchParams.set('assigned_employee_id', params.assigned_employee_id);
    if (params.job_type_id) searchParams.set('job_type_id', params.job_type_id);

    const query = searchParams.toString();
    const path = `/jobs${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPJob>>(path, 'GET', undefined, 3, 'list_jobs');
  }

  async getJob(id: string): Promise<HCPJob | CachedResponse<HCPJob>> {
    return this.makeRequest<HCPJob>(`/jobs/${id}`, 'GET', undefined, 3, 'get_job');
  }

  async createJob(data: CreateJobData): Promise<HCPJob> {
    return this.makeRequest<HCPJob>('/jobs', 'POST', data) as Promise<HCPJob>;
  }

  async updateJob(id: string, data: UpdateJobData): Promise<HCPJob> {
    return this.makeRequest<HCPJob>(`/jobs/${id}`, 'PATCH', data) as Promise<HCPJob>;
  }

  async deleteJob(id: string): Promise<void> {
    return this.makeRequest<void>(`/jobs/${id}`, 'DELETE') as Promise<void>;
  }

  async rescheduleJob(id: string, schedule: HCPJobSchedule): Promise<HCPJob> {
    return this.makeRequest<HCPJob>(`/jobs/${id}/reschedule`, 'POST', { schedule }) as Promise<HCPJob>;
  }

  async getJobLineItems(id: string): Promise<HCPLineItem[] | CachedResponse<{ data: HCPLineItem[] }>> {
    const response = await this.makeRequest<{ data: HCPLineItem[] }>(`/jobs/${id}/line_items`, 'GET', undefined, 3, 'get_job_line_items');
    
    // Handle cached responses
    if ('_cached' in response) {
      return response;
    }
    
    return response.data || [];
  }

  async updateJobLineItems(id: string, lineItems: HCPLineItem[]): Promise<void> {
    return this.makeRequest<void>(`/jobs/${id}/line_items/bulk_update`, 'PUT', { line_items: lineItems }) as Promise<void>;
  }

  async createJobLineItem(jobId: string, lineItem: HCPLineItem): Promise<HCPLineItem> {
    return this.makeRequest<HCPLineItem>(`/jobs/${jobId}/line_items`, 'POST', lineItem) as Promise<HCPLineItem>;
  }

  async getJobLineItem(jobId: string, lineItemId: string): Promise<HCPLineItem | CachedResponse<HCPLineItem>> {
    return this.makeRequest<HCPLineItem>(`/jobs/${jobId}/line_items/${lineItemId}`, 'GET', undefined, 3, 'get_job_line_item');
  }

  async updateJobLineItem(jobId: string, lineItemId: string, lineItem: Partial<HCPLineItem>): Promise<HCPLineItem> {
    return this.makeRequest<HCPLineItem>(`/jobs/${jobId}/line_items/${lineItemId}`, 'PUT', lineItem) as Promise<HCPLineItem>;
  }

  async deleteJobLineItem(jobId: string, lineItemId: string): Promise<void> {
    return this.makeRequest<void>(`/jobs/${jobId}/line_items/${lineItemId}`, 'DELETE') as Promise<void>;
  }

  // Job Type methods
  async listJobTypes(params: ListJobTypesParams = {}): Promise<PaginatedResponse<HCPJobType> | CachedResponse<PaginatedResponse<HCPJobType>>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.is_active !== undefined) searchParams.set('is_active', params.is_active.toString());

    const query = searchParams.toString();
    const path = `/job_types${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPJobType>>(path, 'GET', undefined, 3, 'list_job_types');
  }

  async getJobType(id: string): Promise<HCPJobType | CachedResponse<HCPJobType>> {
    return this.makeRequest<HCPJobType>(`/job_types/${id}`, 'GET', undefined, 3, 'get_job_type');
  }

  async createJobType(data: CreateJobTypeData): Promise<HCPJobType> {
    return this.makeRequest<HCPJobType>('/job_types', 'POST', data) as Promise<HCPJobType>;
  }

  async updateJobType(id: string, data: UpdateJobTypeData): Promise<HCPJobType> {
    return this.makeRequest<HCPJobType>(`/job_types/${id}`, 'PATCH', data) as Promise<HCPJobType>;
  }

  // Appointment methods
  async listAppointments(params: ListAppointmentsParams = {}): Promise<HCPAppointment[] | CachedResponse<{ appointments: HCPAppointment[] }> | CachedResponse<PaginatedResponse<HCPAppointment>>> {
    const searchParams = new URLSearchParams();
    
    if (params.job_id) searchParams.set('job_id', params.job_id);
    if (params.scheduled_start_min) searchParams.set('scheduled_start_min', params.scheduled_start_min);
    if (params.scheduled_start_max) searchParams.set('scheduled_start_max', params.scheduled_start_max);
    if (params.assigned_employee_id) searchParams.set('assigned_employee_id', params.assigned_employee_id);
    if (params.status) searchParams.set('status', params.status);

    const query = searchParams.toString();
    
    if (params.job_id) {
      // Use job-specific endpoint
      const path = `/jobs/${params.job_id}/appointments${query ? `?${query}` : ''}`;
      const response = await this.makeRequest<{ appointments: HCPAppointment[] }>(path, 'GET', undefined, 3, 'list_appointments');
      
      // Handle cached responses
      if ('_cached' in response) {
        return response;
      }
      
      return response.appointments || [];
    } else {
      // Use general appointments endpoint
      const path = `/appointments${query ? `?${query}` : ''}`;
      const response = await this.makeRequest<PaginatedResponse<HCPAppointment>>(path, 'GET', undefined, 3, 'list_appointments');
      
      // Handle cached responses
      if ('_cached' in response) {
        return response;
      }
      
      return response.data || [];
    }
  }

  async getAppointment(id: string): Promise<HCPAppointment | CachedResponse<HCPAppointment>> {
    return this.makeRequest<HCPAppointment>(`/appointments/${id}`, 'GET', undefined, 3, 'get_appointment');
  }

  async createAppointment(data: CreateAppointmentData): Promise<HCPAppointment> {
    return this.makeRequest<HCPAppointment>('/appointments', 'POST', data) as Promise<HCPAppointment>;
  }

  async updateAppointment(id: string, data: UpdateAppointmentData): Promise<HCPAppointment> {
    return this.makeRequest<HCPAppointment>(`/appointments/${id}`, 'PATCH', data) as Promise<HCPAppointment>;
  }

  async deleteAppointment(id: string): Promise<void> {
    return this.makeRequest<void>(`/appointments/${id}`, 'DELETE') as Promise<void>;
  }

  // Cache management methods
  async searchCache(filePath: string, searchTerm: string, fieldPath?: string): Promise<any[]> {
    return this.cacheService.searchCache(filePath, searchTerm, fieldPath);
  }

  async listCacheFiles(operation?: string): Promise<any[]> {
    return this.cacheService.listCacheFiles(this.environment, operation);
  }

  async cleanupCache(): Promise<number> {
    return this.cacheService.cleanup(this.environment);
  }

  getCacheSummary(data: any, operation: string): string {
    return this.cacheService.getSummary(data, operation);
  }

  // Analysis methods
  async analyzeLaundryJobs(): Promise<any> {
    return this.analysisService.analyzeLaundryJobs();
  }

  async analyzeServiceItems(itemPattern: string): Promise<any> {
    return this.analysisService.analyzeServiceItems(itemPattern);
  }

  async analyzeCustomerRevenue(customerId?: string): Promise<any> {
    return this.analysisService.analyzeCustomerRevenue(customerId);
  }

  async analyzeJobStatistics(): Promise<any> {
    return this.analysisService.analyzeJobStatistics();
  }

  async generateAnalysisReport(): Promise<any> {
    return this.analysisService.generateAnalysisReport();
  }

  // Utility methods
  getStatus() {
    return {
      environment: this.environment,
      baseUrl: this.baseUrl,
      rateLimiter: this.rateLimiter.getStatus(),
      cache: {
        enabled: true,
        environment: this.environment
      }
    };
  }
}