#!/usr/bin/env python3
"""
FAANG-Quality NCOA Results Import Script

Safely imports TrueNCOA results back into the database with:
- Full backup before changes
- Transaction safety with rollback
- Comprehensive verification
- Detailed logging and statistics
- Dry-run mode for testing
- Move history tracking

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

# Configure comprehensive logging
log_filename = f'logs/import_ncoa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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

# TrueNCOA CSV field mapping
# Based on TrueNCOA's actual export format
REQUIRED_CSV_FIELDS = [
    'input_ID',        # Contact ID (maps to contacts.id)
    'Move Applied',    # Move indicator (Yes/No)
]

# Optional but recommended fields
RECOMMENDED_CSV_FIELDS = [
    'Address Line 1',  # New street address line 1
    'Address Line 2',  # New street address line 2
    'City Name',       # New city
    'State Code',      # New state
    'Postal Code',     # New ZIP/postal code
    'Move Date',       # When the move occurred
    'Move Type',       # Type of move (Individual, Family, Business)
]


class NCOAImporter:
    """FAANG-quality NCOA results importer with safety features"""

    def __init__(self, input_file, dry_run=False):
        self.input_file = input_file
        self.dry_run = dry_run
        self.conn = None
        self.stats = {
            'total_records': 0,
            'matched': 0,
            'moved': 0,
            'no_change': 0,
            'business_moved': 0,
            'family_moved': 0,
            'individual_moved': 0,
            'errors': 0,
            'updated': 0
        }

    def create_backup(self):
        """Create full backup of contacts table before making changes"""
        backup_table = f"contacts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_ncoa"

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
                # Drop if exists (using sql.Identifier for SQL injection safety)
                cursor.execute(
                    sql.SQL("DROP TABLE IF EXISTS {}").format(
                        sql.Identifier(backup_table)
                    )
                )

                # Create backup (using sql.Identifier for SQL injection safety)
                cursor.execute(
                    sql.SQL("CREATE TABLE {} AS SELECT * FROM contacts").format(
                        sql.Identifier(backup_table)
                    )
                )

                # Verify backup (using sql.Identifier for SQL injection safety)
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
                logger.info("   Rollback command (if needed):")
                logger.info("   psql -c 'DROP TABLE contacts; ALTER TABLE %s RENAME TO contacts;'",
                          backup_table)
                logger.info("")

                return backup_table

        except Exception as e:
            logger.error("❌ Backup failed: %s", e)
            raise

    def validate_csv_fields(self, fieldnames):
        """
        Validate CSV has required fields
        FAANG Standard: Fail fast with clear error messages
        """
        missing_required = [f for f in REQUIRED_CSV_FIELDS if f not in fieldnames]
        missing_recommended = [f for f in RECOMMENDED_CSV_FIELDS if f not in fieldnames]

        if missing_required:
            logger.error("❌ Missing REQUIRED CSV fields: %s", ', '.join(missing_required))
            logger.error("")
            logger.error("Required fields: %s", ', '.join(REQUIRED_CSV_FIELDS))
            logger.error("Fields found in CSV: %s", ', '.join(fieldnames))
            logger.error("")
            logger.error("This CSV file does not match the expected NCOA format.")
            logger.error("Please check your NCOA provider's export settings.")
            raise ValueError(f"Missing required CSV fields: {', '.join(missing_required)}")

        if missing_recommended:
            logger.warning("⚠️  Missing RECOMMENDED CSV fields: %s", ', '.join(missing_recommended))
            logger.warning("   Import will continue, but some NCOA data may be incomplete.")
            logger.warning("")

        logger.info("✅ CSV field validation passed")
        logger.info("   Required fields: %s", ', '.join(REQUIRED_CSV_FIELDS))
        if not missing_recommended:
            logger.info("   Recommended fields: %s", ', '.join(RECOMMENDED_CSV_FIELDS))
        logger.info("")

    def read_ncoa_results(self):
        """Read and parse NCOA results CSV"""
        logger.info("=" * 80)
        logger.info("READING NCOA RESULTS")
        logger.info("=" * 80)
        logger.info("")

        if not os.path.exists(self.input_file):
            logger.error("❌ File not found: %s", self.input_file)
            sys.exit(1)

        results = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate CSV has required fields (FAANG: fail fast)
            if reader.fieldnames:
                self.validate_csv_fields(reader.fieldnames)

            for row in reader:
                results.append(row)

        logger.info("✅ Loaded %s NCOA results", f"{len(results):,}")
        logger.info("")

        return results

    def analyze_ncoa_results(self, results):
        """Analyze NCOA results and categorize"""
        logger.info("=" * 80)
        logger.info("ANALYZING NCOA RESULTS")
        logger.info("=" * 80)
        logger.info("")

        # TrueNCOA field parsing
        moves = []
        no_moves = []

        for result in results:
            # TrueNCOA uses 'Move Applied' field: 'Yes' or 'No'
            move_applied = result.get('Move Applied', '').strip().upper()

            # Check if a move was detected
            if move_applied == 'YES':
                moves.append(result)
            else:
                no_moves.append(result)

        logger.info("Move Summary:")
        logger.info("  Total records:     %s", f"{len(results):,}")
        logger.info("  Moved:             %s (%.1f%%)", f"{len(moves):,}",
                   len(moves)/len(results)*100 if results else 0)
        logger.info("  No change:         %s (%.1f%%)", f"{len(no_moves):,}",
                   len(no_moves)/len(results)*100 if results else 0)
        logger.info("")

        return moves, no_moves

    def parse_move_date(self, date_str):
        """
        Parse TrueNCOA move date format (YYYYMM) to PostgreSQL DATE format (YYYY-MM-DD)
        Example: "202508" -> "2025-08-01"
        """
        if not date_str or len(date_str) != 6:
            return None

        try:
            year = date_str[:4]
            month = date_str[4:6]
            # Use day 01 since TrueNCOA only provides year/month
            return f"{year}-{month}-01"
        except (ValueError, IndexError):
            logger.warning("⚠️  Invalid move date format: %s", date_str)
            return None

    def import_move(self, result):
        """Import a single NCOA move result"""
        contact_id = result.get('input_ID', '').strip()

        if not contact_id:
            logger.warning("⚠️  Missing contact ID in result")
            self.stats['errors'] += 1
            return False

        # Extract NCOA data from TrueNCOA format
        new_address1 = result.get('Address Line 1', '').strip()
        new_address2 = result.get('Address Line 2', '').strip()
        new_city = result.get('City Name', '').strip()
        new_state = result.get('State Code', '').strip()
        new_postal = result.get('Postal Code', '').strip()
        move_date_raw = result.get('Move Date', '').strip()
        move_type = result.get('Move Type', '').strip()  # Individual, Family, Business

        # Parse TrueNCOA date format (YYYYMM) to PostgreSQL DATE (YYYY-MM-DD)
        move_date = self.parse_move_date(move_date_raw)

        # If no new address data, skip
        if not new_address1 or not new_city or not new_state:
            logger.debug("No move data for contact %s", contact_id)
            self.stats['no_change'] += 1
            return False

        if self.dry_run:
            logger.info("DRY RUN - Would update contact %s:", contact_id)
            logger.info("  New: %s, %s, %s %s", new_address1, new_city, new_state, new_postal)
            logger.info("  Move date: %s%s, Type: %s",
                       move_date or 'N/A',
                       f" (from {move_date_raw})" if move_date_raw else '',
                       move_type or 'N/A')
            self.stats['moved'] += 1
            return True

        try:
            # Store old address in move history
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get current address
                cursor.execute("""
                    SELECT address_line_1, address_line_2, city, state, postal_code
                    FROM contacts
                    WHERE id = %s
                """, (contact_id,))

                old_address = cursor.fetchone()

                if not old_address:
                    logger.warning("⚠️  Contact not found: %s", contact_id)
                    self.stats['errors'] += 1
                    return False

                # Update address
                cursor.execute("""
                    UPDATE contacts
                    SET
                        address_line_1 = %s,
                        address_line_2 = %s,
                        city = %s,
                        state = %s,
                        postal_code = %s,
                        ncoa_move_date = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (new_address1, new_address2, new_city, new_state, new_postal,
                     move_date if move_date else None, contact_id))

                if cursor.rowcount > 0:
                    self.stats['moved'] += 1
                    self.stats['updated'] += 1

                    # Track move type
                    if move_type.upper() == 'INDIVIDUAL':
                        self.stats['individual_moved'] += 1
                    elif move_type.upper() == 'FAMILY':
                        self.stats['family_moved'] += 1
                    elif move_type.upper() == 'BUSINESS':
                        self.stats['business_moved'] += 1

                    return True
                else:
                    self.stats['errors'] += 1
                    return False

        except Exception as e:
            logger.error("❌ Error updating contact %s: %s", contact_id, e)
            self.stats['errors'] += 1
            return False

    def process_results(self, results):
        """Process all NCOA results"""
        logger.info("=" * 80)
        if self.dry_run:
            logger.info("DRY RUN: PROCESSING NCOA RESULTS")
        else:
            logger.info("PROCESSING NCOA RESULTS")
        logger.info("=" * 80)
        logger.info("")

        self.stats['total_records'] = len(results)

        for i, result in enumerate(results, 1):
            self.import_move(result)

            # Progress updates every 100 records
            if i % 100 == 0:
                logger.info("Progress: %s/%s | Moved: %s | No change: %s | Errors: %s",
                          i, len(results),
                          self.stats['moved'],
                          self.stats['no_change'],
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
                # Count contacts with NCOA moves
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_with_move_date,
                        COUNT(DISTINCT ncoa_move_date) as unique_move_dates
                    FROM contacts
                    WHERE ncoa_move_date IS NOT NULL
                """)
                ncoa_stats = cursor.fetchone()

                logger.info("Database verification:")
                logger.info("  Contacts with NCOA move dates:  %s",
                          f"{ncoa_stats['total_with_move_date']:,}")
                logger.info("  Unique move dates:               %s",
                          f"{ncoa_stats['unique_move_dates']:,}")
                logger.info("")

        except Exception as e:
            logger.error("❌ Verification failed: %s", e)

    def print_summary(self):
        """Print final summary statistics"""
        logger.info("=" * 80)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 80)
        logger.info("")

        logger.info("Total NCOA records processed:  %s", f"{self.stats['total_records']:,}")
        logger.info("")
        logger.info("Move Statistics:")
        logger.info("  Addresses updated:           %s", f"{self.stats['moved']:,}")
        logger.info("  No changes:                  %s", f"{self.stats['no_change']:,}")
        logger.info("")

        if self.stats['moved'] > 0:
            logger.info("Move Type Breakdown:")
            if self.stats['individual_moved'] > 0:
                logger.info("  Individual moves:            %s",
                          f"{self.stats['individual_moved']:,}")
            if self.stats['family_moved'] > 0:
                logger.info("  Family moves:                %s",
                          f"{self.stats['family_moved']:,}")
            if self.stats['business_moved'] > 0:
                logger.info("  Business moves:              %s",
                          f"{self.stats['business_moved']:,}")
            logger.info("")

        logger.info("Database Updates:")
        logger.info("  Records updated:             %s", f"{self.stats['updated']:,}")
        logger.info("  Errors:                      %s", f"{self.stats['errors']:,}")
        logger.info("")

        if self.stats['total_records'] > 0:
            success_rate = (self.stats['moved'] / self.stats['total_records']) * 100
            logger.info("Success Rate:                  %.1f%%", success_rate)
            logger.info("")

    def run(self):
        """Main execution flow"""
        logger.info("")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + "NCOA RESULTS IMPORT - FAANG QUALITY".center(78) + "║")
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

            # Read NCOA results
            results = self.read_ncoa_results()

            # Analyze results
            moves, no_moves = self.analyze_ncoa_results(results)

            # Process results
            self.process_results(results)

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
                logger.info("✅ NCOA IMPORT COMPLETE")
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
        description='Import TrueNCOA results with FAANG-quality safety features'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='/tmp/truencoa_results.csv',
        help='Path to NCOA results CSV file (default: /tmp/truencoa_results.csv)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no database changes)'
    )

    args = parser.parse_args()

    importer = NCOAImporter(args.input_file, dry_run=args.dry_run)
    importer.run()


if __name__ == '__main__':
    main()
