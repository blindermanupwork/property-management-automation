// supabase/functions/send-images-to-servativ/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'

const SERVATIV_WEBHOOK_URL = 'https://servativ.themomentcatchers.com/webhooks/supabase'

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse request body
    const { job_id, reservation_uid, image_urls, property_id, filenames } = await req.json()

    // Validate input
    if (!job_id && !reservation_uid) {
      return new Response(
        JSON.stringify({ error: 'Missing job_id or reservation_uid' }), 
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Build image URLs if filenames provided
    let finalImageUrls = image_urls || []
    
    if (property_id && filenames && filenames.length > 0) {
      const baseUrl = 'https://hajzpkxjblpnrwodzxwi.supabase.co/storage/v1/object/public/property-photos'
      const additionalUrls = filenames.map((filename: string) => 
        `${baseUrl}/${property_id}/${filename}`
      )
      finalImageUrls = [...finalImageUrls, ...additionalUrls]
    }

    // Prepare webhook payload
    const webhookPayload = {
      type: 'INSERT',
      table: 'property_photos',
      record: {
        job_id: job_id,
        reservation_uid: reservation_uid,
        image_urls: finalImageUrls,
        property_id: property_id,
        timestamp: new Date().toISOString()
      }
    }

    console.log('Sending to Servativ:', webhookPayload)

    // Send to Servativ webhook
    const response = await fetch(SERVATIV_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(webhookPayload)
    })

    const result = await response.json()
    
    if (!response.ok) {
      throw new Error(`Servativ webhook failed: ${response.status}`)
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Images sent to Servativ',
        images_count: finalImageUrls.length,
        result: result 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )
  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    )
  }
})