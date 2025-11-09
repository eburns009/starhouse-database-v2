#!/usr/bin/env python3
"""
WEEKLY PAYPAL IMPORT - Optimized for Manual Weekly Updates
===========================================================

Purpose: Import weekly PayPal transaction exports to keep database synchronized

What it imports:
  1. NEW transactions (completed payments, refunds)
  2. NEW contacts from transactions
  3. ENRICHMENT data (addresses, phone numbers, business names)
  4. SUBSCRIPTION tracking (from recurring payments)

Usage:
  # Dry-run first (recommended)
  python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --dry-run

  # Execute import
  python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --execute

Required File from PayPal:
  - PayPal transaction export (tab-delimited .txt or .tsv)

Export Instructions:
  1. Log into PayPal Business account
  2. Go to Activity → Statements → Custom
  3. Select date range (last 7-14 days for weekly import)
  4. Download: "All activity" → Tab-delimited format
  5. Save as: data/paypal_export_YYYY_MM_DD.txt
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONNECTION = os.environ.get(
    'DATABASE_URL',
    'postgres://***REMOVED***:***REMOVED***@***REMOVED***:6543/postgres'
)

# ============================================================================
# HELPERS
# ============================================================================

def normalize_email(email: str) -> Optional[str]:
    """Normalize email"""
    return email.strip().lower() if email else None

def parse_name(name_str: str) -> tuple:
    """Parse 'Last, First' or 'Business Name' format"""
    if not name_str:
        return None, None

    # Check if it's "Last, First" format
    if ',' in name_str:
        parts = name_str.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip() if len(parts) > 1 else ''
        return first_name, last_name
    else:
        # Assume it's first name or business name
        return name_str.strip(), None

def parse_date_time(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse PayPal date/time format: MM/DD/YYYY HH:MM:SS"""
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S")
    except:
        return None

def is_business_name(name: str) -> bool:
    """Check if name looks like a business"""
    business_keywords = ['llc', 'inc', 'institute', 'company', 'corp', 'center',
                        'foundation', 'studio', 'group', 'services', 'consulting']
    return any(keyword in name.lower() for keyword in business_keywords)

# ============================================================================
# PAYPAL IMPORTER
# ============================================================================

class PayPalImporter:
    def __init__(self, connection_string: str, dry_run: bool = True):
        self.conn = psycopg2.connect(connection_string)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.dry_run = dry_run
        self.stats = {
            'rows_processed': 0,
            'transactions_new': 0,
            'transactions_skipped': 0,
            'contacts_created': 0,
            'contacts_enriched': 0,
            'contacts_matched': 0,
            'errors': []
        }
        self.membership_products_cache = {}
        self.load_membership_products()

    def load_membership_products(self):
        """Cache membership products for faster lookup"""
        self.cur.execute("""
            SELECT id, membership_group, membership_level, membership_tier,
                   is_legacy, paypal_item_titles
            FROM membership_products
        """)
        for row in self.cur.fetchall():
            if row['paypal_item_titles']:
                for title in row['paypal_item_titles']:
                    self.membership_products_cache[title.lower()] = row

    def get_membership_product(self, item_title: str) -> Optional[Dict]:
        """Get membership product from PayPal item title"""
        if not item_title:
            return None
        return self.membership_products_cache.get(item_title.lower())

    def find_contact(self, email: str) -> Optional[Dict]:
        """Find contact by email"""
        self.cur.execute("""
            SELECT id, first_name, last_name, phone, paypal_business_name
            FROM contacts
            WHERE email = %s OR paypal_email = %s
            LIMIT 1
        """, (email, email))
        return self.cur.fetchone()

    def create_or_enrich_contact(self, row: Dict) -> Optional[str]:
        """Create or enrich contact from PayPal row"""
        email = normalize_email(row.get('From Email Address'))
        if not email or '@' not in email:
            return None

        # Parse name
        first_name, last_name = parse_name(row.get('Name', ''))

        # Check if it's a business
        business_name = None
        if row.get('Name') and is_business_name(row['Name']):
            business_name = row['Name']

        # Find existing contact
        contact = self.find_contact(email)

        # Extract phone (clean it up)
        phone = row.get('Contact Phone Number', '').strip()

        # Get membership info if this is a subscription payment
        membership_group = None
        membership_level = None
        membership_tier = None
        is_legacy = False

        if row.get('Type') == 'Subscription Payment' and row.get('Item Title'):
            product = self.get_membership_product(row['Item Title'])
            if product:
                membership_group = product['membership_group']
                membership_level = product['membership_level']
                membership_tier = product['membership_tier']
                is_legacy = product['is_legacy']

        if contact:
            # Enrich existing contact
            updates = []
            params = []

            # Only update fields that are empty
            if not contact.get('paypal_business_name') and business_name:
                updates.append("paypal_business_name = %s")
                params.append(business_name)

            if not contact.get('phone') and phone:
                updates.append("phone = %s")
                params.append(phone)

            # Always update these PayPal-specific fields
            updates.append("paypal_email = %s")
            params.append(email)

            if first_name:
                updates.append("paypal_first_name = %s")
                params.append(first_name)

            if last_name:
                updates.append("paypal_last_name = %s")
                params.append(last_name)

            if phone:
                updates.append("paypal_phone = %s")
                params.append(phone)

            # Update addresses if provided
            if row.get('Address Line 1'):
                updates.append("shipping_address_line_1 = %s")
                params.append(row['Address Line 1'])

            if row.get('Town/City'):
                updates.append("shipping_city = %s")
                params.append(row['Town/City'])

            if row.get('State/Province/Region/County/Territory/Prefecture/Republic'):
                updates.append("shipping_state = %s")
                params.append(row['State/Province/Region/County/Territory/Prefecture/Republic'])

            if row.get('Zip/Postal Code'):
                updates.append("shipping_postal_code = %s")
                params.append(row['Zip/Postal Code'])

            if row.get('Country'):
                updates.append("shipping_country = %s")
                params.append(row['Country'])

            # Update membership info if found
            if membership_group:
                updates.append("membership_group = %s")
                params.append(membership_group)
            if membership_level:
                updates.append("membership_level = %s")
                params.append(membership_level)
            if membership_tier:
                updates.append("membership_tier = %s")
                params.append(membership_tier)

            updates.append("updated_at = NOW()")
            params.append(contact['id'])

            if updates and not self.dry_run:
                query = f"UPDATE contacts SET {', '.join(updates)} WHERE id = %s"
                self.cur.execute(query, params)

            self.stats['contacts_enriched'] += 1
            self.stats['contacts_matched'] += 1
            return contact['id']

        else:
            # Create new contact
            if not self.dry_run:
                self.cur.execute("""
                    INSERT INTO contacts (
                        email, first_name, last_name,
                        paypal_email, paypal_first_name, paypal_last_name,
                        paypal_business_name, phone, paypal_phone,
                        shipping_address_line_1, shipping_city, shipping_state,
                        shipping_postal_code, shipping_country,
                        membership_group, membership_level, membership_tier,
                        is_legacy_member, source_system, email_subscribed,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    RETURNING id
                """, (
                    email, first_name, last_name,
                    email, first_name, last_name,
                    business_name, phone, phone,
                    row.get('Address Line 1'),
                    row.get('Town/City'),
                    row.get('State/Province/Region/County/Territory/Prefecture/Republic'),
                    row.get('Zip/Postal Code'),
                    row.get('Country'),
                    membership_group, membership_level, membership_tier,
                    is_legacy, 'manual', True
                ))
                result = self.cur.fetchone()
                contact_id = result['id'] if result else None
            else:
                contact_id = 'dry-run-contact-id'

            self.stats['contacts_created'] += 1
            return contact_id

    def create_transaction(self, row: Dict, contact_id: str):
        """Create transaction from PayPal row"""
        # Only import completed or refunded transactions
        if row.get('Status') not in ['Completed', 'Refunded']:
            return

        # Parse amount
        try:
            amount = Decimal(row['Gross'].replace(',', ''))
        except:
            self.stats['errors'].append(f"Invalid amount for txn {row.get('Transaction ID')}")
            return

        # Parse date/time
        transaction_date = parse_date_time(row.get('Date', ''), row.get('Time', ''))
        if not transaction_date:
            transaction_date = datetime.now()

        # Determine transaction type
        txn_type = row.get('Type', '')
        if txn_type == 'Subscription Payment':
            transaction_type = 'subscription'
        elif 'Refund' in txn_type or amount < 0:
            transaction_type = 'refund'
        else:
            transaction_type = 'purchase'

        # Map status
        status = 'completed' if row.get('Status') == 'Completed' else 'refunded'

        if not self.dry_run:
            try:
                self.cur.execute("""
                    INSERT INTO transactions (
                        contact_id, source_system,
                        external_transaction_id, external_order_id, order_number,
                        transaction_type, status,
                        amount, currency,
                        payment_method, payment_processor,
                        transaction_date,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (source_system, external_transaction_id)
                    WHERE external_transaction_id IS NOT NULL
                    DO NOTHING
                """, (
                    contact_id, 'paypal',
                    row.get('Transaction ID'),
                    row.get('Invoice Number') or row.get('Transaction ID'),
                    row.get('Receipt ID') or row.get('Transaction ID'),
                    transaction_type, status,
                    amount, row.get('Currency', 'USD'),
                    'paypal', 'PayPal',
                    transaction_date
                ))
                # Check if row was actually inserted
                if self.cur.rowcount > 0:
                    self.stats['transactions_new'] += 1
                else:
                    self.stats['transactions_skipped'] += 1
            except Exception as e:
                self.stats['errors'].append(f"Transaction {row.get('Transaction ID')}: {str(e)}")
        else:
            self.stats['transactions_new'] += 1

    def import_file(self, filepath: str):
        """Import PayPal export file"""
        print(f"\n{'='*80}")
        print(f"PAYPAL TRANSACTIONS IMPORT - {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"{'='*80}\n")

        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            sys.exit(1)

        print(f"📄 Reading: {filepath}")

        # Read tab-delimited file
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)

        print(f"📊 Found {len(rows)} transactions to process\n")

        for i, row in enumerate(rows):
            self.stats['rows_processed'] += 1

            if i > 0 and i % 100 == 0:
                print(f"  Progress: {i}/{len(rows)} rows...", end='\r')

            try:
                # Create or enrich contact
                contact_id = self.create_or_enrich_contact(row)

                if contact_id:
                    # Create transaction
                    self.create_transaction(row, contact_id)

            except Exception as e:
                self.stats['errors'].append(f"Row {i}: {str(e)}")

        print(f"\n")

    def commit_or_rollback(self):
        """Commit or rollback transaction"""
        if self.dry_run:
            self.conn.rollback()
            print("\n🔄 DRY RUN - No changes made to database")
        else:
            self.conn.commit()
            print("\n✅ Changes committed to database")

    def print_stats(self):
        """Print import statistics"""
        print(f"\n{'='*80}")
        print("IMPORT SUMMARY")
        print(f"{'='*80}\n")

        print(f"📊 Rows Processed: {self.stats['rows_processed']}")

        print(f"\n💰 Transactions:")
        print(f"  New: {self.stats['transactions_new']}")
        print(f"  Skipped (duplicates): {self.stats['transactions_skipped']}")

        print(f"\n📇 Contacts:")
        print(f"  Matched existing: {self.stats['contacts_matched']}")
        print(f"  Created new: {self.stats['contacts_created']}")
        print(f"  Enriched: {self.stats['contacts_enriched']}")

        if self.stats['errors']:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print(f"\n{'='*80}\n")

    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Weekly PayPal Import - Optimized for manual weekly updates'
    )
    parser.add_argument('--file', required=True, help='Path to PayPal export file (tab-delimited)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without committing')
    parser.add_argument('--execute', action='store_true', help='Execute import (make changes)')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Error: Must specify either --dry-run or --execute")
        print("\nExamples:")
        print("  python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --dry-run")
        print("  python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --execute")
        sys.exit(1)

    # Create importer
    importer = PayPalImporter(DB_CONNECTION, dry_run=args.dry_run)

    try:
        # Import file
        importer.import_file(args.file)

        # Commit or rollback
        importer.commit_or_rollback()

        # Print stats
        importer.print_stats()

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()

if __name__ == '__main__':
    main()
