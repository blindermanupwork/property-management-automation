/**
 * Input validation utilities for HousecallPro MCP
 */

import { HCP_API } from './constants.js';

export class ValidationError extends Error {
  constructor(message: string, public field?: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Generic validators
export function validateRequired<T>(value: T | undefined | null, fieldName: string): T {
  if (value === undefined || value === null || value === '') {
    throw new ValidationError(`${fieldName} is required`);
  }
  return value;
}

export function validateString(value: any, fieldName: string, maxLength?: number): string {
  if (typeof value !== 'string') {
    throw new ValidationError(`${fieldName} must be a string`, fieldName);
  }
  
  if (maxLength && value.length > maxLength) {
    throw new ValidationError(`${fieldName} must be ${maxLength} characters or less`, fieldName);
  }
  
  return value;
}

export function validateNumber(value: any, fieldName: string, min?: number, max?: number): number {
  if (typeof value !== 'number' || isNaN(value)) {
    throw new ValidationError(`${fieldName} must be a valid number`, fieldName);
  }
  
  if (min !== undefined && value < min) {
    throw new ValidationError(`${fieldName} must be at least ${min}`, fieldName);
  }
  
  if (max !== undefined && value > max) {
    throw new ValidationError(`${fieldName} must be at most ${max}`, fieldName);
  }
  
  return value;
}

export function validateEmail(value: string, fieldName: string = 'email'): string {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    throw new ValidationError(`${fieldName} must be a valid email address`, fieldName);
  }
  return value;
}

export function validatePhoneNumber(value: string, fieldName: string = 'phone'): string {
  // Basic phone validation - US format
  const phoneRegex = /^[\+]?[1]?[\s\-\.]?[\(]?[0-9]{3}[\)]?[\s\-\.]?[0-9]{3}[\s\-\.]?[0-9]{4}$/;
  if (!phoneRegex.test(value.replace(/\s/g, ''))) {
    throw new ValidationError(`${fieldName} must be a valid phone number`, fieldName);
  }
  return value;
}

export function validateDate(value: string, fieldName: string): string {
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    throw new ValidationError(`${fieldName} must be a valid ISO 8601 date`, fieldName);
  }
  return value;
}

export function validateEnum<T extends readonly string[]>(
  value: string, 
  enumValues: T, 
  fieldName: string
): T[number] {
  if (!enumValues.includes(value as T[number])) {
    throw new ValidationError(
      `${fieldName} must be one of: ${enumValues.join(', ')}`, 
      fieldName
    );
  }
  return value as T[number];
}

// HCP-specific validators
export function validateHCPId(value: string, entityType: string): string {
  validateRequired(value, `${entityType} ID`);
  validateString(value, `${entityType} ID`);
  
  // HCP IDs typically follow pattern: prefix_uuid
  const idRegex = /^[a-z_]+[0-9a-f]+$/i;
  if (!idRegex.test(value)) {
    throw new ValidationError(`${entityType} ID must be a valid HCP ID format`, `${entityType}_id`);
  }
  
  return value;
}

export function validateJobStatus(status: string): string {
  return validateEnum(status, HCP_API.JOB_STATUSES, 'work_status');
}

export function validateEmployeeRole(role: string): string {
  return validateEnum(role, HCP_API.EMPLOYEE_ROLES, 'role');
}

export function validateLineItemKind(kind: string): string {
  return validateEnum(kind, HCP_API.LINE_ITEM_KINDS, 'kind');
}

export function validateAppointmentStatus(status: string): string {
  return validateEnum(status, HCP_API.APPOINTMENT_STATUSES, 'status');
}

export function validateSortDirection(direction: string): string {
  return validateEnum(direction, HCP_API.SORT_DIRECTIONS, 'sort_direction');
}

export function validateCustomerSortField(field: string): string {
  return validateEnum(field, HCP_API.CUSTOMER_SORT_FIELDS, 'sort_by');
}

// Pagination validators
export function validatePaginationParams(params: { page?: number; per_page?: number; page_size?: number }) {
  const result: { page: number; page_size: number } = {
    page: 1,
    page_size: HCP_API.DEFAULT_PAGE_SIZE
  };

  if (params.page !== undefined) {
    result.page = validateNumber(params.page, 'page', 1);
  }

  // Support both per_page and page_size parameters
  if (params.page_size !== undefined) {
    result.page_size = validateNumber(
      params.page_size, 
      'page_size', 
      1, 
      HCP_API.MAX_PAGE_SIZE
    );
  } else if (params.per_page !== undefined) {
    result.page_size = validateNumber(
      params.per_page, 
      'per_page', 
      1, 
      HCP_API.MAX_PAGE_SIZE
    );
  }

  return result;
}

// Date range validators
export function validateDateRange(params: { 
  start_date?: string; 
  end_date?: string; 
  fieldPrefix?: string 
}) {
  const prefix = params.fieldPrefix || '';
  
  if (params.start_date) {
    validateDate(params.start_date, `${prefix}start_date`);
  }
  
  if (params.end_date) {
    validateDate(params.end_date, `${prefix}end_date`);
  }
  
  if (params.start_date && params.end_date) {
    const start = new Date(params.start_date);
    const end = new Date(params.end_date);
    
    if (start >= end) {
      throw new ValidationError(
        `${prefix}start_date must be before ${prefix}end_date`
      );
    }
  }
}

// Schedule validation
export function validateSchedule(schedule: { 
  scheduled_start: string; 
  scheduled_end: string; 
  arrival_window?: number 
}) {
  validateDate(schedule.scheduled_start, 'scheduled_start');
  validateDate(schedule.scheduled_end, 'scheduled_end');
  
  const start = new Date(schedule.scheduled_start);
  const end = new Date(schedule.scheduled_end);
  
  if (start >= end) {
    throw new ValidationError('scheduled_start must be before scheduled_end');
  }
  
  if (schedule.arrival_window !== undefined) {
    validateNumber(schedule.arrival_window, 'arrival_window', 0, 480); // Max 8 hours
  }
  
  return schedule;
}

// Line item validation
export function validateLineItem(item: any) {
  validateRequired(item.name, 'line item name');
  validateString(item.name, 'name', 255);
  validateNumber(item.unit_price, 'unit_price', 0);
  validateNumber(item.quantity, 'quantity', 0);
  validateLineItemKind(item.kind);
  
  if (item.description) {
    validateString(item.description, 'description', 1000);
  }
  
  if (item.unit_cost !== undefined) {
    validateNumber(item.unit_cost, 'unit_cost', 0);
  }
  
  return item;
}

// Array validation
export function validateArray<T>(
  value: any, 
  fieldName: string, 
  itemValidator?: (item: any, index: number) => T,
  maxLength?: number
): T[] {
  if (!Array.isArray(value)) {
    throw new ValidationError(`${fieldName} must be an array`, fieldName);
  }
  
  if (maxLength && value.length > maxLength) {
    throw new ValidationError(`${fieldName} must have at most ${maxLength} items`, fieldName);
  }
  
  if (itemValidator) {
    return value.map((item, index) => {
      try {
        return itemValidator(item, index);
      } catch (error) {
        if (error instanceof ValidationError) {
          throw new ValidationError(
            `${fieldName}[${index}]: ${error.message}`,
            `${fieldName}[${index}]`
          );
        }
        throw error;
      }
    });
  }
  
  return value;
}