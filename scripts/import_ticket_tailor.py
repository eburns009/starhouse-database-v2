#!/usr/bin/env python3
"""
TICKET TAILOR EVENT ORDERS IMPORT
==================================

Imports Ticket Tailor event order export and creates:
- Transaction records for ticket purchases
- Contact records for new attendees
- Enrichment of existing contacts with phone/address data

This script follows FAANG-level production standards:
- Comprehensive error handling and recovery
- Transaction safety with rollback support
- Detailed logging and observability
- Data validation and sanitization
- Idempotent operations (safe to re-run)
- Performance optimization with batching and caching

Usage:
  # Dry-run (recommended first - no changes committed)
  python3 scripts/import_ticket_tailor.py \\
    --file "kajabi 3 files review/ticket_tailor_data.csv" \\
    --dry-run

  # Execute import with full commit
  python3 scripts/import_ticket_tailor.py \\
    --file "kajabi 3 files review/ticket_tailor_data.csv" \\
    --execute

Author: StarHouse Development Team
Date: 2025-11-08
Version: 1.0.0
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2 import errors as pg_errors
from dotenv import load_dotenv
import re

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

BATCH_SIZE = 100

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

@dataclass
class TicketTailorOrder:
    """Structured representation of a Ticket Tailor order."""
    # Order fields
    order_id: str
    order_date: datetime
    total_paid: Decimal
    order_value: Decimal
    remaining_value: Decimal
    tickets_purchased: int
    order_items: str

    # Payment fields
    payment_method: str
    transaction_id: Optional[str]
    payg_fees: Decimal

    # Status fields
    cancelled: bool
    refunded_amount: Decimal

    # Contact fields
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    phone: Optional[str]

    # Address fields
    address_1: Optional[str]
    address_2: Optional[str]
    address_3: Optional[str]
    postcode: Optional[str]

    # Event fields
    event_id: str
    event_name: str
    event_start: Optional[datetime]
    event_end: Optional[datetime]

    # Marketing
    email_opt_in: bool

    # Raw data
    raw_data: Dict


# ============================================================================
# DATA PARSING
# ============================================================================

def parse_ticket_tailor_date(date_str: str) -> Optional[datetime]:
    """
    Parse Ticket Tailor date format: "Nov 7, 2025 2:28 PM" or "Sat Nov 8, 2025 7:15 PM"

    Args:
        date_str: Date string from Ticket Tailor

    Returns:
        Parsed datetime or None if invalid
    """
    if not date_str or not date_str.strip():
        return None

    try:
        # Try with day of week first (e.g., "Sat Nov 8, 2025 7:15 PM")
        return datetime.strptime(date_str.strip(), "%a %b %d, %Y %I:%M %p")
    except (ValueError, AttributeError):
        pass

    try:
        # Try without day of week (e.g., "Nov 7, 2025 2:28 PM")
        return datetime.strptime(date_str.strip(), "%b %d, %Y %I:%M %p")
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date: {date_str}", extra={'error': str(e)})
        return None


def normalize_email(email: str) -> Optional[str]:
    """Normalize email for matching."""
    if not email:
        return None
    email = email.strip().lower().rstrip('.,;')
    return email if validate_email(email) else None


def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone to digits only."""
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    return digits if len(digits) >= 10 else None


def parse_ticket_tailor_order(row: Dict) -> Optional[TicketTailorOrder]:
    """
    Parse a Ticket Tailor CSV row into structured order.

    Args:
        row: Dictionary from CSV DictReader

    Returns:
        TicketTailorOrder instance or None if critical fields missing
    """
    try:
        # Required fields
        order_id = row.get('Order ID', '').strip()
        if not order_id:
            raise ValueError("Missing Order ID")

        email = normalize_email(row.get('Email', ''))
        if not email:
            raise ValueError(f"Invalid email for order {order_id}")

        # Parse amounts
        total_paid = parse_decimal(row.get('Total paid', '0'))
        order_value = parse_decimal(row.get('Order value', '0'))
        remaining_value = parse_decimal(row.get('Remaining order value', '0'))
        refunded_amount = parse_decimal(row.get('Refunded amount', '0'))
        payg_fees = parse_decimal(row.get('PAYG fees', '0'))

        # Parse date
        order_date = parse_ticket_tailor_date(row.get('Order date', ''))
        if not order_date:
            raise ValueError(f"Invalid order date for order {order_id}")

        # Parse event dates
        event_start = parse_ticket_tailor_date(row.get('Event start', ''))
        event_end = parse_ticket_tailor_date(row.get('Event end', ''))

        # Parse tickets
        try:
            tickets_purchased = int(row.get('Tickets purchased', '1'))
        except (ValueError, TypeError):
            tickets_purchased = 1

        # Parse name
        first_name = sanitize_string(row.get('First Name', ''), 100) or None
        last_name = sanitize_string(row.get('Last Name', ''), 100) or None
        full_name = sanitize_string(row.get('Name', ''), 200)

        if not full_name:
            full_name = f"{first_name} {last_name}".strip() if first_name or last_name else "Unknown"

        # Parse contact info
        phone = row.get('Mobile number', '').strip() or None

        # Parse address
        address_1 = sanitize_string(row.get('Address 1', ''), 200) or None
        address_2 = sanitize_string(row.get('Address 2', ''), 200) or None
        address_3 = sanitize_string(row.get('Address 3', ''), 200) or None
        postcode = row.get('Postcode / Zip', '').strip() or None

        # Parse event info
        event_id = row.get('Event ID', '').strip()
        event_name = sanitize_string(row.get('Event name', 'Unknown Event'), 500)

        # Parse payment method
        payment_method = row.get('Payment method', 'UNKNOWN').strip()
        transaction_id = row.get('Transaction ID', '').strip() or None

        # Parse status
        cancelled = row.get('Order cancelled', '0').strip() == '1'

        # Parse email opt-in
        email_opt_in_str = row.get('Are you open to receive emails from StarHouse?', 'No').strip()
        email_opt_in = email_opt_in_str.lower() in ['yes', 'y', '1', 'true']

        return TicketTailorOrder(
            order_id=order_id,
            order_date=order_date,
            total_paid=total_paid,
            order_value=order_value,
            remaining_value=remaining_value,
            tickets_purchased=tickets_purchased,
            order_items=sanitize_string(row.get('Order items', ''), 500),
            payment_method=payment_method,
            transaction_id=transaction_id,
            payg_fees=payg_fees,
            cancelled=cancelled,
            refunded_amount=refunded_amount,
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            phone=phone,
            address_1=address_1,
            address_2=address_2,
            address_3=address_3,
            postcode=postcode,
            event_id=event_id,
            event_name=event_name,
            event_start=event_start,
            event_end=event_end,
            email_opt_in=email_opt_in,
            raw_data=row
        )

    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse Ticket Tailor order: {e}", extra={'row': row})
        return None


# ============================================================================
# CONTACT MATCHING
# ============================================================================

def find_contact_by_email(cursor, email: str, cache: Dict = None) -> Optional[Dict]:
    """Find contact by email (with caching)."""
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    if cache is not None and normalized_email in cache:
        return cache[normalized_email]

    cursor.execute("""
        SELECT id, email, first_name, last_name, phone, address_line_1
        FROM contacts
        WHERE email = %s
        LIMIT 1
    """, (normalized_email,))

    result = cursor.fetchone()

    if cache is not None and result:
        cache[normalized_email] = result

    return result


# ============================================================================
# CONTACT ENRICHMENT
# ============================================================================

def enrich_contact(cursor, contact_id: str, order: TicketTailorOrder) -> List[str]:
    """
    Enrich contact with Ticket Tailor data.

    FAANG Standards:
    - Only update empty fields (never overwrite existing data)
    - Track email subscription opt-in
    - Maintain data provenance
    - Validate before updating

    Args:
        cursor: Database cursor
        contact_id: UUID of contact to enrich
        order: Parsed Ticket Tailor order

    Returns:
        List of fields that were updated
    """
    updates = {}

    cursor.execute("""
        SELECT phone, address_line_1, address_line_2, city, state, postal_code,
               email_subscribed
        FROM contacts
        WHERE id = %s
    """, (contact_id,))

    contact = cursor.fetchone()
    if not contact:
        logger.error(f"Contact {contact_id} not found for enrichment")
        return []

    # Add phone if missing
    if order.phone and not contact.get('phone'):
        normalized_new = normalize_phone(order.phone)
        normalized_existing = normalize_phone(contact.get('phone'))

        if normalized_new and normalized_new != normalized_existing:
            updates['phone'] = order.phone

    # Add address if missing
    if order.address_1 and not contact.get('address_line_1'):
        updates['address_line_1'] = order.address_1
        if order.address_2:
            updates['address_line_2'] = order.address_2
        if order.postcode:
            updates['postal_code'] = order.postcode
        # Default to US for now
        updates['country'] = 'US'

    # Update email subscription status if opted in
    # FAANG: Only update to true if explicitly opted in, never force to false
    if order.email_opt_in and not contact.get('email_subscribed'):
        updates['email_subscribed'] = True

    if updates:
        set_clauses = [f"{key} = %s" for key in updates.keys()]
        values = list(updates.values()) + [contact_id]

        cursor.execute(f"""
            UPDATE contacts
            SET {', '.join(set_clauses)},
                updated_at = NOW()
            WHERE id = %s
        """, values)

        logger.debug(f"Enriched contact {contact_id} with fields: {list(updates.keys())}")

    return list(updates.keys())


# ============================================================================
# TRANSACTION IMPORT
# ============================================================================

def import_ticket_tailor_order(cursor, order: TicketTailorOrder,
                               email_cache: Dict = None,
                               stats: Dict = None) -> Tuple[bool, Optional[str]]:
    """
    Import a single Ticket Tailor order as a transaction.

    Returns:
        (success, contact_id)
    """
    try:
        # Check if transaction already exists
        cursor.execute("""
            SELECT id FROM transactions
            WHERE external_order_id = %s AND source_system = 'ticket_tailor'
        """, (order.order_id,))

        if cursor.fetchone():
            logger.debug(f"Order {order.order_id} already exists, skipping")
            return False, None

        # Find or create contact
        contact = find_contact_by_email(cursor, order.email, email_cache)

        contact_id = None
        if contact:
            contact_id = contact['id']
            # Enrich existing contact
            enriched_fields = enrich_contact(cursor, contact_id, order)
            if enriched_fields and stats:
                stats['contacts_enriched'] += 1
        else:
            # Create new contact
            # FAANG: Set email subscription status at creation time
            cursor.execute("""
                INSERT INTO contacts (
                    email, first_name, last_name, phone,
                    address_line_1, address_line_2, postal_code, country,
                    source_system, email_subscribed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                order.email,
                order.first_name,
                order.last_name,
                order.phone,
                order.address_1,
                order.address_2,
                order.postcode,
                'US',
                'ticket_tailor',
                order.email_opt_in  # True if they opted in, False otherwise
            ))

            contact_id = cursor.fetchone()['id']
            if stats:
                stats['contacts_created'] += 1
            logger.info(f"Created new contact: {contact_id}")

        # Determine transaction type and status
        if order.cancelled:
            transaction_type = 'refund'
            status = 'cancelled'
        elif order.refunded_amount > 0:
            transaction_type = 'refund'
            status = 'refunded'
        else:
            # All tickets (paid and free) are purchases
            transaction_type = 'purchase'
            status = 'completed'

        # Map payment method to processor
        processor_map = {
            'PAYPAL': 'PayPal',
            'NO_COST': 'Free',
            'STRIPE': 'Stripe',
        }
        processor = processor_map.get(order.payment_method, order.payment_method)

        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (
                contact_id,
                external_transaction_id,
                external_order_id,
                transaction_date,
                transaction_type,
                status,
                amount,
                currency,
                quantity,
                payment_method,
                payment_processor,
                source_system,
                raw_source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            contact_id,
            order.transaction_id,  # PayPal transaction ID
            order.order_id,        # Ticket Tailor order ID
            order.order_date,
            transaction_type,
            status,
            order.total_paid,
            'USD',
            order.tickets_purchased,
            order.payment_method,
            processor,
            'ticket_tailor',
            Json({
                'event_id': order.event_id,
                'event_name': order.event_name,
                'event_start': order.event_start.isoformat() if order.event_start else None,
                'event_end': order.event_end.isoformat() if order.event_end else None,
                'order_items': order.order_items,
                'order_value': str(order.order_value),
                'refunded_amount': str(order.refunded_amount),
                'payg_fees': str(order.payg_fees),
                'email_opt_in': order.email_opt_in,
                'import_source': 'ticket_tailor_csv',
                'full_name': order.full_name
            })
        ))

        return True, contact_id

    except Exception as e:
        logger.error(f"Error importing order {order.order_id}: {e}")
        raise


# ============================================================================
# MAIN IMPORT PROCESS
# ============================================================================

def import_ticket_tailor(file_path: str, dry_run: bool = True) -> Dict:
    """
    Import Ticket Tailor orders and create transactions.

    Returns:
        Statistics dictionary
    """
    stats = {
        'total_rows': 0,
        'transactions_imported': 0,
        'transactions_skipped': 0,
        'contacts_created': 0,
        'contacts_enriched': 0,
        'parse_errors': 0,
        'import_errors': 0,
        'email_cache_hits': 0,
    }

    conn = None
    email_cache = {}

    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.set_session(autocommit=False)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info(f"Starting Ticket Tailor import from {file_path} (dry_run={dry_run})")

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    stats['total_rows'] += 1

                    # Parse order
                    order = parse_ticket_tailor_order(row)
                    if not order:
                        stats['parse_errors'] += 1
                        continue

                    # Import order
                    try:
                        success, contact_id = import_ticket_tailor_order(
                            cursor, order, email_cache, stats
                        )

                        if success:
                            stats['transactions_imported'] += 1
                        else:
                            stats['transactions_skipped'] += 1

                        # Commit in batches
                        if stats['total_rows'] % BATCH_SIZE == 0:
                            if dry_run:
                                conn.rollback()
                            else:
                                conn.commit()

                            logger.info(
                                f"Processed {stats['total_rows']} rows - "
                                f"imported: {stats['transactions_imported']}, "
                                f"skipped: {stats['transactions_skipped']}, "
                                f"errors: {stats['import_errors']}"
                            )

                    except Exception as e:
                        logger.error(f"Error processing row {stats['total_rows']}: {e}")
                        stats['import_errors'] += 1
                        conn.rollback()

            # Final commit
            if dry_run:
                conn.rollback()
                logger.info("DRY RUN: All changes rolled back")
            else:
                conn.commit()
                logger.info("All changes committed successfully")

        logger.info("Import complete!")
        logger.info(f"Statistics: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Fatal error during import: {e}")
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Import Ticket Tailor event orders',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--file', required=True, help='Path to Ticket Tailor CSV export')
    parser.add_argument('--dry-run', action='store_true', help='Run without committing changes')
    parser.add_argument('--execute', action='store_true', help='Execute and commit changes')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)

    if not os.path.exists(args.file):
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    dry_run = args.dry_run

    print("\n" + "="*80)
    print("TICKET TAILOR EVENT ORDERS IMPORT")
    print("="*80)
    print(f"File: {args.file}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'EXECUTE (will commit changes)'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    try:
        stats = import_ticket_tailor(args.file, dry_run=dry_run)

        print("\n" + "="*80)
        print("IMPORT COMPLETE")
        print("="*80)
        print(f"Total rows processed: {stats['total_rows']:,}")
        print(f"Transactions imported: {stats['transactions_imported']:,}")
        print(f"Transactions skipped (duplicates): {stats['transactions_skipped']:,}")
        print(f"Contacts created: {stats['contacts_created']:,}")
        print(f"Contacts enriched: {stats['contacts_enriched']:,}")
        print(f"Parse errors: {stats['parse_errors']:,}")
        print(f"Import errors: {stats['import_errors']:,}")
        print("="*80 + "\n")

        if dry_run:
            print("DRY RUN MODE: No changes were committed to the database")
            print("Run with --execute to commit changes\n")
        else:
            print("Changes committed to database successfully\n")

    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
