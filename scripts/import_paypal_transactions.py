#!/usr/bin/env python3
"""
PayPal Transaction Import Script
==================================
Imports PayPal transaction data and enriches contact records with:
- Business names
- Complete shipping addresses
- Phone numbers
- Membership levels
- Subscription tracking

Usage:
    python3 scripts/import_paypal_transactions.py --file data/Paypal_Import --dry-run
    python3 scripts/import_paypal_transactions.py --file data/Paypal_Import --execute
"""

import csv
import sys
import os
import argparse
from datetime import datetime
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor

# Database connection string
DB_CONNECTION = os.environ.get(
    'DATABASE_URL',
    'postgresql://***REMOVED***:***REMOVED***@***REMOVED***:6543/postgres'
)

class PayPalImporter:
    def __init__(self, connection_string, dry_run=True, corrections_file=None):
        self.conn = psycopg2.connect(connection_string)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self.dry_run = dry_run
        self.corrections = {}
        self.stats = {
            'rows_processed': 0,
            'contacts_matched': 0,
            'contacts_created': 0,
            'contacts_updated': 0,
            'transactions_created': 0,
            'subscriptions_created': 0,
            'subscriptions_updated': 0,
            'corrections_applied': 0,
            'errors': []
        }

        # Load corrections file if provided
        if corrections_file and os.path.exists(corrections_file):
            self.load_corrections(corrections_file)

    def load_corrections(self, filepath):
        """Load Program Partner corrections from CSV"""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row['email'].strip().lower()
                self.corrections[email] = {
                    'group': row['correct_group'],
                    'level': row['correct_level'],
                    'notes': row.get('notes', ''),
                    'source': row.get('source', 'manual')
                }
        print(f"\n✅ Loaded {len(self.corrections)} Program Partner corrections from {filepath}")

    def normalize_email(self, email):
        """Normalize email to lowercase and strip whitespace"""
        if not email:
            return None
        return email.strip().lower()

    def parse_name(self, name_str):
        """Parse 'Last, First' format name"""
        if not name_str:
            return None, None
        parts = name_str.split(',', 1)
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
            return first_name, last_name
        elif len(parts) == 1:
            # Assume it's just first name or business name
            return parts[0].strip(), None
        return None, None

    def find_contact_by_email(self, email):
        """Find contact by email (checks both primary and paypal_email)"""
        if not email:
            return None

        self.cursor.execute("""
            SELECT * FROM contacts
            WHERE email = %s OR paypal_email = %s
            LIMIT 1
        """, (email, email))
        return self.cursor.fetchone()

    def find_contact_by_name(self, first_name, last_name):
        """Find contact by name match (fuzzy)"""
        if not first_name or not last_name:
            return None

        self.cursor.execute("""
            SELECT * FROM contacts
            WHERE first_name ILIKE %s AND last_name ILIKE %s
            LIMIT 1
        """, (first_name, last_name))
        return self.cursor.fetchone()

    def get_membership_product(self, item_title):
        """Get membership product from PayPal item title"""
        if not item_title:
            return None

        self.cursor.execute("""
            SELECT * FROM membership_products
            WHERE %s ILIKE ANY(paypal_item_titles)
               OR %s = ANY(paypal_item_titles)
            LIMIT 1
        """, (item_title, item_title))
        return self.cursor.fetchone()

    def create_or_update_contact(self, row):
        """Create or update contact from PayPal row"""
        email = self.normalize_email(row['From Email Address'])
        if not email:
            self.stats['errors'].append(f"No email for transaction {row['Transaction ID']}")
            return None

        # Parse name
        first_name, last_name = self.parse_name(row['Name'])

        # Try to find existing contact
        contact = self.find_contact_by_email(email)

        if not contact and first_name and last_name:
            # Try name match
            contact = self.find_contact_by_name(first_name, last_name)

        # Extract business name (if Name field looks like a business)
        business_name = None
        if row['Name'] and ',' not in row['Name']:
            # Might be a business name
            if any(keyword in row['Name'].lower() for keyword in ['llc', 'inc', 'institute', 'company', 'corp', 'center']):
                business_name = row['Name']

        # PRIORITY 1: Check corrections list FIRST
        correction = self.corrections.get(email)
        if correction:
            membership_group = correction['group']
            membership_level = correction['level']
            membership_tier = 'Partner'  # All Program Partners are 'Partner' tier
            is_legacy = False
            membership_product = None
            self.stats['corrections_applied'] += 1
        # PRIORITY 2: Get membership product from PayPal Item Title
        elif row['Type'] == 'Subscription Payment' and row['Item Title']:
            membership_product = self.get_membership_product(row['Item Title'])
            if membership_product:
                membership_group = membership_product['membership_group']
                membership_level = membership_product['membership_level']
                membership_tier = membership_product['membership_tier']
                is_legacy = membership_product['is_legacy']
            else:
                membership_group = None
                membership_level = None
                membership_tier = None
                is_legacy = False
        else:
            membership_product = None
            membership_group = None
            membership_level = None
            membership_tier = None
            is_legacy = False

        if contact:
            # Update existing contact with PayPal data
            update_data = {
                'paypal_email': email,
                'paypal_first_name': first_name or contact['first_name'],
                'paypal_last_name': last_name or contact['last_name'],
                'paypal_business_name': business_name or contact.get('paypal_business_name'),
                'paypal_phone': row.get('Contact Phone Number') or contact.get('paypal_phone'),
                'shipping_address_line_1': row.get('Address Line 1') or contact.get('shipping_address_line_1'),
                'shipping_address_line_2': row.get('Address Line 2/District/Neighborhood') or contact.get('shipping_address_line_2'),
                'shipping_city': row.get('Town/City') or contact.get('shipping_city'),
                'shipping_state': row.get('State/Province/Region/County/Territory/Prefecture/Republic') or contact.get('shipping_state'),
                'shipping_postal_code': row.get('Zip/Postal Code') or contact.get('shipping_postal_code'),
                'shipping_country': row.get('Country') or contact.get('shipping_country'),
                'shipping_address_status': row.get('Address Status') or contact.get('shipping_address_status'),
                'paypal_subscription_reference': row.get('Reference Txn ID') if row['Type'] == 'Subscription Payment' else contact.get('paypal_subscription_reference'),
                'membership_group': membership_group or contact.get('membership_group'),
                'membership_level': membership_level or contact.get('membership_level'),
                'membership_tier': membership_tier or contact.get('membership_tier'),
                'is_legacy_member': is_legacy or contact.get('is_legacy_member', False),
            }

            # Only update if phone is missing in contact table
            if not contact.get('phone') and row.get('Contact Phone Number'):
                update_data['phone'] = row.get('Contact Phone Number')

            if not self.dry_run:
                self.cursor.execute("""
                    UPDATE contacts SET
                        paypal_email = %s,
                        paypal_first_name = %s,
                        paypal_last_name = %s,
                        paypal_business_name = %s,
                        paypal_phone = %s,
                        phone = COALESCE(phone, %s),
                        shipping_address_line_1 = %s,
                        shipping_address_line_2 = %s,
                        shipping_city = %s,
                        shipping_state = %s,
                        shipping_postal_code = %s,
                        shipping_country = %s,
                        shipping_address_status = %s,
                        paypal_subscription_reference = %s,
                        membership_group = %s,
                        membership_level = %s,
                        membership_tier = %s,
                        is_legacy_member = %s,
                        updated_at = now()
                    WHERE id = %s
                    RETURNING id
                """, (
                    update_data['paypal_email'],
                    update_data['paypal_first_name'],
                    update_data['paypal_last_name'],
                    update_data['paypal_business_name'],
                    update_data['paypal_phone'],
                    row.get('Contact Phone Number'),
                    update_data['shipping_address_line_1'],
                    update_data['shipping_address_line_2'],
                    update_data['shipping_city'],
                    update_data['shipping_state'],
                    update_data['shipping_postal_code'],
                    update_data['shipping_country'],
                    update_data['shipping_address_status'],
                    update_data['paypal_subscription_reference'],
                    update_data['membership_group'],
                    update_data['membership_level'],
                    update_data['membership_tier'],
                    update_data['is_legacy_member'],
                    contact['id']
                ))

            self.stats['contacts_updated'] += 1
            self.stats['contacts_matched'] += 1
            return contact['id']

        else:
            # Create new contact
            if not self.dry_run:
                self.cursor.execute("""
                    INSERT INTO contacts (
                        email, first_name, last_name,
                        paypal_email, paypal_first_name, paypal_last_name,
                        paypal_business_name, paypal_phone, phone,
                        shipping_address_line_1, shipping_address_line_2,
                        shipping_city, shipping_state, shipping_postal_code,
                        shipping_country, shipping_address_status,
                        paypal_subscription_reference,
                        membership_group, membership_level, membership_tier,
                        is_legacy_member,
                        source_system, email_subscribed,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()
                    )
                    RETURNING id
                """, (
                    email, first_name, last_name,
                    email, first_name, last_name,
                    business_name,
                    row.get('Contact Phone Number'),
                    row.get('Contact Phone Number'),
                    row.get('Address Line 1'),
                    row.get('Address Line 2/District/Neighborhood'),
                    row.get('Town/City'),
                    row.get('State/Province/Region/County/Territory/Prefecture/Republic'),
                    row.get('Zip/Postal Code'),
                    row.get('Country'),
                    row.get('Address Status'),
                    row.get('Reference Txn ID') if row['Type'] == 'Subscription Payment' else None,
                    membership_group,
                    membership_level,
                    membership_tier,
                    is_legacy,
                    'manual',  # Source system
                    True  # Email subscribed (they paid, so likely want emails)
                ))
                contact_id = self.cursor.fetchone()['id']
            else:
                contact_id = 'dry-run-id'

            self.stats['contacts_created'] += 1
            return contact_id

    def create_transaction(self, row, contact_id):
        """Create transaction from PayPal row"""
        if row['Status'] not in ['Completed', 'Refunded']:
            return  # Skip non-completed transactions

        # Parse amount
        try:
            amount = float(row['Gross'])
        except (ValueError, TypeError):
            self.stats['errors'].append(f"Invalid amount for transaction {row['Transaction ID']}")
            return

        # Parse date
        try:
            transaction_date = datetime.strptime(f"{row['Date']} {row['Time']}", "%m/%d/%Y %H:%M:%S")
        except (ValueError, TypeError):
            transaction_date = datetime.now()

        # Determine transaction type
        transaction_type = 'purchase'
        if row['Type'] == 'Subscription Payment':
            transaction_type = 'subscription'
        elif row['Type'] in ['Payment Refund', 'Refund']:
            transaction_type = 'refund'

        # Detect refunds by negative amount (PayPal sometimes doesn't mark Type correctly)
        if amount < 0 and transaction_type != 'refund':
            transaction_type = 'refund'

        # Get membership product
        membership_product_id = None
        if row['Item Title']:
            product = self.get_membership_product(row['Item Title'])
            if product:
                membership_product_id = product['id']

        if not self.dry_run:
            self.cursor.execute("""
                INSERT INTO transactions (
                    contact_id,
                    source_system,
                    external_transaction_id,
                    external_order_id,
                    order_number,
                    transaction_type,
                    status,
                    amount,
                    currency,
                    payment_method,
                    payment_processor,
                    transaction_date,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()
                )
                ON CONFLICT (source_system, external_transaction_id) WHERE external_transaction_id IS NOT NULL DO NOTHING
            """, (
                contact_id,
                'paypal',
                row['Transaction ID'],
                row['Invoice Number'] or row['Transaction ID'],
                row['Receipt ID'] or row['Transaction ID'],
                transaction_type,
                'completed' if row['Status'] == 'Completed' else 'refunded',
                amount,
                row['Currency'] or 'USD',
                'paypal',
                'PayPal',
                transaction_date
            ))

        self.stats['transactions_created'] += 1

    def create_or_update_subscription(self, subscription_ref, transactions):
        """Create or update subscription from grouped transactions"""
        if not transactions:
            return

        # Get first and last transaction
        first_txn = transactions[0]
        last_txn = transactions[-1]

        contact_id = first_txn['contact_id']

        # Calculate total amount paid
        total_paid = sum(float(t['Gross']) for t in transactions)
        avg_amount = total_paid / len(transactions)

        # Determine status based on last payment date
        try:
            last_payment_date = datetime.strptime(f"{last_txn['Date']} {last_txn['Time']}", "%m/%d/%Y %H:%M:%S")
            days_since_payment = (datetime.now() - last_payment_date).days

            if days_since_payment < 45:
                status = 'active'
            elif days_since_payment < 60:
                status = 'active'  # Grace period
            else:
                status = 'expired'
        except:
            status = 'active'

        # Get membership product
        membership_product_id = None
        if first_txn['Item Title']:
            product = self.get_membership_product(first_txn['Item Title'])
            if product:
                membership_product_id = product['id']

        # Determine billing cycle from average amount
        if avg_amount < 20:
            billing_cycle = 'Month'
        elif avg_amount < 100:
            billing_cycle = 'Month'
        elif avg_amount < 500:
            billing_cycle = 'Year'
        else:
            billing_cycle = 'Year'

        if not self.dry_run:
            # Check if subscription exists
            self.cursor.execute("""
                SELECT id FROM subscriptions
                WHERE paypal_subscription_reference = %s
                LIMIT 1
            """, (subscription_ref,))

            existing_sub = self.cursor.fetchone()

            if existing_sub:
                # Update existing subscription
                self.cursor.execute("""
                    UPDATE subscriptions SET
                        status = %s,
                        amount = %s,
                        billing_cycle = %s,
                        membership_product_id = %s,
                        updated_at = now()
                    WHERE id = %s
                """, (status, avg_amount, billing_cycle, membership_product_id, existing_sub['id']))
                self.stats['subscriptions_updated'] += 1
            else:
                # Create new subscription
                start_date = datetime.strptime(f"{first_txn['Date']} {first_txn['Time']}", "%m/%d/%Y %H:%M:%S")

                self.cursor.execute("""
                    INSERT INTO subscriptions (
                        contact_id,
                        kajabi_subscription_id,
                        paypal_subscription_reference,
                        membership_product_id,
                        status,
                        amount,
                        currency,
                        billing_cycle,
                        start_date,
                        payment_processor,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now()
                    )
                """, (
                    contact_id,
                    subscription_ref,  # Use as kajabi_subscription_id for now
                    subscription_ref,
                    membership_product_id,
                    status,
                    avg_amount,
                    first_txn['Currency'] or 'USD',
                    billing_cycle,
                    start_date,
                    'PayPal'
                ))
                self.stats['subscriptions_created'] += 1

    def process_file(self, filepath):
        """Process PayPal export file"""
        print(f"\n{'=' * 80}")
        print(f"PayPal Transaction Import - {'DRY RUN' if self.dry_run else 'EXECUTE MODE'}")
        print(f"{'=' * 80}\n")

        # Read CSV file (tab-delimited)
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)

        print(f"📊 Total rows in file: {len(rows)}\n")

        # Group subscription payments by reference ID
        subscription_groups = defaultdict(list)

        # Process each row
        for i, row in enumerate(rows):
            self.stats['rows_processed'] += 1

            if i % 100 == 0:
                print(f"Processing row {i+1}/{len(rows)}...", end='\r')

            try:
                # Create or update contact
                contact_id = self.create_or_update_contact(row)

                if contact_id:
                    # Add contact_id to row for subscription processing
                    row['contact_id'] = contact_id

                    # Create transaction
                    self.create_transaction(row, contact_id)

                    # Group subscription payments
                    if row['Type'] == 'Subscription Payment' and row.get('Reference Txn ID'):
                        subscription_groups[row['Reference Txn ID']].append(row)

            except Exception as e:
                self.stats['errors'].append(f"Row {i}: {str(e)}")

        print(f"\nProcessing subscriptions...")

        # Process subscription groups
        for ref_id, transactions in subscription_groups.items():
            try:
                self.create_or_update_subscription(ref_id, transactions)
            except Exception as e:
                self.stats['errors'].append(f"Subscription {ref_id}: {str(e)}")

        # Commit or rollback
        if not self.dry_run:
            self.conn.commit()
            print("\n✅ Changes committed to database")
        else:
            self.conn.rollback()
            print("\n⚠️  DRY RUN - No changes made to database")

    def print_stats(self):
        """Print import statistics"""
        print(f"\n{'=' * 80}")
        print("Import Statistics")
        print(f"{'=' * 80}\n")

        print(f"Rows processed: {self.stats['rows_processed']}")
        print(f"\n📇 Contacts:")
        print(f"  - Matched existing: {self.stats['contacts_matched']}")
        print(f"  - Created new: {self.stats['contacts_created']}")
        print(f"  - Updated: {self.stats['contacts_updated']}")

        print(f"\n💰 Transactions:")
        print(f"  - Created: {self.stats['transactions_created']}")

        print(f"\n📋 Subscriptions:")
        print(f"  - Created: {self.stats['subscriptions_created']}")
        print(f"  - Updated: {self.stats['subscriptions_updated']}")

        print(f"\n🔧 Program Partner Corrections:")
        print(f"  - Applied: {self.stats['corrections_applied']}")
        if self.corrections:
            print(f"  - Total in corrections list: {len(self.corrections)}")

        if self.stats['errors']:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print(f"\n{'=' * 80}\n")

    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Import PayPal transactions')
    parser.add_argument('--file', required=True, help='Path to PayPal export file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')
    parser.add_argument('--execute', action='store_true', help='Execute mode (make changes)')
    parser.add_argument('--corrections', default='data/program_partner_corrections.csv',
                       help='Path to Program Partner corrections CSV (default: data/program_partner_corrections.csv)')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Error: Must specify either --dry-run or --execute")
        sys.exit(1)

    # Create importer
    importer = PayPalImporter(DB_CONNECTION, dry_run=args.dry_run, corrections_file=args.corrections)

    try:
        # Process file
        importer.process_file(args.file)

        # Print statistics
        importer.print_stats()

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        importer.close()


if __name__ == '__main__':
    main()
