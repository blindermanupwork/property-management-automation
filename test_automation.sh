#!/bin/bash

# Test Property Management Automation Components
cd ~/automation

echo "🧪 Testing Property Management Automation Components..."
echo "========================================================"

# Test 1: Environment variables
echo "1. Testing environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    # Check if it has the main keys (without showing values)
    if grep -q "AIRTABLE_API_KEY" .env; then
        echo "✅ Airtable config found"
    else
        echo "❌ Airtable config missing"
    fi
else
    echo "❌ .env file missing"
fi

# Test 2: Python scripts
echo ""
echo "2. Testing Python script syntax..."
python3 -m py_compile scripts/gmail/gmail_downloader.py && echo "✅ Gmail script syntax OK" || echo "❌ Gmail script has syntax errors"
python3 -m py_compile scripts/evolve/evolveScrape.py && echo "✅ Evolve script syntax OK" || echo "❌ Evolve script has syntax errors"  
python3 -m py_compile scripts/CSVtoAirtable/csvProcess.py && echo "✅ CSV script syntax OK" || echo "❌ CSV script has syntax errors"
python3 -m py_compile scripts/icsAirtableSync/icsProcess.py && echo "✅ ICS script syntax OK" || echo "❌ ICS script has syntax errors"

# Test 3: Node.js scripts  
echo ""
echo "3. Testing Node.js script syntax..."
node -c hcp-sync/hcp_sync.js && echo "✅ HCP script syntax OK" || echo "❌ HCP script has syntax errors"
node -c scripts/airtable-agent/airtable-agent.js && echo "✅ Web interface syntax OK" || echo "❌ Web interface has syntax errors"

# Test 4: Directories
echo ""
echo "4. Testing directory structure..."
for dir in CSV_process CSV_done logs itripcsv/downloads; do
    if [ -d "$dir" ]; then
        echo "✅ $dir directory exists"
    else
        echo "❌ $dir directory missing"
        mkdir -p "$dir"
        echo "📁 Created $dir directory"
    fi
done

# Test 5: Permissions
echo ""
echo "5. Testing script permissions..."
for script in run_complete_automation.sh scripts/gmail/gmail_downloader.py scripts/evolve/evolveScrape.py; do
    if [ -x "$script" ]; then
        echo "✅ $script is executable"
    else
        echo "❌ $script not executable"
        chmod +x "$script"
        echo "🔧 Made $script executable"
    fi
done

echo ""
echo "========================================================"
echo "🧪 Component testing complete!"
echo "Next step: Edit .env with your API keys, then run:"
echo "  ./run_complete_automation.sh"
