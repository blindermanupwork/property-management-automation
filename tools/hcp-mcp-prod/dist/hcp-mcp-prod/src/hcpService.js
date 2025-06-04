/**
 * HousecallPro API Service
 * Handles all API communication with rate limiting and error handling
 */
import fetch from 'node-fetch';
import { RateLimiter } from './rateLimiter.js';
import { HCPError } from '../../hcp-mcp-common/src/index.js';
export class HCPService {
    apiKey;
    baseUrl;
    environment;
    rateLimiter;
    constructor(config) {
        this.apiKey = config.apiKey;
        this.baseUrl = config.baseUrl;
        this.environment = config.environment;
        this.rateLimiter = new RateLimiter(config.rateLimit?.requestsPerMinute || 60);
    }
    async makeRequest(path, method = 'GET', body, retries = 3) {
        return this.rateLimiter.execute(async () => {
            for (let attempt = 0; attempt < retries; attempt++) {
                try {
                    const url = `${this.baseUrl}${path}`;
                    const headers = {
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
                        const error = new HCPError(`API request failed: ${response.status} ${response.statusText}`, response.status, undefined, responseText);
                        // Add headers to error for rate limit handling
                        error.headers = Object.fromEntries(response.headers.entries());
                        throw error;
                    }
                    // Handle empty responses
                    if (!responseText || responseText.trim() === '') {
                        return {};
                    }
                    try {
                        return JSON.parse(responseText);
                    }
                    catch (parseError) {
                        throw new HCPError(`Failed to parse response: ${parseError}`, 500);
                    }
                }
                catch (error) {
                    if (attempt === retries - 1)
                        throw error;
                    // Only retry on certain errors
                    const shouldRetry = error.status === 429 || // Rate limit
                        error.status === 503 || // Service unavailable
                        error.status === 502 || // Bad gateway
                        error.code === 'ECONNRESET' ||
                        error.code === 'ETIMEDOUT';
                    if (!shouldRetry)
                        throw error;
                    const backoffMs = Math.pow(2, attempt) * 1000;
                    console.log(`Attempt ${attempt + 1} failed, retrying in ${backoffMs}ms...`);
                    await new Promise(resolve => setTimeout(resolve, backoffMs));
                }
            }
            throw new Error('Max retries exceeded');
        });
    }
    // Customer methods
    async listCustomers(params = {}) {
        const searchParams = new URLSearchParams();
        if (params.page)
            searchParams.set('page', params.page.toString());
        if (params.page_size)
            searchParams.set('page_size', params.page_size.toString());
        if (params.search)
            searchParams.set('search', params.search);
        if (params.created_after)
            searchParams.set('created_after', params.created_after);
        if (params.created_before)
            searchParams.set('created_before', params.created_before);
        if (params.tags)
            searchParams.set('tags', params.tags.join(','));
        const query = searchParams.toString();
        const path = `/customers${query ? `?${query}` : ''}`;
        return this.makeRequest(path);
    }
    async getCustomer(id) {
        return this.makeRequest(`/customers/${id}`);
    }
    async createCustomer(data) {
        return this.makeRequest('/customers', 'POST', data);
    }
    async updateCustomer(id, data) {
        return this.makeRequest(`/customers/${id}`, 'PATCH', data);
    }
    async deleteCustomer(id) {
        return this.makeRequest(`/customers/${id}`, 'DELETE');
    }
    async getCustomerJobs(id, params = {}) {
        const searchParams = new URLSearchParams();
        if (params.page)
            searchParams.set('page', params.page.toString());
        if (params.page_size)
            searchParams.set('page_size', params.page_size.toString());
        const query = searchParams.toString();
        const path = `/customers/${id}/jobs${query ? `?${query}` : ''}`;
        return this.makeRequest(path);
    }
    // Employee methods
    async listEmployees(params = {}) {
        const searchParams = new URLSearchParams();
        if (params.page)
            searchParams.set('page', params.page.toString());
        if (params.page_size)
            searchParams.set('page_size', params.page_size.toString());
        if (params.is_active !== undefined)
            searchParams.set('is_active', params.is_active.toString());
        if (params.role)
            searchParams.set('role', params.role);
        const query = searchParams.toString();
        const path = `/employees${query ? `?${query}` : ''}`;
        return this.makeRequest(path);
    }
    async getEmployee(id) {
        return this.makeRequest(`/employees/${id}`);
    }
    async createEmployee(data) {
        return this.makeRequest('/employees', 'POST', data);
    }
    async updateEmployee(id, data) {
        return this.makeRequest(`/employees/${id}`, 'PATCH', data);
    }
    async getEmployeeSchedule(id, startDate, endDate) {
        const searchParams = new URLSearchParams();
        if (startDate)
            searchParams.set('start_date', startDate);
        if (endDate)
            searchParams.set('end_date', endDate);
        const query = searchParams.toString();
        const path = `/employees/${id}/schedule${query ? `?${query}` : ''}`;
        return this.makeRequest(path);
    }
    // Job methods
    async listJobs(params = {}) {
        const searchParams = new URLSearchParams();
        if (params.page)
            searchParams.set('page', params.page.toString());
        if (params.page_size)
            searchParams.set('page_size', params.page_size.toString());
        if (params.customer_id)
            searchParams.set('customer_id', params.customer_id);
        if (params.work_status)
            searchParams.set('work_status', params.work_status);
        if (params.scheduled_start_min)
            searchParams.set('scheduled_start_min', params.scheduled_start_min);
        if (params.scheduled_start_max)
            searchParams.set('scheduled_start_max', params.scheduled_start_max);
        if (params.assigned_employee_id)
            searchParams.set('assigned_employee_id', params.assigned_employee_id);
        if (params.job_type_id)
            searchParams.set('job_type_id', params.job_type_id);
        const query = searchParams.toString();
        const path = `/jobs${query ? `?${query}` : ''}`;
        return this.makeRequest(path);
    }
    async getJob(id) {
        return this.makeRequest(`/jobs/${id}`);
    }
    async createJob(data) {
        return this.makeRequest('/jobs', 'POST', data);
    }
    async updateJob(id, data) {
        return this.makeRequest(`/jobs/${id}`, 'PATCH', data);
    }
    async deleteJob(id) {
        return this.makeRequest(`/jobs/${id}`, 'DELETE');
    }
    async rescheduleJob(id, schedule) {
        return this.makeRequest(`/jobs/${id}/reschedule`, 'POST', { schedule });
    }
    async getJobLineItems(id) {
        const response = await this.makeRequest(`/jobs/${id}/line_items`);
        return response.data || [];
    }
    async updateJobLineItems(id, lineItems) {
        return this.makeRequest(`/jobs/${id}/line_items/bulk_update`, 'PUT', { line_items: lineItems });
    }
    async createJobLineItem(jobId, lineItem) {
        return this.makeRequest(`/jobs/${jobId}/line_items`, 'POST', lineItem);
    }
    async getJobLineItem(jobId, lineItemId) {
        return this.makeRequest(`/jobs/${jobId}/line_items/${lineItemId}`);
    }
    async updateJobLineItem(jobId, lineItemId, lineItem) {
        return this.makeRequest(`/jobs/${jobId}/line_items/${lineItemId}`, 'PUT', lineItem);
    }
    async deleteJobLineItem(jobId, lineItemId) {
        return this.makeRequest(`/jobs/${jobId}/line_items/${lineItemId}`, 'DELETE');
    }
    // Job Type methods
    async listJobTypes(params = {}) {
        const searchParams = new URLSearchParams();
        if (params.page)
            searchParams.set('page', params.page.toString());
        if (params.page_size)
            searchParams.set('page_size', params.page_size.toString());
        if (params.is_active !== undefined)
            searchParams.set('is_active', params.is_active.toString());
        const query = searchParams.toString();
        const path = `/job_types${query ? `?${query}` : ''}`;
        return this.makeRequest(path);
    }
    async getJobType(id) {
        return this.makeRequest(`/job_types/${id}`);
    }
    async createJobType(data) {
        return this.makeRequest('/job_types', 'POST', data);
    }
    async updateJobType(id, data) {
        return this.makeRequest(`/job_types/${id}`, 'PATCH', data);
    }
    // Appointment methods
    async listAppointments(params = {}) {
        const searchParams = new URLSearchParams();
        if (params.job_id)
            searchParams.set('job_id', params.job_id);
        if (params.scheduled_start_min)
            searchParams.set('scheduled_start_min', params.scheduled_start_min);
        if (params.scheduled_start_max)
            searchParams.set('scheduled_start_max', params.scheduled_start_max);
        if (params.assigned_employee_id)
            searchParams.set('assigned_employee_id', params.assigned_employee_id);
        if (params.status)
            searchParams.set('status', params.status);
        const query = searchParams.toString();
        if (params.job_id) {
            // Use job-specific endpoint
            const path = `/jobs/${params.job_id}/appointments${query ? `?${query}` : ''}`;
            const response = await this.makeRequest(path);
            return response.appointments || [];
        }
        else {
            // Use general appointments endpoint
            const path = `/appointments${query ? `?${query}` : ''}`;
            const response = await this.makeRequest(path);
            return response.data || [];
        }
    }
    async getAppointment(id) {
        return this.makeRequest(`/appointments/${id}`);
    }
    async createAppointment(data) {
        return this.makeRequest('/appointments', 'POST', data);
    }
    async updateAppointment(id, data) {
        return this.makeRequest(`/appointments/${id}`, 'PATCH', data);
    }
    async deleteAppointment(id) {
        return this.makeRequest(`/appointments/${id}`, 'DELETE');
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
