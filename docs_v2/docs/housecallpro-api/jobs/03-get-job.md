# Get a Job

**GET** `https://api.housecallpro.com/jobs/{id}`

Get a job by ID.

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The ID of the job (required) |

## Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `expand` | array | Array of strings to expand response body. Allowed: `attachments`, `appointments` |

## Response (200 OK)

```json
{
  "id": "string",
  "invoice_number": "string",
  "description": "string",
  "customer": {
    "id": "string",
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "company": "string",
    "notifications_enabled": true,
    "mobile_number": "string",
    "home_number": "string",
    "work_number": "string",
    "addresses": [
      {
        "id": "string",
        "street": "string",
        "street_line_2": "string",
        "city": "string",
        "state": "string",
        "zip": "string",
        "country": "string"
      }
    ]
  },
  "address": {
    "id": "string",
    "street": "string",
    "street_line_2": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string"
  },
  "notes": "string",
  "work_status": "unscheduled",
  "work_timestamps": {
    "started_at": "string",
    "completed_at": "string",
    "on_my_way_at": "string"
  },
  "schedule": {
    "scheduled_start": "string",
    "scheduled_end": "string",
    "arrival_window": "string"
  },
  "total_amount": 0,
  "outstanding_balance": 0,
  "assigned_employees": [
    {
      "id": "string",
      "avatar_url": "string",
      "color_hex": "string",
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "mobile_number": "string",
      "role": "field tech",
      "permissions": {
        "can_add_and_edit_job": "boolean",
        "can_be_booked_online": "boolean",
        "can_call_and_text_with_customers": "boolean",
        "can_chat_with_customers": "boolean",
        "can_delete_and_cancel_job": "boolean",
        "can_edit_message_on_invoice": "boolean",
        "can_see_street_view_data": "boolean",
        "can_share_job": "boolean",
        "can_take_payment_see_prices": "boolean",
        "can_see_customers": "boolean",
        "can_see_full_schedule": "boolean",
        "can_see_future_jobs": "boolean",
        "can_see_marketing_campaigns": "boolean",
        "can_see_reporting": "boolean",
        "can_edit_settings": "boolean",
        "is_point_of_contact": "boolean",
        "is_admin": "boolean"
      }
    }
  ],
  "tags": ["string"],
  "original_estimate_id": "string",
  "lead_source": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

## cURL Example
```bash
curl --request GET \
  --url https://api.housecallpro.com/jobs/job_12345 \
  --header 'Accept: application/json' \
  --header 'Authorization: YOUR_API_TOKEN'
```

## Python Example
```python
import requests

headers = {
    'Accept': 'application/json',
    'Authorization': 'YOUR_API_TOKEN'
}

job_id = 'job_12345'
params = {'expand': ['attachments', 'appointments']}

response = requests.get(f'https://api.housecallpro.com/jobs/{job_id}', headers=headers, params=params)
job = response.json()
```