# Create Customer

**POST** `https://api.housecallpro.com/customers`

Create a new customer.

## Authentication
- API Key (Company API Key)
- API Key (Application API Key) 
- OAuth 2.0

## Request Body

```json
{
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
  "tags": ["string"],
  "addresses": [
    {
      "street": "string",
      "street_line_2": "string",
      "city": "string",
      "state": "string",
      "zip": "string",
      "country": "string"
    }
  ]
}
```

## Response (201 Created)

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
  ]
}
```

## cURL Example
```bash
curl --request POST \
  --url https://api.housecallpro.com/customers \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: YOUR_API_TOKEN' \
  --data '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "mobile_number": "555-0123",
    "company": "Example Corp"
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
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john.doe@example.com',
    'mobile_number': '555-0123',
    'company': 'Example Corp'
}

response = requests.post('https://api.housecallpro.com/customers', headers=headers, json=data)
customer = response.json()
```