# Add Job Line Item

**POST** `https://api.housecallpro.com/jobs/{job_id}/line_items`

Add a line item to a job. This is a rate limited request. If you intend to create multiple line items for the same job use Bulk update a job's line items request.

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | The ID of the job (required) |

## Request Body

```json
{
  "uuid": "string",
  "service_item_id": "string",
  "service_item_type": "market_place",
  "name": "string",
  "unit_price": 0,
  "unit_cost": 0,
  "quantity": 0,
  "kind": "labor",
  "taxable": true,
  "description": "string"
}
```

### Field Descriptions

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `uuid` | string | Unique identifier | No |
| `service_item_id` | string | Service item ID | No |
| `service_item_type` | string | Allowed: `market_place`, `organizational`, `pricebook_material` | No |
| `name` | string | Line item name | Yes |
| `unit_price` | number | Price per unit | No |
| `unit_cost` | number | Cost per unit | No |
| `quantity` | number | Quantity | No |
| `kind` | string | Allowed: `tax`, `materials`, `labor`, `fixed_gratuity`, `fixed_discount` (default: `labor`) | No |
| `taxable` | boolean | Whether item is taxable | No |
| `description` | string | Item description | No |

## Response (201 Created)

```json
{
  "uuid": "string",
  "service_item_id": "string",
  "service_item_type": "market_place",
  "name": "string",
  "unit_price": 0,
  "unit_cost": 0,
  "quantity": 0,
  "kind": "labor",
  "taxable": true,
  "description": "string"
}
```

## cURL Example
```bash
curl --request POST \
  --url https://api.housecallpro.com/jobs/job_12345/line_items \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: YOUR_API_TOKEN' \
  --data '{
    "name": "Labor - Service Call",
    "unit_price": 15000,
    "unit_cost": 5000,
    "quantity": 1,
    "kind": "labor",
    "taxable": true,
    "description": "Basic service call labor"
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

job_id = 'job_12345'
data = {
    'name': 'Labor - Service Call',
    'unit_price': 15000,  # $150.00 in cents
    'unit_cost': 5000,    # $50.00 in cents
    'quantity': 1,
    'kind': 'labor',
    'taxable': True,
    'description': 'Basic service call labor'
}

response = requests.post(f'https://api.housecallpro.com/jobs/{job_id}/line_items', headers=headers, json=data)
line_item = response.json()
```