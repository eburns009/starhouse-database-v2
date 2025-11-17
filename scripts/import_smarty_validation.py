#!/usr/bin/env python3
"""
Import SmartyStreets validation results into the database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/import_smarty_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

def read_validation_results(filepath):
    """Read SmartyStreets validation results"""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def read_contact_mapping(filepath):
    """Read contact ID mapping from input file"""
    mapping = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sequence = row['sequence']
            contact_id = row['contact_id']
            mapping[sequence] = contact_id
    return mapping

def main():
    logger.info("")
    logger.info("=" * 80)
    logger.info("IMPORTING SMARTYSTREETS VALIDATION RESULTS")
    logger.info("=" * 80)
    logger.info("")

    # File paths
    validation_file = '/tmp/shipping_addresses_validated.csv'
    mapping_file = '/tmp/shipping_addresses_for_validation.csv'

    # Read files
    logger.info("Reading validation results...")
    validation_results = read_validation_results(validation_file)
    logger.info(f"  ✓ Loaded {len(validation_results)} validation results")

    logger.info("Reading contact ID mapping...")
    contact_mapping = read_contact_mapping(mapping_file)
    logger.info(f"  ✓ Loaded {len(contact_mapping)} contact mappings")
    logger.info("")

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    logger.info("✅ Connected to database")
    logger.info("")

    # Statistics
    stats = {
        'total': len(validation_results),
        'validated': 0,
        'failed': 0,
        'updated': 0,
        'skipped': 0
    }

    logger.info("Importing validation results...")
    logger.info("-" * 80)

    try:
        for i, result in enumerate(validation_results, 1):
            sequence = result.get('[sequence]', '').strip()

            # Skip if no sequence (error rows)
            if not sequence:
                stats['skipped'] += 1
                continue

            # Get contact ID
            contact_id = contact_mapping.get(sequence)
            if not contact_id:
                logger.warning(f"⚠️  No contact ID for sequence {sequence}")
                stats['skipped'] += 1
                continue

            validation_flag = result.get('ValidationFlag', '').strip()

            if validation_flag == 'OK':
                # Address validated successfully
                stats['validated'] += 1

                # Extract validation data
                dpv_match = result.get('[dpv_match_code]', '')
                delivery_line1 = result.get('[delivery_line_1]', '')
                city = result.get('[city_name]', '')
                state = result.get('[state_abbreviation]', '')
                zipcode = result.get('[full_zipcode]', '')
                county = result.get('[county_name]', '')
                rdi = result.get('[rdi]', '')
                latitude = result.get('[latitude]', '')
                longitude = result.get('[longitude]', '')

                # Update contact
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE contacts
                        SET
                            address_validated = true,
                            usps_dpv_confirmation = %s,
                            usps_validation_date = NOW(),
                            usps_rdi = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (dpv_match, rdi, contact_id))

                    if cursor.rowcount > 0:
                        stats['updated'] += 1

            else:
                # Validation failed
                stats['failed'] += 1

                # Mark as not validated
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE contacts
                        SET
                            address_validated = false,
                            usps_validation_date = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                    """, (contact_id,))

            # Progress update every 100
            if i % 100 == 0:
                logger.info(f"  Progress: {i}/{stats['total']} | "
                          f"Validated: {stats['validated']} | "
                          f"Failed: {stats['failed']} | "
                          f"Updated: {stats['updated']}")

        conn.commit()
        logger.info("")
        logger.info("=" * 80)
        logger.info("IMPORT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total results processed:  {stats['total']}")
        logger.info(f"Successfully validated:   {stats['validated']}")
        logger.info(f"Failed validation:        {stats['failed']}")
        logger.info(f"Database records updated: {stats['updated']}")
        logger.info(f"Skipped:                  {stats['skipped']}")
        logger.info("")

        # Verification
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN address_validated = true THEN 1 ELSE 0 END) as validated,
                    SUM(CASE WHEN usps_dpv_confirmation = 'Y' THEN 1 ELSE 0 END) as dpv_y,
                    SUM(CASE WHEN usps_dpv_confirmation = 'D' THEN 1 ELSE 0 END) as dpv_d,
                    SUM(CASE WHEN usps_dpv_confirmation = 'S' THEN 1 ELSE 0 END) as dpv_s
                FROM contacts
                WHERE address_line_1 IS NOT NULL
            """)
            db_stats = cursor.fetchone()

        logger.info("Database verification:")
        logger.info(f"  Total contacts with addresses:     {db_stats['total']:,}")
        logger.info(f"  Validated addresses:               {db_stats['validated']:,}")
        logger.info(f"  DPV Confirmed (Y):                 {db_stats['dpv_y']:,}")
        logger.info(f"  DPV Confirmed Missing Unit (D):    {db_stats['dpv_d']:,}")
        logger.info(f"  DPV Confirmed Secondary (S):       {db_stats['dpv_s']:,}")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Import failed: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()

    logger.info("✅ Import complete!")
    logger.info("")

if __name__ == '__main__':
    main()
