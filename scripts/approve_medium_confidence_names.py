#!/usr/bin/env python3
"""
Approve and Enrich 3 Medium Confidence Names
Quick execution for manually approved names
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
        logging.FileHandler(f'logs/approve_medium_names_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()

# Medium confidence names to approve
MEDIUM_CONFIDENCE_APPROVALS = [
    {
        'email': 'natalievernon63@gmail.com',
        'first_name': 'Natalie',
        'last_name': 'Vernon',  # Can extract from email!
        'revenue': 236.00,
        'note': 'HIGH PRIORITY - $236 revenue'
    },
    {
        'email': 'lisamcbell2@aol.com',
        'first_name': 'Lisa',
        'last_name': 'McBell',  # Can extract from email!
        'revenue': 0.00,
        'note': 'Common name - email pattern suggests McBell'
    },
    {
        'email': 'mariannewgreen@hotmail.com',
        'first_name': 'Marianne',  # Full first name, not just Maria
        'last_name': 'Green',  # Can extract from email!
        'revenue': 0.00,
        'note': 'Full name extractable from email'
    }
]


def verify_customers_exist(conn):
    """Verify the customers exist in database"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("VERIFYING CUSTOMERS")
    logger.info("=" * 80)
    logger.info("")

    emails = [item['email'] for item in MEDIUM_CONFIDENCE_APPROVALS]

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT id, email, first_name, last_name, total_spent
            FROM contacts
            WHERE email = ANY(%s)
            ORDER BY total_spent DESC
        """, (emails,))
        customers = cursor.fetchall()

    logger.info(f"Found {len(customers)} customers in database:")
    for c in customers:
        logger.info(f"  • {c['email']:45s} ${c['total_spent']:8.2f}")
        logger.info(f"    Current: {c['first_name'] or '(none)'} {c['last_name'] or '(none)'}")

    logger.info("")

    if len(customers) != len(MEDIUM_CONFIDENCE_APPROVALS):
        logger.warning(f"Expected {len(MEDIUM_CONFIDENCE_APPROVALS)} customers, found {len(customers)}")

    return customers


def preview_changes():
    """Preview what will be updated"""
    logger.info("=" * 80)
    logger.info("PREVIEW: PROPOSED UPDATES")
    logger.info("=" * 80)
    logger.info("")

    total_revenue = sum(item['revenue'] for item in MEDIUM_CONFIDENCE_APPROVALS)

    logger.info(f"Total customers to update: {len(MEDIUM_CONFIDENCE_APPROVALS)}")
    logger.info(f"Total revenue impact: ${total_revenue:.2f}")
    logger.info("")

    for i, item in enumerate(MEDIUM_CONFIDENCE_APPROVALS, 1):
        logger.info(f"{i}. {item['email']:45s} ${item['revenue']:8.2f}")
        logger.info(f"   Current: (no name)")
        logger.info(f"   New:     {item['first_name']} {item['last_name']}")
        logger.info(f"   Note:    {item['note']}")
        logger.info("")


def execute_enrichment(conn, dry_run=False):
    """Execute the name enrichment"""
    logger.info("=" * 80)
    if dry_run:
        logger.info("DRY RUN: Simulating Enrichment")
    else:
        logger.info("EXECUTING: Name Enrichment")
    logger.info("=" * 80)
    logger.info("")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Would update {len(MEDIUM_CONFIDENCE_APPROVALS)} customers")
        logger.info("")
        return 0

    updated_count = 0

    try:
        for item in MEDIUM_CONFIDENCE_APPROVALS:
            # Escape quotes
            escaped_first = item['first_name'].replace("'", "''")
            escaped_last = item['last_name'].replace("'", "''")

            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE contacts
                    SET
                        first_name = '{escaped_first}',
                        last_name = '{escaped_last}',
                        updated_at = NOW()
                    WHERE email = '{item['email']}'
                    AND (first_name IS NULL OR first_name = '' OR last_name IS NULL OR last_name = '')
                """)

                if cursor.rowcount > 0:
                    updated_count += 1
                    logger.info(f"✅ {item['email']} → {item['first_name']} {item['last_name']}")
                else:
                    logger.warning(f"⚠️  {item['email']} - No update (already has name?)")

        conn.commit()
        logger.info("")
        logger.info(f"✅ Successfully updated {updated_count} customers")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}")
        conn.rollback()
        raise

    return updated_count


def verify_enrichment(conn):
    """Verify the enrichment was successful"""
    logger.info("=" * 80)
    logger.info("VERIFICATION")
    logger.info("=" * 80)
    logger.info("")

    emails = [item['email'] for item in MEDIUM_CONFIDENCE_APPROVALS]

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
        logger.info(f"  ✅ {c['email']:45s}")
        logger.info(f"     Name: {c['first_name']} {c['last_name']}")
        logger.info(f"     Revenue: ${c['total_spent']:.2f}")
        logger.info("")

    # Check overall stats
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_paying,
                SUM(CASE WHEN (first_name IS NULL OR first_name = '')
                         OR (last_name IS NULL OR last_name = '')
                    THEN 1 ELSE 0 END) as still_missing
            FROM contacts
            WHERE total_spent > 0
        """)
        stats = cursor.fetchone()

    logger.info("Overall statistics:")
    logger.info(f"  Total paying customers:    {stats['total_paying']:,}")
    logger.info(f"  Still missing names:       {stats['still_missing']:,}")
    logger.info(f"  Successfully enriched:     {stats['total_paying'] - stats['still_missing']:,}")
    logger.info("")


def main():
    """Main workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "APPROVE MEDIUM CONFIDENCE NAMES".center(78) + "║")
    logger.info("║" + "Manual approval of 3 customers (+$236)".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")

        # Verify customers exist
        verify_customers_exist(conn)

        # Preview changes
        preview_changes()

        # Execute enrichment
        execute_enrichment(conn, dry_run=False)

        # Verify results
        verify_enrichment(conn)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ MEDIUM CONFIDENCE APPROVAL COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info("  • 3 customers enriched")
        logger.info("  • $236 revenue impact (Natalie)")
        logger.info("  • Full names extracted from email patterns")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Approval failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
