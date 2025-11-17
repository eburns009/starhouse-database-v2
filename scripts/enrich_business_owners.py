#!/usr/bin/env python3
"""
Enrich Business Owner Names via Web Research
Top 3 revenue customers ($2,442) - verified business ownership
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
        logging.FileHandler(f'logs/enrich_business_owners_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()

# Business owner enrichments from web research
BUSINESS_OWNER_ENRICHMENTS = [
    {
        'email': 'heather@rootsofwellnessayurveda.com',
        'first_name': 'Heather',
        'last_name': 'Baines',
        'revenue': 1200.00,
        'business': 'Roots of Wellness Ayurveda',
        'location': 'Boulder, CO',
        'source': 'Web research - rootsofwellnessayurveda.com/heather',
        'confidence': 'HIGH'
    },
    {
        'email': 'juliet@depthsoffeminine.earth',
        'first_name': 'Juliet',
        'last_name': 'Haines',
        'revenue': 1000.00,
        'business': 'Depths of Feminine Wisdom School',
        'alternate_name': 'Juliet Gaia Rose',
        'source': 'Web research - depthsoffeminine.earth/about',
        'confidence': 'HIGH'
    },
    {
        'email': 'kelly@sollunahealing.org',
        'first_name': 'Kelly',
        'last_name': 'Barrett',
        'revenue': 242.00,
        'business': 'Sol Luna Healing',
        'credentials': 'LCSW, RYT, Reiki Master',
        'location': 'Northglenn, CO',
        'source': 'Web research - sollunahealing.org/about',
        'confidence': 'HIGH'
    }
]


def verify_customers(conn):
    """Verify customers exist and show current state"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("VERIFYING BUSINESS OWNER CUSTOMERS")
    logger.info("=" * 80)
    logger.info("")

    emails = [item['email'] for item in BUSINESS_OWNER_ENRICHMENTS]

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
        logger.info(f"✓ {c['email']:50s} ${c['total_spent']:8.2f}")
        logger.info(f"  Current: {c['first_name'] or '(none)'} {c['last_name'] or '(none)'}")
        if c['phone']:
            logger.info(f"  Phone: {c['phone']}")
        if c['city'] and c['state']:
            logger.info(f"  Location: {c['city']}, {c['state']}")
        logger.info("")

    return customers


def preview_enrichments():
    """Preview the proposed business owner enrichments"""
    logger.info("=" * 80)
    logger.info("PREVIEW: BUSINESS OWNER NAME ENRICHMENTS")
    logger.info("=" * 80)
    logger.info("")

    total_revenue = sum(item['revenue'] for item in BUSINESS_OWNER_ENRICHMENTS)

    logger.info(f"Total customers: {len(BUSINESS_OWNER_ENRICHMENTS)}")
    logger.info(f"Total revenue: ${total_revenue:,.2f}")
    logger.info("")

    for i, item in enumerate(BUSINESS_OWNER_ENRICHMENTS, 1):
        logger.info(f"{i}. {item['email']:50s} ${item['revenue']:8.2f}")
        logger.info(f"   Current:  {item['first_name']} (no last name)")
        logger.info(f"   New:      {item['first_name']} {item['last_name']}")
        logger.info(f"   Business: {item['business']}")
        logger.info(f"   Source:   {item['source']}")
        logger.info(f"   Confidence: {item['confidence']}")
        logger.info("")


def execute_enrichment(conn, dry_run=False):
    """Execute the business owner name enrichment"""
    logger.info("=" * 80)
    if dry_run:
        logger.info("DRY RUN: Simulating Enrichment")
    else:
        logger.info("EXECUTING: Business Owner Name Enrichment")
    logger.info("=" * 80)
    logger.info("")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Would update {len(BUSINESS_OWNER_ENRICHMENTS)} customers")
        logger.info("")
        return 0

    updated_count = 0

    try:
        for item in BUSINESS_OWNER_ENRICHMENTS:
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
                    logger.info(f"   Business: {item['business']}")
                else:
                    logger.warning(f"⚠️  {item['email']} - No update (already has last name?)")

        conn.commit()
        logger.info("")
        logger.info(f"✅ Successfully updated {updated_count} customers")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}")
        conn.rollback()
        raise

    return updated_count


def verify_results(conn):
    """Verify the enrichment results"""
    logger.info("=" * 80)
    logger.info("VERIFICATION")
    logger.info("=" * 80)
    logger.info("")

    emails = [item['email'] for item in BUSINESS_OWNER_ENRICHMENTS]

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT email, first_name, last_name, total_spent
            FROM contacts
            WHERE email = ANY(%s)
            ORDER BY total_spent DESC
        """, (emails,))
        customers = cursor.fetchall()

    logger.info("After enrichment:")
    logger.info("")

    for c in customers:
        logger.info(f"  ✅ {c['first_name']} {c['last_name']}")
        logger.info(f"     Email: {c['email']}")
        logger.info(f"     Revenue: ${c['total_spent']:,.2f}")
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
    logger.info("║" + "BUSINESS OWNER NAME ENRICHMENT".center(78) + "║")
    logger.info("║" + "Top 3 revenue customers: $2,442".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")

        # Verify customers
        verify_customers(conn)

        # Preview enrichments
        preview_enrichments()

        # Execute enrichment
        execute_enrichment(conn, dry_run=False)

        # Verify results
        verify_results(conn)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ BUSINESS OWNER ENRICHMENT COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info("  • 3 business owners enriched with last names")
        logger.info("  • $2,442 revenue impact (TOP revenue customers)")
        logger.info("  • Verified via web research")
        logger.info("  • High confidence matches")
        logger.info("")
        logger.info("Businesses enriched:")
        logger.info("  • Roots of Wellness Ayurveda - Heather Baines")
        logger.info("  • Depths of Feminine - Juliet Haines")
        logger.info("  • Sol Luna Healing - Kelly Barrett")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
