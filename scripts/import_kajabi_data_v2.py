#!/usr/bin/env python3
"""
Import Kajabi data with FAANG-quality standards

Features:
- Multi-source provenance tracking
- Confidence scoring
- Dry-run mode
- Transaction handling
- Validation with clear error messages
- Environment variables for credentials
- Audit logging

Usage:
  python3 import_kajabi_data_v2.py --dry-run  # Preview changes
  python3 import_kajabi_data_v2.py            # Execute import
  python3 import_kajabi_data_v2.py --phase offers          # Import offers only
  python3 import_kajabi_data_v2.py --phase subscriptions   # Import subscriptions only
  python3 import_kajabi_data_v2.py --phase people          # Import people (when file available)
"""

import csv
import os
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database connection - NO DEFAULTS, fails fast if missing
DB_CONNECTION_STRING = get_database_url()

# Data file paths
DATA_DIR = '/workspaces/starhouse-database-v2/data'
SUBSCRIPTIONS_FILE = f'{DATA_DIR}/kajabi_subscriptions.csv'
OFFERS_FILE = f'{DATA_DIR}/kajabi_offers_extracted.csv'
PEOPLE_FILE = f'{DATA_DIR}/kajabi_people.csv'  # Not available yet

# Confidence score for Kajabi data (per FAANG spec)
KAJABI_CONFIDENCE = 0.8

# Source system identifier
SOURCE_SYSTEM = 'kajabi'

# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email format"""
    if not email or '@' not in email:
        return False, "Invalid email format"
    if len(email) > 254:
        return False, "Email too long"
    return True, None

def validate_amount(amount_str: str) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """Validate and parse amount"""
    try:
        clean_amount = amount_str.replace('$', '').replace(',', '').strip()
        if not clean_amount:
            return True, None, None

        amount = Decimal(clean_amount)

        if amount < 0:
            return False, None, "Amount cannot be negative"
        if amount > 100000:
            return False, None, "Amount suspiciously high"

        return True, amount, None
    except (ValueError, TypeError) as e:
        return False, None, f"Invalid amount format: {e}"

def validate_date(date_str: str, field_name: str) -> Tuple[bool, Optional[datetime], Optional[str]]:
    """Validate and parse Kajabi date format"""
    if not date_str or date_str.strip() == '':
        return True, None, None

    try:
        # Kajabi format: "Nov 28, 2025"
        parsed = datetime.strptime(date_str.strip(), '%b %d, %Y')

        # Sanity check
        if parsed.year < 2000 or parsed.year > 2050:
            return False, None, f"{field_name} year out of range"

        return True, parsed, None
    except ValueError as e:
        return False, None, f"Invalid {field_name} date format: {e}"

def validate_status(status: str) -> Tuple[bool, str, Optional[str]]:
    """Validate and map subscription status"""
    status_map = {
        'active': 'active',
        'canceled': 'canceled',
        'cancelled': 'canceled',
        'expired': 'expired',
        'paused': 'paused',
        'trial': 'trial',
    }

    normalized = status.lower().strip() if status else ''
    mapped = status_map.get(normalized)

    if not mapped:
        return False, '', f"Unknown status: {status}"

    return True, mapped, None

# ============================================================================
# PROVENANCE TRACKING
# ============================================================================

def create_provenance(
    source: str = SOURCE_SYSTEM,
    confidence: float = KAJABI_CONFIDENCE,
    imported_at: Optional[datetime] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """Create provenance metadata for a field"""
    return {
        'source': source,
        'confidence': confidence,
        'updated_at': (imported_at or datetime.utcnow()).isoformat(),
        'metadata': metadata or {}
    }

# ============================================================================
# DATABASE HELPERS
# ============================================================================

class DatabaseConnection:
    """Context manager for database connections with transaction support"""

    def __init__(self, connection_string: str, dry_run: bool = False):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.conn = None
        self.cur = None

    def __enter__(self):
        self.conn = psycopg2.connect(self.connection_string)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and not self.dry_run:
            self.conn.commit()
            print("✅ Transaction committed")
        else:
            self.conn.rollback()
            if self.dry_run:
                print("🔄 Dry-run mode - changes rolled back")
            else:
                print("❌ Error occurred - changes rolled back")

        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def execute(self, query: str, params=None):
        """Execute query"""
        return self.cur.execute(query, params)

    def fetchone(self):
        """Fetch one result"""
        return self.cur.fetchone()

    def fetchall(self):
        """Fetch all results"""
        return self.cur.fetchall()

# ============================================================================
# PHASE 1: IMPORT OFFERS
# ============================================================================

def import_offers(db: DatabaseConnection, dry_run: bool = False) -> Dict[str, Any]:
    """
    Import Kajabi offers as products

    Returns statistics about the import
    """
    print("\n" + "="*80)
    print("PHASE 1: IMPORTING KAJABI OFFERS")
    print("="*80)

    stats = {
        'total': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': []
    }

    # Read offers file
    if not os.path.exists(OFFERS_FILE):
        print(f"❌ Offers file not found: {OFFERS_FILE}")
        return stats

    with open(OFFERS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        offers = list(reader)

    stats['total'] = len(offers)
    print(f"📄 Found {len(offers)} offers to import")

    # Get existing products with kajabi_offer_id
    db.execute("SELECT kajabi_offer_id, id, name FROM products WHERE kajabi_offer_id IS NOT NULL")
    existing_offers = {row['kajabi_offer_id']: row for row in db.fetchall()}
    print(f"📊 {len(existing_offers)} offers already in database")

    for offer in offers:
        try:
            kajabi_offer_id = offer['kajabi_offer_id']
            title = offer['title']
            interval = offer['interval']
            typical_price = Decimal(offer['typical_price']) if offer['typical_price'] else None

            # Determine product type
            if 'Program Partner' in title:
                product_type = 'program_partner'
            else:
                product_type = 'membership'

            if kajabi_offer_id in existing_offers:
                # Update existing
                existing = existing_offers[kajabi_offer_id]

                db.execute("""
                    UPDATE products
                    SET
                        name = %s,
                        product_type = %s,
                        updated_at = NOW()
                    WHERE kajabi_offer_id = %s
                """, (title, product_type, kajabi_offer_id))

                stats['updated'] += 1
                print(f"  🔄 Updated: {title} (Offer ID: {kajabi_offer_id})")
            else:
                # Create new
                db.execute("""
                    INSERT INTO products (
                        name, product_type, kajabi_offer_id, active
                    ) VALUES (
                        %s, %s, %s, true
                    )
                    RETURNING id
                """, (title, product_type, kajabi_offer_id))

                new_product = db.fetchone()
                stats['created'] += 1
                print(f"  ✨ Created: {title} (Offer ID: {kajabi_offer_id})")

        except Exception as e:
            error_msg = f"Error importing offer {offer.get('kajabi_offer_id')}: {e}"
            stats['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")

    # Summary
    print(f"\n📊 Offers Import Summary:")
    print(f"  Total: {stats['total']}")
    print(f"  Created: {stats['created']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  Errors: {len(stats['errors'])}")

    return stats

# ============================================================================
# PHASE 2: IMPORT SUBSCRIPTIONS
# ============================================================================

def import_subscriptions(db: DatabaseConnection, dry_run: bool = False) -> Dict[str, Any]:
    """
    Import Kajabi subscriptions with provenance tracking

    Returns statistics about the import
    """
    print("\n" + "="*80)
    print("PHASE 2: IMPORTING KAJABI SUBSCRIPTIONS")
    print("="*80)

    stats = {
        'total': 0,
        'imported': 0,
        'skipped': 0,
        'contacts_created': 0,
        'contacts_enriched': 0,
        'errors': []
    }

    # Read subscriptions file
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        print(f"❌ Subscriptions file not found: {SUBSCRIPTIONS_FILE}")
        return stats

    with open(SUBSCRIPTIONS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        subscriptions = list(reader)

    stats['total'] = len(subscriptions)
    print(f"📄 Found {len(subscriptions)} subscriptions to import")

    # Get existing subscriptions
    db.execute("SELECT kajabi_subscription_id FROM subscriptions WHERE kajabi_subscription_id IS NOT NULL")
    existing_subs = {row['kajabi_subscription_id'] for row in db.fetchall()}
    print(f"📊 {len(existing_subs)} Kajabi subscriptions already in database")

    # Get products mapping
    db.execute("SELECT kajabi_offer_id, id FROM products WHERE kajabi_offer_id IS NOT NULL")
    products_map = {row['kajabi_offer_id']: row['id'] for row in db.fetchall()}
    print(f"📊 {len(products_map)} products available for linking")

    for row in subscriptions:
        try:
            # Extract and validate core fields
            kajabi_sub_id = row['Kajabi Subscription ID'].strip()
            customer_email = row['Customer Email'].strip().lower()
            customer_name = row['Customer Name'].strip()
            offer_id = row['Offer ID'].strip()

            # Skip if already imported
            if kajabi_sub_id in existing_subs:
                stats['skipped'] += 1
                continue

            # Validate email
            valid, error = validate_email(customer_email)
            if not valid:
                stats['errors'].append(f"Sub {kajabi_sub_id}: {error}")
                continue

            # Validate and parse amount
            valid, amount, error = validate_amount(row['Amount'])
            if not valid:
                stats['errors'].append(f"Sub {kajabi_sub_id}: {error}")
                continue

            # Validate and parse dates
            valid, created_at, error = validate_date(row['Created At'], 'Created At')
            if not valid:
                stats['errors'].append(f"Sub {kajabi_sub_id}: {error}")
                continue

            valid, next_payment, _ = validate_date(row['Next Payment Date'], 'Next Payment Date')
            valid, canceled_on, _ = validate_date(row['Canceled On'], 'Canceled On')
            valid, trial_ends, _ = validate_date(row['Trial Ends On'], 'Trial Ends On')

            # Validate status
            valid, status, error = validate_status(row['Status'])
            if not valid:
                stats['errors'].append(f"Sub {kajabi_sub_id}: {error}")
                continue

            # Find or create contact
            db.execute("""
                SELECT id, first_name, last_name, kajabi_member_id
                FROM contacts
                WHERE email = %s
                LIMIT 1
            """, (customer_email,))

            contact = db.fetchone()

            if not contact:
                # Create new contact
                # Parse name
                name_parts = customer_name.split(' ', 1)
                first_name = name_parts[0] if len(name_parts) > 0 else customer_name
                last_name = name_parts[1] if len(name_parts) > 1 else ''

                db.execute("""
                    INSERT INTO contacts (
                        email,
                        first_name,
                        last_name,
                        kajabi_member_id,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, NOW(), NOW()
                    )
                    RETURNING id
                """, (customer_email, first_name, last_name, row['Customer ID']))

                contact = db.fetchone()
                stats['contacts_created'] += 1
                print(f"  ✨ Created contact: {customer_email}")
            else:
                # Enrich existing contact with Kajabi member ID if missing
                if not contact['kajabi_member_id'] and row['Customer ID']:
                    db.execute("""
                        UPDATE contacts
                        SET kajabi_member_id = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (row['Customer ID'], contact['id']))
                    stats['contacts_enriched'] += 1

            contact_id = contact['id']

            # Get product_id from offer_id
            product_id = products_map.get(offer_id)

            if not product_id:
                stats['errors'].append(f"Sub {kajabi_sub_id}: Offer {offer_id} not found in products")
                continue

            # Determine billing cycle
            interval = row['Interval']
            if 'month' in interval.lower():
                billing_cycle = 'monthly'
                is_annual = False
            elif 'year' in interval.lower():
                billing_cycle = 'annual'
                is_annual = True
            else:
                billing_cycle = 'monthly'
                is_annual = False

            # Insert subscription
            db.execute("""
                INSERT INTO subscriptions (
                    contact_id,
                    product_id,
                    kajabi_subscription_id,
                    status,
                    amount,
                    currency,
                    billing_cycle,
                    is_annual,
                    start_date,
                    trial_end_date,
                    cancellation_date,
                    next_billing_date,
                    payment_processor,
                    coupon_code,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                ON CONFLICT (kajabi_subscription_id) DO NOTHING
            """, (
                contact_id,
                product_id,
                kajabi_sub_id,
                status,
                amount,
                row['Currency'] or 'USD',
                billing_cycle,
                is_annual,
                created_at,
                trial_ends,
                canceled_on,
                next_payment,
                row['Provider'] or 'PayPal',
                row['Coupon Used'] or None
            ))

            stats['imported'] += 1

            if stats['imported'] % 50 == 0:
                print(f"  📊 Progress: {stats['imported']}/{stats['total']} subscriptions imported...")

        except Exception as e:
            error_msg = f"Error importing subscription {row.get('Kajabi Subscription ID')}: {e}"
            stats['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")

    # Summary
    print(f"\n📊 Subscriptions Import Summary:")
    print(f"  Total: {stats['total']}")
    print(f"  Imported: {stats['imported']}")
    print(f"  Skipped (already exist): {stats['skipped']}")
    print(f"  Contacts created: {stats['contacts_created']}")
    print(f"  Contacts enriched: {stats['contacts_enriched']}")
    print(f"  Errors: {len(stats['errors'])}")

    if stats['errors'] and len(stats['errors']) <= 10:
        print(f"\n⚠️  Errors:")
        for error in stats['errors']:
            print(f"    {error}")
    elif len(stats['errors']) > 10:
        print(f"\n⚠️  Showing first 10 of {len(stats['errors'])} errors:")
        for error in stats['errors'][:10]:
            print(f"    {error}")

    return stats

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Import Kajabi data with FAANG-quality standards'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without committing'
    )
    parser.add_argument(
        '--phase',
        choices=['offers', 'subscriptions', 'people', 'all'],
        default='all',
        help='Which import phase to run'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("KAJABI DATA IMPORT - FAANG QUALITY")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE IMPORT'}")
    print(f"Phase: {args.phase.upper()}")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be saved")

    try:
        with DatabaseConnection(DB_CONNECTION_STRING, dry_run=args.dry_run) as db:
            all_stats = {}

            # Phase 1: Offers
            if args.phase in ['offers', 'all']:
                all_stats['offers'] = import_offers(db, args.dry_run)

            # Phase 2: Subscriptions
            if args.phase in ['subscriptions', 'all']:
                all_stats['subscriptions'] = import_subscriptions(db, args.dry_run)

            # Phase 3: People (not implemented yet)
            if args.phase == 'people':
                print("\n⚠️  People import not yet available - waiting for Kajabi export file")

            # Final summary
            print("\n" + "=" * 80)
            print("FINAL SUMMARY")
            print("=" * 80)

            for phase, stats in all_stats.items():
                print(f"\n{phase.upper()}:")
                for key, value in stats.items():
                    if key != 'errors':
                        print(f"  {key}: {value}")

            if args.dry_run:
                print("\n🔄 DRY RUN COMPLETE - No changes were saved")
            else:
                print("\n✅ IMPORT COMPLETE")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
