#!/usr/bin/env node

/**
 * Test script to verify pagination parameter validation
 */

// Import the compiled validators
import { validatePaginationParams } from './dist/hcp-mcp-common/src/validators.js';

console.log('🧪 Testing validatePaginationParams function');
console.log('============================================');

// Test 1: Default values
console.log('\n1️⃣ Test default values (no params):');
const test1 = validatePaginationParams({});
console.log('Input: {}');
console.log('Output:', JSON.stringify(test1, null, 2));

// Test 2: per_page = 100
console.log('\n2️⃣ Test per_page = 100:');
const test2 = validatePaginationParams({ per_page: 100 });
console.log('Input: { per_page: 100 }');
console.log('Output:', JSON.stringify(test2, null, 2));

// Test 3: per_page = 50, page = 2
console.log('\n3️⃣ Test per_page = 50, page = 2:');
const test3 = validatePaginationParams({ per_page: 50, page: 2 });
console.log('Input: { per_page: 50, page: 2 }');
console.log('Output:', JSON.stringify(test3, null, 2));

// Test 4: per_page = 10
console.log('\n4️⃣ Test per_page = 10:');
const test4 = validatePaginationParams({ per_page: 10 });
console.log('Input: { per_page: 10 }');
console.log('Output:', JSON.stringify(test4, null, 2));

console.log('\n✅ Validation tests completed');