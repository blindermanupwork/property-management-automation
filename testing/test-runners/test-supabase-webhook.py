#!/usr/bin/env python3
"""Test script for Supabase webhook integration"""

import requests
import json
import hmac
import hashlib
import sys
import time

# Configuration
WEBHOOK_URL = "http://localhost:5000/webhooks/supabase"
WEBHOOK_SECRET = ""  # Set this if you have configured SUPABASE_WEBHOOK_SECRET

def generate_signature(payload, secret):
    """Generate HMAC-SHA256 signature for payload"""
    if not secret:
        return ""
    signature = hmac.new(
        secret.encode(),
        payload.encode() if isinstance(payload, str) else payload,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_ping():
    """Test basic connectivity with ping"""
    print("🏓 Testing ping...")
    response = requests.post(WEBHOOK_URL, json={"foo": "bar"})
    print(f"Response: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_webhook_with_job_id():
    """Test webhook with HCP job ID reference"""
    print("\n📤 Testing webhook with HCP job ID...")
    
    payload = {
        "type": "INSERT",
        "table": "job_images",
        "record": {
            "id": 1,
            "job_id": "job_fdf67b8c04c943e98d75230105a033ab",  # Example HCP job ID
            "image_urls": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg"
            ],
            "created_at": "2025-06-26T12:00:00Z"
        },
        "old_record": None
    }
    
    payload_str = json.dumps(payload)
    headers = {
        "Content-Type": "application/json"
    }
    
    if WEBHOOK_SECRET:
        headers["X-Supabase-Signature"] = generate_signature(payload_str.encode(), WEBHOOK_SECRET)
    
    response = requests.post(WEBHOOK_URL, data=payload_str, headers=headers)
    print(f"Response: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_webhook_with_reservation_uid():
    """Test webhook with Reservation UID reference"""
    print("\n📤 Testing webhook with Reservation UID...")
    
    payload = {
        "type": "UPDATE",
        "table": "job_images",
        "record": {
            "id": 2,
            "reservation_uid": "RES-2025-001",  # Example reservation UID
            "images": [
                {
                    "filename": "before_photo.jpg",
                    "url": "https://example.com/before.jpg"
                },
                {
                    "filename": "after_photo.jpg",
                    "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="  # Tiny base64 image
                }
            ],
            "updated_at": "2025-06-26T12:05:00Z"
        },
        "old_record": {
            "id": 2,
            "reservation_uid": "RES-2025-001",
            "images": [],
            "updated_at": "2025-06-26T12:00:00Z"
        }
    }
    
    payload_str = json.dumps(payload)
    headers = {
        "Content-Type": "application/json"
    }
    
    if WEBHOOK_SECRET:
        headers["X-Supabase-Signature"] = generate_signature(payload_str.encode(), WEBHOOK_SECRET)
    
    response = requests.post(WEBHOOK_URL, data=payload_str, headers=headers)
    print(f"Response: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_webhook_no_reference():
    """Test webhook with no job reference (should be handled gracefully)"""
    print("\n📤 Testing webhook with no job reference...")
    
    payload = {
        "type": "INSERT",
        "table": "job_images",
        "record": {
            "id": 3,
            "some_other_field": "value",
            "image_urls": ["https://example.com/orphan.jpg"]
        }
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    print(f"Response: {response.status_code} - {response.json()}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("🧪 Testing Supabase Webhook Integration")
    print("=" * 50)
    
    # Check if webhook server is running
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code != 200:
            print("❌ Webhook server not healthy!")
            return 1
    except requests.exceptions.RequestException:
        print("❌ Webhook server not running on port 5000!")
        print("   Please start it with: python3 src/automation/scripts/webhook/webhook.py")
        return 1
    
    print("✅ Webhook server is running")
    
    # Run tests
    tests = [
        test_ping,
        test_webhook_with_job_id,
        test_webhook_with_reservation_uid,
        test_webhook_no_reference
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Tests passed: {passed}/{len(tests)}")
    
    # Give time for async processing
    print("\n⏳ Waiting 5 seconds for async processing...")
    time.sleep(5)
    
    print("\n📋 Check the webhook logs for processing details:")
    print("   Development: tail -f src/automation/logs/webhook_development.log")
    print("   Production: tail -f src/automation/logs/webhook.log")
    
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    sys.exit(main())