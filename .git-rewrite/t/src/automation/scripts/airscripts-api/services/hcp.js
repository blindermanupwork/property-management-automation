import fetch from 'node-fetch';
import { logger } from '../utils/logger.js';

const HCP_API_BASE = 'https://api.housecallpro.com';
const HCP_TOKEN = process.env.HCP_TOKEN;

class HCPClient {
  constructor() {
    if (!HCP_TOKEN) {
      throw new Error('HCP_TOKEN environment variable not set');
    }
  }

  async request(path, method = 'GET', body = null) {
    const maxRetries = 3;
    let retry = 0;
    
    while (retry < maxRetries) {
      try {
        const response = await fetch(`${HCP_API_BASE}${path}`, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': `Token ${HCP_TOKEN}`
          },
          body: body ? JSON.stringify(body) : undefined
        });
        
        // Handle rate limiting
        if (response.status === 429) {
          retry++;
          const resetHeader = response.headers.get('RateLimit-Reset');
          const waitTime = resetHeader 
            ? Math.max(new Date(resetHeader) - new Date(), 1000)
            : 1000 * Math.pow(2, retry);
          
          logger.warn('HCP rate limit hit', { path, retry, waitTime });
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HCP API error: ${response.status} - ${errorText}`);
        }
        
        return await response.json();
        
      } catch (error) {
        if (retry === maxRetries - 1) {
          throw error;
        }
        retry++;
        const backoff = 1000 * Math.pow(2, retry);
        logger.warn('HCP request failed, retrying', { 
          path, 
          retry, 
          backoff, 
          error: error.message 
        });
        await new Promise(resolve => setTimeout(resolve, backoff));
      }
    }
  }

  async createJob(jobData) {
    logger.info('Creating HCP job', { 
      customerId: jobData.customer_id,
      addressId: jobData.address_id 
    });
    return await this.request('/jobs', 'POST', jobData);
  }

  async getJob(jobId) {
    logger.info('Fetching HCP job', { jobId });
    return await this.request(`/jobs/${jobId}`);
  }

  async updateJob(jobId, updates) {
    logger.info('Updating HCP job', { jobId });
    return await this.request(`/jobs/${jobId}`, 'PATCH', updates);
  }

  async deleteJob(jobId) {
    logger.info('Deleting HCP job', { jobId });
    return await this.request(`/jobs/${jobId}`, 'DELETE');
  }

  async getJobLineItems(jobId) {
    logger.info('Fetching job line items', { jobId });
    const response = await this.request(`/jobs/${jobId}/line_items`);
    return response.data || [];
  }

  async updateJobLineItems(jobId, lineItems) {
    logger.info('Updating job line items', { jobId, count: lineItems.length });
    return await this.request(
      `/jobs/${jobId}/line_items/bulk_update`, 
      'PUT', 
      { line_items: lineItems }
    );
  }

  async getJobAppointments(jobId) {
    logger.info('Fetching job appointments', { jobId });
    const response = await this.request(`/jobs/${jobId}/appointments`);
    return response.appointments || [];
  }

  async rescheduleJob(jobId, schedule) {
    logger.info('Rescheduling job', { jobId, schedule });
    return await this.request(`/jobs/${jobId}/reschedule`, 'POST', { schedule });
  }
}

// Singleton instance
let hcpClient;

export function getHCPClient() {
  if (!hcpClient) {
    hcpClient = new HCPClient();
  }
  return hcpClient;
}