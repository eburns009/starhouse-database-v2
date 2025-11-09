#!/usr/bin/env python3
"""
WEEKLY KAJABI IMPORT - Optimized for Manual Weekly Updates
============================================================

Purpose: Import weekly Kajabi data dumps to keep database synchronized

What it imports:
  1. NEW subscriptions (active, trial, cancelled)
  2. NEW contacts from subscriptions
  3. UPDATED subscription statuses
  4. Products/Offers (if new ones added)

Usage:
  # Dry-run first (recommended)
  python3 scripts/weekly_import_kajabi.py --dry-run

  # Execute import
  python3 scripts/weekly_import_kajabi.py --execute

  # Custom file paths
  python3 scripts/weekly_import_kajabi.py --subscriptions data/kajabi_subs_2025_11_08.csv --execute

Required Files from Kajabi:
  - kajabi_subscriptions.csv (Subscriptions export)
  - kajabi_offers.csv (Products/Offers - optional, only if new products)

Export Instructions:
  1. Log into Kajabi admin
  2. Go to Subscriptions → Export
  3. Download CSV with ALL columns
  4. Save as: data/kajabi_subscriptions_YYYY_MM_DD.csv
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database connection - NO DEFAULTS, fails fast if missing
DB_CONNECTION = get_database_url()

DEFAULT_SUBSCRIPTIONS_FILE = 'data/kajabi_subscriptions.csv'
DEFAULT_OFFERS_FILE = 'data/kajabi_offers_extracted.csv'

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_email(email: str) -> bool:
    """Quick email validation"""
    return email and '@' in email and len(email) < 255

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse Kajabi date format: 'Nov 28, 2025'"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%b %d, %Y')
    except ValueError:
        return None

def parse_amount(amount_str: str) -> Optional[Decimal]:
    """Parse amount string"""
    try:
        clean = amount_str.replace('$', '').replace(',', '').strip()
        return Decimal(clean) if clean else None
    except:
        return None

def map_status(status: str) -> str:
    """Map Kajabi status to our status"""
    status_map = {
        'active': 'active',
        'canceled': 'canceled',
        'cancelled': 'canceled',
        'expired': 'expired',
        'paused': 'paused',
        'trial': 'trial',
    }
    return status_map.get(status.lower().strip(), 'active')

# ============================================================================
# DATABASE HELPER
# ============================================================================

class KajabiImporter:
    def __init__(self, connection_string: str, dry_run: bool = True):
        self.conn = psycopg2.connect(connection_string)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.dry_run = dry_run
        self.stats = {
            'subscriptions_processed': 0,
            'subscriptions_new': 0,
            'subscriptions_updated': 0,
            'subscriptions_skipped': 0,
            'contacts_created': 0,
            'contacts_updated': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': []
        }

    def get_product_by_offer_id(self, offer_id: str) -> Optional[Dict]:
        """Get product by Kajabi offer ID"""
        self.cur.execute("""
            SELECT id, name, kajabi_offer_id
            FROM products
            WHERE kajabi_offer_id = %s
            LIMIT 1
        """, (offer_id,))
        return self.cur.fetchone()

    def create_or_update_product(self, offer_id: str, title: str) -> Optional[str]:
        """Create or update product from Kajabi offer"""
        product = self.get_product_by_offer_id(offer_id)

        # Determine product type
        product_type = 'program_partner' if 'Program Partner' in title else 'membership'

        if product:
            # Update existing
            if not self.dry_run:
                self.cur.execute("""
                    UPDATE products
                    SET name = %s, product_type = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                """, (title, product_type, product['id']))
            self.stats['products_updated'] += 1
            return product['id']
        else:
            # Create new
            if not self.dry_run:
                self.cur.execute("""
                    INSERT INTO products (name, product_type, kajabi_offer_id, active)
                    VALUES (%s, %s, %s, true)
                    RETURNING id
                """, (title, product_type, offer_id))
                result = self.cur.fetchone()
                self.stats['products_created'] += 1
                return result['id'] if result else None
            else:
                self.stats['products_created'] += 1
                return 'dry-run-product-id'

    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """Find contact by email"""
        self.cur.execute("""
            SELECT id, first_name, last_name, kajabi_member_id
            FROM contacts
            WHERE email = %s
            LIMIT 1
        """, (email.lower().strip(),))
        return self.cur.fetchone()

    def create_or_update_contact(self, row: Dict) -> Optional[str]:
        """Create or update contact from Kajabi subscription row"""
        email = row['Customer Email'].strip().lower()
        customer_name = row['Customer Name'].strip()
        customer_id = row['Customer ID'].strip()

        if not validate_email(email):
            self.stats['errors'].append(f"Invalid email: {email}")
            return None

        contact = self.get_contact_by_email(email)

        # Parse name
        name_parts = customer_name.split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else customer_name
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        if contact:
            # Update if Kajabi member ID is missing
            if not contact['kajabi_member_id'] and customer_id:
                if not self.dry_run:
                    self.cur.execute("""
                        UPDATE contacts
                        SET kajabi_member_id = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (customer_id, contact['id']))
                self.stats['contacts_updated'] += 1
            return contact['id']
        else:
            # Create new contact
            if not self.dry_run:
                self.cur.execute("""
                    INSERT INTO contacts (
                        email, first_name, last_name, kajabi_member_id,
                        source_system, email_subscribed, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, 'kajabi', true, NOW(), NOW())
                    RETURNING id
                """, (email, first_name, last_name, customer_id))
                result = self.cur.fetchone()
                self.stats['contacts_created'] += 1
                return result['id'] if result else None
            else:
                self.stats['contacts_created'] += 1
                return 'dry-run-contact-id'

    def get_subscription_by_kajabi_id(self, kajabi_sub_id: str) -> Optional[Dict]:
        """Find existing subscription"""
        self.cur.execute("""
            SELECT id, status, amount, next_billing_date
            FROM subscriptions
            WHERE kajabi_subscription_id = %s
            LIMIT 1
        """, (kajabi_sub_id,))
        return self.cur.fetchone()

    def import_subscription(self, row: Dict):
        """Import or update a single subscription"""
        self.stats['subscriptions_processed'] += 1

        kajabi_sub_id = row['Kajabi Subscription ID'].strip()
        offer_id = row['Offer ID'].strip()
        offer_title = row['Offer Title'].strip()

        # Get or create product
        product_id = self.create_or_update_product(offer_id, offer_title)
        if not product_id:
            self.stats['errors'].append(f"Could not create product for offer {offer_id}")
            return

        # Get or create contact
        contact_id = self.create_or_update_contact(row)
        if not contact_id:
            return  # Error already logged

        # Parse subscription data
        amount = parse_amount(row['Amount'])
        status = map_status(row['Status'])
        created_at = parse_date(row['Created At'])
        trial_ends = parse_date(row['Trial Ends On'])
        canceled_on = parse_date(row['Canceled On'])
        next_payment = parse_date(row['Next Payment Date'])

        # Determine billing cycle
        interval = row['Interval'].lower()
        billing_cycle = 'annual' if 'year' in interval else 'monthly'
        is_annual = 'year' in interval

        # Check if subscription exists
        existing = self.get_subscription_by_kajabi_id(kajabi_sub_id)

        if existing:
            # Update existing subscription
            if not self.dry_run:
                self.cur.execute("""
                    UPDATE subscriptions
                    SET
                        status = %s,
                        amount = %s,
                        next_billing_date = %s,
                        cancellation_date = %s,
                        trial_end_date = %s,
                        updated_at = NOW()
                    WHERE kajabi_subscription_id = %s
                """, (status, amount, next_payment, canceled_on, trial_ends, kajabi_sub_id))
            self.stats['subscriptions_updated'] += 1
        else:
            # Create new subscription
            if not self.dry_run:
                self.cur.execute("""
                    INSERT INTO subscriptions (
                        contact_id, product_id, kajabi_subscription_id,
                        status, amount, currency, billing_cycle, is_annual,
                        start_date, trial_end_date, cancellation_date, next_billing_date,
                        payment_processor, coupon_code,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (kajabi_subscription_id) DO NOTHING
                """, (
                    contact_id, product_id, kajabi_sub_id,
                    status, amount, row['Currency'] or 'USD', billing_cycle, is_annual,
                    created_at, trial_ends, canceled_on, next_payment,
                    row['Provider'] or 'PayPal', row.get('Coupon Used')
                ))
            self.stats['subscriptions_new'] += 1

    def import_subscriptions_file(self, filepath: str):
        """Import all subscriptions from CSV file"""
        print(f"\n{'='*80}")
        print(f"KAJABI SUBSCRIPTIONS IMPORT - {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"{'='*80}\n")

        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return

        print(f"📄 Reading: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"📊 Found {len(rows)} subscriptions to process\n")

        for i, row in enumerate(rows):
            if i > 0 and i % 50 == 0:
                print(f"  Progress: {i}/{len(rows)} subscriptions...", end='\r')

            try:
                self.import_subscription(row)
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

        print(f"📋 Subscriptions:")
        print(f"  Processed: {self.stats['subscriptions_processed']}")
        print(f"  New: {self.stats['subscriptions_new']}")
        print(f"  Updated: {self.stats['subscriptions_updated']}")
        print(f"  Skipped: {self.stats['subscriptions_skipped']}")

        print(f"\n📇 Contacts:")
        print(f"  Created: {self.stats['contacts_created']}")
        print(f"  Updated: {self.stats['contacts_updated']}")

        print(f"\n📦 Products/Offers:")
        print(f"  Created: {self.stats['products_created']}")
        print(f"  Updated: {self.stats['products_updated']}")

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
        description='Weekly Kajabi Import - Optimized for manual weekly updates'
    )
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without committing')
    parser.add_argument('--execute', action='store_true', help='Execute import (make changes)')
    parser.add_argument('--subscriptions', default=DEFAULT_SUBSCRIPTIONS_FILE,
                       help=f'Path to Kajabi subscriptions CSV (default: {DEFAULT_SUBSCRIPTIONS_FILE})')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Error: Must specify either --dry-run or --execute")
        print("\nExamples:")
        print("  python3 scripts/weekly_import_kajabi.py --dry-run")
        print("  python3 scripts/weekly_import_kajabi.py --execute")
        sys.exit(1)

    # Create importer
    importer = KajabiImporter(DB_CONNECTION, dry_run=args.dry_run)

    try:
        # Import subscriptions
        importer.import_subscriptions_file(args.subscriptions)

        # Commit or rollback
        importer.commit_or_rollback()

        # Print stats
        importer.print_stats()

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()

if __name__ == '__main__':
    main()
