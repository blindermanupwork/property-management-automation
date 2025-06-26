# Get Employees

**GET** `https://api.housecallpro.com/employees`

Get all of the active employees in an organization.

## Authentication
- API Key (Company API Key)
- API Key (Application API Key) 
- OAuth 2.0

## Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `location_ids` | array[string] | Id of locations you want to pull from | - |
| `page` | number | Current page | 1 |
| `page_size` | number | Number of employees per page | 10 |
| `sort_by` | string | Employee attribute to sort by | `created_at` |
| `sort_direction` | string | Ascending or descending | `desc` |

## Response (200 OK)

```json
{
  "page": 0,
  "page_size": 0,
  "total_pages": 0,
  "total_items": 0,
  "employees": [
    {
      "id": "string",
      "avatar_url": "string",
      "color_hex": "string",
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "mobile_number": "string",
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
  ]
}
```

## cURL Example
```bash
curl --request GET \
  --url https://api.housecallpro.com/employees \
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
    'sort_by': 'created_at',
    'sort_direction': 'desc'
}

response = requests.get('https://api.housecallpro.com/employees', headers=headers, params=params)
employees = response.json()
```