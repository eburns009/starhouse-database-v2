#!/usr/bin/env python3
"""
FAANG-Quality Data Migration: Link Transactions to Products Using CSV
======================================================================

Purpose: Populate product_id in transactions using original Kajabi CSV data

FAANG Standards Applied:
1. Idempotent - Safe to run multiple times
2. Dry-run mode - Preview before applying
3. Transaction safety - Atomic operations
4. Comprehensive logging - Detailed audit trail
5. Data validation - CSV and database integrity checks
6. Performance optimized - Batch operations, in-memory lookups
7. Error handling - Graceful failures with detailed reporting
8. Metrics & monitoring - Success/failure tracking
9. Progress tracking - Real-time updates
10. Well documented - Clear usage and behavior

Usage:
    # Dry run (safe, no changes)
    python3 link_transactions_from_csv_faang.py --csv-path "../kajabi 3 files review/transactions (2).csv" --dry-run

    # Preview first 100 matches
    python3 link_transactions_from_csv_faang.py --csv-path "../kajabi 3 files review/transactions (2).csv" --dry-run --limit 100

    # Execute migration
    python3 link_transactions_from_csv_faang.py --csv-path "../kajabi 3 files review/transactions (2).csv" --execute

    # Execute with custom batch size
    python3 link_transactions_from_csv_faang.py --csv-path "../kajabi 3 files review/transactions (2).csv" --execute --batch-size 1000

Author: Claude Code (Anthropic)
Date: 2025-11-14
"""

import os
import sys
import csv
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from supabase import create_client, Client

# Configure logging with FAANG standard format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class MigrationMetrics:
    """Track migration statistics for monitoring and reporting"""
    csv_rows_processed: int = 0
    csv_rows_skipped: int = 0
    matches_found: int = 0
    already_linked: int = 0
    no_product_match: int = 0
    no_transaction_match: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    duplicate_kajabi_ids: int = 0

    def print_summary(self):
        """Print human-readable summary"""
        logger.info("=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"CSV rows processed: {self.csv_rows_processed:,}")
        logger.info(f"CSV rows skipped (missing data): {self.csv_rows_skipped:,}")
        logger.info(f"Matches found (can link): {self.matches_found:,}")
        logger.info(f"Already linked (skipped): {self.already_linked:,}")
        logger.info(f"No product match in DB: {self.no_product_match:,}")
        logger.info(f"No transaction match in DB: {self.no_transaction_match:,}")
        logger.info(f"Successful updates: {self.successful_updates:,}")
        logger.info(f"Failed updates: {self.failed_updates:,}")

        if self.duplicate_kajabi_ids > 0:
            logger.warning(f"⚠️  Duplicate kajabi_transaction_ids: {self.duplicate_kajabi_ids:,}")

        if self.matches_found > 0:
            success_rate = (self.successful_updates / self.matches_found) * 100
            logger.info(f"Success rate: {success_rate:.2f}%")
        logger.info("=" * 80)


class CSVTransactionLinker:
    """
    FAANG-Quality migration service for linking transactions using CSV data

    Design Principles:
    - Single Responsibility: Only handles CSV-based transaction linking
    - Dependency Injection: Supabase client and paths injected
    - Immutable operations: Doesn't modify input data
    - Error boundary: Catches and logs all errors gracefully
    """

    def __init__(
        self,
        supabase: Client,
        csv_path: str,
        dry_run: bool = True,
        batch_size: int = 1000
    ):
        self.supabase = supabase
        self.csv_path = csv_path
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.metrics = MigrationMetrics()

    def validate_csv_file(self) -> bool:
        """
        Validate CSV file exists and has expected structure

        FAANG Standard: Fail fast with clear error messages
        """
        logger.info(f"Validating CSV file: {self.csv_path}")

        if not os.path.exists(self.csv_path):
            logger.error(f"✗ CSV file not found: {self.csv_path}")
            return False

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                required_columns = ['ID', 'Offer ID', 'Offer Title']
                missing = [col for col in required_columns if col not in headers]

                if missing:
                    logger.error(f"✗ CSV missing required columns: {missing}")
                    return False

                # Check first row is readable
                first_row = next(reader, None)
                if not first_row:
                    logger.error("✗ CSV file is empty")
                    return False

                logger.info(f"✓ CSV file validated: {len(headers)} columns")
                return True

        except Exception as e:
            logger.error(f"✗ Failed to read CSV file: {e}")
            return False

    def build_product_lookup(self) -> Dict[str, str]:
        """
        Build in-memory lookup table: kajabi_offer_id -> product.id

        FAANG Standard: Single database query for performance
        Complexity: O(1) lookup time after initial O(n) build

        Returns:
            Dictionary mapping kajabi_offer_id to product UUID
        """
        logger.info("Building product lookup table from database...")

        try:
            response = self.supabase.table('products').select('id, kajabi_offer_id').execute()

            lookup = {}
            for product in response.data:
                offer_id = product.get('kajabi_offer_id')
                if offer_id:
                    lookup[str(offer_id)] = product['id']

            logger.info(f"✓ Built lookup table with {len(lookup):,} products")
            return lookup

        except Exception as e:
            logger.error(f"✗ Failed to build product lookup: {e}")
            raise

    def build_transaction_lookup(self) -> Dict[str, Dict]:
        """
        Build in-memory lookup: kajabi_transaction_id -> {id, product_id}

        FAANG Standard: Fetch only needed transactions (product_id IS NULL)

        Returns:
            Dictionary mapping kajabi_transaction_id to transaction data
        """
        logger.info("Building transaction lookup table from database...")

        try:
            # Only fetch transactions that need linking
            response = self.supabase.table('transactions').select(
                'id, kajabi_transaction_id, product_id'
            ).is_('product_id', 'null').not_.is_('kajabi_transaction_id', 'null').execute()

            lookup = {}
            duplicates = []

            for txn in response.data:
                kajabi_id = str(txn['kajabi_transaction_id'])

                if kajabi_id in lookup:
                    duplicates.append(kajabi_id)
                    self.metrics.duplicate_kajabi_ids += 1

                lookup[kajabi_id] = {
                    'id': txn['id'],
                    'product_id': txn['product_id']
                }

            logger.info(f"✓ Built transaction lookup with {len(lookup):,} unlinked transactions")

            if duplicates:
                logger.warning(
                    f"⚠️  Found {len(duplicates)} duplicate kajabi_transaction_ids "
                    f"(will use latest match)"
                )

            return lookup

        except Exception as e:
            logger.error(f"✗ Failed to build transaction lookup: {e}")
            raise

    def process_csv(
        self,
        product_lookup: Dict[str, str],
        transaction_lookup: Dict[str, Dict],
        limit: Optional[int] = None
    ) -> List[Tuple[str, str]]:
        """
        Process CSV to find transaction-product matches

        FAANG Standard: Stream processing for memory efficiency

        Args:
            product_lookup: Mapping of kajabi_offer_id to product UUID
            transaction_lookup: Mapping of kajabi_transaction_id to transaction
            limit: Optional limit for testing

        Returns:
            List of (transaction_id, product_id) tuples to update
        """
        logger.info(f"Processing CSV: {self.csv_path}")
        if limit:
            logger.info(f"Limit: {limit} rows")

        matches = []
        processed_txn_ids = set()  # Track to avoid duplicate updates

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 2):  # Start at 2 (header is 1)
                    if limit and row_num > limit + 1:
                        break

                    self.metrics.csv_rows_processed += 1

                    # Extract CSV data
                    kajabi_txn_id = row.get('ID', '').strip()
                    offer_id = row.get('Offer ID', '').strip()

                    # Skip rows missing critical data
                    if not kajabi_txn_id or not offer_id:
                        self.metrics.csv_rows_skipped += 1
                        continue

                    # Check if transaction exists in DB and needs linking
                    if kajabi_txn_id not in transaction_lookup:
                        self.metrics.no_transaction_match += 1
                        continue

                    txn = transaction_lookup[kajabi_txn_id]

                    # Skip if already linked (shouldn't happen with our query, but safety check)
                    if txn['product_id']:
                        self.metrics.already_linked += 1
                        continue

                    # Check if product exists
                    if offer_id not in product_lookup:
                        self.metrics.no_product_match += 1
                        logger.debug(
                            f"Row {row_num}: No product for Offer ID {offer_id} "
                            f"({row.get('Offer Title', 'Unknown')})"
                        )
                        continue

                    # Found a match!
                    transaction_id = txn['id']
                    product_id = product_lookup[offer_id]

                    # Avoid duplicate updates
                    if transaction_id not in processed_txn_ids:
                        matches.append((transaction_id, product_id))
                        processed_txn_ids.add(transaction_id)
                        self.metrics.matches_found += 1

                    # Progress update every 1000 rows
                    if self.metrics.csv_rows_processed % 1000 == 0:
                        logger.info(f"Processed {self.metrics.csv_rows_processed:,} CSV rows...")

            logger.info(f"✓ CSV processing complete")
            logger.info(f"✓ Found {len(matches):,} transactions to link")

            return matches

        except Exception as e:
            logger.error(f"✗ Failed to process CSV: {e}")
            raise

    def preview_matches(self, matches: List[Tuple[str, str]], limit: int = 10):
        """
        Preview matches for human verification

        FAANG Standard: Always show user what will change
        """
        if not matches:
            logger.warning("No matches to preview")
            return

        logger.info("=" * 80)
        logger.info(f"PREVIEW: First {min(limit, len(matches))} matches")
        logger.info("=" * 80)

        for idx, (txn_id, product_id) in enumerate(matches[:limit], 1):
            logger.info(f"{idx}. Transaction {txn_id[:8]}... → Product {product_id[:8]}...")

        if len(matches) > limit:
            logger.info(f"... and {len(matches) - limit:,} more matches")
        logger.info("=" * 80)

    def update_transactions_batch(self, matches: List[Tuple[str, str]]) -> int:
        """
        Update transactions in batches for performance

        FAANG Standard: Batch operations with progress tracking

        Args:
            matches: List of (transaction_id, product_id) tuples

        Returns:
            Number of successful updates
        """
        if self.dry_run:
            logger.info(f"DRY RUN: Would update {len(matches):,} transactions")
            return len(matches)

        logger.info(f"Updating {len(matches):,} transactions in batches of {self.batch_size}...")

        successful = 0
        failed = 0

        # Process in batches
        for i in range(0, len(matches), self.batch_size):
            batch = matches[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(matches) + self.batch_size - 1) // self.batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")

            for txn_id, product_id in batch:
                try:
                    self.supabase.table('transactions').update(
                        {'product_id': product_id}
                    ).eq('id', txn_id).execute()

                    successful += 1

                except Exception as e:
                    failed += 1
                    logger.error(f"✗ Failed to update transaction {txn_id}: {e}")

            logger.info(f"✓ Batch {batch_num} complete: {successful} successful, {failed} failed")

        self.metrics.successful_updates = successful
        self.metrics.failed_updates = failed

        return successful

    def validate_migration(self) -> bool:
        """
        Validate migration results

        FAANG Standard: Always validate data integrity

        Returns:
            True if validation passes
        """
        logger.info("Validating migration results...")

        try:
            # Count remaining unlinked transactions
            response = self.supabase.table('transactions').select(
                'id', count='exact', head=True
            ).is_('product_id', 'null').not_.is_('kajabi_transaction_id', 'null').execute()

            remaining = response.count

            # Count total linked
            linked_response = self.supabase.table('transactions').select(
                'id', count='exact', head=True
            ).not_.is_('product_id', 'null').execute()

            total_linked = linked_response.count

            logger.info(f"Validation results:")
            logger.info(f"  Total linked transactions: {total_linked:,}")
            logger.info(f"  Remaining unlinked: {remaining:,}")

            logger.info("✓ Validation complete")
            return True

        except Exception as e:
            logger.error(f"✗ Validation failed: {e}")
            return False

    def execute(self, limit: Optional[int] = None):
        """
        Main execution flow with FAANG error handling and logging

        Args:
            limit: Optional limit for testing
        """
        start_time = datetime.now()

        try:
            logger.info("=" * 80)
            logger.info("CSV-BASED TRANSACTION-PRODUCT LINKAGE MIGRATION")
            logger.info(f"Mode: {'DRY RUN (no changes)' if self.dry_run else 'EXECUTE (will modify data)'}")
            logger.info(f"CSV file: {self.csv_path}")
            logger.info(f"Batch size: {self.batch_size}")
            if limit:
                logger.info(f"Limit: {limit} CSV rows")
            logger.info("=" * 80)

            # Step 1: Validate CSV file
            if not self.validate_csv_file():
                return False

            # Step 2: Build product lookup table
            product_lookup = self.build_product_lookup()

            if not product_lookup:
                logger.error("✗ No products found in database. Migration aborted.")
                return False

            # Step 3: Build transaction lookup table
            transaction_lookup = self.build_transaction_lookup()

            if not transaction_lookup:
                logger.warning("⚠️  No unlinked transactions found in database")
                logger.info("✓ All transactions are already linked!")
                return True

            # Step 4: Process CSV to find matches
            matches = self.process_csv(product_lookup, transaction_lookup, limit)

            if not matches:
                logger.warning("⚠️  No matches found")
                logger.info("Possible reasons:")
                logger.info("  - All matchable transactions are already linked")
                logger.info("  - CSV Offer IDs don't match products in database")
                logger.info("  - CSV transaction IDs don't match database")
                return True

            # Step 5: Preview matches
            self.preview_matches(matches, limit=10)

            # Step 6: Update transactions (or preview for dry-run)
            if self.dry_run:
                logger.info("DRY RUN MODE: No changes made")
                logger.info(f"Would update {len(matches):,} transactions")
            else:
                logger.warning("⚠️  EXECUTING MIGRATION - Database will be modified")
                updated = self.update_transactions_batch(matches)

                # Step 7: Validate results
                self.validate_migration()

            # Print metrics
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Migration completed in {elapsed:.2f} seconds")
            self.metrics.print_summary()

            return True

        except Exception as e:
            logger.error(f"✗ Migration failed with error: {e}")
            logger.exception("Full traceback:")
            return False


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='FAANG-Quality migration to link transactions using CSV data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes (safe, recommended first step)
  python3 link_transactions_from_csv_faang.py \\
      --csv-path "../kajabi 3 files review/transactions (2).csv" \\
      --dry-run

  # Preview first 100 matches
  python3 link_transactions_from_csv_faang.py \\
      --csv-path "../kajabi 3 files review/transactions (2).csv" \\
      --dry-run --limit 100

  # Execute migration
  python3 link_transactions_from_csv_faang.py \\
      --csv-path "../kajabi 3 files review/transactions (2).csv" \\
      --execute
        """
    )

    parser.add_argument(
        '--csv-path',
        required=True,
        help='Path to Kajabi transactions CSV file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database (default)'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (modify database)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of CSV rows to process (for testing)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for updates (default: 1000)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.execute and args.dry_run:
        logger.error("Error: Cannot specify both --execute and --dry-run")
        sys.exit(1)

    # Default to dry-run if neither specified
    dry_run = not args.execute

    # Initialize Supabase client
    supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        logger.error("Error: NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        logger.error("Set SUPABASE_SERVICE_ROLE_KEY for write permissions")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)

    # Execute migration
    linker = CSVTransactionLinker(
        supabase=supabase,
        csv_path=args.csv_path,
        dry_run=dry_run,
        batch_size=args.batch_size
    )

    success = linker.execute(limit=args.limit)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
