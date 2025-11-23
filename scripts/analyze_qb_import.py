#!/usr/bin/env python3
"""
Analyze QuickBooks CSV import file for donor module planning.
"""

import csv
import re
from datetime import datetime
from collections import defaultdict

def parse_amount(amount_str):
    """Parse amount string to float, handling commas and negatives."""
    if not amount_str:
        return 0.0
    # Remove commas and quotes
    cleaned = amount_str.replace(',', '').replace('"', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%m/%d/%Y')
    except ValueError:
        return None

def main():
    file_path = '/workspaces/starhouse-database-v2/data/current/11-23-25-QB Import.csv'

    # Read all rows
    all_rows = []
    development_rows = []
    unique_full_names = set()

    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip header rows (first 4 lines)
        for _ in range(4):
            next(f)

        reader = csv.DictReader(f)

        for row in reader:
            all_rows.append(row)
            full_name = row.get('Full name', '')
            unique_full_names.add(full_name)

            if 'DEVELOPMENT:' in full_name:
                development_rows.append(row)

    print("=" * 80)
    print("QUICKBOOKS CSV ANALYSIS: 11-23-25-QB Import.csv")
    print("=" * 80)

    # 1. Total row count
    print(f"\n1. TOTAL ROWS: {len(all_rows):,}")

    # 2. DEVELOPMENT row count
    print(f"\n2. DEVELOPMENT DONATION ROWS: {len(development_rows):,}")

    # 3. Sample DEVELOPMENT rows
    print("\n3. SAMPLE DEVELOPMENT DONATION ROWS (10 samples):")
    print("-" * 80)

    sample_count = min(10, len(development_rows))
    for i, row in enumerate(development_rows[:sample_count]):
        print(f"\n  Sample {i+1}:")
        print(f"    Customer: {row.get('Customer', '')}")
        print(f"    Date: {row.get('Transaction date', '')}")
        print(f"    Type: {row.get('Transaction type', '')}")
        print(f"    Full name: {row.get('Full name', '')}")
        print(f"    Amount: ${row.get('Amount', '0')}")
        print(f"    Memo: {row.get('Memo/Description', '')[:50]}...")
        print(f"    Payment method: {row.get('Payment method', '')}")

    # 4. Total $ amount for DEVELOPMENT donations
    total_development = sum(parse_amount(row.get('Amount', '0')) for row in development_rows)
    print(f"\n4. TOTAL DEVELOPMENT DONATIONS: ${total_development:,.2f}")

    # 5. Date range for DEVELOPMENT donations
    dev_dates = [parse_date(row.get('Transaction date', '')) for row in development_rows]
    dev_dates = [d for d in dev_dates if d is not None]

    if dev_dates:
        earliest = min(dev_dates)
        latest = max(dev_dates)
        print(f"\n5. DEVELOPMENT DONATION DATE RANGE:")
        print(f"   Earliest: {earliest.strftime('%m/%d/%Y')}")
        print(f"   Latest: {latest.strftime('%m/%d/%Y')}")
        print(f"   Span: {(latest - earliest).days} days")

    # 6. All unique Full name values (revenue categories)
    print(f"\n6. UNIQUE REVENUE CATEGORIES (Full name column): {len(unique_full_names)} unique values")
    print("-" * 80)

    # Group by top-level category
    categories = defaultdict(list)
    for name in sorted(unique_full_names):
        if name:
            top_level = name.split(':')[0] if ':' in name else name
            categories[top_level].append(name)

    for top_level in sorted(categories.keys()):
        subcats = categories[top_level]
        print(f"\n  {top_level} ({len(subcats)} subcategories):")
        for subcat in sorted(subcats)[:5]:  # Show first 5 of each
            print(f"    - {subcat}")
        if len(subcats) > 5:
            print(f"    ... and {len(subcats) - 5} more")

    # Additional analysis for DEVELOPMENT subcategories
    print("\n" + "=" * 80)
    print("DEVELOPMENT CATEGORY BREAKDOWN:")
    print("=" * 80)

    dev_subcats = defaultdict(lambda: {'count': 0, 'total': 0.0})
    for row in development_rows:
        full_name = row.get('Full name', '')
        amount = parse_amount(row.get('Amount', '0'))
        dev_subcats[full_name]['count'] += 1
        dev_subcats[full_name]['total'] += amount

    print(f"\n{'Category':<50} {'Count':>8} {'Total':>15}")
    print("-" * 75)
    for cat in sorted(dev_subcats.keys(), key=lambda x: dev_subcats[x]['total'], reverse=True):
        data = dev_subcats[cat]
        print(f"{cat:<50} {data['count']:>8,} ${data['total']:>13,.2f}")

    # Year breakdown for DEVELOPMENT
    print("\n" + "=" * 80)
    print("DEVELOPMENT DONATIONS BY YEAR:")
    print("=" * 80)

    yearly = defaultdict(lambda: {'count': 0, 'total': 0.0})
    for row in development_rows:
        date = parse_date(row.get('Transaction date', ''))
        if date:
            year = date.year
            amount = parse_amount(row.get('Amount', '0'))
            yearly[year]['count'] += 1
            yearly[year]['total'] += amount

    print(f"\n{'Year':<10} {'Count':>8} {'Total':>15}")
    print("-" * 35)
    for year in sorted(yearly.keys()):
        data = yearly[year]
        print(f"{year:<10} {data['count']:>8,} ${data['total']:>13,.2f}")

if __name__ == '__main__':
    main()
