#!/bin/bash
# Webhook Deployment Script
# Run this script to deploy both secured webhooks to Supabase

set -e

echo "============================================"
echo "Deploying Secured Webhooks to Supabase"
echo "============================================"
echo ""

# Check if supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found"
    echo "Install it: https://supabase.com/docs/guides/cli"
    exit 1
fi

echo "✅ Supabase CLI found: $(supabase --version)"
echo ""

# Check if logged in
if ! supabase projects list &> /dev/null; then
    echo "❌ Not logged in to Supabase"
    echo "Run: supabase login"
    exit 1
fi

echo "✅ Logged in to Supabase"
echo ""

# Link to project if not already linked
PROJECT_REF="lnagadkqejnopgfxwlkb"
echo "Linking to project: $PROJECT_REF"
supabase link --project-ref $PROJECT_REF || echo "Already linked"
echo ""

# Deploy kajabi-webhook
echo "📦 Deploying kajabi-webhook..."
supabase functions deploy kajabi-webhook
echo "✅ kajabi-webhook deployed"
echo ""

# Deploy paypal-webhook
echo "📦 Deploying paypal-webhook..."
supabase functions deploy paypal-webhook
echo "✅ paypal-webhook deployed"
echo ""

# Deploy ticket-tailor-webhook
echo "📦 Deploying ticket-tailor-webhook..."
supabase functions deploy ticket-tailor-webhook
echo "✅ ticket-tailor-webhook deployed"
echo ""

echo "============================================"
echo "🎉 Deployment Complete!"
echo "============================================"
echo ""
echo "Webhook URLs:"
echo "- Kajabi: https://$PROJECT_REF.supabase.co/functions/v1/kajabi-webhook"
echo "- PayPal: https://$PROJECT_REF.supabase.co/functions/v1/paypal-webhook"
echo "- Ticket Tailor: https://$PROJECT_REF.supabase.co/functions/v1/ticket-tailor-webhook"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in Supabase dashboard"
echo "2. Test webhooks with Kajabi/PayPal dashboards"
echo "3. Monitor logs: supabase functions logs <function-name> --tail"
echo ""
