#!/usr/bin/env python3
"""
Enrich Billing Addresses from Shipping Data
Quick win: Copy complete shipping addresses to billing for contacts missing billing address

Impact: Increase mailing list from 1,462 (20.5%) to ~2,359 (33.1%)
Gain: +897 contacts (+61%)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/billing_from_shipping_enrichment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def analyze_enrichment_potential(conn):
    """Analyze how many contacts can be enriched"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING ENRICHMENT POTENTIAL")
    logger.info("=" * 80)

    query = """
        SELECT
            COUNT(*) as total_contacts,
            SUM(CASE WHEN address_line_1 IS NOT NULL AND city IS NOT NULL
                     AND state IS NOT NULL AND postal_code IS NOT NULL
                THEN 1 ELSE 0 END) as has_complete_billing,
            SUM(CASE WHEN shipping_address_line_1 IS NOT NULL AND shipping_city IS NOT NULL
                     AND shipping_state IS NOT NULL AND shipping_postal_code IS NOT NULL
                THEN 1 ELSE 0 END) as has_complete_shipping,
            SUM(CASE WHEN shipping_address_line_1 IS NOT NULL AND shipping_city IS NOT NULL
                     AND shipping_state IS NOT NULL AND shipping_postal_code IS NOT NULL
                     AND (address_line_1 IS NULL OR city IS NULL
                          OR state IS NULL OR postal_code IS NULL)
                THEN 1 ELSE 0 END) as can_enrich
        FROM contacts
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        stats = cursor.fetchone()

    total = stats['total_contacts']
    billing = stats['has_complete_billing']
    shipping = stats['has_complete_shipping']
    enrichable = stats['can_enrich']

    logger.info(f"Total contacts:              {total:6,}")
    logger.info(f"Complete billing address:    {billing:6,} ({billing/total*100:5.1f}%)")
    logger.info(f"Complete shipping address:   {shipping:6,} ({shipping/total*100:5.1f}%)")
    logger.info(f"Can enrich from shipping:    {enrichable:6,} ({enrichable/total*100:5.1f}%)")
    logger.info("")

    potential_total = billing + enrichable
    logger.info(f"After enrichment:")
    logger.info(f"  Mailing-ready contacts:    {potential_total:6,} ({potential_total/total*100:5.1f}%)")
    logger.info(f"  Increase:                  +{enrichable:,} contacts (+{enrichable/billing*100:.1f}%)")
    logger.info("")

    return stats


def preview_enrichment(conn, limit=10):
    """Preview which contacts will be enriched"""
    logger.info("=" * 80)
    logger.info("PREVIEW: Sample Contacts to Enrich")
    logger.info("=" * 80)

    query = """
        SELECT
            id,
            email,
            first_name,
            last_name,
            address_line_1 as current_billing_addr,
            city as current_billing_city,
            shipping_address_line_1 as new_addr,
            shipping_city as new_city,
            shipping_state as new_state,
            shipping_postal_code as new_zip
        FROM contacts
        WHERE shipping_address_line_1 IS NOT NULL
          AND shipping_city IS NOT NULL
          AND shipping_state IS NOT NULL
          AND shipping_postal_code IS NOT NULL
          AND (address_line_1 IS NULL OR city IS NULL
               OR state IS NULL OR postal_code IS NULL)
        ORDER BY total_spent DESC
        LIMIT %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (limit,))
        contacts = cursor.fetchall()

    logger.info(f"Showing {len(contacts)} of {limit} contacts:")
    logger.info("")

    for i, c in enumerate(contacts, 1):
        logger.info(f"{i}. {c['first_name']} {c['last_name']} <{c['email']}>")
        logger.info(f"   Current: {c['current_billing_addr'] or '(none)'}, {c['current_billing_city'] or '(none)'}")
        logger.info(f"   New:     {c['new_addr']}, {c['new_city']}, {c['new_state']} {c['new_zip']}")
        logger.info("")

    return contacts


def execute_enrichment(conn, dry_run=True):
    """Execute the enrichment"""
    logger.info("=" * 80)
    if dry_run:
        logger.info("DRY RUN: Simulating Enrichment (no changes made)")
    else:
        logger.info("EXECUTING: Enriching Billing Addresses from Shipping")
    logger.info("=" * 80)

    update_query = """
        UPDATE contacts
        SET
            address_line_1 = shipping_address_line_1,
            address_line_2 = shipping_address_line_2,
            city = shipping_city,
            state = shipping_state,
            postal_code = shipping_postal_code,
            country = COALESCE(shipping_country, country),
            updated_at = NOW()
        WHERE shipping_address_line_1 IS NOT NULL
          AND shipping_city IS NOT NULL
          AND shipping_state IS NOT NULL
          AND shipping_postal_code IS NOT NULL
          AND (address_line_1 IS NULL OR city IS NULL
               OR state IS NULL OR postal_code IS NULL)
    """

    # Count how many will be updated
    count_query = """
        SELECT COUNT(*) as count
        FROM contacts
        WHERE shipping_address_line_1 IS NOT NULL
          AND shipping_city IS NOT NULL
          AND shipping_state IS NOT NULL
          AND shipping_postal_code IS NOT NULL
          AND (address_line_1 IS NULL OR city IS NULL
               OR state IS NULL OR postal_code IS NULL)
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(count_query)
        count = cursor.fetchone()['count']

    logger.info(f"Contacts to update: {count:,}")
    logger.info("")

    if dry_run:
        logger.info("DRY RUN - No changes made")
        logger.info(f"Would update {count:,} contacts if executed")
        return count

    # Execute the update
    with conn.cursor() as cursor:
        logger.info("Executing UPDATE...")
        cursor.execute(update_query)
        updated = cursor.rowcount

    conn.commit()

    logger.info(f"✅ Successfully updated {updated:,} contacts")
    logger.info("")

    return updated


def verify_enrichment(conn):
    """Verify the enrichment results"""
    logger.info("=" * 80)
    logger.info("VERIFYING ENRICHMENT RESULTS")
    logger.info("=" * 80)

    query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN address_line_1 IS NOT NULL AND city IS NOT NULL
                     AND state IS NOT NULL AND postal_code IS NOT NULL
                THEN 1 ELSE 0 END) as complete_billing
        FROM contacts
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        stats = cursor.fetchone()

    total = stats['total']
    complete = stats['complete_billing']

    logger.info(f"Total contacts:          {total:6,}")
    logger.info(f"Complete billing addr:   {complete:6,} ({complete/total*100:5.1f}%)")
    logger.info("")

    return stats


def main():
    """Main enrichment workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "BILLING ADDRESS ENRICHMENT FROM SHIPPING DATA".center(78) + "║")
    logger.info("║" + "Quick Win: +61% Mailing List Growth".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        conn = psycopg2.connect(DATABASE_URL)

        # Step 1: Analyze potential
        stats_before = analyze_enrichment_potential(conn)

        # Step 2: Preview enrichment
        preview_enrichment(conn, limit=20)

        # Step 3: Execute (DRY RUN first)
        logger.info("")
        logger.info("=" * 80)
        logger.info("EXECUTION OPTIONS")
        logger.info("=" * 80)
        logger.info("")
        logger.info("This script is currently in DRY RUN mode.")
        logger.info("No changes will be made to the database.")
        logger.info("")
        logger.info("To execute the enrichment:")
        logger.info("  1. Review the preview above")
        logger.info("  2. Edit this script and change: execute_enrichment(conn, dry_run=False)")
        logger.info("  3. Re-run the script")
        logger.info("")

        # DRY RUN
        execute_enrichment(conn, dry_run=True)

        # Uncomment to execute:
        # execute_enrichment(conn, dry_run=False)
        # verify_enrichment(conn)

        conn.close()
        logger.info("")
        logger.info("✅ Analysis completed successfully")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
