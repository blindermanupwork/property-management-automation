# Get Job Line Items

**GET** `https://api.housecallpro.com/jobs/{job_id}/line_items`

Lists all line items for a job.

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | The ID of the job (required) |

## Response (200 OK)

```json
{
  "url": "string",
  "data": [
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
  ]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `service_item_type` | string | Allowed: `market_place`, `organizational`, `pricebook_material` |
| `kind` | string | Allowed: `tax`, `materials`, `labor`, `fixed_gratuity`, `fixed_discount` |

## cURL Example
```bash
curl --request GET \
  --url https://api.housecallpro.com/jobs/job_12345/line_items \
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
response = requests.get(f'https://api.housecallpro.com/jobs/{job_id}/line_items', headers=headers)
line_items = response.json()
```