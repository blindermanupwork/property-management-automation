import { logger } from '../utils/logger.js';

// Map of API keys to their allowed actions
const API_KEYS = {
  [process.env.AIRSCRIPTS_API_KEY_CREATE_JOB]: ['create-job'],
  [process.env.AIRSCRIPTS_API_KEY_CREATE_ALL]: ['create-all-jobs'],
  [process.env.AIRSCRIPTS_API_KEY_CHECK_SCHEDULES]: ['check-schedules'],
  [process.env.AIRSCRIPTS_API_KEY_UPDATE_SCHEDULE]: ['update-schedule'],
  [process.env.AIRSCRIPTS_API_KEY_DELETE_JOB]: ['delete-job'],
  [process.env.AIRSCRIPTS_API_KEY_ADMIN]: ['*'], // Admin key for all actions
};

export function authenticateRequest(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    logger.warn('Request without API key', { 
      ip: req.ip, 
      path: req.path 
    });
    return res.status(401).json({ error: 'API key required' });
  }
  
  const allowedActions = API_KEYS[apiKey];
  
  if (!allowedActions) {
    logger.warn('Invalid API key attempt', { 
      ip: req.ip, 
      path: req.path 
    });
    return res.status(401).json({ error: 'Invalid API key' });
  }
  
  // Extract action from path (e.g., /api/airscripts/create-job -> create-job)
  const action = req.path.split('/').pop();
  
  if (allowedActions[0] !== '*' && !allowedActions.includes(action)) {
    logger.warn('Unauthorized action attempt', { 
      ip: req.ip, 
      path: req.path,
      action,
      allowedActions 
    });
    return res.status(403).json({ error: 'Action not allowed for this API key' });
  }
  
  // Add metadata to request
  req.apiKeyType = allowedActions[0] === '*' ? 'admin' : action;
  
  logger.info('Authenticated request', {
    ip: req.ip,
    path: req.path,
    action,
    apiKeyType: req.apiKeyType
  });
  
  next();
}