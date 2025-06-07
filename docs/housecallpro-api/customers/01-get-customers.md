# Get Customers

**GET** `https://api.housecallpro.com/customers`

Get a list of customers.

## Authentication
- API Key (Company API Key)
- API Key (Application API Key) 
- OAuth 2.0

## Query Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `expand` | array | Array of strings to expand response body. Allowed: `attachments` | - |
| `location_ids` | array[string] | Id of locations you want to pull from | - |
| `page` | number | Current Page | 1 |
| `page_size` | number | Number of customers per page | 10 |
| `q` | string | Search for customer by name, email, mobile number and address | - |
| `sort_by` | string | Customer attribute to sort by | `created_at` |
| `sort_direction` | string | Ascending or descending (`asc`/`desc`) | `desc` |

## Response (200 OK)

```json
{
  "page": 0,
  "page_size": 0,
  "total_pages": 0,
  "total_items": 0,
  "customers": [
    {
      "id": "string",
      "first_name": "string",
      "last_name": "string", 
      "email": "string",
      "company": "string",
      "notifications_enabled": true,
      "mobile_number": "string",
      "home_number": "string",
      "work_number": "string",
      "tags": ["string"],
      "lead_source": "string",
      "notes": "string",
      "created_at": "string",
      "updated_at": "string",
      "company_name": "string",
      "company_id": "string",
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
      ],
      "attachments": []
    }
  ]
}
```

## cURL Example
```bash
curl --request GET \
  --url https://api.housecallpro.com/customers \
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

response = requests.get('https://api.housecallpro.com/customers', headers=headers, params=params)
data = response.json()
```