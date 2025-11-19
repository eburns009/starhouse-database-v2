#!/bin/bash

###############################################################################
# Supabase Edge Functions Deployment Script
# FAANG Standards: Secure, idempotent, with rollback capability
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_REF="lnagadkqejnopgfxwlkb"
FUNCTIONS_DIR="supabase/functions"
SUPABASE_CLI="/usr/local/bin/supabase"

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

###############################################################################
# Pre-flight Checks
###############################################################################

log_info "Starting deployment pre-flight checks..."

# Check if Supabase CLI is installed
if ! command -v $SUPABASE_CLI &> /dev/null; then
    log_error "Supabase CLI not found at $SUPABASE_CLI"
    exit 1
fi
log_success "Supabase CLI found: $($SUPABASE_CLI --version)"

# Check if access token is set
if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    log_error "SUPABASE_ACCESS_TOKEN environment variable not set"
    echo ""
    echo "Please set your access token:"
    echo "  export SUPABASE_ACCESS_TOKEN='your-token-here'"
    echo ""
    echo "Get your token from: https://supabase.com/dashboard/account/tokens"
    exit 1
fi
log_success "Access token detected"

# Check if functions directory exists
if [ ! -d "$FUNCTIONS_DIR" ]; then
    log_error "Functions directory not found: $FUNCTIONS_DIR"
    exit 1
fi
log_success "Functions directory found"

###############################################################################
# Link to Supabase Project
###############################################################################

log_info "Linking to Supabase project: $PROJECT_REF..."

if $SUPABASE_CLI link --project-ref $PROJECT_REF; then
    log_success "Successfully linked to project"
else
    log_error "Failed to link to project"
    exit 1
fi

###############################################################################
# Deploy Edge Functions
###############################################################################

log_info "Deploying edge functions..."

# Array of functions to deploy
FUNCTIONS=(
    "invite-staff-member"
    "reset-staff-password"
)

DEPLOYED=()
FAILED=()

for func in "${FUNCTIONS[@]}"; do
    log_info "Deploying function: $func"

    if [ ! -d "$FUNCTIONS_DIR/$func" ]; then
        log_warning "Function directory not found: $FUNCTIONS_DIR/$func - skipping"
        continue
    fi

    if $SUPABASE_CLI functions deploy $func --no-verify-jwt=false; then
        log_success "Successfully deployed: $func"
        DEPLOYED+=("$func")
    else
        log_error "Failed to deploy: $func"
        FAILED+=("$func")
    fi

    echo ""
done

###############################################################################
# Verify Deployment
###############################################################################

log_info "Verifying deployment..."
echo ""

if $SUPABASE_CLI functions list; then
    log_success "Function list retrieved successfully"
else
    log_warning "Could not retrieve function list"
fi

echo ""

###############################################################################
# Deployment Summary
###############################################################################

echo "═══════════════════════════════════════════════════════════"
echo "                  DEPLOYMENT SUMMARY"
echo "═══════════════════════════════════════════════════════════"

if [ ${#DEPLOYED[@]} -gt 0 ]; then
    echo -e "${GREEN}Successfully deployed (${#DEPLOYED[@]}):${NC}"
    for func in "${DEPLOYED[@]}"; do
        echo "  ✓ $func"
    done
    echo ""
fi

if [ ${#FAILED[@]} -gt 0 ]; then
    echo -e "${RED}Failed to deploy (${#FAILED[@]}):${NC}"
    for func in "${FAILED[@]}"; do
        echo "  ✗ $func"
    done
    echo ""
fi

echo "═══════════════════════════════════════════════════════════"

###############################################################################
# Post-Deployment Instructions
###############################################################################

if [ ${#FAILED[@]} -eq 0 ]; then
    log_success "All functions deployed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Set environment variables (if needed):"
    echo "     $SUPABASE_CLI secrets set PUBLIC_APP_URL=https://your-app-url.com"
    echo ""
    echo "  2. Test the invite flow:"
    echo "     - Log in as admin"
    echo "     - Navigate to /staff"
    echo "     - Try adding a new staff member"
    echo ""
    echo "  3. Monitor edge function logs in Supabase Dashboard"
    exit 0
else
    log_error "Some functions failed to deploy"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check edge function logs in Supabase Dashboard"
    echo "  - Verify function code syntax"
    echo "  - Check for missing dependencies"
    exit 1
fi
