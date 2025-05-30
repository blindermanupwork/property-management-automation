// airtable-agent.js
import { SYSTEM_PROMPT } from './systemPrompt.js';   // adjust path if needed
import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';
import axios from 'axios';
import OpenAI from 'openai';
import dotenv from 'dotenv';
import { marked } from 'marked';
import cors from 'cors';
import morgan from 'morgan';
import helmet from 'helmet';

// Load environment variables
dotenv.config({ path: path.resolve('/home/opc/automation/.env') });

// Timezone utility for PST (for logging/display)
function getPSTTime() {
  const now = new Date();
  // PST is UTC-8, PDT is UTC-7. Get PST time.
  const pstTime = new Date(now.toLocaleString("en-US", {timeZone: "America/Los_Angeles"}));
  return pstTime.toISOString();
}

// Environment Constants
const CONFIG = {
  AIRTABLE_API_KEY: process.env.AIRTABLE_API_KEY || "pat-your-key-here",
  AIRTABLE_BASE_ID: process.env.AIRTABLE_BASE_ID || "app-your-base-id-here",
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || "sk-your-key-here",
  PORT: process.env.lang_PORT || 3000,
  MAX_HISTORY_LENGTH: 20,
  MAX_TOKENS_PER_MESSAGE: 1000,
};

// Set up Express with security and logging middleware
const app = express();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Basic security headers
app.use(helmet({
  contentSecurityPolicy: false, // Adjust as needed for your frontend
}));
app.use(cors());
app.use(morgan('dev'));
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Set up HTTP server and Socket.io
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*", // Configure appropriately for production
    methods: ["GET", "POST"]
  }
});

// Initialize OpenAI with API key
const openai = new OpenAI({
  apiKey: CONFIG.OPENAI_API_KEY
});

/**
 * In-memory stores for conversation history and schema information
 * In production, consider using Redis or another persistent store
 */
const memoryStore = new Map();

/**
 * Cache for Airtable schema information
 */
const schemaStore = {
  tables: null,
  tableFields: {},
  fieldOptions: {},
  lastUpdated: null
};

/*****************************
 * MARKDOWN HANDLING UTILITIES
 *****************************/

/*****************************
 * SOCKET UTILITIES
 *****************************/

/**
 * Check if a socket is still connected
 * @param {string} socketId - Socket ID to check
 * @returns {boolean} - True if connected
 */
function isSocketConnected(socketId) {
  const socket = io.sockets.sockets.get(socketId);
  return socket && socket.connected;
}
/**
 * Fixes markdown tables to ensure they have proper formatting
 * @param {string} text - The markdown text to fix
 * @returns {string} - Fixed markdown text
 */
function fixMarkdownTables(text) {
  // Split the text into sections (tables and non-tables)
  const sections = [];
  let currentSection = '';
  let inTable = false;
  const lines = text.split('\n');
  
  // Identify and separate table sections
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Check if this line starts a table
    if (!inTable && line.startsWith('|') && line.endsWith('|') && line.split('|').length > 2) {
      if (currentSection) {
        sections.push({ type: 'text', content: currentSection });
        currentSection = '';
      }
      inTable = true;
      currentSection = line;
    }
    // If we're in a table and this line is still part of it
    else if (inTable && line.startsWith('|')) {
      currentSection += '\n' + line;
    }
    // If we were in a table but this line is not part of it
    else if (inTable) {
      // Check if we at least have one line after the header
      const tableLines = currentSection.split('\n');
      
      // If we only have a header, add a separator row
      if (tableLines.length === 1) {
        const headerCells = tableLines[0].split('|').length - 2; // -2 for the empty cells at start/end
        let separatorRow = '|';
        for (let j = 0; j < headerCells; j++) {
          separatorRow += ' --- |';
        }
        currentSection += '\n' + separatorRow;
      }
      
      sections.push({ type: 'table', content: currentSection });
      currentSection = line;
      inTable = false;
    }
    // Regular text
    else {
      currentSection += (currentSection ? '\n' : '') + line;
    }
  }
  
  // Add the last section
  if (currentSection) {
    sections.push({ 
      type: inTable ? 'table' : 'text', 
      content: currentSection 
    });
  }
  
  // Fix each table section
  sections.forEach((section, i) => {
    if (section.type === 'table') {
      const tableLines = section.content.split('\n');
      
      // Make sure there's a separator row after the header
      if (tableLines.length > 1) {
        // Check if the second row is a proper separator
        const secondRow = tableLines[1].trim();
        const isSeparator = /^\|[\s-:]+(\|[\s-:]+)+\|$/.test(secondRow);
        
        if (!isSeparator) {
          // Count cells in header row
          const headerCells = tableLines[0].split('|').filter(Boolean).length;
          
          // Create a separator row
          let separatorRow = '|';
          for (let j = 0; j < headerCells; j++) {
            separatorRow += ' --- |';
          }
          
          // Insert the separator after the header
          tableLines.splice(1, 0, separatorRow);
          sections[i].content = tableLines.join('\n');
        }
      }
    }
  });
  
  // Reassemble the text with fixed tables
  return sections.map(section => section.content).join('\n\n');
}

/**
 * Preprocesses markdown tables to ensure they have proper separator rows
 * @param {string} text - The markdown text to preprocess
 * @returns {string} - Preprocessed markdown text
 */
function preprocessMarkdownTable(text) {
  const lines = text.split('\n');
  let inTable = false;
  let tableStartIndex = -1;
  
  // Find potential table starts
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Detect table start (line with multiple pipe characters)
    if (!inTable && line.includes('|') && line.split('|').length > 2) {
      inTable = true;
      tableStartIndex = i;
    }
    
    // If we found a table start, check if next line has a separator row
    if (inTable && i === tableStartIndex + 1) {
      const isSeparatorRow = /^\s*\|[\s-:]+\|[\s-:|]+$/.test(line);
      
      // If next line isn't a proper separator row, insert one
      if (!isSeparatorRow) {
        const headerCells = lines[tableStartIndex].split('|').length - 2; // -2 for empty cells at start/end
        let separatorRow = '|';
        for (let j = 0; j < headerCells; j++) {
          separatorRow += ' --- |';
        }
        
        // Insert the separator row
        lines.splice(i, 0, separatorRow);
        i++; // Skip the newly inserted line
      }
      inTable = false;
    }
  }
  
  return lines.join('\n');
}

/**
 * Safely stringify JSON, handling circular references
 * @param {any} obj - The object to stringify
 * @returns {string} - JSON string
 */
function safeJsonStringify(obj) {
  try {
    // Replace circular references and handle objects properly
    const seen = new WeakSet();
    return JSON.stringify(obj, (key, value) => {
      // Handle special cases
      if (value === undefined) return null; 
      if (typeof value === 'bigint') return value.toString();
      
      // Handle circular references
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) {
          return "[Circular Reference]";
        }
        seen.add(value);
      }
      return value;
    });
  } catch (err) {
    console.error("Error in safeJsonStringify:", err);
    return JSON.stringify({ error: "Failed to stringify response" });
  }
}

/**
 * Determines if a token should be skipped in the response stream
 * @param {string} token - The token to check
 * @returns {boolean} - True if the token should be skipped
 */
function shouldSkipToken(token) {
  // Tokens to skip completely
  const tokensToSkip = [
    "Analyzing your question...",
    "Gathering data...",
    "Analyzing data...",
    "."
  ];
  
  if (tokensToSkip.includes(token)) {
    return true;
  }
  
  // Patterns to skip
  const patternsToSkip = [
    "Analyzing data..."
  ];
  
  for (const pattern of patternsToSkip) {
    if (token.startsWith(pattern)) {
      return true;
    }
  }
  
  return false;
}

/*****************************
 * AIRTABLE API FUNCTIONS
 *****************************/

/**
 * Get all tables in the Airtable base
 * @returns {Promise<Array>} - List of tables
 */
async function getAirtableTables() {
  try {
    console.log("Fetching Airtable tables...");
    const response = await axios.get(`https://api.airtable.com/v0/meta/bases/${CONFIG.AIRTABLE_BASE_ID}/tables`, {
      headers: {
        Authorization: `Bearer ${CONFIG.AIRTABLE_API_KEY}`,
        "Content-Type": "application/json"
      }
    });
    
    // Cache tables in schema store
    schemaStore.tables = response.data.tables;
    schemaStore.lastUpdated = new Date();
    
    return response.data.tables;
  } catch (error) {
    console.error("Error fetching Airtable tables:", error.message);
    throw error;
  }
}

/**
 * Get a list of all views in an Airtable table
 * @param {string} tableName - The name of the table
 * @returns {Promise<Object>} - Table views information
 */
async function getTableViews(tableName) {
  try {
    // Get tables if not already cached
    if (!schemaStore.tables) {
      await getAirtableTables();
    }
    
    // Find the table
    const table = schemaStore.tables.find(t => 
      t.name.toLowerCase() === tableName.toLowerCase()
    );
    
    if (!table) {
      throw new Error(`Table '${tableName}' not found`);
    }
    
    // Extract view information
    const views = table.views.map(view => ({
      id: view.id,
      name: view.name,
      type: view.type,
    }));
    
    return {
      tableName,
      views
    };
  } catch (error) {
    console.error(`Error getting views for table '${tableName}':`, error.message);
    throw error;
  }
}

/**
 * Get detailed schema for a table including all field options
 * @param {string} tableName - The name of the table
 * @returns {Promise<Array>} - Table fields with options
 */
async function getTableSchema(tableName) {
  try {
    // Get tables if not already cached
    if (!schemaStore.tables) {
      await getAirtableTables();
    }
    
    // Find the table
    const table = schemaStore.tables.find(t => 
      t.name.toLowerCase() === tableName.toLowerCase()
    );
    
    if (!table) {
      throw new Error(`Table '${tableName}' not found`);
    }
    
    // Process each field to extract options
    const fields = table.fields.map(field => {
      const fieldInfo = {
        id: field.id,
        name: field.name,
        type: field.type
      };
      
      // Extract options for select fields
      if (field.type === 'singleSelect' || field.type === 'multipleSelects') {
        if (field.options && field.options.choices) {
          fieldInfo.choices = field.options.choices.map(choice => ({
            id: choice.id,
            name: choice.name,
            color: choice.color
          }));
          
          // Cache field options for later use
          if (!schemaStore.fieldOptions[tableName]) {
            schemaStore.fieldOptions[tableName] = {};
          }
          schemaStore.fieldOptions[tableName][field.name] = fieldInfo.choices;
        }
      }
      
      return fieldInfo;
    });
    
    // Cache the processed fields
    if (!schemaStore.tableFields[tableName]) {
      schemaStore.tableFields[tableName] = fields;
    }
    
    return fields;
  } catch (error) {
    console.error(`Error getting schema for table '${tableName}':`, error.message);
    throw error;
  }
}

/**
 * Preload schemas for all tables in the base
 * @returns {Promise<boolean>} - Success status
 */
async function preloadAllSchemas() {
  try {
    console.log("Preloading all table schemas...");
    
    // First get all tables
    const tables = await getAirtableTables();
    console.log(`Found ${tables.length} tables, now loading schemas...`);
    
    // Then load schema for each table
    for (const table of tables) {
      await getTableSchema(table.name);
      console.log(`Loaded schema for table: ${table.name}`);
    }
    
    console.log("All schemas preloaded successfully");
    return true;
  } catch (error) {
    console.error("Error preloading schemas:", error);
    return false;
  }
}

/**
 * Find exact match for field option value based on cached schema
 * @param {string} tableName - Table name
 * @param {string} fieldName - Field name
 * @param {string} value - Value to match
 * @returns {string} - Matched value or original value
 */
function getExactFieldOption(tableName, fieldName, value) {
  if (!schemaStore.fieldOptions[tableName] || !schemaStore.fieldOptions[tableName][fieldName]) {
    return value; // Return original if we don't have cached options
  }
  
  const options = schemaStore.fieldOptions[tableName][fieldName];
  
  // First try exact match
  const exactMatch = options.find(opt => opt.name === value);
  if (exactMatch) return exactMatch.name;
  
  // Then try case-insensitive match
  const caseInsensitiveMatch = options.find(opt => 
    opt.name.toLowerCase() === value.toLowerCase()
  );
  if (caseInsensitiveMatch) return caseInsensitiveMatch.name;
  
  // Finally return original if no match found
  return value;
}

/**
 * Process date-related values in filter conditions
 * @param {string|any} value - The value to process
 * @returns {string|any} - Processed value
 */
function processDateValue(value) {
  if (typeof value !== 'string') return value;
  
  // Process special date strings
  const lowerValue = value.toLowerCase();
  if (lowerValue === 'today') {
    return 'TODAY()';
  } else if (lowerValue === 'tomorrow') {
    return 'DATEADD(TODAY(), 1, "days")';
  } else if (lowerValue === 'yesterday') {
    return 'DATEADD(TODAY(), -1, "days")';
  } else if (lowerValue.match(/^(\d+)\s+days?\s+from\s+now$/i)) {
    const days = parseInt(lowerValue.match(/^(\d+)\s+days?\s+from\s+now$/i)[1]);
    return `DATEADD(TODAY(), ${days}, "days")`;
  } else if (lowerValue.match(/^(\d+)\s+days?\s+ago$/i)) {
    const days = parseInt(lowerValue.match(/^(\d+)\s+days?\s+ago$/i)[1]);
    return `DATEADD(TODAY(), -${days}, "days")`;
  } else if (lowerValue.match(/^next\s+week$/i)) {
    return 'DATEADD(TODAY(), 7, "days")';
  } else if (lowerValue.match(/^last\s+week$/i)) {
    return 'DATEADD(TODAY(), -7, "days")';
  }
  
  // If it's not a special date string, return the original value
  return value;
}

/**
 * Builds a filterByFormula string for Airtable API from filter conditions
 * @param {string} tableName - The table name
 * @param {Array} filters - Array of filter objects
 * @returns {string} - Filter formula string
 */
function buildFilterFormula(tableName, filters) {
  if (!filters || !Array.isArray(filters) || filters.length === 0) {
    return "";
  }

  const parts = filters.map(({ field, op, value }) => {
    // Check if this is a select field and we have cached options
    let processedValue = value;
    
    // For a select field with known options, try to match the exact value
    if (schemaStore.fieldOptions[tableName] && 
        schemaStore.fieldOptions[tableName][field]) {
      
      if (Array.isArray(value)) {
        // Handle array values for IN operator with multiple select options
        processedValue = value.map(v => getExactFieldOption(tableName, field, v));
      } else {
        // Handle single value
        processedValue = getExactFieldOption(tableName, field, value);
      }
    }
    
    // Handle date-related operations with special syntax for Airtable formulas
    const isDateField = field.toLowerCase().includes('date') || 
                       field.toLowerCase().includes('time') ||
                       field.toLowerCase().includes('deadline');
    
    // Process date values if this is a date field
    if (isDateField && processedValue) {
      if (Array.isArray(processedValue)) {
        processedValue = processedValue.map(v => processDateValue(v));
      } else {
        processedValue = processDateValue(processedValue);
      }
    }
    
    // Match the op exactly to what's in the Airtable UI
    switch (op) {
      // "is any of" in Airtable UI
      case "in":
        if (Array.isArray(processedValue)) {
          return `OR(${processedValue
            .map(v => {
              if (typeof v === 'string' && !v.includes('TODAY()') && !v.includes('DATEADD')) {
                return `{${field}}="${v}"`;
              } else {
                return `{${field}}=${v}`;
              }
            })
            .join(",")})`;
        }
        throw new Error("Value for 'in' operator must be an array");
        
      // "is none of" in Airtable UI
      case "not in":
        if (Array.isArray(processedValue)) {
          return `NOT(OR(${processedValue
            .map(v => {
              if (typeof v === 'string' && !v.includes('TODAY()') && !v.includes('DATEADD')) {
                return `{${field}}="${v}"`;
              } else {
                return `{${field}}=${v}`;
              }
            })
            .join(",")}))`; 
        }
        throw new Error("Value for 'not in' operator must be an array");
      
      // "is" in Airtable UI
      case "=":
      case "equals":
        if (typeof processedValue === 'string' && !processedValue.includes('TODAY()') && !processedValue.includes('DATEADD')) {
          return `{${field}}="${processedValue}"`;
        } else {
          return `{${field}}=${processedValue}`;
        }
      
      // "is not" in Airtable UI  
      case "!=":
        if (typeof processedValue === 'string' && !processedValue.includes('TODAY()') && !processedValue.includes('DATEADD')) {
          return `{${field}}!="${processedValue}"`;
        } else {
          return `{${field}}!=${processedValue}`;
        }
      
      // "contains" in Airtable UI
      case "contains":
        return `FIND("${processedValue}", {${field}})`;
      
      // "does not contain" in Airtable UI
      case "not contains":
        return `NOT(FIND("${processedValue}", {${field}}))`;
      
      // "is on or after" in Airtable UI - matches Airtable's behavior exactly
      case ">=":
        if (isDateField) {
          // When UI says "today", Airtable uses DATEADD(TODAY(), 0, "days")
          if (processedValue === 'TODAY()') {
            return `IS_AFTER({${field}}, DATEADD(TODAY(), 0, "days"))`;
          } else {
            return `IS_AFTER({${field}}, DATEADD(${processedValue}, -1, "days"))`;
          }
        } else {
          return `{${field}}>=${processedValue}`;
        }
      
      // "is on or before" in Airtable UI  
      case "<=":
        if (isDateField) {
          // For "10 days from now", need to use 11 to get inclusive 10 days
          if (processedValue.includes('DATEADD(TODAY()')) {
            // Extract the number of days from DATEADD(TODAY(), X, "days")
            const daysMatch = processedValue.match(/DATEADD\(TODAY\(\), (\d+), "days"\)/);
            if (daysMatch && daysMatch[1]) {
              const days = parseInt(daysMatch[1]);
              return `IS_BEFORE({${field}}, DATEADD(TODAY(), ${days + 1}, "days"))`;
            }
          }
          return `IS_BEFORE({${field}}, DATEADD(${processedValue}, 1, "days"))`;
        } else {
          return `{${field}}<=${processedValue}`;
        }
      
      // "is after" in Airtable UI  
      case ">":
        if (isDateField) {
          return `IS_AFTER({${field}}, ${processedValue})`;
        } else {
          return `{${field}}>${processedValue}`;
        }
      
      // "is before" in Airtable UI
      case "<":
        if (isDateField) {
          return `IS_BEFORE({${field}}, ${processedValue})`;
        } else {
          return `{${field}}<${processedValue}`;
        }
      
      // "is blank" in Airtable UI  
      case "empty":
        return `{${field}}=""`;
      
      // "is not blank" in Airtable UI  
      case "notEmpty":
      case "not_empty":
        return `NOT({${field}}="")`;
      
      // "is between" in Airtable UI  
      case "between":
        if (value && value.start && value.end) {
          const startVal = processDateValue(value.start);
          const endVal = processDateValue(value.end);
          
          if (isDateField) {
            return `AND(
              IS_AFTER({${field}}, DATEADD(${startVal}, -1, "days")),
              IS_BEFORE({${field}}, DATEADD(${endVal}, 1, "days"))
            )`;
          } else {
            return `AND(
              {${field}} >= ${startVal},
              {${field}} <= ${endVal}
            )`;
          }
        }
        throw new Error("Value for 'between' operator must have start and end properties");
      
      default:
        throw new Error(`Unsupported operator "${op}"`);
    }
  });
  
  return parts.length > 1 ? `AND(${parts.join(",")})` : parts[0] || "";
}

/**
 * Get all records from a table with pagination handling
 * @param {string} tableName - Table name
 * @param {Object} params - Query parameters
 * @returns {Promise<Array>} - Array of records
 */
async function getAllRecords(tableName, params = {}) {
  let allRecords = [];
  let offset = null;
  let page = 1;
  
  // Set default pageSize if not provided
  const pageSize = params.pageSize || 100;
  
  // Respect maxRecords if provided
  const maxRecords = params.maxRecords || Number.MAX_SAFE_INTEGER;
  
  do {
    // Build query parameters
    const queryParams = { ...params };
    
    // Add offset for pagination if we have one
    if (offset) {
      queryParams.offset = offset;
    }
    
    // Make the API request
    console.log(`Fetching page ${page} of records from ${tableName}`);
    try {
      const response = await axios.get(
        `https://api.airtable.com/v0/${CONFIG.AIRTABLE_BASE_ID}/${encodeURIComponent(tableName)}`, {
          headers: {
            Authorization: `Bearer ${CONFIG.AIRTABLE_API_KEY}`,
            "Content-Type": "application/json"
          },
          params: queryParams
        }
      );
      
      const pageRecords = response.data.records || [];
      allRecords = allRecords.concat(pageRecords);
      
      console.log(`Fetched ${pageRecords.length} records. Total so far: ${allRecords.length}`);
      
      // Get the offset for the next page
      offset = response.data.offset;
      
      // Stop if we've reached maxRecords
      if (allRecords.length >= maxRecords) {
        allRecords = allRecords.slice(0, maxRecords);
        break;
      }
      
      page++;
    } catch (error) {
      console.error(`Error fetching records from ${tableName}:`, error.message);
      throw error;
    }
  } while (offset); // Continue until there's no more offset
  
  console.log(`Finished fetching all ${allRecords.length} records from ${tableName}`);
  return allRecords;
}

/**
 * Gets formatted records with custom field mappings and Airtable links
 * @param {string} tableName - Table name
 * @param {Object} options - Query options
 * @returns {Promise<Object>} - Formatted records
 */
async function getFormattedRecords(tableName, options = {}) {
  try {
    console.log(`Getting formatted records from ${tableName} with options:`, options);
    
    // Default options
    const defaultOptions = {
      maxRecords: 30,
      view: null,
      filterByFormula: null,
      filters: null,
      sort: null,
      recordId: null
    };
    
    // Merge with provided options
    const mergedOptions = { ...defaultOptions, ...options };
    
    // Field mapping for custom display names
    const fieldMapping = {
      "Reservation UID": "UID",
      "HCP Address (from Property ID)": "Address",
      "Same-day Turnover": "Same-day",
      "Final Service Time": "Time",
      "Service Job Link": "Service Job Link",  
      "On My Way Time": "OMW",
      "Job Started Time": "Started",
      "Job Completed Time": "Completed"
    };
    
    // Order of fields for display
    const fieldOrder = [
      "Airtable Link", "UID", "Address", "Entry Type", "Service Type", 
      "Entry Source", "Check-in Date", "Check-out Date", "Same-day", "Time", 
      "Service Job Link", "Sync Status", "Sync Details", "Job Status", 
      "OMW", "Started", "Completed", "Assignee", "Status"
    ];
    
    // Get base ID, table ID, and view ID for constructing Airtable links
    const baseId = CONFIG.AIRTABLE_BASE_ID;
    let tableId = null;
    let viewId = null;
    
    // Get table ID from cached tables
    if (schemaStore.tables) {
      const table = schemaStore.tables.find(t => 
        t.name.toLowerCase() === tableName.toLowerCase()
      );
      
      if (table) {
        tableId = table.id;
        
        // If view name is provided, get its ID
        if (mergedOptions.view) {
          const viewName = mergedOptions.view;
          const view = table.views.find(v => 
            v.name.toLowerCase() === viewName.toLowerCase() || v.id === viewName
          );
          
          if (view) {
            viewId = view.id;
          }
        }
      }
    }

    // Specify fields to fetch (optimization)
    const fieldsToFetch = new Set();
    
    // Add original field names (before mapping)
    Object.keys(fieldMapping).forEach(originalField => {
      fieldsToFetch.add(originalField);
    });
    
    // Add other fields we want to display
    fieldOrder.forEach(field => {
      // Find the original field name if it's a mapped field
      const originalField = Object.keys(fieldMapping).find(key => fieldMapping[key] === field);
      if (originalField) {
        fieldsToFetch.add(originalField);
      } else if (field !== "Airtable Link" && field !== "ID") {
        // Skip Airtable Link and ID as they're not actual fields
        fieldsToFetch.add(field);
      }
    });
    
    let records = [];
    
    // If a specific record ID is provided, use the direct GET endpoint
    if (mergedOptions.recordId) {
      try {
        const response = await axios.get(
          `https://api.airtable.com/v0/${CONFIG.AIRTABLE_BASE_ID}/${encodeURIComponent(tableName)}/${mergedOptions.recordId}`, {
            headers: {
              Authorization: `Bearer ${CONFIG.AIRTABLE_API_KEY}`,
              "Content-Type": "application/json"
            },
            params: {
              // Only get the fields we need
              fields: [...fieldsToFetch]
            }
          }
        );
        
        // Single record response
        if (response.data && response.data.id) {
          records = [response.data];
        }
      } catch (error) {
        console.error(`Error fetching record ${mergedOptions.recordId}:`, error.message);
        throw error;
      }
    } else {
      // Prepare parameters for Airtable API
      const params = {
        fields: [...fieldsToFetch] // Only get the fields we need
      };
      
      // Set filterByFormula if directly provided
      if (mergedOptions.filterByFormula) {
        params.filterByFormula = mergedOptions.filterByFormula;
      }
      // Or build it from filters with schema awareness
      else if (mergedOptions.filters && mergedOptions.filters.length > 0) {
        params.filterByFormula = buildFilterFormula(tableName, mergedOptions.filters);
      }
      
      // Set other parameters if provided
      if (mergedOptions.sort) params.sort = mergedOptions.sort;
      if (mergedOptions.view) params.view = mergedOptions.view;
      if (mergedOptions.maxRecords) params.maxRecords = mergedOptions.maxRecords;
      
      // Get all records with pagination handling
      records = await getAllRecords(tableName, params);
    }
    
    console.log(`Retrieved ${records.length} records from ${tableName}`);
    
    // Get field schemas to better format different field types
    const tableFields = schemaStore.tableFields[tableName] || [];
    
    // Format records with custom field mappings and Airtable links
    const formattedRecords = records.map(record => {
      const recordId = record.id;
      
      // Create Airtable link
      let airtableLink = null;
      if (baseId && tableId && recordId) {
        // Format with view ID if available, otherwise without
        airtableLink = viewId 
          ? `https://airtable.com/${baseId}/${tableId}/${viewId}/${recordId}`
          : `https://airtable.com/${baseId}/${tableId}/${recordId}`;
      }
      
      // Start with empty mapped fields object
      const mappedFields = {};
      
      // Add Airtable link first with proper markdown formatting
      if (airtableLink) {
        mappedFields["Airtable Link"] = `[View in Airtable](${airtableLink})`;
      }
      
      // Add ID field
      mappedFields["ID"] = recordId;
      
      // Process all other fields with custom mappings
      for (const [originalField, value] of Object.entries(record.fields)) {
        // Map field name if it has a custom mapping
        const displayName = fieldMapping[originalField] || originalField;
        
        // Find the field schema to determine field type
        const fieldSchema = tableFields.find(f => f.name === originalField);
        const fieldType = fieldSchema ? fieldSchema.type : null;
        
        // Format based on field type
if (originalField === "Service Job Link" && value) {
  // Handle JSON object format from Airtable button field
  if (typeof value === 'object' && value.url && value.url.trim() !== '') {
    mappedFields[displayName] = `[Job Link](${value.url})`;
  }
  // Handle simple URL string format
  else if (typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))) {
    mappedFields[displayName] = `[Job Link](${value})`;
  } 
  // Handle JSON string that needs parsing
  else if (typeof value === 'string' && value.includes('"url"')) {
    try {
      const parsed = JSON.parse(value);
      if (parsed.url && parsed.url.trim() !== '') {
        mappedFields[displayName] = `[Job Link](${parsed.url})`;
      } else {
        mappedFields[displayName] = ''; // Show nothing if URL is empty
      }
    } catch (e) {
      mappedFields[displayName] = '';
    }
  }
  else {
    mappedFields[displayName] = ''; // Show nothing for empty/invalid values
  }
}
        // Handle date fields
        else if (fieldType === 'date' && value) {
          try {
            const date = new Date(value);
            if (!isNaN(date)) {
              // Format date as MM/DD/YYYY
              mappedFields[displayName] = date.toLocaleDateString('en-US');
            } else {
              mappedFields[displayName] = value;
            }
          } catch (e) {
            mappedFields[displayName] = value;
          }
        }
        // Handle date and time fields
        else if (fieldType === 'dateTime' && value) {
          try {
            const date = new Date(value);
            if (!isNaN(date)) {
              // Format date and time as MM/DD/YYYY, HH:MM AM/PM
              mappedFields[displayName] = date.toLocaleString('en-US');
            } else {
              mappedFields[displayName] = value;
            }
          } catch (e) {
            mappedFields[displayName] = value;
          }
        }
        // Handle select fields - show the name
        else if ((fieldType === 'singleSelect' || fieldType === 'multipleSelects') && value) {
          if (Array.isArray(value)) {
            // Multiple select - join with commas
            mappedFields[displayName] = value.join(', ');
          } else {
            // Single select
            mappedFields[displayName] = value;
          }
        }
        // Handle attachments - show as links
        else if (fieldType === 'multipleAttachments' && value && Array.isArray(value)) {
          const attachmentLinks = value.map(att => 
            `[${att.filename || 'File'}](${att.url})`
          ).join(', ');
          
          if (attachmentLinks) {
            mappedFields[displayName] = attachmentLinks;
          } else {
            mappedFields[displayName] = '';
          }
        }
        // Handle URL fields - make them clickable
        else if (fieldType === 'url' && value) {
          mappedFields[displayName] = `[${value}](${value})`;
        }
        // Handle boolean/checkbox fields
        else if (fieldType === 'checkbox' && value === true) {
          mappedFields[displayName] = '✓';
        }
        // Generic string dates (field type unknown but value looks like a date)
        else if (value && typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
          try {
            const date = new Date(value);
            if (!isNaN(date)) {
              // Format date as MM/DD/YYYY
              mappedFields[displayName] = date.toLocaleDateString('en-US');
            } else {
              mappedFields[displayName] = value;
            }
          } catch (e) {
            mappedFields[displayName] = value;
          }
        }
        // Default case - use value as is
        else {
          mappedFields[displayName] = value;
        }
      }
      
      return mappedFields;
    });
    
    // Collect all possible field names from the records
    const allFields = new Set();
    formattedRecords.forEach(record => {
      Object.keys(record).forEach(field => allFields.add(field));
    });
    
    // Create a list of fields in the preferred order, falling back to alphabetical
    const orderedFields = fieldOrder.filter(field => allFields.has(field));
    const remainingFields = [...allFields].filter(field => !fieldOrder.includes(field)).sort();
    const finalFieldOrder = [...orderedFields, ...remainingFields];
    
    return {
      tableName,
      viewId: viewId,
      recordCount: formattedRecords.length,
      fields: finalFieldOrder,
      records: formattedRecords
    };
  } catch (error) {
    console.error(`Error getting formatted records from ${tableName}:`, error);
    throw error;
  }
}

/**
 * Compare results between a view and a custom filter
 * @param {string} tableName - Table name
 * @param {string} viewName - View name
 * @param {Array} filters - Filter conditions
 * @returns {Promise<Object>} - Comparison results
 */
async function compareViewWithFilter(tableName, viewName, filters) {
  try {
    // Get records from the view
    const viewParams = {
      view: viewName,
      fields: ['id'] // Just get IDs for comparison
    };
    const viewRecords = await getAllRecords(tableName, viewParams);
    const viewRecordIds = new Set(viewRecords.map(r => r.id));
    
    // Get records with the custom filter
    const filterParams = {};
    if (filters && filters.length > 0) {
      filterParams.filterByFormula = buildFilterFormula(tableName, filters);
    }
    filterParams.fields = ['id'];
    
    const filteredRecords = await getAllRecords(tableName, filterParams);
    const filteredRecordIds = new Set(filteredRecords.map(r => r.id));
    
    // Find records in view but not in filter
    const viewOnlyRecords = viewRecords.filter(r => !filteredRecordIds.has(r.id));
    
    // Find records in filter but not in view
    const filterOnlyRecords = filteredRecords.filter(r => !viewRecordIds.has(r.id));
    
    // Check if they match exactly
    const isExactMatch = viewOnlyRecords.length === 0 && filterOnlyRecords.length === 0;
    
    return {
      tableName,
      viewName,
      viewRecordCount: viewRecords.length,
      filteredRecordCount: filteredRecords.length,
      isExactMatch,
      viewOnlyCount: viewOnlyRecords.length,
      filterOnlyCount: filterOnlyRecords.length,
      formula: filterParams.filterByFormula || null
    };
  } catch (error) {
    console.error(`Error comparing view with filter:`, error.message);
    throw error;
  }
}

/**
 * Suggest field names and options for a table
 * @param {string} tableName - Table name
 * @param {string} partialFieldName - Partial field name to filter by
 * @returns {Object} - Field suggestions
 */
function suggestFieldsAndOptions(tableName, partialFieldName = "") {
  // Check if we have the table fields cached
  if (!schemaStore.tableFields[tableName]) {
    return { 
      error: `Table '${tableName}' schema not loaded. Call get_table_schema first.` 
    };
  }
  
  // Filter fields by partial name if provided
  const matchingFields = partialFieldName 
    ? schemaStore.tableFields[tableName].filter(f => 
        f.name.toLowerCase().includes(partialFieldName.toLowerCase())
      )
    : schemaStore.tableFields[tableName];
  
  // Prepare result with fields and their options if they're select fields
  const result = {
    tableName,
    matchingFields: matchingFields.map(field => {
      const fieldInfo = {
        name: field.name,
        type: field.type
      };
      
      // Add options for select fields
      if ((field.type === 'singleSelect' || field.type === 'multipleSelects') && 
          schemaStore.fieldOptions[tableName] && 
          schemaStore.fieldOptions[tableName][field.name]) {
        fieldInfo.options = schemaStore.fieldOptions[tableName][field.name].map(opt => opt.name);
      }
      
      return fieldInfo;
    })
  };
  
  return result;
}

/**
 * Group records by field value
 * @param {Array} records - Records to group
 * @param {string} field - Field to group by
 * @returns {Array} - Grouped records
 */
function groupRecordsByField(records, field) {
  const groups = {};
  
  records.forEach(record => {
    const value = record.fields[field] || 'Unknown';
    if (!groups[value]) {
      groups[value] = [];
    }
    groups[value].push(record);
  });
  
  return Object.entries(groups).map(([value, groupRecords]) => ({
    value: value,
    count: groupRecords.length,
    percentage: (groupRecords.length / records.length * 100).toFixed(1) + '%',
    records: groupRecords
  }));
}

/*****************************
 * MEMORY MANAGEMENT FUNCTIONS
 *****************************/
/* ────────────────────────────────────────────────────────────── */
/* Build markdown describing tables, their views, and select options */
function buildSchemaContext() {
  if (!schemaStore.tables) return '';

  const lines = [];

  schemaStore.tables.forEach(t => {
    lines.push(`### ${t.name}`);
    if (t.views?.length) {
      lines.push(`*Views:* ${t.views.map(v => `\`${v.name}\``).join(', ')}`);
    }

    t.fields.forEach(f => {
      if (f.type === 'singleSelect' || f.type === 'multipleSelects') {
        const choices =
          schemaStore.fieldOptions[t.name]?.[f.name]?.map(c => `\`${c.name}\``).join(', ');
        lines.push(`- **${f.name}** (${f.type}) → ${choices || 'no options cached'}`);
      } else {
        lines.push(`- **${f.name}** (${f.type})`);
      }
    });

    lines.push(''); // blank line between tables
  });

  return lines.join('\n');
}

/* Produce the full dynamic prompt */
function getDynamicSystemPrompt() {
  return `${SYSTEM_PROMPT}

---
#### Airtable schema snapshot
${buildSchemaContext()}
`;
}

/**
 * Initialize conversation memory for a socket
 * @param {string} socketId - Socket ID
 * @returns {Object} - Memory object
 */
function initializeMemory(socketId) {
  if (!memoryStore.has(socketId)) {
    memoryStore.set(socketId, {
      messages: [],
      tables: null,
      lastTableQueried: null,
      queryResults: {},
      variableStore: {}
    });
  }
  return memoryStore.get(socketId);
}

/**
 * Add a message to the conversation history
 * @param {string} socketId - Socket ID
 * @param {string} role - Message role (system, user, assistant)
 * @param {string} content - Message content
 * @returns {Object} - Updated memory
 */
function addToMemory(socketId, role, content) {
  const memory = initializeMemory(socketId);
  
  // Truncate content to avoid excessive token usage
  let truncatedContent = content;
  if (typeof content === 'string' && content.length > CONFIG.MAX_TOKENS_PER_MESSAGE * 4) {
    truncatedContent = content.substring(0, CONFIG.MAX_TOKENS_PER_MESSAGE * 4) + "... [truncated]";
  }
  
  memory.messages.push({
    role,
    content: truncatedContent,
    timestamp: getPSTTime() // PST for logging/display
  });
  
  // Keep memory within limits
  if (memory.messages.length > CONFIG.MAX_HISTORY_LENGTH) {
    // Remove older messages but keep the first system message
    const systemMessage = memory.messages.find(m => m.role === 'system');
    memory.messages = memory.messages.slice(memory.messages.length - CONFIG.MAX_HISTORY_LENGTH + 1);
    
    // Re-add system message if it was removed
    if (memory.messages[0].role !== 'system') {
      memory.messages.unshift({
        role: 'system',
        content: getDynamicSystemPrompt()
      });
    }
  }
  
  return memory;
}

/**
 * Save query results for future reference
 * @param {string} socketId - Socket ID
 * @param {string} query - Query description
 * @param {Object} result - Query result
 * @returns {string} - Result key
 */
function saveQueryResults(socketId, query, result) {
  const memory = initializeMemory(socketId);
  const timestamp = getPSTTime(); // PST for logging/display
  
  // Create a unique key for this query result
  const resultKey = `query_${Object.keys(memory.queryResults).length + 1}`;
  
  // Store the result with metadata
  memory.queryResults[resultKey] = {
    query,
    result,
    timestamp
  };
  
  // Return the key so it can be referenced
  return resultKey;
}

/**
 * Get the conversation history
 * @param {string} socketId - Socket ID
 * @returns {Array} - Conversation history
 */
function getConversationHistory(socketId) {
  const memory = initializeMemory(socketId);
  return memory.messages;
}

/**
 * Save tables info to memory
 * @param {string} socketId - Socket ID
 * @param {Array} tables - Tables data
 */
function saveTablesToMemory(socketId, tables) {
  const memory = initializeMemory(socketId);
  memory.tables = tables;
}

/**
 * Save the last queried table
 * @param {string} socketId - Socket ID
 * @param {string} tableName - Table name
 */
function saveLastQueriedTable(socketId, tableName) {
  const memory = initializeMemory(socketId);
  memory.lastTableQueried = tableName;
}

/*****************************
 * OPENAI FUNCTION DEFINITIONS
 *****************************/

// Define the functions that will be available to the OpenAI model
const functionDefinitions = [
   {
    name: "debug_socket_status",
    description: "Debug the socket connection status",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "find_duplicates",
    description: "Finds duplicate records based on a field value within a filtered subset",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to search for duplicates"
        },
        duplicateField: {
          type: "string",
          description: "The field to check for duplicate values (e.g., 'Reservation UID')"
        },
        filterByFormula: {
          type: "string",
          description: "Optional Airtable formula to filter records before checking for duplicates"
        },
        filters: {
          type: "array",
          description: "Optional filters to apply before checking for duplicates",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string"
              },
              op: {
                type: "string",
                enum: ["contains", "=", "!=", ">", "<", ">=", "<=", "in", "between", "notEmpty", "empty"]
              },
              value: {}
            }
          }
        },
        view: {
          type: "string",
          description: "Optional view name or ID to use"
        },
        returnFullRecords: {
          type: "boolean",
          description: "Whether to return full record details or just summary (default: false)"
        }
      },
      required: ["tableName", "duplicateField"]
    }
  },
  {
    name: "get_formatted_records",
    description: "Gets formatted records with custom field mappings and Airtable links for table display",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to get records from"
        },
        maxRecords: {
          type: "integer",
          description: "Maximum number of records to return (default: 30)"
        },
        view: {
          type: "string",
          description: "Optional view name or ID to use"
        },
        filterByFormula: {
          type: "string",
          description: "Optional Airtable formula to filter records"
        },
        filters: {
          type: "array",
          description: "Optional filters to apply (alternative to filterByFormula)",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string"
              },
              op: {
                type: "string",
                enum: ["contains", "=", "!=", ">", "<", ">=", "<=", "in", "between", "notEmpty", "empty"]
              },
              value: {}
            }
          }
        },
        sort: {
          type: "array",
          description: "Optional sorting specifications",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string"
              },
              direction: {
                type: "string",
                enum: ["asc", "desc"]
              }
            },
            required: ["field"]
          }
        },
        recordId: {
          type: "string",
          description: "Optional specific record ID to fetch (if you want just one record)"
        }
      },
      required: ["tableName"]
    }
  },
  {
    name: "get_table_views",
    description: "Gets a list of all views in a table",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to get views from"
        }
      },
      required: ["tableName"]
    }
  },
  {
    name: "compare_view_with_filter",
    description: "Compares records in a view with records matching a custom filter",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table"
        },
        viewName: {
          type: "string",
          description: "The name of the view to compare"
        },
        filters: {
          type: "array",
          description: "Custom filters to compare against the view",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string",
                description: "Field name to filter on"
              },
              op: {
                type: "string",
                enum: ["contains", "=", "!=", ">", "<", ">=", "<=", "in", "between", "notEmpty", "empty"],
                description: "Operation to apply"
              },
              value: {
                description: "Value to compare against"
              }
            },
            required: ["field", "op"]
          }
        }
      },
      required: ["tableName", "viewName", "filters"]
    }
  },
  {
    name: "get_tables",
    description: "Gets a list of all tables in the Airtable base",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "get_table_schema",
    description: "Gets detailed information about the fields of a specific table",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to get fields from"
        }
      },
      required: ["tableName"]
    }
  },
  {
    name: "count_records",
    description: "Counts records in a table with support for filter conditions",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to count records from"
        },
        filterByFormula: {
          type: "string",
          description: "Optional Airtable formula to filter records"
        },
        filters: {
          type: "array",
          description: "Optional filters to apply (alternative to filterByFormula)",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string",
                description: "Field name to filter on"
              },
              op: {
                type: "string",
                enum: ["contains", "=", "!=", ">", "<", ">=", "<=", "in", "between", "notEmpty", "empty"],
                description: "Operation to apply"
              },
              value: {
                description: "Value to compare against"
              }
            },
            required: ["field", "op"]
          }
        },
        view: {
          type: "string",
          description: "Optional view name or ID to use"
        }
      },
      required: ["tableName"]
    }
  },
  {
    name: "group_by_field",
    description: "Groups records by a field and counts occurrences",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to group"
        },
        groupByField: {
          type: "string",
          description: "The field to group by"
        },
        filterByFormula: {
          type: "string",
          description: "Optional Airtable formula to filter records"
        },
        filters: {
          type: "array",
          description: "Optional filters to apply (alternative to filterByFormula)",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string",
                description: "Field name to filter on"
              },
              op: {
                type: "string",
                enum: ["contains", "=", "!=", ">", "<", ">=", "<=", "in", "between", "notEmpty", "empty"],
                description: "Operation to apply"
              },
              value: {
                description: "Value to compare against"
              }
            },
            required: ["field", "op"]
          }
        },
        sort: {
          type: "string",
          enum: ["count", "value"],
          description: "How to sort the groups: by count (default) or by value"
        },
        direction: {
          type: "string",
          enum: ["desc", "asc"],
          description: "Sort direction: descending (default) or ascending"
        },
        maxGroups: {
          type: "integer",
          description: "Maximum number of groups to return"
        }
      },
      required: ["tableName", "groupByField"]
    }
  },
  {
    name: "get_all_records",
    description: "Retrieves all records from a table, handling pagination automatically",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to retrieve all records from"
        },
        filterByFormula: {
          type: "string",
          description: "Optional Airtable formula to filter records"
        },
        filters: {
          type: "array",
          description: "Optional filters to apply (alternative to filterByFormula)",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string"
              },
              op: {
                type: "string",
                enum: ["contains", "=", "!=", ">", "<", ">=", "<=", "in", "between", "notEmpty", "empty"]
              },
              value: {}
            }
          }
        },
        fields: {
          type: "array",
          description: "Optional list of field names to include in the result",
          items: {
            type: "string"
          }
        },
        sort: {
          type: "array",
          description: "Optional sorting specifications",
          items: {
            type: "object",
            properties: {
              field: {
                type: "string"
              },
              direction: {
                type: "string",
                enum: ["asc", "desc"]
              }
            },
            required: ["field"]
          }
        },
        view: {
          type: "string",
          description: "Optional view name or ID to use"
        },
        maxRecords: {
          type: "integer",
          description: "Optional maximum total number of records to return"
        }
      },
      required: ["tableName"]
    }
  },
  {
    name: "suggest_fields_and_options",
    description: "Suggests field names and their select options for a table, with case-insensitive matching",
    parameters: {
      type: "object",
      properties: {
        tableName: {
          type: "string",
          description: "The name of the table to get field suggestions for"
        },
        partialFieldName: {
          type: "string",
          description: "Optional partial field name to filter suggestions"
        }
      },
      required: ["tableName"]
    }
  }
];

/*****************************
 * FUNCTION EXECUTION
 *****************************/

/**
 * Execute a function based on name and arguments
 * @param {string} functionName - Function name to execute
 * @param {Object} args - Function arguments
 * @param {string} socketId - Socket ID for memory management
 * @returns {Promise<any>} - Function result
 */
async function executeFunction(functionName, args, socketId) {
  try {
    console.log(`Executing function ${functionName} with args:`, args);
    
    switch (functionName) {
      case "debug_socket_status": {
  const socket = io.sockets.sockets.get(socketId);
  const connected = socket && socket.connected;
  const totalSockets = io.sockets.sockets.size;
  const memoryEntries = memoryStore.size;
  
  return {
    socketId: socketId,
    socketExists: !!socket,
    socketConnected: connected,
    totalConnectedSockets: totalSockets,
    memoryStoreSize: memoryEntries,
    timestamp: getPSTTime() // PST for logging/display
  };
}
      case "find_duplicates": {
      // Prepare parameters for Airtable API
      const params = {};
      
      // Set filterByFormula if directly provided
      if (args.filterByFormula) {
        params.filterByFormula = args.filterByFormula;
      }
      // Or build it from filters with schema awareness
      else if (args.filters && args.filters.length > 0) {
        params.filterByFormula = buildFilterFormula(args.tableName, args.filters);
      }
      
      // Set view if provided
      if (args.view) {
        params.view = args.view;
      }
      
      // Save the table name in memory
      saveLastQueriedTable(socketId, args.tableName);
      
      // Get all records matching the filter criteria
      const records = await getAllRecords(args.tableName, params);
      
      // Group records by the duplicate field
      const duplicateGroups = {};
      const duplicateRecords = [];
      
      records.forEach(record => {
        const fieldValue = record.fields[args.duplicateField];
        
        // Skip records where the field is empty
        if (!fieldValue) return;
        
        if (!duplicateGroups[fieldValue]) {
          duplicateGroups[fieldValue] = [];
        }
        duplicateGroups[fieldValue].push(record);
      });
      
      // Find groups with more than one record (duplicates)
      const duplicates = [];
      Object.entries(duplicateGroups).forEach(([value, groupRecords]) => {
        if (groupRecords.length > 1) {
          duplicates.push({
            duplicateValue: value,
            count: groupRecords.length,
            records: groupRecords
          });
          
          // Add all duplicate records to the flat array
          duplicateRecords.push(...groupRecords);
        }
      });
      
      const result = {
        tableName: args.tableName,
        duplicateField: args.duplicateField,
        totalRecordsChecked: records.length,
        duplicateGroupsFound: duplicates.length,
        totalDuplicateRecords: duplicateRecords.length,
        filtersApplied: !!(args.filterByFormula || (args.filters && args.filters.length > 0)),
        duplicates: args.returnFullRecords ? duplicates : duplicates.map(d => ({
          duplicateValue: d.duplicateValue,
          count: d.count,
          recordIds: d.records.map(r => r.id)
        }))
      };
       // Save the result to memory
      saveQueryResults(socketId, `Find duplicates in ${args.tableName} by ${args.duplicateField}`, result);
      
      return result;
    }
      case "get_formatted_records": {
  saveLastQueriedTable(socketId, args.tableName);
  const result = await getFormattedRecords(args.tableName, {
    maxRecords: args.maxRecords,
    view: args.view,
    filterByFormula: args.filterByFormula,
    filters: args.filters,
    sort: args.sort,
    recordId: args.recordId
  });
  
  // Always try to emit, but have robust fallback
  let emissionSuccessful = false;
  
  try {
    const socket = io.sockets.sockets.get(socketId);
    if (socket && socket.connected) {
      socket.emit('tableData', {
        tableName: args.tableName,
        fields: result.fields,
        records: result.records
      });
      
      console.log(`✅ Emitted ${result.records.length} records to socket ${socketId}`);
      emissionSuccessful = true;
    } else {
      console.warn(`⚠️ Socket ${socketId} not found or disconnected`);
    }
  } catch (emitError) {
    console.error(`❌ Socket emission failed for ${socketId}:`, emitError);
  }
  
  // Return lightweight placeholder - the table will be shown via socket emission
  return { 
    message: `Found ${result.records.length} records. Table displayed above.`,
    recordCount: result.records.length,
    tableName: args.tableName
  };
}
      case "get_table_views": {
        return await getTableViews(args.tableName);
      }
      
      case "compare_view_with_filter": {
        return await compareViewWithFilter(args.tableName, args.viewName, args.filters);
      }
      
      case "get_tables": {
        const tables = await getAirtableTables();
        saveTablesToMemory(socketId, tables);
        return tables.map(table => ({
          name: table.name,
          fieldCount: table.fields.length,
          recordCount: null // We don't know this without querying
        }));
      }
      
      case "get_table_schema": {
        const fields = await getTableSchema(args.tableName);
        return {
          tableName: args.tableName,
          fields: fields
        };
      }
      
      case "count_records": {
        // Prepare parameters for Airtable API
        const params = {};
        
        // Set filterByFormula if directly provided
        if (args.filterByFormula) {
          params.filterByFormula = args.filterByFormula;
        }
        // Or build it from filters with schema awareness
        else if (args.filters && args.filters.length > 0) {
          params.filterByFormula = buildFilterFormula(args.tableName, args.filters);
        }
        
        // Set view if provided
        if (args.view) {
          params.view = args.view;
        }
        
        // We only need the record IDs for counting
        params.fields = [];
        
        // Save the table name in memory
        saveLastQueriedTable(socketId, args.tableName);
        
        // Get all records with pagination handling
        const records = await getAllRecords(args.tableName, params);
        
        const result = {
          tableName: args.tableName,
          count: records.length,
          filtersApplied: !!(args.filterByFormula || (args.filters && args.filters.length > 0)),
          viewUsed: args.view || null
        };
        
        // Save the result to memory
        saveQueryResults(socketId, `Count records in ${args.tableName}`, result);
        
        return result;
      }
      
      case "group_by_field": {
        // Prepare parameters for Airtable API
        const params = {};
        
        // Set filterByFormula if directly provided
        if (args.filterByFormula) {
          params.filterByFormula = args.filterByFormula;
        }
        // Or build it from filters with schema awareness
        else if (args.filters && args.filters.length > 0) {
          params.filterByFormula = buildFilterFormula(args.tableName, args.filters);
        }
        
        // Save the table name in memory
        saveLastQueriedTable(socketId, args.tableName);
        
        // Get all records with pagination handling
        const records = await getAllRecords(args.tableName, params);
        
        // Group records by the specified field
        let groups = groupRecordsByField(records, args.groupByField);
        
        // Sort the groups
        const sortBy = args.sort || "count";
        const direction = args.direction || "desc";
        
        groups.sort((a, b) => {
          if (sortBy === "count") {
            return direction === "desc" ? b.count - a.count : a.count - b.count;
          } else { // sort by value
            if (a.value < b.value) return direction === "desc" ? 1 : -1;
            if (a.value > b.value) return direction === "desc" ? -1 : 1;
            return 0;
          }
        });
        
        // Limit the number of groups if requested
        if (args.maxGroups && args.maxGroups > 0) {
          groups = groups.slice(0, args.maxGroups);
        }
        
        const result = {
          totalRecords: records.length,
          uniqueValueCount: groups.length,
          groups: groups.map(g => ({
            value: g.value,
            count: g.count,
            percentage: g.percentage
          }))
        };
        
        // Save the result to memory
        saveQueryResults(socketId, `Group ${args.tableName} by ${args.groupByField}`, result);
        
        return result;
      }
      
      case "get_all_records": {
        // Prepare parameters for Airtable API
        const params = {};
        
        // Set filterByFormula if directly provided
        if (args.filterByFormula) {
          params.filterByFormula = args.filterByFormula;
        }
        // Or build it from filters with schema awareness
        else if (args.filters && args.filters.length > 0) {
          params.filterByFormula = buildFilterFormula(args.tableName, args.filters);
        }
        
        // Set other parameters if provided
        if (args.sort) params.sort = args.sort;
        if (args.view) params.view = args.view;
        if (args.fields) params.fields = args.fields;
        if (args.maxRecords) params.maxRecords = args.maxRecords;
        
        // Save the table name in memory
        saveLastQueriedTable(socketId, args.tableName);
        
        // Get all records with pagination handling
        const records = await getAllRecords(args.tableName, params);
        
        const result = {
          tableName: args.tableName,
          totalRecords: records.length,
          firstRecordId: records.length > 0 ? records[0].id : null,
          lastRecordId: records.length > 0 ? records[records.length - 1].id : null,
          sampleFields: records.length > 0 ? Object.keys(records[0].fields).slice(0, 10) : [],
          sampleRecords: records.slice(0, 3).map(r => ({
            id: r.id,
            fields: r.fields
          }))
        };
        
        // Save the result to memory
        saveQueryResults(socketId, `Get all records from ${args.tableName}`, result);
        
        return result;
      }
        
      case "suggest_fields_and_options": {
        return suggestFieldsAndOptions(args.tableName, args.partialFieldName);
      }
        
      default:
        throw new Error(`Unknown function: ${functionName}`);
    }
  } catch (error) {
    console.error(`Error executing ${functionName}:`, error);
    throw error;
  }
}

/*****************************
 * MESSAGE PROCESSING
 *****************************/

/**
 * Process a user message, get AI response, and handle function calls
 * @param {string} message - User message
 * @param {Object} socket - Socket.io socket
 * @returns {Promise<void>}
 */
async function processMessage(message, socket) {
  const socketId = socket.id;
  
  try {
    socket.emit('start');
    
    // Stream initial response
    socket.emit('token', { token: "Analyzing your question..." });
    
    // Add user message to memory
    addToMemory(socketId, 'user', message);
    
    // Get conversation history for context
    const conversationHistory = getConversationHistory(socketId);
    
    // Create messages array for OpenAI, adding a new system message if none exists
    let messages = [...conversationHistory];
    if (!messages.some(m => m.role === 'system')) {
      messages.unshift({
        role: 'system',
        content: getDynamicSystemPrompt()
      });
    }
    
    
    // Step 1: Use OpenAI to parse the query and identify the functions to call
    const aiResponse = await openai.chat.completions.create({
      model: "gpt-4.1",
      messages: messages,
      tools: functionDefinitions.map(fn => ({ type: "function", function: fn })),
      tool_choice: "auto",
      temperature: 0
    });
    
    const aiMessage = aiResponse.choices[0].message;
    let toolCalls = aiMessage.tool_calls || [];
    
    if (toolCalls.length === 0) {
      // No tool calls, just return the AI response
      socket.emit('token', { token: aiMessage.content });
      
      // Save AI response to memory
      addToMemory(socketId, 'assistant', aiMessage.content);
      
      socket.emit('complete', {});
      return;
    }
    
    // Execute each tool call and collect results
    const results = [];
    for (const toolCall of toolCalls) {
      socket.emit('token', { token: "\n\nGathering data..." });
      
      try {
        const functionName = toolCall.function.name;
        const functionArgs = JSON.parse(toolCall.function.arguments);
        
        // Log what function is being called
        console.log(`Calling function: ${functionName} with args:`, functionArgs);
        
        // Execute the function
        const result = await executeFunction(functionName, functionArgs, socketId);
        results.push({
          tool_call_id: toolCall.id,
          function_name: functionName,
          args: functionArgs,
          result: result
        });
        
        // Give some feedback as we process
        socket.emit('token', { token: "." });
      } catch (error) {
        console.error("Error executing function:", error);
        results.push({
          tool_call_id: toolCall.id,
          error: error.message
        });
      }
    }
    
    // Step 3: Send the results back to OpenAI to generate a natural language response
    socket.emit('token', { token: "\n\nAnalyzing data..." });
    
    // Prepare messages for final response
    const finalResponseMessages = [
      ...messages,
      aiMessage,
      ...results.map(result => {
        if (result.error) {
          return {
            role: "tool",
            tool_call_id: result.tool_call_id,
            content: safeJsonStringify({ error: result.error })
          };
        } else {
          return {
            role: "tool",
            tool_call_id: result.tool_call_id,
            content: safeJsonStringify(result.result)
          };
        }
      })
    ];
    
    const finalResponse = await openai.chat.completions.create({
      model: "gpt-4.1",
      messages: finalResponseMessages,
      stream: true
    });
    
    // Collect the full response to save to memory
    let fullResponse = '';
    
    // Stream the response tokens
    for await (const chunk of finalResponse) {
      const content = chunk.choices[0]?.delta?.content || '';
      if (content) {
        socket.emit('token', { token: content });
        fullResponse += content;
      }
    }
    
    // Save AI response to memory
    addToMemory(socketId, 'assistant', fullResponse);
    
    // Show memory stats
    const memory = memoryStore.get(socketId);
    console.log(`Memory for socket ${socketId}:`);
    console.log(`- Messages: ${memory.messages.length}`);
    console.log(`- Stored query results: ${Object.keys(memory.queryResults).length}`);
    
    socket.emit('complete', {});
  } catch (error) {
    console.error("Error processing message:", error);
    socket.emit('error', { message: error.message });
    socket.emit('complete', {});
  }
}

/*****************************
 * SOCKET HANDLING
 *****************************/

io.on('connection', async (socket) => {
  console.log('Client connected', socket.id);
  
  // Add system message to memory
  addToMemory(socket.id, 'system', getDynamicSystemPrompt());

  
  // Test Airtable connection on client connect
  try {
    const tables = await getAirtableTables();
    console.log("Airtable connection successful");
    console.log(`Found ${tables.length} tables:`);
    tables.forEach(table => {
      console.log(`- ${table.name} (${table.fields.length} fields)`);
    });
    
    // Save tables to memory
    saveTablesToMemory(socket.id, tables);
    
    // Preload all schemas in the background
    socket.emit('token', { token: "Initializing and loading table schemas..." });
    preloadAllSchemas().then(success => {
      if (success) {
        socket.emit('token', { token: "\nAll table schemas loaded successfully. You can now ask questions without worrying about exact capitalization of field values!" });
      } else {
        socket.emit('token', { token: "\nWarning: There was an issue preloading some schemas. You may need to check field values carefully." });
      }
      socket.emit('complete', {});
    });
    
    // Handle client messages
socket.on('message', async (data) => {
  try {
    // Check if socket is still connected before processing
    if (!socket.connected) {
      console.warn(`⚠️ Received message from disconnected socket ${socket.id}`);
      return;
    }
    
    await processMessage(data.message, socket);
  } catch (error) {
    console.error('Error processing message:', error);
    if (socket.connected) {
      socket.emit('error', { message: error.message });
      socket.emit('complete', {});
    }
  }
});
  } catch (error) {
    console.error("Airtable connection failed:", error.message);
    socket.emit('error', { message: "Failed to connect to Airtable. Please check API keys and permissions." });
  }
  
  socket.on('disconnect', () => {
  console.log('Client disconnected', socket.id);
  
  // Immediate cleanup for this socket
  if (memoryStore.has(socket.id)) {
    const memory = memoryStore.get(socket.id);
    console.log(`🧹 Cleaning up memory for socket ${socket.id}: ${memory.messages.length} messages, ${Object.keys(memory.queryResults).length} query results`);
    memoryStore.delete(socket.id);
  }
});
});

/*****************************
 * WEB SERVER ROUTES
 *****************************/

// Home route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    version: '1.0.0',
    uptime: process.uptime()
  });
});

// Start server
server.listen(CONFIG.PORT, '0.0.0.0', async () => {
  console.log(`Server running on http://0.0.0.0:${CONFIG.PORT}`);
  
  // Preload schemas when server starts
  console.log("Preloading schemas on server start...");
  const success = await preloadAllSchemas();
  console.log("Schema preloading completed:", success ? "Success" : "Issues occurred");
});
// Add this after the server.listen call
// Periodic cleanup of disconnected sockets
// Periodic cleanup of disconnected sockets  
setInterval(() => {
  // Clean up memory for disconnected sockets
  let cleanedUp = 0;
  for (const [socketId] of memoryStore.entries()) {
    if (!isSocketConnected(socketId)) {
      console.log(`🧹 Cleaning up memory for disconnected socket: ${socketId}`);
      memoryStore.delete(socketId);
      cleanedUp++;
    }
  }
  
  // Only log if there was actually cleanup needed
  if (cleanedUp > 0) {
    const connectedSockets = io.sockets.sockets.size;
    const memoryEntries = memoryStore.size;
    console.log(`🧹 Cleaned up ${cleanedUp} disconnected socket memories. Current: ${connectedSockets} sockets, ${memoryEntries} memory entries`);
  }
}, 300000); // Every 5 minutes
// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});