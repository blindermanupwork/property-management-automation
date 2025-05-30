#!/bin/bash
# Simple version display script

if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
    echo "Property Management Automation v${VERSION}"
    
    # Show git info if available
    if git rev-parse --git-dir > /dev/null 2>&1; then
        BRANCH=$(git branch --show-current)
        COMMIT=$(git rev-parse --short HEAD)
        echo "Branch: ${BRANCH}"
        echo "Commit: ${COMMIT}"
        
        # Check if there are uncommitted changes
        if ! git diff-index --quiet HEAD --; then
            echo "Status: Modified (uncommitted changes)"
        else
            echo "Status: Clean"
        fi
    fi
else
    echo "VERSION file not found"
    exit 1
fi