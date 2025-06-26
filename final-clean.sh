#!/bin/bash

echo "🔒 Final cleaning pass for remaining sensitive data..."
echo ""

# Create comprehensive replacement script
cat > /tmp/final-replace.sh << 'EOF'
#!/bin/bash

# All secrets to replace
declare -A secrets=(
    ["REDACTED_API_KEY"]="REDACTED-AIRTABLE-KEY"
    ["c7f3c26c0c4347c080d3fb4dda1bd193"]="REDACTED-HCP-DEV-TOKEN"
    ["7224147bbf9843cbb66c81b49262f605"]="REDACTED-HCP-PROD-TOKEN"
    ["REDACTED_DEV_API_KEY"]="REDACTED-AIRTABLE-DEV"
    ["REDACTED_PROD_API_KEY"]="REDACTED-AIRTABLE-PROD"
    ["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"]="REDACTED-OPENAI-KEY"
)

# Process ALL files this time
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.cjs" -o -name "*.sh" -o -name "*.json" -o -name "*.env" -o -name "*.txt" \) -print0 | while IFS= read -r -d '' file; do
    if [ -f "$file" ] && [ ! -L "$file" ] && [[ "$file" != *".git/"* ]]; then
        temp_file=$(mktemp)
        cp "$file" "$temp_file"
        
        changed=false
        for secret in "${!secrets[@]}"; do
            if grep -q "$secret" "$temp_file" 2>/dev/null; then
                sed -i "s|${secret}|${secrets[$secret]}|g" "$temp_file"
                changed=true
            fi
        done
        
        if [ "$changed" = true ]; then
            mv "$temp_file" "$file"
            echo "Cleaned: $file"
        else
            rm "$temp_file"
        fi
    fi
done
EOF

chmod +x /tmp/final-replace.sh

# Run final filter-branch
echo "Running final comprehensive cleaning..."
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force \
    --tree-filter '/tmp/final-replace.sh' \
    --tag-name-filter cat \
    -- --all

echo ""
echo "✅ Final cleaning complete!"