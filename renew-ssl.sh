#!/bin/bash
# SSL Certificate Auto-Renewal Script

echo "$(date): Starting SSL certificate renewal check..."

# Stop nginx
sudo systemctl stop nginx

# Renew certificates
sudo certbot renew --quiet

# Start nginx
sudo systemctl start nginx

# Test the renewal worked
if curl -s --max-time 10 https://servativ.themomentcatchers.com/api/prod/health > /dev/null 2>&1; then
    echo "$(date): SSL renewal successful - HTTPS working"
else
    echo "$(date): SSL renewal failed - HTTPS not responding"
fi