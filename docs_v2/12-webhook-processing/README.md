# Webhook Processing

## Overview
The Webhook Processing feature handles real-time updates from external systems through HTTP webhook endpoints. It manages webhook receipt from CloudMailin (email processing) and HousecallPro (job status updates), providing secure authentication, data validation, and automated response processing to maintain system synchronization.

## Core Functionality

### CloudMailin Webhook Processing
- **Email-to-Webhook Conversion**: Receives iTrip reservation emails forwarded through CloudMailin service
- **CSV Attachment Extraction**: Automatically downloads and processes reservation CSV files from email attachments
- **Authentication Validation**: Verifies CloudMailin webhook signatures for security
- **Bulk Email Processing**: Handles multiple attachments and large email volumes efficiently

### HousecallPro Webhook Processing
- **Job Status Updates**: Receives real-time job status changes from HousecallPro
- **Schedule Modifications**: Processes appointment time changes and cancellations
- **Worker Assignments**: Handles cleaner assignment updates and modifications
- **Dual Authentication**: Supports both direct HCP webhooks and forwarded webhook authentication

### Security and Authentication
- **Signature Verification**: Validates webhook authenticity using cryptographic signatures
- **Rate Limiting**: Prevents abuse through intelligent request throttling
- **IP Whitelisting**: Restricts webhook access to known service providers
- **Dual Auth Support**: Handles both original service signatures and forwarding authentication

## Key Components

### Webhook Endpoints
1. **CloudMailin Email Processing**: `/webhooks/cloudmailin` - Processes incoming reservation emails
2. **HCP Development**: `/webhooks/hcp-dev` - Development HCP job updates (port 5001)
3. **HCP Production**: `/webhooks/hcp` - Production HCP job updates (port 5000)
4. **Health Check**: `/webhooks/health` - Service availability monitoring

### Processing Pipeline
1. **Request Reception**: Webhook payload receipt and initial validation
2. **Authentication**: Signature verification and sender authentication
3. **Data Extraction**: Payload parsing and content extraction
4. **Validation**: Data quality checking and format validation
5. **Processing**: Business logic execution and system updates
6. **Response**: Confirmation response and error handling

### Integration Points
1. **Airtable Updates**: Direct record modifications based on webhook data
2. **File System Operations**: CSV file download and processing coordination
3. **Email Services**: CloudMailin integration for email-to-webhook conversion
4. **HCP API Synchronization**: Bidirectional data sync with HousecallPro

## Processing Architecture

### Environment Separation
- **Development Webhooks**: Separate endpoint and processing for development environment
- **Production Webhooks**: Isolated production processing with enhanced monitoring
- **Environment-Specific Routing**: Automatic routing based on webhook endpoint
- **Separate Logging**: Environment-specific log files and monitoring

### Error Handling and Recovery
- **Graceful Degradation**: Continue processing even with partial failures
- **Retry Logic**: Automatic retry for transient failures
- **Dead Letter Queue**: Failed webhook storage for manual review
- **Alert Generation**: Automatic notification for critical failures

### Performance Optimization
- **Asynchronous Processing**: Non-blocking webhook processing
- **Queue Management**: Intelligent queuing for high-volume periods
- **Resource Pooling**: Efficient use of system resources
- **Response Optimization**: Fast webhook response times

## Security Framework

### Authentication Methods
1. **CloudMailin Signatures**: HMAC-SHA256 signature verification
2. **HCP Signatures**: HousecallPro cryptographic signature validation
3. **Forwarding Authentication**: Custom authentication for forwarded webhooks
4. **IP Validation**: Source IP verification for additional security

### Data Protection
- **Payload Sanitization**: Input validation and sanitization
- **Sensitive Data Handling**: Secure processing of customer information
- **Audit Logging**: Complete webhook processing audit trails
- **Data Retention**: Secure storage and deletion policies

## Current Version
**Version**: 2.2.8
**Status**: Active with dual authentication support
**Environment Support**: Complete dev/prod separation
**Processing Volume**: 100+ webhooks daily (production)

## Related Documentation
- **CSV Processing**: For CloudMailin email attachment processing
- **HousecallPro Integration**: For job status update handling
- **API Server**: For webhook endpoint implementation
- **Environment Management**: For dev/prod webhook routing