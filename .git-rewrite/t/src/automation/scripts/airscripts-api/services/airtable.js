import Airtable from 'airtable';
import { logger } from '../utils/logger.js';

// Configure Airtable based on environment
const ENVIRONMENT = process.env.ENVIRONMENT || 'development';
const AIRTABLE_API_KEY = ENVIRONMENT === 'production' 
  ? process.env.PROD_AIRTABLE_API_KEY 
  : process.env.DEV_AIRTABLE_API_KEY;

class AirtableClient {
  constructor() {
    if (!AIRTABLE_API_KEY) {
      throw new Error('Airtable API key not configured for environment: ' + ENVIRONMENT);
    }
    
    Airtable.configure({
      apiKey: AIRTABLE_API_KEY
    });
    
    logger.info('Airtable client initialized', { environment: ENVIRONMENT });
  }

  base(baseId) {
    return Airtable.base(baseId);
  }

  async getRecord(baseId, tableName, recordId) {
    try {
      const record = await this.base(baseId).table(tableName).find(recordId);
      return record;
    } catch (error) {
      logger.error('Failed to fetch Airtable record', {
        baseId,
        tableName,
        recordId,
        error: error.message
      });
      throw error;
    }
  }

  async updateRecord(baseId, tableName, recordId, fields) {
    try {
      const record = await this.base(baseId).table(tableName).update(recordId, fields);
      logger.info('Updated Airtable record', {
        baseId,
        tableName,
        recordId,
        fields: Object.keys(fields)
      });
      return record;
    } catch (error) {
      logger.error('Failed to update Airtable record', {
        baseId,
        tableName,
        recordId,
        error: error.message
      });
      throw error;
    }
  }

  async findRecords(baseId, tableName, formula, options = {}) {
    try {
      const records = await this.base(baseId)
        .table(tableName)
        .select({
          filterByFormula: formula,
          ...options
        })
        .all();
      
      logger.info('Found Airtable records', {
        baseId,
        tableName,
        count: records.length
      });
      
      return records;
    } catch (error) {
      logger.error('Failed to find Airtable records', {
        baseId,
        tableName,
        formula,
        error: error.message
      });
      throw error;
    }
  }

  async getAllRecords(baseId, tableName, view = null) {
    try {
      const options = view ? { view } : {};
      const records = await this.base(baseId)
        .table(tableName)
        .select(options)
        .all();
      
      logger.info('Fetched all Airtable records', {
        baseId,
        tableName,
        view,
        count: records.length
      });
      
      return records;
    } catch (error) {
      logger.error('Failed to fetch all Airtable records', {
        baseId,
        tableName,
        view,
        error: error.message
      });
      throw error;
    }
  }
}

// Singleton instance
let airtableClient;

export function getAirtableClient() {
  if (!airtableClient) {
    airtableClient = new AirtableClient();
  }
  return airtableClient;
}