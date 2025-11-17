#!/usr/bin/env python3
"""
FAANG-Quality Phase 3 State Verification

Verifies current state for Phase 3 tasks:
- Remaining 'nan' names (34 contacts expected)
- Duplicate contacts detection (exact name matches)
- Duplicate contacts detection (phone matches)
- Duplicate contacts detection (email similarity)

USAGE:
    python3 scripts/verify_phase3_state.py

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
"""

import psycopg2
import sys

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

def main():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require', connect_timeout=10)
        cursor = conn.cursor()
        print("✓ Database connection established\n")

        print("=" * 80)
        print("PHASE 3 STATE VERIFICATION")
        print("=" * 80)
        print()

        # Task 3.1: Remaining 'nan' names
        print("Task 3.1: Remaining 'nan' Names")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND (first_name = 'nan' OR last_name = 'nan')
        """)

        nan_count = cursor.fetchone()[0]
        print(f"   Contacts with 'nan' names: {nan_count}")

        # Sample
        cursor.execute("""
            SELECT id, email, first_name, last_name, source_system
            FROM contacts
            WHERE deleted_at IS NULL
              AND (first_name = 'nan' OR last_name = 'nan')
            ORDER BY email
            LIMIT 5
        """)

        print("   Sample contacts:")
        for row in cursor.fetchall():
            print(f"     {row[1][:40]:40} | '{row[2]}' '{row[3]}' | {row[4]}")
        print()

        # Task 3.2: Exact name duplicates
        print("Task 3.2: Exact Name Duplicates")
        print("-" * 80)

        cursor.execute("""
            SELECT
                first_name,
                last_name,
                COUNT(*) as count,
                STRING_AGG(email, ', ' ORDER BY created_at) as emails
            FROM contacts
            WHERE deleted_at IS NULL
              AND first_name IS NOT NULL
              AND last_name IS NOT NULL
              AND first_name != ''
              AND last_name != ''
              AND first_name != 'nan'
              AND last_name != 'nan'
            GROUP BY first_name, last_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)

        name_dupes = cursor.fetchall()
        total_name_dupes = len(name_dupes)

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT first_name, last_name
                FROM contacts
                WHERE deleted_at IS NULL
                  AND first_name IS NOT NULL
                  AND last_name IS NOT NULL
                  AND first_name != ''
                  AND last_name != ''
                  AND first_name != 'nan'
                  AND last_name != 'nan'
                GROUP BY first_name, last_name
                HAVING COUNT(*) > 1
            ) as dupes
        """)

        total_name_dupes = cursor.fetchone()[0]
        print(f"   Name groups with duplicates: {total_name_dupes}")

        print("   Sample duplicate groups:")
        for row in name_dupes[:5]:
            print(f"     {row[0]} {row[1]}: {row[2]} contacts")
            print(f"       Emails: {row[3][:100]}...")
        print()

        # Task 3.3: Phone duplicates
        print("Task 3.3: Phone Number Duplicates")
        print("-" * 80)

        cursor.execute("""
            SELECT
                REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as normalized_phone,
                COUNT(*) as count,
                STRING_AGG(first_name || ' ' || last_name, ', ' ORDER BY created_at) as names
            FROM contacts
            WHERE deleted_at IS NULL
              AND phone IS NOT NULL
              AND phone != ''
              AND LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '', 'g')) >= 10
            GROUP BY REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)

        phone_dupes = cursor.fetchall()

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as normalized_phone
                FROM contacts
                WHERE deleted_at IS NULL
                  AND phone IS NOT NULL
                  AND phone != ''
                  AND LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '', 'g')) >= 10
                GROUP BY REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
                HAVING COUNT(*) > 1
            ) as dupes
        """)

        total_phone_dupes = cursor.fetchone()[0]
        print(f"   Phone numbers with duplicates: {total_phone_dupes}")

        print("   Sample duplicate groups:")
        for row in phone_dupes[:5]:
            print(f"     Phone {row[0]}: {row[1]} contacts")
            print(f"       Names: {row[2]}")
        print()

        # Task 3.4: Email domain duplicates (same person, different emails)
        print("Task 3.4: Same Person, Different Emails (Heuristic)")
        print("-" * 80)

        cursor.execute("""
            WITH same_name_diff_email AS (
                SELECT
                    first_name,
                    last_name,
                    COUNT(DISTINCT email) as unique_emails,
                    COUNT(*) as contact_count,
                    STRING_AGG(DISTINCT email, ', ' ORDER BY email) as sample_emails
                FROM contacts
                WHERE deleted_at IS NULL
                  AND first_name IS NOT NULL
                  AND last_name IS NOT NULL
                  AND first_name != ''
                  AND last_name != ''
                  AND first_name != 'nan'
                  AND last_name != 'nan'
                  AND email IS NOT NULL
                GROUP BY first_name, last_name
                HAVING COUNT(DISTINCT email) > 1
            )
            SELECT * FROM same_name_diff_email
            ORDER BY unique_emails DESC, contact_count DESC
            LIMIT 5
        """)

        email_dupes = cursor.fetchall()

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT first_name, last_name
                FROM contacts
                WHERE deleted_at IS NULL
                  AND first_name IS NOT NULL
                  AND last_name IS NOT NULL
                  AND first_name != ''
                  AND last_name != ''
                  AND first_name != 'nan'
                  AND last_name != 'nan'
                  AND email IS NOT NULL
                GROUP BY first_name, last_name
                HAVING COUNT(DISTINCT email) > 1
            ) as dupes
        """)

        total_email_dupes = cursor.fetchone()[0]
        print(f"   Name groups with multiple emails: {total_email_dupes}")

        print("   Sample groups:")
        for row in email_dupes[:5]:
            print(f"     {row[0]} {row[1]}: {row[2]} different emails ({row[3]} contacts)")
            print(f"       Emails: {row[4]}")
        print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Task 3.1 (Remaining 'nan' names):       {nan_count} contacts")
        print(f"Task 3.2 (Exact name duplicates):       {total_name_dupes} groups")
        print(f"Task 3.3 (Phone duplicates):            {total_phone_dupes} groups")
        print(f"Task 3.4 (Same name, diff emails):      {total_email_dupes} groups")
        print()
        print("Note: Duplicate resolution requires manual review.")
        print("Phase 3 will focus on detection, flagging, and providing tools for review.")
        print()

        cursor.close()
        conn.close()

        return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
