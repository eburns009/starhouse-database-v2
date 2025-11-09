#!/usr/bin/env python3
"""
WEEKLY DATA IMPORT - MASTER ORCHESTRATOR
==========================================

Purpose: Run all weekly imports in the correct order

This script orchestrates:
  1. Kajabi subscriptions import
  2. PayPal transactions import
  3. (Future: Ticket Tailor events)

Usage:
  # Dry-run all imports (recommended first)
  python3 scripts/weekly_import_all.py --dry-run

  # Execute all imports
  python3 scripts/weekly_import_all.py --execute

  # Custom file paths
  python3 scripts/weekly_import_all.py \\
    --kajabi data/kajabi_subs_2025_11_08.csv \\
    --paypal data/paypal_export_2025_11_08.txt \\
    --execute

Required Files:
  - Kajabi subscriptions CSV (default: data/kajabi_subscriptions.csv)
  - PayPal transactions TXT (default: data/paypal_export.txt)

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

DEFAULT_KAJABI_FILE = 'data/kajabi_subscriptions.csv'
DEFAULT_PAYPAL_FILE = 'data/paypal_export.txt'

SCRIPTS_DIR = 'scripts'
KAJABI_SCRIPT = f'{SCRIPTS_DIR}/weekly_import_kajabi.py'
PAYPAL_SCRIPT = f'{SCRIPTS_DIR}/weekly_import_paypal.py'

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

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Weekly Data Import - Master Orchestrator'
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without committing (recommended first)')
    parser.add_argument('--execute', action='store_true',
                       help='Execute imports (make changes to database)')
    parser.add_argument('--kajabi', default=DEFAULT_KAJABI_FILE,
                       help=f'Path to Kajabi subscriptions CSV (default: {DEFAULT_KAJABI_FILE})')
    parser.add_argument('--paypal', default=DEFAULT_PAYPAL_FILE,
                       help=f'Path to PayPal transactions TXT (default: {DEFAULT_PAYPAL_FILE})')
    parser.add_argument('--skip-kajabi', action='store_true',
                       help='Skip Kajabi import')
    parser.add_argument('--skip-paypal', action='store_true',
                       help='Skip PayPal import')

    args = parser.parse_args()

    # Validate run mode
    if not args.dry_run and not args.execute:
        print("❌ Error: Must specify either --dry-run or --execute")
        print("\nExamples:")
        print("  python3 scripts/weekly_import_all.py --dry-run")
        print("  python3 scripts/weekly_import_all.py --execute")
        sys.exit(1)

    # Determine mode
    mode = '--dry-run' if args.dry_run else '--execute'
    mode_label = 'DRY RUN' if args.dry_run else 'EXECUTE'

    # Print header
    print_header(f"WEEKLY DATA IMPORT - {mode_label} MODE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {mode_label}")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be saved")
        print("Run with --execute to apply changes\n")

    results = {}

    # ========================================================================
    # PRE-FLIGHT: Check all files exist
    # ========================================================================

    print_header("PRE-FLIGHT: Checking Files")

    all_files_ok = True

    if not args.skip_kajabi:
        if not check_file_exists(args.kajabi, "Kajabi subscriptions file"):
            all_files_ok = False

    if not args.skip_paypal:
        if not check_file_exists(args.paypal, "PayPal transactions file"):
            all_files_ok = False

    if not all_files_ok:
        print("\n❌ Missing required files. Please export data first.")
        print("See docs/runbooks/WEEKLY_IMPORT_GUIDE.md for export instructions.")
        sys.exit(1)

    print("\n✅ All files present")

    # ========================================================================
    # STEP 1: Import Kajabi Subscriptions
    # ========================================================================

    if not args.skip_kajabi:
        print_header("STEP 1: Importing Kajabi Subscriptions")

        kajabi_args = [
            mode,
            '--subscriptions', args.kajabi
        ]

        success = run_import_script(KAJABI_SCRIPT, kajabi_args)
        results['kajabi'] = 'SUCCESS' if success else 'FAILED'

        if not success:
            print("\n⚠️  Kajabi import failed. Check errors above.")
            if not args.dry_run:
                response = input("\nContinue with PayPal import? (y/N): ")
                if response.lower() != 'y':
                    print("\nImport aborted.")
                    sys.exit(1)
    else:
        print_header("STEP 1: Skipping Kajabi Import (--skip-kajabi)")
        results['kajabi'] = 'SKIPPED'

    # ========================================================================
    # STEP 2: Import PayPal Transactions
    # ========================================================================

    if not args.skip_paypal:
        print_header("STEP 2: Importing PayPal Transactions")

        paypal_args = [
            mode,
            '--file', args.paypal
        ]

        success = run_import_script(PAYPAL_SCRIPT, paypal_args)
        results['paypal'] = 'SUCCESS' if success else 'FAILED'

        if not success:
            print("\n⚠️  PayPal import failed. Check errors above.")
    else:
        print_header("STEP 2: Skipping PayPal Import (--skip-paypal)")
        results['paypal'] = 'SKIPPED'

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print_header("IMPORT COMPLETE")

    print("Results:")
    for source, result in results.items():
        icon = '✅' if result == 'SUCCESS' else '⚠️' if result == 'SKIPPED' else '❌'
        print(f"  {icon} {source.upper()}: {result}")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.dry_run:
        print("\n🔄 DRY RUN COMPLETE - No changes were saved")
        print("Run with --execute to apply changes")
    else:
        print("\n✅ IMPORT COMPLETE - Changes saved to database")

    # Exit with error code if any imports failed
    if 'FAILED' in results.values():
        sys.exit(1)

if __name__ == '__main__':
    main()
