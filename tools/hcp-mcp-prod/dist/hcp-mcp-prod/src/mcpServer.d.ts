/**
 * HousecallPro MCP Server Implementation
 * Provides all HCP API functionality through MCP tools
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { HCPService } from './hcpService.js';
export declare class HCPMCPServer {
    private server;
    private hcpService;
    private environment;
    constructor(hcpService: HCPService, environment: 'dev' | 'prod');
    private toolName;
    private setupHandlers;
    private handleListCustomers;
    private handleGetCustomer;
    private handleCreateCustomer;
    private handleUpdateCustomer;
    private handleDeleteCustomer;
    private handleGetCustomerJobs;
    private handleListEmployees;
    private handleGetEmployee;
    private handleCreateEmployee;
    private handleUpdateEmployee;
    private handleGetEmployeeSchedule;
    private handleListJobs;
    private handleGetJob;
    private handleCreateJob;
    private handleUpdateJob;
    private handleDeleteJob;
    private handleRescheduleJob;
    private handleGetJobLineItems;
    private handleUpdateJobLineItems;
    private handleCreateJobLineItem;
    private handleGetJobLineItem;
    private handleUpdateJobLineItem;
    private handleDeleteJobLineItem;
    private handleListJobTypes;
    private handleGetJobType;
    private handleCreateJobType;
    private handleUpdateJobType;
    private handleListAppointments;
    private handleGetAppointment;
    private handleCreateAppointment;
    private handleUpdateAppointment;
    private handleDeleteAppointment;
    private handleSearchCache;
    private handleListCache;
    private handleGetCacheSummary;
    private handleCleanupCache;
    private handleAnalyzeLaundryJobs;
    private handleAnalyzeServiceItems;
    private handleAnalyzeCustomerRevenue;
    private handleAnalyzeJobStatistics;
    private handleAnalyzeTowelUsage;
    private getToolDefinitions;
    getServer(): Server;
}
//# sourceMappingURL=mcpServer.d.ts.map