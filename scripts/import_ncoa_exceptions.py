#!/usr/bin/env python3
"""
Import TrueNCOA Exceptions with Corrected ZIP Codes

Handles the 706 exception records (Status = 'N') from TrueNCOA where ZIP codes
were truncated in the output but correct in the input.

Strategy:
- Use TrueNCOA's corrected address data (Address Line 1, City, State)
- Use the CORRECT ZIP from input_PostalCode (not truncated Postal Code)
- Update database with properly formatted addresses

Author: StarHouse CRM
Date: 2025-11-15
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import csv
import logging
from datetime import datetime
import sys
import os

# Configure logging
log_filename = f'logs/import_ncoa_exceptions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


class NCOAExceptionImporter:
    """Import TrueNCOA exceptions with corrected ZIP codes"""

    def __init__(self, input_file, dry_run=False):
        self.input_file = input_file
        self.dry_run = dry_run
        self.conn = None
        self.stats = {
            'total_exceptions': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'zip_corrections': 0
        }

    def create_backup(self):
        """Create backup before making changes"""
        backup_table = f"contacts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_exceptions"

        logger.info("")
        logger.info("=" * 80)
        logger.info("CREATING BACKUP")
        logger.info("=" * 80)
        logger.info("")

        if self.dry_run:
            logger.info("DRY RUN - Would create backup table: %s", backup_table)
            return backup_table

        try:
            with self.conn.cursor() as cursor:
                # Drop if exists
                cursor.execute(
                    sql.SQL("DROP TABLE IF EXISTS {}").format(
                        sql.Identifier(backup_table)
                    )
                )

                # Create backup
                cursor.execute(
                    sql.SQL("CREATE TABLE {} AS SELECT * FROM contacts").format(
                        sql.Identifier(backup_table)
                    )
                )

                # Verify backup
                cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(backup_table)
                    )
                )
                backup_count = cursor.fetchone()[0]

                self.conn.commit()

                logger.info("✅ Backup created: %s", backup_table)
                logger.info("   Records backed up: %s", f"{backup_count:,}")
                logger.info("")

                return backup_table

        except Exception as e:
            logger.error("❌ Backup failed: %s", e)
            raise

    def read_exceptions(self):
        """Read exception records from TrueNCOA CSV"""
        logger.info("=" * 80)
        logger.info("READING TRUENCOA EXCEPTIONS")
        logger.info("=" * 80)
        logger.info("")

        if not os.path.exists(self.input_file):
            logger.error("❌ File not found: %s", self.input_file)
            sys.exit(1)

        exceptions = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Only process exception records (Status = 'N')
                if row.get('Address Status') == 'N':
                    exceptions.append(row)

        logger.info("✅ Found %s exception records (Status = 'N')", f"{len(exceptions):,}")
        logger.info("")

        return exceptions

    def update_exception(self, record):
        """Update a single exception record with corrected data"""
        contact_id = record.get('input_ID', '').strip()

        if not contact_id:
            logger.warning("⚠️  Missing contact ID")
            self.stats['errors'] += 1
            return False

        # Extract corrected address from TrueNCOA
        new_address1 = record.get('Address Line 1', '').strip()
        new_address2 = record.get('Address Line 2', '').strip()
        new_city = record.get('City Name', '').strip()
        new_state = record.get('State Code', '').strip()

        # IMPORTANT: Use input_PostalCode (correct) not Postal Code (truncated)
        correct_zip = record.get('input_PostalCode', '').strip()
        truncated_zip = record.get('Postal Code', '').strip()

        # Skip if no address data
        if not new_address1 or not new_city or not new_state:
            logger.debug("Skipping %s - no address data", contact_id)
            self.stats['skipped'] += 1
            return False

        # Skip if no correct ZIP
        if not correct_zip:
            logger.warning("⚠️  No correct ZIP for contact %s", contact_id)
            self.stats['skipped'] += 1
            return False

        if self.dry_run:
            zip_fixed = len(truncated_zip) < len(correct_zip.replace('-', '')[:5])
            logger.info("DRY RUN - Would update contact %s:", contact_id)
            logger.info("  Address: %s, %s, %s", new_address1, new_city, new_state)
            logger.info("  ZIP: %s %s", correct_zip,
                       f"(FIXED from {truncated_zip})" if zip_fixed else "")
            self.stats['updated'] += 1
            if zip_fixed:
                self.stats['zip_corrections'] += 1
            return True

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Update address with corrected data
                cursor.execute("""
                    UPDATE contacts
                    SET
                        address_line_1 = %s,
                        address_line_2 = %s,
                        city = %s,
                        state = %s,
                        postal_code = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (new_address1, new_address2, new_city, new_state, correct_zip, contact_id))

                if cursor.rowcount > 0:
                    self.stats['updated'] += 1

                    # Track if we fixed a truncated ZIP
                    if truncated_zip and len(truncated_zip) < len(correct_zip.replace('-', '')[:5]):
                        self.stats['zip_corrections'] += 1

                    return True
                else:
                    logger.warning("⚠️  Contact not found: %s", contact_id)
                    self.stats['errors'] += 1
                    return False

        except Exception as e:
            logger.error("❌ Error updating contact %s: %s", contact_id, e)
            self.stats['errors'] += 1
            return False

    def process_exceptions(self, exceptions):
        """Process all exception records"""
        logger.info("=" * 80)
        if self.dry_run:
            logger.info("DRY RUN: PROCESSING EXCEPTIONS")
        else:
            logger.info("PROCESSING EXCEPTIONS")
        logger.info("=" * 80)
        logger.info("")

        self.stats['total_exceptions'] = len(exceptions)

        for i, record in enumerate(exceptions, 1):
            self.update_exception(record)

            # Progress updates every 100 records
            if i % 100 == 0:
                logger.info("Progress: %s/%s | Updated: %s | Skipped: %s | Errors: %s",
                          i, len(exceptions),
                          self.stats['updated'],
                          self.stats['skipped'],
                          self.stats['errors'])

        if not self.dry_run:
            self.conn.commit()

        logger.info("")
        logger.info("✅ Processing complete")
        logger.info("")

    def verify_import(self):
        """Verify the import results"""
        logger.info("=" * 80)
        logger.info("VERIFICATION")
        logger.info("=" * 80)
        logger.info("")

        if self.dry_run:
            logger.info("DRY RUN - Skipping verification")
            return

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check for 5-digit ZIP codes
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE LENGTH(postal_code) = 5) as five_digit_zips,
                        COUNT(*) FILTER (WHERE LENGTH(postal_code) = 10) as extended_zips,
                        COUNT(*) FILTER (WHERE LENGTH(postal_code) < 5) as truncated_zips,
                        COUNT(*) as total
                    FROM contacts
                    WHERE postal_code IS NOT NULL
                """)
                zip_stats = cursor.fetchone()

                logger.info("ZIP Code Statistics:")
                logger.info("  5-digit ZIPs:     %s", f"{zip_stats['five_digit_zips']:,}")
                logger.info("  Extended ZIPs:    %s", f"{zip_stats['extended_zips']:,}")
                logger.info("  Truncated ZIPs:   %s", f"{zip_stats['truncated_zips']:,}")
                logger.info("  Total with ZIP:   %s", f"{zip_stats['total']:,}")
                logger.info("")

        except Exception as e:
            logger.error("❌ Verification failed: %s", e)

    def print_summary(self):
        """Print final summary statistics"""
        logger.info("=" * 80)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 80)
        logger.info("")

        logger.info("Total exception records:   %s", f"{self.stats['total_exceptions']:,}")
        logger.info("")
        logger.info("Results:")
        logger.info("  Updated:                 %s", f"{self.stats['updated']:,}")
        logger.info("  ZIP codes corrected:     %s", f"{self.stats['zip_corrections']:,}")
        logger.info("  Skipped (no data):       %s", f"{self.stats['skipped']:,}")
        logger.info("  Errors:                  %s", f"{self.stats['errors']:,}")
        logger.info("")

        if self.stats['total_exceptions'] > 0:
            success_rate = (self.stats['updated'] / self.stats['total_exceptions']) * 100
            logger.info("Success Rate:              %.1f%%", success_rate)
            logger.info("")

    def run(self):
        """Main execution flow"""
        logger.info("")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + "TRUENCOA EXCEPTIONS IMPORT - ZIP CODE FIX".center(78) + "║")
        if self.dry_run:
            logger.info("║" + "DRY RUN MODE - NO CHANGES WILL BE MADE".center(78) + "║")
        logger.info("╚" + "=" * 78 + "╝")

        try:
            # Connect to database
            self.conn = psycopg2.connect(DATABASE_URL)
            logger.info("")
            logger.info("✅ Connected to database")

            # Create backup
            backup_table = self.create_backup()

            # Read exceptions
            exceptions = self.read_exceptions()

            # Process exceptions
            self.process_exceptions(exceptions)

            # Verify import
            self.verify_import()

            # Print summary
            self.print_summary()

            # Close connection
            self.conn.close()

            logger.info("=" * 80)
            if self.dry_run:
                logger.info("✅ DRY RUN COMPLETE - No changes made")
            else:
                logger.info("✅ EXCEPTION IMPORT COMPLETE")
            logger.info("=" * 80)
            logger.info("")

            if not self.dry_run and backup_table:
                logger.info("Backup table: %s", backup_table)
                logger.info("Log file: %s", log_filename)
                logger.info("")

        except Exception as e:
            logger.error("❌ Import failed: %s", e, exc_info=True)
            if self.conn:
                self.conn.rollback()
                logger.error("Transaction rolled back")
            raise
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import TrueNCOA exceptions with corrected ZIP codes'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='kajabi 3 files review/truencoa.csv',
        help='Path to TrueNCOA results CSV file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no database changes)'
    )

    args = parser.parse_args()

    importer = NCOAExceptionImporter(args.input_file, dry_run=args.dry_run)
    importer.run()


if __name__ == '__main__':
    main()
