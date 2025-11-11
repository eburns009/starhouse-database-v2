#!/usr/bin/env python3
"""
Analyze the impact of running Kajabi weekly import on enriched data.
Shows what data would be lost or overwritten.
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, List, Tuple
from collections import defaultdict

def get_db_connection():
    """Get database connection from environment."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def load_kajabi_csv(csv_path: str) -> Dict[str, Dict]:
    """Load Kajabi CSV file, indexed by email."""
    print(f"Loading Kajabi CSV: {csv_path}")

    contacts = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if not email:
                continue

            contacts[email] = {
                'email': email,
                'first_name': row.get('First Name', '').strip() or None,
                'last_name': row.get('Last Name', '').strip() or None,
                'phone': row.get('Phone Number (phone_number)', '').strip() or None,
                'address_line_1': row.get('Address (address_line_1)', '').strip() or None,
                'address_line_2': row.get('Address Line 2 (address_line_2)', '').strip() or None,
                'city': row.get('City (address_city)', '').strip() or None,
                'state': row.get('State (address_state)', '').strip() or None,
                'postal_code': row.get('Zip Code (address_zip)', '').strip() or None,
                'country': row.get('Country (address_country)', '').strip() or None,
                'kajabi_id': row.get('ID', '').strip() or None,
            }

    print(f"Loaded {len(contacts)} contacts from Kajabi CSV")
    return contacts

def analyze_impact(conn, kajabi_contacts: Dict[str, Dict]) -> Dict:
    """
    Analyze what would happen if we ran the import.
    Simulates the COALESCE logic from the import script.
    """
    print("\nAnalyzing impact of Kajabi import on enriched data...")

    cursor = conn.cursor(cursor_factory=DictCursor)

    # Get all contacts from database
    cursor.execute("""
        SELECT
            id, email, first_name, last_name, phone,
            address_line_1, address_line_2, city, state, postal_code, country,
            source_system, kajabi_id,
            paypal_email, paypal_first_name, paypal_last_name, paypal_phone,
            zoho_id, ticket_tailor_id,
            shipping_address_line_1, shipping_city, shipping_state, shipping_postal_code,
            phone_source, billing_address_source
        FROM contacts
        ORDER BY email
    """)

    results = {
        'total_db_contacts': 0,
        'total_kajabi_contacts': len(kajabi_contacts),
        'matched_contacts': 0,
        'impacts': defaultdict(list)
    }

    for db_row in cursor:
        results['total_db_contacts'] += 1

        email = db_row['email'].strip().lower()

        # Check if this contact exists in Kajabi CSV
        if email not in kajabi_contacts:
            # Contact in DB but not in Kajabi - would be unaffected
            continue

        results['matched_contacts'] += 1
        kajabi = kajabi_contacts[email]

        # Simulate COALESCE logic: new_value if not null, else keep old_value
        def would_change(kajabi_val, db_val, field_name):
            """Check if field would change after COALESCE."""
            # COALESCE(%s, field) means: use new value if not None, else keep existing
            if kajabi_val is not None and kajabi_val != db_val:
                return True
            return False

        # Track what would change
        changes = {}

        # Check each field
        if would_change(kajabi['first_name'], db_row['first_name'], 'first_name'):
            changes['first_name'] = {
                'current': db_row['first_name'],
                'would_become': kajabi['first_name'],
                'enriched_from': 'PayPal' if db_row['paypal_first_name'] else None
            }

        if would_change(kajabi['last_name'], db_row['last_name'], 'last_name'):
            changes['last_name'] = {
                'current': db_row['last_name'],
                'would_become': kajabi['last_name'],
                'enriched_from': 'PayPal' if db_row['paypal_last_name'] else None
            }

        if would_change(kajabi['phone'], db_row['phone'], 'phone'):
            changes['phone'] = {
                'current': db_row['phone'],
                'would_become': kajabi['phone'],
                'enriched_from': db_row['phone_source'] or ('PayPal' if db_row['paypal_phone'] else None)
            }

        if would_change(kajabi['address_line_1'], db_row['address_line_1'], 'address_line_1'):
            changes['address_line_1'] = {
                'current': db_row['address_line_1'],
                'would_become': kajabi['address_line_1'],
                'enriched_from': db_row['billing_address_source']
            }

        if would_change(kajabi['address_line_2'], db_row['address_line_2'], 'address_line_2'):
            changes['address_line_2'] = {
                'current': db_row['address_line_2'],
                'would_become': kajabi['address_line_2'],
                'enriched_from': db_row['billing_address_source']
            }

        if would_change(kajabi['city'], db_row['city'], 'city'):
            changes['city'] = {
                'current': db_row['city'],
                'would_become': kajabi['city'],
                'enriched_from': db_row['billing_address_source']
            }

        if would_change(kajabi['state'], db_row['state'], 'state'):
            changes['state'] = {
                'current': db_row['state'],
                'would_become': kajabi['state'],
                'enriched_from': db_row['billing_address_source']
            }

        if would_change(kajabi['postal_code'], db_row['postal_code'], 'postal_code'):
            changes['postal_code'] = {
                'current': db_row['postal_code'],
                'would_become': kajabi['postal_code'],
                'enriched_from': db_row['billing_address_source']
            }

        if would_change(kajabi['country'], db_row['country'], 'country'):
            changes['country'] = {
                'current': db_row['country'],
                'would_become': kajabi['country'],
                'enriched_from': db_row['billing_address_source']
            }

        # If there are changes, record them
        if changes:
            impact_record = {
                'email': email,
                'db_source': db_row['source_system'],
                'linked_to_paypal': db_row['paypal_email'] is not None,
                'linked_to_zoho': db_row['zoho_id'] is not None,
                'has_shipping_address': db_row['shipping_address_line_1'] is not None,
                'changes': changes
            }

            # Categorize by severity
            if any(c.get('enriched_from') for c in changes.values()):
                results['impacts']['enriched_data_would_be_lost'].append(impact_record)
            else:
                results['impacts']['corrections_would_be_lost'].append(impact_record)

    cursor.close()
    return results

def print_summary(results: Dict) -> None:
    """Print impact summary."""
    print("\n" + "="*80)
    print("CRITICAL IMPACT ANALYSIS: Next Kajabi Import")
    print("="*80)

    print(f"\nDatabase Contacts: {results['total_db_contacts']}")
    print(f"Kajabi CSV Contacts: {results['total_kajabi_contacts']}")
    print(f"Matched (would be updated): {results['matched_contacts']}")

    enriched_lost = results['impacts']['enriched_data_would_be_lost']
    corrections_lost = results['impacts']['corrections_would_be_lost']

    print(f"\n🚨 CRITICAL: {len(enriched_lost)} contacts with ENRICHED data would be overwritten")
    print(f"⚠️  WARNING: {len(corrections_lost)} contacts with CORRECTIONS would be overwritten")

    # Breakdown by field
    print("\n" + "-"*80)
    print("Breakdown by Field:")
    print("-"*80)

    field_counts = defaultdict(int)
    for record in enriched_lost + corrections_lost:
        for field in record['changes'].keys():
            field_counts[field] += 1

    for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {field:20s}: {count:4d} contacts would change")

    # Show enrichment sources at risk
    print("\n" + "-"*80)
    print("Enriched Data at Risk:")
    print("-"*80)

    enriched_from_paypal = sum(1 for r in enriched_lost if r['linked_to_paypal'])
    enriched_from_zoho = sum(1 for r in enriched_lost if r['linked_to_zoho'])

    print(f"  Contacts enriched from PayPal: {enriched_from_paypal}")
    print(f"  Contacts linked to Zoho: {enriched_from_zoho}")

    print("\n" + "="*80)

def save_detailed_report(results: Dict, output_path: str) -> None:
    """Save detailed report of impacts."""
    print(f"\nSaving detailed impact report: {output_path}")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow([
            'Severity',
            'Email',
            'Source_System',
            'Linked_To_PayPal',
            'Linked_To_Zoho',
            'Has_Shipping_Address',
            'Fields_Affected',
            'Field_Details'
        ])

        # Enriched data losses (critical)
        for record in results['impacts']['enriched_data_would_be_lost']:
            field_details = []
            for field, change in record['changes'].items():
                enriched = change.get('enriched_from', 'corrected')
                field_details.append(
                    f"{field}: {change['current']} → {change['would_become']} (from {enriched})"
                )

            writer.writerow([
                'CRITICAL',
                record['email'],
                record['db_source'],
                'Yes' if record['linked_to_paypal'] else 'No',
                'Yes' if record['linked_to_zoho'] else 'No',
                'Yes' if record['has_shipping_address'] else 'No',
                ', '.join(record['changes'].keys()),
                ' | '.join(field_details)
            ])

        # Correction losses (warning)
        for record in results['impacts']['corrections_would_be_lost']:
            field_details = []
            for field, change in record['changes'].items():
                field_details.append(
                    f"{field}: {change['current']} → {change['would_become']}"
                )

            writer.writerow([
                'WARNING',
                record['email'],
                record['db_source'],
                'Yes' if record['linked_to_paypal'] else 'No',
                'Yes' if record['linked_to_zoho'] else 'No',
                'Yes' if record['has_shipping_address'] else 'No',
                ', '.join(record['changes'].keys()),
                ' | '.join(field_details)
            ])

    print(f"✅ Detailed report saved")

def main() -> None:
    """Main analysis function."""
    kajabi_csv = "/workspaces/starhouse-database-v2/kajabi 3 files review/11012025_kajabi_contact_evaluate.csv"
    report_path = "/workspaces/starhouse-database-v2/data/current/import_impact_analysis.csv"

    if not os.path.exists(kajabi_csv):
        print(f"ERROR: Kajabi CSV not found: {kajabi_csv}")
        sys.exit(1)

    try:
        # Load data
        kajabi_contacts = load_kajabi_csv(kajabi_csv)

        conn = get_db_connection()
        results = analyze_impact(conn, kajabi_contacts)

        # Print summary
        print_summary(results)

        # Save detailed report
        save_detailed_report(results, report_path)

        conn.close()

        print("\n" + "="*80)
        print("CONCLUSION:")
        print("="*80)
        print("Running the next Kajabi import WITHOUT PROTECTION will:")
        print(f"  ❌ Overwrite {len(results['impacts']['enriched_data_would_be_lost'])} enriched records")
        print(f"  ❌ Overwrite {len(results['impacts']['corrections_would_be_lost'])} corrected records")
        print(f"  ❌ Lose all cross-system enrichment work")
        print(f"\nYou MUST implement protection before the next import!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
