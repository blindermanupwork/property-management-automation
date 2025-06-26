#!/bin/bash

# AirScripts API Deployment Script

echo "🚀 Deploying AirScripts API..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install --production

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/airscripts-api.service << EOF
[Unit]
Description=AirScripts API Server
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/automation/src/automation/scripts/airscripts-api
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/airscripts-api.log
StandardError=append:/var/log/airscripts-api.error.log
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# Create log files
touch /var/log/airscripts-api.log
touch /var/log/airscripts-api.error.log
chown opc:opc /var/log/airscripts-api*.log

# Enable and start service
echo "🏃 Starting service..."
systemctl daemon-reload
systemctl enable airscripts-api
systemctl start airscripts-api

# Check status
if systemctl is-active --quiet airscripts-api; then
  echo "✅ AirScripts API is running!"
  echo ""
  echo "📊 Service status:"
  systemctl status airscripts-api --no-pager
  echo ""
  echo "📝 View logs with:"
  echo "  sudo journalctl -u airscripts-api -f"
  echo "  tail -f /var/log/airscripts-api.log"
else
  echo "❌ Failed to start AirScripts API"
  systemctl status airscripts-api --no-pager
  exit 1
fi

# Setup nginx (optional)
read -p "Do you want to configure nginx reverse proxy? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "📝 Add this to your nginx configuration:"
  echo ""
  cat << 'NGINX'
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your credentials"
echo "2. Configure your domain and SSL certificate"
echo "3. Update Airtable button scripts with your API URL"
echo "4. Test the API endpoints"