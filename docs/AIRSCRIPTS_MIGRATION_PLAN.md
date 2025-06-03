# AirScripts Migration Plan

## Overview
This document outlines the migration strategy for moving AirScripts from Airtable's Script Extension to a controlled environment while maintaining button functionality and improving security.

## Current State Analysis

### Scripts Identified
1. **createjob.js** - Creates a single HCP job from a selected reservation
2. **createalljobs.js** - Batch creates HCP jobs for multiple reservations
3. **checkallschedules.js** - Checks and syncs all active reservation schedules
4. **updateallschedules.js** - Updates HCP schedules based on Final Service Time
5. **hcpupdateschedule.js** - Updates a single HCP job schedule
6. **deletejob.js** - Deletes/cancels an HCP job

### Authentication Method
- All scripts retrieve HCP API token from Airtable's "Secrets" table
- Token is stored with KeyName="hcpdev" and KeyValue containing the actual token
- This is insecure as anyone with Airtable access can view the token

### Dependencies
- Airtable Script Extension API (base, table, input, output)
- HousecallPro API
- No external npm packages (limited by Airtable environment)

### Button Fields in Reservations Table
Based on script analysis, the following button actions exist:
- Create Job (single reservation)
- Create All Jobs (batch)
- Check All Schedules
- Update Schedule
- Delete Job

## Migration Strategy

### Phase 1: Infrastructure Setup

#### 1.1 Create API Endpoint Service
```javascript
// src/automation/scripts/airscripts-api/server.js
import express from 'express';
import { authenticateRequest } from './auth.js';
import { createJob, createAllJobs, checkSchedules, updateSchedule, deleteJob } from './handlers.js';

const app = express();
app.use(express.json());
app.use(authenticateRequest);

// Endpoints matching button actions
app.post('/api/airscripts/create-job', createJob);
app.post('/api/airscripts/create-all-jobs', createAllJobs);
app.post('/api/airscripts/check-schedules', checkSchedules);
app.post('/api/airscripts/update-schedule', updateSchedule);
app.post('/api/airscripts/delete-job', deleteJob);

app.listen(process.env.AIRSCRIPTS_PORT || 3001);
```

#### 1.2 Secure Authentication
- Move HCP token to environment variables
- Implement API key authentication for webhook endpoints
- Generate unique API keys for each Airtable button

### Phase 2: Script Migration

#### 2.1 Refactor Scripts to Node.js Modules
Each script will be converted to a proper Node.js module:

```javascript
// src/automation/scripts/airscripts-api/handlers/createJob.js
import { getHCPClient } from '../services/hcp.js';
import { getAirtableClient } from '../services/airtable.js';

export async function createJob(req, res) {
  const { recordId, baseId } = req.body;
  
  try {
    // Fetch record from Airtable
    const airtable = getAirtableClient();
    const record = await airtable.base(baseId).table('Reservations').find(recordId);
    
    // Process job creation logic (migrated from createjob.js)
    // ... (existing logic)
    
    res.json({ success: true, jobId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

#### 2.2 Update Airtable Button Scripts
Replace complex logic with simple webhook calls:

```javascript
// New Airtable button script for "Create Job"
const API_KEY = 'YOUR_BUTTON_SPECIFIC_API_KEY'; // Store in Airtable Secrets table
const API_ENDPOINT = 'https://your-domain.com/api/airscripts/create-job';

const record = await input.recordAsync('Select a reservation', table);
if (!record) {
  output.text('No record selected');
  return;
}

output.text('Creating job...');

const response = await remoteFetchAsync(API_ENDPOINT, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify({
    recordId: record.id,
    baseId: base.id
  })
});

const result = await response.json();
if (result.success) {
  output.text(`✅ Job created: ${result.jobId}`);
} else {
  output.text(`❌ Error: ${result.error}`);
}
```

### Phase 3: Security Enhancements

#### 3.1 Environment Variables
Move all sensitive data to .env:
```bash
# HousecallPro Configuration
HCP_TOKEN=your_hcp_token_here
HCP_API_BASE=https://api.housecallpro.com

# API Security
AIRSCRIPTS_API_KEY_CREATE_JOB=generated_key_1
AIRSCRIPTS_API_KEY_CREATE_ALL=generated_key_2
AIRSCRIPTS_API_KEY_CHECK_SCHEDULES=generated_key_3
AIRSCRIPTS_API_KEY_UPDATE_SCHEDULE=generated_key_4
AIRSCRIPTS_API_KEY_DELETE_JOB=generated_key_5
```

#### 3.2 API Key Management
- Generate unique API keys for each button action
- Store API keys in Airtable Secrets table (but not the HCP token)
- Implement rate limiting per API key
- Add request logging and monitoring

### Phase 4: Deployment

#### 4.1 Service Deployment
```yaml
# docker-compose.yml addition
  airscripts-api:
    build: ./src/automation/scripts/airscripts-api
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
    env_file:
      - .env
    restart: unless-stopped
```

#### 4.2 Nginx Configuration
```nginx
location /api/airscripts/ {
    proxy_pass http://airscripts-api:3001/api/airscripts/;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
    
    # Rate limiting
    limit_req zone=airscripts burst=10 nodelay;
}
```

### Phase 5: Testing & Rollout

#### 5.1 Testing Strategy
1. **Unit Tests**: Test each handler function independently
2. **Integration Tests**: Test full workflow from Airtable button to HCP API
3. **Load Tests**: Ensure batch operations can handle expected volume
4. **Rollback Plan**: Keep original scripts as backup

#### 5.2 Gradual Rollout
1. Deploy API service to staging environment
2. Update one button (e.g., "Check All Schedules") as pilot
3. Monitor for 1 week
4. Roll out remaining buttons one at a time
5. Remove HCP token from Airtable Secrets table

## Benefits

1. **Security**: HCP token no longer exposed in Airtable
2. **Version Control**: All code in Git with proper history
3. **Testing**: Ability to write unit and integration tests
4. **Monitoring**: Centralized logging and error tracking
5. **Performance**: Better error handling and retry logic
6. **Maintainability**: Standard Node.js development practices

## Timeline

- **Week 1**: Infrastructure setup and API service scaffold
- **Week 2**: Migrate createJob and checkAllSchedules
- **Week 3**: Migrate remaining scripts
- **Week 4**: Testing and staging deployment
- **Week 5**: Production rollout and monitoring

## Risks & Mitigation

1. **Risk**: Airtable button timeout (30 seconds)
   - **Mitigation**: Implement async processing with status webhooks

2. **Risk**: API endpoint downtime affects operations
   - **Mitigation**: Implement redundancy and health checks

3. **Risk**: Breaking changes during migration
   - **Mitigation**: Maintain backward compatibility during transition

## Next Steps

1. Review and approve migration plan
2. Set up development environment for API service
3. Generate API keys for button authentication
4. Begin Phase 1 implementation