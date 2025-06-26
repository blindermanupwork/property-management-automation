# Supabase Webhook Integration

## Overview

The Supabase webhook endpoint (`/webhooks/supabase`) allows external Supabase instances to send image data and other information that can be linked to existing HCP jobs in the system.

## Endpoint

```
POST https://servativ.themomentcatchers.com/webhooks/supabase
```

## Authentication

The webhook supports two authentication methods:

1. **Supabase Signature Verification** (Recommended)
   - Set `SUPABASE_WEBHOOK_SECRET` environment variable
   - Supabase will send signature in `X-Supabase-Signature` header
   - Format: `sha256=<hex_digest>`

2. **Servativ Forwarding Authentication**
   - Use `X-Internal-Auth` header with `SERVATIV_WEBHOOK_SECRET` value
   - For webhooks forwarded through Servativ's infrastructure

## Payload Format

### Standard Supabase Database Webhook

```json
{
  "type": "INSERT|UPDATE|DELETE",
  "table": "your_table_name",
  "record": {
    // One of these fields is required for job linking:
    "job_id": "job_fdf67b8c04c943e98d75230105a033ab",      // HCP job ID
    "hcp_job_id": "job_xxx",                               // Alternative field name
    "service_job_id": "job_xxx",                           // Alternative field name
    "reservation_uid": "RES-2025-001",                     // Airtable reservation UID
    "reference_id": "job_xxx",                             // Generic reference field
    
    // Image data can be provided in multiple ways:
    "image_urls": [                                        // Array of image URLs
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    
    "images": [                                           // Array of image objects
      {
        "filename": "before_photo.jpg",
        "url": "https://example.com/before.jpg"
      },
      {
        "filename": "after_photo.jpg",
        "data": "data:image/jpeg;base64,..."             // Base64 encoded image
      }
    ]
  },
  "old_record": {                                         // Previous record state (for UPDATE)
    // ... previous values
  }
}
```

## Job Reference Matching

The webhook will attempt to match the incoming data to an existing reservation using these fields in order:

1. **HCP Job ID** (`job_id`, `hcp_job_id`, `service_job_id`) - Matches against "Service Job ID" in Airtable
2. **Reservation UID** (`reservation_uid`) - Matches against "Reservation UID" in Airtable
3. **Reference ID** (`reference_id`) - Generic fallback, tries both methods

## Image Processing

### Supported Formats
- Direct URLs to images (will be downloaded)
- Base64 encoded image data
- Data URLs (e.g., `data:image/jpeg;base64,...`)

### Storage
- Images are saved to environment-specific directories:
  - Development: `/home/opc/automation/src/automation/images_development/`
  - Production: `/home/opc/automation/src/automation/images_production/`
- Filenames include timestamp, job reference, and unique ID

### File Naming Convention
```
YYYYMMDD_HHMMSS_<job_reference>_<unique_id>_<original_filename>
```

## Response

The webhook always returns HTTP 200 to prevent webhook disabling:

```json
{
  "status": "success",
  "message": "Webhook queued"
}
```

## Airtable Updates

When images are processed successfully:
- The reservation's "Sync Date and Time" is updated
- **Service Job Images** field is updated with image URLs (attachments)
- Sync details include: "Supabase webhook: {event_type}, Images: X uploaded to Airtable, Y saved locally"
- Direct URLs are uploaded to Airtable's attachment field automatically
- Base64/data URLs are saved locally (future enhancement: upload to CDN)

## Testing

Use the provided test script:

```bash
python3 testing/test-runners/test-supabase-webhook.py
```

## Environment Variables

Add to your `.env` file:

```bash
# Supabase webhook authentication (optional but recommended)
SUPABASE_WEBHOOK_SECRET=your-webhook-secret-here

# Image storage configuration (optional)
IMAGE_STORAGE_PATH=/custom/path/to/images
ENABLE_IMAGE_DOWNLOADS=true
```

## Example Supabase Database Webhook Setup

In your Supabase project:

1. Go to Database → Webhooks
2. Create new webhook
3. Configure:
   - Name: "Send images to Servativ"
   - Table: Your images/jobs table
   - Events: INSERT, UPDATE (as needed)
   - URL: `https://servativ.themomentcatchers.com/webhooks/supabase`
   - HTTP Headers: (leave empty, signature is automatic)
   - Payload: Use default database webhook payload

## Error Handling

- Missing job references are logged but don't cause failures
- Failed image downloads are logged individually
- All errors return HTTP 200 to prevent webhook disabling
- Check logs for detailed error information:
  - Development: `src/automation/logs/webhook_development.log`
  - Production: `src/automation/logs/webhook.log`

## Security Considerations

1. Always use HTTPS in production
2. Configure `SUPABASE_WEBHOOK_SECRET` for signature verification
3. Images are stored locally - ensure adequate disk space
4. Consider implementing image size limits
5. Validate image content types before processing

## Future Enhancements

1. Add dedicated Airtable field for image attachments
2. Upload images directly to Airtable as attachments
3. Support for image thumbnails/resizing
4. Implement image cleanup/retention policies
5. Add support for other file types (PDFs, documents)