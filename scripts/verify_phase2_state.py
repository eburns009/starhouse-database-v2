#!/usr/bin/env python3
"""
FAANG-Quality Phase 2 State Verification

Verifies current state for Phase 2 tasks:
- Task 2.1: Phone enrichment opportunities (27 contacts expected)
- Task 2.2: Different PayPal emails (2 contacts expected)
- Task 2.3: Additional name parsing (5 contacts expected)

USAGE:
    python3 scripts/verify_phase2_state.py

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
"""

import psycopg2
import sys

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

def main():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        print("✓ Database connection established\n")

        print("=" * 80)
        print("PHASE 2 STATE VERIFICATION")
        print("=" * 80)
        print()

        # Task 2.1: Phone Enrichment
        print("Task 2.1: Phone Enrichment Opportunities")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND (phone IS NULL OR phone = '')
              AND (
                  (paypal_phone IS NOT NULL AND paypal_phone != '')
                  OR (zoho_phone IS NOT NULL AND zoho_phone != '')
                  OR (additional_phone IS NOT NULL AND additional_phone != '')
              )
        """)

        phone_count = cursor.fetchone()[0]
        print(f"   Contacts without primary phone but have alt phone: {phone_count}")

        # Sample
        cursor.execute("""
            SELECT id, email, paypal_phone, zoho_phone, additional_phone
            FROM contacts
            WHERE deleted_at IS NULL
              AND (phone IS NULL OR phone = '')
              AND (
                  (paypal_phone IS NOT NULL AND paypal_phone != '')
                  OR (zoho_phone IS NOT NULL AND zoho_phone != '')
                  OR (additional_phone IS NOT NULL AND additional_phone != '')
              )
            LIMIT 5
        """)

        print("   Sample contacts:")
        for row in cursor.fetchall():
            alt_phone = row[2] or row[3] or row[4]
            source = 'paypal' if row[2] else ('zoho' if row[3] else 'additional')
            print(f"     {row[0][:8]}... ({row[1]}): {alt_phone} (from {source})")
        print()

        # Task 2.2: Different PayPal Emails
        print("Task 2.2: Different PayPal Emails")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND paypal_email IS NOT NULL
              AND paypal_email != ''
              AND paypal_email != email
        """)

        paypal_email_count = cursor.fetchone()[0]
        print(f"   Contacts where paypal_email differs from primary: {paypal_email_count}")

        # Sample
        cursor.execute("""
            SELECT id, email, paypal_email
            FROM contacts
            WHERE deleted_at IS NULL
              AND paypal_email IS NOT NULL
              AND paypal_email != ''
              AND paypal_email != email
            LIMIT 5
        """)

        print("   Sample contacts:")
        for row in cursor.fetchall():
            print(f"     {row[0][:8]}... primary: {row[1]}, paypal: {row[2]}")
        print()

        # Task 2.3: Additional Name Parsing
        print("Task 2.3: Additional Name Parsing")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND additional_name IS NOT NULL
              AND additional_name != ''
              AND (
                  first_name IS NULL OR first_name = '' OR first_name = 'nan'
                  OR last_name IS NULL OR last_name = '' OR last_name = 'nan'
              )
        """)

        additional_name_count = cursor.fetchone()[0]
        print(f"   Contacts with additional_name but incomplete primary name: {additional_name_count}")

        # Sample
        cursor.execute("""
            SELECT id, first_name, last_name, additional_name, email
            FROM contacts
            WHERE deleted_at IS NULL
              AND additional_name IS NOT NULL
              AND additional_name != ''
              AND (
                  first_name IS NULL OR first_name = '' OR first_name = 'nan'
                  OR last_name IS NULL OR last_name = '' OR last_name = 'nan'
              )
            LIMIT 5
        """)

        print("   Sample contacts:")
        for row in cursor.fetchall():
            print(f"     {row[0][:8]}... current: '{row[1]}' '{row[2]}', additional: '{row[3]}' ({row[4]})")
        print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Task 2.1 (Phone Enrichment):      {phone_count} contacts")
        print(f"Task 2.2 (PayPal Emails):          {paypal_email_count} contacts")
        print(f"Task 2.3 (Additional Name Parse):  {additional_name_count} contacts")
        print(f"Total Phase 2 Impact:              {phone_count + paypal_email_count + additional_name_count} contacts")
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
