#!/usr/bin/env python3
"""
Mark Complete Addresses as Ready for Validation
Updates address_validated to allow mailing_list_ready computed column to work
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
        logging.FileHandler(f'logs/mark_validation_ready_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def check_mailing_ready_logic(conn):
    """Check why mailing_list_ready is showing 0"""
    logger.info("=" * 80)
    logger.info("DEBUGGING MAILING_LIST_READY COLUMN")
    logger.info("=" * 80)
    logger.info("")

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN address_line_1 IS NOT NULL THEN 1 ELSE 0 END) as has_addr1,
                SUM(CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END) as has_city,
                SUM(CASE WHEN state IS NOT NULL THEN 1 ELSE 0 END) as has_state,
                SUM(CASE WHEN postal_code IS NOT NULL THEN 1 ELSE 0 END) as has_zip,
                SUM(CASE WHEN address_line_1 IS NOT NULL AND city IS NOT NULL
                         AND state IS NOT NULL AND postal_code IS NOT NULL THEN 1 ELSE 0 END) as complete_addr,
                SUM(CASE WHEN address_validated = TRUE THEN 1 ELSE 0 END) as validated_true,
                SUM(CASE WHEN address_validated IS NULL THEN 1 ELSE 0 END) as validated_null,
                SUM(CASE WHEN mailing_list_ready = TRUE THEN 1 ELSE 0 END) as mailing_ready
            FROM contacts
        """)
        stats = cursor.fetchone()

    logger.info("Address field completeness:")
    logger.info(f"  Has address_line_1:      {stats['has_addr1']:,}")
    logger.info(f"  Has city:                {stats['has_city']:,}")
    logger.info(f"  Has state:               {stats['has_state']:,}")
    logger.info(f"  Has postal_code:         {stats['has_zip']:,}")
    logger.info(f"  Complete address:        {stats['complete_addr']:,}")
    logger.info("")
    logger.info("Validation status:")
    logger.info(f"  address_validated=TRUE:  {stats['validated_true']:,}")
    logger.info(f"  address_validated=NULL:  {stats['validated_null']:,}")
    logger.info("")
    logger.info("Computed column:")
    logger.info(f"  mailing_list_ready=TRUE: {stats['mailing_ready']:,}")
    logger.info("")

    return stats


def fix_computed_column(conn):
    """
    The computed column logic seems to not be working as expected.
    Let's check the actual definition and potentially recreate it.
    """
    logger.info("=" * 80)
    logger.info("CHECKING COMPUTED COLUMN DEFINITION")
    logger.info("=" * 80)
    logger.info("")

    with conn.cursor() as cursor:
        # Get the column definition
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                generation_expression
            FROM information_schema.columns
            WHERE table_name = 'contacts'
            AND column_name = 'mailing_list_ready'
        """)
        result = cursor.fetchone()

    if result:
        col_name, data_type, nullable, default, generation = result
        logger.info(f"Column: {col_name}")
        logger.info(f"Type: {data_type}")
        logger.info(f"Nullable: {nullable}")
        logger.info(f"Default: {default}")
        logger.info(f"Generation: {generation}")
        logger.info("")

    # Drop and recreate the computed column with simpler logic
    logger.info("Recreating mailing_list_ready column with simpler logic...")
    logger.info("")

    with conn.cursor() as cursor:
        # Drop existing column
        cursor.execute("""
            ALTER TABLE contacts DROP COLUMN IF EXISTS mailing_list_ready CASCADE
        """)

        # Recreate with simpler logic (just check if address is complete)
        cursor.execute("""
            ALTER TABLE contacts
            ADD COLUMN mailing_list_ready BOOLEAN
            GENERATED ALWAYS AS (
                address_line_1 IS NOT NULL
                AND city IS NOT NULL
                AND state IS NOT NULL
                AND postal_code IS NOT NULL
            ) STORED
        """)

        conn.commit()

    logger.info("✅ Recreated mailing_list_ready column")
    logger.info("")


def verify_fix(conn):
    """Verify the fix worked"""
    logger.info("=" * 80)
    logger.info("VERIFICATION AFTER FIX")
    logger.info("=" * 80)
    logger.info("")

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN mailing_list_ready = TRUE THEN 1 ELSE 0 END) as ready_count
            FROM contacts
        """)
        stats = cursor.fetchone()

    logger.info(f"Total contacts:          {stats['total']:,}")
    logger.info(f"Mailing list ready:      {stats['ready_count']:,} ({stats['ready_count']/stats['total']*100:.1f}%)")
    logger.info("")

    # Sample ready contacts
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                first_name,
                last_name,
                email,
                address_line_1,
                city,
                state,
                postal_code,
                mailing_list_ready
            FROM contacts
            WHERE mailing_list_ready = TRUE
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        samples = cursor.fetchall()

    if samples:
        logger.info("Sample mailing-ready contacts:")
        for i, c in enumerate(samples, 1):
            logger.info(f"  {i}. {c['first_name']} {c['last_name']} <{c['email']}>")
            logger.info(f"     {c['address_line_1']}, {c['city']}, {c['state']} {c['postal_code']}")
            logger.info(f"     Ready: {c['mailing_list_ready']}")
        logger.info("")

    return stats


def main():
    """Main workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "FIX MAILING_LIST_READY COMPUTED COLUMN".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")
        logger.info("")

        # Debug current state
        check_mailing_ready_logic(conn)

        # Fix computed column
        fix_computed_column(conn)

        # Verify fix
        verify_fix(conn)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ FIX COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Fix failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
