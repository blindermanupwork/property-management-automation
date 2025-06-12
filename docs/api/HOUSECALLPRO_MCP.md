## Overview

This document outlines a comprehensive plan to build, test, and maintain a Housecall Pro–backed MCP (Model Context Protocol) server, following patterns established by existing MCP server implementations. It covers project structure, environment setup, tool definitions, CI/CD, deployment, and ongoing maintenance. Wherever possible, each section provides detailed steps and best practices to ensure a robust, modular, and maintainable server that exposes key Housecall Pro functionality to LLM clients via MCP.

---

## Table of Contents

1. [Objectives](#objectives)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Environment Setup](#environment-setup)
5. [Utility Modules](#utility-modules)
6. [Tool Definitions](#tool-definitions)

   * 6.1. [Customer Tools](#61-customer-tools)
   * 6.2. [Job Tools](#62-job-tools)
   * 6.3. [Invoice Tools](#63-invoice-tools)
   * 6.4. [Additional Resources](#64-additional-resources)
7. [Webhook Prompts](#webhook-prompts)
8. [Server Entry Point](#server-entry-point)
9. [Testing Strategy](#testing-strategy)

   * 9.1. [Unit Tests](#91-unit-tests)
   * 9.2. [Integration Tests](#92-integration-tests)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Containerization & Deployment](#containerization--deployment)
12. [Versioning & Release Management](#versioning--release-management)
13. [Monitoring & Maintenance](#monitoring--maintenance)
14. [Documentation & Onboarding](#documentation--onboarding)

---

## Objectives

* **Expose Housecall Pro API via MCP:** Create a set of MCP tools and resources that wrap Housecall Pro REST endpoints (e.g., customers, jobs, invoices), allowing LLM clients to programmatically query and manipulate data.
* **Support Webhooks:** Define MCP prompts to handle incoming Housecall Pro webhook events (e.g., `job.created`), converting them into prompt updates for LLMs.
* **Modular, Scalable Architecture:** Follow the pattern of existing MCP servers (e.g., Airtable, Google Maps), keeping each integration in its own directory, with clear separation of concerns.
* **Secure Configuration:** Load API keys and secrets via environment variables, never hard-coding sensitive data.
* **Automated Testing & CI/CD:** Implement a comprehensive test suite (unit and integration) and a GitHub Actions workflow to build, test, and version-check the codebase.
* **Containerization:** Provide a Dockerfile to deploy the MCP server in containerized environments.
* **Ongoing Maintenance:** Establish processes to track Housecall Pro API changes, update tools accordingly, and maintain version consistency.

---

## Prerequisites

* **Node.js 18 LTS (or later)** and npm
* **TypeScript 4.9+** (installed via npm)
* **Housecall Pro MAX Plan** (required to generate API keys and use webhooks)
* A basic familiarity with MCP (Model Context Protocol) concepts and `@modelcontextprotocol/mcp-sdk` (FastMCP)
* A GitHub account to manage the repository and leverage GitHub Actions for CI/CD
* (Optional) Docker installed locally for building and testing the container

---

## Project Structure

```
housecallpro-mcp-server/
├── .github/
│   ├── workflows/
│   │   ├── build.yaml         # CI workflow: build, test, version-check
│   │   └── publish.yaml       # Optional: publish to NPM or Docker registry
├── src/
│   ├── index.ts               # Server entry point: instantiate MCP, register tools/prompts
│   ├── utils/
│   │   ├── httpClient.ts      # Axios client configured for Housecall Pro
│   │   └── types.ts           # TypeScript interfaces for Housecall Pro objects
│   ├── tools/
│   │   ├── getCustomer.ts     # Tool: GET /customers/{id}
│   │   ├── listCustomers.ts   # Tool: GET /customers
│   │   ├── createJob.ts       # Tool: POST /jobs
│   │   ├── updateJob.ts       # Tool: PUT /jobs/{id}
│   │   ├── cancelJob.ts       # Tool: DELETE /jobs/{id}
│   │   ├── listInvoices.ts    # Tool: GET /invoices
│   │   ├── getInvoice.ts      # Tool: GET /invoices/{id}
│   │   └── …                  # Additional resource wrappers (e.g., leads, estimates)
│   └── prompts/
│       └── onJobCreated.ts    # Prompt: handle job.created webhook payload
├── test/
│   ├── unit/
│   │   ├── getCustomer.test.ts
│   │   ├── createJob.test.ts
│   │   └── …                  # Other unit tests
│   └── integration/
│       ├── getCustomer.int.test.ts
│       ├── createJob.int.test.ts
│       └── …                  # Integration tests calling real or sandbox API
├── .env.example               # Example environment variables file
├── .gitignore                 # Ignore node_modules/, build/, .env, etc.
├── Dockerfile                 # Containerization instructions
├── package.json               # Dependencies, scripts, metadata
├── tsconfig.json              # TypeScript configuration
├── version.ts                 # Single source of truth for package version
├── smithery.yaml              # Manifest for Smithery (optional)
└── README.md                  # Overview, setup, usage, examples
```

---

## Environment Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/housecallpro-mcp-server.git
   cd housecallpro-mcp-server
   ```

2. **Install Dependencies**

   ```bash
   npm install
   ```

3. **Create a `.env` File**

   * Copy `.env.example` to `.env`
   * Populate the following environment variables:

     ```
     HCP_API_KEY=your_housecallpro_api_key
     HCP_WEBHOOK_SECRET=your_optional_webhook_signing_secret
     PORT=8002                      # Optional: default MCP port
     ```
   * **Do not** commit your `.env` file; it is included in `.gitignore`.

4. **TypeScript Compilation**

   ```bash
   npm run build
   ```

   * Verifies that TypeScript compiles without errors.
   * Produces compiled JavaScript in `dist/`.

---

## Utility Modules

### `src/utils/httpClient.ts`

* **Purpose:** Create and export a preconfigured Axios instance for all HTTP calls to Housecall Pro.
* **Key Points:**

  * Reads `HCP_API_KEY` from `process.env`.
  * Sets `baseURL` to `https://api.housecallpro.com/v1`.
  * Adds headers:

    ```ts
    {
      "Company-API-Key": process.env.HCP_API_KEY,
      "Content-Type": "application/json",
      Accept: "application/json"
    }
    ```
  * Exports an `AxiosInstance` named `hcpClient`.
* **Sample Code:**

  ```ts
  import axios, { AxiosInstance } from "axios";

  const BASE_URL = "https://api.housecallpro.com/v1";
  const API_KEY_HEADER = "Company-API-Key";

  export function createHousecallClient(): AxiosInstance {
    const apiKey = process.env.HCP_API_KEY;
    if (!apiKey) {
      throw new Error("HCP_API_KEY is not set");
    }
    return axios.create({
      baseURL: BASE_URL,
      headers: {
        [API_KEY_HEADER]: apiKey,
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      timeout: 10000
    });
  }
  ```

  * **Location:** `src/utils/httpClient.ts`

### `src/utils/types.ts`

* **Purpose:** Define TypeScript interfaces for frequently used Housecall Pro objects (e.g., `Customer`, `Job`, `Invoice`), ensuring type safety.
* **Key Interfaces:**

  ```ts
  export interface Customer {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    mobile_phone?: string;
    // … other fields as needed
  }

  export interface Job {
    id: string;
    customer_id: string;
    service_address: string;
    schedule: string;         // ISO 8601 datetime
    status: string;
    details?: string;
    // … other fields
  }

  export interface Invoice {
    id: string;
    job_id: string;
    total_amount: number;
    status: string;
    // … other fields
  }
  ```

  * **Location:** `src/utils/types.ts`

---

## Tool Definitions

Each tool definition uses `@mcp.tool()` (from `@modelcontextprotocol/mcp-sdk`) to declare:

* **`name`**: Unique identifier for the tool.
* **`description`**: Brief summary of its purpose.
* **`parameters`**: JSON schema describing expected arguments.
* **`run`**: Async function that calls the Housecall Pro API via `hcpClient` and returns parsed data or throws an error.

Below are recommended tool modules to cover core Housecall Pro functionality:

### 6.1. Customer Tools

#### `src/tools/listCustomers.ts`

* **Purpose:** Retrieve a paginated list of customers.
* **Endpoint:** `GET /customers?limit={limit}&offset={offset}`
* **Parameters:**

  ```jsonc
  {
    "properties": {
      "limit": { "type": "integer", "minimum": 1, "maximum": 100 },
      "offset": { "type": "integer", "minimum": 0 }
    },
    "required": []
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function listCustomersTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "list_customers",
      description: "Retrieve a list of Housecall Pro customers (paginated)",
      parameters: {
        type: "object",
        properties: {
          limit: { type: "integer", minimum: 1, maximum: 100 },
          offset: { type: "integer", minimum: 0 }
        }
      },
      run: async (args) => {
        const { limit = 50, offset = 0 } = args as { limit?: number; offset?: number };
        const response = await client.get("/customers", {
          params: { limit, offset }
        });
        return response.data; // Assume shape { customers: Customer[], total: number, ... }
      }
    };
  }
  ```
* **Location:** `src/tools/listCustomers.ts`

#### `src/tools/getCustomer.ts`

* **Purpose:** Retrieve details for a single customer by ID.
* **Endpoint:** `GET /customers/{customer_id}`
* **Parameters:**

  ```jsonc
  {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" }
    },
    "required": ["customer_id"]
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function getCustomerTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "get_customer",
      description: "Retrieve a Housecall Pro customer by ID",
      parameters: {
        type: "object",
        properties: {
          customer_id: { type: "string" }
        },
        required: ["customer_id"]
      },
      run: async (args) => {
        const { customer_id } = args as { customer_id: string };
        const response = await client.get(`/customers/${customer_id}`);
        return response.data; // Assume shape Customer
      }
    };
  }
  ```
* **Location:** `src/tools/getCustomer.ts`

### 6.2. Job Tools

#### `src/tools/createJob.ts`

* **Purpose:** Create a new job tied to an existing customer.
* **Endpoint:** `POST /jobs`
* **Parameters:**

  ```jsonc
  {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "service_address": { "type": "string" },
      "schedule": { "type": "string", "format": "date-time" },
      "details": { "type": "string" }
    },
    "required": ["customer_id", "service_address", "schedule"]
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function createJobTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "create_job",
      description: "Create a new job in Housecall Pro",
      parameters: {
        type: "object",
        properties: {
          customer_id: { type: "string" },
          service_address: { type: "string" },
          schedule: { type: "string", format: "date-time" },
          details: { type: "string" }
        },
        required: ["customer_id", "service_address", "schedule"]
      },
      run: async (args) => {
        const payload = args as {
          customer_id: string;
          service_address: string;
          schedule: string;
          details?: string;
        };
        const response = await client.post("/jobs", payload);
        return response.data; // Assume shape Job
      }
    };
  }
  ```
* **Location:** `src/tools/createJob.ts`

#### `src/tools/updateJob.ts`

* **Purpose:** Update fields on an existing job.
* **Endpoint:** `PUT /jobs/{job_id}`
* **Parameters:**

  ```jsonc
  {
    "type": "object",
    "properties": {
      "job_id": { "type": "string" },
      "updates": { "type": "object" }
    },
    "required": ["job_id", "updates"]
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function updateJobTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "update_job",
      description: "Update an existing Housecall Pro job",
      parameters: {
        type: "object",
        properties: {
          job_id: { type: "string" },
          updates: { type: "object" }
        },
        required: ["job_id", "updates"]
      },
      run: async (args) => {
        const { job_id, updates } = args as { job_id: string; updates: Record<string, any> };
        const response = await client.put(`/jobs/${job_id}`, updates);
        return response.data; // Assume shape Job
      }
    };
  }
  ```
* **Location:** `src/tools/updateJob.ts`

#### `src/tools/cancelJob.ts`

* **Purpose:** Cancel or delete a job.
* **Endpoint:** `DELETE /jobs/{job_id}`
* **Parameters:**

  ```jsonc
  {
    "type": "object",
    "properties": {
      "job_id": { "type": "string" }
    },
    "required": ["job_id"]
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function cancelJobTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "cancel_job",
      description: "Cancel (delete) a Housecall Pro job by ID",
      parameters: {
        type: "object",
        properties: {
          job_id: { type: "string" }
        },
        required: ["job_id"]
      },
      run: async (args) => {
        const { job_id } = args as { job_id: string };
        const response = await client.delete(`/jobs/${job_id}`);
        return response.data; // Often returns an empty object or confirmation
      }
    };
  }
  ```
* **Location:** `src/tools/cancelJob.ts`

### 6.3. Invoice Tools

#### `src/tools/listInvoices.ts`

* **Purpose:** Retrieve a paginated list of invoices.
* **Endpoint:** `GET /invoices?limit={limit}&offset={offset}`
* **Parameters:**

  ```jsonc
  {
    "type": "object",
    "properties": {
      "limit": { "type": "integer", "minimum": 1, "maximum": 100 },
      "offset": { "type": "integer", "minimum": 0 }
    }
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function listInvoicesTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "list_invoices",
      description: "Retrieve a list of Housecall Pro invoices (paginated)",
      parameters: {
        type: "object",
        properties: {
          limit: { type: "integer", minimum: 1, maximum: 100 },
          offset: { type: "integer", minimum: 0 }
        }
      },
      run: async (args) => {
        const { limit = 50, offset = 0 } = args as { limit?: number; offset?: number };
        const response = await client.get("/invoices", {
          params: { limit, offset }
        });
        return response.data; // Assume shape { invoices: Invoice[], total: number, ... }
      }
    };
  }
  ```
* **Location:** `src/tools/listInvoices.ts`

#### `src/tools/getInvoice.ts`

* **Purpose:** Retrieve details of a single invoice by ID.
* **Endpoint:** `GET /invoices/{invoice_id}`
* **Parameters:**

  ```jsonc
  {
    "type": "object",
    "properties": {
      "invoice_id": { "type": "string" }
    },
    "required": ["invoice_id"]
  }
  ```
* **Implementation:**

  ```ts
  import { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";
  import { AxiosInstance } from "axios";

  export function getInvoiceTool(client: AxiosInstance): ToolDefinition {
    return {
      name: "get_invoice",
      description: "Retrieve a Housecall Pro invoice by ID",
      parameters: {
        type: "object",
        properties: {
          invoice_id: { type: "string" }
        },
        required: ["invoice_id"]
      },
      run: async (args) => {
        const { invoice_id } = args as { invoice_id: string };
        const response = await client.get(`/invoices/${invoice_id}`);
        return response.data; // Assume shape Invoice
      }
    };
  }
  ```
* **Location:** `src/tools/getInvoice.ts`

### 6.4. Additional Resources

Depending on business needs, you may add more tools for:

* **Leads** (`GET /leads`, `POST /leads`)
* **Estimates** (`GET /estimates`, `POST /estimates`)
* **Payments** (`GET /payments`, `POST /payments`)
* **Technicians** (`GET /technicians`, `POST /technicians`)
* **Products & Services** (`GET /services`, `GET /items`)
* **Webhooks Management** (`GET /webhooks`, `POST /webhooks`)

Each follows the same pattern: define a tool module in `src/tools/` with `@mcp.tool()`, JSON-schema parameters, and an Axios call to the corresponding Housecall Pro endpoint.

---

## Webhook Prompts

Housecall Pro can send webhook events (e.g., `job.created`, `customer.updated`, `invoice.paid`). To integrate these with MCP:

1. **Define a Prompt Module** in `src/prompts/onJobCreated.ts` (for the `job.created` event).

2. **Sample Prompt Definition** (`src/prompts/onJobCreated.ts`):

   ```ts
   import { PromptDefinition } from "@modelcontextprotocol/mcp-sdk";

   /**
    * Triggered when Housecall Pro sends a job.created webhook.
    * The payload contains at least:
    *  - { job: { id: string; customer_id: string; ... }, ... }
    */
   export const onJobCreatedPrompt: PromptDefinition = {
     name: "on_job_created",
     description: "Handle a new job.created webhook from Housecall Pro",
     run: async (payload) => {
       const jobInfo = (payload as any).job;
       if (!jobInfo) {
         return "Received job.created webhook without job data";
       }
       const jobId = jobInfo.id;
       const customerId = jobInfo.customer_id;
       return `A new job was created in Housecall Pro: job ID ${jobId} for customer ${customerId}.`;
     }
   };
   ```

   * **Location:** `src/prompts/onJobCreated.ts`

3. **Additional Webhook Prompts:**

   * `onCustomerUpdatedPrompt` for `customer.updated`.
   * `onInvoicePaidPrompt` for `invoice.paid`.

Each prompt exports a `PromptDefinition` with:

* **`name`**: Unique prompt identifier.
* **`description`**: Brief explanation.
* **`run`**: Async function accepting raw webhook JSON (`payload`) and returning a string (to feed into the LLM).

---

## Server Entry Point

### `src/index.ts`

This is the single entry point that ties together:

* Utility client
* Tool registrations
* Prompt registrations
* Express (or Fastify) app to receive webhooks
* MCP transport over HTTP/SSE

#### Sample Code

```ts
import { FastMCP } from "@modelcontextprotocol/mcp-sdk";
import express from "express";
import { createHousecallClient } from "./utils/httpClient";

// Import tool factories
import { getCustomerTool } from "./tools/getCustomer";
import { listCustomersTool } from "./tools/listCustomers";
import { createJobTool } from "./tools/createJob";
import { updateJobTool } from "./tools/updateJob";
import { cancelJobTool } from "./tools/cancelJob";
import { listInvoicesTool } from "./tools/listInvoices";
import { getInvoiceTool } from "./tools/getInvoice";
// … import other tool modules as needed

// Import prompts
import { onJobCreatedPrompt } from "./prompts/onJobCreated";
// … import other prompts as needed

async function main() {
  // Instantiate MCP
  const mcp = new FastMCP("housecallpro");

  // Create HTTP client
  const client = createHousecallClient();

  // Register tools
  mcp.registerTool(getCustomerTool(client));
  mcp.registerTool(listCustomersTool(client));
  mcp.registerTool(createJobTool(client));
  mcp.registerTool(updateJobTool(client));
  mcp.registerTool(cancelJobTool(client));
  mcp.registerTool(listInvoicesTool(client));
  mcp.registerTool(getInvoiceTool(client));
  // … register additional tools

  // Register prompts (webhook handlers)
  mcp.registerPrompt(onJobCreatedPrompt);
  // … register other prompts

  // Set up Express for webhooks
  const app = express();
  app.use(express.json());

  // Example: job.created webhook endpoint
  app.post("/webhook/job_created", async (req, res) => {
    // (Optional) Verify HCP_WEBHOOK_SECRET signature here
    const payload = req.body;
    await mcp.invokePrompt("on_job_created", payload);
    res.status(200).send({ received: true });
  });

  // (Optional) Add other webhook endpoints (e.g., /webhook/customer_updated)

  // Combine MCP transport with Express
  mcp.listenWithExpress(app, {
    port: Number(process.env.PORT) || 8002
  });

  console.log(`Housecall Pro MCP server listening on port ${process.env.PORT || 8002}`);
}

main().catch((err) => {
  console.error("Failed to start MCP server:", err);
  process.exit(1);
});
```

* **Key Points:**

  * Calls `mcp.registerTool(...)` for each tool.
  * Calls `mcp.registerPrompt(...)` for each webhook prompt.
  * Sets up Express to receive webhooks and invoke the matching prompt.
  * Calls `mcp.listenWithExpress(app, { port })` to start both the MCP server (HTTP/SSE for LLM clients) and the Express app for webhooks.

---

## Testing Strategy

A robust testing strategy ensures that changes to Housecall Pro’s API or our tool implementation are caught early.

### 9.1. Unit Tests

* **Location:** `test/unit/`

* **Purpose:** Test individual tool modules in isolation by mocking the Axios client.

* **Approach:**

  1. Create a mock Axios instance (using a library like `nock` or manual stubbing).
  2. Inject the mock client into the tool factory (e.g., `getCustomerTool(mockClient)`).
  3. Call `tool.run({ customer_id: "abc123" })` and assert that:

     * The mock Axios client was called with the correct URL and headers.
     * The returned value matches expected shape.
  4. Test error handling: simulate a 404 or 500 response and assert the tool throws or returns a structured error.

* **Sample `getCustomer.test.ts`:**

  ```ts
  import { expect } from "chai";
  import nock from "nock";
  import axios from "axios";
  import { getCustomerTool } from "../../src/tools/getCustomer";
  import type { ToolDefinition } from "@modelcontextprotocol/mcp-sdk";

  describe("getCustomerTool", () => {
    const BASE_URL = "https://api.housecallpro.com/v1";
    let client = axios.create({ baseURL: BASE_URL });
    let tool: ToolDefinition;

    before(() => {
      process.env.HCP_API_KEY = "test_key";
      client = axios.create({
        baseURL: BASE_URL,
        headers: { "Company-API-Key": "test_key" }
      });
      tool = getCustomerTool(client);
    });

    afterEach(() => {
      nock.cleanAll();
    });

    it("fetches customer by ID successfully", async () => {
      const customerId = "cust_123";
      const mockData = { id: customerId, first_name: "Alice", last_name: "Smith" };

      nock(BASE_URL)
        .get(`/customers/${customerId}`)
        .reply(200, mockData);

      const result = await tool.run({ customer_id: customerId });
      expect(result).to.deep.equal(mockData);
    });

    it("throws error on 404", async () => {
      const customerId = "cust_notfound";
      nock(BASE_URL)
        .get(`/customers/${customerId}`)
        .reply(404, { message: "Not Found" });

      try {
        await tool.run({ customer_id: customerId });
        throw new Error("Expected error, but got success");
      } catch (err: any) {
        expect(err.response.status).to.equal(404);
      }
    });
  });
  ```

* **Tools & Libraries:**

  * `mocha` for test runner
  * `chai` for assertions
  * `nock` for HTTP request mocking
  * `ts-node` or pre-compiled JavaScript to run tests against built code

### 9.2. Integration Tests

* **Location:** `test/integration/`

* **Purpose:** Validate real interactions against a sandbox or test Housecall Pro environment.

* **Prerequisites:**

  * A dedicated test account in Housecall Pro (with API key).
  * Known test data (e.g., a customer ID that always exists, or a test job template).

* **Approach:**

  1. Configure environment variables to point to the test account:

     ```
     HCP_API_KEY=live_test_key
     PORT=8002
     ```
  2. Start the MCP server locally (`npm run start`).
  3. Write tests that call the MCP tools via the MCP transport (e.g., an HTTP client that sends JSON-RPC requests to `http://localhost:8002`).
  4. Assert that responses match real data shapes and values.
  5. Test webhook prompts by sending a sample webhook payload to `http://localhost:8002/webhook/job_created` and verifying the MCP prompt output (via listening on SSE or inspecting logs).

* **Sample `getCustomer.int.test.ts`:**

  ```ts
  import { expect } from "chai";
  import fetch from "node-fetch";

  describe("Integration: get_customer", () => {
    const MCP_URL = "http://localhost:8002";
    const customerId = "known_test_customer";

    it("retrieves a real customer", async () => {
      const payload = {
        jsonrpc: "2.0",
        id: 1,
        method: "get_customer",
        params: { customer_id: customerId }
      };

      const response = await fetch(`${MCP_URL}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      expect(data).to.have.property("result");
      expect(data.result).to.have.property("id", customerId);
      expect(data.result).to.have.property("first_name");
    });
  });
  ```

* **Notes:**

  * Integration tests are often slower and require network access; run them conditionally (e.g., only on the `integration` branch or with a special flag).
  * Clean up test data if tests create or modify records.

---

## CI/CD Pipeline

Leverage GitHub Actions to automate:

1. **Build & Test:**

   * **Trigger:** on `push` to `main` or PRs to `main`.
   * **Actions:**

     * Checkout code.
     * Load Node.js 18.
     * Install dependencies (`npm install`).
     * Run TypeScript compilation (`npm run build`).
     * Run unit tests (`npm run test:unit`).
     * (Optional) Run integration tests if environment variables for test account are set (`npm run test:integration`).
     * Run version check: ensure `version.ts` matches `package.json` version.
   * **Artifacts:** Build logs, test reports.

2. **Publish Package:**

   * **Trigger:** on `tag` push (e.g., `v1.0.0`).
   * **Actions:**

     * Checkout code.
     * Install dependencies.
     * Run `npm run build`.
     * Authenticate to NPM registry (using `NODE_AUTH_TOKEN` secret).
     * Publish to NPM (`npm publish --access public`).
     * (Optional) Build Docker image and push to registry (Docker Hub or GitHub Container Registry), tagging with the same version (e.g., `ghcr.io/yourusername/housecallpro-mcp-server:1.0.0`).
   * **Output:** Published NPM package and Docker image.

### Sample `build.yaml` (CI)

```yaml
name: Build & Test

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build-test:
    runs-on: ubuntu-latest
    env:
      NODE_OPTIONS: "--max_old_space_size=4096"
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Build TypeScript
        run: npm run build

      - name: Run Unit Tests
        run: npm run test:unit

      - name: Run Version Check
        run: node scripts/version-check.js
```

### Sample `publish.yaml` (CD)

```yaml
name: Publish

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
          registry-url: https://registry.npmjs.org
          scope: '@your-scope'   # if using a scoped package

      - name: Install dependencies
        run: npm ci

      - name: Build TypeScript
        run: npm run build

      - name: Publish to NPM
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npm publish --access public

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_TOKEN }}

      - name: Build and Push Docker Image
        run: |
          IMAGE=ghcr.io/yourusername/housecallpro-mcp-server:$(node -p "require('./version').version")
          docker build -t $IMAGE .
          docker push $IMAGE
```

---

## Containerization & Deployment

### Dockerfile

```dockerfile
# Use official Node.js LTS image
FROM node:18-alpine

# Create app directory
WORKDIR /app

# Copy package manifest and install production dependencies
COPY package.json package-lock.json ./
RUN npm ci --production

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Expose MCP port
EXPOSE 8002

# Start the server
CMD ["npm", "run", "start"]
```

* **Build Locally:**

  ```bash
  docker build -t housecallpro-mcp-server:latest .
  ```
* **Run Container:**

  ```bash
  docker run -d \
    --name hcp-mcp \
    -p 8002:8002 \
    -e HCP_API_KEY=your_housecall_api_key \
    -e HCP_WEBHOOK_SECRET=your_webhook_secret \
    housecallpro-mcp-server:latest
  ```
* **Logging & Health Checks:**

  * The container outputs MCP logs to STDOUT; use `docker logs -f hcp-mcp` to monitor.
  * For Kubernetes, define a `readinessProbe` on `/health` (FastMCP exposes a default health endpoint) and a `livenessProbe` similarly.

### Deployment Targets

1. **Docker-Compose / Local Testing:**

   * Use a `docker-compose.yml` if additional dependencies are needed (e.g., a local webhook tunnel via ngrok for development).

2. **Kubernetes:**

   * Create a `Deployment` YAML that references `ghcr.io/yourusername/housecallpro-mcp-server:1.0.0`.
   * Configure `envFrom` to load `HCP_API_KEY` and `HCP_WEBHOOK_SECRET` from a Kubernetes `Secret`.
   * Configure a `Service` of type `ClusterIP` (or `LoadBalancer`) exposing port 8002.
   * Add `readinessProbe` for `httpGet: { path: /health, port: 8002 }`.

3. **Serverless (AWS Fargate / ECS):**

   * Push Docker image to Amazon ECR.
   * Define an ECS Task Definition, referencing environment variables from AWS Secrets Manager or SSM.
   * Configure a load balancer rule to forward HTTP (port 80) to container port 8002.

---

## Versioning & Release Management

* **Single Source of Truth:** Maintain `version.ts` in project root:

  ```ts
  export const version = "1.0.0";
  ```
* **package.json Version:** Match `"version": "1.0.0"` in `package.json`.
* **Version Check Script (`scripts/version-check.js`):**

  ```js
  const fs = require("fs");
  const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
  const { version } = require("../version");
  if (pkg.version !== version) {
    console.error(`Version mismatch: package.json (${pkg.version}) vs version.ts (${version})`);
    process.exit(1);
  }
  process.exit(0);
  ```
* **Release Workflow:**

  1. Update `version.ts` to next version (e.g., `1.1.0`).
  2. Update `package.json` version accordingly.
  3. Commit with message `chore: bump version to 1.1.0`.
  4. Create Git tag `v1.1.0`.
  5. Push to GitHub; GitHub Actions runs `publish.yaml` and publishes to NPM and/or Docker.

---

## Monitoring & Maintenance

1. **API Change Monitoring:**

   * **Manual:** Regularly check Housecall Pro’s API docs ([https://docs.housecallpro.com](https://docs.housecallpro.com)).
   * **Automated Diff:** Set up a weekly GitHub Actions job to `curl` the API docs HTML and `diff` against a stored snapshot. On diff, send a notification (e.g., via Slack or email).
   * **Integration Tests:** If an endpoint changes, integration tests will fail; monitor CI for failures.

2. **Error Logging & Alerts:**

   * Use a structured logger (e.g., `winston`) to log errors and requests.
   * Forward logs to a centralized service (e.g., Datadog, LogDNA, or CloudWatch) for monitoring.
   * Configure alerts on repeated errors (e.g., 5xx responses from Housecall Pro or internal exceptions).

3. **Security & Key Rotation:**

   * Store `HCP_API_KEY` and `HCP_WEBHOOK_SECRET` in a secrets manager (AWS Secrets Manager, GitHub Secrets, or Kubernetes Secrets).
   * Rotate the Housecall Pro API key every 90 days. Update Kubernetes or environment variables accordingly.
   * Verify that no API key is hard-coded in repository.

4. **Dependency Updates:**

   * Schedule a monthly Dependabot or Renovate run to update npm dependencies (e.g., Axios, FastMCP).
   * Review changelogs for major version bumps; update code if breaking changes occur.

---

## Documentation & Onboarding

1. **`README.md` Contents:**

   * **Project Overview:** Purpose and high-level architecture.
   * **Prerequisites:** Node.js version, Housecall Pro plan requirements.
   * **Setup Instructions:**

     1. Clone repo.
     2. Create `.env` from `.env.example`.
     3. `npm install` → `npm run build` → `npm start`.
   * **Tool Usage Examples:**

     ```jsonc
     // Example JSON-RPC request to list customers
     {
       "jsonrpc": "2.0",
       "id": 1,
       "method": "list_customers",
       "params": { "limit": 10, "offset": 0 }
     }
     ```

     ```jsonc
     // Example JSON-RPC response
     {
       "jsonrpc": "2.0",
       "id": 1,
       "result": {
         "customers": [ /* array of customer objects */ ],
         "total": 345
       }
     }
     ```
   * **Webhook Setup:**

     1. In Housecall Pro Admin → App Store → Webhooks, create a new “job.created” subscription.
     2. Set callback URL to `https://your-domain.com/webhook/job_created`.
     3. (Optional) Set signing secret; store in `HCP_WEBHOOK_SECRET`.
   * **Testing:**

     * Run unit tests: `npm run test:unit`.
     * Run integration tests: `HCP_API_KEY=your_test_key npm run test:integration`.
   * **Deployment:**

     * Docker build/push commands.
     * Kubernetes manifests sample.

2. **`.env.example` File:**

   ```env
   # Housecall Pro API Key (MAX Plan required)
   HCP_API_KEY=

   # (Optional) Webhook Signing Secret, if you configure webhooks with a secret
   HCP_WEBHOOK_SECRET=

   # Port for MCP server (default: 8002)
   PORT=8002
   ```

3. **Code Comments & Docstrings:**

   * Each `@mcp.tool()` function should include a clear JSDoc comment describing purpose, parameters, and expected return value.
   * Example:

     ```ts
     /**
      * Retrieve a Housecall Pro customer by ID.
      *
      * @param args.customer_id  Unique identifier of the customer
      * @returns Customer object with fields such as id, first_name, last_name, email, etc.
      */
     @mcp.tool()
     async function get_customer(args: { customer_id: string }): Promise<Customer> {
       // ...
     }
     ```

4. **Onboarding Guide:**

   * Include a short “Quickstart” in `README.md` that guides a new developer from cloning the repo to making their first MCP call.
   * Provide contact info or links to Housecall Pro developer support.

---

## Summary

By following this plan, you will have a fully functional, modular, and maintainable Housecall Pro MCP server that:

* Exposes core Housecall Pro API endpoints (customers, jobs, invoices, etc.) to LLM clients via MCP.
* Handles webhook events (e.g., `job.created`) through MCP prompts.
* Uses TypeScript and `@modelcontextprotocol/mcp-sdk` for consistency with existing MCP servers.
* Includes a robust testing strategy (unit + integration).
* Automates builds, tests, and version‐checking via GitHub Actions.
* Can be containerized with Docker and deployed to Kubernetes or other environments.
* Provides clear documentation and onboarding steps.

This architecture ensures that as Housecall Pro’s API evolves, you can quickly identify changes, update tool definitions, re-run tests, and deploy new versions with confidence.
