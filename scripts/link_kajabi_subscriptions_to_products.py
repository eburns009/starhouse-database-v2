#!/usr/bin/env python3
"""
Link existing Kajabi subscriptions to products

The subscriptions were imported but didn't have product_id set.
This script reads the Kajabi CSV to get the offer_id for each subscription,
then links subscriptions to products via the kajabi_offer_id field.
"""

import csv
import os
import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DB_CONNECTION_STRING = os.environ.get(
    'DATABASE_URL',
    'PLACEHOLDER_USE_ENV_VAR'
)

SUBSCRIPTIONS_FILE = '/workspaces/starhouse-database-v2/data/kajabi_subscriptions.csv'

def main():
    parser = argparse.ArgumentParser(description='Link Kajabi subscriptions to products')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    args = parser.parse_args()

    print("=" * 80)
    print("LINK KAJABI SUBSCRIPTIONS TO PRODUCTS")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be saved")

    # Connect to database
    conn = psycopg2.connect(DB_CONNECTION_STRING)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get product mapping: kajabi_offer_id -> product_id
        cur.execute("""
            SELECT kajabi_offer_id, id, name
            FROM products
            WHERE kajabi_offer_id IS NOT NULL
        """)
        products_map = {row['kajabi_offer_id']: row for row in cur.fetchall()}
        print(f"\n📊 Found {len(products_map)} products with Kajabi offer IDs")

        # Read Kajabi CSV to get subscription -> offer mapping
        subscription_to_offer = {}
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                kajabi_sub_id = row['Kajabi Subscription ID'].strip()
                offer_id = row['Offer ID'].strip()
                if kajabi_sub_id and offer_id:
                    subscription_to_offer[kajabi_sub_id] = offer_id

        print(f"📄 Found {len(subscription_to_offer)} subscription->offer mappings in CSV")

        # Get subscriptions without product_id
        cur.execute("""
            SELECT id, kajabi_subscription_id
            FROM subscriptions
            WHERE kajabi_subscription_id IS NOT NULL
              AND kajabi_subscription_id NOT LIKE 'I-%'
              AND product_id IS NULL
        """)
        unlinked_subs = cur.fetchall()
        print(f"🔗 Found {len(unlinked_subs)} subscriptions without product_id\n")

        # Link subscriptions to products
        stats = {
            'linked': 0,
            'missing_offer': 0,
            'missing_product': 0,
            'errors': []
        }

        for sub in unlinked_subs:
            kajabi_sub_id = sub['kajabi_subscription_id']

            # Get offer_id from CSV
            offer_id = subscription_to_offer.get(kajabi_sub_id)
            if not offer_id:
                stats['missing_offer'] += 1
                continue

            # Get product_id from products map
            product = products_map.get(offer_id)
            if not product:
                stats['missing_product'] += 1
                stats['errors'].append(f"No product found for offer {offer_id} (sub: {kajabi_sub_id})")
                continue

            # Update subscription with product_id
            cur.execute("""
                UPDATE subscriptions
                SET product_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (product['id'], sub['id']))

            stats['linked'] += 1
            if stats['linked'] <= 10:
                print(f"  ✅ Linked subscription {kajabi_sub_id} to product: {product['name']}")
            elif stats['linked'] % 50 == 0:
                print(f"  📊 Progress: {stats['linked']} subscriptions linked...")

        # Summary
        print(f"\n📊 Summary:")
        print(f"  Linked: {stats['linked']}")
        print(f"  Missing offer in CSV: {stats['missing_offer']}")
        print(f"  Missing product in DB: {stats['missing_product']}")
        print(f"  Errors: {len(stats['errors'])}")

        if stats['errors']:
            print(f"\n⚠️  Errors:")
            for error in stats['errors'][:10]:
                print(f"    {error}")

        # Verify results
        if not args.dry_run:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(product_id) as with_product
                FROM subscriptions
                WHERE kajabi_subscription_id IS NOT NULL
                  AND kajabi_subscription_id NOT LIKE 'I-%'
            """)
            result = cur.fetchone()
            print(f"\n✅ Verification:")
            print(f"  Total Kajabi subscriptions: {result['total']}")
            print(f"  With product_id: {result['with_product']}")
            print(f"  Still missing: {result['total'] - result['with_product']}")

        # Commit or rollback
        if args.dry_run:
            conn.rollback()
            print("\n🔄 DRY RUN COMPLETE - No changes were saved")
        else:
            conn.commit()
            print("\n✅ CHANGES COMMITTED")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
