#!/usr/bin/env python3
"""
WEEKLY KAJABI IMPORT - SIMPLIFIED (3 Native Files)
===================================================

Purpose: Import weekly Kajabi native exports (3 CSV files) - MUCH SIMPLER!

What it imports from 3 native Kajabi exports:
  1. Contacts file → Contacts, Tags, Products, and relationships
  2. Subscriptions file → Recurring subscriptions
  3. Transactions file → Payment transactions and addresses

Usage:
  # Dry-run first (recommended)
  python3 scripts/weekly_import_kajabi_simple.py --dry-run

  # Execute import
  python3 scripts/weekly_import_kajabi_simple.py --execute

  # Custom file paths
  python3 scripts/weekly_import_kajabi_simple.py \
    --contacts "kajabi 3 files review/kajabi contacts.csv" \
    --subscriptions "kajabi 3 files review/subscriptions (1).csv" \
    --transactions "kajabi 3 files review/transactions (2).csv" \
    --dry-run

Required Files from Kajabi:
  - Kajabi Contacts export (People → Contacts → Export)
  - Subscriptions export (People → Subscriptions → Export)
  - Transactions export (Sales → Transactions → Export)

Export Instructions:
  1. Kajabi → People → Contacts → Export All → CSV
  2. Kajabi → People → Subscriptions → Export All → CSV
  3. Kajabi → Sales/Transactions → Export → CSV
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONNECTION = os.environ.get(
    'DATABASE_URL',
    'postgresql://***REMOVED***:***REMOVED***@***REMOVED***:6543/postgres'
)

# Default file locations
DEFAULT_CONTACTS_FILE = 'data/current/kajabi_contacts.csv'
DEFAULT_SUBSCRIPTIONS_FILE = 'data/current/kajabi_subscriptions.csv'
DEFAULT_TRANSACTIONS_FILE = 'data/current/kajabi_transactions.csv'

# ============================================================================
# UTILITIES
# ============================================================================

def parse_decimal(value: str) -> Optional[Decimal]:
    """Parse decimal value from string, handling various formats."""
    if not value or value.strip() in ['', 'N/A', 'null']:
        return None
    try:
        # Remove currency symbols and commas
        clean = value.replace('$', '').replace(',', '').strip()
        return Decimal(clean)
    except:
        return None

def parse_date(date_str: str) -> Optional[str]:
    """Parse date string to ISO format."""
    if not date_str or date_str.strip() in ['', 'N/A', 'null']:
        return None

    try:
        # Kajabi format: "Dec 19, 2021" or "2020-11-05 11:10:44 -0700"
        if '-' in date_str and ':' in date_str:
            # ISO-ish format: "2020-11-05 11:10:44 -0700"
            dt = datetime.strptime(date_str.split('.')[0].rsplit(' ', 1)[0], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # "Dec 19, 2021" format
            dt = datetime.strptime(date_str.strip(), '%b %d, %Y')
            return dt.strftime('%Y-%m-%d')
    except:
        return None

def parse_comma_separated(value: str) -> List[str]:
    """Parse comma-separated string into list of items."""
    if not value or value.strip() in ['', 'N/A', 'null']:
        return []

    # Split and clean each item
    items = [item.strip() for item in value.split(',')]
    return [item for item in items if item]

def normalize_email(email: str) -> Optional[str]:
    """Normalize and validate email address."""
    if not email or email.strip() in ['', 'N/A', 'null']:
        return None

    email = email.strip().lower()

    # Basic validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return None

    return email

def map_payment_status(status_str: str) -> str:
    """Map Kajabi payment status to database enum values."""
    status = status_str.strip().lower() if status_str else 'completed'

    # Map Kajabi statuses to database enum
    status_map = {
        'succeeded': 'completed',
        'success': 'completed',
        'completed': 'completed',
        'pending': 'pending',
        'failed': 'failed',
        'failure': 'failed',
        'refunded': 'refunded',
        'refund': 'refunded',
        'disputed': 'disputed',
        'dispute': 'disputed',
    }

    return status_map.get(status, 'completed')

# ============================================================================
# KAJABI SIMPLE IMPORTER CLASS
# ============================================================================

class KajabiSimpleImporter:
    """Simplified Kajabi importer for 3 native export files."""

    def __init__(self, contacts_file: str, subscriptions_file: str,
                 transactions_file: str, dry_run: bool = True):
        self.contacts_file = contacts_file
        self.subscriptions_file = subscriptions_file
        self.transactions_file = transactions_file
        self.dry_run = dry_run
        self.conn = None
        self.cur = None

        # Statistics
        self.stats = {
            'contacts': {'processed': 0, 'created': 0, 'updated': 0, 'errors': 0},
            'tags': {'processed': 0, 'created': 0, 'errors': 0},
            'contact_tags': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'products': {'processed': 0, 'created': 0, 'errors': 0},
            'contact_products': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'subscriptions': {'processed': 0, 'created': 0, 'updated': 0, 'errors': 0},
            'transactions': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
        }

        # Caches for lookups
        self.tag_name_to_id: Dict[str, str] = {}
        self.product_name_to_id: Dict[str, str] = {}
        self.contact_email_to_id: Dict[str, str] = {}

    def connect(self):
        """Connect to database."""
        print("📡 Connecting to database...")
        self.conn = psycopg2.connect(DB_CONNECTION)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Connected\n")

    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            if self.dry_run:
                print("\n🔄 DRY RUN - Rolling back all changes...")
                self.conn.rollback()
            else:
                print("\n💾 Committing changes to database...")
                self.conn.commit()
            self.conn.close()

    def verify_files(self) -> bool:
        """Verify all required files exist."""
        print("=" * 80)
        print("  PRE-FLIGHT: Checking Files")
        print("=" * 80)
        print()

        files = [
            (self.contacts_file, "Kajabi Contacts"),
            (self.subscriptions_file, "Kajabi Subscriptions"),
            (self.transactions_file, "Kajabi Transactions"),
        ]

        missing_files = []
        for filepath, description in files:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"✅ {description:30s} ({size:,} bytes)")
            else:
                print(f"❌ {description:30s} NOT FOUND: {filepath}")
                missing_files.append(filepath)

        print()

        if missing_files:
            print(f"❌ Missing {len(missing_files)} required file(s)")
            return False

        print("✅ All required files present")
        return True

    def load_contacts(self):
        """Import contacts from Kajabi contacts export."""
        print("\n" + "=" * 80)
        print("  STEP 1: Importing Contacts (with Products and Tags)")
        print("=" * 80)
        print()

        # Track unique tags and products from all contacts
        all_tags: Set[str] = set()
        all_products: Set[str] = set()
        contact_tags_map: Dict[str, List[str]] = {}  # email -> [tags]
        contact_products_map: Dict[str, List[str]] = {}  # email -> [products]

        with open(self.contacts_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['contacts']['processed'] += 1

                try:
                    # Parse contact data
                    email = normalize_email(row.get('Email', ''))
                    if not email:
                        self.stats['contacts']['errors'] += 1
                        continue

                    first_name = row.get('First Name', '').strip() or None
                    last_name = row.get('Last Name', '').strip() or None

                    # Phone - try multiple columns
                    phone = (row.get('Phone Number (phone_number)', '') or
                            row.get('Mobile Phone Number (mobile_phone_number)', '') or
                            row.get('Phone', '')).strip() or None

                    # Address fields
                    address_line_1 = row.get('Address (address_line_1)', '').strip() or None
                    address_line_2 = row.get('Address Line 2 (address_line_2)', '').strip() or None
                    city = row.get('City (address_city)', '').strip() or None
                    state = row.get('State (address_state)', '').strip() or None
                    postal_code = row.get('Zip Code (address_zip)', '').strip() or None
                    country = row.get('Country (address_country)', '').strip() or None

                    # Kajabi IDs
                    kajabi_id = row.get('ID', '').strip() or None
                    kajabi_member_id = row.get('Member ID', '').strip() or None

                    # Parse Products and Tags (comma-separated)
                    products_str = row.get('Products', '')
                    tags_str = row.get('Tags', '')

                    contact_products = parse_comma_separated(products_str)
                    contact_tags = parse_comma_separated(tags_str)

                    # Add to global sets
                    all_products.update(contact_products)
                    all_tags.update(contact_tags)

                    # Store mappings
                    if contact_tags:
                        contact_tags_map[email] = contact_tags
                    if contact_products:
                        contact_products_map[email] = contact_products

                    # Check if contact exists
                    self.cur.execute("SELECT id FROM contacts WHERE email = %s", (email,))
                    existing = self.cur.fetchone()

                    if existing:
                        contact_id = existing['id']

                        # Update existing contact
                        self.cur.execute("""
                            UPDATE contacts
                            SET
                                first_name = COALESCE(%s, first_name),
                                last_name = COALESCE(%s, last_name),
                                phone = COALESCE(%s, phone),
                                address_line_1 = COALESCE(%s, address_line_1),
                                address_line_2 = COALESCE(%s, address_line_2),
                                city = COALESCE(%s, city),
                                state = COALESCE(%s, state),
                                postal_code = COALESCE(%s, postal_code),
                                country = COALESCE(%s, country),
                                kajabi_id = COALESCE(%s, kajabi_id),
                                kajabi_member_id = COALESCE(%s, kajabi_member_id),
                                source_system = 'kajabi',
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            first_name, last_name, phone,
                            address_line_1, address_line_2, city, state, postal_code, country,
                            kajabi_id, kajabi_member_id,
                            contact_id
                        ))

                        self.stats['contacts']['updated'] += 1
                    else:
                        # Create new contact
                        self.cur.execute("""
                            INSERT INTO contacts (
                                email, first_name, last_name, phone,
                                address_line_1, address_line_2, city, state, postal_code, country,
                                kajabi_id, kajabi_member_id,
                                source_system, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                        """, (
                            email, first_name, last_name, phone,
                            address_line_1, address_line_2, city, state, postal_code, country,
                            kajabi_id, kajabi_member_id,
                            'kajabi'
                        ))

                        result = self.cur.fetchone()
                        contact_id = result['id']
                        self.stats['contacts']['created'] += 1

                    # Cache contact ID
                    self.contact_email_to_id[email] = contact_id

                    # Create/update contact_emails entry
                    self.cur.execute("""
                        INSERT INTO contact_emails (
                            contact_id, email, email_type, is_primary, is_outreach,
                            source, created_at, updated_at
                        )
                        VALUES (%s, %s, 'personal', true, true, 'kajabi', NOW(), NOW())
                        ON CONFLICT (contact_id, email) DO UPDATE
                        SET is_outreach = true, updated_at = NOW()
                    """, (contact_id, email))

                except Exception as e:
                    self.stats['contacts']['errors'] += 1
                    print(f"⚠️  Error processing contact {email}: {e}")

        print(f"\n📇 Contacts:")
        print(f"  Processed: {self.stats['contacts']['processed']}")
        print(f"  Created: {self.stats['contacts']['created']}")
        print(f"  Updated: {self.stats['contacts']['updated']}")
        print(f"  Errors: {self.stats['contacts']['errors']}")

        # Now create tags
        print(f"\n🏷️  Creating Tags ({len(all_tags)} unique)...")
        for tag_name in all_tags:
            if not tag_name:
                continue

            self.stats['tags']['processed'] += 1

            try:
                # Check if tag exists first (name_norm is a generated column)
                self.cur.execute("""
                    SELECT id FROM tags WHERE LOWER(TRIM(%s)) = name_norm
                """, (tag_name,))

                existing = self.cur.fetchone()
                if existing:
                    self.tag_name_to_id[tag_name] = existing['id']
                else:
                    self.cur.execute("""
                        INSERT INTO tags (name, created_at, updated_at)
                        VALUES (%s, NOW(), NOW())
                        RETURNING id
                    """, (tag_name,))

                    result = self.cur.fetchone()
                    self.tag_name_to_id[tag_name] = result['id']

                self.stats['tags']['created'] += 1

            except Exception as e:
                self.stats['tags']['errors'] += 1
                print(f"⚠️  Error creating tag '{tag_name}': {e}")

        print(f"  Created/Updated: {self.stats['tags']['created']}")

        # Now create products
        print(f"\n📦 Creating Products ({len(all_products)} unique)...")
        for product_name in all_products:
            if not product_name:
                continue

            self.stats['products']['processed'] += 1

            try:
                # Check if product exists first (name_norm is a generated column)
                self.cur.execute("""
                    SELECT id FROM products WHERE LOWER(TRIM(%s)) = name_norm
                """, (product_name,))

                existing = self.cur.fetchone()
                if existing:
                    self.product_name_to_id[product_name] = existing['id']
                else:
                    self.cur.execute("""
                        INSERT INTO products (name, product_type, created_at, updated_at)
                        VALUES (%s, 'course', NOW(), NOW())
                        RETURNING id
                    """, (product_name,))

                    result = self.cur.fetchone()
                    self.product_name_to_id[product_name] = result['id']

                self.stats['products']['created'] += 1

            except Exception as e:
                self.stats['products']['errors'] += 1
                print(f"⚠️  Error creating product '{product_name}': {e}")

        print(f"  Created/Updated: {self.stats['products']['created']}")

        # Now link contact-tags
        print(f"\n🔗 Linking Contact-Tags...")
        for email, tag_names in contact_tags_map.items():
            contact_id = self.contact_email_to_id.get(email)
            if not contact_id:
                continue

            for tag_name in tag_names:
                tag_id = self.tag_name_to_id.get(tag_name)
                if not tag_id:
                    continue

                self.stats['contact_tags']['processed'] += 1

                try:
                    self.cur.execute("""
                        INSERT INTO contact_tags (contact_id, tag_id, created_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (contact_id, tag_id) DO NOTHING
                    """, (contact_id, tag_id))

                    if self.cur.rowcount > 0:
                        self.stats['contact_tags']['created'] += 1
                    else:
                        self.stats['contact_tags']['skipped'] += 1

                except Exception as e:
                    pass  # Quietly skip errors

        print(f"  Linked: {self.stats['contact_tags']['created']}")
        print(f"  Skipped (duplicates): {self.stats['contact_tags']['skipped']}")

        # Now link contact-products
        print(f"\n🛒 Linking Contact-Products...")
        for email, product_names in contact_products_map.items():
            contact_id = self.contact_email_to_id.get(email)
            if not contact_id:
                continue

            for product_name in product_names:
                product_id = self.product_name_to_id.get(product_name)
                if not product_id:
                    continue

                self.stats['contact_products']['processed'] += 1

                try:
                    self.cur.execute("""
                        INSERT INTO contact_products (contact_id, product_id, created_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (contact_id, product_id) DO NOTHING
                    """, (contact_id, product_id))

                    if self.cur.rowcount > 0:
                        self.stats['contact_products']['created'] += 1
                    else:
                        self.stats['contact_products']['skipped'] += 1

                except Exception as e:
                    pass  # Quietly skip errors

        print(f"  Linked: {self.stats['contact_products']['created']}")
        print(f"  Skipped (duplicates): {self.stats['contact_products']['skipped']}")

    def load_subscriptions(self):
        """Import subscriptions from Kajabi subscriptions export."""
        print("\n" + "=" * 80)
        print("  STEP 2: Importing Subscriptions")
        print("=" * 80)
        print()

        with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['subscriptions']['processed'] += 1

                try:
                    # Parse subscription data
                    email = normalize_email(row.get('Customer Email', ''))
                    if not email:
                        self.stats['subscriptions']['errors'] += 1
                        continue

                    # Get or create contact
                    contact_id = self.contact_email_to_id.get(email)
                    if not contact_id:
                        # Create contact from subscription data
                        customer_name = row.get('Customer Name', '').strip()
                        parts = customer_name.split(' ', 1) if customer_name else ['', '']
                        first_name = parts[0] or None
                        last_name = parts[1] if len(parts) > 1 else None

                        self.cur.execute("""
                            INSERT INTO contacts (
                                email, first_name, last_name, source_system,
                                created_at, updated_at
                            )
                            VALUES (%s, %s, %s, 'kajabi', NOW(), NOW())
                            ON CONFLICT (email) DO UPDATE
                            SET updated_at = NOW()
                            RETURNING id
                        """, (email, first_name, last_name))

                        result = self.cur.fetchone()
                        contact_id = result['id']
                        self.contact_email_to_id[email] = contact_id

                    # Get or create product from Offer Title
                    offer_title = row.get('Offer Title', '').strip()
                    product_id = None

                    if offer_title:
                        product_id = self.product_name_to_id.get(offer_title)
                        if not product_id:
                            # Check if product exists first
                            self.cur.execute("""
                                SELECT id FROM products WHERE LOWER(TRIM(%s)) = name_norm
                            """, (offer_title,))

                            existing = self.cur.fetchone()
                            if existing:
                                product_id = existing['id']
                            else:
                                self.cur.execute("""
                                    INSERT INTO products (name, product_type, created_at, updated_at)
                                    VALUES (%s, 'membership', NOW(), NOW())
                                    RETURNING id
                                """, (offer_title,))

                                result = self.cur.fetchone()
                                product_id = result['id']

                            self.product_name_to_id[offer_title] = product_id

                    # Parse subscription details
                    kajabi_subscription_id = row.get('Kajabi Subscription ID', '').strip() or None
                    status = row.get('Status', '').strip().lower() or 'active'
                    amount = parse_decimal(row.get('Amount', '0'))
                    currency = row.get('Currency', 'USD').strip().upper()

                    interval = row.get('Interval', '').strip().lower()
                    billing_cycle = 'annual' if 'year' in interval else 'monthly'

                    # Dates
                    created_at = parse_date(row.get('Created At', ''))
                    trial_end_date = parse_date(row.get('Trial Ends On', ''))
                    cancellation_date = parse_date(row.get('Canceled On', ''))
                    next_billing_date = parse_date(row.get('Next Payment Date', ''))

                    payment_processor = row.get('Provider', '').strip() or 'kajabi'
                    coupon_code = row.get('Coupon Used', '').strip() or None

                    # Insert or update subscription
                    if kajabi_subscription_id:
                        self.cur.execute("""
                            INSERT INTO subscriptions (
                                contact_id, product_id, kajabi_subscription_id,
                                status, amount, currency, billing_cycle,
                                start_date, trial_end_date, cancellation_date, next_billing_date,
                                payment_processor, coupon_code,
                                created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), NOW())
                            ON CONFLICT (kajabi_subscription_id) DO UPDATE
                            SET
                                status = EXCLUDED.status,
                                amount = EXCLUDED.amount,
                                cancellation_date = EXCLUDED.cancellation_date,
                                next_billing_date = EXCLUDED.next_billing_date,
                                updated_at = NOW()
                        """, (
                            contact_id, product_id, kajabi_subscription_id,
                            status, amount, currency, billing_cycle,
                            created_at, trial_end_date, cancellation_date, next_billing_date,
                            payment_processor, coupon_code,
                            created_at
                        ))

                        if self.cur.rowcount > 0:
                            self.stats['subscriptions']['created'] += 1
                        else:
                            self.stats['subscriptions']['updated'] += 1

                except Exception as e:
                    self.stats['subscriptions']['errors'] += 1
                    print(f"⚠️  Error processing subscription: {e}")

        print(f"\n💳 Subscriptions:")
        print(f"  Processed: {self.stats['subscriptions']['processed']}")
        print(f"  Created: {self.stats['subscriptions']['created']}")
        print(f"  Updated: {self.stats['subscriptions']['updated']}")
        print(f"  Errors: {self.stats['subscriptions']['errors']}")

    def load_transactions(self):
        """Import transactions from Kajabi transactions export."""
        print("\n" + "=" * 80)
        print("  STEP 3: Importing Transactions")
        print("=" * 80)
        print()

        with open(self.transactions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['transactions']['processed'] += 1

                try:
                    # Parse transaction data
                    email = normalize_email(row.get('Customer Email', ''))
                    if not email:
                        self.stats['transactions']['errors'] += 1
                        continue

                    # Get or create contact
                    contact_id = self.contact_email_to_id.get(email)
                    if not contact_id:
                        # Create contact from transaction data
                        customer_name = row.get('Customer Name', '').strip()
                        parts = customer_name.split(' ', 1) if customer_name else ['', '']
                        first_name = parts[0] or None
                        last_name = parts[1] if len(parts) > 1 else None

                        phone = row.get('Phone', '').strip() or None
                        address_line_1 = row.get('Address', '').strip() or None
                        address_line_2 = row.get('Address 2', '').strip() or None
                        city = row.get('City', '').strip() or None
                        state = row.get('State', '').strip() or None
                        postal_code = row.get('Zipcode', '').strip() or None
                        country = row.get('Country', '').strip() or None

                        self.cur.execute("""
                            INSERT INTO contacts (
                                email, first_name, last_name, phone,
                                address_line_1, address_line_2, city, state, postal_code, country,
                                source_system, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'kajabi', NOW(), NOW())
                            ON CONFLICT (email) DO UPDATE
                            SET
                                phone = COALESCE(EXCLUDED.phone, contacts.phone),
                                address_line_1 = COALESCE(EXCLUDED.address_line_1, contacts.address_line_1),
                                updated_at = NOW()
                            RETURNING id
                        """, (email, first_name, last_name, phone,
                              address_line_1, address_line_2, city, state, postal_code, country))

                        result = self.cur.fetchone()
                        contact_id = result['id']
                        self.contact_email_to_id[email] = contact_id

                    # Get or create product from Offer Title
                    offer_title = row.get('Offer Title', '').strip()
                    product_id = None

                    if offer_title:
                        product_id = self.product_name_to_id.get(offer_title)
                        if not product_id:
                            # Check if product exists first
                            self.cur.execute("""
                                SELECT id FROM products WHERE LOWER(TRIM(%s)) = name_norm
                            """, (offer_title,))

                            existing = self.cur.fetchone()
                            if existing:
                                product_id = existing['id']
                            else:
                                self.cur.execute("""
                                    INSERT INTO products (name, product_type, created_at, updated_at)
                                    VALUES (%s, 'course', NOW(), NOW())
                                    RETURNING id
                                """, (offer_title,))

                                result = self.cur.fetchone()
                                product_id = result['id']

                            self.product_name_to_id[offer_title] = product_id

                    # Parse transaction details
                    transaction_id = row.get('ID', '').strip() or None
                    order_number = row.get('Order No.', '').strip() or None
                    transaction_type = row.get('Type', '').strip().lower() or 'purchase'
                    status = map_payment_status(row.get('Status', ''))
                    amount = parse_decimal(row.get('Amount', '0'))
                    currency = row.get('Currency', 'USD').strip().upper()
                    tax_amount = parse_decimal(row.get('Tax Amount', '0'))
                    quantity = int(row.get('Quantity', '1') or 1)
                    payment_method = row.get('Payment Method', '').strip() or None
                    payment_processor = row.get('Provider', '').strip() or 'kajabi'
                    coupon_code = row.get('Coupon Used', '').strip() or None
                    transaction_date = parse_date(row.get('Created At', ''))

                    # Insert transaction
                    if transaction_id:
                        self.cur.execute("""
                            INSERT INTO transactions (
                                contact_id, product_id, kajabi_transaction_id, order_number,
                                transaction_type, status, amount, currency, tax_amount, quantity,
                                payment_method, payment_processor, coupon_code, transaction_date,
                                source_system, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), 'kajabi', NOW(), NOW())
                            ON CONFLICT (kajabi_transaction_id) DO NOTHING
                        """, (
                            contact_id, product_id, transaction_id, order_number,
                            transaction_type, status, amount, currency, tax_amount, quantity,
                            payment_method, payment_processor, coupon_code, transaction_date
                        ))

                        if self.cur.rowcount > 0:
                            self.stats['transactions']['created'] += 1
                        else:
                            self.stats['transactions']['skipped'] += 1

                except Exception as e:
                    self.stats['transactions']['errors'] += 1
                    print(f"⚠️  Error processing transaction: {e}")

        print(f"\n💰 Transactions:")
        print(f"  Processed: {self.stats['transactions']['processed']}")
        print(f"  Created: {self.stats['transactions']['created']}")
        print(f"  Skipped (duplicates): {self.stats['transactions']['skipped']}")
        print(f"  Errors: {self.stats['transactions']['errors']}")

    def run(self):
        """Run the complete import process."""
        print("=" * 80)
        print("  KAJABI SIMPLIFIED IMPORT (3 Native Files)")
        print("=" * 80)
        print()
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print()

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be saved")
        else:
            print("🔴 EXECUTE MODE - Changes will be committed to database")

        print()

        # Verify files
        if not self.verify_files():
            print("\n❌ Pre-flight check failed. Cannot continue.")
            return False

        # Connect to database
        self.connect()

        try:
            # Run imports in order
            self.load_contacts()       # 1. Contacts (with tags, products, relationships)
            self.load_subscriptions()  # 2. Subscriptions
            self.load_transactions()   # 3. Transactions

            # Summary
            print("\n" + "=" * 80)
            print("  IMPORT COMPLETE")
            print("=" * 80)
            print()
            print("📊 Summary:")
            print()
            print(f"  Contacts:         {self.stats['contacts']['created']} created, {self.stats['contacts']['updated']} updated")
            print(f"  Tags:             {self.stats['tags']['created']} created/updated")
            print(f"  Contact-Tags:     {self.stats['contact_tags']['created']} linked")
            print(f"  Products:         {self.stats['products']['created']} created/updated")
            print(f"  Contact-Products: {self.stats['contact_products']['created']} linked")
            print(f"  Subscriptions:    {self.stats['subscriptions']['created']} created, {self.stats['subscriptions']['updated']} updated")
            print(f"  Transactions:     {self.stats['transactions']['created']} created")
            print()

            total_errors = sum(s['errors'] for s in self.stats.values())
            if total_errors > 0:
                print(f"⚠️  Total errors: {total_errors}")
            else:
                print("✅ No errors")

            print()
            print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if self.dry_run:
                print("\n🔄 DRY RUN COMPLETE - No changes were saved")
                print("Run with --execute to apply changes")
            else:
                print("\n✅ Changes committed to database")

            return True

        except Exception as e:
            print(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Import simplified Kajabi exports (3 native files)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--contacts',
        default=DEFAULT_CONTACTS_FILE,
        help=f'Kajabi contacts CSV file (default: {DEFAULT_CONTACTS_FILE})'
    )

    parser.add_argument(
        '--subscriptions',
        default=DEFAULT_SUBSCRIPTIONS_FILE,
        help=f'Kajabi subscriptions CSV file (default: {DEFAULT_SUBSCRIPTIONS_FILE})'
    )

    parser.add_argument(
        '--transactions',
        default=DEFAULT_TRANSACTIONS_FILE,
        help=f'Kajabi transactions CSV file (default: {DEFAULT_TRANSACTIONS_FILE})'
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without committing to database'
    )
    mode_group.add_argument(
        '--execute',
        action='store_true',
        help='Execute import and commit changes to database'
    )

    args = parser.parse_args()

    # Validate files exist
    for filepath in [args.contacts, args.subscriptions, args.transactions]:
        if not os.path.exists(filepath):
            print(f"❌ Error: File not found: {filepath}")
            sys.exit(1)

    # Run importer
    importer = KajabiSimpleImporter(
        contacts_file=args.contacts,
        subscriptions_file=args.subscriptions,
        transactions_file=args.transactions,
        dry_run=args.dry_run
    )

    success = importer.run()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
