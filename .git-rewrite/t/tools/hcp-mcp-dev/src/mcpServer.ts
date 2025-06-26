/**
 * HousecallPro MCP Server Implementation
 * Provides all HCP API functionality through MCP tools
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from '@modelcontextprotocol/sdk/types.js';
import { HCPService } from './hcpService.js';
import {
  validateRequired,
  validateString,
  validateNumber,
  validateEmail,
  validatePhoneNumber,
  validateDate,
  validateHCPId,
  validateJobStatus,
  validateEmployeeRole,
  validateLineItemKind,
  validateAppointmentStatus,
  validateSortDirection,
  validateCustomerSortField,
  validatePaginationParams,
  validateSchedule,
  validateLineItem,
  validateArray,
  ValidationError,
  MCP_TOOL_NAMES
} from '../../hcp-mcp-common/src/index.js';

export class HCPMCPServer {
  private server: Server;
  private hcpService: HCPService;
  private environment: 'dev' | 'prod';

  constructor(hcpService: HCPService, environment: 'dev' | 'prod') {
    this.hcpService = hcpService;
    this.environment = environment;
    this.server = new Server({
      name: `hcp-mcp-${environment}`,
      version: '1.0.0'
    });

    this.setupHandlers();
  }

  private toolName(name: string): string {
    return `mcp__hcp-${this.environment}__${name}`;
  }

  private setupHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: this.getToolDefinitions()
    }));

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        console.log(`[${this.environment}] Calling tool: ${name}`);
        console.log(`[${this.environment}] Arguments:`, JSON.stringify(args, null, 2));

        switch (name) {
          // Customer tools
          case this.toolName(MCP_TOOL_NAMES.LIST_CUSTOMERS):
            return await this.handleListCustomers(args);
          case this.toolName(MCP_TOOL_NAMES.GET_CUSTOMER):
            return await this.handleGetCustomer(args);
          case this.toolName(MCP_TOOL_NAMES.CREATE_CUSTOMER):
            return await this.handleCreateCustomer(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_CUSTOMER):
            return await this.handleUpdateCustomer(args);
          case this.toolName(MCP_TOOL_NAMES.DELETE_CUSTOMER):
            return await this.handleDeleteCustomer(args);
          case this.toolName(MCP_TOOL_NAMES.GET_CUSTOMER_JOBS):
            return await this.handleGetCustomerJobs(args);

          // Employee tools
          case this.toolName(MCP_TOOL_NAMES.LIST_EMPLOYEES):
            return await this.handleListEmployees(args);
          case this.toolName(MCP_TOOL_NAMES.GET_EMPLOYEE):
            return await this.handleGetEmployee(args);
          case this.toolName(MCP_TOOL_NAMES.CREATE_EMPLOYEE):
            return await this.handleCreateEmployee(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_EMPLOYEE):
            return await this.handleUpdateEmployee(args);
          case this.toolName(MCP_TOOL_NAMES.GET_EMPLOYEE_SCHEDULE):
            return await this.handleGetEmployeeSchedule(args);

          // Job tools
          case this.toolName(MCP_TOOL_NAMES.LIST_JOBS):
            return await this.handleListJobs(args);
          case this.toolName(MCP_TOOL_NAMES.GET_JOB):
            return await this.handleGetJob(args);
          case this.toolName(MCP_TOOL_NAMES.CREATE_JOB):
            return await this.handleCreateJob(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_JOB):
            return await this.handleUpdateJob(args);
          case this.toolName(MCP_TOOL_NAMES.DELETE_JOB):
            return await this.handleDeleteJob(args);
          case this.toolName(MCP_TOOL_NAMES.RESCHEDULE_JOB):
            return await this.handleRescheduleJob(args);
          case this.toolName(MCP_TOOL_NAMES.GET_JOB_LINE_ITEMS):
            return await this.handleGetJobLineItems(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_JOB_LINE_ITEMS):
            return await this.handleUpdateJobLineItems(args);
          case this.toolName(MCP_TOOL_NAMES.CREATE_JOB_LINE_ITEM):
            return await this.handleCreateJobLineItem(args);
          case this.toolName(MCP_TOOL_NAMES.GET_JOB_LINE_ITEM):
            return await this.handleGetJobLineItem(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_JOB_LINE_ITEM):
            return await this.handleUpdateJobLineItem(args);
          case this.toolName(MCP_TOOL_NAMES.DELETE_JOB_LINE_ITEM):
            return await this.handleDeleteJobLineItem(args);

          // Job Type tools
          case this.toolName(MCP_TOOL_NAMES.LIST_JOB_TYPES):
            return await this.handleListJobTypes(args);
          case this.toolName(MCP_TOOL_NAMES.GET_JOB_TYPE):
            return await this.handleGetJobType(args);
          case this.toolName(MCP_TOOL_NAMES.CREATE_JOB_TYPE):
            return await this.handleCreateJobType(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_JOB_TYPE):
            return await this.handleUpdateJobType(args);

          // Appointment tools
          case this.toolName(MCP_TOOL_NAMES.LIST_APPOINTMENTS):
            return await this.handleListAppointments(args);
          case this.toolName(MCP_TOOL_NAMES.GET_APPOINTMENT):
            return await this.handleGetAppointment(args);
          case this.toolName(MCP_TOOL_NAMES.CREATE_APPOINTMENT):
            return await this.handleCreateAppointment(args);
          case this.toolName(MCP_TOOL_NAMES.UPDATE_APPOINTMENT):
            return await this.handleUpdateAppointment(args);
          case this.toolName(MCP_TOOL_NAMES.DELETE_APPOINTMENT):
            return await this.handleDeleteAppointment(args);

          // Cache management tools
          case this.toolName(MCP_TOOL_NAMES.SEARCH_CACHE):
            return await this.handleSearchCache(args);
          case this.toolName(MCP_TOOL_NAMES.LIST_CACHE):
            return await this.handleListCache(args);
          case this.toolName(MCP_TOOL_NAMES.GET_CACHE_SUMMARY):
            return await this.handleGetCacheSummary(args);
          case this.toolName(MCP_TOOL_NAMES.CLEANUP_CACHE):
            return await this.handleCleanupCache(args);

          // New search tools
          case this.toolName(MCP_TOOL_NAMES.SEARCH_ADDRESSES):
            return await this.handleSearchAddresses(args);
          case this.toolName(MCP_TOOL_NAMES.GET_JOBS_BY_ADDRESS):
            return await this.handleGetJobsByAddress(args);

          // Analysis tools
          case this.toolName(MCP_TOOL_NAMES.ANALYZE_LAUNDRY_JOBS):
            return await this.handleAnalyzeLaundryJobs(args);
          case this.toolName(MCP_TOOL_NAMES.ANALYZE_SERVICE_ITEMS):
            return await this.handleAnalyzeServiceItems(args);
          case this.toolName(MCP_TOOL_NAMES.ANALYZE_CUSTOMER_REVENUE):
            return await this.handleAnalyzeCustomerRevenue(args);
          case this.toolName(MCP_TOOL_NAMES.ANALYZE_JOB_STATISTICS):
            return await this.handleAnalyzeJobStatistics(args);
          case this.toolName(MCP_TOOL_NAMES.ANALYZE_TOWEL_USAGE):
            return await this.handleAnalyzeTowelUsage(args);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error: any) {
        console.error(`[${this.environment}] Tool error:`, error);
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`
            }
          ],
          isError: true
        };
      }
    });
  }

  // Customer tool handlers
  private async handleListCustomers(args: any) {
    const paginationParams = validatePaginationParams(args);
    const params: any = { ...paginationParams };
    
    if (args.q) params.q = validateString(args.q, 'q');
    if (args.sort_by) params.sort_by = validateCustomerSortField(args.sort_by);
    if (args.sort_direction) params.sort_direction = validateSortDirection(args.sort_direction);
    if (args.created_after) params.created_after = validateDate(args.created_after, 'created_after');
    if (args.created_before) params.created_before = validateDate(args.created_before, 'created_before');
    if (args.tags) params.tags = validateArray(args.tags, 'tags');

    const result = await this.hcpService.listCustomers(params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetCustomer(args: any) {
    const customerId = validateHCPId(args.customer_id, 'customer');
    const result = await this.hcpService.getCustomer(customerId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleCreateCustomer(args: any) {
    const data: any = {};
    
    if (args.first_name) data.first_name = validateString(args.first_name, 'first_name');
    if (args.last_name) data.last_name = validateString(args.last_name, 'last_name');
    if (args.company) data.company = validateString(args.company, 'company');
    if (args.email) data.email = validateEmail(args.email);
    if (args.mobile_number) data.mobile_number = validatePhoneNumber(args.mobile_number, 'mobile_number');
    if (args.home_number) data.home_number = validatePhoneNumber(args.home_number, 'home_number');
    if (args.work_number) data.work_number = validatePhoneNumber(args.work_number, 'work_number');
    if (args.lead_source) data.lead_source = validateString(args.lead_source, 'lead_source');
    if (args.notes) data.notes = validateString(args.notes, 'notes');
    if (args.tags) data.tags = validateArray(args.tags, 'tags');
    if (args.addresses) data.addresses = args.addresses;

    const result = await this.hcpService.createCustomer(data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateCustomer(args: any) {
    const customerId = validateHCPId(args.customer_id, 'customer');
    const data: any = {};
    
    if (args.first_name) data.first_name = validateString(args.first_name, 'first_name');
    if (args.last_name) data.last_name = validateString(args.last_name, 'last_name');
    if (args.company) data.company = validateString(args.company, 'company');
    if (args.email) data.email = validateEmail(args.email);
    if (args.mobile_number) data.mobile_number = validatePhoneNumber(args.mobile_number, 'mobile_number');
    if (args.home_number) data.home_number = validatePhoneNumber(args.home_number, 'home_number');
    if (args.work_number) data.work_number = validatePhoneNumber(args.work_number, 'work_number');
    if (args.lead_source) data.lead_source = validateString(args.lead_source, 'lead_source');
    if (args.notes) data.notes = validateString(args.notes, 'notes');
    if (args.tags) data.tags = validateArray(args.tags, 'tags');

    const result = await this.hcpService.updateCustomer(customerId, data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleDeleteCustomer(args: any) {
    const customerId = validateHCPId(args.customer_id, 'customer');
    await this.hcpService.deleteCustomer(customerId);
    
    return {
      content: [
        {
          type: 'text',
          text: `Customer ${customerId} deleted successfully`
        }
      ]
    };
  }

  private async handleGetCustomerJobs(args: any) {
    const customerId = validateHCPId(args.customer_id, 'customer');
    const params = validatePaginationParams(args);
    
    const result = await this.hcpService.getCustomerJobs(customerId, params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  // Employee tool handlers
  private async handleListEmployees(args: any) {
    const paginationParams = validatePaginationParams(args);
    const params: any = { ...paginationParams };
    
    if (args.is_active !== undefined) params.is_active = Boolean(args.is_active);
    if (args.role) params.role = validateEmployeeRole(args.role);

    const result = await this.hcpService.listEmployees(params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetEmployee(args: any) {
    const employeeId = validateHCPId(args.employee_id, 'employee');
    const result = await this.hcpService.getEmployee(employeeId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleCreateEmployee(args: any) {
    const data: any = {
      first_name: validateString(args.first_name, 'first_name'),
      last_name: validateString(args.last_name, 'last_name'),
      role: validateEmployeeRole(args.role)
    };
    
    if (args.email) data.email = validateEmail(args.email);
    if (args.mobile_number) data.mobile_number = validatePhoneNumber(args.mobile_number, 'mobile_number');
    if (args.color_hex) data.color_hex = validateString(args.color_hex, 'color_hex');
    if (args.tags) data.tags = validateArray(args.tags, 'tags');

    const result = await this.hcpService.createEmployee(data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateEmployee(args: any) {
    const employeeId = validateHCPId(args.employee_id, 'employee');
    const data: any = {};
    
    if (args.first_name) data.first_name = validateString(args.first_name, 'first_name');
    if (args.last_name) data.last_name = validateString(args.last_name, 'last_name');
    if (args.email) data.email = validateEmail(args.email);
    if (args.mobile_number) data.mobile_number = validatePhoneNumber(args.mobile_number, 'mobile_number');
    if (args.role) data.role = validateEmployeeRole(args.role);
    if (args.is_active !== undefined) data.is_active = Boolean(args.is_active);
    if (args.color_hex) data.color_hex = validateString(args.color_hex, 'color_hex');
    if (args.tags) data.tags = validateArray(args.tags, 'tags');

    const result = await this.hcpService.updateEmployee(employeeId, data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetEmployeeSchedule(args: any) {
    const employeeId = validateHCPId(args.employee_id, 'employee');
    let startDate, endDate;
    
    if (args.start_date) startDate = validateDate(args.start_date, 'start_date');
    if (args.end_date) endDate = validateDate(args.end_date, 'end_date');

    const result = await this.hcpService.getEmployeeSchedule(employeeId, startDate, endDate);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  // Job tool handlers
  private async handleListJobs(args: any) {
    console.log(`[${this.environment}] handleListJobs args:`, JSON.stringify(args, null, 2));
    const paginationParams = validatePaginationParams(args);
    console.log(`[${this.environment}] validatePaginationParams returned:`, JSON.stringify(paginationParams, null, 2));
    const params: any = { ...paginationParams };
    
    if (args.customer_id) params.customer_id = validateHCPId(args.customer_id, 'customer');
    if (args.work_status) params.work_status = validateJobStatus(args.work_status);
    if (args.scheduled_start_min) params.scheduled_start_min = validateDate(args.scheduled_start_min, 'scheduled_start_min');
    if (args.scheduled_start_max) params.scheduled_start_max = validateDate(args.scheduled_start_max, 'scheduled_start_max');
    if (args.assigned_employee_id) params.assigned_employee_id = validateHCPId(args.assigned_employee_id, 'employee');
    if (args.job_type_id) params.job_type_id = validateHCPId(args.job_type_id, 'job_type');

    console.log(`[${this.environment}] Final params sent to hcpService.listJobs:`, JSON.stringify(params, null, 2));
    const result = await this.hcpService.listJobs(params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetJob(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const result = await this.hcpService.getJob(jobId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleCreateJob(args: any) {
    const data: any = {
      customer_id: validateHCPId(args.customer_id, 'customer'),
      address_id: validateHCPId(args.address_id, 'address'),
      schedule: validateSchedule(args.schedule)
    };
    
    if (args.assigned_employee_ids) {
      data.assigned_employee_ids = validateArray(
        args.assigned_employee_ids, 
        'assigned_employee_ids',
        (id) => validateHCPId(id, 'employee')
      );
    }
    
    if (args.line_items) {
      data.line_items = validateArray(
        args.line_items,
        'line_items',
        validateLineItem
      );
    }
    
    if (args.job_type_id) data.job_type_id = validateHCPId(args.job_type_id, 'job_type');
    if (args.notes) data.notes = validateString(args.notes, 'notes');
    if (args.description) data.description = validateString(args.description, 'description');
    if (args.work_status) data.work_status = validateJobStatus(args.work_status);

    const result = await this.hcpService.createJob(data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateJob(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const data: any = {};
    
    if (args.customer_id) data.customer_id = validateHCPId(args.customer_id, 'customer');
    if (args.address_id) data.address_id = validateHCPId(args.address_id, 'address');
    if (args.schedule) data.schedule = validateSchedule(args.schedule);
    if (args.work_status) data.work_status = validateJobStatus(args.work_status);
    if (args.assigned_employee_ids) {
      data.assigned_employee_ids = validateArray(
        args.assigned_employee_ids,
        'assigned_employee_ids',
        (id) => validateHCPId(id, 'employee')
      );
    }
    if (args.job_type_id) data.job_type_id = validateHCPId(args.job_type_id, 'job_type');
    if (args.notes) data.notes = validateString(args.notes, 'notes');
    if (args.description) data.description = validateString(args.description, 'description');

    const result = await this.hcpService.updateJob(jobId, data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleDeleteJob(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    await this.hcpService.deleteJob(jobId);
    
    return {
      content: [
        {
          type: 'text',
          text: `Job ${jobId} deleted successfully`
        }
      ]
    };
  }

  private async handleRescheduleJob(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const schedule = validateSchedule(args.schedule);

    const result = await this.hcpService.rescheduleJob(jobId, schedule);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetJobLineItems(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const result = await this.hcpService.getJobLineItems(jobId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateJobLineItems(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const lineItems = validateArray(args.line_items, 'line_items', validateLineItem);

    await this.hcpService.updateJobLineItems(jobId, lineItems);
    
    return {
      content: [
        {
          type: 'text',
          text: `Line items for job ${jobId} updated successfully`
        }
      ]
    };
  }

  private async handleCreateJobLineItem(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const lineItem = validateLineItem(args);
    
    const result = await this.hcpService.createJobLineItem(jobId, lineItem);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetJobLineItem(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const lineItemId = validateHCPId(args.line_item_id, 'line_item');
    
    const result = await this.hcpService.getJobLineItem(jobId, lineItemId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateJobLineItem(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const lineItemId = validateHCPId(args.line_item_id, 'line_item');
    const lineItem = validateLineItem(args);
    
    const result = await this.hcpService.updateJobLineItem(jobId, lineItemId, lineItem);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleDeleteJobLineItem(args: any) {
    const jobId = validateHCPId(args.job_id, 'job');
    const lineItemId = validateHCPId(args.line_item_id, 'line_item');
    
    await this.hcpService.deleteJobLineItem(jobId, lineItemId);
    
    return {
      content: [
        {
          type: 'text',
          text: `Line item ${lineItemId} deleted from job ${jobId} successfully`
        }
      ]
    };
  }

  // Job Type tool handlers
  private async handleListJobTypes(args: any) {
    const paginationParams = validatePaginationParams(args);
    const params: any = { ...paginationParams };
    
    if (args.is_active !== undefined) params.is_active = Boolean(args.is_active);

    const result = await this.hcpService.listJobTypes(params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetJobType(args: any) {
    const jobTypeId = validateHCPId(args.job_type_id, 'job_type');
    const result = await this.hcpService.getJobType(jobTypeId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleCreateJobType(args: any) {
    const data: any = {
      name: validateString(args.name, 'name')
    };
    
    if (args.description) data.description = validateString(args.description, 'description');
    if (args.color_hex) data.color_hex = validateString(args.color_hex, 'color_hex');

    const result = await this.hcpService.createJobType(data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateJobType(args: any) {
    const jobTypeId = validateHCPId(args.job_type_id, 'job_type');
    const data: any = {};
    
    if (args.name) data.name = validateString(args.name, 'name');
    if (args.description) data.description = validateString(args.description, 'description');
    if (args.color_hex) data.color_hex = validateString(args.color_hex, 'color_hex');
    if (args.is_active !== undefined) data.is_active = Boolean(args.is_active);

    const result = await this.hcpService.updateJobType(jobTypeId, data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  // Appointment tool handlers
  private async handleListAppointments(args: any) {
    const params: any = {};
    
    if (args.job_id) params.job_id = validateHCPId(args.job_id, 'job');
    if (args.scheduled_start_min) params.scheduled_start_min = validateDate(args.scheduled_start_min, 'scheduled_start_min');
    if (args.scheduled_start_max) params.scheduled_start_max = validateDate(args.scheduled_start_max, 'scheduled_start_max');
    if (args.assigned_employee_id) params.assigned_employee_id = validateHCPId(args.assigned_employee_id, 'employee');
    if (args.status) params.status = validateAppointmentStatus(args.status);

    const result = await this.hcpService.listAppointments(params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleGetAppointment(args: any) {
    const appointmentId = validateHCPId(args.appointment_id, 'appointment');
    const result = await this.hcpService.getAppointment(appointmentId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleCreateAppointment(args: any) {
    const data: any = {
      job_id: validateHCPId(args.job_id, 'job'),
      scheduled_start: validateDate(args.scheduled_start, 'scheduled_start'),
      scheduled_end: validateDate(args.scheduled_end, 'scheduled_end'),
      assigned_employee_ids: validateArray(
        args.assigned_employee_ids,
        'assigned_employee_ids',
        (id) => validateHCPId(id, 'employee')
      )
    };
    
    if (args.notes) data.notes = validateString(args.notes, 'notes');

    const result = await this.hcpService.createAppointment(data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleUpdateAppointment(args: any) {
    const appointmentId = validateHCPId(args.appointment_id, 'appointment');
    const data: any = {};
    
    if (args.job_id) data.job_id = validateHCPId(args.job_id, 'job');
    if (args.scheduled_start) data.scheduled_start = validateDate(args.scheduled_start, 'scheduled_start');
    if (args.scheduled_end) data.scheduled_end = validateDate(args.scheduled_end, 'scheduled_end');
    if (args.assigned_employee_ids) {
      data.assigned_employee_ids = validateArray(
        args.assigned_employee_ids,
        'assigned_employee_ids',
        (id) => validateHCPId(id, 'employee')
      );
    }
    if (args.status) data.status = validateAppointmentStatus(args.status);
    if (args.notes) data.notes = validateString(args.notes, 'notes');

    const result = await this.hcpService.updateAppointment(appointmentId, data);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleDeleteAppointment(args: any) {
    const appointmentId = validateHCPId(args.appointment_id, 'appointment');
    await this.hcpService.deleteAppointment(appointmentId);
    
    return {
      content: [
        {
          type: 'text',
          text: `Appointment ${appointmentId} deleted successfully`
        }
      ]
    };
  }

  // New search tool handlers
  private async handleSearchAddresses(args: any) {
    const params: any = {};
    
    if (args.street) params.street = validateString(args.street, 'street');
    if (args.city) params.city = validateString(args.city, 'city');
    if (args.state) params.state = validateString(args.state, 'state');
    if (args.zip) params.zip = validateString(args.zip, 'zip');
    if (args.customer_name) params.customer_name = validateString(args.customer_name, 'customer_name');
    if (args.customer_id) params.customer_id = validateHCPId(args.customer_id, 'customer');

    const results = await this.hcpService.searchAddresses(params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            search_params: params,
            results_count: results.length,
            results: results
          }, null, 2)
        }
      ]
    };
  }

  private async handleGetJobsByAddress(args: any) {
    const addressId = validateHCPId(args.address_id, 'address');
    const params: any = {};
    
    if (args.work_status) params.work_status = validateJobStatus(args.work_status);
    if (args.scheduled_start_min) params.scheduled_start_min = validateDate(args.scheduled_start_min, 'scheduled_start_min');
    if (args.scheduled_start_max) params.scheduled_start_max = validateDate(args.scheduled_start_max, 'scheduled_start_max');

    const results = await this.hcpService.getJobsByAddress(addressId, params);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            address_id: addressId,
            search_params: params,
            results_count: results.length,
            results: results
          }, null, 2)
        }
      ]
    };
  }

  // Cache management tool handlers
  private async handleSearchCache(args: any) {
    const filePath = validateString(args.file_path, 'file_path');
    const searchTerm = validateString(args.search_term, 'search_term');
    const fieldPath = args.field_path ? validateString(args.field_path, 'field_path') : undefined;

    const results = await this.hcpService.searchCache(filePath, searchTerm, fieldPath);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            file_path: filePath,
            search_term: searchTerm,
            field_path: fieldPath,
            results_count: results.length,
            results: results
          }, null, 2)
        }
      ]
    };
  }

  private async handleListCache(args: any) {
    const operation = args.operation ? validateString(args.operation, 'operation') : undefined;
    
    const files = await this.hcpService.listCacheFiles(operation);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            environment: this.environment,
            operation: operation || 'all',
            files_count: files.length,
            files: files
          }, null, 2)
        }
      ]
    };
  }

  private async handleGetCacheSummary(args: any) {
    const data = args.data;
    const operation = validateString(args.operation, 'operation');
    
    const summary = this.hcpService.getCacheSummary(data, operation);
    
    return {
      content: [
        {
          type: 'text',
          text: summary
        }
      ]
    };
  }

  private async handleCleanupCache(args: any) {
    const deletedCount = await this.hcpService.cleanupCache();
    
    return {
      content: [
        {
          type: 'text',
          text: `Cache cleanup completed. Deleted ${deletedCount} old files from ${this.environment} environment.`
        }
      ]
    };
  }

  // Analysis tool handlers
  private async handleAnalyzeLaundryJobs(args: any) {
    const result = await this.hcpService.analyzeLaundryJobs();
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleAnalyzeServiceItems(args: any) {
    const itemPattern = validateString(args.item_pattern, 'item_pattern');
    const result = await this.hcpService.analyzeServiceItems(itemPattern);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleAnalyzeCustomerRevenue(args: any) {
    const customerId = args.customer_id ? validateHCPId(args.customer_id, 'customer') : undefined;
    const result = await this.hcpService.analyzeCustomerRevenue(customerId);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleAnalyzeJobStatistics(args: any) {
    const result = await this.hcpService.analyzeJobStatistics();
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private async handleAnalyzeTowelUsage(args: any) {
    const result = await this.hcpService.analyzeServiceItems('towel');
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  private getToolDefinitions(): Tool[] {
    return [
      // Customer tools
      {
        name: this.toolName(MCP_TOOL_NAMES.LIST_CUSTOMERS),
        description: 'List customers with optional filtering and pagination',
        inputSchema: {
          type: 'object',
          properties: {
            page: { type: 'number', description: 'Page number (default: 1)' },
            page_size: { type: 'number', description: 'Items per page (default: 20, max: 200)' },
            q: { type: 'string', description: 'Search customers by name, email, mobile number and address' },
            sort_by: { type: 'string', description: 'Customer attribute to sort by (default: created_at)' },
            sort_direction: { type: 'string', enum: ['asc', 'desc'], description: 'Ascending or descending (default: desc)' },
            created_after: { type: 'string', description: 'Filter by creation date (ISO 8601)' },
            created_before: { type: 'string', description: 'Filter by creation date (ISO 8601)' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Filter by tags' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_CUSTOMER),
        description: 'Get detailed information about a specific customer',
        inputSchema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', description: 'Customer ID' }
          },
          required: ['customer_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CREATE_CUSTOMER),
        description: 'Create a new customer',
        inputSchema: {
          type: 'object',
          properties: {
            first_name: { type: 'string', description: 'Customer first name' },
            last_name: { type: 'string', description: 'Customer last name' },
            company: { type: 'string', description: 'Company name' },
            email: { type: 'string', description: 'Email address' },
            mobile_number: { type: 'string', description: 'Mobile phone number' },
            home_number: { type: 'string', description: 'Home phone number' },
            work_number: { type: 'string', description: 'Work phone number' },
            lead_source: { type: 'string', description: 'Lead source' },
            notes: { type: 'string', description: 'Customer notes' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Customer tags' },
            addresses: { type: 'array', description: 'Customer addresses' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_CUSTOMER),
        description: 'Update an existing customer',
        inputSchema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', description: 'Customer ID' },
            first_name: { type: 'string', description: 'Customer first name' },
            last_name: { type: 'string', description: 'Customer last name' },
            company: { type: 'string', description: 'Company name' },
            email: { type: 'string', description: 'Email address' },
            mobile_number: { type: 'string', description: 'Mobile phone number' },
            home_number: { type: 'string', description: 'Home phone number' },
            work_number: { type: 'string', description: 'Work phone number' },
            lead_source: { type: 'string', description: 'Lead source' },
            notes: { type: 'string', description: 'Customer notes' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Customer tags' }
          },
          required: ['customer_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.DELETE_CUSTOMER),
        description: 'Delete a customer',
        inputSchema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', description: 'Customer ID' }
          },
          required: ['customer_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_CUSTOMER_JOBS),
        description: 'Get all jobs for a specific customer',
        inputSchema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', description: 'Customer ID' },
            page: { type: 'number', description: 'Page number (default: 1)' },
            per_page: { type: 'number', description: 'Items per page (default: 20, max: 200)' }
          },
          required: ['customer_id']
        }
      },

      // Employee tools
      {
        name: this.toolName(MCP_TOOL_NAMES.LIST_EMPLOYEES),
        description: 'List employees with optional filtering',
        inputSchema: {
          type: 'object',
          properties: {
            page: { type: 'number', description: 'Page number (default: 1)' },
            per_page: { type: 'number', description: 'Items per page (default: 20, max: 200)' },
            is_active: { type: 'boolean', description: 'Filter by active status' },
            role: { type: 'string', enum: ['admin', 'employee', 'field_employee'], description: 'Filter by role' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_EMPLOYEE),
        description: 'Get detailed information about a specific employee',
        inputSchema: {
          type: 'object',
          properties: {
            employee_id: { type: 'string', description: 'Employee ID' }
          },
          required: ['employee_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CREATE_EMPLOYEE),
        description: 'Create a new employee',
        inputSchema: {
          type: 'object',
          properties: {
            first_name: { type: 'string', description: 'Employee first name' },
            last_name: { type: 'string', description: 'Employee last name' },
            email: { type: 'string', description: 'Email address' },
            mobile_number: { type: 'string', description: 'Mobile phone number' },
            role: { type: 'string', enum: ['admin', 'employee', 'field_employee'], description: 'Employee role' },
            color_hex: { type: 'string', description: 'Color in hex format' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Employee tags' }
          },
          required: ['first_name', 'last_name', 'role']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_EMPLOYEE),
        description: 'Update an existing employee',
        inputSchema: {
          type: 'object',
          properties: {
            employee_id: { type: 'string', description: 'Employee ID' },
            first_name: { type: 'string', description: 'Employee first name' },
            last_name: { type: 'string', description: 'Employee last name' },
            email: { type: 'string', description: 'Email address' },
            mobile_number: { type: 'string', description: 'Mobile phone number' },
            role: { type: 'string', enum: ['admin', 'employee', 'field_employee'], description: 'Employee role' },
            is_active: { type: 'boolean', description: 'Active status' },
            color_hex: { type: 'string', description: 'Color in hex format' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Employee tags' }
          },
          required: ['employee_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_EMPLOYEE_SCHEDULE),
        description: 'Get employee schedule for a date range',
        inputSchema: {
          type: 'object',
          properties: {
            employee_id: { type: 'string', description: 'Employee ID' },
            start_date: { type: 'string', description: 'Start date (ISO 8601)' },
            end_date: { type: 'string', description: 'End date (ISO 8601)' }
          },
          required: ['employee_id']
        }
      },

      // Job tools
      {
        name: this.toolName(MCP_TOOL_NAMES.LIST_JOBS),
        description: 'List jobs with comprehensive filtering options',
        inputSchema: {
          type: 'object',
          properties: {
            page: { type: 'number', description: 'Page number (default: 1)' },
            per_page: { type: 'number', description: 'Items per page (default: 20, max: 200)' },
            customer_id: { type: 'string', description: 'Filter by customer' },
            work_status: { 
              type: 'string', 
              enum: ['unscheduled', 'scheduled', 'in_progress', 'completed', 'canceled'],
              description: 'Filter by work status'
            },
            scheduled_start_min: { type: 'string', description: 'Minimum scheduled start (ISO 8601)' },
            scheduled_start_max: { type: 'string', description: 'Maximum scheduled start (ISO 8601)' },
            assigned_employee_id: { type: 'string', description: 'Filter by assigned employee' },
            job_type_id: { type: 'string', description: 'Filter by job type' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_JOB),
        description: 'Get detailed information about a specific job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' }
          },
          required: ['job_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CREATE_JOB),
        description: 'Create a new job with schedule and assignments',
        inputSchema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', description: 'Customer ID' },
            address_id: { type: 'string', description: 'Address ID' },
            schedule: {
              type: 'object',
              properties: {
                scheduled_start: { type: 'string', description: 'Scheduled start time (ISO 8601)' },
                scheduled_end: { type: 'string', description: 'Scheduled end time (ISO 8601)' },
                arrival_window: { type: 'number', description: 'Arrival window in minutes' }
              },
              required: ['scheduled_start', 'scheduled_end']
            },
            assigned_employee_ids: { type: 'array', items: { type: 'string' }, description: 'Assigned employee IDs' },
            job_type_id: { type: 'string', description: 'Job type ID' },
            line_items: { type: 'array', description: 'Job line items' },
            notes: { type: 'string', description: 'Job notes' },
            description: { type: 'string', description: 'Job description' },
            work_status: { 
              type: 'string', 
              enum: ['unscheduled', 'scheduled'],
              description: 'Initial work status'
            }
          },
          required: ['customer_id', 'address_id', 'schedule']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_JOB),
        description: 'Update an existing job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            customer_id: { type: 'string', description: 'Customer ID' },
            address_id: { type: 'string', description: 'Address ID' },
            schedule: {
              type: 'object',
              properties: {
                scheduled_start: { type: 'string', description: 'Scheduled start time (ISO 8601)' },
                scheduled_end: { type: 'string', description: 'Scheduled end time (ISO 8601)' },
                arrival_window: { type: 'number', description: 'Arrival window in minutes' }
              }
            },
            work_status: { 
              type: 'string', 
              enum: ['unscheduled', 'scheduled', 'in_progress', 'completed', 'canceled'],
              description: 'Work status'
            },
            assigned_employee_ids: { type: 'array', items: { type: 'string' }, description: 'Assigned employee IDs' },
            job_type_id: { type: 'string', description: 'Job type ID' },
            notes: { type: 'string', description: 'Job notes' },
            description: { type: 'string', description: 'Job description' }
          },
          required: ['job_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.DELETE_JOB),
        description: 'Delete a job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' }
          },
          required: ['job_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.RESCHEDULE_JOB),
        description: 'Reschedule an existing job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            schedule: {
              type: 'object',
              properties: {
                scheduled_start: { type: 'string', description: 'New scheduled start time (ISO 8601)' },
                scheduled_end: { type: 'string', description: 'New scheduled end time (ISO 8601)' },
                arrival_window: { type: 'number', description: 'Arrival window in minutes' }
              },
              required: ['scheduled_start', 'scheduled_end']
            }
          },
          required: ['job_id', 'schedule']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_JOB_LINE_ITEMS),
        description: 'Get line items for a specific job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' }
          },
          required: ['job_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_JOB_LINE_ITEMS),
        description: 'Update line items for a job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            line_items: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  name: { type: 'string', description: 'Line item name' },
                  description: { type: 'string', description: 'Line item description' },
                  unit_price: { type: 'number', description: 'Unit price' },
                  unit_cost: { type: 'number', description: 'Unit cost' },
                  quantity: { type: 'number', description: 'Quantity' },
                  kind: { type: 'string', enum: ['service', 'product', 'discount', 'fee'], description: 'Line item kind' },
                  taxable: { type: 'boolean', description: 'Is taxable' },
                  service_item_id: { type: 'string', description: 'Service item ID' }
                },
                required: ['name', 'unit_price', 'quantity', 'kind']
              }
            }
          },
          required: ['job_id', 'line_items']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CREATE_JOB_LINE_ITEM),
        description: 'Create a new line item for a job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            name: { type: 'string', description: 'Line item name' },
            description: { type: 'string', description: 'Line item description' },
            unit_price: { type: 'number', description: 'Unit price' },
            unit_cost: { type: 'number', description: 'Unit cost' },
            quantity: { type: 'number', description: 'Quantity' },
            kind: { type: 'string', enum: ['service', 'product', 'discount', 'fee'], description: 'Line item kind' },
            taxable: { type: 'boolean', description: 'Is taxable' },
            service_item_id: { type: 'string', description: 'Service item ID' }
          },
          required: ['job_id', 'name', 'unit_price', 'quantity', 'kind']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_JOB_LINE_ITEM),
        description: 'Get a specific line item from a job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            line_item_id: { type: 'string', description: 'Line item ID' }
          },
          required: ['job_id', 'line_item_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_JOB_LINE_ITEM),
        description: 'Update a specific line item in a job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            line_item_id: { type: 'string', description: 'Line item ID' },
            name: { type: 'string', description: 'Line item name' },
            description: { type: 'string', description: 'Line item description' },
            unit_price: { type: 'number', description: 'Unit price' },
            unit_cost: { type: 'number', description: 'Unit cost' },
            quantity: { type: 'number', description: 'Quantity' },
            kind: { type: 'string', enum: ['service', 'product', 'discount', 'fee'], description: 'Line item kind' },
            taxable: { type: 'boolean', description: 'Is taxable' },
            service_item_id: { type: 'string', description: 'Service item ID' }
          },
          required: ['job_id', 'line_item_id', 'name', 'unit_price', 'quantity', 'kind']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.DELETE_JOB_LINE_ITEM),
        description: 'Delete a specific line item from a job',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            line_item_id: { type: 'string', description: 'Line item ID' }
          },
          required: ['job_id', 'line_item_id']
        }
      },

      // Job Type tools
      {
        name: this.toolName(MCP_TOOL_NAMES.LIST_JOB_TYPES),
        description: 'List job types with optional filtering',
        inputSchema: {
          type: 'object',
          properties: {
            page: { type: 'number', description: 'Page number (default: 1)' },
            per_page: { type: 'number', description: 'Items per page (default: 20, max: 200)' },
            is_active: { type: 'boolean', description: 'Filter by active status' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_JOB_TYPE),
        description: 'Get detailed information about a specific job type',
        inputSchema: {
          type: 'object',
          properties: {
            job_type_id: { type: 'string', description: 'Job type ID' }
          },
          required: ['job_type_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CREATE_JOB_TYPE),
        description: 'Create a new job type',
        inputSchema: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Job type name' },
            description: { type: 'string', description: 'Job type description' },
            color_hex: { type: 'string', description: 'Color in hex format' }
          },
          required: ['name']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_JOB_TYPE),
        description: 'Update an existing job type',
        inputSchema: {
          type: 'object',
          properties: {
            job_type_id: { type: 'string', description: 'Job type ID' },
            name: { type: 'string', description: 'Job type name' },
            description: { type: 'string', description: 'Job type description' },
            color_hex: { type: 'string', description: 'Color in hex format' },
            is_active: { type: 'boolean', description: 'Active status' }
          },
          required: ['job_type_id']
        }
      },

      // Appointment tools
      {
        name: this.toolName(MCP_TOOL_NAMES.LIST_APPOINTMENTS),
        description: 'List appointments with optional filtering',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Filter by job ID' },
            scheduled_start_min: { type: 'string', description: 'Minimum scheduled start (ISO 8601)' },
            scheduled_start_max: { type: 'string', description: 'Maximum scheduled start (ISO 8601)' },
            assigned_employee_id: { type: 'string', description: 'Filter by assigned employee' },
            status: { 
              type: 'string', 
              enum: ['scheduled', 'in_progress', 'completed', 'canceled'],
              description: 'Filter by status'
            }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_APPOINTMENT),
        description: 'Get detailed information about a specific appointment',
        inputSchema: {
          type: 'object',
          properties: {
            appointment_id: { type: 'string', description: 'Appointment ID' }
          },
          required: ['appointment_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CREATE_APPOINTMENT),
        description: 'Create a new appointment',
        inputSchema: {
          type: 'object',
          properties: {
            job_id: { type: 'string', description: 'Job ID' },
            scheduled_start: { type: 'string', description: 'Scheduled start time (ISO 8601)' },
            scheduled_end: { type: 'string', description: 'Scheduled end time (ISO 8601)' },
            assigned_employee_ids: { type: 'array', items: { type: 'string' }, description: 'Assigned employee IDs' },
            notes: { type: 'string', description: 'Appointment notes' }
          },
          required: ['job_id', 'scheduled_start', 'scheduled_end', 'assigned_employee_ids']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.UPDATE_APPOINTMENT),
        description: 'Update an existing appointment',
        inputSchema: {
          type: 'object',
          properties: {
            appointment_id: { type: 'string', description: 'Appointment ID' },
            job_id: { type: 'string', description: 'Job ID' },
            scheduled_start: { type: 'string', description: 'Scheduled start time (ISO 8601)' },
            scheduled_end: { type: 'string', description: 'Scheduled end time (ISO 8601)' },
            assigned_employee_ids: { type: 'array', items: { type: 'string' }, description: 'Assigned employee IDs' },
            status: { 
              type: 'string', 
              enum: ['scheduled', 'in_progress', 'completed', 'canceled'],
              description: 'Appointment status'
            },
            notes: { type: 'string', description: 'Appointment notes' }
          },
          required: ['appointment_id']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.DELETE_APPOINTMENT),
        description: 'Delete an appointment',
        inputSchema: {
          type: 'object',
          properties: {
            appointment_id: { type: 'string', description: 'Appointment ID' }
          },
          required: ['appointment_id']
        }
      },

      // New search tools
      {
        name: this.toolName(MCP_TOOL_NAMES.SEARCH_ADDRESSES),
        description: 'Search for addresses across all customers with flexible filtering',
        inputSchema: {
          type: 'object',
          properties: {
            street: { type: 'string', description: 'Street address to search for (partial match)' },
            city: { type: 'string', description: 'City to search for (partial match)' },
            state: { type: 'string', description: 'State to search for (partial match)' },
            zip: { type: 'string', description: 'ZIP code to search for (partial match)' },
            customer_name: { type: 'string', description: 'Customer name to filter by' },
            customer_id: { type: 'string', description: 'Specific customer ID to search within' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_JOBS_BY_ADDRESS),
        description: 'Find all jobs associated with a specific address',
        inputSchema: {
          type: 'object',
          properties: {
            address_id: { type: 'string', description: 'Address ID to find jobs for' },
            work_status: { 
              type: 'string', 
              enum: ['unscheduled', 'scheduled', 'in_progress', 'completed', 'canceled'],
              description: 'Filter by work status'
            },
            scheduled_start_min: { type: 'string', description: 'Minimum scheduled start (ISO 8601)' },
            scheduled_start_max: { type: 'string', description: 'Maximum scheduled start (ISO 8601)' }
          },
          required: ['address_id']
        }
      },

      // Cache management tools
      {
        name: this.toolName(MCP_TOOL_NAMES.SEARCH_CACHE),
        description: 'Search through cached HCP response data using text or field-specific queries',
        inputSchema: {
          type: 'object',
          properties: {
            file_path: { type: 'string', description: 'Path to the cached JSON file to search' },
            search_term: { type: 'string', description: 'Text to search for in the cached data' },
            field_path: { type: 'string', description: 'Optional field path for targeted search (e.g., "customer.name" or "work_status")' }
          },
          required: ['file_path', 'search_term']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.LIST_CACHE),
        description: 'List available cached response files with metadata',
        inputSchema: {
          type: 'object',
          properties: {
            operation: { type: 'string', description: 'Optional filter by operation type (e.g., "list_jobs", "list_customers")' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.GET_CACHE_SUMMARY),
        description: 'Get summary information about cached data size and record count',
        inputSchema: {
          type: 'object',
          properties: {
            data: { type: 'object', description: 'Data object to summarize' },
            operation: { type: 'string', description: 'Operation name for context' }
          },
          required: ['data', 'operation']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.CLEANUP_CACHE),
        description: 'Clean up old cached files based on retention policy',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      },

      // Analysis tools
      {
        name: this.toolName(MCP_TOOL_NAMES.ANALYZE_LAUNDRY_JOBS),
        description: 'Analyze laundry-related jobs using Linux commands on cached data',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.ANALYZE_SERVICE_ITEMS),
        description: 'Analyze specific service items (like towels, linens) from cached job data',
        inputSchema: {
          type: 'object',
          properties: {
            item_pattern: { type: 'string', description: 'Pattern to search for service items (e.g., "towel", "linen")' }
          },
          required: ['item_pattern']
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.ANALYZE_CUSTOMER_REVENUE),
        description: 'Analyze customer revenue and job statistics from cached data',
        inputSchema: {
          type: 'object',
          properties: {
            customer_id: { type: 'string', description: 'Optional specific customer ID to analyze' }
          }
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.ANALYZE_JOB_STATISTICS),
        description: 'Generate comprehensive job statistics from cached data',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      },
      {
        name: this.toolName(MCP_TOOL_NAMES.ANALYZE_TOWEL_USAGE),
        description: 'Analyze towel usage and costs from service line items in cached data',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      }
    ];
  }

  getServer(): Server {
    return this.server;
  }
}