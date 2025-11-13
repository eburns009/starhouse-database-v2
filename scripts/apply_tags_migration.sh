#!/bin/bash

# Script to apply the contact tags migration to Supabase
# This adds the tags TEXT[] column to the contacts table

echo "Applying contact tags migration..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

# Apply the migration
psql "$DATABASE_URL" -f /workspaces/starhouse-database-v2/supabase/migrations/20251113000001_add_contact_tags.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration applied successfully!"
    echo ""
    echo "Tags column added to contacts table."
    echo "UI will now be able to save and load contact tags."
else
    echo "❌ Migration failed!"
    exit 1
fi
