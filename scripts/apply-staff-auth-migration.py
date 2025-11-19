#!/usr/bin/env python3
"""
Apply Staff Auth Metadata Migration to Production
FAANG Standards: Safe, verified, with rollback capability
"""

import os
import psycopg2
from datetime import datetime

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:ia5Amxkf5fpf3wKU@db.lnagadkqejnopgfxwlkb.supabase.co:5432/postgres')

def main():
    print("=" * 80)
    print("STAFF AUTH METADATA MIGRATION - PRODUCTION DEPLOYMENT")
    print("=" * 80)
    print()

    # Connect to database
    print("📡 Connecting to production database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False  # Use transaction for safety
    cur = conn.cursor()

    try:
        # Step 1: Check current state
        print("\n📊 STEP 1: Checking current state of staff_users table...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'staff_users'
            ORDER BY ordinal_position;
        """)

        current_columns = cur.fetchall()
        print(f"   Current columns: {len(current_columns)}")

        # Check if migration already applied
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'staff_users'
              AND column_name IN ('last_sign_in_at', 'email_confirmed_at', 'updated_at');
        """)

        existing_new_columns = cur.fetchall()
        if len(existing_new_columns) == 3:
            print("   ⚠️  Migration already applied! Columns exist:")
            for col in existing_new_columns:
                print(f"      - {col[0]}")
            print("\n   Skipping migration (idempotent).")
            conn.rollback()
            return
        elif len(existing_new_columns) > 0:
            print(f"   ⚠️  Partial migration detected! {len(existing_new_columns)}/3 columns exist")
            print("   Continuing with migration (idempotent)...")

        # Step 2: Read migration file
        print("\n📄 STEP 2: Reading migration file...")
        migration_path = '/workspaces/starhouse-database-v2/supabase/migrations/20251119000001_add_staff_auth_metadata.sql'

        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        print(f"   Migration file loaded: {len(migration_sql)} characters")

        # Step 3: Apply migration
        print("\n🚀 STEP 3: Applying migration...")
        print("   (This may take 10-30 seconds...)")

        cur.execute(migration_sql)

        # Step 4: Verify migration
        print("\n✅ STEP 4: Verifying migration...")

        # Check columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'staff_users'
              AND column_name IN ('last_sign_in_at', 'email_confirmed_at', 'updated_at');
        """)

        new_columns = cur.fetchall()
        print(f"   ✅ Columns added: {len(new_columns)}/3")
        for col in new_columns:
            print(f"      - {col[0]} ({col[1]}, nullable={col[2]})")

        # Check trigger
        cur.execute("""
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema = 'auth'
              AND event_object_table = 'users'
              AND trigger_name = 'sync_staff_auth_metadata_trigger';
        """)

        trigger = cur.fetchone()
        if trigger:
            print(f"   ✅ Trigger created: {trigger[0]}")
        else:
            print("   ❌ Trigger NOT found!")
            raise Exception("Trigger creation failed")

        # Check index
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'staff_users'
              AND indexname = 'idx_staff_users_last_sign_in';
        """)

        index = cur.fetchone()
        if index:
            print(f"   ✅ Index created: {index[0]}")
        else:
            print("   ❌ Index NOT found!")
            raise Exception("Index creation failed")

        # Check backfill
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(last_sign_in_at) as with_sign_in_data,
                COUNT(email_confirmed_at) as with_email_confirmed,
                COUNT(updated_at) as with_updated_at
            FROM staff_users;
        """)

        backfill_stats = cur.fetchone()
        print(f"\n   📊 Backfill results:")
        print(f"      Total staff: {backfill_stats[0]}")
        print(f"      With last_sign_in_at: {backfill_stats[1]}")
        print(f"      With email_confirmed_at: {backfill_stats[2]}")
        print(f"      With updated_at: {backfill_stats[3]}")

        if backfill_stats[3] != backfill_stats[0]:
            print(f"      ⚠️  Not all staff have updated_at! Expected {backfill_stats[0]}, got {backfill_stats[3]}")

        # Step 5: Commit transaction
        print("\n💾 STEP 5: Committing transaction...")
        conn.commit()
        print("   ✅ Migration committed to database")

        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("📊 Next steps:")
        print("   1. Test trigger functionality (sign in as staff user)")
        print("   2. Verify auth metadata syncs correctly")
        print("   3. Update UI to display new columns")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("🔄 Rolling back transaction...")
        conn.rollback()
        print("   ✅ Rollback complete - database unchanged")
        raise

    finally:
        cur.close()
        conn.close()
        print("📡 Database connection closed")

if __name__ == '__main__':
    main()
