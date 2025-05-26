#!/bin/bash
# Deploy from dev branch to production

set -e

echo "🚀 Starting deployment to production..."

# Ensure we're on dev branch and up to date
git checkout dev
git pull origin dev

# Test in development environment first
echo "🧪 Testing in development environment..."
export ENVIRONMENT=development
source environments/dev/.env
timeout 300 ./monitor.sh || {
    echo "❌ Development tests failed - aborting deployment"
    exit 1
}

# Create backup
echo "💾 Creating backup..."
./backup.sh

# Merge dev to main (production)
echo "🔄 Merging dev to main..."
git checkout main
git pull origin main
git merge dev --no-ff -m "Deploy: Merge dev to production

🚀 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to production
git push origin main

# Switch to production environment and restart services
echo "🔄 Switching to production environment..."
export ENVIRONMENT=production
source environments/prod/.env

# Update dependencies
echo "📦 Updating dependencies..."
pip install -r requirements.txt --quiet
npm install --silent

# Verify deployment
echo "✅ Verifying deployment..."
./monitor.sh

echo "🎉 Production deployment complete!"
echo "Repository: https://github.com/blindermanupwork/property-management-automation"

# Switch back to dev branch for continued development
git checkout dev