#!/usr/bin/env python3
"""
Show the 36 remaining paying customers with missing names
Prioritized by revenue for targeted enrichment
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from db_config import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()


def show_remaining_customers(conn):
    """Show all remaining customers with missing names"""

    query = """
        SELECT
            email,
            first_name,
            last_name,
            total_spent,
            transaction_count,
            phone,
            city,
            state,
            source_system,
            paypal_business_name
        FROM contacts
        WHERE total_spent > 0
          AND ((first_name IS NULL OR first_name = '' OR TRIM(first_name) = '')
               OR (last_name IS NULL OR last_name = '' OR TRIM(last_name) = ''))
        ORDER BY total_spent DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        customers = cursor.fetchall()

    total_revenue = sum(c['total_spent'] for c in customers)

    logger.info("")
    logger.info("=" * 100)
    logger.info("REMAINING 36 PAYING CUSTOMERS WITH MISSING NAMES")
    logger.info("=" * 100)
    logger.info("")
    logger.info(f"Total: {len(customers)} customers")
    logger.info(f"Total revenue: ${total_revenue:,.2f}")
    logger.info("")

    # Categorize by revenue tiers
    high_value = [c for c in customers if c['total_spent'] >= 100]
    medium_value = [c for c in customers if 10 < c['total_spent'] < 100]
    low_value = [c for c in customers if 0 < c['total_spent'] <= 10]

    logger.info(f"HIGH VALUE (≥$100):   {len(high_value):2d} customers  (${sum(c['total_spent'] for c in high_value):,.2f})")
    logger.info(f"MEDIUM VALUE ($10-99): {len(medium_value):2d} customers  (${sum(c['total_spent'] for c in medium_value):,.2f})")
    logger.info(f"LOW VALUE (<$10):     {len(low_value):2d} customers  (${sum(c['total_spent'] for c in low_value):,.2f})")
    logger.info("")

    # Show all customers
    logger.info("=" * 100)
    logger.info("FULL LIST (Sorted by Revenue)")
    logger.info("=" * 100)
    logger.info("")

    for i, c in enumerate(customers, 1):
        logger.info(f"{i:2d}. {c['email']:50s} ${c['total_spent']:8.2f}")

        # Show current name status
        name_status = []
        if c['first_name']:
            name_status.append(f"First: {c['first_name']}")
        if c['last_name']:
            name_status.append(f"Last: {c['last_name']}")

        if name_status:
            logger.info(f"    Current: {', '.join(name_status)}")
        else:
            logger.info(f"    Current: (no name)")

        # Show additional info
        info = []
        if c['phone']:
            info.append(f"Phone: {c['phone']}")
        if c['city'] and c['state']:
            info.append(f"Location: {c['city']}, {c['state']}")
        if c['paypal_business_name']:
            info.append(f"Business: {c['paypal_business_name']}")
        if c['source_system']:
            info.append(f"Source: {c['source_system']}")

        if info:
            logger.info(f"    {' | '.join(info)}")

        # Suggest possible enrichment
        email_local = c['email'].split('@')[0].lower()
        suggestions = []

        # Check for initials pattern (j.perata, r.babkiewich)
        if '.' in email_local and len(email_local.split('.')) == 2:
            parts = email_local.split('.')
            if len(parts[0]) == 1:  # Single letter
                suggestions.append(f"Initial + last name pattern: {parts[1].title()}")

        # Check for common patterns
        if c['paypal_business_name']:
            suggestions.append(f"Check business name: {c['paypal_business_name']}")

        if suggestions:
            logger.info(f"    💡 {'; '.join(suggestions)}")

        logger.info("")

    # Summary by priority
    logger.info("=" * 100)
    logger.info("PRIORITY RECOMMENDATIONS")
    logger.info("=" * 100)
    logger.info("")

    if high_value:
        logger.info(f"🔴 HIGH PRIORITY ({len(high_value)} customers - ${sum(c['total_spent'] for c in high_value):,.2f}):")
        for c in high_value:
            logger.info(f"   • {c['email']:50s} ${c['total_spent']:8.2f}")
        logger.info("")

    if medium_value:
        logger.info(f"🟡 MEDIUM PRIORITY ({len(medium_value)} customers - ${sum(c['total_spent'] for c in medium_value):,.2f}):")
        for c in medium_value[:5]:
            logger.info(f"   • {c['email']:50s} ${c['total_spent']:8.2f}")
        if len(medium_value) > 5:
            logger.info(f"   ... and {len(medium_value) - 5} more")
        logger.info("")

    logger.info(f"🟢 LOW PRIORITY ({len(low_value)} customers - ${sum(c['total_spent'] for c in low_value):,.2f})")
    logger.info("   Consider bulk deletion or low-priority manual research")
    logger.info("")

    return customers


def main():
    """Main function"""
    logger.info("")
    logger.info("╔" + "=" * 98 + "╗")
    logger.info("║" + "REMAINING CUSTOMERS WITH MISSING NAMES".center(98) + "║")
    logger.info("╚" + "=" * 98 + "╝")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        customers = show_remaining_customers(conn)
        conn.close()

    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
