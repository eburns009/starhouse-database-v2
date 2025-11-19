#!/usr/bin/env python3
"""
Verify Staff Auth Metadata Trigger Synchronization
Tests that trigger correctly syncs auth.users to staff_users
"""

import os
import psycopg2
from datetime import datetime
import json

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:ia5Amxkf5fpf3wKU@db.lnagadkqejnopgfxwlkb.supabase.co:5432/postgres')

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def print_table(headers, rows):
    """Print formatted table"""
    if not rows:
        print("   (No data)")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val) if val else 'NULL'))

    # Print header
    header_line = "   " + " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("   " + "-" * (len(header_line) - 3))

    # Print rows
    for row in rows:
        formatted_row = []
        for val, width in zip(row, widths):
            if val is None:
                formatted_row.append('NULL'.ljust(width))
            elif isinstance(val, datetime):
                formatted_row.append(val.strftime('%Y-%m-%d %H:%M:%S').ljust(width))
            else:
                formatted_row.append(str(val).ljust(width))
        print("   " + " | ".join(formatted_row))

def main():
    print_header("STAFF AUTH METADATA SYNC VERIFICATION")
    print()
    print("This script verifies that auth metadata is syncing correctly")
    print("from auth.users to staff_users table via trigger.")
    print()

    # Connect to database
    print("📡 Connecting to production database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Step 1: Current state of all staff
        print_header("STEP 1: Current State - All Staff Users")

        cur.execute("""
            SELECT
                id,
                email,
                last_sign_in_at,
                email_confirmed_at,
                updated_at,
                created_at
            FROM staff_users
            ORDER BY email;
        """)

        staff_data = cur.fetchall()
        headers = ['ID', 'Email', 'Last Sign In', 'Email Confirmed', 'Updated At', 'Created At']
        print_table(headers, staff_data)

        # Step 2: Save current state for comparison
        print_header("STEP 2: Saving Current State for Comparison")

        # Save to file
        state_file = '/tmp/staff_auth_before_signin.json'
        state_data = []
        for row in staff_data:
            state_data.append({
                'id': str(row[0]),
                'email': row[1],
                'last_sign_in_at': row[2].isoformat() if row[2] else None,
                'email_confirmed_at': row[3].isoformat() if row[3] else None,
                'updated_at': row[4].isoformat() if row[4] else None,
                'created_at': row[5].isoformat() if row[5] else None,
            })

        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

        print(f"   ✅ State saved to: {state_file}")
        print(f"   📊 Total staff users: {len(staff_data)}")

        # Step 3: Cross-check with auth.users
        print_header("STEP 3: Cross-Check with auth.users")

        cur.execute("""
            SELECT
                au.email,
                au.last_sign_in_at as auth_last_sign_in,
                su.last_sign_in_at as staff_last_sign_in,
                au.email_confirmed_at as auth_confirmed,
                su.email_confirmed_at as staff_confirmed,
                CASE
                    WHEN au.last_sign_in_at IS NOT DISTINCT FROM su.last_sign_in_at
                     AND au.email_confirmed_at IS NOT DISTINCT FROM su.email_confirmed_at
                    THEN '✅ SYNCED'
                    ELSE '❌ OUT OF SYNC'
                END as sync_status
            FROM auth.users au
            JOIN staff_users su ON au.id = su.id
            ORDER BY au.email;
        """)

        sync_data = cur.fetchall()
        headers = ['Email', 'Auth Last Sign In', 'Staff Last Sign In', 'Auth Confirmed', 'Staff Confirmed', 'Status']
        print_table(headers, sync_data)

        # Count sync status
        synced_count = sum(1 for row in sync_data if '✅' in row[5])
        total_count = len(sync_data)

        print()
        print(f"   📊 Sync Status: {synced_count}/{total_count} staff users in sync")

        if synced_count < total_count:
            print(f"   ⚠️  {total_count - synced_count} users are OUT OF SYNC")
            print("   💡 This is expected if the trigger hasn't fired yet (no sign-ins since migration)")
        else:
            print("   ✅ All users are in sync!")

        # Step 4: Trigger diagnostics
        print_header("STEP 4: Trigger Diagnostics")

        cur.execute("""
            SELECT
                trigger_name,
                event_manipulation,
                event_object_table,
                action_timing
            FROM information_schema.triggers
            WHERE trigger_schema = 'auth'
              AND event_object_table = 'users'
              AND trigger_name = 'sync_staff_auth_metadata_trigger';
        """)

        trigger_info = cur.fetchone()
        if trigger_info:
            print(f"   ✅ Trigger exists: {trigger_info[0]}")
            print(f"      Event: {trigger_info[1]} on {trigger_info[2]}")
            print(f"      Timing: {trigger_info[3]}")
        else:
            print("   ❌ Trigger NOT found!")

        # Step 5: Function diagnostics
        cur.execute("""
            SELECT
                routine_name,
                security_type
            FROM information_schema.routines
            WHERE routine_schema = 'public'
              AND routine_name = 'sync_staff_auth_metadata';
        """)

        function_info = cur.fetchone()
        if function_info:
            print(f"   ✅ Function exists: {function_info[0]}")
            print(f"      Security: {function_info[1]}")
        else:
            print("   ❌ Function NOT found!")

        # Step 6: Instructions for testing
        print_header("STEP 6: Testing Instructions")
        print()
        print("To test the trigger:")
        print()
        print("1. Go to: https://starhouse-database-v2.vercel.app/login")
        print("2. Sign in with your staff account")
        print("3. Wait 10 seconds for trigger to fire")
        print("4. Run this script again to see updated data")
        print()
        print("Then run:")
        print("   python3 scripts/verify-trigger-sync.py --after-signin")
        print()

        # Save before-state summary
        print_header("Summary Saved")
        print()
        print(f"   Before-state saved to: {state_file}")
        print(f"   Total staff users: {len(staff_data)}")
        print(f"   Currently synced: {synced_count}/{total_count}")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise

    finally:
        cur.close()
        conn.close()
        print("📡 Database connection closed")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--after-signin':
        print("\n🔄 Comparing AFTER sign-in state...\n")

        # Load before state
        state_file = '/tmp/staff_auth_before_signin.json'
        try:
            with open(state_file, 'r') as f:
                before_state = json.load(f)

            print(f"   ✅ Loaded before-state: {len(before_state)} users")
        except FileNotFoundError:
            print(f"   ❌ Before-state file not found: {state_file}")
            print("   💡 Run this script without --after-signin first")
            sys.exit(1)

        # Run verification again
        main()

        # TODO: Compare before/after states
        print_header("Comparison Analysis")
        print("   (Comparison logic would go here)")
    else:
        main()
