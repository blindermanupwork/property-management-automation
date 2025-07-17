# Notification System

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Status:** Active Production Feature

## Overview

The notification system provides multi-channel alerting and communication capabilities throughout the property management automation platform. It delivers critical operational information to administrators, tracks system events, and ensures stakeholders are informed of important status changes.

## Business Purpose

### Why This Feature Exists
- **Operational Visibility**: Keep administrators informed of system status and issues
- **Error Escalation**: Alert appropriate personnel when critical errors occur
- **Status Updates**: Notify stakeholders of job completion and schedule changes
- **Compliance Tracking**: Maintain audit trails of all notification activities
- **Proactive Management**: Enable early intervention for potential issues

### What It Solves
- Delayed response to critical system failures
- Lack of visibility into automation status
- Manual monitoring requirements
- Missing audit trails for communications
- Inefficient error escalation processes

## Key Components

### 1. **Airtable Status Updates**
- Real-time automation status tracking
- Job creation and sync notifications
- Error condition reporting
- Schedule mismatch alerts

### 2. **Log File System**
- Structured logging with rotation
- Environment-specific log files
- Real-time error tracking
- Performance metrics logging

### 3. **Console Output**
- Live progress indicators
- Color-coded status messages
- UTF-8 character support
- Real-time operation feedback

### 4. **Webhook Notifications**
- HCP status change alerts
- Job completion notifications
- Error condition webhooks
- Real-time event streaming

### 5. **Email Alerts**
- Critical error notifications
- Daily summary reports
- Scheduled job confirmations
- System health alerts

## Technical Architecture

### Notification Channels

```
┌─────────────────────────────────────────────────────────────┐
│                   Notification System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Airtable   │  │   Log Files  │  │   Console    │    │
│  │   Updates    │  │    System    │  │   Output     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Webhook    │  │    Email     │  │   Metrics    │    │
│  │   Events     │  │   Alerts     │  │  Dashboard   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Notification Flow

1. **Event Detection**
   - System monitors for notification triggers
   - Events classified by severity and type
   - Context gathered for notification content

2. **Channel Selection**
   - Critical errors → Multiple channels
   - Status updates → Airtable + logs
   - Progress tracking → Console output
   - External events → Webhooks

3. **Message Formatting**
   - Standardized timestamp formats
   - Environment-specific content
   - Security sanitization applied
   - UTF-8 encoding handled

4. **Delivery & Tracking**
   - Messages sent through appropriate channels
   - Delivery status monitored
   - Failed notifications logged
   - Audit trail maintained

## Integration Points

### Internal Systems
- **Automation Controller**: Status updates and error reporting
- **Error Handler**: Critical error escalation
- **Job Manager**: Creation and completion notifications
- **Schedule Sync**: Mismatch alerts and corrections

### External Services
- **Airtable API**: Real-time field updates
- **HCP Webhooks**: Status change notifications
- **CloudMailin**: Email processing alerts
- **File System**: Log rotation and archival

## File Locations

### Core Implementation
- `/src/automation/controller.py` - Automation status updates
- `/src/automation/logs/` - Log file management
- `/src/automation/scripts/webhook/webhook.py` - Webhook notifications
- `/src/automation/scripts/shared/syncMessageBuilder.js` - Message formatting

### Configuration
- `.env` files - Channel configurations
- `/src/automation/config_base.py` - Logging setup
- `logging.conf` - Log rotation settings

### Log Files
- `automation_dev*.log` - Development automation logs
- `automation_prod*.log` - Production automation logs
- `webhook_development.log` - Dev webhook activity
- `webhook.log` - Production webhook activity

## Key Features

### 1. **Multi-Channel Delivery**
- Simultaneous notification across multiple channels
- Channel-specific formatting
- Fallback channel support
- Priority-based routing

### 2. **Smart Throttling**
- Prevents notification spam
- Aggregates similar events
- Respects quiet hours
- Rate limiting per channel

### 3. **Context Preservation**
- Full error context in logs
- Sanitized messages for external channels
- Correlation IDs for tracking
- Timestamp standardization

### 4. **Audit Trail**
- All notifications logged
- Delivery status tracked
- Failed attempts recorded
- Compliance reporting ready

## Configuration Examples

### Airtable Status Update
```python
# From controller.py
self.update_automation_status(
    automation_name="CSV Processing",
    success=True,
    details="Processed 15 files successfully",
    start_time=start_time
)
```

### Log Configuration
```python
# From config_base.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
```

### Console Output
```python
# Color-coded progress indicators
print(f"✅ {automation_name} completed successfully")
print(f"❌ {automation_name} failed with error: {error}")
print(f"⏭️ {automation_name} is disabled, skipping...")
```

## Security & Compliance

### Data Protection
- API keys masked in notifications
- Personal information sanitized
- Secure webhook signatures
- Encrypted email transport

### Audit Requirements
- All notifications logged
- Timestamps in multiple timezones
- User actions tracked
- Compliance reports available

## Performance Considerations

### Channel Performance
- **Airtable**: ~200ms per update
- **Logs**: <5ms write time
- **Console**: Immediate
- **Webhooks**: ~100ms delivery
- **Email**: Queued delivery

### Optimization Strategies
- Batch Airtable updates when possible
- Asynchronous webhook delivery
- Log rotation to prevent large files
- Console output buffering

## Monitoring & Metrics

### Key Metrics
- Notification delivery rate
- Channel response times
- Failed notification count
- Message volume by type

### Health Indicators
- All channels responsive
- No delivery backlogs
- Error rates within threshold
- Audit trail complete

## Common Issues & Solutions

### Issue: Notifications Not Delivered
- Check channel configuration
- Verify API credentials
- Review rate limits
- Check network connectivity

### Issue: Duplicate Notifications
- Review throttling settings
- Check event deduplication
- Verify webhook signatures
- Audit trigger conditions

### Issue: Missing Audit Trail
- Verify log rotation settings
- Check disk space
- Review retention policies
- Validate write permissions

## Related Documentation
- [Error Handling & Recovery](../15-error-handling-recovery/README.md)
- [Automation Controller](../13-automation-controller/README.md)
- [Webhook Processing](../12-webhook-processing/README.md)
- [Monitoring & Health Checks](../18-monitoring-health-checks/README.md)

---

**Next Steps**: Review [BusinessLogicAtoZ.md](./BusinessLogicAtoZ.md) for detailed notification rules or [SYSTEM_LOGICAL_FLOW.md](./SYSTEM_LOGICAL_FLOW.md) for visual flow diagrams.