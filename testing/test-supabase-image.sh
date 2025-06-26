#!/bin/bash
# Test Supabase webhook with real image URLs

# Your webhook URL
WEBHOOK_URL="https://servativ.themomentcatchers.com/webhooks/supabase"

# Test with a real Supabase storage URL
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "INSERT",
    "table": "property_photos",
    "record": {
      "job_id": "job_26f468ec92fb40ca9b8a3fadda02ec25",
      "image_urls": [
        "https://hajzpkxjblpnrwodzxwi.supabase.co/storage/v1/object/public/property-photos/30443/30443_1750539699021_0.jpg"
      ]
    }
  }'

echo -e "\n\nCheck logs with: tail -f /home/opc/automation/src/automation/logs/webhook.log"