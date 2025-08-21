# Client Domain Configuration Options

## Domain Setup Options for Client Deployment

### Option 1: Subdomain (Recommended)
Use a subdomain of the client's main domain:
- `automation.clientname.com`
- `api.clientname.com`
- `manage.clientname.com`

**Advantages:**
- Keeps automation separate from main website
- Easy SSL certificate management
- Clear purpose in URL

### Option 2: Dedicated Domain
Register a specific domain for the automation:
- `clientname-automation.com`
- `clientname-management.com`

**Advantages:**
- Complete isolation from main domain
- Can transfer ownership easily
- Independent DNS management

### Option 3: Path-based (Not Recommended)
Use main domain with path:
- `clientname.com/automation`

**Disadvantages:**
- Complicated nginx configuration
- May conflict with existing website
- Harder to manage services

## Where to Update Domain References

### 1. Environment Files (.env)
```bash
# Root .env
API_DOMAIN=automation.clientname.com
HCP_WEBHOOK_URL=https://automation.clientname.com/webhooks/hcp

# CloudMailin webhook will be:
https://automation.clientname.com/webhooks/csv-email
```

### 2. Nginx Configuration
```nginx
server {
    server_name automation.clientname.com;
    # ... rest of config
}
```

### 3. External Services

#### CloudMailin
- Dashboard URL: `https://automation.clientname.com/webhooks/csv-email`

#### HousecallPro
- Production: `https://automation.clientname.com/webhooks/hcp`
- Development: `https://automation.clientname.com/webhooks/hcp-dev`

### 4. SSL Certificate
```bash
sudo certbot --nginx -d automation.clientname.com
```

## DNS Configuration

Add these DNS records at your DNS provider:

### For Subdomain (Option 1)
```
Type: A
Name: automation
Value: [NEW_SERVER_IP]
TTL: 300 (5 minutes during testing, increase later)
```

### For Dedicated Domain (Option 2)
```
Type: A
Name: @
Value: [NEW_SERVER_IP]
TTL: 300

Type: A  
Name: www
Value: [NEW_SERVER_IP]
TTL: 300
```

## Testing Before DNS Change

Before updating DNS, test with hosts file:
```bash
# On your local machine
echo "[NEW_SERVER_IP] automation.clientname.com" | sudo tee -a /etc/hosts

# Test
curl https://automation.clientname.com/api/health
```

## Important Notes

1. **Consistency**: Use the same domain everywhere - don't mix different domains
2. **HTTPS Only**: Always use https:// for webhooks (never http://)
3. **No Trailing Slashes**: Webhook URLs should not end with /
4. **Case Sensitive**: Some services are case-sensitive with URLs

## Example for Client "ABC Property Management"

If client is "ABC Property Management", you might use:
- Domain: `automation.abcproperty.com`
- CloudMailin: `https://automation.abcproperty.com/webhooks/csv-email`
- HCP Webhook: `https://automation.abcproperty.com/webhooks/hcp`
- API Health: `https://automation.abcproperty.com/api/health`