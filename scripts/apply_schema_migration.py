#!/usr/bin/env python3
"""
Apply Schema Migration for Address Validation Fields
FAANG-quality migration execution with rollback capability
"""

import psycopg2
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/schema_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
MIGRATION_FILE = "supabase/migrations/20251115000003_add_address_validation_fields.sql"


def read_migration_file():
    """Read migration SQL from file"""
    migration_path = Path(MIGRATION_FILE)

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {MIGRATION_FILE}")

    with open(migration_path, 'r') as f:
        sql = f.read()

    logger.info(f"Read migration file: {MIGRATION_FILE}")
    logger.info(f"Size: {len(sql)} characters")
    logger.info("")

    return sql


def apply_migration(conn, sql):
    """Apply migration with transaction safety"""
    logger.info("=" * 80)
    logger.info("APPLYING SCHEMA MIGRATION")
    logger.info("=" * 80)
    logger.info("")

    try:
        with conn.cursor() as cursor:
            logger.info("Starting transaction...")

            # Execute migration
            cursor.execute(sql)

            logger.info("Migration SQL executed successfully")

            # Commit transaction
            conn.commit()
            logger.info("✅ Transaction committed")
            logger.info("")

            return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        logger.info("Transaction rolled back")
        raise


def verify_migration(conn):
    """Verify migration was successful"""
    logger.info("=" * 80)
    logger.info("VERIFYING MIGRATION")
    logger.info("=" * 80)
    logger.info("")

    expected_columns = [
        'address_validated',
        'usps_dpv_confirmation',
        'usps_validation_date',
        'usps_rdi',
        'ncoa_move_date',
        'ncoa_new_address',
        'address_quality_score',
        'mailing_list_ready',
        'household_id',
        'is_primary_household_contact',
        'secondary_emails',
        'is_alias_of',
        'merge_history'
    ]

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'contacts'
            AND column_name = ANY(%s)
            ORDER BY column_name
        """, (expected_columns,))

        columns = cursor.fetchall()

    logger.info("New columns added:")
    for col_name, data_type, nullable in columns:
        logger.info(f"  ✅ {col_name:30s} {data_type:20s} {'NULL' if nullable == 'YES' else 'NOT NULL'}")

    logger.info("")

    missing = set(expected_columns) - set([col[0] for col in columns])
    if missing:
        logger.error(f"❌ Missing columns: {missing}")
        return False

    logger.info(f"✅ All {len(expected_columns)} columns added successfully")
    logger.info("")

    return True


def verify_indexes(conn):
    """Verify indexes were created"""
    logger.info("=" * 80)
    logger.info("VERIFYING INDEXES")
    logger.info("=" * 80)
    logger.info("")

    expected_indexes = [
        'idx_contacts_mailing_ready',
        'idx_contacts_address_validated',
        'idx_contacts_household_id',
        'idx_contacts_is_alias_of',
        'idx_contacts_usps_validation'
    ]

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'contacts'
            AND indexname = ANY(%s)
            ORDER BY indexname
        """, (expected_indexes,))

        indexes = [row[0] for row in cursor.fetchall()]

    logger.info("Indexes created:")
    for idx in indexes:
        logger.info(f"  ✅ {idx}")

    logger.info("")

    missing = set(expected_indexes) - set(indexes)
    if missing:
        logger.warning(f"⚠️  Missing indexes: {missing}")
    else:
        logger.info(f"✅ All {len(expected_indexes)} indexes created successfully")

    logger.info("")


def check_mailing_ready_status(conn):
    """Check how many contacts are now marked as mailing_list_ready"""
    logger.info("=" * 80)
    logger.info("MAILING LIST READINESS CHECK")
    logger.info("=" * 80)
    logger.info("")

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN mailing_list_ready THEN 1 ELSE 0 END) as ready_count
            FROM contacts
        """)

        total, ready_count = cursor.fetchone()

    logger.info(f"Total contacts:          {total:,}")
    logger.info(f"Mailing list ready:      {ready_count:,} ({ready_count/total*100:.1f}%)")
    logger.info("")
    logger.info("Note: mailing_list_ready is a computed column based on:")
    logger.info("  - Has complete address (line_1, city, state, postal_code)")
    logger.info("  - Address validated (or validation pending)")
    logger.info("")


def main():
    """Main migration workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "SCHEMA MIGRATION: ADDRESS VALIDATION FIELDS".center(78) + "║")
    logger.info("║" + "FAANG-Quality Migration Execution".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    try:
        # Read migration file
        sql = read_migration_file()

        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")
        logger.info("")

        # Apply migration
        apply_migration(conn, sql)

        # Verify columns
        if not verify_migration(conn):
            raise Exception("Migration verification failed")

        # Verify indexes
        verify_indexes(conn)

        # Check mailing ready status
        check_mailing_ready_status(conn)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run USPS validation: python3 scripts/validate_addresses_usps.py")
        logger.info("  2. Fix 47 missing names: Review exported CSV")
        logger.info("  3. Merge phone duplicates: Create consolidation script")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
