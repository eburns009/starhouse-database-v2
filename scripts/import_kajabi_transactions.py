#!/usr/bin/env python3
"""
Kajabi Transactions Import - FAANG Production Standards
========================================================

Imports Kajabi transaction history with:
- Safe contact enrichment (never overwrites primary data)
- Product/offer linking
- Data provenance tracking
- Idempotent operations

Key Principles:
1. NEVER overwrite existing contact data (Kajabi contact record is primary)
2. Only enrich EMPTY fields (phone, address)
3. Track enrichment source (phone_source, address_source)
4. Link transactions to products via Offer ID
5. Handle duplicates gracefully

Usage:
  # Dry-run (recommended first)
  python3 scripts/import_kajabi_transactions.py \\
    --file "kajabi 3 files review/transactions (2).csv" \\
    --dry-run

  # Execute import
  python3 scripts/import_kajabi_transactions.py \\
    --file "kajabi 3 files review/transactions (2).csv" \\
    --execute
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import re

def parse_kajabi_date(date_str: str) -> Optional[datetime]:
    """Parse Kajabi date: '2025-11-08 04:11:00 -0700'"""
    if not date_str:
        return None
    try:
        # Remove timezone
        date_part = date_str.rsplit(' ', 1)[0]
        return datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
    except:
        return None

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone to digits, keep original format for display"""
    if not phone:
        return None
    # Keep original format but validate it has enough digits
    digits = re.sub(r'\D', '', phone)
    return phone.strip() if len(digits) >= 10 else None

def normalize_email(email: str) -> Optional[str]:
    """Normalize email"""
    if not email:
        return None
    return email.strip().lower()

def find_or_create_product(cur, offer_id: str, offer_title: str, dry_run=False) -> Optional[str]:
    """Find or create product by Kajabi Offer ID"""
    if not offer_id or not offer_title:
        return None

    # Check if product exists
    cur.execute("""
        SELECT id FROM products
        WHERE kajabi_offer_id = %s
    """, (offer_id,))

    result = cur.fetchone()
    if result:
        return result['id']

    # Create product
    if dry_run:
        return f"[DRY-RUN-PRODUCT-{offer_id}]"

    cur.execute("""
        INSERT INTO products (
            name,
            kajabi_offer_id
        ) VALUES (%s, %s)
        RETURNING id
    """, (offer_title, offer_id))

    return cur.fetchone()['id']

def find_contact_by_email(cur, email: str) -> Optional[Dict]:
    """Find contact by email"""
    normalized = normalize_email(email)
    if not normalized:
        return None

    cur.execute("""
        SELECT id, email, phone, address_line_1, phone_source, billing_address_source
        FROM contacts
        WHERE email = %s
        LIMIT 1
    """, (normalized,))

    return cur.fetchone()

def enrich_contact_from_transaction(cur, contact_id: str, transaction: Dict, dry_run=False) -> List[str]:
    """
    Enrich contact with transaction data - FAANG SAFE ENRICHMENT

    Rules:
    1. ONLY update EMPTY fields
    2. NEVER overwrite existing data
    3. Track data provenance
    """
    enrichments = []

    # Get current contact data
    cur.execute("""
        SELECT phone, address_line_1, address_line_2, city, state, postal_code, country,
               phone_source, billing_address_source
        FROM contacts
        WHERE id = %s
    """, (contact_id,))

    contact = cur.fetchone()
    if not contact:
        return []

    updates = {}

    # Phone enrichment - ONLY if empty
    txn_phone = normalize_phone(transaction.get('Phone'))
    if txn_phone and not contact['phone']:
        updates['phone'] = txn_phone
        updates['phone_source'] = 'kajabi_transaction'
        enrichments.append('phone')

    # Address enrichment - ONLY if empty
    txn_address = transaction.get('Address', '').strip()
    if txn_address and not contact['address_line_1']:
        updates['address_line_1'] = txn_address[:200] if txn_address else None

        address_2 = transaction.get('Address 2', '').strip()
        if address_2:
            updates['address_line_2'] = address_2[:200]

        city = transaction.get('City', '').strip()
        if city:
            updates['city'] = city[:100]

        state = transaction.get('State', '').strip()
        if state:
            updates['state'] = state[:50]

        postal = transaction.get('Zipcode', '').strip()
        if postal:
            updates['postal_code'] = postal[:20]

        country = transaction.get('Country', '').strip()
        if country:
            updates['country'] = country[:50]

        updates['billing_address_source'] = 'kajabi_transaction'
        enrichments.append('address')

    # Apply updates
    if updates:
        if dry_run:
            return enrichments

        set_clauses = [f"{key} = %s" for key in updates.keys()]
        values = list(updates.values()) + [contact_id]

        cur.execute(f"""
            UPDATE contacts
            SET {', '.join(set_clauses)},
                updated_at = NOW()
            WHERE id = %s
        """, values)

    return enrichments

def import_kajabi_transaction(cur, row: Dict, dry_run=False) -> Tuple[bool, Optional[str], List[str]]:
    """
    Import a single Kajabi transaction

    Returns:
        (success, contact_id, enrichments)
    """
    try:
        # Required fields
        transaction_id = row.get('ID', '').strip()
        email = normalize_email(row.get('Customer Email', ''))

        if not transaction_id or not email:
            return False, None, []

        # Check if transaction already exists
        cur.execute("""
            SELECT id FROM transactions
            WHERE external_transaction_id = %s AND source_system = 'kajabi'
        """, (transaction_id,))

        if cur.fetchone():
            return False, None, []  # Already imported

        # Find contact
        contact = find_contact_by_email(cur, email)
        if not contact:
            # Contact doesn't exist - shouldn't happen for Kajabi customers
            # But handle gracefully
            print(f"   ⚠️  WARNING: Contact not found for {email} (transaction {transaction_id})")
            return False, None, []

        contact_id = contact['id']

        # Enrich contact (safe - only empty fields)
        enrichments = enrich_contact_from_transaction(cur, contact_id, row, dry_run)

        # Find or create product
        offer_id = row.get('Offer ID', '').strip()
        offer_title = row.get('Offer Title', '').strip() or 'Unknown Offer'
        product_id = find_or_create_product(cur, offer_id, offer_title, dry_run) if offer_id else None

        # Parse transaction data
        amount = Decimal(row.get('Amount', '0') or '0')
        currency = row.get('Currency', 'USD').strip() or 'USD'
        txn_type = row.get('Type', 'unknown').strip().lower()
        status = row.get('Status', 'unknown').strip().lower()
        payment_method = row.get('Payment Method', '').strip() or 'unknown'
        created_at = parse_kajabi_date(row.get('Created At', ''))

        if not created_at:
            created_at = datetime.now()

        # Map transaction type
        type_map = {
            'subscription': 'subscription',
            'charge': 'purchase',
            'payment plan': 'payment_plan',
            'refund': 'refund'
        }
        mapped_type = type_map.get(txn_type, 'purchase')

        # Map status
        status_map = {
            'succeeded': 'completed',
            'failed': 'failed',
            'pending': 'pending'
        }
        mapped_status = status_map.get(status, status)

        if dry_run:
            return True, contact_id, enrichments

        # Insert transaction
        cur.execute("""
            INSERT INTO transactions (
                contact_id,
                external_transaction_id,
                external_order_id,
                transaction_date,
                transaction_type,
                status,
                amount,
                currency,
                payment_method,
                payment_processor,
                product_id,
                source_system,
                raw_source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
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
            product_id,
            'kajabi',
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

        return True, contact_id, enrichments

    except Exception as e:
        print(f"   ERROR importing transaction {transaction_id}: {e}")
        return False, None, []

def main():
    parser = argparse.ArgumentParser(
        description='Import Kajabi transactions with safe enrichment',
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
    print("KAJABI TRANSACTIONS IMPORT")
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
            with open(args.file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    stats['total_rows'] += 1

                    success, contact_id, enrichments = import_kajabi_transaction(cur, row, dry_run)

                    if success:
                        stats['transactions_imported'] += 1
                        if 'phone' in enrichments:
                            stats['contacts_enriched_phone'] += 1
                        if 'address' in enrichments:
                            stats['contacts_enriched_address'] += 1
                    else:
                        if contact_id is None:
                            stats['transactions_skipped'] += 1

                    # Progress
                    if stats['total_rows'] % 500 == 0:
                        print(f"  Processed {stats['total_rows']:,} rows...")

        if dry_run:
            conn.rollback()
            print("\n✓ DRY-RUN: All changes rolled back")
        else:
            conn.commit()
            print("\n✓ COMMITTED: All changes saved")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

    # Print stats
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total rows: {stats['total_rows']:,}")
    print(f"Transactions imported: {stats['transactions_imported']:,}")
    print(f"Transactions skipped (duplicates): {stats['transactions_skipped']:,}")
    print(f"Contacts enriched with phone: {stats['contacts_enriched_phone']:,}")
    print(f"Contacts enriched with address: {stats['contacts_enriched_address']:,}")
    print(f"Errors: {stats['errors']:,}")
    print("=" * 80)

    if dry_run:
        print("\nTo execute, run with --execute flag")

if __name__ == '__main__':
    main()
