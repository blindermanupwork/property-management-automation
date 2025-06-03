/**
 * Environment-aware configuration
 * Mirrors the logic from your main automation config
 */

function getAirtableConfig(forceEnvironment = null) {
  const environment = forceEnvironment || process.env.ENVIRONMENT || 'development';
  
  if (environment === 'production') {
    return {
      apiKey: process.env.PROD_AIRTABLE_API_KEY,
      baseId: process.env.PROD_AIRTABLE_BASE_ID
    };
  } else {
    return {
      apiKey: process.env.DEV_AIRTABLE_API_KEY,
      baseId: process.env.DEV_AIRTABLE_BASE_ID
    };
  }
}

function getHCPConfig(forceEnvironment = null) {
  const environment = forceEnvironment || process.env.ENVIRONMENT || 'development';
  
  if (environment === 'production') {
    return {
      token: process.env.PROD_HCP_TOKEN,
      employeeId: process.env.PROD_HCP_EMPLOYEE_ID,
      jobTypes: {
        returnLaundry: process.env.PROD_HCP_RETURN_LAUNDRY_JOB_TYPE,
        inspection: process.env.PROD_HCP_INSPECTION_JOB_TYPE,
        turnover: process.env.PROD_HCP_TURNOVER_JOB_TYPE
      }
    };
  } else {
    return {
      token: process.env.DEV_HCP_TOKEN,
      employeeId: process.env.DEV_HCP_EMPLOYEE_ID,
      jobTypes: {
        returnLaundry: process.env.DEV_HCP_RETURN_LAUNDRY_JOB_TYPE,
        inspection: process.env.DEV_HCP_INSPECTION_JOB_TYPE,
        turnover: process.env.DEV_HCP_TURNOVER_JOB_TYPE
      }
    };
  }
}

module.exports = {
  getAirtableConfig,
  getHCPConfig
};