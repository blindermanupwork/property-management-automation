// Example: Call Servativ webhook directly from your app

async function sendImagesToServativ(jobId, imageUrls) {
  const WEBHOOK_URL = 'https://servativ.themomentcatchers.com/webhooks/supabase';
  
  try {
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        type: 'INSERT',
        table: 'property_photos',
        record: {
          job_id: jobId,
          image_urls: imageUrls,
          timestamp: new Date().toISOString()
        }
      })
    });

    const result = await response.json();
    console.log('Webhook response:', result);
    return result;
  } catch (error) {
    console.error('Error sending images to Servativ:', error);
    throw error;
  }
}

// Usage example:
// After uploading images to Supabase Storage
const imageUrls = [
  'https://hajzpkxjblpnrwodzxwi.supabase.co/storage/v1/object/public/property-photos/30443/30443_1750539699021_0.jpg',
  'https://hajzpkxjblpnrwodzxwi.supabase.co/storage/v1/object/public/property-photos/30443/30443_1750539699021_1.jpg'
];

await sendImagesToServativ('job_26f468ec92fb40ca9b8a3fadda02ec25', imageUrls);