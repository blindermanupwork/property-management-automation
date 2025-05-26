#!/bin/bash
# self-signed-ssl-setup.sh - Quick SSL setup without domain

echo "🔒 Setting up self-signed SSL certificates..."

# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Generate private key
echo "📝 Generating private key..."
sudo openssl genrsa -out /etc/nginx/ssl/nginx.key 2048

# Generate certificate signing request with pre-filled answers
echo "📄 Creating certificate signing request..."
sudo openssl req -new -key /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.csr -subj "/C=US/ST=California/L=Costa Mesa/O=Your Organization/OU=IT Department/CN=158.101.11.214/emailAddress=admin@example.com"

# Generate self-signed certificate (valid for 1 year)
echo "🔐 Generating self-signed certificate..."
sudo openssl x509 -req -days 365 -in /etc/nginx/ssl/nginx.csr -signkey /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt

# Set proper permissions
sudo chmod 600 /etc/nginx/ssl/nginx.key
sudo chmod 644 /etc/nginx/ssl/nginx.crt

echo "✅ Self-signed SSL certificates created!"
echo "📁 Certificate location: /etc/nginx/ssl/"

# Verify the files were created
echo "🔍 Verifying certificates..."
ls -la /etc/nginx/ssl/
