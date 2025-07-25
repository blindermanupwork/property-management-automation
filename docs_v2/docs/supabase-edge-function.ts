// supabase/functions/send-images-to-servativ/index.ts
// Deploy this to your Supabase project

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SERVATIV_WEBHOOK_URL = 'https://servativ.themomentcatchers.com/webhooks/supabase'

serve(async (req) => {
  try {
    // Get the authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response('Unauthorized', { status: 401 })
    }

    // Parse request body
    const { job_id, reservation_uid, image_urls } = await req.json()

    if (!job_id && !reservation_uid) {
      return new Response('Missing job_id or reservation_uid', { status: 400 })
    }

    // Prepare webhook payload
    const webhookPayload = {
      type: 'INSERT',
      table: 'property_photos',
      record: {
        job_id: job_id,
        reservation_uid: reservation_uid,
        image_urls: image_urls,
        timestamp: new Date().toISOString()
      }
    }

    // Send to Servativ webhook
    const response = await fetch(SERVATIV_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(webhookPayload)
    })

    const result = await response.json()

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Images sent to Servativ',
        result: result 
      }),
      { 
        headers: { 'Content-Type': 'application/json' },
        status: 200 
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message 
      }),
      { 
        headers: { 'Content-Type': 'application/json' },
        status: 500 
      }
    )
  }
})

// Call this function from your app like:
// const { data, error } = await supabase.functions.invoke('send-images-to-servativ', {
//   body: {
//     job_id: 'job_xxxx',
//     image_urls: [
//       'https://hajzpkxjblpnrwodzxwi.supabase.co/storage/v1/object/public/property-photos/30443/30443_1750539699021_0.jpg'
//     ]
//   }
// })