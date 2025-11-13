#!/usr/bin/env python3
"""
Backfill Ticket Tailor IDs
===========================
Links Ticket Tailor contacts to their order IDs by looking up the
external_order_id from the transactions table.

This fixes a bug in the original import where ticket_tailor_id wasn't populated.

Run modes:
  --dry-run: Show what would be updated (default)
  --execute: Actually update the database
"""

import psycopg2
import os
import sys
from datetime import datetime

def print_header(text):
    print("=" * 80)
    print(text)
    print("=" * 80)

def backfill_ticket_tailor_ids(dry_run=True):
    """Backfill ticket_tailor_id from transactions table."""

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print_header("BACKFILL TICKET TAILOR IDs")
    print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    print(f"Time: {datetime.now().isoformat()}")

    if not dry_run:
        print("\n⚠️  EXECUTE MODE - Changes will be made to the database!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n   Starting execution...")

    # Check current status
    print("\n" + "=" * 80)
    print("CURRENT STATUS")
    print("=" * 80)

    cur.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN ticket_tailor_id IS NULL THEN 1 ELSE 0 END) as missing_id,
            SUM(CASE WHEN ticket_tailor_id IS NOT NULL THEN 1 ELSE 0 END) as has_id
        FROM contacts
        WHERE deleted_at IS NULL
        AND source_system = 'ticket_tailor'
    """)
    row = cur.fetchone()
    print(f"\nTicket Tailor contacts:")
    print(f"  Total: {row[0]}")
    print(f"  Missing ticket_tailor_id: {row[1]} ({100*row[1]/row[0]:.1f}%)")
    print(f"  Has ticket_tailor_id: {row[2]} ({100*row[2]/row[0]:.1f}%)")

    # Check how many can be backfilled
    print("\n" + "=" * 80)
    print("BACKFILL OPPORTUNITIES")
    print("=" * 80)

    cur.execute("""
        SELECT
            c.id,
            c.email,
            c.first_name || ' ' || c.last_name as name,
            c.ticket_tailor_id as current_tt_id,
            t.external_order_id as order_id_from_transaction,
            t.transaction_date
        FROM contacts c
        INNER JOIN transactions t ON c.id = t.contact_id
        WHERE c.deleted_at IS NULL
        AND c.source_system = 'ticket_tailor'
        AND c.ticket_tailor_id IS NULL
        AND t.source_system = 'ticket_tailor'
        AND t.external_order_id IS NOT NULL
        ORDER BY t.transaction_date DESC
    """)

    backfill_data = cur.fetchall()
    print(f"\nFound {len(backfill_data)} contacts that can be backfilled")

    if backfill_data:
        print(f"\nSample contacts to be updated:")
        print(f"{'Email':<35} {'Name':<25} {'Order ID':<15} {'Date':<12}")
        print("-" * 95)
        for row in backfill_data[:10]:
            print(f"{row[1]:<35} {row[2]:<25} {row[4]:<15} {str(row[5].date()):<12}")

    # Check for contacts that CAN'T be backfilled (no transaction)
    cur.execute("""
        SELECT
            c.id,
            c.email,
            c.first_name || ' ' || c.last_name as name,
            c.created_at::date
        FROM contacts c
        WHERE c.deleted_at IS NULL
        AND c.source_system = 'ticket_tailor'
        AND c.ticket_tailor_id IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM transactions t
            WHERE t.contact_id = c.id
            AND t.source_system = 'ticket_tailor'
        )
    """)

    no_transaction = cur.fetchall()
    if no_transaction:
        print(f"\n⚠️  WARNING: {len(no_transaction)} Ticket Tailor contacts have no transactions")
        print(f"   These cannot be backfilled automatically")
        if len(no_transaction) <= 5:
            for row in no_transaction:
                print(f"   • {row[2]} ({row[1]}) - created {row[3]}")

    if not backfill_data:
        print("\n✓ No backfill needed - all contacts already have ticket_tailor_id")
        cur.close()
        conn.close()
        return

    # Apply backfill
    print("\n" + "=" * 80)
    print("APPLYING BACKFILL")
    print("=" * 80)

    if dry_run:
        print(f"\n[DRY-RUN] Would update {len(backfill_data)} contacts:")
        for i, row in enumerate(backfill_data[:5], 1):
            print(f"   [{i}] {row[2]} ({row[1]})")
            print(f"       SET ticket_tailor_id = '{row[4]}'")
    else:
        print(f"\nUpdating {len(backfill_data)} contacts...")

        update_count = 0
        for row in backfill_data:
            contact_id = row[0]
            order_id = row[4]

            cur.execute("""
                UPDATE contacts
                SET ticket_tailor_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (order_id, contact_id))

            update_count += 1
            if update_count % 50 == 0:
                print(f"   Updated {update_count}/{len(backfill_data)} contacts...")

        print(f"   ✓ Updated all {update_count} contacts")

    # Commit or rollback
    if not dry_run:
        print("\n" + "=" * 80)
        print("COMMITTING CHANGES")
        print("=" * 80)
        conn.commit()
        print("✓ Transaction committed successfully")
    else:
        conn.rollback()

    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    cur.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN ticket_tailor_id IS NULL THEN 1 ELSE 0 END) as missing_id,
            SUM(CASE WHEN ticket_tailor_id IS NOT NULL THEN 1 ELSE 0 END) as has_id
        FROM contacts
        WHERE deleted_at IS NULL
        AND source_system = 'ticket_tailor'
    """)
    row = cur.fetchone()

    print(f"\nTicket Tailor contacts after backfill:")
    print(f"  Total: {row[0]}")
    print(f"  Missing ticket_tailor_id: {row[1]} ({100*row[1]/row[0]:.1f}%)")
    print(f"  Has ticket_tailor_id: {row[2]} ({100*row[2]/row[0]:.1f}%)")

    # Show sample of updated contacts
    if not dry_run:
        cur.execute("""
            SELECT
                email,
                first_name || ' ' || last_name as name,
                ticket_tailor_id
            FROM contacts
            WHERE deleted_at IS NULL
            AND source_system = 'ticket_tailor'
            AND ticket_tailor_id IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 5
        """)

        print(f"\nSample updated contacts:")
        for row in cur.fetchall():
            print(f"   ✓ {row[1]} ({row[0]}) → ticket_tailor_id: {row[2]}")

    print("\n" + "=" * 80)
    if dry_run:
        print("✓ DRY-RUN COMPLETE")
        print("=" * 80)
        print("\nTo apply these changes, run:")
        print("  python3 scripts/backfill_ticket_tailor_ids.py --execute")
    else:
        print("✓ BACKFILL COMPLETE")
        print("=" * 80)

    cur.close()
    conn.close()

def main():
    dry_run = '--execute' not in sys.argv
    backfill_ticket_tailor_ids(dry_run=dry_run)

if __name__ == '__main__':
    main()
