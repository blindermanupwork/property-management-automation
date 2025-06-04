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
    LINE_ITEM_KINDS: readonly ["service", "product", "discount", "fee"];
    ADDRESS_TYPES: readonly ["service", "billing"];
    CONTACT_TYPES: readonly ["phone", "email", "other"];
    APPOINTMENT_STATUSES: readonly ["scheduled", "in_progress", "completed", "canceled"];
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