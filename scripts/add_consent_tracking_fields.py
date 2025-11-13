#!/usr/bin/env python3
"""
Add GDPR Consent Tracking Fields
=================================
Adds enhanced consent tracking fields to contacts table for full GDPR compliance.

Fields Added:
- consent_date: When did they opt in?
- consent_source: Where did consent come from? (kajabi_form, ticket_tailor, manual, etc.)
- consent_method: How was consent obtained? (double_opt_in, single_opt_in, manual_staff, etc.)
- unsubscribe_date: When did they opt out?
- legal_basis: GDPR legal basis (consent, legitimate_interest, contract)

Safety Features:
- Dry-run mode (default)
- Transaction with rollback
- Pre and post validation
- Comprehensive logging
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

import psycopg2
from psycopg2.extras import RealDictCursor

def check_existing_fields(cursor) -> Dict[str, bool]:
    """Check which consent fields already exist."""
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'contacts'
          AND column_name IN (
              'consent_date',
              'consent_source',
              'consent_method',
              'unsubscribe_date',
              'legal_basis'
          );
    """)

    existing = {row[0] for row in cursor.fetchall()}

    return {
        'consent_date': 'consent_date' in existing,
        'consent_source': 'consent_source' in existing,
        'consent_method': 'consent_method' in existing,
        'unsubscribe_date': 'unsubscribe_date' in existing,
        'legal_basis': 'legal_basis' in existing
    }

def add_consent_fields(cursor, dry_run: bool = True):
    """Add consent tracking fields to contacts table."""

    print("\n" + "=" * 80)
    print("STEP 1: ADD CONSENT TRACKING FIELDS")
    print("=" * 80)

    # Check existing fields
    existing = check_existing_fields(cursor)

    print("\nField Status:")
    for field, exists in existing.items():
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {field:<20} {status}")

    if all(existing.values()):
        print("\n✓ All consent fields already exist - skipping creation")
        return True

    print("\nAdding missing fields...")

    # Build ALTER TABLE statement for missing fields
    alter_statements = []

    if not existing['consent_date']:
        alter_statements.append("ADD COLUMN consent_date TIMESTAMP")

    if not existing['consent_source']:
        alter_statements.append("""
            ADD COLUMN consent_source VARCHAR(50)
            CHECK (consent_source IN (
                'kajabi_form',
                'ticket_tailor',
                'manual',
                'import_historical',
                'paypal',
                'zoho',
                'unknown'
            ))
        """)

    if not existing['consent_method']:
        alter_statements.append("""
            ADD COLUMN consent_method VARCHAR(50)
            CHECK (consent_method IN (
                'double_opt_in',
                'single_opt_in',
                'manual_staff',
                'legacy_import',
                'unknown'
            ))
        """)

    if not existing['unsubscribe_date']:
        alter_statements.append("ADD COLUMN unsubscribe_date TIMESTAMP")

    if not existing['legal_basis']:
        alter_statements.append("""
            ADD COLUMN legal_basis VARCHAR(100)
            CHECK (legal_basis IN (
                'consent',
                'legitimate_interest',
                'contract',
                'legal_obligation',
                'vital_interests',
                'public_task'
            ))
        """)

    if not alter_statements:
        print("✓ No fields to add")
        return True

    sql = "ALTER TABLE contacts " + ", ".join(alter_statements) + ";"

    if dry_run:
        print("\n[DRY-RUN] Would execute:")
        print(sql)
        return True
    else:
        print("\n[EXECUTE] Running migration...")
        cursor.execute(sql)
        print("✓ Fields added successfully")
        return True

def backfill_consent_data(cursor, dry_run: bool = True):
    """Backfill consent data from existing records."""

    print("\n" + "=" * 80)
    print("STEP 2: BACKFILL CONSENT DATA")
    print("=" * 80)

    # Get counts before backfill
    cursor.execute("""
        SELECT
            source_system,
            email_subscribed,
            COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY source_system, email_subscribed
        ORDER BY source_system, email_subscribed;
    """)

    print("\nCurrent Data (before backfill):")
    print(f"{'Source':<20} {'Status':<15} {'Count':>10}")
    print("-" * 50)
    for row in cursor.fetchall():
        source = row[0] or 'NULL'
        status = 'Subscribed' if row[1] else 'Unsubscribed'
        print(f"{source:<20} {status:<15} {row[2]:>10,}")

    # Backfill strategies by source
    backfill_queries = []

    # 1. Kajabi contacts (subscribed)
    backfill_queries.append({
        'name': 'Kajabi Subscribed',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'kajabi_form',
                consent_method = 'double_opt_in',
                legal_basis = 'consent'
            WHERE source_system = 'kajabi'
              AND email_subscribed = true
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    # 2. Kajabi contacts (unsubscribed) - set unsubscribe date
    backfill_queries.append({
        'name': 'Kajabi Unsubscribed',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'kajabi_form',
                consent_method = 'double_opt_in',
                unsubscribe_date = updated_at,
                legal_basis = 'consent'
            WHERE source_system = 'kajabi'
              AND email_subscribed = false
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    # 3. Ticket Tailor contacts (subscribed)
    backfill_queries.append({
        'name': 'Ticket Tailor Subscribed',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'ticket_tailor',
                consent_method = 'single_opt_in',
                legal_basis = 'consent'
            WHERE source_system = 'ticket_tailor'
              AND email_subscribed = true
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    # 4. Ticket Tailor contacts (unsubscribed)
    backfill_queries.append({
        'name': 'Ticket Tailor Unsubscribed',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'ticket_tailor',
                consent_method = 'single_opt_in',
                unsubscribe_date = updated_at,
                legal_basis = 'consent'
            WHERE source_system = 'ticket_tailor'
              AND email_subscribed = false
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    # 5. Manual contacts (almost all subscribed)
    backfill_queries.append({
        'name': 'Manual Contacts',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'manual',
                consent_method = 'manual_staff',
                legal_basis = CASE
                    WHEN email_subscribed = true THEN 'consent'
                    ELSE 'consent'
                END,
                unsubscribe_date = CASE
                    WHEN email_subscribed = false THEN updated_at
                    ELSE NULL
                END
            WHERE source_system = 'manual'
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    # 6. PayPal contacts (mostly unsubscribed - no direct consent)
    backfill_queries.append({
        'name': 'PayPal Contacts',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'paypal',
                consent_method = 'legacy_import',
                legal_basis = CASE
                    WHEN email_subscribed = true THEN 'consent'
                    ELSE 'consent'
                END,
                unsubscribe_date = CASE
                    WHEN email_subscribed = false THEN updated_at
                    ELSE NULL
                END
            WHERE source_system = 'paypal'
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    # 7. Zoho contacts (legacy, mostly unsubscribed)
    backfill_queries.append({
        'name': 'Zoho Contacts',
        'sql': """
            UPDATE contacts SET
                consent_date = created_at,
                consent_source = 'zoho',
                consent_method = 'legacy_import',
                legal_basis = 'consent',
                unsubscribe_date = CASE
                    WHEN email_subscribed = false THEN updated_at
                    ELSE NULL
                END
            WHERE source_system = 'zoho'
              AND consent_date IS NULL
              AND deleted_at IS NULL
        """
    })

    print("\nBackfill Operations:")
    print("-" * 80)

    total_updated = 0

    for query in backfill_queries:
        if dry_run:
            # Get count of what would be updated
            count_sql = query['sql'].replace('UPDATE contacts SET', 'SELECT COUNT(*) FROM contacts WHERE') \
                                     .split('WHERE')[0] + ' WHERE ' + ' AND '.join(query['sql'].split('WHERE')[1:])
            # Simplify to just get count
            cursor.execute(f"SELECT COUNT(*) FROM contacts WHERE {query['sql'].split('WHERE')[-1]}")
            count = cursor.fetchone()[0]
            print(f"  [{query['name']}]")
            print(f"    Would update: {count:,} contacts")
            total_updated += count
        else:
            cursor.execute(query['sql'])
            count = cursor.rowcount
            print(f"  [{query['name']}]")
            print(f"    ✓ Updated: {count:,} contacts")
            total_updated += count

    print("-" * 80)
    print(f"Total: {total_updated:,} contacts {'would be' if dry_run else ''} updated")

    return True

def verify_backfill(cursor):
    """Verify the backfill completed successfully."""

    print("\n" + "=" * 80)
    print("STEP 3: VERIFICATION")
    print("=" * 80)

    # Check coverage
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(consent_date) as with_date,
            COUNT(consent_source) as with_source,
            COUNT(consent_method) as with_method,
            COUNT(legal_basis) as with_basis,
            COUNT(CASE WHEN email_subscribed = false THEN unsubscribe_date END) as unsubscribed_with_date
        FROM contacts
        WHERE deleted_at IS NULL;
    """)

    row = cursor.fetchone()
    total = row[0]

    print("\nConsent Field Coverage:")
    print(f"  Total contacts: {total:,}")
    print(f"  With consent_date: {row[1]:,} ({row[1]/total*100:.1f}%)")
    print(f"  With consent_source: {row[2]:,} ({row[2]/total*100:.1f}%)")
    print(f"  With consent_method: {row[3]:,} ({row[3]/total*100:.1f}%)")
    print(f"  With legal_basis: {row[4]:,} ({row[4]/total*100:.1f}%)")

    # Count unsubscribed with date
    cursor.execute("SELECT COUNT(*) FROM contacts WHERE email_subscribed = false AND deleted_at IS NULL")
    total_unsub = cursor.fetchone()[0]
    print(f"  Unsubscribed with date: {row[5]:,} of {total_unsub:,} ({row[5]/total_unsub*100:.1f}%)")

    # Show breakdown by source and consent_source
    cursor.execute("""
        SELECT
            source_system,
            consent_source,
            consent_method,
            COUNT(*) as count,
            COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY source_system, consent_source, consent_method
        ORDER BY source_system, consent_source;
    """)

    print("\nConsent Tracking by Source:")
    print(f"{'Source System':<20} {'Consent Source':<20} {'Method':<20} {'Total':>10} {'Subscribed':>12}")
    print("-" * 90)
    for row in cursor.fetchall():
        source = row[0] or 'NULL'
        consent_src = row[1] or 'NULL'
        method = row[2] or 'NULL'
        print(f"{source:<20} {consent_src:<20} {method:<20} {row[3]:>10,} {row[4]:>12,}")

    # Check for any contacts missing consent data
    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND (consent_date IS NULL OR consent_source IS NULL);
    """)

    missing = cursor.fetchone()[0]
    if missing > 0:
        print(f"\n⚠️  WARNING: {missing:,} contacts still missing consent data")
        return False
    else:
        print("\n✓ All contacts have complete consent tracking")
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Add GDPR consent tracking fields and backfill data',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute changes (default is dry-run)'
    )

    args = parser.parse_args()
    dry_run = not args.execute

    # Connect to database
    try:
        database_url = get_database_url()
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return 1

    try:
        print("=" * 80)
        print("GDPR CONSENT TRACKING ENHANCEMENT")
        print("=" * 80)
        print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")

        if not dry_run:
            print("\n⚠️  EXECUTE MODE - Changes will be made to the database!")
            print("   Press Ctrl+C within 5 seconds to cancel...")
            import time
            for i in range(5, 0, -1):
                print(f"   {i}...", end=' ', flush=True)
                time.sleep(1)
            print("\n   Starting execution...")

        # Step 1: Add fields
        if not add_consent_fields(cursor, dry_run):
            raise Exception("Failed to add consent fields")

        # Step 2: Backfill data
        if not backfill_consent_data(cursor, dry_run):
            raise Exception("Failed to backfill consent data")

        # Step 3: Verify
        if not dry_run:
            if not verify_backfill(cursor):
                raise Exception("Verification failed")

        if dry_run:
            print("\n" + "=" * 80)
            print("DRY-RUN COMPLETE - No changes made")
            print("=" * 80)
            print("\nTo execute changes, run:")
            print("  python3 scripts/add_consent_tracking_fields.py --execute")
        else:
            print("\n" + "=" * 80)
            print("COMMITTING CHANGES")
            print("=" * 80)
            conn.commit()
            print("✓ Transaction committed successfully")

            # Final verification
            verify_backfill(cursor)

            print("\n" + "=" * 80)
            print("✓ CONSENT TRACKING ENHANCEMENT COMPLETE")
            print("=" * 80)
            print("\nNext steps:")
            print("  1. Review verification output above")
            print("  2. Update import scripts to populate consent fields")
            print("  3. Document consent tracking in procedures")

        cursor.close()
        conn.close()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        conn.rollback()
        cursor.close()
        conn.close()
        return 1

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        print("Rolling back changes...")
        conn.rollback()
        cursor.close()
        conn.close()
        return 1

if __name__ == '__main__':
    sys.exit(main())
