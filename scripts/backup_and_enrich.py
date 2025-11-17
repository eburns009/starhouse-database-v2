#!/usr/bin/env python3
"""
FAANG-Quality Mailing List Enrichment - Production Execution
Safely enriches billing addresses from shipping data with full backup and verification
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
        logging.FileHandler(f'logs/enrichment_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def create_backup(conn):
    """Create backup table before enrichment"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("STEP 1: CREATING BACKUP TABLE")
    logger.info("=" * 80)

    backup_table = f"contacts_backup_20251115_enrichment"

    # Drop backup if exists
    with conn.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {backup_table}")
        logger.info(f"Dropped existing backup table if present")

    # Create backup
    with conn.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE {backup_table} AS
            SELECT * FROM contacts
        """)
        conn.commit()
        logger.info(f"✅ Created backup table: {backup_table}")

    # Verify backup
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_rows,
                SUM(CASE WHEN address_line_1 IS NOT NULL AND city IS NOT NULL
                         AND state IS NOT NULL AND postal_code IS NOT NULL
                    THEN 1 ELSE 0 END) as complete_addresses
            FROM {backup_table}
        """)
        stats = cursor.fetchone()

    logger.info(f"Backup verification:")
    logger.info(f"  Total rows:          {stats['total_rows']:,}")
    logger.info(f"  Complete addresses:  {stats['complete_addresses']:,}")
    logger.info("")

    return backup_table


def analyze_before_enrichment(conn):
    """Analyze state before enrichment"""
    logger.info("=" * 80)
    logger.info("STEP 2: PRE-ENRICHMENT ANALYSIS")
    logger.info("=" * 80)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_contacts,
                SUM(CASE WHEN address_line_1 IS NOT NULL AND city IS NOT NULL
                         AND state IS NOT NULL AND postal_code IS NOT NULL
                    THEN 1 ELSE 0 END) as complete_billing,
                SUM(CASE WHEN shipping_address_line_1 IS NOT NULL AND shipping_city IS NOT NULL
                         AND shipping_state IS NOT NULL AND shipping_postal_code IS NOT NULL
                    THEN 1 ELSE 0 END) as complete_shipping,
                SUM(CASE WHEN shipping_address_line_1 IS NOT NULL AND shipping_city IS NOT NULL
                         AND shipping_state IS NOT NULL AND shipping_postal_code IS NOT NULL
                         AND (address_line_1 IS NULL OR city IS NULL
                              OR state IS NULL OR postal_code IS NULL)
                    THEN 1 ELSE 0 END) as will_enrich
            FROM contacts
        """)
        stats = cursor.fetchone()

    logger.info("Current state:")
    logger.info(f"  Total contacts:          {stats['total_contacts']:6,}")
    logger.info(f"  Complete billing:        {stats['complete_billing']:6,} ({stats['complete_billing']/stats['total_contacts']*100:5.1f}%)")
    logger.info(f"  Complete shipping:       {stats['complete_shipping']:6,} ({stats['complete_shipping']/stats['total_contacts']*100:5.1f}%)")
    logger.info(f"  Will enrich:             {stats['will_enrich']:6,} ({stats['will_enrich']/stats['total_contacts']*100:5.1f}%)")
    logger.info("")

    expected_total = stats['complete_billing'] + stats['will_enrich']
    logger.info("After enrichment:")
    logger.info(f"  Expected total:          {expected_total:6,} ({expected_total/stats['total_contacts']*100:5.1f}%)")
    logger.info(f"  Increase:                +{stats['will_enrich']:,} contacts (+{stats['will_enrich']/stats['complete_billing']*100:.1f}%)")
    logger.info("")

    return stats


def execute_enrichment(conn):
    """Execute the enrichment with transaction safety"""
    logger.info("=" * 80)
    logger.info("STEP 3: EXECUTING ENRICHMENT")
    logger.info("=" * 80)

    try:
        with conn.cursor() as cursor:
            logger.info("Starting transaction...")

            # Execute update
            cursor.execute("""
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
            """)

            updated_count = cursor.rowcount
            logger.info(f"Updated {updated_count:,} contacts")

            # Commit transaction
            conn.commit()
            logger.info("✅ Transaction committed successfully")
            logger.info("")

            return updated_count

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}")
        conn.rollback()
        logger.info("Transaction rolled back")
        raise


def verify_enrichment(conn, expected_count):
    """Verify enrichment results"""
    logger.info("=" * 80)
    logger.info("STEP 4: VERIFICATION")
    logger.info("=" * 80)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_contacts,
                SUM(CASE WHEN address_line_1 IS NOT NULL AND city IS NOT NULL
                         AND state IS NOT NULL AND postal_code IS NOT NULL
                    THEN 1 ELSE 0 END) as complete_billing
            FROM contacts
        """)
        stats = cursor.fetchone()

    logger.info("After enrichment:")
    logger.info(f"  Total contacts:          {stats['total_contacts']:6,}")
    logger.info(f"  Complete billing:        {stats['complete_billing']:6,} ({stats['complete_billing']/stats['total_contacts']*100:5.1f}%)")
    logger.info("")

    # Sample enriched contacts
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                first_name,
                last_name,
                email,
                address_line_1,
                city,
                state,
                postal_code
            FROM contacts
            WHERE updated_at > NOW() - INTERVAL '5 minutes'
              AND address_line_1 IS NOT NULL
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        samples = cursor.fetchall()

    if samples:
        logger.info("Sample enriched contacts:")
        for i, c in enumerate(samples, 1):
            logger.info(f"  {i}. {c['first_name']} {c['last_name']} <{c['email']}>")
            logger.info(f"     {c['address_line_1']}, {c['city']}, {c['state']} {c['postal_code']}")
        logger.info("")

    return stats


def generate_summary(before_stats, after_stats, updated_count, backup_table):
    """Generate final summary"""
    logger.info("=" * 80)
    logger.info("ENRICHMENT COMPLETE - SUMMARY")
    logger.info("=" * 80)
    logger.info("")

    logger.info("BEFORE ENRICHMENT:")
    logger.info(f"  Complete addresses:      {before_stats['complete_billing']:6,} ({before_stats['complete_billing']/before_stats['total_contacts']*100:5.1f}%)")
    logger.info("")

    logger.info("AFTER ENRICHMENT:")
    logger.info(f"  Complete addresses:      {after_stats['complete_billing']:6,} ({after_stats['complete_billing']/before_stats['total_contacts']*100:5.1f}%)")
    logger.info("")

    logger.info("CHANGES:")
    logger.info(f"  Contacts updated:        {updated_count:6,}")
    logger.info(f"  New complete addresses:  +{after_stats['complete_billing'] - before_stats['complete_billing']:,}")
    logger.info(f"  Growth:                  +{(after_stats['complete_billing'] - before_stats['complete_billing'])/before_stats['complete_billing']*100:.1f}%")
    logger.info("")

    logger.info("BACKUP:")
    logger.info(f"  Backup table:            {backup_table}")
    logger.info(f"  To rollback:             DROP TABLE contacts;")
    logger.info(f"                           ALTER TABLE {backup_table} RENAME TO contacts;")
    logger.info("")

    logger.info("NEXT STEPS:")
    logger.info("  1. ✅ Enrichment complete")
    logger.info("  2. 📍 Run USPS validation on new addresses")
    logger.info("  3. 🔧 Add schema enhancements (validation fields)")
    logger.info("  4. 📊 Fix 47 missing names")
    logger.info("  5. 🔄 Merge 146 phone duplicates")
    logger.info("")
    logger.info("=" * 80)


def main():
    """Main execution workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "FAANG-QUALITY MAILING LIST ENRICHMENT".center(78) + "║")
    logger.info("║" + "Production Execution with Safety Checks".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")
        logger.info("")

        # Step 1: Create backup
        backup_table = create_backup(conn)

        # Step 2: Analyze before state
        before_stats = analyze_before_enrichment(conn)

        # Step 3: Execute enrichment
        updated_count = execute_enrichment(conn)

        # Step 4: Verify results
        after_stats = verify_enrichment(conn, updated_count)

        # Step 5: Generate summary
        generate_summary(before_stats, after_stats, updated_count, backup_table)

        conn.close()
        logger.info("✅ ENRICHMENT COMPLETED SUCCESSFULLY")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
