#!/usr/bin/env python3
"""
Kajabi Transactions Import - OPTIMIZED for Large Datasets
==========================================================

FAANG Production Standards with Performance Optimization:
- Bulk loading with in-memory caching
- Batch processing for large datasets
- Safe contact enrichment (never overwrites primary data)
- Data provenance tracking

Performance Optimizations:
1. Pre-load all contact emails → IDs into memory
2. Cache product lookups
3. Batch database operations
4. Reduce round-trips to database

Usage:
  # Dry-run
  python3 scripts/import_kajabi_transactions_optimized.py \\
    --file "kajabi 3 files review/transactions (2).csv" \\
    --dry-run

  # Execute
  python3 scripts/import_kajabi_transactions_optimized.py \\
    --file "kajabi 3 files review/transactions (2).csv" \\
    --execute
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor, Json, execute_values
import re

# Configuration
BATCH_SIZE = 500

def parse_kajabi_date(date_str: str) -> Optional[datetime]:
    """Parse Kajabi date: '2025-11-08 04:11:00 -0700'"""
    if not date_str:
        return None
    try:
        date_part = date_str.rsplit(' ', 1)[0]
        return datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
    except:
        return None

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone, keep original format"""
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    return phone.strip() if len(digits) >= 10 else None

def normalize_email(email: str) -> Optional[str]:
    """Normalize email"""
    if not email:
        return None
    return email.strip().lower()

def load_contact_cache(cur) -> Dict[str, Dict]:
    """Pre-load ALL contacts into memory for fast lookup"""
    print("  Loading contact cache...")
    cur.execute("""
        SELECT id, email, phone, address_line_1,
               phone_source, billing_address_source
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    cache = {}
    for row in cur.fetchall():
        cache[row['email'].lower()] = {
            'id': row['id'],
            'email': row['email'],
            'phone': row['phone'],
            'address_line_1': row['address_line_1'],
            'phone_source': row['phone_source'],
            'billing_address_source': row['billing_address_source']
        }

    print(f"  ✓ Loaded {len(cache):,} contacts into cache")
    return cache

def load_product_cache(cur) -> Dict[str, str]:
    """Pre-load products by kajabi_offer_id"""
    print("  Loading product cache...")
    cur.execute("""
        SELECT id, kajabi_offer_id
        FROM products
        WHERE kajabi_offer_id IS NOT NULL
    """)

    cache = {}
    for row in cur.fetchall():
        cache[row['kajabi_offer_id']] = row['id']

    print(f"  ✓ Loaded {len(cache):,} products into cache")
    return cache

def load_existing_transactions(cur) -> Set[str]:
    """Load set of existing transaction IDs"""
    print("  Loading existing transactions...")
    cur.execute("""
        SELECT external_transaction_id
        FROM transactions
        WHERE source_system = 'kajabi'
        AND external_transaction_id IS NOT NULL
    """)

    existing = {row[0] for row in cur.fetchall()}
    print(f"  ✓ Found {len(existing):,} existing Kajabi transactions")
    return existing

def create_products_batch(cur, offers: Dict[str, str], dry_run=False) -> Dict[str, str]:
    """Create multiple products at once"""
    if not offers or dry_run:
        return {offer_id: f"[DRY-RUN-{offer_id}]" for offer_id in offers}

    # Insert all products
    product_ids = {}
    for offer_id, offer_title in offers.items():
        # Check if exists by offer_id
        cur.execute("""
            SELECT id FROM products
            WHERE kajabi_offer_id = %s
        """, (offer_id,))

        result = cur.fetchone()
        if result:
            product_ids[offer_id] = result['id']
        else:
            # Check if exists by normalized name
            cur.execute("""
                SELECT id, kajabi_offer_id FROM products
                WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
            """, (offer_title,))

            result = cur.fetchone()
            if result:
                # Update with kajabi_offer_id if missing
                if not result['kajabi_offer_id']:
                    cur.execute("""
                        UPDATE products
                        SET kajabi_offer_id = %s
                        WHERE id = %s
                    """, (offer_id, result['id']))
                product_ids[offer_id] = result['id']
            else:
                # Insert new product
                try:
                    cur.execute("""
                        INSERT INTO products (name, kajabi_offer_id)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (offer_title, offer_id))

                    result = cur.fetchone()
                    if result:
                        product_ids[offer_id] = result['id']
                except psycopg2.errors.UniqueViolation:
                    # Race condition or duplicate - fetch the existing one
                    cur.execute("""
                        SELECT id FROM products
                        WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
                        OR kajabi_offer_id = %s
                    """, (offer_title, offer_id))
                    result = cur.fetchone()
                    if result:
                        product_ids[offer_id] = result['id']

    return product_ids

def prepare_contact_enrichments(transactions: List[Dict], contact_cache: Dict) -> Dict[str, Dict]:
    """
    Prepare contact enrichments (SAFE - only empty fields)

    Returns dict of contact_id → updates
    """
    enrichments = {}

    for txn in transactions:
        email = normalize_email(txn.get('email'))
        if not email or email not in contact_cache:
            continue

        contact = contact_cache[email]
        contact_id = contact['id']

        updates = {}

        # Phone enrichment - ONLY if empty
        txn_phone = normalize_phone(txn.get('phone'))
        if txn_phone and not contact['phone']:
            updates['phone'] = txn_phone
            updates['phone_source'] = 'kajabi_transaction'

        # Address enrichment - ONLY if empty
        txn_address = txn.get('address', '').strip()
        if txn_address and not contact['address_line_1']:
            updates['address_line_1'] = txn_address[:200]

            address_2 = txn.get('address_2', '').strip()
            if address_2:
                updates['address_line_2'] = address_2[:200]

            city = txn.get('city', '').strip()
            if city:
                updates['city'] = city[:100]

            state = txn.get('state', '').strip()
            if state:
                updates['state'] = state[:50]

            postal = txn.get('postal', '').strip()
            if postal:
                updates['postal_code'] = postal[:20]

            country = txn.get('country', '').strip()
            if country:
                updates['country'] = country[:50]

            updates['billing_address_source'] = 'kajabi_transaction'

        if updates:
            enrichments[contact_id] = updates

    return enrichments

def apply_contact_enrichments(cur, enrichments: Dict[str, Dict], dry_run=False) -> Tuple[int, int]:
    """Apply contact enrichments in batch"""
    if not enrichments or dry_run:
        phones = sum(1 for e in enrichments.values() if 'phone' in e)
        addresses = sum(1 for e in enrichments.values() if 'address_line_1' in e)
        return phones, addresses

    phones = 0
    addresses = 0

    for contact_id, updates in enrichments.items():
        if 'phone' in updates:
            phones += 1
        if 'address_line_1' in updates:
            addresses += 1

        set_clauses = [f"{key} = %s" for key in updates.keys()]
        set_clauses.append("updated_at = NOW()")
        values = list(updates.values()) + [contact_id]

        cur.execute(f"""
            UPDATE contacts
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """, values)

    return phones, addresses

def prepare_transactions(rows: List[Dict], contact_cache: Dict,
                        product_cache: Dict, existing_txns: Set[str]) -> Tuple[List, Set[Tuple]]:
    """
    Prepare transaction data for bulk insert

    Returns (transaction_values, new_products_needed)
    """
    transaction_values = []
    new_products = set()  # (offer_id, offer_title)

    for row in rows:
        transaction_id = row.get('ID', '').strip()
        email = normalize_email(row.get('email', ''))

        # Skip if already exists or invalid
        if not transaction_id or not email:
            continue
        if transaction_id in existing_txns:
            continue

        # Check if contact exists
        if email not in contact_cache:
            continue

        contact_id = contact_cache[email]['id']

        # Find or queue product creation
        offer_id = row.get('Offer ID', '').strip()
        offer_title = row.get('Offer Title', '').strip() or 'Unknown Offer'

        product_id = None
        if offer_id:
            if offer_id in product_cache:
                product_id = product_cache[offer_id]
            else:
                new_products.add((offer_id, offer_title))

        # Parse transaction data
        amount = Decimal(row.get('Amount', '0') or '0')
        currency = row.get('Currency', 'USD').strip() or 'USD'
        txn_type = row.get('Type', 'unknown').strip().lower()
        status = row.get('Status', 'unknown').strip().lower()
        payment_method = row.get('Payment Method', '').strip() or 'unknown'
        created_at = parse_kajabi_date(row.get('Created At', '')) or datetime.now()

        # Map types (valid: purchase, subscription, refund, adjustment)
        type_map = {
            'subscription': 'subscription',
            'charge': 'purchase',
            'payment plan': 'purchase',  # Payment plans are purchases
            'refund': 'refund'
        }
        mapped_type = type_map.get(txn_type, 'purchase')

        status_map = {
            'succeeded': 'completed',
            'failed': 'failed',
            'pending': 'pending'
        }
        mapped_status = status_map.get(status, status)

        # Store transaction data
        transaction_values.append((
            contact_id,
            transaction_id,
            row.get('Order No.', '').strip() or None,
            created_at,
            mapped_type,
            mapped_status,
            amount,
            currency,
            payment_method,
            row.get('Provider', 'Kajabi').strip(),
            product_id,  # Will be None if new product
            offer_id if not product_id else None,  # Store offer_id temporarily
            Json({
                'customer_id': row.get('Customer ID'),
                'customer_name': row.get('Customer Name'),
                'offer_id': offer_id,
                'offer_title': offer_title,
                'coupon_used': row.get('Coupon Used'),
                'card_brand': row.get('Card Brand'),
                'card_funding': row.get('Card Funding'),
                'tax_amount': row.get('Tax Amount'),
                'quantity': row.get('Quantity'),
                'charge_attempt': row.get('Charge Attempt'),
                'failure_message': row.get('Failure Message')
            })
        ))

    return transaction_values, new_products

def insert_transactions_batch(cur, transaction_values: List, product_cache: Dict, dry_run=False) -> int:
    """Insert transactions in batch"""
    if not transaction_values or dry_run:
        return len(transaction_values)

    # Update product_ids for transactions with new products
    final_values = []
    for values in transaction_values:
        values_list = list(values)
        offer_id = values_list[11]  # Temporary offer_id

        if offer_id and offer_id in product_cache:
            values_list[10] = product_cache[offer_id]  # Set product_id

        values_list[11] = None  # Remove temporary offer_id
        final_values.append(tuple(values_list[:11] + values_list[12:]))  # Skip offer_id field

    # Bulk insert
    execute_values(cur, """
        INSERT INTO transactions (
            contact_id, external_transaction_id, external_order_id,
            transaction_date, transaction_type, status, amount, currency,
            payment_method, payment_processor, product_id, source_system, raw_source
        ) VALUES %s
    """, [(v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9], v[10], 'kajabi', v[11])
          for v in final_values])

    return len(final_values)

def main():
    parser = argparse.ArgumentParser(
        description='Import Kajabi transactions (OPTIMIZED)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--file', required=True, help='Path to Kajabi transactions CSV')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run (no changes)')
    parser.add_argument('--execute', action='store_true', help='Execute import')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)

    dry_run = args.dry_run

    print("=" * 80)
    print("KAJABI TRANSACTIONS IMPORT (OPTIMIZED)")
    print("=" * 80)
    print(f"File: {args.file}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    if not dry_run:
        print("\n⚠️  EXECUTE MODE - Changes will be made!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n")

    stats = {
        'total_rows': 0,
        'transactions_imported': 0,
        'transactions_skipped': 0,
        'contacts_enriched_phone': 0,
        'contacts_enriched_address': 0,
        'products_created': 0,
        'errors': 0
    }

    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.set_session(autocommit=False)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Step 1: Pre-load all caches
            print("\n" + "=" * 80)
            print("STEP 1: LOADING CACHES")
            print("=" * 80)

            contact_cache = load_contact_cache(cur)
            product_cache = load_product_cache(cur)
            existing_txns = load_existing_transactions(cur)

            # Step 2: Read and prepare all transactions
            print("\n" + "=" * 80)
            print("STEP 2: READING TRANSACTIONS FILE")
            print("=" * 80)

            all_rows = []
            with open(args.file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_rows.append({
                        'ID': row.get('ID'),
                        'email': row.get('Customer Email'),
                        'phone': row.get('Phone'),
                        'address': row.get('Address'),
                        'address_2': row.get('Address 2'),
                        'city': row.get('City'),
                        'state': row.get('State'),
                        'postal': row.get('Zipcode'),
                        'country': row.get('Country'),
                        'Amount': row.get('Amount'),
                        'Currency': row.get('Currency'),
                        'Type': row.get('Type'),
                        'Status': row.get('Status'),
                        'Payment Method': row.get('Payment Method'),
                        'Created At': row.get('Created At'),
                        'Offer ID': row.get('Offer ID'),
                        'Offer Title': row.get('Offer Title'),
                        'Order No.': row.get('Order No.'),
                        'Provider': row.get('Provider'),
                        'Customer ID': row.get('Customer ID'),
                        'Customer Name': row.get('Customer Name'),
                        'Coupon Used': row.get('Coupon Used'),
                        'Card Brand': row.get('Card Brand'),
                        'Card Funding': row.get('Card Funding'),
                        'Tax Amount': row.get('Tax Amount'),
                        'Quantity': row.get('Quantity'),
                        'Charge Attempt': row.get('Charge Attempt'),
                        'Failure Message': row.get('Failure Message')
                    })

            stats['total_rows'] = len(all_rows)
            print(f"  ✓ Read {stats['total_rows']:,} transactions")

            # Step 3: Prepare enrichments
            print("\n" + "=" * 80)
            print("STEP 3: PREPARING CONTACT ENRICHMENTS")
            print("=" * 80)

            enrichments = prepare_contact_enrichments(all_rows, contact_cache)
            print(f"  ✓ Found {len(enrichments):,} contacts to enrich")

            # Step 4: Prepare transactions
            print("\n" + "=" * 80)
            print("STEP 4: PREPARING TRANSACTIONS")
            print("=" * 80)

            transaction_values, new_products = prepare_transactions(
                all_rows, contact_cache, product_cache, existing_txns
            )
            print(f"  ✓ Prepared {len(transaction_values):,} transactions to import")
            print(f"  ✓ Found {len(new_products):,} new products to create")

            stats['transactions_skipped'] = stats['total_rows'] - len(transaction_values)

            # Step 5: Create new products
            if new_products:
                print("\n" + "=" * 80)
                print("STEP 5: CREATING NEW PRODUCTS")
                print("=" * 80)

                new_product_dict = dict(new_products)
                new_product_ids = create_products_batch(cur, new_product_dict, dry_run)
                product_cache.update(new_product_ids)
                stats['products_created'] = len(new_products)
                print(f"  ✓ Created {stats['products_created']:,} products")

            # Step 6: Apply enrichments
            print("\n" + "=" * 80)
            print("STEP 6: ENRICHING CONTACTS")
            print("=" * 80)

            phones, addresses = apply_contact_enrichments(cur, enrichments, dry_run)
            stats['contacts_enriched_phone'] = phones
            stats['contacts_enriched_address'] = addresses
            print(f"  ✓ Enriched {phones:,} contacts with phone")
            print(f"  ✓ Enriched {addresses:,} contacts with address")

            # Step 7: Insert transactions
            print("\n" + "=" * 80)
            print("STEP 7: INSERTING TRANSACTIONS")
            print("=" * 80)

            imported = insert_transactions_batch(cur, transaction_values, product_cache, dry_run)
            stats['transactions_imported'] = imported
            print(f"  ✓ Inserted {imported:,} transactions")

            # Commit or rollback
            if dry_run:
                conn.rollback()
                print("\n✓ DRY-RUN: All changes rolled back")
            else:
                conn.commit()
                print("\n✓ COMMITTED: All changes saved")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()

    # Print summary
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total rows: {stats['total_rows']:,}")
    print(f"Transactions imported: {stats['transactions_imported']:,}")
    print(f"Transactions skipped: {stats['transactions_skipped']:,}")
    print(f"Products created: {stats['products_created']:,}")
    print(f"Contacts enriched:")
    print(f"  └─ Phone: {stats['contacts_enriched_phone']:,}")
    print(f"  └─ Address: {stats['contacts_enriched_address']:,}")
    print("=" * 80)

    if dry_run:
        print("\n✓ To execute, run with --execute flag")

if __name__ == '__main__':
    main()
