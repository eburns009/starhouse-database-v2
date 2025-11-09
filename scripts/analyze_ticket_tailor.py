#!/usr/bin/env python3
"""
Analyze Ticket Tailor Export Data
Provides detailed analysis of the Ticket Tailor CSV to inform import strategy
"""

import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal

def analyze_ticket_tailor(filepath):
    """Analyze Ticket Tailor export file structure and data quality"""

    print(f"\n{'='*80}")
    print(f"TICKET TAILOR EXPORT ANALYSIS: {filepath}")
    print(f"{'='*80}\n")

    # Statistics
    total_rows = 0
    field_stats = defaultdict(lambda: {'filled': 0, 'empty': 0, 'samples': []})

    # Specific counters
    email_count = 0
    phone_count = 0
    address_count = 0
    cancelled_count = 0
    refunded_count = 0
    payment_methods = Counter()
    events = Counter()
    total_revenue = Decimal('0')
    total_refunded = Decimal('0')

    with open(filepath, 'r', encoding='utf-8-sig') as f:
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
            if row.get('Mobile number'):
                phone_count += 1
            if row.get('Address 1'):
                address_count += 1
            if row.get('Order cancelled') == '1':
                cancelled_count += 1

            # Track refunds
            try:
                refunded = Decimal(row.get('Refunded amount', '0') or '0')
                if refunded > 0:
                    refunded_count += 1
                    total_refunded += refunded
            except:
                pass

            # Track payment methods
            payment_method = row.get('Payment method', 'Unknown')
            payment_methods[payment_method] += 1

            # Track events
            event_name = row.get('Event name', 'Unknown')
            events[event_name] += 1

            # Track revenue
            try:
                paid = Decimal(row.get('Total paid', '0') or '0')
                total_revenue += paid
            except:
                pass

    # Print summary
    print(f"SUMMARY:")
    print(f"  Total Orders: {total_rows:,}")
    print(f"  With Email: {email_count:,} ({email_count/total_rows*100:.1f}%)")
    print(f"  With Phone: {phone_count:,} ({phone_count/total_rows*100:.1f}%)")
    print(f"  With Address: {address_count:,} ({address_count/total_rows*100:.1f}%)")
    print(f"  Cancelled Orders: {cancelled_count:,} ({cancelled_count/total_rows*100:.1f}%)")
    print(f"  Refunded Orders: {refunded_count:,} ({refunded_count/total_rows*100:.1f}%)")
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    print(f"  Total Refunded: ${total_refunded:,.2f}")
    print()

    # Payment methods
    print("PAYMENT METHODS:")
    for method, count in payment_methods.most_common():
        print(f"  {method}: {count:,} ({count/total_rows*100:.1f}%)")
    print()

    # Top events
    print("TOP 10 EVENTS:")
    for event, count in events.most_common(10):
        print(f"  {event}: {count:,} orders")
    print()

    # Field completeness report
    print("FIELD COMPLETENESS (Top 20):")
    print(f"{'Field':<35} {'Filled':>10} {'Empty':>10} {'Fill %':>8}")
    print("-" * 67)

    # Sort by fill percentage
    sorted_fields = sorted(field_stats.items(),
                          key=lambda x: x[1]['filled'],
                          reverse=True)

    for field, stats in sorted_fields[:20]:
        if stats['filled'] > 0:
            fill_pct = stats['filled'] / total_rows * 100
            print(f"{field:<35} {stats['filled']:>10,} {stats['empty']:>10,} {fill_pct:>7.1f}%")

    print()

    # Sample data for key fields
    print("SAMPLE DATA:")
    key_fields = ['Order ID', 'Total paid', 'Order date', 'Name', 'First Name',
                  'Last Name', 'Email', 'Mobile number', 'Event name',
                  'Payment method', 'Transaction ID']

    for field in key_fields:
        if field in field_stats and field_stats[field]['samples']:
            print(f"\n{field}:")
            for i, sample in enumerate(field_stats[field]['samples'], 1):
                print(f"  {i}. {sample}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    filepath = 'kajabi 3 files review/ticket_tailor_data.csv'
    analyze_ticket_tailor(filepath)
