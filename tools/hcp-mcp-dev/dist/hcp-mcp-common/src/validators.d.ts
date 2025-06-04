/**
 * Input validation utilities for HousecallPro MCP
 */
export declare class ValidationError extends Error {
    field?: string | undefined;
    constructor(message: string, field?: string | undefined);
}
export declare function validateRequired<T>(value: T | undefined | null, fieldName: string): T;
export declare function validateString(value: any, fieldName: string, maxLength?: number): string;
export declare function validateNumber(value: any, fieldName: string, min?: number, max?: number): number;
export declare function validateEmail(value: string, fieldName?: string): string;
export declare function validatePhoneNumber(value: string, fieldName?: string): string;
export declare function validateDate(value: string, fieldName: string): string;
export declare function validateEnum<T extends readonly string[]>(value: string, enumValues: T, fieldName: string): T[number];
export declare function validateHCPId(value: string, entityType: string): string;
export declare function validateJobStatus(status: string): string;
export declare function validateEmployeeRole(role: string): string;
export declare function validateLineItemKind(kind: string): string;
export declare function validateAppointmentStatus(status: string): string;
export declare function validatePaginationParams(params: {
    page?: number;
    per_page?: number;
}): {
    page: number;
    per_page: number;
};
export declare function validateDateRange(params: {
    start_date?: string;
    end_date?: string;
    fieldPrefix?: string;
}): void;
export declare function validateSchedule(schedule: {
    scheduled_start: string;
    scheduled_end: string;
    arrival_window?: number;
}): {
    scheduled_start: string;
    scheduled_end: string;
    arrival_window?: number;
};
export declare function validateLineItem(item: any): any;
export declare function validateArray<T>(value: any, fieldName: string, itemValidator?: (item: any, index: number) => T, maxLength?: number): T[];
//# sourceMappingURL=validators.d.ts.map