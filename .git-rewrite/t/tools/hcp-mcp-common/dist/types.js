/**
 * Core HousecallPro API Types
 * Shared between dev and prod MCP servers
 */
export class HCPError extends Error {
    status;
    code;
    details;
    constructor(message, status, code, details) {
        super(message);
        this.status = status;
        this.code = code;
        this.details = details;
        this.name = 'HCPError';
    }
    static fromResponse(response) {
        return new HCPError(response.message, response.status, response.code, response.details);
    }
}
