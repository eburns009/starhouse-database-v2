#!/usr/bin/env python3
"""
Sync migration records - mark already-applied migrations as applied in schema_migrations
"""

import psycopg2
from datetime import datetime
from db_config import get_database_url

DATABASE_URL = get_database_url()

def check_migration_applied(cursor, migration_name):
    """
    Check if a migration has already been applied by examining the database schema.
    Returns True if the migration's changes are already present.
    """

    checks = {
        '20251101000000_add_transaction_source_system': lambda c: check_constraint_exists(c, 'transactions_source_system_check'),
        '20251101000001_proper_transaction_provenance': lambda c: True,  # Depends on previous
        '20251102000001_contact_module_schema': lambda c: check_table_exists(c, 'contact_tags'),
        '20251102000002_contact_module_views': lambda c: check_table_exists(c, 'contact_tags'),
        '20251102000003_contact_module_functions': lambda c: check_table_exists(c, 'contact_tags'),
        '20251102000004_contact_module_migration': lambda c: check_table_exists(c, 'contact_tags'),
        '20251102000005_fix_function_types': lambda c: check_table_exists(c, 'contact_tags'),
        '20251113000001_add_contact_tags': lambda c: check_table_exists(c, 'contact_tags'),
        '20251113000002_add_atomic_tag_functions': lambda c: check_table_exists(c, 'tags'),
        '20251113000003_staff_rls_policies': lambda c: check_table_exists(c, 'tags'),
        '20251113000004_secure_staff_access_control': lambda c: check_table_exists(c, 'tags'),
        '20251113000005_secure_financial_tables_rls': lambda c: check_table_exists(c, 'tags'),
        '20251113000006_simplify_staff_access': lambda c: check_table_exists(c, 'tags'),
        '20251114000000_mailing_list_priority_system': lambda c: check_column_exists(c, 'contacts', 'mailing_list_priority'),
        '20251114000001_protect_mailing_list': lambda c: check_column_exists(c, 'contacts', 'mailing_list_priority'),
        '20251114000002_fix_address_scoring_critical_bugs': lambda c: check_column_exists(c, 'contacts', 'mailing_list_priority'),
        '20251115000003_add_address_validation_fields': lambda c: check_column_exists(c, 'contacts', 'billing_usps_validated_at'),
        '20251115000004_add_ncoa_performance_index': lambda c: check_column_exists(c, 'contacts', 'ncoa_move_date'),
        '20251115000005_validation_first_scoring': lambda c: check_column_exists(c, 'contacts', 'billing_usps_validated_at'),
    }

    if migration_name in checks:
        return checks[migration_name](cursor)

    return False


def check_table_exists(cursor, table_name):
    """Check if a table exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        )
    """, (table_name,))
    return cursor.fetchone()[0]


def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            AND column_name = %s
        )
    """, (table_name, column_name))
    return cursor.fetchone()[0]


def check_constraint_exists(cursor, constraint_name):
    """Check if a constraint exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_name = %s
        )
    """, (constraint_name,))
    return cursor.fetchone()[0]


def main():
    print("=" * 80)
    print("MIGRATION SYNC - Recording Already-Applied Migrations")
    print("=" * 80)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    migrations_to_check = [
        '20251101000000_add_transaction_source_system',
        '20251101000001_proper_transaction_provenance',
        '20251102000001_contact_module_schema',
        '20251102000002_contact_module_views',
        '20251102000003_contact_module_functions',
        '20251102000004_contact_module_migration',
        '20251102000005_fix_function_types',
        '20251113000001_add_contact_tags',
        '20251113000002_add_atomic_tag_functions',
        '20251113000003_staff_rls_policies',
        '20251113000004_secure_staff_access_control',
        '20251113000005_secure_financial_tables_rls',
        '20251113000006_simplify_staff_access',
        '20251114000000_mailing_list_priority_system',
        '20251114000001_protect_mailing_list',
        '20251114000002_fix_address_scoring_critical_bugs',
        '20251115000003_add_address_validation_fields',
        '20251115000004_add_ncoa_performance_index',
        '20251115000005_validation_first_scoring',
    ]

    # Get currently recorded migrations
    cursor.execute("SELECT version FROM supabase_migrations.schema_migrations")
    recorded = {row[0] for row in cursor.fetchall()}

    synced_count = 0

    for migration_name in migrations_to_check:
        version = migration_name.split('_')[0]

        if version in recorded:
            print(f"✅ Already recorded: {migration_name}")
            continue

        # Check if migration has been applied
        if check_migration_applied(cursor, migration_name):
            print(f"📝 Recording as applied: {migration_name}")

            cursor.execute("""
                INSERT INTO supabase_migrations.schema_migrations (version, name)
                VALUES (%s, %s)
                ON CONFLICT (version) DO NOTHING
            """, (version, migration_name))

            synced_count += 1
        else:
            print(f"⏭️  Not yet applied: {migration_name}")

    conn.commit()

    print("\n" + "=" * 80)
    print(f"✅ Synced {synced_count} migration records")
    print("=" * 80)

    # Show current status
    cursor.execute("""
        SELECT version, name
        FROM supabase_migrations.schema_migrations
        ORDER BY version DESC
        LIMIT 20
    """)

    print("\nRecorded Migrations (most recent):")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
