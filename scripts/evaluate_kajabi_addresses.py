#!/usr/bin/env python3
"""
Evaluate Kajabi CSV addresses against corrected database addresses.
Identifies which Kajabi records need to be updated.
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def get_db_connection():
    """Get database connection from environment."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def load_kajabi_csv(csv_path: str) -> List[Dict]:
    """Load Kajabi CSV file."""
    print(f"Loading Kajabi CSV: {csv_path}")

    contacts = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract address fields
            contact = {
                'email': row.get('Email', '').strip().lower(),
                'name': row.get('Name', '').strip(),
                'kajabi_id': row.get('ID', '').strip(),
                'address_line_1': row.get('Address (address_line_1)', '').strip(),
                'address_line_2': row.get('Address Line 2 (address_line_2)', '').strip(),
                'city': row.get('City (address_city)', '').strip(),
                'state': row.get('State (address_state)', '').strip(),
                'country': row.get('Country (address_country)', '').strip(),
                'zip': row.get('Zip Code (address_zip)', '').strip(),
            }
            contacts.append(contact)

    print(f"Loaded {len(contacts)} contacts from Kajabi CSV")
    return contacts

def load_db_addresses(conn) -> Dict[str, Dict]:
    """Load corrected addresses from database, indexed by email."""
    print("Loading corrected addresses from database...")

    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("""
        SELECT
            email,
            first_name,
            last_name,
            address_line_1,
            address_line_2,
            city,
            state,
            country,
            postal_code
        FROM contacts
        WHERE email IS NOT NULL
        AND email != ''
        ORDER BY email
    """)

    db_addresses = {}
    for row in cursor:
        email = row['email'].strip().lower()

        # Construct full name
        first = row['first_name'] or ''
        last = row['last_name'] or ''
        full_name = f"{first} {last}".strip()

        db_addresses[email] = {
            'email': email,
            'name': full_name,
            'address_line_1': row['address_line_1'] or '',
            'address_line_2': row['address_line_2'] or '',
            'city': row['city'] or '',
            'state': row['state'] or '',
            'country': row['country'] or '',
            'zip': row['postal_code'] or '',
            'corrected_at': None,
            'correction_source': None
        }

    cursor.close()
    print(f"Loaded {len(db_addresses)} addresses from database")
    return db_addresses

def normalize_field(value: str) -> str:
    """Normalize field for comparison."""
    if not value:
        return ''
    return value.strip().lower()

def addresses_differ(kajabi: Dict, db: Dict) -> Tuple[bool, List[str]]:
    """
    Check if addresses differ between Kajabi and database.
    Returns (differs, list_of_differences)
    """
    differences = []

    fields = ['address_line_1', 'address_line_2', 'city', 'state', 'country', 'zip']

    for field in fields:
        kajabi_val = normalize_field(kajabi.get(field, ''))
        db_val = normalize_field(db.get(field, ''))

        if kajabi_val != db_val:
            differences.append(field)

    return len(differences) > 0, differences

def evaluate_addresses(kajabi_contacts: List[Dict], db_addresses: Dict[str, Dict]) -> Dict:
    """
    Compare Kajabi addresses with database addresses.
    Returns evaluation results.
    """
    print("\nEvaluating addresses...")

    results = {
        'matched': [],           # Email found, addresses match
        'needs_update': [],      # Email found, addresses differ
        'not_in_db': [],        # Email in Kajabi but not in database
        'not_in_kajabi': [],    # Email in database but not in Kajabi
        'no_address_kajabi': [], # In Kajabi but no address
        'no_address_db': []     # In DB but no address
    }

    kajabi_emails = set()

    for kajabi_contact in kajabi_contacts:
        email = kajabi_contact['email']
        kajabi_emails.add(email)

        if not email:
            continue

        # Check if email exists in database
        if email not in db_addresses:
            results['not_in_db'].append(kajabi_contact)
            continue

        db_contact = db_addresses[email]

        # Check if Kajabi has no address
        has_kajabi_address = any([
            kajabi_contact.get('address_line_1'),
            kajabi_contact.get('city'),
            kajabi_contact.get('state'),
            kajabi_contact.get('zip')
        ])

        # Check if DB has no address
        has_db_address = any([
            db_contact.get('address_line_1'),
            db_contact.get('city'),
            db_contact.get('state'),
            db_contact.get('zip')
        ])

        if not has_kajabi_address and not has_db_address:
            results['matched'].append({
                'kajabi': kajabi_contact,
                'db': db_contact,
                'differences': []
            })
            continue

        if not has_kajabi_address and has_db_address:
            results['no_address_kajabi'].append({
                'kajabi': kajabi_contact,
                'db': db_contact
            })
            continue

        if has_kajabi_address and not has_db_address:
            results['no_address_db'].append({
                'kajabi': kajabi_contact,
                'db': db_contact
            })
            continue

        # Compare addresses
        differs, differences = addresses_differ(kajabi_contact, db_contact)

        if differs:
            results['needs_update'].append({
                'kajabi': kajabi_contact,
                'db': db_contact,
                'differences': differences
            })
        else:
            results['matched'].append({
                'kajabi': kajabi_contact,
                'db': db_contact,
                'differences': []
            })

    # Find contacts in DB but not in Kajabi
    db_emails = set(db_addresses.keys())
    emails_not_in_kajabi = db_emails - kajabi_emails
    for email in emails_not_in_kajabi:
        results['not_in_kajabi'].append(db_addresses[email])

    return results

def print_evaluation_summary(results: Dict) -> None:
    """Print evaluation summary."""
    print("\n" + "="*80)
    print("KAJABI ADDRESS EVALUATION SUMMARY")
    print("="*80)

    print(f"\n✅ Addresses Match: {len(results['matched'])}")
    print(f"   Kajabi and database have identical addresses")

    print(f"\n🔄 Needs Update in Kajabi: {len(results['needs_update'])}")
    print(f"   Database has corrected address, Kajabi needs update")

    print(f"\n⚠️  No Address in Kajabi: {len(results['no_address_kajabi'])}")
    print(f"   Database has address, but Kajabi is empty")

    print(f"\n📭 No Address in Database: {len(results['no_address_db'])}")
    print(f"   Kajabi has address, but database is empty")

    print(f"\n❓ Not in Database: {len(results['not_in_db'])}")
    print(f"   Contact exists in Kajabi but not in database")

    print(f"\n❓ Not in Kajabi: {len(results['not_in_kajabi'])}")
    print(f"   Contact exists in database but not in Kajabi")

    print("\n" + "="*80)

def generate_detailed_report(results: Dict, output_path: str) -> None:
    """Generate detailed CSV report of changes needed."""
    print(f"\nGenerating detailed report: {output_path}")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Status',
            'Email',
            'Name',
            'Kajabi_ID',
            'Changed_Fields',
            'Kajabi_Address_Line_1',
            'DB_Address_Line_1',
            'Kajabi_Address_Line_2',
            'DB_Address_Line_2',
            'Kajabi_City',
            'DB_City',
            'Kajabi_State',
            'DB_State',
            'Kajabi_Country',
            'DB_Country',
            'Kajabi_Zip',
            'DB_Zip',
            'Corrected_At',
            'Correction_Source'
        ])

        # Needs update records
        for record in results['needs_update']:
            kajabi = record['kajabi']
            db = record['db']

            writer.writerow([
                'NEEDS_UPDATE',
                kajabi['email'],
                kajabi['name'],
                kajabi['kajabi_id'],
                ', '.join(record['differences']),
                kajabi['address_line_1'],
                db['address_line_1'],
                kajabi['address_line_2'],
                db['address_line_2'],
                kajabi['city'],
                db['city'],
                kajabi['state'],
                db['state'],
                kajabi['country'],
                db['country'],
                kajabi['zip'],
                db['zip'],
                db.get('corrected_at', ''),
                db.get('correction_source', '')
            ])

        # No address in Kajabi
        for record in results['no_address_kajabi']:
            kajabi = record['kajabi']
            db = record['db']

            writer.writerow([
                'NO_ADDRESS_KAJABI',
                kajabi['email'],
                kajabi['name'],
                kajabi['kajabi_id'],
                'all fields empty',
                '',
                db['address_line_1'],
                '',
                db['address_line_2'],
                '',
                db['city'],
                '',
                db['state'],
                '',
                db['country'],
                '',
                db['zip'],
                db.get('corrected_at', ''),
                db.get('correction_source', '')
            ])

    print(f"✅ Detailed report saved: {output_path}")

def generate_kajabi_import_csv(results: Dict, output_path: str) -> None:
    """
    Generate CSV file ready for import into Kajabi.
    Only includes records that need updates.
    """
    print(f"\nGenerating Kajabi import CSV: {output_path}")

    records_to_update = results['needs_update'] + results['no_address_kajabi']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header matching Kajabi import format
        writer.writerow([
            'ID',  # Kajabi ID for matching
            'Email',
            'Name',
            'Address (address_line_1)',
            'Address Line 2 (address_line_2)',
            'City (address_city)',
            'State (address_state)',
            'Country (address_country)',
            'Zip Code (address_zip)'
        ])

        # Write records with corrected addresses
        for record in records_to_update:
            kajabi = record['kajabi']
            db = record['db']

            writer.writerow([
                kajabi['kajabi_id'],
                db['email'],
                db['name'],
                db['address_line_1'],
                db['address_line_2'],
                db['city'],
                db['state'],
                db['country'],
                db['zip']
            ])

    print(f"✅ Kajabi import CSV saved: {output_path}")
    print(f"   Records to update: {len(records_to_update)}")

def main() -> None:
    """Main evaluation function."""
    # Paths
    kajabi_csv = "/workspaces/starhouse-database-v2/kajabi 3 files review/11012025_kajabi_contact_evaluate.csv"
    report_path = "/workspaces/starhouse-database-v2/data/current/kajabi_address_evaluation_report.csv"
    import_path = "/workspaces/starhouse-database-v2/data/current/kajabi_address_import_ready.csv"

    if not os.path.exists(kajabi_csv):
        print(f"ERROR: Kajabi CSV not found: {kajabi_csv}")
        sys.exit(1)

    try:
        # Load data
        kajabi_contacts = load_kajabi_csv(kajabi_csv)

        conn = get_db_connection()
        db_addresses = load_db_addresses(conn)

        # Evaluate
        results = evaluate_addresses(kajabi_contacts, db_addresses)

        # Print summary
        print_evaluation_summary(results)

        # Generate reports
        generate_detailed_report(results, report_path)
        generate_kajabi_import_csv(results, import_path)

        conn.close()

        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print(f"1. Review detailed report: {report_path}")
        print(f"2. Import corrected addresses to Kajabi: {import_path}")
        print(f"3. Records to update: {len(results['needs_update']) + len(results['no_address_kajabi'])}")
        print("="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
