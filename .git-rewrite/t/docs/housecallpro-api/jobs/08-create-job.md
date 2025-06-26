# Create a Job

**POST** `https://api.housecallpro.com/jobs`

Create a job with the ID for an already existing address and customer.

## Request Body

```json
{
  "invoice_number": 0,
  "customer_id": "string",
  "address_id": "string",
  "schedule": {
    "scheduled_start": "string",
    "scheduled_end": "string",
    "arrival_window": 0
  },
  "assigned_employee_ids": ["string"],
  "line_items": [
    {
      "name": "string",
      "description": "string",
      "unit_price": 0,
      "quantity": 1,
      "unit_cost": 0
    }
  ],
  "tags": ["string"],
  "lead_source": "string",
  "notes": "string",
  "job_fields": {
    "job_type_id": "string",
    "business_unit_id": "string"
  }
}
```

### Field Descriptions

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `invoice_number` | number | Invoice number must be unique across all jobs. If blank, auto-generated | No |
| `customer_id` | string | Customer ID | Yes |
| `address_id` | string | Address ID | Yes |
| `schedule.scheduled_start` | string | ISO-8601 formatted date string | No |
| `schedule.scheduled_end` | string | ISO-8601 formatted date string | No |
| `schedule.arrival_window` | integer | Arrival window in minutes | No |
| `assigned_employee_ids` | array[string] | Array of employee IDs | No |
| `line_items[].name` | string | Line item name | Yes |
| `line_items[].description` | string | Line item description | No |
| `line_items[].unit_price` | number | Selling price of single unit in cents | No |
| `line_items[].quantity` | number | Number of items (float up to 2 decimals) | No |
| `line_items[].unit_cost` | number | Direct cost to company per unit in cents | No |
| `tags` | array[string] | Job tags | No |
| `lead_source` | string | Lead source | No |
| `notes` | string | Job notes | No |
| `job_fields.job_type_id` | string | Job type ID | No |
| `job_fields.business_unit_id` | string | Business unit ID | No |

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
    "mobile_number": "string",
    "home_number": "string",
    "work_number": "string",
    "company": "string",
    "notifications_enabled": true,
    "lead_source": "string",
    "notes": [{"id": "string", "content": "string"}],
    "created_at": "string",
    "updated_at": "string",
    "company_name": "string",
    "company_id": "string",
    "tags": ["string"]
  },
  "address": {
    "id": "string",
    "type": "billing",
    "street": "string",
    "street_line_2": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string"
  },
  "notes": [{"id": "string", "content": "string"}],
  "work_status": "unscheduled",
  "work_timestamps": {
    "on_my_way_at": "string",
    "started_at": "string",
    "completed_at": "string"
  },
  "schedule": {
    "scheduled_start": "string",
    "scheduled_end": "string",
    "arrival_window": 0,
    "appointments": [
      {
        "id": "string",
        "start_time": "2021-01-10T10:45:00",
        "end_time": "2021-01-10T10:45:00",
        "arrival_window_minutes": 0,
        "dispatched_employees_ids": ["string"]
      }
    ]
  },
  "total_amount": 0,
  "outstanding_balance": 0,
  "assigned_employees": [
    {
      "id": "string",
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "mobile_number": "string",
      "color_hex": "string",
      "avatar_url": "string",
      "role": "string",
      "tags": ["string"],
      "permissions": {
        "can_add_and_edit_job": true,
        "can_be_booked_online": true,
        "can_call_and_text_with_customers": true,
        "can_chat_with_customers": true,
        "can_delete_and_cancel_job": true,
        "can_edit_message_on_invoice": true,
        "can_see_street_view_data": true,
        "can_share_job": true,
        "can_take_payment_see_prices": true,
        "can_see_customers": true,
        "can_see_full_schedule": true,
        "can_see_future_jobs": true,
        "can_see_marketing_campaigns": true,
        "can_see_reporting": true,
        "can_edit_settings": true,
        "is_point_of_contact": true,
        "is_admin": true
      },
      "company_name": "string",
      "company_id": "string"
    }
  ],
  "tags": ["string"],
  "original_estimate_id": "string",
  "lead_source": "string",
  "job_fields": {
    "job_type": {"id": "string", "name": "string"},
    "business_unit": {"id": "string", "name": "string"}
  },
  "attachments": [
    {
      "id": "string",
      "file_name": "string",
      "url": "string",
      "file_type": "string"
    }
  ],
  "created_at": "string",
  "updated_at": "string",
  "company_name": "string",
  "company_id": "string"
}
```

## cURL Example
```bash
curl --request POST \
  --url https://api.housecallpro.com/jobs \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: YOUR_API_TOKEN' \
  --data '{
    "customer_id": "cus_12345",
    "address_id": "adr_67890",
    "schedule": {
      "scheduled_start": "2023-12-01T09:00:00Z",
      "scheduled_end": "2023-12-01T11:00:00Z",
      "arrival_window": 30
    },
    "assigned_employee_ids": ["emp_123"],
    "line_items": [
      {
        "name": "Service Call",
        "description": "Basic service call",
        "unit_price": 15000,
        "quantity": 1,
        "unit_cost": 5000
      }
    ]
  }'
```

## Python Example
```python
import requests

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': 'YOUR_API_TOKEN'
}

data = {
    'customer_id': 'cus_12345',
    'address_id': 'adr_67890',
    'schedule': {
        'scheduled_start': '2023-12-01T09:00:00Z',
        'scheduled_end': '2023-12-01T11:00:00Z',
        'arrival_window': 30
    },
    'assigned_employee_ids': ['emp_123'],
    'line_items': [
        {
            'name': 'Service Call',
            'description': 'Basic service call',
            'unit_price': 15000,  # $150.00 in cents
            'quantity': 1,
            'unit_cost': 5000     # $50.00 in cents
        }
    ]
}

response = requests.post('https://api.housecallpro.com/jobs', headers=headers, json=data)
job = response.json()
```