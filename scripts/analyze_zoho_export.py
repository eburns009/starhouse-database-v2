#!/usr/bin/env python3
"""
Analyze Zoho CRM Export Structure
Provides detailed analysis of the Zoho export file to inform import strategy
"""

import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime

def analyze_zoho_export(filepath):
    """Analyze Zoho export file structure and data quality"""

    print(f"\n{'='*80}")
    print(f"ZOHO EXPORT ANALYSIS: {filepath}")
    print(f"{'='*80}\n")

    # Statistics
    total_rows = 0
    field_stats = defaultdict(lambda: {'filled': 0, 'empty': 0, 'samples': []})
    email_count = 0
    phone_count = 0
    address_count = 0
    secondary_email_count = 0
    tag_count = 0
    product_count = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Print columns
        print("COLUMNS FOUND:")
        for i, col in enumerate(reader.fieldnames, 1):
            print(f"  {i:2d}. {col}")
        print()

        for row in reader:
            total_rows += 1

            # Analyze each field
            for field, value in row.items():
                if value and value.strip():
                    field_stats[field]['filled'] += 1
                    if len(field_stats[field]['samples']) < 3:
                        field_stats[field]['samples'].append(value[:100])
                else:
                    field_stats[field]['empty'] += 1

            # Count key fields
            if row.get('Email'):
                email_count += 1
            if row.get('Phone'):
                phone_count += 1
            if row.get('Secondary Email'):
                secondary_email_count += 1
            if row.get('Tag'):
                tag_count += 1
            if row.get('Products'):
                product_count += 1
            if any([row.get('Mailing Street'), row.get('Mailing City'),
                   row.get('Mailing State'), row.get('Mailing Zip')]):
                address_count += 1

    # Print summary
    print(f"SUMMARY:")
    print(f"  Total Contacts: {total_rows:,}")
    print(f"  With Email: {email_count:,} ({email_count/total_rows*100:.1f}%)")
    print(f"  With Phone: {phone_count:,} ({phone_count/total_rows*100:.1f}%)")
    print(f"  With Address: {address_count:,} ({address_count/total_rows*100:.1f}%)")
    print(f"  With Secondary Email: {secondary_email_count:,} ({secondary_email_count/total_rows*100:.1f}%)")
    print(f"  With Tags: {tag_count:,} ({tag_count/total_rows*100:.1f}%)")
    print(f"  With Products: {product_count:,} ({product_count/total_rows*100:.1f}%)")
    print()

    # Field completeness report
    print("FIELD COMPLETENESS:")
    print(f"{'Field':<30} {'Filled':>10} {'Empty':>10} {'Fill %':>8}")
    print("-" * 62)

    # Sort by fill percentage
    sorted_fields = sorted(field_stats.items(),
                          key=lambda x: x[1]['filled'],
                          reverse=True)

    for field, stats in sorted_fields:
        if stats['filled'] > 0:  # Only show fields with data
            fill_pct = stats['filled'] / total_rows * 100
            print(f"{field:<30} {stats['filled']:>10,} {stats['empty']:>10,} {fill_pct:>7.1f}%")

    print()

    # Sample data for key fields
    print("SAMPLE DATA:")
    key_fields = ['Record Id', 'First Name', 'Last Name', 'Email', 'Phone',
                  'Mailing Street', 'Mailing City', 'Mailing State', 'Mailing Zip',
                  'Tag', 'Products', 'Description', 'Secondary Email']

    for field in key_fields:
        if field in field_stats and field_stats[field]['samples']:
            print(f"\n{field}:")
            for i, sample in enumerate(field_stats[field]['samples'], 1):
                print(f"  {i}. {sample}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    filepath = 'kajabi 3 files review/Zoho_Contacts_2025_11_08.csv'
    analyze_zoho_export(filepath)
