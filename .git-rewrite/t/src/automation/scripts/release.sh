#!/bin/bash
# Release script for property management automation
# Usage: ./scripts/release.sh [patch|minor|major] "Release description"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the automation directory
if [ ! -f "VERSION" ]; then
    echo -e "${RED}Error: VERSION file not found. Run from automation root directory.${NC}"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(cat VERSION)
echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Parse version type
VERSION_TYPE=${1:-patch}
DESCRIPTION=${2:-"Release update"}

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(patch|minor|major)$ ]]; then
    echo -e "${RED}Error: Version type must be patch, minor, or major${NC}"
    exit 1
fi

# Calculate new version
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

case $VERSION_TYPE in
    "major")
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    "minor")
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    "patch")
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Confirm release
echo -e "${YELLOW}Release description: ${DESCRIPTION}${NC}"
read -p "Continue with release? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Release cancelled."
    exit 1
fi

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Update README
sed -i "s/\*\*Version [0-9]\+\.[0-9]\+\.[0-9]\+\*\*/\*\*Version $NEW_VERSION\*\*/" README.md

# Get current date
RELEASE_DATE=$(date +%Y-%m-%d)

# Add to CHANGELOG
sed -i "4i\\
\\
## [$NEW_VERSION] - $RELEASE_DATE\\
\\
### Changed\\
- $DESCRIPTION\\
" CHANGELOG.md

# Stage changes
git add VERSION README.md CHANGELOG.md

# Commit
git commit -m "Release v${NEW_VERSION}: ${DESCRIPTION}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Create tag
git tag -a "v${NEW_VERSION}" -m "Version ${NEW_VERSION}: ${DESCRIPTION}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin dev
git push origin "v${NEW_VERSION}"

echo -e "${GREEN}✅ Successfully released version ${NEW_VERSION}!${NC}"
echo -e "${YELLOW}📝 Don't forget to update the changelog with detailed changes${NC}"