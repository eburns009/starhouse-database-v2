#!/usr/bin/env python3
"""
WEEKLY KAJABI V2 IMPORT - Comprehensive Data Import
====================================================

Purpose: Import complete Kajabi v2 data exports (7 CSV files) to keep database fully synchronized

What it imports:
  1. Contacts (with email subscription status, phones, addresses)
  2. Tags and contact-tag relationships
  3. Products/Offers and contact-product relationships (purchases)
  4. Subscriptions (active, trial, cancelled)
  5. Transactions (payments, refunds)

Usage:
  # Dry-run first (recommended)
  python3 scripts/weekly_import_kajabi_v2.py --dry-run

  # Execute import
  python3 scripts/weekly_import_kajabi_v2.py --execute

  # Custom data folder
  python3 scripts/weekly_import_kajabi_v2.py --data-dir data/samples --execute

Required Files from Kajabi (v2 exports):
  - v2_contacts.csv          (Contact information, email subscription status)
  - v2_tags.csv              (Tag definitions)
  - v2_contact_tags.csv      (Which contacts have which tags)
  - v2_products.csv          (Product/offer catalog)
  - v2_contact_products.csv  (Which contacts bought which products)
  - v2_subscriptions.csv     (Active/cancelled subscriptions)
  - v2_transactions.csv      (Payment transactions)

Export Instructions:
  1. Log into Kajabi admin
  2. Export all 7 files from the v2 export system
  3. Save to: data/current/ (for production) or data/samples/ (for testing)
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Set
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database connection - NO DEFAULTS, fails fast if missing
DB_CONNECTION = get_database_url()

# Expected file names (without path)
REQUIRED_FILES = {
    'contacts': 'v2_contacts.csv',
    'tags': 'v2_tags.csv',
    'contact_tags': 'v2_contact_tags.csv',
    'products': 'v2_products.csv',
    'contact_products': 'v2_contact_products.csv',
    'subscriptions': 'v2_subscriptions.csv',
    'transactions': 'v2_transactions.csv',
}

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
        # Try ISO format first (2025-10-28T06:56:07Z)
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')

        # Try other formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%b %d, %Y']:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        return None
    except:
        return None

def parse_bool(value: str) -> bool:
    """Parse boolean value from string."""
    if not value:
        return False
    return value.lower() in ['true', 't', 'yes', 'y', '1']

def normalize_email(email: str) -> Optional[str]:
    """Normalize and validate email address."""
    if not email or email.strip() in ['', 'N/A', 'null']:
        return None

    email = email.strip().lower()

    # Basic validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return None

    return email

# ============================================================================
# KAJABI V2 IMPORTER CLASS
# ============================================================================

class KajabiV2Importer:
    """Comprehensive Kajabi v2 data importer."""

    def __init__(self, data_dir: str, dry_run: bool = True):
        self.data_dir = data_dir
        self.dry_run = dry_run
        self.conn = None
        self.cur = None

        # Statistics
        self.stats = {
            'contacts': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'tags': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'contact_tags': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'products': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'contact_products': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'subscriptions': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'transactions': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'validation': {'city_corrected': 0, 'duplicates_removed': 0, 'total_issues': 0},
        }

        # Caches for lookups
        self.contact_id_by_email: Dict[str, str] = {}
        self.tag_ids: Set[str] = set()
        self.product_ids: Set[str] = set()

    def validate_and_correct_address(self, address_line_1: Optional[str], address_line_2: Optional[str],
                                     city: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
        """
        Validate and auto-correct address fields based on known patterns.

        Patterns corrected:
        1. City in address_line_2 (when city is empty but address_line_2 has data)
        2. Duplicate addresses (when address_line_1 equals address_line_2)

        Returns:
            Tuple of (corrected_address_line_1, corrected_address_line_2, corrected_city, was_corrected)
        """
        corrected = False

        # Pattern 1: City in address_line_2
        # If city is empty, address_line_1 has data, and address_line_2 has data,
        # move address_line_2 to city
        if not city and address_line_1 and address_line_2:
            city = address_line_2
            address_line_2 = None
            corrected = True
            self.stats['validation']['city_corrected'] += 1

        # Pattern 2: Duplicate addresses
        # If address_line_1 equals address_line_2, clear address_line_2
        if address_line_1 and address_line_2 and address_line_1 == address_line_2:
            address_line_2 = None
            corrected = True
            self.stats['validation']['duplicates_removed'] += 1

        if corrected:
            self.stats['validation']['total_issues'] += 1

        return address_line_1, address_line_2, city, corrected

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

        missing_files = []
        for file_type, filename in REQUIRED_FILES.items():
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"✅ {filename:30s} ({size:,} bytes)")
            else:
                print(f"❌ {filename:30s} NOT FOUND")
                missing_files.append(filename)

        print()

        if missing_files:
            print(f"❌ Missing {len(missing_files)} required file(s)")
            return False

        print("✅ All required files present")
        return True

    def load_contacts(self):
        """Import contacts from v2_contacts.csv."""
        print("\n" + "=" * 80)
        print("  STEP 1: Importing Contacts")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['contacts'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['contacts']['processed'] += 1

                try:
                    # Parse contact data
                    email = normalize_email(row.get('email', ''))
                    if not email:
                        self.stats['contacts']['errors'] += 1
                        continue

                    first_name = row.get('first_name', '').strip() or None
                    last_name = row.get('last_name', '').strip() or None
                    phone = row.get('phone', '').strip() or None
                    email_subscribed = parse_bool(row.get('email_subscribed', 'false'))

                    # Address fields
                    address_line_1 = row.get('address_line_1', '').strip() or None
                    address_line_2 = row.get('address_line_2', '').strip() or None
                    city = row.get('city', '').strip() or None
                    state = row.get('state', '').strip() or None
                    postal_code = row.get('postal_code', '').strip() or None
                    country = row.get('country', '').strip() or None

                    # Validate and auto-correct address data
                    address_line_1, address_line_2, city, was_corrected = self.validate_and_correct_address(
                        address_line_1, address_line_2, city
                    )

                    # External IDs
                    kajabi_id = row.get('kajabi_id', '').strip() or None
                    kajabi_member_id = row.get('kajabi_member_id', '').strip() or None

                    # Check if contact exists by email
                    self.cur.execute("""
                        SELECT id FROM contacts WHERE email = %s
                    """, (email,))
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
                                email_subscribed = %s,
                                source_system = 'kajabi',
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            first_name, last_name, phone,
                            address_line_1, address_line_2, city, state, postal_code, country,
                            kajabi_id, kajabi_member_id, email_subscribed,
                            contact_id
                        ))

                        self.stats['contacts']['updated'] += 1
                    else:
                        # Create new contact
                        self.cur.execute("""
                            INSERT INTO contacts (
                                email, first_name, last_name, phone,
                                address_line_1, address_line_2,
                                city, state, postal_code, country,
                                kajabi_id, kajabi_member_id,
                                email_subscribed,
                                source_system, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                        """, (
                            email, first_name, last_name, phone,
                            address_line_1, address_line_2, city, state, postal_code, country,
                            kajabi_id, kajabi_member_id, email_subscribed,
                            'kajabi'
                        ))

                        result = self.cur.fetchone()
                        contact_id = result['id']
                        self.stats['contacts']['created'] += 1

                    # Cache contact ID for later lookups
                    self.contact_id_by_email[email] = contact_id

                    # Also create/update contact_emails entry (for the contact_emails table)
                    self.cur.execute("""
                        INSERT INTO contact_emails (
                            contact_id, email, email_type, is_primary, is_outreach,
                            source, created_at, updated_at
                        )
                        VALUES (%s, %s, 'personal', true, true, 'kajabi', NOW(), NOW())
                        ON CONFLICT (contact_id, email) DO UPDATE
                        SET
                            is_outreach = true,
                            updated_at = NOW()
                    """, (contact_id, email))

                except Exception as e:
                    self.stats['contacts']['errors'] += 1
                    print(f"⚠️  Error processing contact {email}: {e}")

        print(f"\n📇 Contacts:")
        print(f"  Processed: {self.stats['contacts']['processed']}")
        print(f"  Created: {self.stats['contacts']['created']}")
        print(f"  Updated: {self.stats['contacts']['updated']}")
        print(f"  Errors: {self.stats['contacts']['errors']}")

        # Address validation summary
        if self.stats['validation']['total_issues'] > 0:
            print(f"\n🔧 Address Validation (Auto-Corrections):")
            print(f"  City placement fixed: {self.stats['validation']['city_corrected']}")
            print(f"  Duplicates removed: {self.stats['validation']['duplicates_removed']}")
            print(f"  Total corrections: {self.stats['validation']['total_issues']}")

    def load_tags(self):
        """Import tags from v2_tags.csv."""
        print("\n" + "=" * 80)
        print("  STEP 2: Importing Tags")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['tags'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['tags']['processed'] += 1

                try:
                    tag_id = row.get('id', '').strip()
                    name = row.get('name', '').strip()
                    description = row.get('description', '').strip() or None
                    category = row.get('category', '').strip() or None

                    if not tag_id or not name:
                        self.stats['tags']['errors'] += 1
                        continue

                    # Insert or update tag
                    self.cur.execute("""
                        INSERT INTO tags (id, name, description, category, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (id) DO UPDATE
                        SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            category = EXCLUDED.category,
                            updated_at = NOW()
                    """, (tag_id, name, description, category))

                    self.tag_ids.add(tag_id)
                    self.stats['tags']['created'] += 1

                except Exception as e:
                    self.stats['tags']['errors'] += 1
                    print(f"⚠️  Error processing tag {name}: {e}")

        print(f"\n🏷️  Tags:")
        print(f"  Processed: {self.stats['tags']['processed']}")
        print(f"  Created/Updated: {self.stats['tags']['created']}")
        print(f"  Errors: {self.stats['tags']['errors']}")

    def load_contact_tags(self):
        """Import contact-tag relationships from v2_contact_tags.csv."""
        print("\n" + "=" * 80)
        print("  STEP 3: Importing Contact-Tag Relationships")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['contact_tags'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['contact_tags']['processed'] += 1

                try:
                    contact_id = row.get('contact_id', '').strip()
                    tag_id = row.get('tag_id', '').strip()

                    if not contact_id or not tag_id:
                        self.stats['contact_tags']['errors'] += 1
                        continue

                    # Insert contact-tag relationship
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
                    self.stats['contact_tags']['errors'] += 1
                    # print(f"⚠️  Error processing contact-tag relationship: {e}")

        print(f"\n🔗 Contact-Tag Relationships:")
        print(f"  Processed: {self.stats['contact_tags']['processed']}")
        print(f"  Created: {self.stats['contact_tags']['created']}")
        print(f"  Skipped (duplicates): {self.stats['contact_tags']['skipped']}")
        print(f"  Errors: {self.stats['contact_tags']['errors']}")

    def load_products(self):
        """Import products from v2_products.csv."""
        print("\n" + "=" * 80)
        print("  STEP 4: Importing Products")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['products'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['products']['processed'] += 1

                try:
                    product_id = row.get('id', '').strip()
                    name = row.get('name', '').strip()
                    description = row.get('description', '').strip() or None
                    product_type = row.get('product_type', '').strip() or 'offer'
                    kajabi_offer_id = row.get('kajabi_offer_id', '').strip() or None
                    active = parse_bool(row.get('active', 'true'))

                    if not product_id or not name:
                        self.stats['products']['errors'] += 1
                        continue

                    # Insert or update product
                    self.cur.execute("""
                        INSERT INTO products (
                            id, name, description, product_type, kajabi_offer_id,
                            active, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (id) DO UPDATE
                        SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            product_type = EXCLUDED.product_type,
                            kajabi_offer_id = EXCLUDED.kajabi_offer_id,
                            active = EXCLUDED.active,
                            updated_at = NOW()
                    """, (product_id, name, description, product_type, kajabi_offer_id, active))

                    self.product_ids.add(product_id)
                    self.stats['products']['created'] += 1

                except Exception as e:
                    self.stats['products']['errors'] += 1
                    print(f"⚠️  Error processing product {name}: {e}")

        print(f"\n📦 Products:")
        print(f"  Processed: {self.stats['products']['processed']}")
        print(f"  Created/Updated: {self.stats['products']['created']}")
        print(f"  Errors: {self.stats['products']['errors']}")

    def load_contact_products(self):
        """Import contact-product relationships from v2_contact_products.csv."""
        print("\n" + "=" * 80)
        print("  STEP 5: Importing Contact-Product Relationships (Purchases)")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['contact_products'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['contact_products']['processed'] += 1

                try:
                    contact_id = row.get('contact_id', '').strip()
                    product_id = row.get('product_id', '').strip()

                    if not contact_id or not product_id:
                        self.stats['contact_products']['errors'] += 1
                        continue

                    # Insert contact-product relationship
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
                    self.stats['contact_products']['errors'] += 1
                    # print(f"⚠️  Error processing contact-product relationship: {e}")

        print(f"\n🛒 Contact-Product Relationships (Purchases):")
        print(f"  Processed: {self.stats['contact_products']['processed']}")
        print(f"  Created: {self.stats['contact_products']['created']}")
        print(f"  Skipped (duplicates): {self.stats['contact_products']['skipped']}")
        print(f"  Errors: {self.stats['contact_products']['errors']}")

    def load_subscriptions(self):
        """Import subscriptions from v2_subscriptions.csv."""
        print("\n" + "=" * 80)
        print("  STEP 6: Importing Subscriptions")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['subscriptions'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['subscriptions']['processed'] += 1

                try:
                    contact_id = row.get('contact_id', '').strip()
                    product_id = row.get('product_id', '').strip() or None
                    kajabi_subscription_id = row.get('kajabi_subscription_id', '').strip() or None
                    status = row.get('status', '').strip().lower() or 'active'
                    amount = parse_decimal(row.get('amount', '0'))
                    currency = row.get('currency', 'USD').strip().upper()
                    billing_cycle = row.get('billing_cycle', '').strip().lower() or 'monthly'

                    # Dates
                    start_date = parse_date(row.get('start_date', ''))
                    trial_end_date = parse_date(row.get('trial_end_date', ''))
                    cancellation_date = parse_date(row.get('cancellation_date', ''))
                    next_billing_date = parse_date(row.get('next_billing_date', ''))

                    payment_processor = row.get('payment_processor', '').strip() or 'kajabi'
                    coupon_code = row.get('coupon_code', '').strip() or None

                    if not contact_id:
                        self.stats['subscriptions']['errors'] += 1
                        continue

                    # Map billing_cycle to proper values
                    billing_cycle_map = {
                        'year': 'annual',
                        'yearly': 'annual',
                        'annual': 'annual',
                        'month': 'monthly',
                        'monthly': 'monthly',
                    }
                    billing_cycle = billing_cycle_map.get(billing_cycle, 'monthly')

                    # Insert or update subscription
                    if kajabi_subscription_id:
                        # Update by Kajabi subscription ID
                        self.cur.execute("""
                            INSERT INTO subscriptions (
                                contact_id, product_id, kajabi_subscription_id,
                                status, amount, currency, billing_cycle,
                                start_date, trial_end_date, cancellation_date, next_billing_date,
                                payment_processor, coupon_code,
                                created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
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
                            start_date, trial_end_date, cancellation_date, next_billing_date,
                            payment_processor, coupon_code
                        ))
                    else:
                        # No kajabi_subscription_id, just insert (no conflict handling)
                        self.cur.execute("""
                            INSERT INTO subscriptions (
                                contact_id, product_id,
                                status, amount, currency, billing_cycle,
                                start_date, trial_end_date, cancellation_date, next_billing_date,
                                payment_processor, coupon_code,
                                created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, (
                            contact_id, product_id,
                            status, amount, currency, billing_cycle,
                            start_date, trial_end_date, cancellation_date, next_billing_date,
                            payment_processor, coupon_code
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
        """Import transactions from v2_transactions.csv."""
        print("\n" + "=" * 80)
        print("  STEP 7: Importing Transactions")
        print("=" * 80)
        print()

        filepath = os.path.join(self.data_dir, REQUIRED_FILES['transactions'])

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats['transactions']['processed'] += 1

                try:
                    contact_id = row.get('contact_id', '').strip()
                    product_id = row.get('product_id', '').strip() or None
                    subscription_id = row.get('subscription_id', '').strip() or None
                    kajabi_transaction_id = row.get('kajabi_transaction_id', '').strip() or None
                    order_number = row.get('order_number', '').strip() or None

                    transaction_type = row.get('transaction_type', '').strip().lower() or 'purchase'
                    status = row.get('status', '').strip().lower() or 'completed'
                    amount = parse_decimal(row.get('amount', '0'))
                    currency = row.get('currency', 'USD').strip().upper()
                    tax_amount = parse_decimal(row.get('tax_amount', '0'))
                    quantity = int(row.get('quantity', '1') or 1)

                    payment_method = row.get('payment_method', '').strip() or None
                    payment_processor = row.get('payment_processor', '').strip() or 'kajabi'
                    coupon_code = row.get('coupon_code', '').strip() or None
                    transaction_date = parse_date(row.get('transaction_date', ''))

                    if not contact_id or not amount:
                        self.stats['transactions']['errors'] += 1
                        continue

                    # Insert transaction (with deduplication by kajabi_transaction_id)
                    if kajabi_transaction_id:
                        self.cur.execute("""
                            INSERT INTO transactions (
                                contact_id, product_id, subscription_id,
                                kajabi_transaction_id, order_number,
                                transaction_type, status, amount, currency, tax_amount, quantity,
                                payment_method, payment_processor, coupon_code, transaction_date,
                                source_system, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            ON CONFLICT (kajabi_transaction_id) DO NOTHING
                        """, (
                            contact_id, product_id, subscription_id,
                            kajabi_transaction_id, order_number,
                            transaction_type, status, amount, currency, tax_amount, quantity,
                            payment_method, payment_processor, coupon_code, transaction_date,
                            'kajabi'
                        ))
                    else:
                        # No kajabi_transaction_id, insert anyway (may create duplicates if re-run)
                        self.cur.execute("""
                            INSERT INTO transactions (
                                contact_id, product_id, subscription_id,
                                order_number,
                                transaction_type, status, amount, currency, tax_amount, quantity,
                                payment_method, payment_processor, coupon_code, transaction_date,
                                source_system, created_at, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, (
                            contact_id, product_id, subscription_id,
                            order_number,
                            transaction_type, status, amount, currency, tax_amount, quantity,
                            payment_method, payment_processor, coupon_code, transaction_date,
                            'kajabi'
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
        print("  KAJABI V2 COMPREHENSIVE IMPORT")
        print("=" * 80)
        print()
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"Data directory: {self.data_dir}")
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
            self.load_contacts()           # 1. Contacts first (base records)
            self.load_tags()               # 2. Tags (definitions)
            self.load_contact_tags()       # 3. Contact-Tag relationships
            self.load_products()           # 4. Products (catalog)
            self.load_contact_products()   # 5. Contact-Product relationships (purchases)
            self.load_subscriptions()      # 6. Subscriptions
            self.load_transactions()       # 7. Transactions

            # Summary
            print("\n" + "=" * 80)
            print("  IMPORT COMPLETE")
            print("=" * 80)
            print()
            print("📊 Summary:")
            print()
            print(f"  Contacts:         {self.stats['contacts']['created']} created, {self.stats['contacts']['updated']} updated")
            print(f"  Tags:             {self.stats['tags']['created']} created/updated")
            print(f"  Contact Tags:     {self.stats['contact_tags']['created']} linked")
            print(f"  Products:         {self.stats['products']['created']} created/updated")
            print(f"  Contact Products: {self.stats['contact_products']['created']} linked")
            print(f"  Subscriptions:    {self.stats['subscriptions']['created']} created, {self.stats['subscriptions']['updated']} updated")
            print(f"  Transactions:     {self.stats['transactions']['created']} created")
            print()

            # Validation summary
            if self.stats['validation']['total_issues'] > 0:
                print(f"🔧 Address Validation:")
                print(f"  City placements fixed:   {self.stats['validation']['city_corrected']}")
                print(f"  Duplicates removed:      {self.stats['validation']['duplicates_removed']}")
                print(f"  Total auto-corrections:  {self.stats['validation']['total_issues']}")
                print()

            total_errors = sum(s.get('errors', 0) for s in self.stats.values() if 'errors' in s)
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
        description='Import comprehensive Kajabi v2 data exports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--data-dir',
        default='data/current',
        help='Directory containing Kajabi CSV files (default: data/current)'
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

    # Validate data directory
    if not os.path.isdir(args.data_dir):
        print(f"❌ Error: Data directory not found: {args.data_dir}")
        print()
        print("Please create the directory and place the 7 Kajabi CSV files there:")
        for filename in REQUIRED_FILES.values():
            print(f"  - {filename}")
        sys.exit(1)

    # Run importer
    importer = KajabiV2Importer(
        data_dir=args.data_dir,
        dry_run=args.dry_run
    )

    success = importer.run()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
