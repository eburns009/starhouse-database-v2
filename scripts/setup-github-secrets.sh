#!/bin/bash

###############################################################################
# GitHub Secrets Setup Script
# FAANG Standards: Interactive, secure, with validation
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

###############################################################################
# Banner
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${CYAN}    GitHub Secrets Setup for Automated Deployments${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

###############################################################################
# Prerequisites Check
###############################################################################

echo -e "${BLUE}ℹ${NC} Checking prerequisites..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗${NC} GitHub CLI (gh) not found"
    echo ""
    echo "Please install GitHub CLI:"
    echo "  https://cli.github.com/"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} GitHub CLI found: $(gh --version | head -1)"

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Not authenticated with GitHub"
    echo ""
    echo "Please authenticate:"
    echo "  gh auth login"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Authenticated with GitHub"
echo ""

###############################################################################
# Collect Information
###############################################################################

echo "═══════════════════════════════════════════════════════════════"
echo "                    Secret Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# SUPABASE_PROJECT_ID (pre-filled)
PROJECT_ID="lnagadkqejnopgfxwlkb"
echo -e "${CYAN}1. SUPABASE_PROJECT_ID${NC}"
echo "   Value: $PROJECT_ID"
echo "   (Auto-detected from your Supabase configuration)"
echo ""

# SUPABASE_ACCESS_TOKEN (user input)
echo -e "${CYAN}2. SUPABASE_ACCESS_TOKEN${NC}"
echo "   Get your token from: ${BLUE}https://supabase.com/dashboard/account/tokens${NC}"
echo ""
echo -e "${YELLOW}⚠${NC}  This token grants full access to your Supabase project"
echo -e "${YELLOW}⚠${NC}  It will be stored securely in GitHub Secrets (encrypted)"
echo -e "${YELLOW}⚠${NC}  Never commit this token to git or share it publicly"
echo ""

# Read token securely (hidden input)
read -sp "   Enter your Supabase Access Token: " ACCESS_TOKEN
echo ""
echo ""

# Validate token is not empty
if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}✗${NC} Access token cannot be empty"
    exit 1
fi

# Validate token format (basic check)
if [[ ! $ACCESS_TOKEN =~ ^sbp_ ]]; then
    echo -e "${YELLOW}⚠${NC} Warning: Token doesn't start with 'sbp_' - this might be incorrect"
    read -p "   Continue anyway? (y/N): " CONTINUE
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

###############################################################################
# Confirmation
###############################################################################

echo "═══════════════════════════════════════════════════════════════"
echo "                    Confirmation"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "The following secrets will be set in your GitHub repository:"
echo ""
echo -e "  ${CYAN}SUPABASE_PROJECT_ID${NC}    = $PROJECT_ID"
echo -e "  ${CYAN}SUPABASE_ACCESS_TOKEN${NC}  = ${GREEN}***configured***${NC}"
echo ""
read -p "Proceed with setting these secrets? (y/N): " CONFIRM

if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

###############################################################################
# Set Secrets
###############################################################################

echo -e "${BLUE}ℹ${NC} Setting GitHub secrets..."
echo ""

# Set SUPABASE_PROJECT_ID
echo "Setting SUPABASE_PROJECT_ID..."
if echo "$PROJECT_ID" | gh secret set SUPABASE_PROJECT_ID; then
    echo -e "${GREEN}✓${NC} SUPABASE_PROJECT_ID configured"
else
    echo -e "${RED}✗${NC} Failed to set SUPABASE_PROJECT_ID"
    exit 1
fi

# Set SUPABASE_ACCESS_TOKEN
echo "Setting SUPABASE_ACCESS_TOKEN..."
if echo "$ACCESS_TOKEN" | gh secret set SUPABASE_ACCESS_TOKEN; then
    echo -e "${GREEN}✓${NC} SUPABASE_ACCESS_TOKEN configured"
else
    echo -e "${RED}✗${NC} Failed to set SUPABASE_ACCESS_TOKEN"
    exit 1
fi

echo ""

###############################################################################
# Verify
###############################################################################

echo -e "${BLUE}ℹ${NC} Verifying configuration..."
echo ""

if gh secret list | grep -q "SUPABASE_PROJECT_ID"; then
    echo -e "${GREEN}✓${NC} SUPABASE_PROJECT_ID is set"
else
    echo -e "${YELLOW}⚠${NC} SUPABASE_PROJECT_ID verification failed"
fi

if gh secret list | grep -q "SUPABASE_ACCESS_TOKEN"; then
    echo -e "${GREEN}✓${NC} SUPABASE_ACCESS_TOKEN is set"
else
    echo -e "${YELLOW}⚠${NC} SUPABASE_ACCESS_TOKEN verification failed"
fi

echo ""

###############################################################################
# Success
###############################################################################

echo "═══════════════════════════════════════════════════════════════"
echo -e "               ${GREEN}✓ Setup Complete!${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "  1. ${CYAN}Test Manual Deployment${NC}"
echo "     Go to: GitHub → Actions → Deploy Supabase Edge Functions → Run workflow"
echo ""
echo "  2. ${CYAN}Automatic Deployments${NC}"
echo "     Any push to 'main' with changes in 'supabase/functions/**' will auto-deploy"
echo ""
echo "  3. ${CYAN}Monitor Deployments${NC}"
echo "     View logs: GitHub → Actions tab"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Clear sensitive variables
unset ACCESS_TOKEN
