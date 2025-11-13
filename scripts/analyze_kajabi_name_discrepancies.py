#!/usr/bin/env python3
"""
FAANG-Quality Name Discrepancy Analysis for Email Compliance

Purpose: Identify contacts where Kajabi's full name differs from our database
         to ensure email compliance with accurate contact information.

Email Compliance Issue:
- Kajabi has: "Lynn Amber Ryan"
- Our DB has: "Lynn Ryan"
- Missing: "Amber" (middle name)

This script:
1. Parses latest Kajabi export (11102025kajabi.csv)
2. Compares Kajabi full names with database first_name + last_name
3. Identifies discrepancies (middle names, multi-word first names, etc.)
4. Generates fix plan with proper name parsing
5. Creates dry-run and execution modes

Standards: FAANG-quality with safety features
"""

import csv
import os
import sys
from supabase import create_client, Client
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime

# Supabase connection
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)

supabase: Client = create_client(url, key)

# File paths
KAJABI_CSV = "/workspaces/starhouse-database-v2/kajabi 3 files review/11102025kajabi.csv"
REPORT_FILE = f"/workspaces/starhouse-database-v2/name_discrepancy_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def parse_kajabi_export() -> Dict[str, Dict]:
    """
    Parse Kajabi CSV export and extract name fields.

    Returns:
        Dict[email, {full_name, first_name, last_name, kajabi_id}]
    """
    print("\n" + "=" * 80)
    print("PARSING KAJABI EXPORT")
    print("=" * 80)

    contacts = {}

    with open(KAJABI_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = row['Email'].strip().lower()
            if not email:
                continue

            full_name = row['Name'].strip()  # Column 1: "Lynn Amber Ryan"
            first_name = row['First Name'].strip()  # Column 2: "Lynn"
            last_name = row['Last Name'].strip()  # Column 3: "Ryan"
            kajabi_id = row['ID'].strip()

            contacts[email] = {
                'full_name': full_name,
                'first_name': first_name,
                'last_name': last_name,
                'kajabi_id': kajabi_id,
                'name_custom_field': row.get('Name (name)', '').strip()  # Column 15
            }

    print(f"✓ Parsed {len(contacts)} contacts from Kajabi export")
    return contacts

def fetch_database_contacts() -> Dict[str, Dict]:
    """
    Fetch all contacts from database with name fields.

    Returns:
        Dict[email, {id, first_name, last_name, additional_name, kajabi_id}]
    """
    print("\n" + "=" * 80)
    print("FETCHING DATABASE CONTACTS")
    print("=" * 80)

    response = supabase.table('contacts')\
        .select('id, email, first_name, last_name, additional_name, kajabi_id')\
        .is_('deleted_at', 'null')\
        .not_.is_('kajabi_id', 'null')\
        .execute()

    contacts = {}
    for row in response.data:
        email = row['email'].strip().lower() if row['email'] else ''
        if not email:
            continue

        contacts[email] = {
            'id': row['id'],
            'first_name': row.get('first_name', '') or '',
            'last_name': row.get('last_name', '') or '',
            'additional_name': row.get('additional_name', '') or '',
            'kajabi_id': row.get('kajabi_id', '') or ''
        }

    print(f"✓ Fetched {len(contacts)} Kajabi contacts from database")
    return contacts

def analyze_name_discrepancies(kajabi_contacts: Dict, db_contacts: Dict) -> List[Dict]:
    """
    Compare Kajabi full names with database names and identify discrepancies.

    Returns:
        List of discrepancies with analysis and proposed fixes
    """
    print("\n" + "=" * 80)
    print("ANALYZING NAME DISCREPANCIES")
    print("=" * 80)

    discrepancies = []

    for email, kajabi in kajabi_contacts.items():
        if email not in db_contacts:
            continue  # Contact not in database yet

        db = db_contacts[email]

        # Construct what we have in database
        db_full_name = f"{db['first_name']} {db['last_name']}".strip()
        kajabi_full_name = kajabi['full_name']

        # Check if names match
        if db_full_name.lower() == kajabi_full_name.lower():
            continue  # Perfect match

        # Check if it's just a simple concatenation issue
        if f"{kajabi['first_name']} {kajabi['last_name']}".strip().lower() == db_full_name.lower():
            continue  # Matches Kajabi's first + last

        # We have a discrepancy!
        # Analyze what's different
        analysis = analyze_name_difference(kajabi_full_name, kajabi['first_name'],
                                          kajabi['last_name'], db)

        discrepancy = {
            'email': email,
            'kajabi_id': kajabi['kajabi_id'],
            'db_id': db['id'],
            'kajabi_full_name': kajabi_full_name,
            'kajabi_first_name': kajabi['first_name'],
            'kajabi_last_name': kajabi['last_name'],
            'db_first_name': db['first_name'],
            'db_last_name': db['last_name'],
            'db_additional_name': db['additional_name'],
            'db_full_name': db_full_name,
            'analysis': analysis,
            'proposed_fix': None  # Will be set below
        }

        # Propose a fix
        discrepancy['proposed_fix'] = propose_fix(discrepancy)

        discrepancies.append(discrepancy)

    print(f"\n✓ Found {len(discrepancies)} name discrepancies")
    return discrepancies

def analyze_name_difference(full_name: str, first_name: str, last_name: str, db: Dict) -> Dict:
    """
    Analyze what's different between Kajabi and database names.

    Returns:
        Dict with analysis details
    """
    # Split full name into parts
    parts = full_name.split()

    analysis = {
        'type': 'unknown',
        'missing_words': [],
        'extra_words': [],
        'notes': []
    }

    # Check if full name has more words than first + last
    expected_word_count = len(first_name.split()) + len(last_name.split())
    actual_word_count = len(parts)

    if actual_word_count > expected_word_count:
        analysis['type'] = 'middle_name_or_multi_word'

        # Try to find what's missing
        first_parts = first_name.split()
        last_parts = last_name.split()

        # Check if there are words in full_name not in first_name or last_name
        for part in parts:
            if part.lower() not in first_name.lower() and part.lower() not in last_name.lower():
                analysis['missing_words'].append(part)

        if len(analysis['missing_words']) > 0:
            analysis['notes'].append(f"Full name contains: {', '.join(analysis['missing_words'])}")

    # Check if first name in full name matches first name field
    if not full_name.lower().startswith(first_name.lower()):
        analysis['type'] = 'different_first_name'
        analysis['notes'].append(f"Full name doesn't start with first name")

    # Check database state
    if db['first_name'] != first_name:
        analysis['notes'].append(f"DB first name differs from Kajabi: '{db['first_name']}' vs '{first_name}'")

    if db['last_name'] != last_name:
        analysis['notes'].append(f"DB last name differs from Kajabi: '{db['last_name']}' vs '{last_name}'")

    return analysis

def propose_fix(discrepancy: Dict) -> Dict:
    """
    Propose a fix for the name discrepancy.

    Strategy:
    1. If full name has middle word(s), extract and set additional_name
    2. Update first_name and last_name to match Kajabi
    3. Preserve any existing additional_name that's valuable

    Returns:
        Dict with proposed updates
    """
    kajabi_full = discrepancy['kajabi_full_name']
    kajabi_first = discrepancy['kajabi_first_name']
    kajabi_last = discrepancy['kajabi_last_name']

    parts = kajabi_full.split()

    fix = {
        'update_first_name': None,
        'update_last_name': None,
        'update_additional_name': None,
        'reasoning': ''
    }

    # Case 1: Full name is "First Middle Last"
    if len(parts) == 3:
        first = parts[0]
        middle = parts[1]
        last = parts[2]

        fix['update_first_name'] = first
        fix['update_last_name'] = last
        fix['update_additional_name'] = middle
        fix['reasoning'] = f"Full name '{kajabi_full}' appears to be First Middle Last. Setting additional_name='{middle}'"

    # Case 2: Full name is "First Middle1 Middle2 Last"
    elif len(parts) > 3:
        first = parts[0]
        last = parts[-1]
        middles = ' '.join(parts[1:-1])

        fix['update_first_name'] = first
        fix['update_last_name'] = last
        fix['update_additional_name'] = middles
        fix['reasoning'] = f"Full name '{kajabi_full}' has multiple middle names/words. Setting additional_name='{middles}'"

    # Case 3: Full name is "First Last" but DB has different values
    elif len(parts) == 2:
        fix['update_first_name'] = kajabi_first
        fix['update_last_name'] = kajabi_last
        fix['reasoning'] = f"Updating to match Kajabi: first_name='{kajabi_first}', last_name='{kajabi_last}'"

    # Don't override existing additional_name if it's a business name
    current_additional = discrepancy['db_additional_name']
    if current_additional and ('LLC' in current_additional or 'Inc' in current_additional or
                               'Productions' in current_additional or 'Corp' in current_additional):
        fix['update_additional_name'] = None
        fix['reasoning'] += f" (Preserving business name in additional_name: '{current_additional}')"

    return fix

def generate_report(discrepancies: List[Dict]) -> None:
    """Generate comprehensive JSON report."""
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_discrepancies': len(discrepancies),
        'summary': {
            'critical': 0,
            'needs_middle_name': 0,
            'needs_update': 0
        },
        'discrepancies': discrepancies
    }

    # Categorize
    for d in discrepancies:
        if d['analysis']['type'] == 'middle_name_or_multi_word':
            report['summary']['needs_middle_name'] += 1

        if d['proposed_fix']['update_first_name'] or d['proposed_fix']['update_last_name']:
            report['summary']['needs_update'] += 1

    # Write report
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Report saved to: {REPORT_FILE}")

def print_summary(discrepancies: List[Dict]) -> None:
    """Print human-readable summary."""
    print("\n" + "=" * 80)
    print("SUMMARY OF NAME DISCREPANCIES")
    print("=" * 80)

    if len(discrepancies) == 0:
        print("\n✅ No name discrepancies found! All contacts match Kajabi.")
        return

    print(f"\nTotal discrepancies: {len(discrepancies)}")

    # Group by type
    by_type = {}
    for d in discrepancies:
        dtype = d['analysis']['type']
        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(d)

    for dtype, items in by_type.items():
        print(f"\n{dtype}: {len(items)} contacts")

    # Show examples
    print("\n" + "-" * 80)
    print("EXAMPLES:")
    print("-" * 80)

    for i, d in enumerate(discrepancies[:5]):  # Show first 5
        print(f"\n{i+1}. {d['email']}")
        print(f"   Kajabi Full Name: {d['kajabi_full_name']}")
        print(f"   DB Full Name:     {d['db_full_name']}")
        print(f"   Type: {d['analysis']['type']}")
        if d['analysis']['missing_words']:
            print(f"   Missing: {', '.join(d['analysis']['missing_words'])}")
        print(f"   Proposed Fix: {d['proposed_fix']['reasoning']}")

    if len(discrepancies) > 5:
        print(f"\n   ... and {len(discrepancies) - 5} more (see JSON report)")

    # Lynn Amber Ryan specific
    lynn = next((d for d in discrepancies if 'amber@the360emergence' in d['email']), None)
    if lynn:
        print("\n" + "=" * 80)
        print("LYNN AMBER RYAN - SPECIFIC ANALYSIS")
        print("=" * 80)
        print(f"Kajabi Full Name: {lynn['kajabi_full_name']}")
        print(f"DB Full Name:     {lynn['db_full_name']}")
        print(f"Missing:          {', '.join(lynn['analysis']['missing_words'])}")
        print(f"\nProposed Fix:")
        if lynn['proposed_fix']['update_first_name']:
            print(f"  first_name: '{lynn['db_first_name']}' → '{lynn['proposed_fix']['update_first_name']}'")
        if lynn['proposed_fix']['update_last_name']:
            print(f"  last_name: '{lynn['db_last_name']}' → '{lynn['proposed_fix']['update_last_name']}'")
        if lynn['proposed_fix']['update_additional_name']:
            print(f"  additional_name: '{lynn['db_additional_name']}' → '{lynn['proposed_fix']['update_additional_name']}'")
        print(f"\nReasoning: {lynn['proposed_fix']['reasoning']}")

def main():
    """Main execution."""
    print("=" * 80)
    print("KAJABI NAME DISCREPANCY ANALYSIS FOR EMAIL COMPLIANCE")
    print("=" * 80)
    print("\nPurpose: Ensure database names match Kajabi for email compliance")
    print("Standard: FAANG-quality analysis with comprehensive reporting")

    # Step 1: Parse Kajabi export
    kajabi_contacts = parse_kajabi_export()

    # Step 2: Fetch database contacts
    db_contacts = fetch_database_contacts()

    # Step 3: Analyze discrepancies
    discrepancies = analyze_name_discrepancies(kajabi_contacts, db_contacts)

    # Step 4: Generate report
    generate_report(discrepancies)

    # Step 5: Print summary
    print_summary(discrepancies)

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"1. Review the JSON report: {REPORT_FILE}")
    print("2. Run the fix script with --dry-run to see proposed changes")
    print("3. Execute the fix script to update database")
    print("\nCommand: python3 scripts/fix_kajabi_name_discrepancies.py --dry-run")

if __name__ == '__main__':
    main()
