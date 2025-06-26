#!/bin/bash

echo "🔒 Comprehensive secret cleaning from git history..."
echo "This will replace all occurrences of sensitive strings with REDACTED"
echo ""

# Create a replacement script
cat > /tmp/replace-secrets.sh << 'EOF'
#!/bin/bash

# List of patterns to replace
declare -A secrets=(
    ["patbrTH6yCjhAwd4i.972b74cbf7ea28c84e773759269c291628b5b4f4bfa11989ac4eff5d618f4003"]="REDACTED-AIRTABLE-KEY"
    ["c7f3c26c0c4347c080d3fb4dda1bd193"]="REDACTED-HCP-DEV-TOKEN"
    ["7224147bbf9843cbb66c81b49262f605"]="REDACTED-HCP-PROD-TOKEN"
    ["patyXgxqzJQYBgE2e.1e83544d7d123c91f3f6bb00cef9a14a073d734f152944c9a24fe18ae27bfdbb"]="REDACTED-AIRTABLE-DEV"
    ["patbrTH6yCjhAwd4i.c0cf3cd101ccb4382a2fa891292d4c393c9edc794e879cc16f9d4d1e9ab2ced1"]="REDACTED-AIRTABLE-PROD"
)

# Process all text files
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.sh" -o -name "*.yml" -o -name "*.yaml" -o -name "*.env" -o -name "*.cjs" -o -name "*.ts" -o -name "*.md" \) -print0 | while IFS= read -r -d '' file; do
    if [ -f "$file" ] && [ ! -L "$file" ]; then
        # Skip binary files and .git directory
        if [[ "$file" == *".git/"* ]]; then
            continue
        fi
        
        # Create temp file
        temp_file=$(mktemp)
        cp "$file" "$temp_file"
        
        # Replace each secret
        for secret in "${!secrets[@]}"; do
            if grep -q "$secret" "$temp_file" 2>/dev/null; then
                sed -i "s|${secret}|${secrets[$secret]}|g" "$temp_file"
                echo "Cleaned: $file"
            fi
        done
        
        # Move temp file back
        mv "$temp_file" "$file"
    fi
done
EOF

chmod +x /tmp/replace-secrets.sh

# Run filter-branch with the replacement script
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --tree-filter '/tmp/replace-secrets.sh' --tag-name-filter cat -- --all

echo "✅ Secrets replaced in git history!"
echo ""
echo "📋 Verification steps:"
echo "1. Check for secrets: git log -p --all | grep -E 'patbrTH6yCjhAwd4i|c7f3c26c0c4347c080d3fb4dda1bd193'"
echo "2. If clean, remove backup: rm -rf .git/refs/original/"
echo "3. Force push: git push --force --all"
echo "4. Cleanup: git reflog expire --expire=now --all && git gc --prune=now --aggressive"