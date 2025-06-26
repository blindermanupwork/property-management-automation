/**
 * HousecallPro API Constants
 */
export declare const HCP_API: {
    BASE_URL: string;
    VERSION: string;
    DEFAULT_RATE_LIMIT: {
        REQUESTS_PER_MINUTE: number;
        RETRY_AFTER_MS: number;
        MAX_RETRIES: number;
        BACKOFF_MULTIPLIER: number;
    };
    DEFAULT_PAGE_SIZE: number;
    MAX_PAGE_SIZE: number;
    JOB_STATUSES: readonly ["unscheduled", "scheduled", "in_progress", "completed", "canceled"];
    EMPLOYEE_ROLES: readonly ["admin", "employee", "field_employee"];
    LINE_ITEM_KINDS: readonly ["labor", "materials", "discount", "fee"];
    ADDRESS_TYPES: readonly ["service", "billing"];
    CONTACT_TYPES: readonly ["phone", "email", "other"];
    APPOINTMENT_STATUSES: readonly ["scheduled", "in_progress", "completed", "canceled"];
    CUSTOMER_SORT_FIELDS: readonly ["created_at", "updated_at", "first_name", "last_name", "email", "company"];
    SORT_DIRECTIONS: readonly ["asc", "desc"];
};
export declare const CACHE_DEFAULTS: {
    readonly BASE_DIR: "/tmp/hcp-cache";
    readonly RETENTION_HOURS: 48;
    readonly MAX_SIZE_MB: 1000;
    readonly THRESHOLDS: {
        readonly JOBS: 10;
        readonly CUSTOMERS: 5;
        readonly LINE_ITEMS: 15;
        readonly CHARACTERS: 50000;
    };
    readonly ANALYSIS_CACHE_DIR: "analysis";
    readonly FILE_PERMISSIONS: 384;
};
export declare const MCP_TOOL_NAMES: {
    readonly LIST_CUSTOMERS: "list_customers";
    readonly GET_CUSTOMER: "get_customer";
    readonly CREATE_CUSTOMER: "create_customer";
    readonly UPDATE_CUSTOMER: "update_customer";
    readonly DELETE_CUSTOMER: "delete_customer";
    readonly GET_CUSTOMER_JOBS: "get_customer_jobs";
    readonly LIST_EMPLOYEES: "list_employees";
    readonly GET_EMPLOYEE: "get_employee";
    readonly CREATE_EMPLOYEE: "create_employee";
    readonly UPDATE_EMPLOYEE: "update_employee";
    readonly GET_EMPLOYEE_SCHEDULE: "get_employee_schedule";
    readonly LIST_JOBS: "list_jobs";
    readonly GET_JOB: "get_job";
    readonly CREATE_JOB: "create_job";
    readonly UPDATE_JOB: "update_job";
    readonly DELETE_JOB: "delete_job";
    readonly RESCHEDULE_JOB: "reschedule_job";
    readonly GET_JOB_LINE_ITEMS: "get_job_line_items";
    readonly UPDATE_JOB_LINE_ITEMS: "update_job_line_items";
    readonly CREATE_JOB_LINE_ITEM: "create_job_line_item";
    readonly GET_JOB_LINE_ITEM: "get_job_line_item";
    readonly UPDATE_JOB_LINE_ITEM: "update_job_line_item";
    readonly DELETE_JOB_LINE_ITEM: "delete_job_line_item";
    readonly LIST_JOB_TYPES: "list_job_types";
    readonly GET_JOB_TYPE: "get_job_type";
    readonly CREATE_JOB_TYPE: "create_job_type";
    readonly UPDATE_JOB_TYPE: "update_job_type";
    readonly LIST_APPOINTMENTS: "list_appointments";
    readonly GET_APPOINTMENT: "get_appointment";
    readonly CREATE_APPOINTMENT: "create_appointment";
    readonly UPDATE_APPOINTMENT: "update_appointment";
    readonly DELETE_APPOINTMENT: "delete_appointment";
    readonly SEARCH_CACHE: "search_hcp_cache";
    readonly LIST_CACHE: "list_hcp_cache";
    readonly GET_CACHE_SUMMARY: "get_cache_summary";
    readonly CLEANUP_CACHE: "cleanup_hcp_cache";
    readonly SEARCH_ADDRESSES: "search_addresses";
    readonly GET_JOBS_BY_ADDRESS: "get_jobs_by_address";
    readonly ANALYZE_LAUNDRY_JOBS: "analyze_laundry_jobs";
    readonly ANALYZE_SERVICE_ITEMS: "analyze_service_items";
    readonly ANALYZE_CUSTOMER_REVENUE: "analyze_customer_revenue";
    readonly ANALYZE_JOB_STATISTICS: "analyze_job_statistics";
    readonly ANALYZE_TOWEL_USAGE: "analyze_towel_usage";
};
export declare const HTTP_METHODS: {
    readonly GET: "GET";
    readonly POST: "POST";
    readonly PUT: "PUT";
    readonly PATCH: "PATCH";
    readonly DELETE: "DELETE";
};
export declare const HTTP_STATUS: {
    readonly OK: 200;
    readonly CREATED: 201;
    readonly NO_CONTENT: 204;
    readonly BAD_REQUEST: 400;
    readonly UNAUTHORIZED: 401;
    readonly FORBIDDEN: 403;
    readonly NOT_FOUND: 404;
    readonly TOO_MANY_REQUESTS: 429;
    readonly INTERNAL_SERVER_ERROR: 500;
    readonly SERVICE_UNAVAILABLE: 503;
};
//# sourceMappingURL=constants.d.ts.map