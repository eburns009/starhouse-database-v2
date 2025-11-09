#!/usr/bin/env python3
"""
ZOHO CRM CONTACT IMPORT AND ENRICHMENT
======================================

Imports Zoho CRM contact export and enriches existing contacts with:
- Primary contact data (name, email, phone)
- Mailing address information
- Zoho CRM ID for future synchronization
- Additional contact metadata

This script follows FAANG-level production standards:
- Comprehensive error handling and recovery
- Transaction safety with rollback support
- Detailed logging and observability
- Data validation and sanitization
- Idempotent operations (safe to re-run)
- Performance optimization with batching and caching

Usage:
  # Dry-run (recommended first - no changes committed)
  python3 scripts/import_zoho_contacts.py \\
    --file "kajabi 3 files review/Zoho_Contacts_2025_11_08.csv" \\
    --dry-run

  # Execute import with full commit
  python3 scripts/import_zoho_contacts.py \\
    --file "kajabi 3 files review/Zoho_Contacts_2025_11_08.csv" \\
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
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Set
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
from validation import validate_email, sanitize_string, validate_phone

# ============================================================================
# CONFIGURATION
# ============================================================================

config = get_config()
setup_logging(config.logging.level, config.logging.environment)
logger = get_logger(__name__)

BATCH_SIZE = 100
MAX_RETRIES = 3

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class MatchStrategy(Enum):
    """Strategy used to match Zoho contact to existing contact."""
    ZOHO_ID = "zoho_id"           # Matched by existing Zoho ID
    EMAIL_EXACT = "email_exact"    # Exact email match
    PHONE_EXACT = "phone_exact"    # Exact phone match (normalized)
    NO_MATCH = "no_match"          # No existing contact found


@dataclass
class ZohoContact:
    """Structured representation of a Zoho CRM contact."""
    # Primary identifiers
    zoho_id: str
    email: Optional[str]
    secondary_email: Optional[str]

    # Name fields
    first_name: Optional[str]
    last_name: str
    full_name: str

    # Contact information
    phone: Optional[str]

    # Mailing address
    mailing_street: Optional[str]
    mailing_city: Optional[str]
    mailing_state: Optional[str]
    mailing_zip: Optional[str]
    mailing_country: Optional[str]

    # Metadata
    created_time: Optional[datetime]
    modified_time: Optional[datetime]
    description: Optional[str]

    # Account information
    account_name: Optional[str]

    # Owner information
    contact_owner: Optional[str]

    # Raw row for debugging
    raw_data: Dict


@dataclass
class ImportResult:
    """Result of importing a single Zoho contact."""
    success: bool
    contact_id: Optional[str]
    zoho_id: str
    match_strategy: MatchStrategy
    created_new: bool
    enriched_fields: List[str]
    error_message: Optional[str] = None


# ============================================================================
# DATA PARSING AND VALIDATION
# ============================================================================

def parse_zoho_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse Zoho datetime format: YYYY-MM-DD HH:MM:SS

    Args:
        datetime_str: Datetime string from Zoho export

    Returns:
        Parsed datetime or None if invalid
    """
    if not datetime_str or not datetime_str.strip():
        return None

    try:
        return datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse datetime: {datetime_str}", extra={'error': str(e)})
        return None


def normalize_email(email: str) -> Optional[str]:
    """
    Normalize email for matching.

    Args:
        email: Raw email address

    Returns:
        Normalized email or None if invalid
    """
    if not email:
        return None
    # Strip whitespace and common trailing punctuation errors
    email = email.strip().lower().rstrip('.,;')
    return email if validate_email(email) else None


def normalize_phone(phone: str) -> Optional[str]:
    """
    Normalize phone number for matching (digits only).

    Args:
        phone: Raw phone number

    Returns:
        Normalized phone (digits only) or None if invalid
    """
    if not phone:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Must be at least 10 digits
    return digits if len(digits) >= 10 else None


def parse_zoho_contact(row: Dict) -> Optional[ZohoContact]:
    """
    Parse a Zoho CSV row into a structured ZohoContact.

    Args:
        row: Dictionary from CSV DictReader

    Returns:
        ZohoContact instance or None if critical fields missing

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Required fields
        zoho_id = row.get('Record Id', '').strip()
        if not zoho_id:
            raise ValueError("Missing required field: Record Id")

        # Zoho IDs must start with zcrm_
        if not zoho_id.startswith('zcrm_'):
            raise ValueError(f"Invalid Zoho ID format: {zoho_id}")

        last_name = sanitize_string(row.get('Last Name', ''), 100)
        if not last_name:
            raise ValueError("Missing required field: Last Name")

        # Parse name fields
        first_name = sanitize_string(row.get('First Name', ''), 100) or None
        full_name = sanitize_string(row.get('Contact Name', ''), 200)
        if not full_name:
            # Construct from first/last if not provided
            full_name = f"{first_name} {last_name}".strip() if first_name else last_name

        # Parse contact information
        email = normalize_email(row.get('Email', ''))
        secondary_email = normalize_email(row.get('Secondary Email', ''))
        phone = row.get('Phone', '').strip() or None

        # Parse address
        mailing_street = sanitize_string(row.get('Mailing Street', ''), 200) or None
        mailing_city = sanitize_string(row.get('Mailing City', ''), 100) or None
        mailing_state = sanitize_string(row.get('Mailing State', ''), 100) or None
        mailing_zip = row.get('Mailing Zip', '').strip() or None
        mailing_country = sanitize_string(row.get('Mailing Country', ''), 100) or None

        # Parse timestamps
        created_time = parse_zoho_datetime(row.get('Created Time', ''))
        modified_time = parse_zoho_datetime(row.get('Modified Time', ''))

        # Parse metadata
        description = sanitize_string(row.get('Description', ''), 2000) or None
        account_name = sanitize_string(row.get('Account Name', ''), 200) or None
        contact_owner = sanitize_string(row.get('Contact Owner', ''), 200) or None

        return ZohoContact(
            zoho_id=zoho_id,
            email=email,
            secondary_email=secondary_email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            phone=phone,
            mailing_street=mailing_street,
            mailing_city=mailing_city,
            mailing_state=mailing_state,
            mailing_zip=mailing_zip,
            mailing_country=mailing_country,
            created_time=created_time,
            modified_time=modified_time,
            description=description,
            account_name=account_name,
            contact_owner=contact_owner,
            raw_data=row
        )

    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse Zoho contact: {e}", extra={'row': row})
        return None


# ============================================================================
# CONTACT MATCHING
# ============================================================================

def find_contact_by_zoho_id(cursor, zoho_id: str) -> Optional[Dict]:
    """
    Find contact by Zoho ID (fastest, most reliable match).

    Args:
        cursor: Database cursor
        zoho_id: Zoho CRM Record ID

    Returns:
        Contact record or None
    """
    cursor.execute("""
        SELECT id, email, first_name, last_name, phone, zoho_id,
               zoho_email, zoho_phone,
               address_line_1, city, state, postal_code, country
        FROM contacts
        WHERE zoho_id = %s
        LIMIT 1
    """, (zoho_id,))

    return cursor.fetchone()


def find_contact_by_email(cursor, email: str, cache: Dict = None) -> Optional[Dict]:
    """
    Find contact by email (with optional caching for performance).

    Args:
        cursor: Database cursor
        email: Normalized email address
        cache: Optional email -> contact cache

    Returns:
        Contact record or None
    """
    if not email:
        return None

    # Check cache first
    if cache is not None and email in cache:
        return cache[email]

    cursor.execute("""
        SELECT id, email, first_name, last_name, phone, zoho_id,
               zoho_email, zoho_phone,
               address_line_1, city, state, postal_code, country
        FROM contacts
        WHERE email = %s OR zoho_email = %s
        LIMIT 1
    """, (email, email))

    result = cursor.fetchone()

    # Cache the result
    if cache is not None and result:
        cache[email] = result

    return result


def find_contact_by_phone(cursor, phone: str) -> Optional[Dict]:
    """
    Find contact by phone number (normalized to digits only).

    Args:
        cursor: Database cursor
        phone: Phone number (will be normalized)

    Returns:
        Contact record or None
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return None

    cursor.execute("""
        SELECT id, email, first_name, last_name, phone, zoho_id,
               zoho_email, zoho_phone,
               address_line_1, city, state, postal_code, country
        FROM contacts
        WHERE regexp_replace(phone, '[^0-9]', '', 'g') = %s
           OR regexp_replace(zoho_phone, '[^0-9]', '', 'g') = %s
        LIMIT 1
    """, (normalized_phone, normalized_phone))

    return cursor.fetchone()


def find_existing_contact(cursor, zoho_contact: ZohoContact,
                         email_cache: Dict = None) -> Tuple[Optional[Dict], MatchStrategy]:
    """
    Find existing contact using multiple strategies with priority order.

    Priority:
    1. Zoho ID (if contact already linked)
    2. Email address (most reliable)
    3. Phone number (fallback)

    Args:
        cursor: Database cursor
        zoho_contact: Parsed Zoho contact
        email_cache: Optional email cache for performance

    Returns:
        Tuple of (contact_record, match_strategy)
    """
    # Strategy 1: Zoho ID (existing link)
    contact = find_contact_by_zoho_id(cursor, zoho_contact.zoho_id)
    if contact:
        return contact, MatchStrategy.ZOHO_ID

    # Strategy 2: Email match (try both primary and secondary)
    if zoho_contact.email:
        contact = find_contact_by_email(cursor, zoho_contact.email, email_cache)
        if contact:
            return contact, MatchStrategy.EMAIL_EXACT

    if zoho_contact.secondary_email:
        contact = find_contact_by_email(cursor, zoho_contact.secondary_email, email_cache)
        if contact:
            return contact, MatchStrategy.EMAIL_EXACT

    # Strategy 3: Phone match (fallback)
    if zoho_contact.phone:
        contact = find_contact_by_phone(cursor, zoho_contact.phone)
        if contact:
            return contact, MatchStrategy.PHONE_EXACT

    return None, MatchStrategy.NO_MATCH


# ============================================================================
# CONTACT ENRICHMENT
# ============================================================================

def enrich_contact(cursor, contact_id: str, zoho_contact: ZohoContact,
                  source: str = 'zoho_crm') -> List[str]:
    """
    Enrich existing contact with Zoho CRM data.

    Only updates fields that are empty or improves data quality.
    Never overwrites existing data with empty values.

    Args:
        cursor: Database cursor
        contact_id: UUID of contact to enrich
        zoho_contact: Parsed Zoho contact data
        source: Source identifier for provenance tracking

    Returns:
        List of field names that were updated
    """
    updates = {}

    # Get current contact data
    cursor.execute("""
        SELECT zoho_id, zoho_email, zoho_phone,
               address_line_1, city, state, postal_code, country,
               first_name, last_name, phone, email
        FROM contacts
        WHERE id = %s
    """, (contact_id,))

    contact = cursor.fetchone()
    if not contact:
        logger.error(f"Contact {contact_id} not found for enrichment")
        return []

    # Always set/update Zoho ID for linking
    if not contact.get('zoho_id') or contact.get('zoho_id') != zoho_contact.zoho_id:
        updates['zoho_id'] = zoho_contact.zoho_id

    # Add Zoho email if different from primary and not already set
    if zoho_contact.email:
        normalized_zoho_email = normalize_email(zoho_contact.email)
        normalized_primary_email = normalize_email(contact.get('email'))
        normalized_existing_zoho = normalize_email(contact.get('zoho_email'))

        if (normalized_zoho_email and
            normalized_zoho_email != normalized_primary_email and
            normalized_zoho_email != normalized_existing_zoho):
            updates['zoho_email'] = zoho_contact.email

    # Add Zoho phone if not already set and different from primary
    if zoho_contact.phone:
        normalized_zoho_phone = normalize_phone(zoho_contact.phone)
        normalized_primary_phone = normalize_phone(contact.get('phone'))
        normalized_existing_zoho = normalize_phone(contact.get('zoho_phone'))

        if (normalized_zoho_phone and
            normalized_zoho_phone != normalized_primary_phone and
            normalized_existing_zoho != normalized_zoho_phone):
            updates['zoho_phone'] = zoho_contact.phone
            updates['zoho_phone_source'] = source

    # Update primary address if empty (Zoho uses "Mailing" which is typically the primary address)
    if not contact.get('address_line_1') and zoho_contact.mailing_street:
        updates['address_line_1'] = zoho_contact.mailing_street
        updates['city'] = zoho_contact.mailing_city
        updates['state'] = zoho_contact.mailing_state
        updates['postal_code'] = zoho_contact.mailing_zip
        updates['country'] = zoho_contact.mailing_country or 'US'

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

        logger.debug(f"Enriched contact {contact_id} with fields: {list(updates.keys())}")

    return list(updates.keys())


# ============================================================================
# CONTACT CREATION
# ============================================================================

def create_contact_from_zoho(cursor, zoho_contact: ZohoContact) -> Optional[str]:
    """
    Create new contact from Zoho data.

    Requires at minimum: email or phone number

    Args:
        cursor: Database cursor
        zoho_contact: Parsed Zoho contact data

    Returns:
        New contact ID or None if creation failed
    """
    # Require at least email or phone
    if not zoho_contact.email and not zoho_contact.phone:
        logger.warning(
            f"Cannot create contact without email or phone: {zoho_contact.zoho_id}",
            extra={'zoho_contact': zoho_contact.full_name}
        )
        return None

    try:
        cursor.execute("""
            INSERT INTO contacts (
                zoho_id, email, zoho_email, first_name, last_name,
                phone, zoho_phone, source_system,
                address_line_1, city, state, postal_code, country
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
        """, (
            zoho_contact.zoho_id,
            zoho_contact.email,
            zoho_contact.email,
            zoho_contact.first_name,
            zoho_contact.last_name,
            zoho_contact.phone,
            zoho_contact.phone,
            'zoho',
            zoho_contact.mailing_street,
            zoho_contact.mailing_city,
            zoho_contact.mailing_state,
            zoho_contact.mailing_zip,
            zoho_contact.mailing_country or 'US'
        ))

        contact_id = cursor.fetchone()['id']
        logger.info(
            f"Created new contact from Zoho: {contact_id}",
            extra={
                'zoho_id': zoho_contact.zoho_id,
                'email': zoho_contact.email,
                'name': zoho_contact.full_name
            }
        )
        return contact_id

    except pg_errors.UniqueViolation as e:
        logger.warning(f"Duplicate contact detected: {zoho_contact.email}", extra={'error': str(e)})
        return None
    except Exception as e:
        logger.error(f"Failed to create contact: {e}", extra={'zoho_contact': zoho_contact.zoho_id})
        raise


# ============================================================================
# IMPORT ORCHESTRATION
# ============================================================================

def import_zoho_contact(cursor, zoho_contact: ZohoContact,
                       email_cache: Dict = None,
                       stats: Dict = None) -> ImportResult:
    """
    Import a single Zoho contact (idempotent).

    Args:
        cursor: Database cursor
        zoho_contact: Parsed Zoho contact
        email_cache: Optional email cache for performance
        stats: Optional stats dict for tracking

    Returns:
        ImportResult with details of the operation
    """
    try:
        # Find existing contact
        contact, match_strategy = find_existing_contact(cursor, zoho_contact, email_cache)

        contact_id = None
        created_new = False
        enriched_fields = []

        if contact:
            # Update existing contact
            contact_id = contact['id']
            enriched_fields = enrich_contact(cursor, contact_id, zoho_contact)

            if stats and match_strategy == MatchStrategy.EMAIL_EXACT and email_cache:
                stats['email_cache_hits'] = stats.get('email_cache_hits', 0) + 1

        else:
            # Create new contact
            contact_id = create_contact_from_zoho(cursor, zoho_contact)
            if contact_id:
                created_new = True
                # All fields are "enriched" on creation
                enriched_fields = ['zoho_id', 'email', 'first_name', 'last_name', 'phone']

        success = contact_id is not None

        return ImportResult(
            success=success,
            contact_id=contact_id,
            zoho_id=zoho_contact.zoho_id,
            match_strategy=match_strategy,
            created_new=created_new,
            enriched_fields=enriched_fields
        )

    except Exception as e:
        logger.error(
            f"Error importing Zoho contact {zoho_contact.zoho_id}: {e}",
            extra={'zoho_id': zoho_contact.zoho_id}
        )
        return ImportResult(
            success=False,
            contact_id=None,
            zoho_id=zoho_contact.zoho_id,
            match_strategy=MatchStrategy.NO_MATCH,
            created_new=False,
            enriched_fields=[],
            error_message=str(e)
        )


# ============================================================================
# MAIN IMPORT PROCESS
# ============================================================================

def import_zoho_contacts(file_path: str, dry_run: bool = True) -> Dict:
    """
    Import Zoho CRM contacts with enrichment.

    Args:
        file_path: Path to Zoho CSV export
        dry_run: If True, rolls back all changes

    Returns:
        Statistics dictionary with import results
    """
    stats = {
        'total_rows': 0,
        'contacts_processed': 0,
        'contacts_created': 0,
        'contacts_updated': 0,
        'contacts_enriched': 0,
        'contacts_skipped': 0,
        'parse_errors': 0,
        'import_errors': 0,
        'email_cache_hits': 0,
        'match_strategies': {
            'zoho_id': 0,
            'email_exact': 0,
            'phone_exact': 0,
            'no_match': 0
        }
    }

    conn = None
    email_cache = {}  # email -> contact record (for performance)

    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.set_session(autocommit=False)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info(f"Starting Zoho contact import from {file_path} (dry_run={dry_run})")

            # Read and import contacts
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    stats['total_rows'] += 1

                    # Parse Zoho contact
                    zoho_contact = parse_zoho_contact(row)
                    if not zoho_contact:
                        stats['parse_errors'] += 1
                        continue

                    # Import contact
                    try:
                        result = import_zoho_contact(cursor, zoho_contact, email_cache, stats)

                        if result.success:
                            stats['contacts_processed'] += 1
                            if result.created_new:
                                stats['contacts_created'] += 1
                            else:
                                stats['contacts_updated'] += 1
                                if result.enriched_fields:
                                    stats['contacts_enriched'] += 1

                            # Track match strategy
                            stats['match_strategies'][result.match_strategy.value] += 1
                        else:
                            stats['contacts_skipped'] += 1
                            if result.error_message:
                                stats['import_errors'] += 1

                        # Commit in batches for better performance
                        if stats['total_rows'] % BATCH_SIZE == 0:
                            if dry_run:
                                conn.rollback()
                            else:
                                conn.commit()

                            logger.info(
                                f"Processed {stats['total_rows']} rows - "
                                f"created: {stats['contacts_created']}, "
                                f"updated: {stats['contacts_updated']}, "
                                f"enriched: {stats['contacts_enriched']}, "
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
        description='Import Zoho CRM contacts and enrich existing database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run to preview changes
  python3 scripts/import_zoho_contacts.py --file zoho_export.csv --dry-run

  # Execute import with full commit
  python3 scripts/import_zoho_contacts.py --file zoho_export.csv --execute
        """
    )

    parser.add_argument(
        '--file',
        required=True,
        help='Path to Zoho CRM contacts CSV export'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without committing changes (recommended first)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the import and commit changes to database'
    )

    args = parser.parse_args()

    # Validation
    if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)

    if args.dry_run and args.execute:
        print("ERROR: Cannot specify both --dry-run and --execute")
        sys.exit(1)

    if not os.path.exists(args.file):
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    dry_run = args.dry_run

    # Print banner
    print("\n" + "="*80)
    print("ZOHO CRM CONTACT IMPORT AND ENRICHMENT")
    print("="*80)
    print(f"File: {args.file}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'EXECUTE (will commit changes)'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    try:
        stats = import_zoho_contacts(args.file, dry_run=dry_run)

        # Print results
        print("\n" + "="*80)
        print("IMPORT COMPLETE")
        print("="*80)
        print(f"Total rows processed: {stats['total_rows']:,}")
        print(f"Contacts created: {stats['contacts_created']:,}")
        print(f"Contacts updated: {stats['contacts_updated']:,}")
        print(f"Contacts enriched: {stats['contacts_enriched']:,}")
        print(f"Contacts skipped: {stats['contacts_skipped']:,}")
        print(f"Parse errors: {stats['parse_errors']:,}")
        print(f"Import errors: {stats['import_errors']:,}")
        print(f"\nMatch Strategies:")
        for strategy, count in stats['match_strategies'].items():
            if count > 0:
                print(f"  {strategy}: {count:,}")
        print(f"\nEmail cache hits: {stats.get('email_cache_hits', 0):,}")
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
