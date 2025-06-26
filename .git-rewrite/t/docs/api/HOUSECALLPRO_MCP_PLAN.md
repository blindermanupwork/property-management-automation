# HousecallPro MCP Server Implementation Plan

## 🎯 Executive Summary

This document outlines the comprehensive plan for creating Model Context Protocol (MCP) servers for HousecallPro's API, with complete environment separation between development and production. The MCP servers will provide Claude and other AI assistants with direct access to HousecallPro data for Customers, Employees, Jobs, Job Appointments, and Job Types.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Entities & API Endpoints](#core-entities--api-endpoints)
3. [Environment Separation Strategy](#environment-separation-strategy)
4. [MCP Server Structure](#mcp-server-structure)
5. [Authentication & Security](#authentication--security)
6. [Rate Limiting & Error Handling](#rate-limiting--error-handling)
7. [Implementation Phases](#implementation-phases)
8. [Directory Structure](#directory-structure)
9. [Tool Definitions](#tool-definitions)
10. [Testing Strategy](#testing-strategy)
11. [Deployment & Usage](#deployment--usage)

## 🏗️ Architecture Overview

### Design Principles
- **Complete Environment Isolation**: Separate MCP servers for dev/prod
- **Type Safety**: Full TypeScript implementation with strict typing
- **Resilient API Communication**: Comprehensive retry logic and rate limit handling
- **Consistent Patterns**: Follow existing Airtable MCP server patterns
- **Security First**: Credential isolation and secure token management

### Technology Stack
- **Runtime**: Node.js with TypeScript
- **MCP SDK**: @modelcontextprotocol/sdk
- **API Client**: node-fetch with custom retry logic
- **Testing**: Jest with comprehensive mocking
- **Build**: TypeScript compiler with ES modules

## 📊 Core Entities & API Endpoints

Based on the existing codebase analysis and HousecallPro API patterns:

### 1. **Customers**
```typescript
// Endpoints
GET    /customers              // List customers with pagination
GET    /customers/:id          // Get customer details
POST   /customers              // Create new customer
PATCH  /customers/:id          // Update customer
DELETE /customers/:id          // Delete customer
GET    /customers/:id/jobs     // Get customer's jobs
```

### 2. **Employees**
```typescript
// Endpoints
GET    /employees              // List employees
GET    /employees/:id          // Get employee details
POST   /employees              // Create employee
PATCH  /employees/:id          // Update employee
GET    /employees/:id/schedule // Get employee schedule
```

### 3. **Jobs**
```typescript
// Endpoints
GET    /jobs                   // List jobs with filters
GET    /jobs/:id               // Get job details
POST   /jobs                   // Create job
PATCH  /jobs/:id               // Update job
DELETE /jobs/:id               // Delete job
POST   /jobs/:id/reschedule    // Reschedule job
GET    /jobs/:id/line_items    // Get line items
PUT    /jobs/:id/line_items/bulk_update // Update line items
```

### 4. **Job Appointments**
```typescript
// Endpoints
GET    /jobs/:jobId/appointments      // List job appointments
GET    /appointments/:id              // Get appointment details
POST   /appointments                  // Create appointment
PATCH  /appointments/:id              // Update appointment
DELETE /appointments/:id              // Delete appointment
```

### 5. **Job Types**
```typescript
// Endpoints
GET    /job_types              // List job types
GET    /job_types/:id          // Get job type details
POST   /job_types              // Create job type
PATCH  /job_types/:id          // Update job type
```

## 🔐 Environment Separation Strategy

### Configuration Structure
```
config/
├── environments/
│   ├── dev/
│   │   └── .env                # DEV_HCP_TOKEN, DEV_HCP_BASE_URL
│   └── prod/
│       └── .env                # PROD_HCP_TOKEN, PROD_HCP_BASE_URL
```

### Environment Variables
```bash
# Development
DEV_HCP_TOKEN=tok_dev_xxxxx
DEV_HCP_BASE_URL=https://api.housecallpro.com
DEV_HCP_EMPLOYEE_ID=emp_dev_xxxxx

# Production
PROD_HCP_TOKEN=tok_prod_xxxxx
PROD_HCP_BASE_URL=https://api.housecallpro.com
PROD_HCP_EMPLOYEE_ID=emp_prod_xxxxx
```

### Separate MCP Servers
- `hcp-mcp-dev`: Development server with test data access
- `hcp-mcp-prod`: Production server with live data access

## 📁 MCP Server Structure

### Core Components

```typescript
// src/types.ts
export interface HCPCustomer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  address?: HCPAddress;
  created_at: string;
  updated_at: string;
}

export interface HCPJob {
  id: string;
  customer_id: string;
  address_id: string;
  work_status: 'unscheduled' | 'scheduled' | 'in_progress' | 'completed' | 'canceled';
  schedule: {
    scheduled_start: string;
    scheduled_end: string;
    arrival_window?: number;
  };
  assigned_employee_ids: string[];
  line_items: HCPLineItem[];
  job_fields?: {
    job_type_id?: string;
  };
}

export interface HCPAppointment {
  id: string;
  job_id: string;
  scheduled_start: string;
  scheduled_end: string;
  assigned_employee_ids: string[];
  status: string;
}
```

### Service Layer

```typescript
// src/hcpService.ts
export class HCPService {
  private apiKey: string;
  private baseUrl: string;
  private rateLimiter: RateLimiter;

  constructor(config: HCPConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl;
    this.rateLimiter = new RateLimiter(config.rateLimit);
  }

  // Customers
  async listCustomers(params?: ListCustomersParams): Promise<PaginatedResponse<HCPCustomer>>
  async getCustomer(id: string): Promise<HCPCustomer>
  async createCustomer(data: CreateCustomerData): Promise<HCPCustomer>
  async updateCustomer(id: string, data: UpdateCustomerData): Promise<HCPCustomer>
  async deleteCustomer(id: string): Promise<void>

  // Jobs
  async listJobs(params?: ListJobsParams): Promise<PaginatedResponse<HCPJob>>
  async getJob(id: string): Promise<HCPJob>
  async createJob(data: CreateJobData): Promise<HCPJob>
  async updateJob(id: string, data: UpdateJobData): Promise<HCPJob>
  async deleteJob(id: string): Promise<void>
  async rescheduleJob(id: string, schedule: JobSchedule): Promise<HCPJob>

  // Appointments
  async listAppointments(jobId: string): Promise<HCPAppointment[]>
  async getAppointment(id: string): Promise<HCPAppointment>
  async createAppointment(data: CreateAppointmentData): Promise<HCPAppointment>
  async updateAppointment(id: string, data: UpdateAppointmentData): Promise<HCPAppointment>
}
```

## 🔒 Authentication & Security

### Token Management
```typescript
class TokenManager {
  private static validateToken(token: string): boolean {
    // Token validation logic
    return token.startsWith('tok_') && token.length > 20;
  }

  static getToken(environment: 'dev' | 'prod'): string {
    const token = process.env[`${environment.toUpperCase()}_HCP_TOKEN`];
    if (!token || !this.validateToken(token)) {
      throw new Error(`Invalid or missing ${environment} HCP token`);
    }
    return token;
  }
}
```

### Request Authentication
```typescript
private getAuthHeaders(): Headers {
  return {
    'Authorization': `Token ${this.apiKey}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'HCP-MCP-Server/1.0.0'
  };
}
```

## ⚡ Rate Limiting & Error Handling

### Rate Limiter Implementation
```typescript
class RateLimiter {
  private queue: Array<() => Promise<any>> = [];
  private processing = false;
  private requestsPerMinute: number;
  private retryAfter?: Date;

  constructor(requestsPerMinute = 60) {
    this.requestsPerMinute = requestsPerMinute;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;
    
    if (this.retryAfter && new Date() < this.retryAfter) {
      const waitTime = this.retryAfter.getTime() - Date.now();
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.processing = true;
    const minInterval = 60000 / this.requestsPerMinute;

    while (this.queue.length > 0) {
      const startTime = Date.now();
      const task = this.queue.shift()!;
      
      try {
        await task();
      } catch (error: any) {
        if (error.status === 429) {
          const resetTime = error.headers?.['RateLimit-Reset'];
          if (resetTime) {
            this.retryAfter = new Date(resetTime);
          }
        }
      }

      const elapsed = Date.now() - startTime;
      if (elapsed < minInterval) {
        await new Promise(resolve => setTimeout(resolve, minInterval - elapsed));
      }
    }

    this.processing = false;
  }
}
```

### Error Handling
```typescript
class HCPError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'HCPError';
  }
}

async function withRetry<T>(
  operation: () => Promise<T>,
  maxAttempts = 3,
  backoffMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === maxAttempts - 1) throw error;
      
      const isRetryable = 
        error.status === 429 || // Rate limit
        error.status === 503 || // Service unavailable
        error.code === 'ECONNRESET';
      
      if (!isRetryable) throw error;
      
      const delay = backoffMs * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  throw new Error('Max retry attempts reached');
}
```

## 📝 Tool Definitions

### Customer Tools
```typescript
{
  name: "mcp__hcp-{env}__list_customers",
  description: "List customers with optional filters",
  parameters: {
    page: { type: "number", description: "Page number (default: 1)" },
    per_page: { type: "number", description: "Items per page (default: 20, max: 100)" },
    search: { type: "string", description: "Search customers by name, email, or phone" },
    created_after: { type: "string", description: "Filter by creation date (ISO 8601)" }
  }
}

{
  name: "mcp__hcp-{env}__get_customer",
  description: "Get detailed information about a specific customer",
  parameters: {
    customer_id: { type: "string", required: true, description: "Customer ID" }
  }
}

{
  name: "mcp__hcp-{env}__create_customer",
  description: "Create a new customer",
  parameters: {
    name: { type: "string", required: true },
    email: { type: "string" },
    phone: { type: "string" },
    address: { type: "object" }
  }
}
```

### Job Tools
```typescript
{
  name: "mcp__hcp-{env}__list_jobs",
  description: "List jobs with comprehensive filtering options",
  parameters: {
    page: { type: "number" },
    per_page: { type: "number" },
    customer_id: { type: "string", description: "Filter by customer" },
    work_status: { 
      type: "string", 
      enum: ["unscheduled", "scheduled", "in_progress", "completed", "canceled"] 
    },
    scheduled_start_min: { type: "string", description: "Minimum scheduled start (ISO 8601)" },
    scheduled_start_max: { type: "string", description: "Maximum scheduled start (ISO 8601)" },
    assigned_employee_id: { type: "string", description: "Filter by assigned employee" }
  }
}

{
  name: "mcp__hcp-{env}__create_job",
  description: "Create a new job with schedule and assignments",
  parameters: {
    customer_id: { type: "string", required: true },
    address_id: { type: "string", required: true },
    schedule: { 
      type: "object",
      properties: {
        scheduled_start: { type: "string", required: true },
        scheduled_end: { type: "string", required: true },
        arrival_window: { type: "number" }
      }
    },
    assigned_employee_ids: { type: "array", items: { type: "string" } },
    job_type_id: { type: "string" },
    line_items: { type: "array" }
  }
}

{
  name: "mcp__hcp-{env}__reschedule_job",
  description: "Reschedule an existing job",
  parameters: {
    job_id: { type: "string", required: true },
    schedule: {
      type: "object",
      properties: {
        scheduled_start: { type: "string", required: true },
        scheduled_end: { type: "string", required: true }
      }
    }
  }
}
```

### Appointment Tools
```typescript
{
  name: "mcp__hcp-{env}__list_appointments",
  description: "List appointments for a specific job",
  parameters: {
    job_id: { type: "string", required: true }
  }
}

{
  name: "mcp__hcp-{env}__update_appointment",
  description: "Update appointment details",
  parameters: {
    appointment_id: { type: "string", required: true },
    scheduled_start: { type: "string" },
    scheduled_end: { type: "string" },
    assigned_employee_ids: { type: "array", items: { type: "string" } }
  }
}
```

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up TypeScript project structure
- [ ] Implement core HCP API client with authentication
- [ ] Create rate limiting and retry logic
- [ ] Set up environment configuration system
- [ ] Implement comprehensive error handling

### Phase 2: Customer & Employee Management (Week 2)
- [ ] Implement Customer service methods
- [ ] Create Customer MCP tools
- [ ] Implement Employee service methods
- [ ] Create Employee MCP tools
- [ ] Add comprehensive unit tests

### Phase 3: Job Management (Week 3)
- [ ] Implement Job service methods
- [ ] Create Job MCP tools
- [ ] Implement line item management
- [ ] Add job template support
- [ ] Create integration tests

### Phase 4: Appointments & Job Types (Week 4)
- [ ] Implement Appointment service methods
- [ ] Create Appointment MCP tools
- [ ] Implement Job Type service methods
- [ ] Create Job Type MCP tools
- [ ] Add end-to-end tests

### Phase 5: Polish & Documentation (Week 5)
- [ ] Comprehensive documentation
- [ ] Performance optimization
- [ ] Security audit
- [ ] Deployment scripts
- [ ] Usage examples

## 📂 Directory Structure

```
tools/
├── hcp-mcp-dev/                    # Development MCP server
│   ├── src/
│   │   ├── index.ts               # MCP server entry point
│   │   ├── hcpService.ts          # HCP API service layer
│   │   ├── mcpServer.ts           # MCP server implementation
│   │   ├── types.ts               # TypeScript type definitions
│   │   ├── rateLimiter.ts         # Rate limiting implementation
│   │   ├── errors.ts              # Error handling
│   │   └── utils/
│   │       ├── auth.ts            # Authentication utilities
│   │       ├── retry.ts           # Retry logic
│   │       └── validators.ts      # Input validation
│   ├── tests/
│   │   ├── hcpService.test.ts
│   │   ├── mcpServer.test.ts
│   │   └── integration.test.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
│
├── hcp-mcp-prod/                   # Production MCP server (similar structure)
│
└── hcp-mcp-common/                 # Shared utilities
    ├── src/
    │   ├── types.ts               # Shared type definitions
    │   ├── constants.ts           # API constants
    │   └── validators.ts          # Common validators
    └── package.json
```

## 🧪 Testing Strategy

### Unit Tests
```typescript
// hcpService.test.ts
describe('HCPService', () => {
  describe('listCustomers', () => {
    it('should return paginated customer list', async () => {
      const mockResponse = {
        data: [{ id: 'cust_123', name: 'Test Customer' }],
        page: 1,
        per_page: 20,
        total: 1
      };
      
      fetchMock.mockResponseOnce(JSON.stringify(mockResponse));
      
      const result = await service.listCustomers({ page: 1 });
      expect(result).toEqual(mockResponse);
    });

    it('should handle rate limiting gracefully', async () => {
      fetchMock.mockResponseOnce('', { 
        status: 429, 
        headers: { 'RateLimit-Reset': new Date(Date.now() + 1000).toISOString() }
      });
      fetchMock.mockResponseOnce(JSON.stringify({ data: [] }));
      
      const result = await service.listCustomers();
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
  });
});
```

### Integration Tests
```typescript
// integration.test.ts
describe('HCP MCP Integration', () => {
  it('should create job and retrieve appointments', async () => {
    // Create customer
    const customer = await mcp.call('mcp__hcp-dev__create_customer', {
      name: 'Integration Test Customer',
      email: 'test@example.com'
    });

    // Create job
    const job = await mcp.call('mcp__hcp-dev__create_job', {
      customer_id: customer.id,
      address_id: customer.address_id,
      schedule: {
        scheduled_start: '2025-01-15T10:00:00Z',
        scheduled_end: '2025-01-15T12:00:00Z'
      }
    });

    // List appointments
    const appointments = await mcp.call('mcp__hcp-dev__list_appointments', {
      job_id: job.id
    });

    expect(appointments).toHaveLength(1);
    expect(appointments[0].job_id).toBe(job.id);
  });
});
```

## 🚢 Deployment & Usage

### Installation
```bash
# Development environment
cd tools/hcp-mcp-dev
npm install
npm run build

# Production environment
cd tools/hcp-mcp-prod
npm install
npm run build
```

### Configuration
```bash
# Set up environment variables
cp config/environments/dev/.env.example config/environments/dev/.env
cp config/environments/prod/.env.example config/environments/prod/.env

# Edit with your credentials
nano config/environments/dev/.env
nano config/environments/prod/.env
```

### Starting the MCP Servers
```bash
# Development
npm run start:dev

# Production
npm run start:prod
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "hcp-dev": {
      "command": "node",
      "args": ["/path/to/tools/hcp-mcp-dev/dist/index.js"],
      "env": {
        "NODE_ENV": "development"
      }
    },
    "hcp-prod": {
      "command": "node",
      "args": ["/path/to/tools/hcp-mcp-prod/dist/index.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### Usage Examples

#### List Recent Jobs
```
Use the mcp__hcp-dev__list_jobs tool to show me all scheduled jobs for today
```

#### Create a New Customer
```
Use mcp__hcp-prod__create_customer to add John Smith with email john@example.com and phone 555-0123
```

#### Reschedule a Job
```
Use mcp__hcp-dev__reschedule_job to move job job_abc123 to tomorrow at 2:00 PM
```

## 🔍 Monitoring & Observability

### Logging
```typescript
class Logger {
  private context: string;

  constructor(context: string) {
    this.context = context;
  }

  info(message: string, meta?: any) {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'info',
      context: this.context,
      message,
      ...meta
    }));
  }

  error(message: string, error?: Error, meta?: any) {
    console.error(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'error',
      context: this.context,
      message,
      error: error?.message,
      stack: error?.stack,
      ...meta
    }));
  }
}
```

### Metrics
- Request count by endpoint
- Response time percentiles
- Error rates by type
- Rate limit hits
- Active connections

## 🎯 Success Criteria

1. **Functionality**: All core HCP entities accessible via MCP
2. **Reliability**: 99.9% uptime with graceful error handling
3. **Performance**: Average response time < 500ms
4. **Security**: Complete credential isolation between environments
5. **Developer Experience**: Comprehensive documentation and examples
6. **Testing**: >90% code coverage with unit and integration tests

## 📚 References

- [HousecallPro API Documentation](https://docs.housecallpro.com/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [TypeScript Best Practices](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)
- [Node.js Security Checklist](https://blog.risingstack.com/node-js-security-checklist/)

## 🤝 Next Steps

1. Review and approve this implementation plan
2. Set up development environment and credentials
3. Begin Phase 1 implementation
4. Schedule weekly progress reviews
5. Plan production deployment timeline

---

**Created**: 2025-01-03
**Author**: Claude AI Assistant
**Status**: Draft - Awaiting Review