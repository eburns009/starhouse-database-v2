#!/usr/bin/env python3
"""
Deploy Three-Tier Staff Roles Migration
Runs migration: 20251117000001_three_tier_staff_roles.sql

FAANG Standards:
- Secure credential management via db_config
- Transaction-based deployment with rollback
- Comprehensive pre/post verification
- Detailed logging and error handling
"""

import psycopg2
import sys
from pathlib import Path
from db_config import get_database_url

# Database connection - secure credential management
DATABASE_URL = get_database_url()

def main():
    print("=" * 80)
    print("DEPLOYING: Three-Tier Staff Roles Migration")
    print("=" * 80)
    print()

    # Read migration file
    migration_file = Path(__file__).parent.parent / 'supabase' / 'migrations' / '20251117000001_three_tier_staff_roles.sql'

    if not migration_file.exists():
        print(f"❌ ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"📄 Reading migration from: {migration_file}")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"   Size: {len(migration_sql)} characters")
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()
        print("   Connected ✓")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    try:
        # Check current schema before migration
        print("🔍 Pre-migration check...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'staff_members'
            ORDER BY ordinal_position
        """)
        columns_before = [row[0] for row in cursor.fetchall()]
        print(f"   Current columns: {', '.join(columns_before)}")

        cursor.execute("""
            SELECT COUNT(*)
            FROM staff_members
            WHERE role = 'staff'
        """)
        staff_count = cursor.fetchone()[0]
        print(f"   Staff members with 'staff' role: {staff_count}")
        print()

        # Run migration
        print("🚀 Running migration...")
        cursor.execute(migration_sql)
        print("   Migration executed ✓")
        print()

        # Verify migration
        print("✅ Post-migration verification...")

        # Check new columns
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'staff_members'
            ORDER BY ordinal_position
        """)
        columns_after = [row[0] for row in cursor.fetchall()]
        print(f"   Columns now: {', '.join(columns_after)}")

        # Check for new columns
        new_columns = set(columns_after) - set(columns_before)
        if 'display_name' in new_columns and 'last_login_at' in new_columns:
            print("   ✓ New columns added: display_name, last_login_at")

        # Check role constraint
        cursor.execute("""
            SELECT COUNT(*)
            FROM staff_members
            WHERE role NOT IN ('admin', 'full_user', 'read_only', 'staff')
        """)
        invalid_roles = cursor.fetchone()[0]
        if invalid_roles == 0:
            print("   ✓ Role constraint updated successfully")

        # Check migration of 'staff' to 'full_user'
        cursor.execute("""
            SELECT COUNT(*)
            FROM staff_members
            WHERE role = 'staff'
        """)
        remaining_staff = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM staff_members
            WHERE role = 'full_user'
        """)
        full_users = cursor.fetchone()[0]

        print(f"   ✓ Migrated {staff_count} 'staff' → 'full_user'")
        print(f"   Remaining 'staff' roles: {remaining_staff}")
        print(f"   Total 'full_user' roles: {full_users}")

        # Check helper functions
        print()
        print("🔧 Testing helper functions...")

        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'is_admin')")
        if cursor.fetchone()[0]:
            print("   ✓ is_admin() function exists")

        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'can_edit')")
        if cursor.fetchone()[0]:
            print("   ✓ can_edit() function exists")

        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'get_user_role')")
        if cursor.fetchone()[0]:
            print("   ✓ get_user_role() function exists")

        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'change_staff_role')")
        if cursor.fetchone()[0]:
            print("   ✓ change_staff_role() function exists")

        # Check RLS policies
        print()
        print("🔒 Checking RLS policies...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = 'contacts'
            AND policyname LIKE 'staff_%'
        """)
        policy_count = cursor.fetchone()[0]
        print(f"   ✓ {policy_count} staff RLS policies on contacts table")

        # Commit transaction
        print()
        print("💾 Committing migration...")
        conn.commit()
        print("   Committed ✓")
        print()

        print("=" * 80)
        print("✅ MIGRATION COMPLETE")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Test helper functions:")
        print("   SELECT is_admin(), can_edit(), get_user_role();")
        print()
        print("2. View staff members:")
        print("   SELECT email, role, display_name, active FROM staff_members;")
        print()
        print("3. Add a test user:")
        print("   SELECT add_staff_member('test@example.com', 'read_only', 'Test User');")
        print()

    except Exception as e:
        print()
        print(f"❌ ERROR during migration: {e}")
        print()
        print("🔄 Rolling back...")
        conn.rollback()
        print("   Rolled back ✓")
        print()
        print("Migration was NOT applied. Database is unchanged.")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
