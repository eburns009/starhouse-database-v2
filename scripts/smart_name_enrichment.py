#!/usr/bin/env python3
"""
FAANG-Quality Smart Name Enrichment
Improved email parsing with validation and confidence scoring
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import re
import logging
from datetime import datetime
from db_config import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/smart_enrichment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()


def smart_parse_email(email):
    """
    Intelligently parse name from email with confidence scoring
    Returns: (first_name, last_name, confidence_level)
    """
    if not email or '@' not in email:
        return None, None, 'NONE'

    local_part = email.split('@')[0].lower()

    # Pattern 1: first.last or first_last (HIGH confidence)
    match = re.match(r'^([a-z]{2,})[._]([a-z]{2,})$', local_part)
    if match:
        first = match.group(1).title()
        last = match.group(2).title()
        # Validate names aren't weird patterns
        if len(first) >= 2 and len(last) >= 2 and first.isalpha() and last.isalpha():
            return first, last, 'HIGH'

    # Pattern 2: firstlast (two distinct words) - use common name dictionary
    # heather, juliet, kelly, natalie are common first names
    common_first_names = {
        'heather', 'juliet', 'kelly', 'natalie', 'rachel', 'sarah', 'jessica',
        'jennifer', 'amanda', 'melissa', 'lauren', 'ashley', 'emily', 'nicole',
        'stephanie', 'michelle', 'elizabeth', 'rebecca', 'maria', 'lisa'
    }

    for name in common_first_names:
        if local_part.startswith(name) and len(local_part) > len(name):
            return name.title(), None, 'MEDIUM'

    # Pattern 3: Single common first name (kelly, heather, etc.)
    if local_part in common_first_names:
        return local_part.title(), None, 'HIGH'

    # Pattern 4: first-last with hyphen
    match = re.match(r'^([a-z]{2,})-([a-z]{2,})$', local_part)
    if match:
        first = match.group(1).title()
        last = match.group(2).title()
        if first.isalpha() and last.isalpha():
            return first, last, 'HIGH'

    return None, None, 'NONE'


def load_paying_customers(conn):
    """Load paying customers with missing names"""
    query = """
        SELECT
            id, email, first_name, last_name, total_spent,
            transaction_count, source_system, paypal_business_name
        FROM contacts
        WHERE (first_name IS NULL OR first_name = '' OR TRIM(first_name) = '')
           OR (last_name IS NULL OR last_name = '' OR TRIM(last_name) = '')
        AND total_spent > 0
        ORDER BY total_spent DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def analyze_and_categorize(customers):
    """Categorize customers by enrichment confidence"""
    high_confidence = []
    medium_confidence = []
    needs_review = []

    for customer in customers:
        first, last, confidence = smart_parse_email(customer['email'])

        if confidence == 'HIGH' and first:
            high_confidence.append({
                'customer': customer,
                'first_name': first,
                'last_name': last,
                'confidence': 'HIGH'
            })
        elif confidence == 'MEDIUM' and first:
            medium_confidence.append({
                'customer': customer,
                'first_name': first,
                'last_name': last,
                'confidence': 'MEDIUM'
            })
        else:
            needs_review.append(customer)

    return high_confidence, medium_confidence, needs_review


def preview_enrichments(high_conf, medium_conf, needs_review):
    """Preview categorized enrichments"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("SMART ENRICHMENT ANALYSIS")
    logger.info("=" * 80)
    logger.info("")

    logger.info(f"HIGH CONFIDENCE (auto-approve): {len(high_conf):3d}")
    logger.info(f"MEDIUM CONFIDENCE (verify):     {len(medium_conf):3d}")
    logger.info(f"NEEDS MANUAL REVIEW:            {len(needs_review):3d}")
    logger.info("")

    if high_conf:
        logger.info("HIGH CONFIDENCE ENRICHMENTS (will execute automatically):")
        logger.info("")
        for i, item in enumerate(high_conf[:15], 1):
            c = item['customer']
            logger.info(f"{i:2d}. {c['email']:45s} ${c['total_spent']:8.2f}")
            logger.info(f"    → {item['first_name']} {item.get('last_name', '(no last name)')}")
        if len(high_conf) > 15:
            logger.info(f"    ... and {len(high_conf) - 15} more")
        logger.info("")

    if medium_conf:
        logger.info("MEDIUM CONFIDENCE (review recommended):")
        logger.info("")
        for i, item in enumerate(medium_conf[:10], 1):
            c = item['customer']
            logger.info(f"{i:2d}. {c['email']:45s} ${c['total_spent']:8.2f}")
            logger.info(f"    → {item['first_name']} (first name only)")
        if len(medium_conf) > 10:
            logger.info(f"    ... and {len(medium_conf) - 10} more")
        logger.info("")


def execute_enrichment(conn, enrichments, category_name, dry_run=True):
    """Execute enrichment for a category"""
    if not enrichments:
        return 0

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"{'DRY RUN: ' if dry_run else ''}ENRICHING {category_name}")
    logger.info("=" * 80)
    logger.info("")

    if dry_run:
        logger.info(f"DRY RUN - Would update {len(enrichments)} customers")
        return len(enrichments)

    updated = 0

    try:
        for item in enrichments:
            customer = item['customer']
            first = item.get('first_name')
            last = item.get('last_name')

            if not first:
                continue

            # Escape quotes
            escaped_first = first.replace("'", "''")
            escaped_last = last.replace("'", "''") if last else None

            updates = [f"first_name = '{escaped_first}'"]
            if escaped_last:
                updates.append(f"last_name = '{escaped_last}'")
            updates.append("updated_at = NOW()")

            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE contacts
                    SET {', '.join(updates)}
                    WHERE id = '{customer['id']}'
                """)

            updated += 1
            logger.info(f"✅ {customer['email']} → {first} {last or ''}")

        conn.commit()
        logger.info("")
        logger.info(f"✅ Successfully updated {updated} customers")

    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        conn.rollback()
        raise

    return updated


def main():
    """Main workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "SMART NAME ENRICHMENT - HIGH-VALUE CUSTOMERS".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        conn = psycopg2.connect(DATABASE_URL)

        # Load customers
        customers = load_paying_customers(conn)
        total_revenue = sum(c['total_spent'] for c in customers)

        logger.info(f"Found {len(customers)} paying customers with missing names")
        logger.info(f"Total revenue: ${total_revenue:,.2f}")

        # Analyze and categorize
        high_conf, medium_conf, needs_review = analyze_and_categorize(customers)

        # Preview
        preview_enrichments(high_conf, medium_conf, needs_review)

        # Execute HIGH CONFIDENCE automatically (dry run first)
        logger.info("=" * 80)
        logger.info("EXECUTION PLAN")
        logger.info("=" * 80)
        logger.info("")
        logger.info("HIGH CONFIDENCE will be executed automatically")
        logger.info("MEDIUM CONFIDENCE requires manual approval")
        logger.info("")

        # DRY RUN
        execute_enrichment(conn, high_conf, "HIGH CONFIDENCE", dry_run=True)

        logger.info("")
        logger.info("To execute:")
        logger.info("  Edit line 242: execute_enrichment(conn, high_conf, 'HIGH CONFIDENCE', dry_run=False)")
        logger.info("")

        # Execute for real
        execute_enrichment(conn, high_conf, "HIGH CONFIDENCE", dry_run=False)

        # Verify after execution
        verify_enrichment(conn)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ ANALYSIS COMPLETE")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)
        raise


def verify_enrichment(conn):
    """Verify enrichment results"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("VERIFICATION")
    logger.info("=" * 80)
    logger.info("")

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_paying,
                SUM(CASE WHEN (first_name IS NULL OR first_name = '')
                         AND (last_name IS NULL OR last_name = '')
                    THEN 1 ELSE 0 END) as still_missing
            FROM contacts
            WHERE total_spent > 0
        """)
        stats = cursor.fetchone()

    logger.info(f"Paying customers total:       {stats['total_paying']:,}")
    logger.info(f"Still missing names:          {stats['still_missing']:,}")
    logger.info(f"Successfully enriched:        {stats['total_paying'] - stats['still_missing']:,}")
    logger.info("")


if __name__ == '__main__':
    main()
