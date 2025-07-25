# Get Jobs

**GET** `https://api.housecallpro.com/jobs`

Get a list of jobs

## Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `customer_id` | string | Filters jobs by a single customer ID | - |
| `employee_ids` | array | Array of employee IDs to filter by | - |
| `expand` | array | Array of strings to expand response body. Allowed: `attachments`, `appointments` | - |
| `franchisee_ids` | array | Gets jobs from the specified franchisees | - |
| `location_ids` | array[string] | Id of locations you want to pull from | - |
| `page` | string | Paginated page number | 1 |
| `page_size` | number | Number of jobs returned per page | 10 |
| `scheduled_end_max` | string | Filters jobs with an end time ≤ the date sent | - |
| `scheduled_end_min` | string | Filters jobs with an end time ≥ the date sent | - |
| `scheduled_start_max` | string | Filters jobs with a starting time ≤ the date sent | - |
| `scheduled_start_min` | string | Filters jobs with a starting time ≥ the date sent | - |
| `sort_by` | string | Attribute to sort by: `created_at`, `updated_at`, `invoice_number`, `id`, `description`, `work_status` | `created_at` |
| `sort_direction` | string | Sort direction: `asc`, `desc` | `desc` |
| `work_status` | array[string] | Work status filter: `unscheduled`, `scheduled`, `in_progress`, `completed`, `canceled` | - |

## Response (200 OK)

```json
{
  "page": 0,
  "page_size": 0,
  "total_pages": 0,
  "total_items": 0,
  "jobs": [
    {
      "id": "string",
      "invoice_number": "string",
      "name": "string",
      "description": "string",
      "customer": {
        "id": "string"
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
  ]
}
```

## cURL Example
```bash
curl --request GET \
  --url https://api.housecallpro.com/jobs \
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

params = {
    'page': 1,
    'page_size': 50,
    'work_status': ['scheduled', 'in_progress'],
    'sort_by': 'created_at',
    'sort_direction': 'desc'
}

response = requests.get('https://api.housecallpro.com/jobs', headers=headers, params=params)
jobs = response.json()
```