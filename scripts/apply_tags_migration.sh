#!/bin/bash

# Script to apply contact tags and security migrations to Supabase
# IMPORTANT: Edit migration 20251113000004 with YOUR email before running!

echo "========================================="
echo "StarHouse CRM - Secure Setup"
echo "========================================="
echo ""
echo "⚠️  STOP! Before continuing:"
echo "   1. Edit supabase/migrations/20251113000004_secure_staff_access_control.sql"
echo "   2. Replace 'your.email@thestarhouse.org' with YOUR actual email (line ~50)"
echo "   3. This is critical - you'll lock yourself out otherwise!"
echo ""
read -p "Have you updated your email in the migration? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted. Please update your email first."
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

MIGRATION_DIR="/workspaces/starhouse-database-v2/supabase/migrations"

# Migration 1: Add tags column
echo ""
echo "Step 1/3: Adding tags column to contacts table..."
psql "$DATABASE_URL" -f "$MIGRATION_DIR/20251113000001_add_contact_tags.sql"

if [ $? -ne 0 ]; then
    echo "❌ Migration 1 failed!"
    exit 1
fi
echo "✅ Tags column added successfully"

# Migration 2: Add atomic tag functions
echo ""
echo "Step 2/3: Creating atomic tag operation functions..."
psql "$DATABASE_URL" -f "$MIGRATION_DIR/20251113000002_add_atomic_tag_functions.sql"

if [ $? -ne 0 ]; then
    echo "❌ Migration 2 failed!"
    exit 1
fi
echo "✅ Atomic tag functions created successfully"

# Migration 3: DEPRECATED - Skip old insecure RLS policies
echo ""
echo "Step 3/4: Skipping deprecated migration (20251113000003)..."
echo "⏭️  Using secure staff access control instead"

# Migration 4: Add secure staff access control
echo ""
echo "Step 4/4: Setting up secure staff access control..."
echo "   - Creating staff_members allowlist table"
echo "   - Adding role-based permissions (admin/staff)"
echo "   - Implementing proper RLS verification"
echo "   - Adding audit trail to contacts"
psql "$DATABASE_URL" -f "$MIGRATION_DIR/20251113000004_secure_staff_access_control.sql"

if [ $? -ne 0 ]; then
    echo "❌ Migration 4 failed!"
    echo "   Check that you updated your email in the migration file"
    exit 1
fi
echo "✅ Secure staff access control configured successfully"

echo ""
echo "========================================="
echo "✅ All migrations completed successfully!"
echo "========================================="
echo ""
echo "🔐 Security Model:"
echo "  - Allowlist-based (staff_members table)"
echo "  - Role-based (admin/staff permissions)"
echo "  - Audit trail (created_by, updated_by tracking)"
echo ""
echo "👥 Staff Management Functions:"
echo "  - add_staff_member(email, role, notes)    -- Admins only"
echo "  - deactivate_staff_member(email)          -- Admins only"
echo "  - promote_to_admin(email)                 -- Admins only"
echo "  - is_verified_staff()                     -- Check current user"
echo ""
echo "🏷️  Tag Management Functions:"
echo "  - add_contact_tag(contact_id, tag)"
echo "  - remove_contact_tag(contact_id, tag)"
echo "  - bulk_add_contact_tags(contact_id, tags[])"
echo ""
echo "✅ Features enabled:"
echo "  ✅ Secure staff access control (allowlist-based)"
echo "  ✅ Admin role can manage staff members"
echo "  ✅ Audit trail for all contact modifications"
echo "  ✅ Race-condition-free tag operations"
echo "  ✅ Tag validation (max 50 chars, max 50 tags/contact)"
echo "  ✅ Automatic duplicate prevention"
echo "  ✅ Case-insensitive tag storage"
echo "  ✅ GIN index for fast tag queries"
echo ""
echo "⚠️  NEXT STEPS:"
echo "  1. Verify you can log in and access contacts"
echo "  2. Check: SELECT * FROM staff_members WHERE role = 'admin';"
echo "  3. Add other staff: SELECT add_staff_member('email', 'staff', 'notes');"
echo "  4. Test tags functionality in UI"
echo ""
echo "📖 Full documentation:"
echo "   docs/SECURE_STAFF_SETUP_GUIDE.md"
echo ""
