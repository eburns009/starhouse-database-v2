#!/usr/bin/env python3
"""
SYSTEMATIC ADDRESS AUDIT - FAANG Quality
==========================================

Compare database addresses vs Kajabi CSV (source of truth) for ALL contacts
from the Dec 3, 2020 import to determine the scope of address data mixing.

This script will:
1. Load all contacts from Dec 3, 2020 from database
2. Load all contacts from Kajabi CSV
3. Compare addresses field-by-field
4. Report mismatches systematically
5. Determine if this is an import error or post-import scrambling

Usage:
  python3 scripts/systematic_address_audit.py
"""

import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONNECTION = get_database_url()
KAJABI_CSV = '/workspaces/starhouse-database-v2/kajabi 3 files review/kajabi contacts.csv'
OUTPUT_FILE = '/tmp/address_audit_report.json'

# ============================================================================
# LOAD DATA
# ============================================================================

def load_kajabi_contacts() -> Dict[str, Dict]:
    """Load all contacts from Kajabi CSV, keyed by email."""
    contacts = {}

    with open(KAJABI_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row['Email'].strip().lower()
            contacts[email] = {
                'name': row['Name'],
                'first_name': row['First Name'],
                'last_name': row['Last Name'],
                'address_line_1': row['Address (address_line_1)'].strip(),
                'address_line_2': row['Address Line 2 (address_line_2)'].strip(),
                'city': row['City (address_city)'].strip(),
                'state': row['State (address_state)'].strip(),
                'zip': row['Zip Code (address_zip)'].strip(),
                'country': row['Country (address_country)'].strip()
            }

    return contacts

def load_database_contacts() -> Dict[str, Dict]:
    """Load all contacts from Dec 3, 2020 from database."""
    conn = psycopg2.connect(DB_CONNECTION)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            email,
            first_name,
            last_name,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country,
            created_at,
            billing_address_updated_at,
            billing_address_source
        FROM contacts
        WHERE created_at::date = '2020-12-03'
        ORDER BY email
    """)

    contacts = {}
    for row in cur.fetchall():
        email = row['email'].strip().lower() if row['email'] else ''
        contacts[email] = {
            'first_name': row['first_name'] or '',
            'last_name': row['last_name'] or '',
            'address_line_1': row['address_line_1'] or '',
            'address_line_2': row['address_line_2'] or '',
            'city': row['city'] or '',
            'state': row['state'] or '',
            'zip': row['postal_code'] or '',
            'country': row['country'] or '',
            'created_at': str(row['created_at']),
            'billing_address_updated_at': str(row['billing_address_updated_at']) if row['billing_address_updated_at'] else None,
            'billing_address_source': row['billing_address_source'] or ''
        }

    cur.close()
    conn.close()

    return contacts

# ============================================================================
# COMPARISON
# ============================================================================

def normalize_address(addr: str) -> str:
    """Normalize address for comparison."""
    return addr.lower().strip().replace('  ', ' ')

def compare_addresses(db: Dict, kajabi: Dict, email: str) -> Tuple[bool, List[str]]:
    """
    Compare database address vs Kajabi address.

    Returns: (is_match, list_of_differences)
    """
    differences = []

    # Compare each field
    db_addr = normalize_address(db['address_line_1'])
    k_addr = normalize_address(kajabi['address_line_1'])

    if db_addr != k_addr and db_addr and k_addr:  # Both have addresses
        differences.append(f"address_line_1: DB='{db['address_line_1']}' vs Kajabi='{kajabi['address_line_1']}'")

    db_city = normalize_address(db['city'])
    k_city = normalize_address(kajabi['city'])

    if db_city != k_city and db_city and k_city:
        differences.append(f"city: DB='{db['city']}' vs Kajabi='{kajabi['city']}'")

    db_state = normalize_address(db['state'])
    k_state = normalize_address(kajabi['state'])

    if db_state != k_state and db_state and k_state:
        differences.append(f"state: DB='{db['state']}' vs Kajabi='{kajabi['state']}'")

    # Zip codes - compare base zip (ignore +4)
    db_zip_base = db['zip'].split('-')[0].strip()
    k_zip_base = kajabi['zip'].split('-')[0].strip()

    if db_zip_base != k_zip_base and db_zip_base and k_zip_base:
        differences.append(f"zip: DB='{db['zip']}' vs Kajabi='{kajabi['zip']}'")

    is_match = len(differences) == 0
    return is_match, differences

# ============================================================================
# MAIN AUDIT
# ============================================================================

def run_audit():
    """Run systematic address audit."""
    print("=" * 80)
    print("SYSTEMATIC ADDRESS AUDIT - Dec 3, 2020 Import")
    print("=" * 80)
    print()

    # Load data
    print("Loading Kajabi CSV...")
    kajabi_contacts = load_kajabi_contacts()
    print(f"  Loaded {len(kajabi_contacts)} contacts from Kajabi")

    print("Loading database contacts...")
    db_contacts = load_database_contacts()
    print(f"  Loaded {len(db_contacts)} contacts from database (Dec 3, 2020)")
    print()

    # Compare
    matches = []
    mismatches = []
    db_only = []
    kajabi_only = []

    # Check all database contacts
    for email, db_data in db_contacts.items():
        if email in kajabi_contacts:
            k_data = kajabi_contacts[email]
            is_match, differences = compare_addresses(db_data, k_data, email)

            if is_match:
                matches.append(email)
            else:
                mismatches.append({
                    'email': email,
                    'name': f"{db_data['first_name']} {db_data['last_name']}",
                    'differences': differences,
                    'db_address': f"{db_data['address_line_1']}, {db_data['city']}, {db_data['state']} {db_data['zip']}",
                    'kajabi_address': f"{k_data['address_line_1']}, {k_data['city']}, {k_data['state']} {k_data['zip']}",
                    'billing_address_source': db_data['billing_address_source'],
                    'billing_address_updated_at': db_data['billing_address_updated_at']
                })
        else:
            db_only.append(email)

    # Check Kajabi-only contacts
    for email in kajabi_contacts:
        if email not in db_contacts:
            kajabi_only.append(email)

    # ========================================================================
    # REPORT
    # ========================================================================

    print("=" * 80)
    print("AUDIT RESULTS")
    print("=" * 80)
    print(f"Total database contacts (Dec 3, 2020): {len(db_contacts)}")
    print(f"Total Kajabi contacts: {len(kajabi_contacts)}")
    print()
    print(f"✅ Matches (addresses identical): {len(matches)}")
    print(f"❌ Mismatches (addresses different): {len(mismatches)}")
    print(f"⚠️  In database but not Kajabi: {len(db_only)}")
    print(f"⚠️  In Kajabi but not database: {len(kajabi_only)}")
    print()

    if mismatches:
        print("=" * 80)
        print(f"ADDRESS MISMATCHES ({len(mismatches)} contacts)")
        print("=" * 80)

        for i, mismatch in enumerate(mismatches[:20], 1):  # Show first 20
            print(f"\n{i}. {mismatch['name']} ({mismatch['email']})")
            print(f"   Database:  {mismatch['db_address']}")
            print(f"   Kajabi:    {mismatch['kajabi_address']}")
            print(f"   Source: {mismatch['billing_address_source']}")
            print(f"   Last Updated: {mismatch['billing_address_updated_at']}")
            for diff in mismatch['differences']:
                print(f"   - {diff}")

        if len(mismatches) > 20:
            print(f"\n... and {len(mismatches) - 20} more mismatches")

    # Save full report
    report = {
        'audit_date': datetime.utcnow().isoformat(),
        'summary': {
            'total_db_contacts': len(db_contacts),
            'total_kajabi_contacts': len(kajabi_contacts),
            'matches': len(matches),
            'mismatches': len(mismatches),
            'db_only': len(db_only),
            'kajabi_only': len(kajabi_only)
        },
        'mismatches': mismatches,
        'db_only_emails': db_only,
        'kajabi_only_emails': kajabi_only
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    print()
    print("=" * 80)
    print(f"Full report saved to: {OUTPUT_FILE}")
    print("=" * 80)

    return report

if __name__ == '__main__':
    run_audit()
