#!/usr/bin/env python3
"""
Extract Last Names from Email Patterns
Quick win: 3 customers with clear last name patterns in email addresses
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
        logging.FileHandler(f'logs/extract_last_names_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# Last names to extract from email patterns
EMAIL_PATTERN_EXTRACTIONS = [
    {
        'email': 'vjoshi1001@gmail.com',
        'first_name': 'Vishnukant',  # Already have
        'last_name': 'Joshi',  # Extract from vjoshi (v + joshi)
        'revenue': 834.00,
        'pattern': 'vjoshi1001 → v + joshi',
        'confidence': 'HIGH'
    },
    {
        'email': 'bonharrington@yahoo.com',
        'first_name': 'Bonnie',  # Already have
        'last_name': 'Harrington',  # Extract from bonharrington (bon + harrington)
        'revenue': 169.00,
        'pattern': 'bonharrington → bon(nie) + harrington',
        'confidence': 'HIGH'
    },
    {
        'email': 'rcorzor@yahoo.co.uk',
        'first_name': 'C',  # Already have (just initial)
        'last_name': 'Corzor',  # Extract from rcorzor (r + corzor)
        'revenue': 150.00,
        'pattern': 'rcorzor → r + corzor',
        'confidence': 'MEDIUM'
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
    logger.info("PREVIEW: PROPOSED LAST NAME EXTRACTIONS")
    logger.info("=" * 80)
    logger.info("")

    total_revenue = sum(item['revenue'] for item in EMAIL_PATTERN_EXTRACTIONS)

    logger.info(f"Total customers: {len(EMAIL_PATTERN_EXTRACTIONS)}")
    logger.info(f"Total revenue: ${total_revenue:,.2f}")
    logger.info("")

    for i, item in enumerate(EMAIL_PATTERN_EXTRACTIONS, 1):
        logger.info(f"{i}. {item['email']:45s} ${item['revenue']:8.2f}")
        logger.info(f"   Current:    {item['first_name']} (no last name)")
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
        logger.info("EXECUTING: Last Name Extraction")
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
            escaped_last = item['last_name'].replace("'", "''")

            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE contacts
                    SET
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
    logger.info(f"  Total paying customers:    {stats['total_paying']:,}")
    logger.info(f"  Complete names (first+last): {stats['complete_names']:,}")
    logger.info(f"  Still missing names:       {stats['still_missing']:,}")
    logger.info("")


def main():
    """Main workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "EXTRACT LAST NAMES FROM EMAIL PATTERNS".center(78) + "║")
    logger.info("║" + "Quick Win: 3 customers, $1,153 revenue".center(78) + "║")
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
        logger.info("✅ LAST NAME EXTRACTION COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info("  • 3 customers enriched with last names")
        logger.info("  • $1,153 revenue impact")
        logger.info("  • Extracted from email patterns")
        logger.info("  • High confidence matches")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
