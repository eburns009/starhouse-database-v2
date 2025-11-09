#!/usr/bin/env python3
"""
Sync shipping addresses to billing addresses for contacts that have shipping but no billing address.

Many contacts (especially from PayPal imports) have shipping addresses but no billing address.
In most cases, the shipping address IS the billing address.

This script:
1. Finds contacts with shipping address but no billing address
2. Copies shipping address fields to billing address fields
3. Sets billing_address_source appropriately
4. Preserves source information
"""
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"


def sync_shipping_to_billing(dry_run=True):
    """
    Copy shipping addresses to billing addresses where billing is missing

    Args:
        dry_run: If True, only report what would be updated without making changes
    """
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print(f"Sync Shipping to Billing Addresses")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE UPDATE'}")
    print(f"{'=' * 100}\n")

    # Find contacts with shipping but no billing
    cur.execute("""
        SELECT
            id,
            email,
            source_system,
            shipping_address_line_1,
            shipping_address_line_2,
            shipping_city,
            shipping_state,
            shipping_postal_code,
            shipping_country,
            shipping_address_source,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country
        FROM contacts
        WHERE
            shipping_address_line_1 IS NOT NULL
            AND address_line_1 IS NULL
        ORDER BY created_at DESC
    """)

    contacts = cur.fetchall()

    print(f"Found {len(contacts):,} contacts with shipping address but no billing address\n")

    if len(contacts) == 0:
        print("No contacts to update.")
        cur.close()
        conn.close()
        return {'contacts_updated': 0}

    # Statistics
    stats = {
        'total_found': len(contacts),
        'contacts_updated': 0,
        'by_source_system': {},
        'by_shipping_source': {}
    }

    sample_updates = []

    # Process each contact
    for contact in contacts:
        # Skip if shipping address is actually empty (only has NULL/empty city)
        has_real_address = (
            contact['shipping_address_line_1'] and contact['shipping_address_line_1'].strip()
        ) or (
            contact['shipping_city'] and contact['shipping_city'].strip()
        )

        if not has_real_address:
            continue

        # Count by source
        source = contact['source_system']
        if source not in stats['by_source_system']:
            stats['by_source_system'][source] = 0
        stats['by_source_system'][source] += 1

        # Count by shipping address source
        ship_source = contact['shipping_address_source'] or 'unknown'
        if ship_source not in stats['by_shipping_source']:
            stats['by_shipping_source'][ship_source] = 0
        stats['by_shipping_source'][ship_source] += 1

        # Prepare update
        updates = {
            'address_line_1': contact['shipping_address_line_1'],
            'address_line_2': contact['shipping_address_line_2'],
            'city': contact['shipping_city'],
            'state': contact['shipping_state'],
            'postal_code': contact['shipping_postal_code'],
            'country': contact['shipping_country'],
            'billing_address_source': contact['shipping_address_source'] or 'copied_from_shipping',
            'billing_address_updated_at': datetime.now()
        }

        stats['contacts_updated'] += 1

        # Collect sample for display
        if len(sample_updates) < 20:
            sample_updates.append({
                'email': contact['email'],
                'source': contact['source_system'],
                'address': f"{contact['shipping_address_line_1']}, {contact['shipping_city']}, {contact['shipping_state']} {contact['shipping_postal_code']}"
            })

        # Execute update if not dry run
        if not dry_run:
            cur.execute("""
                UPDATE contacts
                SET
                    address_line_1 = %s,
                    address_line_2 = %s,
                    city = %s,
                    state = %s,
                    postal_code = %s,
                    country = %s,
                    billing_address_source = %s,
                    billing_address_updated_at = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                updates['address_line_1'],
                updates['address_line_2'],
                updates['city'],
                updates['state'],
                updates['postal_code'],
                updates['country'],
                updates['billing_address_source'],
                updates['billing_address_updated_at'],
                contact['id']
            ))

    # Commit if not dry run
    if not dry_run:
        conn.commit()
        print("✓ Changes committed to database\n")
    else:
        print("ℹ DRY RUN - No changes were made\n")

    # Print statistics
    print(f"{'=' * 100}")
    print("SYNC STATISTICS")
    print(f"{'=' * 100}")
    print(f"Contacts with shipping but no billing: {stats['total_found']:,}")
    print(f"Contacts that will be updated: {stats['contacts_updated']:,}")
    print()

    print(f"BREAKDOWN BY SOURCE SYSTEM:")
    for source, count in sorted(stats['by_source_system'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count:,}")
    print()

    print(f"BREAKDOWN BY SHIPPING ADDRESS SOURCE:")
    for source, count in sorted(stats['by_shipping_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count:,}")
    print()

    # Show samples
    if sample_updates:
        print(f"{'=' * 100}")
        print(f"SAMPLE UPDATES (showing {min(len(sample_updates), 20)}):")
        print(f"{'=' * 100}\n")

        for i, update in enumerate(sample_updates, 1):
            print(f"{i}. {update['email']} ({update['source']})")
            print(f"   Will copy to billing: {update['address']}")
            print()

        if len(contacts) > 20:
            print(f"... and {len(contacts) - 20} more contacts")

    # Impact analysis
    cur.execute("SELECT COUNT(*) as total FROM contacts")
    total_contacts = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as with_billing FROM contacts WHERE address_line_1 IS NOT NULL")
    current_with_billing = cur.fetchone()['with_billing']

    new_with_billing = current_with_billing + stats['contacts_updated']

    print(f"\n{'=' * 100}")
    print("IMPACT ANALYSIS")
    print(f"{'=' * 100}")
    print(f"Total contacts: {total_contacts:,}")
    print(f"Current with billing address: {current_with_billing:,} ({current_with_billing/total_contacts*100:.1f}%)")
    print(f"After sync: {new_with_billing:,} ({new_with_billing/total_contacts*100:.1f}%)")
    print(f"Improvement: +{stats['contacts_updated']:,} contacts (+{stats['contacts_updated']/total_contacts*100:.1f} percentage points)")
    print()

    cur.close()
    conn.close()

    return stats


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Sync shipping addresses to billing addresses for contacts missing billing data'
    )
    parser.add_argument('--live', action='store_true',
                       help='Run in LIVE mode (default is DRY RUN)')
    args = parser.parse_args()

    try:
        stats = sync_shipping_to_billing(dry_run=not args.live)

        if not args.live and stats['contacts_updated'] > 0:
            print(f"{'=' * 100}")
            print("READY TO APPLY CHANGES")
            print(f"{'=' * 100}")
            print(f"\nThis will update {stats['contacts_updated']:,} contacts by copying their shipping")
            print(f"addresses to billing addresses.")
            print(f"\nThis is a safe operation that fills in missing data without overwriting anything.")
            print(f"\nTo apply these changes, run with --live flag:")
            print("  python3 scripts/sync_shipping_to_billing.py --live")
            print(f"{'=' * 100}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
