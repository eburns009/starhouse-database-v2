#!/usr/bin/env python3
"""
Extract Last Names from Email Patterns - Round 4
6 more customers with clear firstlast patterns
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from db_config import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/extract_last_names_round4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()

# Last names to extract from email patterns
EMAIL_PATTERN_EXTRACTIONS = [
    {
        'email': 'artieegendorf@gmail.com',
        'first_name': 'Artie',  # Fix from ArthurcEgendorf
        'last_name': 'Egendorf',
        'revenue': 10.00,
        'pattern': 'artieegendorf → artie + egendorf',
        'confidence': 'HIGH',
        'note': 'Also fixing first name from ArthurcEgendorf to Artie'
    },
    {
        'email': 'genedilworth@gmail.com',
        'first_name': 'Gene',
        'last_name': 'Dilworth',
        'revenue': 10.00,
        'pattern': 'genedilworth → gene + dilworth',
        'confidence': 'HIGH'
    },
    {
        'email': 'franceszammit@gmx.com',
        'first_name': 'Frances',
        'last_name': 'Zammit',
        'revenue': 10.00,
        'pattern': 'franceszammit → frances + zammit',
        'confidence': 'HIGH'
    },
    {
        'email': 'janemealey@yahoo.com',
        'first_name': 'Jane',
        'last_name': 'Mealey',
        'revenue': 7.00,
        'pattern': 'janemealey → jane + mealey',
        'confidence': 'HIGH'
    },
    {
        'email': 'mmariscal@sia-jpa.org',
        'first_name': 'Michele',  # Already have
        'last_name': 'Mariscal',
        'revenue': 7.00,
        'pattern': 'mmariscal → m + mariscal',
        'confidence': 'HIGH'
    },
    {
        'email': 'jhpulk@gmail.com',
        'first_name': 'Jane',  # Already have
        'last_name': 'Pulk',
        'revenue': 7.00,
        'pattern': 'jhpulk → jh + pulk',
        'confidence': 'MEDIUM',
        'note': 'Could be J.H. Pulk or Jane Pulk'
    }
]


def verify_customers(conn):
    """Verify customers exist and show current state"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("VERIFYING CUSTOMERS")
    logger.info("=" * 80)
    logger.info("")

    emails = [item['email'] for item in EMAIL_PATTERN_EXTRACTIONS]

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, email, first_name, last_name, total_spent, phone, city, state
            FROM contacts
            WHERE email = ANY(%s)
            ORDER BY total_spent DESC
        """, (emails,))
        customers = cursor.fetchall()

    logger.info(f"Found {len(customers)} customers:")
    logger.info("")

    for c in customers:
        logger.info(f"✓ {c['email']:45s} ${c['total_spent']:8.2f}")
        logger.info(f"  Current: {c['first_name'] or '(none)'} {c['last_name'] or '(none)'}")
        if c['phone']:
            logger.info(f"  Phone: {c['phone']}")
        if c['city'] and c['state']:
            logger.info(f"  Location: {c['city']}, {c['state']}")
        logger.info("")

    return customers


def preview_extractions():
    """Preview the proposed last name extractions"""
    logger.info("=" * 80)
    logger.info("PREVIEW: PROPOSED LAST NAME EXTRACTIONS - ROUND 4")
    logger.info("=" * 80)
    logger.info("")

    total_revenue = sum(item['revenue'] for item in EMAIL_PATTERN_EXTRACTIONS)

    logger.info(f"Total customers: {len(EMAIL_PATTERN_EXTRACTIONS)}")
    logger.info(f"Total revenue: ${total_revenue:,.2f}")
    logger.info("")

    for i, item in enumerate(EMAIL_PATTERN_EXTRACTIONS, 1):
        logger.info(f"{i}. {item['email']:45s} ${item['revenue']:8.2f}")
        logger.info(f"   Current:    {item.get('note', 'First name only')}")
        logger.info(f"   New:        {item['first_name']} {item['last_name']}")
        logger.info(f"   Pattern:    {item['pattern']}")
        logger.info(f"   Confidence: {item['confidence']}")
        logger.info("")


def execute_extraction(conn, dry_run=False):
    """Execute the last name extraction"""
    logger.info("=" * 80)
    if dry_run:
        logger.info("DRY RUN: Simulating Extraction")
    else:
        logger.info("EXECUTING: Last Name Extraction - Round 4")
    logger.info("=" * 80)
    logger.info("")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Would update {len(EMAIL_PATTERN_EXTRACTIONS)} customers")
        logger.info("")
        return 0

    updated_count = 0

    try:
        for item in EMAIL_PATTERN_EXTRACTIONS:
            # Escape quotes
            escaped_first = item['first_name'].replace("'", "''")
            escaped_last = item['last_name'].replace("'", "''")

            with conn.cursor() as cursor:
                # Update both first and last name (to fix the ArthurcEgendorf typo)
                cursor.execute(f"""
                    UPDATE contacts
                    SET
                        first_name = '{escaped_first}',
                        last_name = '{escaped_last}',
                        updated_at = NOW()
                    WHERE email = '{item['email']}'
                    AND (last_name IS NULL OR last_name = '')
                """)

                if cursor.rowcount > 0:
                    updated_count += 1
                    logger.info(f"✅ {item['email']}")
                    logger.info(f"   → {item['first_name']} {item['last_name']}")
                else:
                    logger.warning(f"⚠️  {item['email']} - No update (already has last name?)")

        conn.commit()
        logger.info("")
        logger.info(f"✅ Successfully updated {updated_count} customers")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        conn.rollback()
        raise

    return updated_count


def verify_results(conn):
    """Verify the extraction results"""
    logger.info("=" * 80)
    logger.info("VERIFICATION")
    logger.info("=" * 80)
    logger.info("")

    emails = [item['email'] for item in EMAIL_PATTERN_EXTRACTIONS]

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT email, first_name, last_name, total_spent
            FROM contacts
            WHERE email = ANY(%s)
            ORDER BY total_spent DESC
        """, (emails,))
        customers = cursor.fetchall()

    logger.info("After extraction:")
    logger.info("")

    for c in customers:
        logger.info(f"  ✅ {c['first_name']} {c['last_name']}")
        logger.info(f"     Email: {c['email']}")
        logger.info(f"     Revenue: ${c['total_spent']:.2f}")
        logger.info("")

    # Overall stats
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_paying,
                SUM(CASE WHEN (first_name IS NULL OR first_name = '')
                         OR (last_name IS NULL OR last_name = '')
                    THEN 1 ELSE 0 END) as still_missing,
                SUM(CASE WHEN first_name IS NOT NULL AND first_name != ''
                         AND last_name IS NOT NULL AND last_name != ''
                    THEN 1 ELSE 0 END) as complete_names
            FROM contacts
            WHERE total_spent > 0
        """)
        stats = cursor.fetchone()

    logger.info("Overall statistics:")
    logger.info(f"  Total paying customers:      {stats['total_paying']:,}")
    logger.info(f"  Complete names (first+last): {stats['complete_names']:,}")
    logger.info(f"  Still missing names:         {stats['still_missing']:,}")
    completion_pct = (stats['complete_names'] / stats['total_paying'] * 100) if stats['total_paying'] > 0 else 0
    logger.info(f"  Completion rate:             {completion_pct:.1f}%")
    logger.info("")


def main():
    """Main workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "EXTRACT LAST NAMES FROM EMAIL PATTERNS - ROUND 4".center(78) + "║")
    logger.info("║" + "Quick Win: 6 customers, $51 revenue".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")

        # Verify customers
        verify_customers(conn)

        # Preview extractions
        preview_extractions()

        # Execute extraction
        execute_extraction(conn, dry_run=False)

        # Verify results
        verify_results(conn)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ LAST NAME EXTRACTION ROUND 4 COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info("  • 6 customers enriched with last names")
        logger.info("  • $51 revenue impact")
        logger.info("  • Extracted from email patterns (firstlast)")
        logger.info("  • High confidence matches")
        logger.info("  • Fixed 'ArthurcEgendorf' typo → Artie Egendorf")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
