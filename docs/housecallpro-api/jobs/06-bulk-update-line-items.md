# Bulk Update Job Line Items

**PUT** `https://api.housecallpro.com/jobs/{job_id}/line_items/bulk_update`

Bulk update a job's line items. If uuid not defined for a line item it will be considered as a new line item for the job.

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | The ID of the job (required) |

## Request Body

```json
{
  "line_items": [
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
  ],
  "append_line_items": false
}
```

### Field Descriptions

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `line_items` | array | Array of line item objects | - |
| `line_items[].uuid` | string | Unique identifier (if not provided, creates new item) | - |
| `line_items[].service_item_id` | string | Service item ID | - |
| `line_items[].service_item_type` | string | Allowed: `market_place`, `organizational`, `pricebook_material` | - |
| `line_items[].name` | string | Line item name (required) | - |
| `line_items[].unit_price` | number | Price per unit | - |
| `line_items[].unit_cost` | number | Cost per unit | - |
| `line_items[].quantity` | number | Quantity | - |
| `line_items[].kind` | string | Allowed: `tax`, `materials`, `labor`, `fixed_gratuity`, `fixed_discount` | `labor` |
| `line_items[].taxable` | boolean | Whether item is taxable | - |
| `line_items[].description` | string | Item description | - |
| `append_line_items` | boolean | Append line items to job. If true, existing line items not in request will not be deleted | `false` |

## Response (200 OK)

```json
{
  "url": "string",
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "unit_price": 0,
      "unit_cost": 0,
      "unit_of_measure": 0,
      "quantity": 0,
      "kind": "labor",
      "taxable": true,
      "amount": 0,
      "order_index": 0,
      "service_item_id": "string",
      "service_item_type": "market_place"
    }
  ]
}
```

## cURL Example
```bash
curl --request PUT \
  --url https://api.housecallpro.com/jobs/job_12345/line_items/bulk_update \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: YOUR_API_TOKEN' \
  --data '{
    "line_items": [
      {
        "name": "Labor - Service Call",
        "unit_price": 15000,
        "unit_cost": 5000,
        "quantity": 1,
        "kind": "labor",
        "taxable": true,
        "description": "Basic service call labor"
      },
      {
        "name": "Parts - Filter",
        "unit_price": 2500,
        "unit_cost": 1000,
        "quantity": 2,
        "kind": "materials",
        "taxable": true,
        "description": "Replacement air filter"
      }
    ],
    "append_line_items": false
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
    'line_items': [
        {
            'name': 'Labor - Service Call',
            'unit_price': 15000,  # $150.00 in cents
            'unit_cost': 5000,    # $50.00 in cents
            'quantity': 1,
            'kind': 'labor',
            'taxable': True,
            'description': 'Basic service call labor'
        },
        {
            'name': 'Parts - Filter',
            'unit_price': 2500,   # $25.00 in cents
            'unit_cost': 1000,    # $10.00 in cents
            'quantity': 2,
            'kind': 'materials',
            'taxable': True,
            'description': 'Replacement air filter'
        }
    ],
    'append_line_items': False
}

response = requests.put(f'https://api.housecallpro.com/jobs/{job_id}/line_items/bulk_update', headers=headers, json=data)
result = response.json()
```