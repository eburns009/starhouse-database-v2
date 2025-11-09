#!/usr/bin/env python3
"""
FUZZY CONTACT ENRICHMENT FROM PAYPAL DATA
==========================================

Enriches existing contacts by finding additional contact information from PayPal
transactions using fuzzy matching. Focuses on:

1. SAME EMAIL, DIFFERENT NAME - Captures name variations for same email
2. Similar names with different emails
3. Phone number variations
4. Address information

This is a separate enrichment pass after the main import.

Usage:
  # Dry-run (recommended first)
  python3 scripts/fuzzy_enrich_contacts_paypal.py --dry-run

  # Execute enrichment
  python3 scripts/fuzzy_enrich_contacts_paypal.py --execute
"""

import os
import sys
import argparse
from typing import Dict, List, Optional, Tuple, Set
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

from config import get_config
from logging_config import setup_logging, get_logger

# ============================================================================
# CONFIGURATION
# ============================================================================

config = get_config()
setup_logging(config.logging.level, config.logging.environment)
logger = get_logger(__name__)

# ============================================================================
# FUZZY MATCHING UTILITIES
# ============================================================================

def normalize_email(email: str) -> Optional[str]:
    """Normalize email for matching."""
    if not email:
        return None
    return email.strip().lower()

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number (digits only)."""
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    return digits if len(digits) >= 10 else None

def normalize_name(name: str) -> Optional[str]:
    """Normalize name for comparison."""
    if not name:
        return None
    # Convert to lowercase, remove extra spaces
    name = ' '.join(name.lower().split())
    return name if name else None

def names_are_different(name1: str, name2: str) -> bool:
    """
    Check if two names are different enough to warrant saving as additional_name.

    Returns True if names are different variations of same person.
    """
    if not name1 or not name2:
        return False

    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    # Exact match - not different
    if n1 == n2:
        return False

    # One is substring of other (e.g., "John" vs "John Smith") - different enough
    if n1 in n2 or n2 in n1:
        return True

    # Check if last name matches (common for "Smith, John" vs "John Smith")
    parts1 = n1.split()
    parts2 = n2.split()

    if parts1 and parts2:
        # If last names match, consider them different variations
        if parts1[-1] == parts2[-1]:
            return True

    return True

# ============================================================================
# ENRICHMENT LOGIC
# ============================================================================

def find_email_name_variations(cursor) -> List[Dict]:
    """
    Find contacts where PayPal transactions have same email but different name.

    This is the PRIMARY use case - capturing name variations.
    """
    logger.info("Finding email/name variations in PayPal data...")

    cursor.execute("""
        WITH paypal_names AS (
            SELECT DISTINCT
                t.contact_id,
                c.email,
                c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name,
                c.additional_name,
                t.raw_source->>'original_type' as txn_type,
                -- Extract name from shipping address in raw_source
                CASE
                    WHEN t.raw_source ? 'full_name' THEN t.raw_source->>'full_name'
                    ELSE NULL
                END as paypal_name
            FROM transactions t
            JOIN contacts c ON t.contact_id = c.id
            WHERE t.source_system = 'paypal'
              AND t.raw_source IS NOT NULL
              AND t.raw_source->>'full_name' IS NOT NULL
              AND t.raw_source->>'full_name' != ''
        )
        SELECT
            contact_id,
            email,
            contact_name,
            paypal_name,
            additional_name,
            COUNT(*) as occurrence_count
        FROM paypal_names
        WHERE LOWER(TRIM(contact_name)) != LOWER(TRIM(paypal_name))
        GROUP BY contact_id, email, contact_name, paypal_name, additional_name
        ORDER BY occurrence_count DESC, contact_id
    """)

    results = cursor.fetchall()
    logger.info(f"Found {len(results)} email/name variations to review")

    return results

def find_similar_names_different_emails(cursor) -> List[Dict]:
    """
    Find contacts with similar names but different emails.
    Uses PostgreSQL similarity() function.
    """
    logger.info("Finding similar names with different emails...")

    cursor.execute("""
        WITH paypal_contacts AS (
            SELECT DISTINCT
                c.id as contact_id,
                c.email,
                c.first_name || ' ' || COALESCE(c.last_name, '') as contact_name,
                t.raw_source->>'from_email' as paypal_email,
                t.raw_source->>'full_name' as paypal_name,
                c.additional_email,
                c.additional_name
            FROM transactions t
            JOIN contacts c ON t.contact_id = c.id
            WHERE t.source_system = 'paypal'
              AND t.raw_source IS NOT NULL
              AND t.raw_source->>'from_email' IS NOT NULL
              AND t.raw_source->>'full_name' IS NOT NULL
        )
        SELECT
            pc.contact_id,
            pc.email,
            pc.contact_name,
            pc.paypal_email,
            pc.paypal_name,
            pc.additional_email,
            pc.additional_name,
            similarity(pc.contact_name, pc.paypal_name) as name_similarity
        FROM paypal_contacts pc
        WHERE LOWER(TRIM(pc.email)) != LOWER(TRIM(pc.paypal_email))
          AND similarity(pc.contact_name, pc.paypal_name) > 0.6
          AND (pc.additional_email IS NULL OR LOWER(pc.additional_email) != LOWER(pc.paypal_email))
        ORDER BY name_similarity DESC, pc.contact_id
        LIMIT 500
    """)

    results = cursor.fetchall()
    logger.info(f"Found {len(results)} similar names with different emails")

    return results

def enrich_contact_from_variations(cursor, contact_id: str, paypal_name: str,
                                   paypal_email: str = None, dry_run: bool = True) -> Dict:
    """
    Enrich a single contact with name/email variations.

    Returns dict of fields that were updated.
    """
    updates = {}

    # Get current contact data
    cursor.execute("""
        SELECT
            email, first_name, last_name,
            additional_name, additional_name_source,
            additional_email, additional_email_source,
            paypal_email
        FROM contacts
        WHERE id = %s
    """, (contact_id,))

    contact = cursor.fetchone()
    if not contact:
        return updates

    current_name = f"{contact['first_name'] or ''} {contact['last_name'] or ''}".strip()

    # Check if PayPal name is different and worth saving
    if paypal_name and names_are_different(current_name, paypal_name):
        # Don't overwrite if additional_name already has this value
        existing_additional = normalize_name(contact.get('additional_name'))
        new_additional = normalize_name(paypal_name)

        if not contact.get('additional_name') or existing_additional != new_additional:
            updates['additional_name'] = paypal_name
            updates['additional_name_source'] = 'paypal_fuzzy_match'

    # Check if PayPal email is different and worth saving
    if paypal_email:
        normalized_paypal_email = normalize_email(paypal_email)
        existing_emails = {
            normalize_email(contact.get('email')),
            normalize_email(contact.get('paypal_email')),
            normalize_email(contact.get('additional_email'))
        }
        existing_emails.discard(None)

        if normalized_paypal_email and normalized_paypal_email not in existing_emails:
            if not contact.get('additional_email'):
                updates['additional_email'] = paypal_email
                updates['additional_email_source'] = 'paypal_fuzzy_match'

    # Execute update if we have changes
    if updates and not dry_run:
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
# MAIN ENRICHMENT PROCESS
# ============================================================================

def fuzzy_enrich_contacts(dry_run: bool = True) -> Dict:
    """
    Run fuzzy enrichment on contacts from PayPal data.

    Returns statistics dict.
    """
    stats = {
        'email_name_variations_found': 0,
        'email_name_variations_enriched': 0,
        'similar_names_found': 0,
        'similar_names_enriched': 0,
        'total_enriched': 0,
        'names_added': 0,
        'emails_added': 0
    }

    conn = None

    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.set_session(autocommit=False)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info(f"Starting fuzzy contact enrichment (dry_run={dry_run})")

            # Phase 1: Same email, different name (PRIMARY USE CASE)
            logger.info("=" * 80)
            logger.info("PHASE 1: Same Email, Different Name Variations")
            logger.info("=" * 80)

            email_variations = find_email_name_variations(cursor)
            stats['email_name_variations_found'] = len(email_variations)

            enriched_contacts = set()

            for variation in email_variations:
                contact_id = variation['contact_id']

                # Skip if already enriched in this run
                if contact_id in enriched_contacts:
                    continue

                updates = enrich_contact_from_variations(
                    cursor,
                    contact_id,
                    variation['paypal_name'],
                    dry_run=dry_run
                )

                if updates:
                    stats['email_name_variations_enriched'] += 1
                    enriched_contacts.add(contact_id)

                    if 'additional_name' in updates:
                        stats['names_added'] += 1
                        logger.info(f"Contact {contact_id}: '{variation['contact_name']}' → additional_name: '{variation['paypal_name']}'")

            # Phase 2: Similar names, different emails
            logger.info("=" * 80)
            logger.info("PHASE 2: Similar Names with Different Emails")
            logger.info("=" * 80)

            similar_names = find_similar_names_different_emails(cursor)
            stats['similar_names_found'] = len(similar_names)

            for match in similar_names:
                contact_id = match['contact_id']

                # Skip if already enriched in this run
                if contact_id in enriched_contacts:
                    continue

                updates = enrich_contact_from_variations(
                    cursor,
                    contact_id,
                    match['paypal_name'],
                    match['paypal_email'],
                    dry_run=dry_run
                )

                if updates:
                    stats['similar_names_enriched'] += 1
                    enriched_contacts.add(contact_id)

                    if 'additional_name' in updates:
                        stats['names_added'] += 1
                    if 'additional_email' in updates:
                        stats['emails_added'] += 1

                    logger.info(f"Contact {contact_id} (similarity: {match['name_similarity']:.2f}): {list(updates.keys())}")

            stats['total_enriched'] = len(enriched_contacts)

            # Commit or rollback
            if dry_run:
                conn.rollback()
                logger.info("DRY RUN: All enrichments rolled back")
            else:
                conn.commit()
                logger.info("Enrichments committed")

        logger.info("Fuzzy enrichment complete!")
        logger.info(f"Statistics: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Fatal error during fuzzy enrichment: {e}")
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
    parser = argparse.ArgumentParser(description='Fuzzy enrich contacts from PayPal data')
    parser.add_argument('--dry-run', action='store_true', help='Run without committing changes')
    parser.add_argument('--execute', action='store_true', help='Execute the enrichment (commits changes)')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: Must specify either --dry-run or --execute")
        sys.exit(1)

    dry_run = args.dry_run

    print("\n" + "="*80)
    print("FUZZY CONTACT ENRICHMENT FROM PAYPAL DATA")
    print("="*80)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'EXECUTE (will commit changes)'}")
    print("="*80 + "\n")

    try:
        stats = fuzzy_enrich_contacts(dry_run=dry_run)

        print("\n" + "="*80)
        print("ENRICHMENT COMPLETE")
        print("="*80)
        print(f"Email/Name variations found: {stats['email_name_variations_found']}")
        print(f"Email/Name variations enriched: {stats['email_name_variations_enriched']}")
        print(f"Similar names found: {stats['similar_names_found']}")
        print(f"Similar names enriched: {stats['similar_names_enriched']}")
        print(f"Total contacts enriched: {stats['total_enriched']}")
        print(f"  - Additional names added: {stats['names_added']}")
        print(f"  - Additional emails added: {stats['emails_added']}")
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
