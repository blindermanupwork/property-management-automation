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
  HCPJobSchedule
} from '../../hcp-mcp-common/src/index.js';

export class HCPService {
  private apiKey: string;
  private baseUrl: string;
  private environment: 'dev' | 'prod';
  private rateLimiter: RateLimiter;

  constructor(config: HCPConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl;
    this.environment = config.environment;
    this.rateLimiter = new RateLimiter(config.rateLimit?.requestsPerMinute || 60);
  }

  private async makeRequest<T>(
    path: string,
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
    body?: any,
    retries = 3
  ): Promise<T> {
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

          console.log(`[${this.environment}] ${method} ${path}`);

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
            return JSON.parse(responseText) as T;
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
  async listCustomers(params: ListCustomersParams = {}): Promise<PaginatedResponse<HCPCustomer>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.search) searchParams.set('search', params.search);
    if (params.created_after) searchParams.set('created_after', params.created_after);
    if (params.created_before) searchParams.set('created_before', params.created_before);
    if (params.tags) searchParams.set('tags', params.tags.join(','));

    const query = searchParams.toString();
    const path = `/customers${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPCustomer>>(path);
  }

  async getCustomer(id: string): Promise<HCPCustomer> {
    return this.makeRequest<HCPCustomer>(`/customers/${id}`);
  }

  async createCustomer(data: CreateCustomerData): Promise<HCPCustomer> {
    return this.makeRequest<HCPCustomer>('/customers', 'POST', data);
  }

  async updateCustomer(id: string, data: UpdateCustomerData): Promise<HCPCustomer> {
    return this.makeRequest<HCPCustomer>(`/customers/${id}`, 'PATCH', data);
  }

  async deleteCustomer(id: string): Promise<void> {
    return this.makeRequest<void>(`/customers/${id}`, 'DELETE');
  }

  async getCustomerJobs(id: string, params: ListJobsParams = {}): Promise<PaginatedResponse<HCPJob>> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    
    const query = searchParams.toString();
    const path = `/customers/${id}/jobs${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPJob>>(path);
  }

  // Employee methods
  async listEmployees(params: ListEmployeesParams = {}): Promise<PaginatedResponse<HCPEmployee>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.is_active !== undefined) searchParams.set('is_active', params.is_active.toString());
    if (params.role) searchParams.set('role', params.role);

    const query = searchParams.toString();
    const path = `/employees${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPEmployee>>(path);
  }

  async getEmployee(id: string): Promise<HCPEmployee> {
    return this.makeRequest<HCPEmployee>(`/employees/${id}`);
  }

  async createEmployee(data: CreateEmployeeData): Promise<HCPEmployee> {
    return this.makeRequest<HCPEmployee>('/employees', 'POST', data);
  }

  async updateEmployee(id: string, data: UpdateEmployeeData): Promise<HCPEmployee> {
    return this.makeRequest<HCPEmployee>(`/employees/${id}`, 'PATCH', data);
  }

  async getEmployeeSchedule(id: string, startDate?: string, endDate?: string): Promise<any> {
    const searchParams = new URLSearchParams();
    if (startDate) searchParams.set('start_date', startDate);
    if (endDate) searchParams.set('end_date', endDate);
    
    const query = searchParams.toString();
    const path = `/employees/${id}/schedule${query ? `?${query}` : ''}`;
    
    return this.makeRequest<any>(path);
  }

  // Job methods
  async listJobs(params: ListJobsParams = {}): Promise<PaginatedResponse<HCPJob>> {
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
    
    return this.makeRequest<PaginatedResponse<HCPJob>>(path);
  }

  async getJob(id: string): Promise<HCPJob> {
    return this.makeRequest<HCPJob>(`/jobs/${id}`);
  }

  async createJob(data: CreateJobData): Promise<HCPJob> {
    return this.makeRequest<HCPJob>('/jobs', 'POST', data);
  }

  async updateJob(id: string, data: UpdateJobData): Promise<HCPJob> {
    return this.makeRequest<HCPJob>(`/jobs/${id}`, 'PATCH', data);
  }

  async deleteJob(id: string): Promise<void> {
    return this.makeRequest<void>(`/jobs/${id}`, 'DELETE');
  }

  async rescheduleJob(id: string, schedule: HCPJobSchedule): Promise<HCPJob> {
    return this.makeRequest<HCPJob>(`/jobs/${id}/reschedule`, 'POST', { schedule });
  }

  async getJobLineItems(id: string): Promise<HCPLineItem[]> {
    const response = await this.makeRequest<{ data: HCPLineItem[] }>(`/jobs/${id}/line_items`);
    return response.data || [];
  }

  async updateJobLineItems(id: string, lineItems: HCPLineItem[]): Promise<void> {
    return this.makeRequest<void>(`/jobs/${id}/line_items/bulk_update`, 'PUT', { line_items: lineItems });
  }

  async createJobLineItem(jobId: string, lineItem: HCPLineItem): Promise<HCPLineItem> {
    return this.makeRequest<HCPLineItem>(`/jobs/${jobId}/line_items`, 'POST', lineItem);
  }

  async getJobLineItem(jobId: string, lineItemId: string): Promise<HCPLineItem> {
    return this.makeRequest<HCPLineItem>(`/jobs/${jobId}/line_items/${lineItemId}`);
  }

  async updateJobLineItem(jobId: string, lineItemId: string, lineItem: Partial<HCPLineItem>): Promise<HCPLineItem> {
    return this.makeRequest<HCPLineItem>(`/jobs/${jobId}/line_items/${lineItemId}`, 'PUT', lineItem);
  }

  async deleteJobLineItem(jobId: string, lineItemId: string): Promise<void> {
    return this.makeRequest<void>(`/jobs/${jobId}/line_items/${lineItemId}`, 'DELETE');
  }

  // Job Type methods
  async listJobTypes(params: ListJobTypesParams = {}): Promise<PaginatedResponse<HCPJobType>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.is_active !== undefined) searchParams.set('is_active', params.is_active.toString());

    const query = searchParams.toString();
    const path = `/job_types${query ? `?${query}` : ''}`;
    
    return this.makeRequest<PaginatedResponse<HCPJobType>>(path);
  }

  async getJobType(id: string): Promise<HCPJobType> {
    return this.makeRequest<HCPJobType>(`/job_types/${id}`);
  }

  async createJobType(data: CreateJobTypeData): Promise<HCPJobType> {
    return this.makeRequest<HCPJobType>('/job_types', 'POST', data);
  }

  async updateJobType(id: string, data: UpdateJobTypeData): Promise<HCPJobType> {
    return this.makeRequest<HCPJobType>(`/job_types/${id}`, 'PATCH', data);
  }

  // Appointment methods
  async listAppointments(params: ListAppointmentsParams = {}): Promise<HCPAppointment[]> {
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
      const response = await this.makeRequest<{ appointments: HCPAppointment[] }>(path);
      return response.appointments || [];
    } else {
      // Use general appointments endpoint
      const path = `/appointments${query ? `?${query}` : ''}`;
      const response = await this.makeRequest<PaginatedResponse<HCPAppointment>>(path);
      return response.data || [];
    }
  }

  async getAppointment(id: string): Promise<HCPAppointment> {
    return this.makeRequest<HCPAppointment>(`/appointments/${id}`);
  }

  async createAppointment(data: CreateAppointmentData): Promise<HCPAppointment> {
    return this.makeRequest<HCPAppointment>('/appointments', 'POST', data);
  }

  async updateAppointment(id: string, data: UpdateAppointmentData): Promise<HCPAppointment> {
    return this.makeRequest<HCPAppointment>(`/appointments/${id}`, 'PATCH', data);
  }

  async deleteAppointment(id: string): Promise<void> {
    return this.makeRequest<void>(`/appointments/${id}`, 'DELETE');
  }

  // Utility methods
  getStatus() {
    return {
      environment: this.environment,
      baseUrl: this.baseUrl,
      rateLimiter: this.rateLimiter.getStatus()
    };
  }
}