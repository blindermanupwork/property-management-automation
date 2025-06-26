#!/bin/bash

echo "🔒 Targeted cleaning of sensitive data from git history..."
echo "This approach focuses on specific files for faster execution"
echo ""

# Create a targeted replacement script for known problematic files
cat > /tmp/targeted-replace.sh << 'EOF'
#!/bin/bash

# Target only specific files that we know had secrets
declare -A files_to_clean=(
    ["src/automation/config.py"]=1
    ["tools/debug-mcp-params.cjs"]=1
    ["tools/start-airtable-mcp.sh"]=1
    ["tools/test-airtable-mcp.js"]=1
    ["tools/airscripts-api-key.txt"]=1
    [".env"]=1
)

# Secrets to replace
declare -A secrets=(
    ["REDACTED_API_KEY"]="REDACTED-AIRTABLE-KEY"
    ["c7f3c26c0c4347c080d3fb4dda1bd193"]="REDACTED-HCP-DEV-TOKEN"
    ["7224147bbf9843cbb66c81b49262f605"]="REDACTED-HCP-PROD-TOKEN"
    ["REDACTED_DEV_API_KEY"]="REDACTED-AIRTABLE-DEV"
    ["REDACTED_PROD_API_KEY"]="REDACTED-AIRTABLE-PROD"
)

# Process only the targeted files
for file in "${!files_to_clean[@]}"; do
    if [ -f "$file" ]; then
        temp_file=$(mktemp)
        cp "$file" "$temp_file"
        
        # Replace each secret
        for secret in "${!secrets[@]}"; do
            sed -i "s|${secret}|${secrets[$secret]}|g" "$temp_file"
        done
        
        mv "$temp_file" "$file"
        echo "Cleaned: $file"
    fi
done
EOF

chmod +x /tmp/targeted-replace.sh

# Run filter-branch with targeted approach
echo "Starting targeted filter-branch operation..."
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force \
    --tree-filter '/tmp/targeted-replace.sh' \
    --tag-name-filter cat \
    -- --all

echo ""
echo "✅ Targeted cleaning complete!"
echo ""
echo "📋 Next: Verify the cleaning worked:"
echo "git log -p --all -S 'REDACTED_API_KEY' -- src/automation/config.py"