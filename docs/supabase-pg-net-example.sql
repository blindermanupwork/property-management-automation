-- Enable pg_net extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Create a function to send webhook
CREATE OR REPLACE FUNCTION send_images_to_servativ()
RETURNS TRIGGER AS $$
DECLARE
  payload jsonb;
  image_urls jsonb;
BEGIN
  -- Build image URLs array
  image_urls = jsonb_build_array(
    format('https://hajzpkxjblpnrwodzxwi.supabase.co/storage/v1/object/public/property-photos/%s/%s', 
      NEW.property_id, 
      NEW.filename)
  );
  
  -- Build webhook payload
  payload = jsonb_build_object(
    'type', TG_OP,
    'table', TG_TABLE_NAME,
    'record', jsonb_build_object(
      'job_id', NEW.job_id,
      'reservation_uid', NEW.reservation_uid,
      'image_urls', image_urls,
      'property_id', NEW.property_id,
      'filename', NEW.filename
    )
  );
  
  -- Send HTTP request using pg_net
  PERFORM net.http_post(
    url := 'https://servativ.themomentcatchers.com/webhooks/supabase',
    headers := '{"Content-Type": "application/json"}'::jsonb,
    body := payload::text
  );
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER send_images_webhook
AFTER INSERT OR UPDATE ON property_photos
FOR EACH ROW
EXECUTE FUNCTION send_images_to_servativ();