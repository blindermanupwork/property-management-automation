#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import socket

def send_webhook_alert(email, subject, message):
    """
    Send alert email using a webhook service (ntfy.sh)
    This is more reliable than SMTP and doesn't require authentication
    """

    try:
        # Use ntfy.sh service for notifications
        topic = "airscripts-api-monitor-liveitup278"
        url = f"https://ntfy.sh/{topic}"

        # Send notification using header-based format
        headers = {
            "Title": subject,
            "Priority": "high" if "DOWN" in subject else "default",
            "Tags": "warning" if "DOWN" in subject else "check",
            "Email": email,
        }
        response = requests.post(url, data=message.encode('utf-8'), headers=headers, timeout=30)

        if response.status_code == 200:
            print(f"✅ Alert sent successfully to {email} via ntfy.sh")
            return True
        else:
            print(f"❌ Failed to send alert via ntfy.sh: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Failed to send webhook alert: {str(e)}")

        # Fallback: Log to syslog
        try:
            import syslog
            syslog.openlog("airscripts-monitor")
            syslog.syslog(syslog.LOG_ALERT, f"AirScripts API Alert: {subject} - {message}")
            print("📝 Alert logged to syslog as fallback")
        except:
            pass

        return False

def send_simple_webhook(email, subject, message):
    """
    Fallback: Use a simple HTTP service for email alerts
    """
    try:
        # Use httpbin as a test endpoint (replace with actual service)
        # In production, you might use SendGrid, Mailgun, or similar

        # For now, just write to a file that can be monitored
        alert_file = "/tmp/airscripts-alerts.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(alert_file, "a") as f:
            f.write(f"[{timestamp}] TO: {email}\n")
            f.write(f"[{timestamp}] SUBJECT: {subject}\n")
            f.write(f"[{timestamp}] MESSAGE: {message}\n")
            f.write("-" * 80 + "\n")

        print(f"📝 Alert written to {alert_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to write alert: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: send-webhook-alert.py <email> <subject> <message>")
        sys.exit(1)

    email = sys.argv[1]
    subject = sys.argv[2]
    message = sys.argv[3]

    # Try webhook first, fallback to file logging
    success = send_webhook_alert(email, subject, message)
    if not success:
        success = send_simple_webhook(email, subject, message)

    sys.exit(0 if success else 1)