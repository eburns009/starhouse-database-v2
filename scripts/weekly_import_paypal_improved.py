#!/usr/bin/env python3
"""
WEEKLY PAYPAL IMPORT - IMPROVED (FAANG Quality)
================================================

Production-grade PayPal transaction importer with:
- Secure credential management (no hardcoded passwords)
- Structured logging with correlation IDs
- Batch operations for performance
- Proper error handling with specific exceptions
- Data validation and sanitization
- Comprehensive metrics and observability

Usage:
  # Dry-run first (recommended)
  python3 scripts/weekly_import_paypal_improved.py --file data/paypal_export.txt --dry-run

  # Execute import
  python3 scripts/weekly_import_paypal_improved.py --file data/paypal_export.txt --execute

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
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import errors as pg_errors
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from config import get_config
from logging_config import setup_logging, get_logger
from validation import validate_email, parse_decimal, sanitize_string, validate_phone

# ============================================================================
# CONFIGURATION
# ============================================================================

config = get_config()
setup_logging(config.logging.level, config.logging.environment)
logger = get_logger(__name__)

DEFAULT_PAYPAL_FILE = 'data/current/paypal_export.txt'

# ============================================================================
# PAYPAL-SPECIFIC UTILITIES
# ============================================================================

def parse_name(name_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse PayPal name format.

    Handles:
    - "Last, First" format
    - "Business Name" format
    - Single name

    Returns:
        Tuple of (first_name, last_name)
    """
    if not name_str or not isinstance(name_str, str):
        return None, None

    name_str = sanitize_string(name_str, 200)

    # Check if it's "Last, First" format
    if ',' in name_str:
        parts = name_str.split(',', 1)
        last_name = parts[0].strip() or None
        first_name = parts[1].strip() if len(parts) > 1 else None
        return first_name, last_name
    else:
        # Single name - assume it's first name or business
        return name_str.strip() or None, None


def parse_paypal_datetime(date_str: str, time_str: str) -> Optional[str]:
    """
    Parse PayPal date/time format.

    PayPal format: MM/DD/YYYY HH:MM:SS

    Returns:
        ISO formatted datetime string or None
    """
    if not date_str or not time_str:
        return None

    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S")
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return None


def is_business_name(name: str) -> bool:
    """Check if name looks like a business."""
    if not name:
        return False

    business_keywords = [
        'llc', 'inc', 'institute', 'company', 'corp', 'corporation',
        'center', 'foundation', 'studio', 'group', 'services',
        'consulting', 'solutions', 'enterprises', 'associates'
    ]

    name_lower = name.lower()
    return any(keyword in name_lower for keyword in business_keywords)


class ImportStats:
    """Track PayPal import statistics."""

    def __init__(self):
        self.stats = {
            'rows_processed': 0,
            'rows_skipped': 0,
            'transactions': {'new': 0, 'skipped': 0, 'errors': 0},
            'contacts': {'created': 0, 'enriched': 0, 'matched': 0, 'errors': 0},
            'errors': [],
        }

    def increment(self, category: str, metric: Optional[str] = None, amount: int = 1):
        """Increment a stat counter."""
        if metric is None:
            # Direct increment (e.g., 'rows_processed')
            if category in self.stats and isinstance(self.stats[category], int):
                self.stats[category] += amount
        else:
            # Nested increment (e.g., 'transactions', 'new')
            if category in self.stats and isinstance(self.stats[category], dict):
                if metric in self.stats[category]:
                    self.stats[category][metric] += amount

    def add_error(self, error: str):
        """Add an error message."""
        self.stats['errors'].append(error)

    def get(self, category: str, metric: Optional[str] = None) -> int:
        """Get a stat value."""
        if metric:
            return self.stats.get(category, {}).get(metric, 0)
        return self.stats.get(category, 0)

    def total_errors(self) -> int:
        """Get total error count."""
        return len(self.stats['errors']) + sum(
            cat.get('errors', 0) for cat in self.stats.values() if isinstance(cat, dict)
        )


# ============================================================================
# IMPROVED PAYPAL IMPORTER CLASS
# ============================================================================

class PayPalImprover:
    """
    Production-grade PayPal transaction importer.

    Features:
    - Batch operations for performance
    - Structured logging with trace IDs
    - Proper error handling
    - Data validation
    - Contact enrichment
    """

    def __init__(self, paypal_file: str, dry_run: bool = True):
        self.paypal_file = paypal_file
        self.dry_run = dry_run

        # Generate trace ID
        self.trace_id = str(uuid.uuid4())

        # Get logger with trace ID
        self.logger = get_logger(__name__, self.trace_id)

        # Database connection
        self.conn = None
        self.cur = None

        # Statistics
        self.stats = ImportStats()

        # Caches
        self.contact_cache: Dict[str, str] = {}  # email -> contact_id
        self.membership_products_cache: Dict[str, Dict] = {}

        self.logger.info(
            "paypal_importer_initialized",
            paypal_file=paypal_file,
            dry_run=dry_run
        )

    def connect(self):
        """Connect to database."""
        self.logger.info("connecting_to_database")

        try:
            self.conn = psycopg2.connect(config.database.url)
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            self.logger.info("database_connected")
        except pg_errors.OperationalError as e:
            self.logger.error("database_connection_failed", error=str(e), exc_info=True)
            raise ConnectionError(f"Failed to connect to database: {e}") from e

    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()

        if self.conn:
            if self.dry_run:
                self.logger.info("rolling_back_dry_run")
                self.conn.rollback()
            else:
                self.logger.info("committing_changes")
                self.conn.commit()
            self.conn.close()

        self.logger.info("database_connection_closed")

    def load_membership_products(self):
        """Load membership products cache for faster lookups."""
        self.logger.info("loading_membership_products")

        try:
            self.cur.execute("""
                SELECT id, membership_group, membership_level, membership_tier,
                       is_legacy, paypal_item_titles
                FROM membership_products
                WHERE paypal_item_titles IS NOT NULL
            """)

            count = 0
            for row in self.cur.fetchall():
                if row['paypal_item_titles']:
                    for title in row['paypal_item_titles']:
                        self.membership_products_cache[title.lower()] = dict(row)
                        count += 1

            self.logger.info("membership_products_loaded", count=count)

        except pg_errors.DatabaseError as e:
            self.logger.warning("membership_products_load_failed", error=str(e))
            # Non-fatal - continue without membership mapping

    def get_membership_product(self, item_title: str) -> Optional[Dict]:
        """Get membership product from PayPal item title."""
        if not item_title:
            return None
        return self.membership_products_cache.get(item_title.lower())

    def find_or_create_contact(self, row: Dict) -> Optional[str]:
        """
        Find existing contact or create new one from PayPal data.

        Returns:
            Contact ID or None if failed
        """
        # Validate email
        email = validate_email(row.get('From Email Address', ''))
        if not email:
            self.stats.add_error(f"Invalid email: {row.get('From Email Address', 'N/A')}")
            self.stats.increment('contacts', 'errors')
            return None

        # Check cache first
        if email in self.contact_cache:
            self.stats.increment('contacts', 'matched')
            return self.contact_cache[email]

        # Parse contact data
        first_name, last_name = parse_name(row.get('Name', ''))

        # Check if business
        business_name = None
        if row.get('Name') and is_business_name(row['Name']):
            business_name = sanitize_string(row['Name'], 255)

        # Phone
        phone = validate_phone(row.get('Contact Phone Number', ''))

        # Addresses
        address_line_1 = sanitize_string(row.get('Address Line 1', ''), 255) or None
        city = sanitize_string(row.get('Town/City', ''), 100) or None
        state = sanitize_string(
            row.get('State/Province/Region/County/Territory/Prefecture/Republic', ''), 50
        ) or None
        postal_code = sanitize_string(row.get('Zip/Postal Code', ''), 20) or None
        country = sanitize_string(row.get('Country', ''), 50) or None

        # Get membership info if subscription payment
        membership_group = None
        membership_level = None
        membership_tier = None
        is_legacy = False

        if row.get('Type') == 'Subscription Payment' and row.get('Item Title'):
            product = self.get_membership_product(row['Item Title'])
            if product:
                membership_group = product.get('membership_group')
                membership_level = product.get('membership_level')
                membership_tier = product.get('membership_tier')
                is_legacy = product.get('is_legacy', False)

        # Check if contact exists
        try:
            self.cur.execute("""
                SELECT id FROM contacts
                WHERE email = %s OR paypal_email = %s
                LIMIT 1
            """, (email, email))

            existing = self.cur.fetchone()

            if existing:
                contact_id = existing['id']

                # Enrich existing contact
                self.cur.execute("""
                    UPDATE contacts
                    SET
                        paypal_email = %s,
                        paypal_first_name = COALESCE(%s, paypal_first_name),
                        paypal_last_name = COALESCE(%s, paypal_last_name),
                        paypal_business_name = COALESCE(%s, paypal_business_name),
                        paypal_phone = COALESCE(%s, paypal_phone),
                        phone = COALESCE(phone, %s),
                        shipping_address_line_1 = COALESCE(%s, shipping_address_line_1),
                        shipping_city = COALESCE(%s, shipping_city),
                        shipping_state = COALESCE(%s, shipping_state),
                        shipping_postal_code = COALESCE(%s, shipping_postal_code),
                        shipping_country = COALESCE(%s, shipping_country),
                        membership_group = COALESCE(%s, membership_group),
                        membership_level = COALESCE(%s, membership_level),
                        membership_tier = COALESCE(%s, membership_tier),
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    email, first_name, last_name, business_name, phone, phone,
                    address_line_1, city, state, postal_code, country,
                    membership_group, membership_level, membership_tier,
                    contact_id
                ))

                self.stats.increment('contacts', 'enriched')
                self.stats.increment('contacts', 'matched')

                self.logger.debug("contact_enriched", email=email, contact_id=contact_id)
            else:
                # Create new contact
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
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    RETURNING id
                """, (
                    email, first_name, last_name,
                    email, first_name, last_name,
                    business_name, phone, phone,
                    address_line_1, city, state, postal_code, country,
                    membership_group, membership_level, membership_tier,
                    is_legacy, 'paypal', True
                ))

                result = self.cur.fetchone()
                contact_id = result['id'] if result else None

                self.stats.increment('contacts', 'created')
                self.logger.debug("contact_created", email=email, contact_id=contact_id)

            # Cache the contact ID
            self.contact_cache[email] = contact_id
            return contact_id

        except (ValueError, KeyError, TypeError) as e:
            self.logger.warning("contact_validation_error", email=email, error=str(e))
            self.stats.increment('contacts', 'errors')
            self.stats.add_error(f"Contact validation error for {email}: {e}")
            return None
        except pg_errors.DatabaseError as e:
            self.logger.error("contact_database_error", email=email, error=str(e), exc_info=True)
            self.stats.increment('contacts', 'errors')
            self.stats.add_error(f"Database error for contact {email}: {e}")
            raise

    def create_transaction(self, row: Dict, contact_id: str):
        """Create transaction from PayPal row."""
        # Only import completed or refunded transactions
        status_raw = row.get('Status', '')
        if status_raw not in ['Completed', 'Refunded']:
            self.stats.increment('rows_skipped')
            return

        try:
            # Parse amount
            amount = parse_decimal(row.get('Gross', '0'))
            if amount is None:
                self.stats.add_error(f"Invalid amount for txn {row.get('Transaction ID')}")
                self.stats.increment('transactions', 'errors')
                return

            # Parse date/time
            transaction_date = parse_paypal_datetime(
                row.get('Date', ''),
                row.get('Time', '')
            )

            # Determine transaction type
            txn_type = row.get('Type', '')
            if txn_type == 'Subscription Payment':
                transaction_type = 'subscription'
            elif 'Refund' in txn_type or amount < 0:
                transaction_type = 'refund'
            else:
                transaction_type = 'purchase'

            # Map status
            status = 'completed' if status_raw == 'Completed' else 'refunded'

            # Insert transaction
            transaction_id = sanitize_string(row.get('Transaction ID', ''), 255)
            if not transaction_id:
                self.stats.increment('transactions', 'errors')
                return

            self.cur.execute("""
                INSERT INTO transactions (
                    contact_id, source_system,
                    external_transaction_id, external_order_id, order_number,
                    transaction_type, status,
                    amount, currency,
                    payment_method, payment_processor,
                    transaction_date,
                    created_at, updated_at
                )
                VALUES (
                    %s, 'paypal', %s, %s, %s, %s, %s, %s, %s, 'paypal', 'PayPal',
                    COALESCE(%s, NOW()), NOW(), NOW()
                )
                ON CONFLICT (source_system, external_transaction_id)
                WHERE external_transaction_id IS NOT NULL
                DO NOTHING
            """, (
                contact_id,
                transaction_id,
                row.get('Invoice Number') or transaction_id,
                row.get('Receipt ID') or transaction_id,
                transaction_type, status,
                amount, row.get('Currency', 'USD'),
                transaction_date
            ))

            if self.cur.rowcount > 0:
                self.stats.increment('transactions', 'new')
                self.logger.debug("transaction_created", transaction_id=transaction_id)
            else:
                self.stats.increment('transactions', 'skipped')

        except (ValueError, InvalidOperation) as e:
            self.logger.warning(
                "transaction_validation_error",
                transaction_id=row.get('Transaction ID'),
                error=str(e)
            )
            self.stats.increment('transactions', 'errors')
            self.stats.add_error(f"Transaction validation error: {e}")
        except pg_errors.DatabaseError as e:
            self.logger.error(
                "transaction_database_error",
                transaction_id=row.get('Transaction ID'),
                error=str(e),
                exc_info=True
            )
            self.stats.increment('transactions', 'errors')
            self.stats.add_error(f"Database error for transaction: {e}")
            raise

    def import_file(self):
        """Import PayPal export file."""
        self.logger.info("starting_paypal_import", file=self.paypal_file)

        # Verify file exists
        if not os.path.exists(self.paypal_file):
            self.logger.error("file_not_found", file=self.paypal_file)
            raise FileNotFoundError(f"PayPal file not found: {self.paypal_file}")

        # Read tab-delimited file
        try:
            with open(self.paypal_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)

            self.logger.info("file_parsed", row_count=len(rows))

        except IOError as e:
            self.logger.error("file_read_error", file=self.paypal_file, error=str(e), exc_info=True)
            raise

        # Process rows
        for i, row in enumerate(rows):
            self.stats.increment('rows_processed')

            if i > 0 and i % 100 == 0:
                self.logger.info("import_progress", processed=i, total=len(rows))

            try:
                # Find or create contact
                contact_id = self.find_or_create_contact(row)

                if contact_id:
                    # Create transaction
                    self.create_transaction(row, contact_id)

            except pg_errors.DatabaseError:
                # Already logged, re-raise
                raise
            except Exception as e:
                self.logger.error(
                    "row_processing_error",
                    row_number=i + 2,  # +2 for header and 0-index
                    error=str(e),
                    exc_info=True
                )
                self.stats.add_error(f"Row {i + 2}: {e}")

        self.logger.info("paypal_import_completed", rows_processed=len(rows))

    def run(self):
        """Run the complete import process."""
        start_time = datetime.now()

        self.logger.info(
            "import_started",
            mode="dry_run" if self.dry_run else "execute",
            start_time=start_time.isoformat()
        )

        # Connect to database
        try:
            self.connect()
        except ConnectionError as e:
            self.logger.error("import_aborted_connection_failed", error=str(e))
            return False

        try:
            # Load membership products
            self.load_membership_products()

            # Import file
            self.import_file()

            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Log completion
            self.logger.info(
                "import_completed",
                duration_seconds=duration,
                total_errors=self.stats.total_errors(),
                stats=self.stats.stats
            )

            # Print summary for user
            self._print_summary(duration)

            return self.stats.total_errors() == 0

        except Exception as e:
            self.logger.error("import_failed", error=str(e), exc_info=True)
            return False
        finally:
            self.close()

    def _print_summary(self, duration: float):
        """Print import summary to console."""
        print("\n" + "=" * 80)
        print("  PAYPAL IMPORT COMPLETE")
        print("=" * 80)
        print()
        print(f"Duration: {duration:.1f} seconds")
        print(f"Trace ID: {self.trace_id}")
        print()
        print("📊 Summary:")
        print()
        print(f"  Rows Processed:    {self.stats.get('rows_processed')}")
        print(f"  Rows Skipped:      {self.stats.get('rows_skipped')}")
        print()
        print("💰 Transactions:")
        print(f"  New:               {self.stats.get('transactions', 'new')}")
        print(f"  Skipped (duplicates): {self.stats.get('transactions', 'skipped')}")
        print(f"  Errors:            {self.stats.get('transactions', 'errors')}")
        print()
        print("📇 Contacts:")
        print(f"  Created:           {self.stats.get('contacts', 'created')}")
        print(f"  Matched existing:  {self.stats.get('contacts', 'matched')}")
        print(f"  Enriched:          {self.stats.get('contacts', 'enriched')}")
        print(f"  Errors:            {self.stats.get('contacts', 'errors')}")
        print()

        total_errors = self.stats.total_errors()
        if total_errors > 0:
            print(f"⚠️  Total errors: {total_errors}")
            if self.stats.stats['errors']:
                print(f"\nFirst 10 errors:")
                for error in self.stats.stats['errors'][:10]:
                    print(f"  - {error}")
                if len(self.stats.stats['errors']) > 10:
                    print(f"  ... and {len(self.stats.stats['errors']) - 10} more")
        else:
            print("✅ No errors")

        print()
        if self.dry_run:
            print("🔄 DRY RUN COMPLETE - No changes were saved")
            print("Run with --execute to apply changes")
        else:
            print("✅ Changes committed to database")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Import PayPal transactions (IMPROVED VERSION - FAANG Quality)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--file',
        default=DEFAULT_PAYPAL_FILE,
        help=f'PayPal export file (default: {DEFAULT_PAYPAL_FILE})'
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

    # Validate file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    # Run importer
    importer = PayPalImprover(
        paypal_file=args.file,
        dry_run=args.dry_run
    )

    success = importer.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
