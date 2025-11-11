#!/usr/bin/env python3
"""
EXPORT CORRECTED ADDRESSES FOR KAJABI UPDATE
=============================================

Exports all contacts with addresses that were corrected during the Nov 10 cleanup.
This data can be used to update the Kajabi system with correct address information.

Features:
- Exports contacts modified on Nov 10, 2025
- Includes before/after comparison (from backup files)
- CSV format for easy import to Kajabi
- Type hints and error handling

Usage:
  python3 scripts/export_corrected_addresses.py --output data/corrected_addresses_for_kajabi.csv
"""

import csv
import os
import sys
import json
import argparse
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONNECTION = get_database_url()
BACKUP_DIR = Path('/workspaces/starhouse-database-v2/backups/address_fixes')

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def load_backup_data() -> Dict[str, Dict]:
    """
    Load original data from backup files.

    Returns:
        Dictionary mapping contact_id to original contact data
    """
    backup_data = {}

    backup_files = list(BACKUP_DIR.glob('backup_*.json'))

    print(f"📦 Loading backup files from {BACKUP_DIR}")

    for backup_file in backup_files:
        print(f"  Reading: {backup_file.name}")
        with open(backup_file, 'r') as f:
            data = json.load(f)
            for contact in data['contacts']:
                contact_id = contact['id']
                backup_data[contact_id] = contact

    print(f"  Loaded: {len(backup_data)} contact backups\n")

    return backup_data

def export_corrected_addresses(output_file: str) -> None:
    """
    Export corrected addresses from database.

    Args:
        output_file: Path to output CSV file
    """
    print("=" * 80)
    print("EXPORT CORRECTED ADDRESSES FOR KAJABI")
    print("=" * 80)
    print()

    # Load backup data
    backup_data = load_backup_data()

    # Connect to database
    print("📡 Connecting to database...")
    conn = psycopg2.connect(DB_CONNECTION)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Connected\n")

    try:
        # Get contacts modified on Nov 10, 2025
        print("🔍 Querying corrected contacts...")
        cur.execute("""
            SELECT
                id,
                email,
                first_name,
                last_name,
                address_line_1,
                address_line_2,
                city,
                state,
                postal_code,
                country,
                kajabi_id,
                kajabi_member_id,
                phone,
                updated_at,
                created_at
            FROM contacts
            WHERE DATE(updated_at) = '2025-11-10'
              AND address_line_1 IS NOT NULL
            ORDER BY email
        """)

        contacts = cur.fetchall()
        print(f"  Found: {len(contacts)} corrected contacts\n")

        # Export to CSV
        print(f"📝 Writing to: {output_file}")

        fieldnames = [
            'email',
            'first_name',
            'last_name',
            'kajabi_id',
            'kajabi_member_id',
            'phone',
            # Original address (before correction)
            'original_address_line_1',
            'original_address_line_2',
            'original_city',
            # Corrected address (current)
            'corrected_address_line_1',
            'corrected_address_line_2',
            'corrected_city',
            # Other fields
            'state',
            'postal_code',
            'country',
            'updated_at',
            # Correction type
            'correction_type'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for contact in contacts:
                contact_id = str(contact['id'])

                # Get original data from backup
                original = backup_data.get(contact_id, {})

                # Determine correction type
                correction_type = []
                if original:
                    if original.get('city') is None and contact['city'] is not None:
                        correction_type.append('city_placement')
                    if original.get('address_line_1') == original.get('address_line_2'):
                        correction_type.append('duplicate_removed')
                    if (original.get('address_line_1') and len(original.get('address_line_1', '')) < 10 and
                        original.get('address_line_2') and len(original.get('address_line_2', '')) > 10):
                        correction_type.append('field_reversal')

                row = {
                    'email': contact['email'],
                    'first_name': contact['first_name'] or '',
                    'last_name': contact['last_name'] or '',
                    'kajabi_id': contact['kajabi_id'] or '',
                    'kajabi_member_id': contact['kajabi_member_id'] or '',
                    'phone': contact['phone'] or '',
                    # Original
                    'original_address_line_1': original.get('address_line_1') or '',
                    'original_address_line_2': original.get('address_line_2') or '',
                    'original_city': original.get('city') or '',
                    # Corrected
                    'corrected_address_line_1': contact['address_line_1'] or '',
                    'corrected_address_line_2': contact['address_line_2'] or '',
                    'corrected_city': contact['city'] or '',
                    # Other
                    'state': contact['state'] or '',
                    'postal_code': contact['postal_code'] or '',
                    'country': contact['country'] or '',
                    'updated_at': str(contact['updated_at']),
                    'correction_type': ', '.join(correction_type) if correction_type else 'updated'
                }

                writer.writerow(row)

        print(f"✅ Exported: {len(contacts)} contacts\n")

        # Summary
        print("📊 Correction Type Summary:")
        correction_counts = {}
        for contact in contacts:
            contact_id = str(contact['id'])
            original = backup_data.get(contact_id, {})

            if original:
                if original.get('city') is None and contact['city'] is not None:
                    correction_counts['city_placement'] = correction_counts.get('city_placement', 0) + 1
                if original.get('address_line_1') == original.get('address_line_2'):
                    correction_counts['duplicate_removed'] = correction_counts.get('duplicate_removed', 0) + 1
                if (original.get('address_line_1') and len(original.get('address_line_1', '')) < 10 and
                    original.get('address_line_2') and len(original.get('address_line_2', '')) > 10):
                    correction_counts['field_reversal'] = correction_counts.get('field_reversal', 0) + 1

        for correction_type, count in correction_counts.items():
            print(f"  {correction_type}: {count}")

        print()
        print("=" * 80)
        print("EXPORT COMPLETE")
        print("=" * 80)
        print()
        print(f"📄 File: {output_file}")
        print(f"📊 Records: {len(contacts)}")
        print()
        print("Next Steps:")
        print("1. Review the exported CSV file")
        print("2. Import to Kajabi to update address data")
        print("3. Re-export clean CSV from Kajabi")
        print("4. Run weekly_import_kajabi_v2.py with clean data")

    finally:
        cur.close()
        conn.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Export corrected addresses for Kajabi update',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--output',
        default='data/corrected_addresses_for_kajabi.csv',
        help='Output CSV file path (default: data/corrected_addresses_for_kajabi.csv)'
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        export_corrected_addresses(args.output)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
