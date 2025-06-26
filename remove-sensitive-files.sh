#!/bin/bash

# Script to remove files with sensitive data from git history
# This is a safer approach - remove specific files that contained secrets

echo "🔒 Removing files with sensitive data from git history..."
echo "Backup branch 'backup-before-cleanup' has been created"
echo ""

# Remove specific files that contained hardcoded secrets
echo "📝 Removing files with hardcoded credentials..."

# Files that definitely had hardcoded secrets
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch tools/start-airtable-mcp.sh tools/test-airtable-mcp.js' \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✅ Files removed from history!"
echo ""
echo "📋 Next steps:"
echo "1. Check the results: git log --oneline --all -- tools/start-airtable-mcp.sh"
echo "2. If satisfied, force push: git push --force --all"
echo "3. Clean up: rm -rf .git/refs/original/"
echo "4. Run: git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo ""
echo "⚠️  WARNING: This rewrites history. All collaborators need to re-clone!"