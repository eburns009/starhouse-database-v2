#!/usr/bin/env python3
"""
Verify current database state for Phase 1 execution
Checks:
1. Missing/nan names (47 contacts expected)
2. Additional emails to migrate (375 contacts expected)
"""

import psycopg2
from db_config import get_database_url

DATABASE_URL = get_database_url()

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("=" * 80)
    print("PHASE 1 STATE VERIFICATION")
    print("=" * 80)
    print()

    # Check 1: Missing/nan names
    print("1. MISSING/NAN NAME ISSUE")
    print("-" * 80)

    cursor.execute("""
        SELECT
            COUNT(*) as total_with_issue,
            COUNT(CASE WHEN first_name IS NULL OR first_name = '' THEN 1 END) as null_first,
            COUNT(CASE WHEN first_name = 'nan' THEN 1 END) as nan_first,
            COUNT(CASE WHEN last_name IS NULL OR last_name = '' THEN 1 END) as null_last,
            COUNT(CASE WHEN last_name = 'nan' THEN 1 END) as nan_last
        FROM contacts
        WHERE deleted_at IS NULL
          AND (first_name IS NULL OR first_name = '' OR first_name = 'nan'
               OR last_name IS NULL OR last_name = '' OR last_name = 'nan')
    """)

    row = cursor.fetchone()
    print(f"   Total contacts with name issues: {row[0]}")
    print(f"   - NULL/empty first_name: {row[1]}")
    print(f"   - 'nan' first_name: {row[2]}")
    print(f"   - NULL/empty last_name: {row[3]}")
    print(f"   - 'nan' last_name: {row[4]}")
    print()

    # Show sample of nan names
    cursor.execute("""
        SELECT id, first_name, last_name, email, source_system
        FROM contacts
        WHERE deleted_at IS NULL
          AND (first_name = 'nan' OR last_name = 'nan')
        LIMIT 5
    """)

    print("   Sample contacts with 'nan' names:")
    for row in cursor.fetchall():
        print(f"   - ID {row[0]}: '{row[1]}' '{row[2]}' ({row[3]}) from {row[4]}")
    print()

    # Check 2: Additional email migration
    print("2. ADDITIONAL EMAIL MIGRATION")
    print("-" * 80)

    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND additional_email IS NOT NULL
          AND additional_email != ''
    """)

    total_additional = cursor.fetchone()[0]
    print(f"   Contacts with additional_email: {total_additional}")

    # Check how many are already in contact_emails table
    cursor.execute("""
        SELECT COUNT(DISTINCT c.id)
        FROM contacts c
        INNER JOIN contact_emails ce ON c.id = ce.contact_id
          AND ce.email = c.additional_email
        WHERE c.deleted_at IS NULL
          AND c.additional_email IS NOT NULL
          AND c.additional_email != ''
    """)

    already_migrated = cursor.fetchone()[0]
    needs_migration = total_additional - already_migrated

    print(f"   Already in contact_emails: {already_migrated}")
    print(f"   NEEDS MIGRATION: {needs_migration}")
    print()

    # Sample of emails to migrate
    cursor.execute("""
        SELECT c.id, c.email, c.additional_email, c.source_system
        FROM contacts c
        LEFT JOIN contact_emails ce ON c.id = ce.contact_id
          AND ce.email = c.additional_email
        WHERE c.deleted_at IS NULL
          AND c.additional_email IS NOT NULL
          AND c.additional_email != ''
          AND ce.id IS NULL
        LIMIT 5
    """)

    print("   Sample emails to migrate:")
    for row in cursor.fetchall():
        print(f"   - ID {row[0]}: primary={row[1]}, additional={row[2]} (from {row[3]})")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY - PHASE 1 PRIORITIES")
    print("=" * 80)
    print()
    print(f"✅ Task 1.1: Fix Missing Names - {row[0]} contacts")
    print(f"✅ Task 1.2: Migrate Additional Emails - {needs_migration} contacts")
    print()
    print("RECOMMENDATION:")
    print("Start with Task 1.2 (Email Migration) because:")
    print("  - Lower risk (simple data copy)")
    print(f"  - Clear success criteria ({needs_migration} → 0 remaining)")
    print("  - Quick win (~5 minutes)")
    print("  - No data loss risk")
    print()
    print("Then tackle Task 1.1 (Missing Names) which requires:")
    print("  - Investigation into 'nan' source (47 contacts from QuickBooks)")
    print("  - Potential data recovery from contact_names table")
    print("  - Manual review for unrecoverable cases")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
