#!/bin/bash
# Run all tests for the NutriMatch project

set -e

echo "=========================================="
echo "Running All Tests - NutriMatch"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Backend tests
echo -e "${YELLOW}[1/3] Running backend tests...${NC}"
cd "$(dirname "$0")/../backend"
if pytest -q; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    FAILED=1
fi
echo ""

# Bot tests
echo -e "${YELLOW}[2/3] Running bot tests...${NC}"
cd "$(dirname "$0")/.."
cd apps/telegram_bot
if pytest -q; then
    echo -e "${GREEN}✓ Bot tests passed${NC}"
else
    echo -e "${RED}✗ Bot tests failed${NC}"
    FAILED=1
fi
echo ""

# Admin panel tests
echo -e "${YELLOW}[3/3] Running admin panel tests...${NC}"
cd "$(dirname "$0")/../apps/admin_panel"
if npm run test:run 2>&1; then
    echo -e "${GREEN}✓ Admin panel tests passed${NC}"
else
    echo -e "${RED}✗ Admin panel tests failed${NC}"
    FAILED=1
fi
echo ""

# Summary
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
