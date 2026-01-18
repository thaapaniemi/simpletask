#!/usr/bin/env bash
# Install git hooks for simpletask development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "Installing git hooks for simpletask..."
echo ""

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# List of hooks to install
HOOKS=("pre-commit" "commit-msg" "pre-push")
INSTALLED=0

for hook in "${HOOKS[@]}"; do
    if [ -f "$SCRIPT_DIR/$hook" ]; then
        cp "$SCRIPT_DIR/$hook" "$GIT_HOOKS_DIR/$hook"
        chmod +x "$GIT_HOOKS_DIR/$hook"
        echo -e "${GREEN}Installed $hook hook${NC}"
        INSTALLED=$((INSTALLED + 1))
    else
        echo -e "${RED}Warning: $hook not found in scripts/${NC}"
    fi
done

echo ""
echo "================================================"
echo -e "${GREEN}$INSTALLED git hooks installed successfully!${NC}"
echo "================================================"
echo ""
echo "Hooks will enforce:"
echo ""
echo "  pre-commit:"
echo "    - Version bump required when code in cli/simpletask/ changes"
echo "    - Both pyproject.toml and __init__.py must be updated"
echo ""
echo "  commit-msg:"
echo "    - Conventional Commits format required"
echo "    - Example: feat: add new feature"
echo "    - Example: fix(cli): resolve crash"
echo ""
echo "  pre-push:"
echo "    - All tests must pass before push"
echo ""
echo "To bypass hooks temporarily:"
echo "  git commit --no-verify    # Skip pre-commit and commit-msg"
echo "  git push --no-verify      # Skip pre-push"
echo ""
