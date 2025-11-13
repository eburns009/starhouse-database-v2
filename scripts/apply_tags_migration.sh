#!/bin/bash

# Script to apply the contact tags migrations to Supabase
# This adds the tags TEXT[] column and atomic operation functions

echo "========================================="
echo "Applying Contact Tags Migrations"
echo "========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

MIGRATION_DIR="/workspaces/starhouse-database-v2/supabase/migrations"

# Migration 1: Add tags column
echo ""
echo "Step 1/2: Adding tags column to contacts table..."
psql "$DATABASE_URL" -f "$MIGRATION_DIR/20251113000001_add_contact_tags.sql"

if [ $? -ne 0 ]; then
    echo "❌ Migration 1 failed!"
    exit 1
fi
echo "✅ Tags column added successfully"

# Migration 2: Add atomic tag functions
echo ""
echo "Step 2/2: Creating atomic tag operation functions..."
psql "$DATABASE_URL" -f "$MIGRATION_DIR/20251113000002_add_atomic_tag_functions.sql"

if [ $? -ne 0 ]; then
    echo "❌ Migration 2 failed!"
    exit 1
fi
echo "✅ Atomic tag functions created successfully"

echo ""
echo "========================================="
echo "✅ All migrations completed successfully!"
echo "========================================="
echo ""
echo "Available functions:"
echo "  - add_contact_tag(contact_id, tag)"
echo "  - remove_contact_tag(contact_id, tag)"
echo "  - bulk_add_contact_tags(contact_id, tags[])"
echo ""
echo "Features enabled:"
echo "  ✅ Race-condition-free tag operations"
echo "  ✅ Automatic duplicate prevention"
echo "  ✅ Case-insensitive tag storage"
echo "  ✅ Tag validation (max 50 chars)"
echo "  ✅ GIN index for fast tag queries"
echo ""
echo "Test query performance:"
echo "  EXPLAIN ANALYZE SELECT * FROM contacts WHERE 'vip' = ANY(tags);"
echo ""
