#!/bin/bash
# Setup Dependencies for Servativ Automation v2.2.22

echo "🚀 Setting up Servativ Automation Dependencies"
echo "=============================================="

# Check Node.js version
echo "📦 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+ first."
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Found Node.js: $NODE_VERSION"

# Check Python version
echo "🐍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Found Python: $PYTHON_VERSION"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    npm install
    if [ $? -eq 0 ]; then
        echo "✅ Node.js dependencies installed successfully"
    else
        echo "❌ Failed to install Node.js dependencies"
        exit 1
    fi
else
    echo "❌ package.json not found"
    exit 1
fi

# Test HCP sync scripts
echo "🧪 Testing HCP sync scripts..."
echo "Testing dev HCP sync..."
if node src/automation/scripts/hcp/dev-hcp-sync.cjs --help &>/dev/null; then
    echo "✅ Dev HCP sync script loads correctly"
else
    echo "⚠️  Dev HCP sync script may have issues (but dependencies are installed)"
fi

echo "Testing prod HCP sync..."
if node src/automation/scripts/hcp/prod-hcp-sync.cjs --help &>/dev/null; then
    echo "✅ Prod HCP sync script loads correctly"
else
    echo "⚠️  Prod HCP sync script may have issues (but dependencies are installed)"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo "💡 To avoid dependency issues in the future:"
echo "   1. Run 'npm install' whenever you see MODULE_NOT_FOUND errors"
echo "   2. This package.json will track all required Node.js dependencies"
echo "   3. Use 'npm run hcp-sync-prod' instead of direct node commands"