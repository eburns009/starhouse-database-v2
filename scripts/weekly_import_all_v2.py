#!/usr/bin/env python3
"""
WEEKLY DATA IMPORT V2 - MASTER ORCHESTRATOR
============================================

Purpose: Run all weekly imports in the correct order using comprehensive Kajabi v2 format

This script orchestrates:
  1. Kajabi v2 comprehensive import (7 CSV files: contacts, tags, products, subscriptions, etc.)
  2. PayPal transactions import
  3. (Future: Ticket Tailor events)

Usage:
  # Dry-run all imports (recommended first)
  python3 scripts/weekly_import_all_v2.py --dry-run

  # Execute all imports
  python3 scripts/weekly_import_all_v2.py --execute

  # Custom data directories
  python3 scripts/weekly_import_all_v2.py \\
    --kajabi-dir data/current \\
    --paypal-file data/current/paypal_export_2025_11_08.txt \\
    --execute

  # Skip specific imports
  python3 scripts/weekly_import_all_v2.py --skip-paypal --execute

Required Files:
  Kajabi v2 exports (7 CSV files in kajabi-dir):
    - v2_contacts.csv          (Contact information, email subscription status)
    - v2_tags.csv              (Tag definitions)
    - v2_contact_tags.csv      (Contact-tag relationships)
    - v2_products.csv          (Product/offer catalog)
    - v2_contact_products.csv  (Contact-product relationships / purchases)
    - v2_subscriptions.csv     (Subscriptions)
    - v2_transactions.csv      (Transactions)

  PayPal export:
    - paypal_export.txt        (Tab-delimited transaction export)

See WEEKLY_IMPORT_GUIDE.md for detailed export instructions.
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_KAJABI_DIR = 'data/current'
DEFAULT_PAYPAL_FILE = 'data/current/paypal_export.txt'

SCRIPTS_DIR = 'scripts'
KAJABI_V2_SCRIPT = f'{SCRIPTS_DIR}/weekly_import_kajabi_v2.py'
PAYPAL_SCRIPT = f'{SCRIPTS_DIR}/weekly_import_paypal.py'

# Required Kajabi v2 files
KAJABI_V2_FILES = [
    'v2_contacts.csv',
    'v2_tags.csv',
    'v2_contact_tags.csv',
    'v2_products.csv',
    'v2_contact_products.csv',
    'v2_subscriptions.csv',
    'v2_transactions.csv',
]

# ============================================================================
# HELPERS
# ============================================================================

def print_header(title: str):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def run_import_script(script_path: str, args: list) -> bool:
    """Run an import script and return success status"""
    try:
        result = subprocess.run(
            ['python3', script_path] + args,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Script failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running script: {e}")
        return False

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a required file exists"""
    if not os.path.exists(filepath):
        print(f"❌ {description} not found: {filepath}")
        return False
    file_size = os.path.getsize(filepath)
    print(f"✅ {description} found: {filepath} ({file_size:,} bytes)")
    return True

def check_kajabi_v2_files(data_dir: str) -> bool:
    """Check if all required Kajabi v2 files exist"""
    print("Checking Kajabi v2 files:")
    all_present = True
    for filename in KAJABI_V2_FILES:
        filepath = os.path.join(data_dir, filename)
        if not check_file_exists(filepath, f"  {filename}"):
            all_present = False
    return all_present

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Weekly Data Import V2 - Master Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--dry-run', action='store_true',
                       help='Preview changes without committing (recommended first)')
    mode_group.add_argument('--execute', action='store_true',
                       help='Execute imports (make changes to database)')

    # File/directory paths
    parser.add_argument('--kajabi-dir', default=DEFAULT_KAJABI_DIR,
                       help=f'Directory containing Kajabi v2 CSV files (default: {DEFAULT_KAJABI_DIR})')
    parser.add_argument('--paypal-file', default=DEFAULT_PAYPAL_FILE,
                       help=f'Path to PayPal export TXT file (default: {DEFAULT_PAYPAL_FILE})')

    # Skip options
    parser.add_argument('--skip-kajabi', action='store_true',
                       help='Skip Kajabi import')
    parser.add_argument('--skip-paypal', action='store_true',
                       help='Skip PayPal import')

    args = parser.parse_args()

    # Validate at least one import is enabled
    if args.skip_kajabi and args.skip_paypal:
        print("❌ Error: Cannot skip all imports. At least one must be enabled.")
        sys.exit(1)

    # Validate directories and files exist
    if not args.skip_kajabi:
        if not os.path.isdir(args.kajabi_dir):
            print(f"❌ Error: Kajabi directory not found: {args.kajabi_dir}")
            sys.exit(1)

    # Print banner
    print_header("WEEKLY DATA IMPORT - V2 COMPREHENSIVE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print()

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be saved")
    else:
        print("🔴 EXECUTE MODE - Changes will be committed to database")

    print()

    # Pre-flight check
    print_header("PRE-FLIGHT: Checking Files")

    all_files_present = True

    if not args.skip_kajabi:
        if not check_kajabi_v2_files(args.kajabi_dir):
            all_files_present = False

    if not args.skip_paypal:
        if not check_file_exists(args.paypal_file, "PayPal transactions file"):
            all_files_present = False

    print()

    if not all_files_present:
        print("❌ Pre-flight check failed. Cannot continue.")
        print()
        print("Please ensure all required files are present:")
        print(f"  Kajabi v2: {args.kajabi_dir}/")
        for filename in KAJABI_V2_FILES:
            print(f"    - {filename}")
        if not args.skip_paypal:
            print(f"  PayPal: {args.paypal_file}")
        sys.exit(1)

    print("✅ All files present")

    # Track results
    results = {
        'kajabi': None,
        'paypal': None,
    }

    # ========================================================================
    # STEP 1: Import Kajabi V2 Data
    # ========================================================================

    if not args.skip_kajabi:
        print_header("STEP 1: Importing Kajabi V2 Data (7 CSV files)")

        kajabi_args = [
            '--data-dir', args.kajabi_dir,
            '--dry-run' if args.dry_run else '--execute'
        ]

        results['kajabi'] = run_import_script(KAJABI_V2_SCRIPT, kajabi_args)

        if not results['kajabi']:
            print("\n❌ Kajabi import FAILED")
            print("Aborting remaining imports.")
            sys.exit(1)
        else:
            print("\n✅ Kajabi import completed successfully")
    else:
        print_header("STEP 1: Skipping Kajabi Import")
        results['kajabi'] = 'skipped'

    # ========================================================================
    # STEP 2: Import PayPal Transactions
    # ========================================================================

    if not args.skip_paypal:
        print_header("STEP 2: Importing PayPal Transactions")

        paypal_args = [
            '--file', args.paypal_file,
            '--dry-run' if args.dry_run else '--execute'
        ]

        results['paypal'] = run_import_script(PAYPAL_SCRIPT, paypal_args)

        if not results['paypal']:
            print("\n❌ PayPal import FAILED")
            sys.exit(1)
        else:
            print("\n✅ PayPal import completed successfully")
    else:
        print_header("STEP 2: Skipping PayPal Import")
        results['paypal'] = 'skipped'

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print_header("IMPORT COMPLETE")

    print("Results:")
    if not args.skip_kajabi:
        status = "✅ SUCCESS" if results['kajabi'] == True else "❌ FAILED"
        print(f"  KAJABI V2: {status}")
    if not args.skip_paypal:
        status = "✅ SUCCESS" if results['paypal'] == True else "❌ FAILED"
        print(f"  PAYPAL:    {status}")

    print()
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if args.dry_run:
        print("🔄 DRY RUN COMPLETE - No changes were saved")
        print("Run with --execute to apply changes")
    else:
        print("✅ Changes committed to database")

    # Exit with appropriate code
    all_successful = all(r in [True, 'skipped'] for r in results.values())
    sys.exit(0 if all_successful else 1)

if __name__ == '__main__':
    main()
