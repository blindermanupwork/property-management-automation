#!/bin/bash

# Script to clean sensitive data from git history
# WARNING: This will rewrite git history!

echo "⚠️  WARNING: This will rewrite your git history!"
echo "Make sure you have a backup (we created 'backup-before-cleanup' branch)"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo "🔍 Cleaning sensitive data from git history..."

# List of sensitive strings to remove
SENSITIVE_STRINGS=(
    "REDACTED_API_KEY"
    "c7f3c26c0c4347c080d3fb4dda1bd193"
    "7224147bbf9843cbb66c81b49262f605"
    "REDACTED_DEV_API_KEY"
    "REDACTED_PROD_API_KEY"
)

# Create a sed script to replace all sensitive strings
echo "#!/bin/sed -f" > /tmp/clean-secrets.sed
for secret in "${SENSITIVE_STRINGS[@]}"; do
    echo "s/${secret}/REDACTED-API-KEY/g" >> /tmp/clean-secrets.sed
done
chmod +x /tmp/clean-secrets.sed

# Run filter-branch to clean the history
git filter-branch --force --tree-filter '
    find . -type f -name "*.sh" -o -name "*.js" -o -name "*.py" -o -name "*.json" -o -name "*.env" -o -name "*.cjs" | 
    while read file; do
        if [ -f "$file" ]; then
            /tmp/clean-secrets.sed "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        fi
    done
' --tag-name-filter cat -- --all

echo "✅ Git history cleaned!"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Review the changes: git log --oneline"
echo "2. Force push to remote: git push --force --all"
echo "3. Force push tags: git push --force --tags"
echo "4. Clean up backup refs: git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin"
echo "5. Run garbage collection: git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo ""
echo "⚠️  All team members will need to re-clone the repository!"