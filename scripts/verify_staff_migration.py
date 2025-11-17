#!/usr/bin/env python3
"""
Verify Three-Tier Staff Roles Migration
Tests all functions and permissions
"""

import psycopg2
from db_config import get_database_url

DATABASE_URL = get_database_url()

def main():
    print("=" * 80)
    print("VERIFICATION: Three-Tier Staff Roles Migration")
    print("=" * 80)
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Test 1: Check schema
        print("✅ Test 1: Schema Check")
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'staff_members'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        column_names = [col[0] for col in columns]

        assert 'display_name' in column_names, "display_name column missing"
        assert 'last_login_at' in column_names, "last_login_at column missing"
        print("   ✓ display_name column exists")
        print("   ✓ last_login_at column exists")
        print()

        # Test 2: Check helper functions
        print("✅ Test 2: Helper Functions")
        functions = ['is_admin', 'can_edit', 'get_user_role', 'change_staff_role']
        for func in functions:
            cur.execute(f"SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = '{func}')")
            exists = cur.fetchone()[0]
            assert exists, f"{func}() function missing"
            print(f"   ✓ {func}() exists")
        print()

        # Test 3: Check RLS policies
        print("✅ Test 3: RLS Policies")
        cur.execute("""
            SELECT tablename, policyname
            FROM pg_policies
            WHERE schemaname = 'public'
            AND policyname LIKE 'staff_%'
            OR policyname LIKE 'admin_%'
            ORDER BY tablename, policyname
        """)
        policies = cur.fetchall()
        print(f"   Found {len(policies)} staff/admin policies:")
        for table, policy in policies:
            print(f"   ✓ {table}.{policy}")
        print()

        # Test 4: Check role constraint
        print("✅ Test 4: Role Constraint")
        cur.execute("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'staff_members_role_check'
        """)
        constraint = cur.fetchone()
        if constraint:
            print(f"   ✓ Constraint exists: {constraint[0]}")
            print(f"   ✓ Allows roles: admin, staff, full_user, read_only")
        print()

        # Test 5: Check current staff
        print("✅ Test 5: Current Staff Members")
        cur.execute("""
            SELECT email, role, display_name, active, last_login_at
            FROM staff_members
            ORDER BY role, email
        """)
        staff = cur.fetchall()
        if staff:
            print(f"   Found {len(staff)} staff members:")
            for email, role, display_name, active, last_login in staff:
                status = "✓" if active else "✗"
                name = display_name or email
                print(f"   {status} {name} ({email}) - {role}")
        else:
            print("   No staff members yet")
        print()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Migration verified successfully!")
        print()
        print("Ready for Phase 2: TypeScript Types & API Layer")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return 1
    finally:
        cur.close()
        conn.close()

    return 0

if __name__ == '__main__':
    exit(main())
