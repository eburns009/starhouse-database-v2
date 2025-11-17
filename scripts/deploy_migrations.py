#!/usr/bin/env python3
"""
Deploy all pending Supabase migrations to production database
"""

import os
import psycopg2
from datetime import datetime
from db_config import get_database_url

DATABASE_URL = get_database_url()

# List of migrations to deploy (in order)
MIGRATIONS = [
    '20251101000000_add_transaction_source_system.sql',
    '20251101000001_proper_transaction_provenance.sql',
    '20251102000001_contact_module_schema.sql',
    '20251102000002_contact_module_views.sql',
    '20251102000003_contact_module_functions.sql',
    '20251102000004_contact_module_migration.sql',
    '20251102000005_fix_function_types.sql',
    '20251113000001_add_contact_tags.sql',
    '20251113000002_add_atomic_tag_functions.sql',
    '20251113000003_staff_rls_policies.sql',
    '20251113000004_secure_staff_access_control.sql',
    '20251113000005_secure_financial_tables_rls.sql',
    '20251113000006_simplify_staff_access.sql',
    '20251114000000_mailing_list_priority_system.sql',
    '20251114000001_protect_mailing_list.sql',
    '20251114000002_fix_address_scoring_critical_bugs.sql',
    '20251115000003_add_address_validation_fields.sql',
    '20251115000004_add_ncoa_performance_index.sql',
    '20251115000005_validation_first_scoring.sql',
]

MIGRATIONS_DIR = './supabase/migrations'


def get_applied_migrations(cursor):
    """Get list of already applied migrations."""
    cursor.execute("""
        SELECT version FROM supabase_migrations.schema_migrations
    """)
    return {row[0] for row in cursor.fetchall()}


def extract_version(filename):
    """Extract version number from migration filename."""
    return filename.split('_')[0]


def apply_migration(cursor, filepath, filename):
    """Apply a single migration file."""
    version = extract_version(filename)
    name = filename.replace('.sql', '')

    print(f"\n{'='*80}")
    print(f"Applying: {filename}")
    print(f"Version: {version}")
    print(f"{'='*80}")

    # Read migration file
    with open(filepath, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    try:
        # Execute migration
        cursor.execute(migration_sql)

        # Record in schema_migrations table
        cursor.execute("""
            INSERT INTO supabase_migrations.schema_migrations (version, name, applied_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (version) DO NOTHING
        """, (version, name))

        print(f"✅ SUCCESS: {filename}")
        return True

    except Exception as e:
        print(f"❌ FAILED: {filename}")
        print(f"Error: {e}")
        raise


def main():
    print("=" * 80)
    print("SUPABASE MIGRATION DEPLOYMENT")
    print("=" * 80)
    print(f"Database: Supabase Production")
    print(f"Migrations to deploy: {len(MIGRATIONS)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False  # Use transactions
    cursor = conn.cursor()

    try:
        # Get already applied migrations
        applied = get_applied_migrations(cursor)
        print(f"\nAlready applied migrations: {len(applied)}")

        # Filter out already applied
        to_apply = []
        for migration in MIGRATIONS:
            version = extract_version(migration)
            if version not in applied:
                to_apply.append(migration)
            else:
                print(f"⏭️  Skipping (already applied): {migration}")

        print(f"\nMigrations to apply: {len(to_apply)}")

        if not to_apply:
            print("\n✅ All migrations already applied!")
            cursor.close()
            conn.close()
            return

        # Apply migrations
        applied_count = 0
        for migration in to_apply:
            filepath = os.path.join(MIGRATIONS_DIR, migration)

            if not os.path.exists(filepath):
                print(f"⚠️  WARNING: File not found: {filepath}")
                continue

            apply_migration(cursor, filepath, migration)
            applied_count += 1

        # Commit all migrations
        conn.commit()

        print("\n" + "=" * 80)
        print("DEPLOYMENT COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully applied {applied_count} migrations")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Show final migration status
        cursor.execute("""
            SELECT version, name, applied_at
            FROM supabase_migrations.schema_migrations
            ORDER BY version DESC
            LIMIT 20
        """)

        print("\nRecent Migrations in Database:")
        print(f"{'Version':<20} {'Name':<50} {'Applied At':<20}")
        print("-" * 90)
        for row in cursor.fetchall():
            print(f"{row[0]:<20} {row[1]:<50} {str(row[2]):<20}")

    except Exception as e:
        print(f"\n❌ DEPLOYMENT FAILED: {e}")
        conn.rollback()
        print("All changes have been rolled back.")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
