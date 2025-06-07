# Get Customer

**GET** `https://api.housecallpro.com/customers/{customer_id}`

Get detailed information about a specific customer.

## Authentication
- API Key (Company API Key)
- API Key (Application API Key) 
- OAuth 2.0

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `customer_id` | string | Unique identifier for the customer |

## Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `expand` | array | Array of strings to expand response body. Allowed: `attachments` |

## Response (200 OK)

```json
{
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
  "notes": "string",
  "created_at": "string",
  "updated_at": "string",
  "company_name": "string",
  "company_id": "string",
  "tags": ["string"],
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
```

## cURL Example
```bash
curl --request GET \
  --url https://api.housecallpro.com/customers/cus_12345 \
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

customer_id = 'cus_12345'
response = requests.get(f'https://api.housecallpro.com/customers/{customer_id}', headers=headers)
customer = response.json()
```