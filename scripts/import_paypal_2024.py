#!/usr/bin/env python3
"""
PAYPAL 2024 IMPORT AND CONTACT ENRICHMENT
==========================================

Imports PayPal 2024 CSV export and enriches contact records with:
- Transaction data
- Phone numbers (using fuzzy matching)
- Email addresses (using fuzzy matching)
- Address information
- Alternate names

This script uses fuzzy matching to identify contacts and add additional
contact information to the contacts table.

Usage:
  # Dry-run (recommended first)
  python3 scripts/import_paypal_2024.py --file "kajabi 3 files review/paypal 2024.CSV" --dry-run

  # Execute import and enrichment
  python3 scripts/import_paypal_2024.py --file "kajabi 3 files review/paypal 2024.CSV" --execute
"""

import csv
import os
import sys
import argparse
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Set
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values, Json
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
# FUZZY MATCHING UTILITIES
# ============================================================================

def normalize_email(email: str) -> Optional[str]:
    """Normalize email for matching."""
    if not email:
        return None
    email = email.strip().lower()
    return email if validate_email(email) else None

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number for matching (digits only)."""
    if not phone:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Must be at least 10 digits
    return digits if len(digits) >= 10 else None

def normalize_name(name: str) -> Optional[str]:
    """Normalize name for fuzzy matching."""
    if not name:
        return None
    # Convert to lowercase, remove extra spaces
    name = ' '.join(name.lower().split())
    return name if name else None

def parse_paypal_name(name_str: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse PayPal name format.

    Returns: (first_name, last_name, full_name)
    """
    if not name_str:
        return None, None, None

    full_name = sanitize_string(name_str, 200)

    # Try to split on comma (Last, First format)
    if ',' in name_str:
        parts = name_str.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip() if len(parts) > 1 else None
        return first_name, last_name, full_name

    # Try to split on space
    parts = name_str.strip().split()
    if len(parts) >= 2:
        first_name = parts[0]
        last_name = ' '.join(parts[1:])
        return first_name, last_name, full_name

    # Single name
    return name_str.strip(), None, full_name

def parse_paypal_datetime(date_str: str, time_str: str, timezone_str: str = None) -> Optional[datetime]:
    """Parse PayPal date/time format: MM/DD/YYYY HH:MM:SS."""
    try:
        datetime_str = f"{date_str} {time_str}"
        return datetime.strptime(datetime_str, "%m/%d/%Y %H:%M:%S")
    except (ValueError, AttributeError):
        return None

# ============================================================================
# CONTACT MATCHING
# ============================================================================

def find_contact_by_email(cursor, email: str, cache: Dict = None) -> Optional[Dict]:
    """Find contact by exact email match (with optional caching)."""
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    # Check cache first
    if cache is not None and normalized_email in cache:
        return cache[normalized_email]

    cursor.execute("""
        SELECT id, email, first_name, last_name, phone,
               paypal_phone, paypal_email,
               additional_phone, additional_email, additional_name
        FROM contacts
        WHERE email = %s OR paypal_email = %s OR additional_email = %s
        LIMIT 1
    """, (normalized_email, normalized_email, normalized_email))

    result = cursor.fetchone()

    # Cache the result
    if cache is not None and result:
        cache[normalized_email] = result

    return result

def find_contact_fuzzy(cursor, email: str = None, phone: str = None,
                       first_name: str = None, last_name: str = None,
                       cache: Dict = None, stats: Dict = None) -> Optional[Dict]:
    """
    Find contact using simple matching on email and phone.

    Priority:
    1. Exact email match (cached)
    2. Phone number match (digits only)
    """
    # Try email first (fastest, with caching)
    if email:
        contact = find_contact_by_email(cursor, email, cache)
        if contact:
            if cache and email in cache and stats:
                stats['contact_cache_hits'] = stats.get('contact_cache_hits', 0) + 1
            return contact

    # Try phone number (exact digits match)
    normalized_phone = normalize_phone(phone)
    if normalized_phone:
        cursor.execute("""
            SELECT id, email, first_name, last_name, phone,
                   paypal_phone, paypal_email,
                   additional_phone, additional_email, additional_name
            FROM contacts
            WHERE regexp_replace(phone, '[^0-9]', '', 'g') = %s
               OR regexp_replace(paypal_phone, '[^0-9]', '', 'g') = %s
               OR regexp_replace(additional_phone, '[^0-9]', '', 'g') = %s
            LIMIT 1
        """, (normalized_phone, normalized_phone, normalized_phone))

        contact = cursor.fetchone()
        if contact:
            return contact

    return None

# ============================================================================
# CONTACT ENRICHMENT
# ============================================================================

def enrich_contact(cursor, contact_id: str, transaction_data: Dict, source: str = 'paypal_2024') -> Dict:
    """
    Enrich contact with additional data from PayPal transaction.

    Returns dict with fields that were updated.
    """
    updates = {}

    # Get current contact data
    cursor.execute("""
        SELECT phone, paypal_phone, additional_phone,
               email, paypal_email, additional_email,
               additional_name,
               paypal_first_name, paypal_last_name,
               shipping_address_line_1, shipping_address_line_2,
               shipping_city, shipping_state, shipping_postal_code,
               shipping_country, shipping_address_status
        FROM contacts
        WHERE id = %s
    """, (contact_id,))

    contact = cursor.fetchone()
    if not contact:
        return updates

    # Check and add phone numbers
    new_phone = normalize_phone(transaction_data.get('phone'))
    if new_phone:
        existing_phones = {
            normalize_phone(contact.get('phone')),
            normalize_phone(contact.get('paypal_phone')),
            normalize_phone(contact.get('additional_phone'))
        }
        existing_phones.discard(None)

        if new_phone not in existing_phones:
            if not contact.get('paypal_phone'):
                updates['paypal_phone'] = transaction_data.get('phone')
                updates['phone_source'] = source
            elif not contact.get('additional_phone'):
                updates['additional_phone'] = transaction_data.get('phone')
                updates['additional_phone_source'] = source

    # Check and add email addresses
    new_email = normalize_email(transaction_data.get('from_email'))
    if new_email:
        existing_emails = {
            normalize_email(contact.get('email')),
            normalize_email(contact.get('paypal_email')),
            normalize_email(contact.get('additional_email'))
        }
        existing_emails.discard(None)

        if new_email not in existing_emails:
            if not contact.get('paypal_email'):
                updates['paypal_email'] = new_email
            elif not contact.get('additional_email'):
                updates['additional_email'] = new_email
                updates['additional_email_source'] = source

    # Check and add alternate name
    paypal_name = transaction_data.get('full_name')
    if paypal_name:
        contact_name = f"{contact.get('paypal_first_name', '')} {contact.get('paypal_last_name', '')}".strip()
        normalized_paypal = normalize_name(paypal_name)
        normalized_contact = normalize_name(contact_name)

        if normalized_paypal and normalized_paypal != normalized_contact:
            if not contact.get('additional_name'):
                updates['additional_name'] = paypal_name
                updates['additional_name_source'] = source

    # Update shipping address if empty or from PayPal
    if transaction_data.get('address_line_1') and not contact.get('shipping_address_line_1'):
        updates['shipping_address_line_1'] = transaction_data.get('address_line_1')
        updates['shipping_address_line_2'] = transaction_data.get('address_line_2')
        updates['shipping_city'] = transaction_data.get('city')
        updates['shipping_state'] = transaction_data.get('state')
        updates['shipping_postal_code'] = transaction_data.get('postal_code')
        updates['shipping_country'] = transaction_data.get('country')
        updates['shipping_address_status'] = transaction_data.get('address_status')
        updates['shipping_address_source'] = source

    # Execute update if we have changes
    if updates:
        set_clauses = [f"{key} = %s" for key in updates.keys()]
        values = list(updates.values()) + [contact_id]

        cursor.execute(f"""
            UPDATE contacts
            SET {', '.join(set_clauses)},
                updated_at = NOW()
            WHERE id = %s
        """, values)

    return updates

# ============================================================================
# TRANSACTION IMPORT
# ============================================================================

def parse_transaction_row(row: Dict) -> Optional[Dict]:
    """Parse a PayPal CSV row into transaction data."""
    try:
        # Parse name
        first_name, last_name, full_name = parse_paypal_name(row.get('Name', ''))

        # Parse amount
        gross = parse_decimal(row.get('Gross', '0'))
        fee = parse_decimal(row.get('Fee', '0'))
        net = parse_decimal(row.get('Net', '0'))

        # Parse datetime
        transaction_date = parse_paypal_datetime(
            row.get('Date', ''),
            row.get('Time', ''),
            row.get('TimeZone', '')
        )

        # Determine email (from customer, not to StarHouse)
        from_email = row.get('From Email Address', '').strip()
        to_email = row.get('To Email Address', '').strip()

        # Customer is the one paying TO StarHouse
        customer_email = from_email if to_email and 'starhouse' in to_email.lower() else to_email

        return {
            'transaction_id': row.get('Transaction ID', '').strip(),
            'transaction_date': transaction_date,
            'type': row.get('Type', '').strip(),
            'status': row.get('Status', '').strip(),
            'currency': row.get('Currency', 'USD').strip(),
            'gross': gross,
            'fee': fee,
            'net': net,
            'from_email': customer_email,
            'item_title': sanitize_string(row.get('Item Title', ''), 500),
            'phone': row.get('Contact Phone Number', '').strip(),
            'address_line_1': sanitize_string(row.get('Address Line 1', ''), 200),
            'address_line_2': sanitize_string(row.get('Address Line 2/District/Neighborhood', ''), 200),
            'city': sanitize_string(row.get('Town/City', ''), 100),
            'state': sanitize_string(row.get('State/Province/Region/County/Territory/Prefecture/Republic', ''), 100),
            'postal_code': row.get('Zip/Postal Code', '').strip(),
            'country': sanitize_string(row.get('Country', ''), 100),
            'address_status': row.get('Address Status', '').strip(),
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'reference_txn_id': row.get('Reference Txn ID', '').strip(),
            'invoice_number': row.get('Invoice Number', '').strip(),
            'note': sanitize_string(row.get('Note', ''), 1000),
        }
    except Exception as e:
        logger.error(f"Error parsing transaction row: {e}", extra={'row': row})
        return None

def import_transaction(cursor, txn_data: Dict, cache: Dict = None, stats: Dict = None) -> Tuple[bool, Optional[str]]:
    """
    Import a single PayPal transaction.

    Returns: (success, contact_id)
    """
    try:
        # Check if transaction already exists
        cursor.execute("""
            SELECT id FROM transactions
            WHERE external_transaction_id = %s AND source_system = 'paypal'
        """, (txn_data['transaction_id'],))

        if cursor.fetchone():
            logger.debug(f"Transaction {txn_data['transaction_id']} already exists, skipping")
            return False, None

        # Find or create contact (with caching)
        contact = find_contact_fuzzy(
            cursor,
            email=txn_data['from_email'],
            phone=txn_data['phone'],
            first_name=txn_data['first_name'],
            last_name=txn_data['last_name'],
            cache=cache,
            stats=stats
        )

        contact_id = None
        if contact:
            contact_id = contact['id']
            logger.debug(f"Found existing contact: {contact_id}")
        else:
            # Create new contact
            if not txn_data['from_email']:
                logger.warning(f"Cannot create contact without email for transaction {txn_data['transaction_id']}")
                return False, None

            cursor.execute("""
                INSERT INTO contacts (
                    email, first_name, last_name, phone,
                    source_system, paypal_phone, paypal_email,
                    shipping_address_line_1, shipping_address_line_2,
                    shipping_city, shipping_state, shipping_postal_code,
                    shipping_country, shipping_address_status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
            """, (
                txn_data['from_email'],
                txn_data['first_name'],
                txn_data['last_name'],
                txn_data['phone'],
                'paypal',
                txn_data['phone'],
                txn_data['from_email'],
                txn_data['address_line_1'],
                txn_data['address_line_2'],
                txn_data['city'],
                txn_data['state'],
                txn_data['postal_code'],
                txn_data['country'],
                txn_data['address_status']
            ))

            contact_id = cursor.fetchone()['id']
            logger.info(f"Created new contact: {contact_id}")

        # Insert transaction
        # Map PayPal status to our payment_status enum
        status_map = {
            'Completed': 'completed',
            'Pending': 'pending',
            'Refunded': 'refunded',
            'Reversed': 'failed',
            'Canceled': 'cancelled',
            'Denied': 'failed',
        }
        payment_status = status_map.get(txn_data['status'], 'pending')

        # Map PayPal type to our transaction_type enum
        # Check if this is an outgoing payment (StarHouse paying someone)
        amount = txn_data['gross']
        is_outgoing = amount < 0

        type_map = {
            'Subscription Payment': 'subscription',
            'Payment': 'purchase',
            'Website Payment': 'purchase',
            'Express Checkout Payment': 'purchase',
            'Payment Refund': 'refund',
            'Refund': 'refund',
            'General Payment': 'refund' if is_outgoing else 'purchase',  # Outgoing payments
        }
        transaction_type = type_map.get(txn_data['type'], 'purchase' if amount > 0 else 'refund')

        # Ensure refunds have negative amounts
        if transaction_type == 'refund' and amount > 0:
            amount = -amount

        cursor.execute("""
            INSERT INTO transactions (
                contact_id, external_transaction_id, transaction_date,
                transaction_type, amount, currency, status,
                payment_processor, source_system, raw_source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            contact_id,
            txn_data['transaction_id'],
            txn_data['transaction_date'],
            transaction_type,
            amount,
            txn_data['currency'],
            payment_status,
            'PayPal',
            'paypal',
            Json({
                'item_title': txn_data['item_title'],
                'fee': str(txn_data['fee']),
                'net': str(txn_data['net']),
                'reference_txn_id': txn_data['reference_txn_id'],
                'invoice_number': txn_data['invoice_number'],
                'note': txn_data['note'],
                'import_source': 'paypal_2024_csv',
                'original_type': txn_data['type'],
                'original_status': txn_data['status'],
                'full_name': txn_data['full_name'],
                'from_email': txn_data['from_email']
            })
        ))

        return True, contact_id

    except Exception as e:
        logger.error(f"Error importing transaction {txn_data.get('transaction_id')}: {e}")
        raise

# ============================================================================
# MAIN IMPORT PROCESS
# ============================================================================

def import_paypal_2024(file_path: str, dry_run: bool = True) -> Dict:
    """
    Import PayPal 2024 CSV and enrich contacts.

    Returns statistics dict.
    """
    stats = {
        'total_rows': 0,
        'transactions_imported': 0,
        'transactions_skipped': 0,
        'contacts_created': 0,
        'contacts_enriched': 0,
        'errors': 0,
        'contact_cache_hits': 0,
        'unique_contacts_enriched': 0
    }

    conn = None
    enrichment_map = {}  # contact_id -> latest transaction data (deduplicated)
    contact_cache = {}  # email -> contact record (for caching)

    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.set_session(autocommit=False)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info(f"Starting PayPal 2024 import from {file_path} (dry_run={dry_run})")

            # Read and import transactions
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                batch = []
                for row in reader:
                    stats['total_rows'] += 1

                    txn_data = parse_transaction_row(row)
                    if not txn_data:
                        stats['errors'] += 1
                        continue

                    try:
                        success, contact_id = import_transaction(cursor, txn_data, contact_cache, stats)

                        if success:
                            stats['transactions_imported'] += 1
                            if contact_id:
                                # Store for enrichment, but deduplicate by contact_id
                                # (keep most recent transaction data for each contact)
                                enrichment_map[contact_id] = txn_data
                        else:
                            stats['transactions_skipped'] += 1

                        # Commit in batches
                        if stats['total_rows'] % BATCH_SIZE == 0:
                            if dry_run:
                                conn.rollback()
                            else:
                                conn.commit()
                            logger.info(f"Processed {stats['total_rows']} rows - imported: {stats['transactions_imported']}, skipped: {stats['transactions_skipped']}, errors: {stats['errors']}")

                    except Exception as e:
                        logger.error(f"Error processing row {stats['total_rows']}: {e}")
                        stats['errors'] += 1
                        conn.rollback()

            # Final commit for transactions
            if dry_run:
                conn.rollback()
                logger.info("DRY RUN: All transaction imports rolled back")
            else:
                conn.commit()
                logger.info("Transaction imports committed")

            # Now enrich contacts with additional data (deduplicated)
            unique_contacts = len(enrichment_map)
            logger.info(f"Starting contact enrichment for {unique_contacts} unique contacts (from {stats['transactions_imported']} transactions)...")

            for contact_id, txn_data in enrichment_map.items():
                try:
                    updates = enrich_contact(cursor, contact_id, txn_data, 'paypal_2024')
                    if updates:
                        stats['contacts_enriched'] += 1
                        logger.debug(f"Enriched contact {contact_id} with: {list(updates.keys())}")
                except Exception as e:
                    logger.error(f"Error enriching contact {contact_id}: {e}")

            stats['unique_contacts_enriched'] = len(enrichment_map)

            # Commit enrichments
            if dry_run:
                conn.rollback()
                logger.info("DRY RUN: All enrichments rolled back")
            else:
                conn.commit()
                logger.info("Contact enrichments committed")

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
    parser = argparse.ArgumentParser(description='Import PayPal 2024 CSV and enrich contacts')
    parser.add_argument('--file', required=True, help='Path to PayPal 2024 CSV file')
    parser.add_argument('--dry-run', action='store_true', help='Run without committing changes')
    parser.add_argument('--execute', action='store_true', help='Execute the import (commits changes)')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)

    if not os.path.exists(args.file):
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    dry_run = args.dry_run

    print("\n" + "="*80)
    print("PAYPAL 2024 IMPORT AND CONTACT ENRICHMENT")
    print("="*80)
    print(f"File: {args.file}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'EXECUTE (will commit changes)'}")
    print("="*80 + "\n")

    try:
        stats = import_paypal_2024(args.file, dry_run=dry_run)

        print("\n" + "="*80)
        print("IMPORT COMPLETE")
        print("="*80)
        print(f"Total rows processed: {stats['total_rows']}")
        print(f"Transactions imported: {stats['transactions_imported']}")
        print(f"Transactions skipped (duplicates): {stats['transactions_skipped']}")
        print(f"Unique contacts enriched: {stats['unique_contacts_enriched']}")
        print(f"Contact fields updated: {stats['contacts_enriched']}")
        print(f"Contact cache hits: {stats.get('contact_cache_hits', 0)}")
        print(f"Errors: {stats['errors']}")
        print("="*80 + "\n")

        if dry_run:
            print("⚠️  DRY RUN MODE: No changes were committed to the database")
            print("    Run with --execute to commit changes\n")
        else:
            print("✅ Changes committed to database\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
