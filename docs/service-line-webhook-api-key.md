# API Key Location for Service Line Webhook

## Where to Find the API Key

The API key for the webhook is stored in the `.env` file:

```bash
# Location
/home/opc/automation/src/automation/scripts/airscripts-api/.env

# View the key
grep AIRTABLE_API_KEY /home/opc/automation/src/automation/scripts/airscripts-api/.env
```

## Important Notes

1. **Use the same API key** that the airscripts-api service uses
2. **Keep it secure** - never share or commit this key
3. **The key works for both** development and production environments

## In Airtable Automation

When setting up the webhook in Airtable:
1. Add a header named `X-API-Key`
2. Copy the value from the .env file
3. Paste it as the header value (no quotes needed)

This key authenticates your Airtable automation to call the API endpoint.