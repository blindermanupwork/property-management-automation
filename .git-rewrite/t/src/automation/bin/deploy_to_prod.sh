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
source config/environments/dev/.env
timeout 300 python3 run_anywhere.py --test || {
    echo "❌ Development tests failed - aborting deployment"
    exit 1
}

# Create backup
echo "💾 Creating backup..."
./bin/backup.sh

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
source config/environments/prod/.env

# Update dependencies
echo "📦 Updating dependencies..."
pip3 install -r requirements.txt --quiet
npm install --silent

# Verify deployment
echo "✅ Verifying deployment..."
./bin/monitor.sh

echo "🎉 Production deployment complete!"
echo "Repository: https://github.com/blindermanupwork/property-management-automation"

# Switch back to dev branch for continued development
git checkout dev