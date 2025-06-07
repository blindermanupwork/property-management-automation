/**
 * HousecallPro API Service
 * Handles all API communication with rate limiting and error handling
 */
import fetch from 'node-fetch';
import { RateLimiter } from './rateLimiter.js';
import { HCPError } from '../../hcp-mcp-common/src/index.js';
import { CacheService } from '../../hcp-mcp-common/src/cacheService.js';
import { AnalysisService } from '../../hcp-mcp-common/src/analysisService.js';
export class HCPService {
    apiKey;
    baseUrl;
    environment;
    rateLimiter;
    cacheService;
    analysisService;
    constructor(config) {
        this.apiKey = config.apiKey;
        this.baseUrl = config.baseUrl;
        this.environment = config.environment;
        this.rateLimiter = new RateLimiter(config.rateLimit?.requestsPerMinute || 60);
        this.cacheService = new CacheService(config.cache);
        this.analysisService = new AnalysisService(config.environment);
    }
    async makeRequest(path, method = 'GET', body, retries = 3, operationName) {
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
                    console.log(`[${this.environment}] ${method} ${url}`);
                    console.log(`[${this.environment}] Full URL: ${url}`);
                    const response = await fetch(url, {
                        method,
                        headers,
                        body: body ? JSON.stringify(body) : null
                    });
                    const responseText = await response.text();
                    if (!response.ok) {
                        // Enhanced error handling with specific types
                        let errorType = 'APIError';
                        let suggestion = 'Check your request parameters and try again';
                        let context = `${method} request to ${path}`;
                        if (response.status === 404) {
                            if (path.includes('/customers/') && path.includes('/jobs')) {
                                errorType = 'CustomerHasNoJobs';
                                suggestion = 'Use list_jobs with customer_id filter instead of get_customer_jobs';
                                context = `Customer exists but may have no jobs`;
                            }
                            else if (path.includes('/customers/')) {
                                errorType = 'CustomerNotFound';
                                suggestion = 'Verify the customer ID is correct';
                            }
                        }
                        else if (response.status === 401 || response.status === 403) {
                            errorType = 'InvalidPermissions';
                            suggestion = 'Check your API key has the required permissions';
                        }
                        const error = new HCPError(`API request failed: ${response.status} ${response.statusText}`, response.status, undefined, responseText);
                        // Add enhanced error details
                        error.type = errorType;
                        error.context = context;
                        error.suggestion = suggestion;
                        error.headers = Object.fromEntries(response.headers.entries());
                        throw error;
                    }
                    // Handle empty responses
                    if (!responseText || responseText.trim() === '') {
                        return {};
                    }
                    try {
                        const data = JSON.parse(responseText);
                        // Check if response should be cached (only for GET requests)
                        if (method === 'GET' && operationName && this.cacheService.shouldCache(data, operationName)) {
                            try {
                                const cachedResponse = await this.cacheService.cacheResponse(data, operationName, this.environment, { path, method });
                                console.log(`[${this.environment}] Cached large response: ${this.cacheService.getSummary(data, operationName)}`);
                                return cachedResponse;
                            }
                            catch (cacheError) {
                                console.warn(`[${this.environment}] Cache write failed:`, cacheError);
                                // Continue with normal response if caching fails
                                return data;
                            }
                        }
                        return data;
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
        if (params.q)
            searchParams.set('q', params.q);
        if (params.search)
            searchParams.set('search', params.search);
        if (params.sort_by)
            searchParams.set('sort_by', params.sort_by);
        if (params.sort_direction)
            searchParams.set('sort_direction', params.sort_direction);
        if (params.created_after)
            searchParams.set('created_after', params.created_after);
        if (params.created_before)
            searchParams.set('created_before', params.created_before);
        if (params.tags)
            searchParams.set('tags', params.tags.join(','));
        const query = searchParams.toString();
        const path = `/customers${query ? `?${query}` : ''}`;
        return this.makeRequest(path, 'GET', undefined, 3, 'list_customers');
    }
    async getCustomer(id) {
        return this.makeRequest(`/customers/${id}`, 'GET', undefined, 3, 'get_customer');
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
        return this.makeRequest(path, 'GET', undefined, 3, 'get_customer_jobs');
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
        return this.makeRequest(path, 'GET', undefined, 3, 'list_employees');
    }
    async getEmployee(id) {
        return this.makeRequest(`/employees/${id}`, 'GET', undefined, 3, 'get_employee');
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
        return this.makeRequest(path, 'GET', undefined, 3, 'get_employee_schedule');
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
        return this.makeRequest(path, 'GET', undefined, 3, 'list_jobs');
    }
    async getJob(id) {
        return this.makeRequest(`/jobs/${id}`, 'GET', undefined, 3, 'get_job');
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
        const response = await this.makeRequest(`/jobs/${id}/line_items`, 'GET', undefined, 3, 'get_job_line_items');
        // Handle cached responses
        if ('_cached' in response) {
            return response;
        }
        return response.data || [];
    }
    async updateJobLineItems(id, lineItems) {
        return this.makeRequest(`/jobs/${id}/line_items/bulk_update`, 'PUT', { line_items: lineItems });
    }
    async createJobLineItem(jobId, lineItem) {
        return this.makeRequest(`/jobs/${jobId}/line_items`, 'POST', lineItem);
    }
    async getJobLineItem(jobId, lineItemId) {
        return this.makeRequest(`/jobs/${jobId}/line_items/${lineItemId}`, 'GET', undefined, 3, 'get_job_line_item');
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
        return this.makeRequest(path, 'GET', undefined, 3, 'list_job_types');
    }
    async getJobType(id) {
        return this.makeRequest(`/job_types/${id}`, 'GET', undefined, 3, 'get_job_type');
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
            const response = await this.makeRequest(path, 'GET', undefined, 3, 'list_appointments');
            // Handle cached responses
            if ('_cached' in response) {
                return response;
            }
            return response.appointments || [];
        }
        else {
            // Use general appointments endpoint
            const path = `/appointments${query ? `?${query}` : ''}`;
            const response = await this.makeRequest(path, 'GET', undefined, 3, 'list_appointments');
            // Handle cached responses
            if ('_cached' in response) {
                return response;
            }
            return response.data || [];
        }
    }
    async getAppointment(id) {
        return this.makeRequest(`/appointments/${id}`, 'GET', undefined, 3, 'get_appointment');
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
    // Enhanced search methods
    async searchAddresses(params) {
        try {
            // If customer_id is provided, get that customer's addresses directly
            if (params.customer_id) {
                const customer = await this.getCustomer(params.customer_id);
                // Handle cached response
                let customerData;
                if ('_cached' in customer) {
                    // Read from cache file
                    const cacheContent = await this.cacheService.searchCache(customer._filePath, '', '');
                    customerData = cacheContent[0] || {};
                }
                else {
                    customerData = customer;
                }
                if (customerData.addresses) {
                    return customerData.addresses
                        .filter((addr) => this.matchesAddressFilter(addr, params))
                        .map((addr) => ({
                        address: addr,
                        customer: {
                            id: customerData.id,
                            first_name: customerData.first_name,
                            last_name: customerData.last_name,
                            company: customerData.company
                        }
                    }));
                }
                return [];
            }
            // Build server-side search query from address components
            const searchTerms = [];
            if (params.street)
                searchTerms.push(params.street);
            if (params.city)
                searchTerms.push(params.city);
            if (params.state)
                searchTerms.push(params.state);
            if (params.zip)
                searchTerms.push(params.zip);
            if (params.customer_name)
                searchTerms.push(params.customer_name);
            const searchQuery = searchTerms.join(' ').trim();
            let results = [];
            // If we have search terms, use server-side filtering first (MUCH more efficient)
            if (searchQuery) {
                console.log(`[${this.environment}] Address search using server-side query: "${searchQuery}"`);
                const customersResponse = await this.listCustomers({
                    q: searchQuery,
                    page_size: 200 // Use max page size for efficiency
                });
                let customers = [];
                if ('_cached' in customersResponse) {
                    const cacheResults = await this.cacheService.searchCache(customersResponse._filePath, '', '');
                    customers = cacheResults;
                }
                else {
                    customers = customersResponse.data || [];
                }
                console.log(`[${this.environment}] Server-side search returned ${customers.length} customers`);
                // Filter the small result set locally for exact matches
                for (const customer of customers) {
                    if (customer.addresses) {
                        const matchingAddresses = customer.addresses
                            .filter((addr) => this.matchesAddressFilter(addr, params))
                            .map((addr) => ({
                            address: addr,
                            customer: {
                                id: customer.id,
                                first_name: customer.first_name,
                                last_name: customer.last_name,
                                company: customer.company
                            }
                        }));
                        results.push(...matchingAddresses);
                    }
                }
                console.log(`[${this.environment}] Found ${results.length} matching addresses after local filtering`);
                return results;
            }
            // Fallback: If no search terms provided, scan all customers (warn about inefficiency)
            console.warn(`[${this.environment}] No search terms provided - falling back to full customer scan (INEFFICIENT!)`);
            let page = 1;
            const pageSize = 200; // Use max page size
            let hasMore = true;
            while (hasMore) {
                const customersResponse = await this.listCustomers({
                    page,
                    page_size: pageSize
                });
                let customers = [];
                if ('_cached' in customersResponse) {
                    // For cached responses, need to search the cache
                    const cacheResults = await this.cacheService.searchCache(customersResponse._filePath, '', '');
                    customers = cacheResults;
                }
                else {
                    customers = customersResponse.data || [];
                }
                // Filter customers' addresses
                for (const customer of customers) {
                    if (customer.addresses) {
                        const matchingAddresses = customer.addresses
                            .filter((addr) => this.matchesAddressFilter(addr, params))
                            .map((addr) => ({
                            address: addr,
                            customer: {
                                id: customer.id,
                                first_name: customer.first_name,
                                last_name: customer.last_name,
                                company: customer.company
                            }
                        }));
                        results.push(...matchingAddresses);
                    }
                }
                // Check if we have more pages (only for non-cached responses)
                if ('_cached' in customersResponse) {
                    hasMore = false; // Cached responses include all data
                }
                else {
                    hasMore = customers.length === pageSize;
                    page++;
                }
            }
            return results;
        }
        catch (error) {
            throw this.createDetailedError('APIError', `Address search failed: ${error.message}`, 'Error occurred while searching addresses', 'Try with more specific search criteria');
        }
    }
    async getJobsByAddress(addressId, params = {}) {
        try {
            const jobParams = {
                ...params,
                address_id: addressId,
                page_size: 200 // Get max results
            };
            // Remove address_id from params since it's not a valid filter for list_jobs
            const { address_id, ...listJobsParams } = jobParams;
            // We need to search through jobs to find ones matching the address
            const results = [];
            let page = 1;
            let hasMore = true;
            while (hasMore) {
                const jobsResponse = await this.listJobs({
                    ...listJobsParams,
                    page,
                    page_size: 200
                });
                let jobs = [];
                if ('_cached' in jobsResponse) {
                    const cacheResults = await this.cacheService.searchCache(jobsResponse._filePath, addressId, 'address_id');
                    jobs = cacheResults;
                }
                else {
                    jobs = (jobsResponse.data || []).filter((job) => job.address_id === addressId);
                }
                results.push(...jobs);
                // Check if we have more pages
                if ('_cached' in jobsResponse) {
                    hasMore = false;
                }
                else {
                    hasMore = (jobsResponse.data || []).length === 200;
                    page++;
                }
            }
            return results;
        }
        catch (error) {
            throw this.createDetailedError('APIError', `Jobs by address search failed: ${error.message}`, `Failed to find jobs for address ${addressId}`, 'Verify the address ID exists and try again');
        }
    }
    // Helper methods for enhanced error handling
    createDetailedError(type, message, context, suggestion) {
        const error = new Error(message);
        error.type = type;
        error.context = context;
        error.suggestion = suggestion;
        return error;
    }
    matchesAddressFilter(address, params) {
        if (params.street && !address.street?.toLowerCase().includes(params.street.toLowerCase())) {
            return false;
        }
        if (params.city && !address.city?.toLowerCase().includes(params.city.toLowerCase())) {
            return false;
        }
        if (params.state && !address.state?.toLowerCase().includes(params.state.toLowerCase())) {
            return false;
        }
        if (params.zip && !address.zip?.includes(params.zip)) {
            return false;
        }
        return true;
    }
    // Cache management methods
    async searchCache(filePath, searchTerm, fieldPath) {
        return this.cacheService.searchCache(filePath, searchTerm, fieldPath);
    }
    async listCacheFiles(operation) {
        return this.cacheService.listCacheFiles(this.environment, operation);
    }
    async cleanupCache() {
        return this.cacheService.cleanup(this.environment);
    }
    getCacheSummary(data, operation) {
        return this.cacheService.getSummary(data, operation);
    }
    // Analysis methods
    async analyzeLaundryJobs() {
        return this.analysisService.analyzeLaundryJobs();
    }
    async analyzeServiceItems(itemPattern) {
        return this.analysisService.analyzeServiceItems(itemPattern);
    }
    async analyzeCustomerRevenue(customerId) {
        return this.analysisService.analyzeCustomerRevenue(customerId);
    }
    async analyzeJobStatistics() {
        return this.analysisService.analyzeJobStatistics();
    }
    async generateAnalysisReport() {
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
