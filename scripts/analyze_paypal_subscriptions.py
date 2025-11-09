#!/usr/bin/env python3
"""
Analyze PayPal Subscriptions

This script analyzes the PayPal_Import file to find all subscriptions
and compare them against the database to identify missing ones.
"""

import csv
from collections import defaultdict
from decimal import Decimal

# Read PayPal data
paypal_file = '/workspaces/starhouse-database-v2/data/Paypal_Import'

subscriptions = {}  # Key: subscription_id, Value: details

print("Reading PayPal data...")
with open(paypal_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')

    for row in reader:
        # Only process subscription payments that completed
        if row['Type'] == 'Subscription Payment' and row['Status'] == 'Completed':
            ref_id = row['Reference Txn ID']

            # PayPal subscription IDs start with I-
            if ref_id and ref_id.startswith('I-'):
                if ref_id not in subscriptions:
                    # Remove commas from amount before converting
                    amount_str = row['Gross'].replace(',', '') if row['Gross'] else '0'
                    subscriptions[ref_id] = {
                        'subscription_id': ref_id,
                        'item_title': row['Item Title'],
                        'amount': float(amount_str),
                        'emails': set(),
                        'names': set(),
                        'payment_count': 0,
                        'first_payment': row['Date'],
                        'last_payment': row['Date']
                    }

                sub = subscriptions[ref_id]
                sub['emails'].add(row['From Email Address'])
                sub['names'].add(row['Name'])
                sub['payment_count'] += 1

                # Update date range
                if row['Date'] < sub['first_payment']:
                    sub['first_payment'] = row['Date']
                if row['Date'] > sub['last_payment']:
                    sub['last_payment'] = row['Date']

print(f"Found {len(subscriptions)} unique PayPal subscriptions\n")

# Group by item title
by_title = defaultdict(list)
for sub_id, details in subscriptions.items():
    title = details['item_title'].lower().strip()
    by_title[title].append(details)

# Show summary
print("=" * 80)
print("PAYPAL SUBSCRIPTIONS SUMMARY")
print("=" * 80)
print(f"{'Item Title':<40} {'Count':>8} {'Amount':>10}")
print("-" * 80)

for title in sorted(by_title.keys()):
    subs = by_title[title]
    count = len(subs)
    # Get most common amount
    amounts = [s['amount'] for s in subs]
    avg_amount = sum(amounts) / len(amounts) if amounts else 0
    print(f"{title[:40]:<40} {count:>8} ${avg_amount:>9.2f}")

print("-" * 80)
print(f"{'TOTAL':<40} {len(subscriptions):>8}")
print("=" * 80)

# Show some example subscriptions with details
print("\n" + "=" * 80)
print("SAMPLE SUBSCRIPTION DETAILS (First 10)")
print("=" * 80)

for i, (sub_id, details) in enumerate(list(subscriptions.items())[:10]):
    print(f"\n{i+1}. Subscription ID: {sub_id}")
    print(f"   Item: {details['item_title']}")
    print(f"   Amount: ${details['amount']:.2f}")
    print(f"   Emails: {', '.join(list(details['emails'])[:3])}")
    print(f"   Payment Count: {details['payment_count']}")
    print(f"   First: {details['first_payment']} → Last: {details['last_payment']}")

# Export to CSV for analysis
output_file = '/workspaces/starhouse-database-v2/data/paypal_subscriptions_analysis.csv'
print(f"\n\nExporting to {output_file}...")

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'subscription_id', 'item_title', 'amount',
        'email', 'customer_name', 'payment_count',
        'first_payment', 'last_payment'
    ])

    for sub_id, details in sorted(subscriptions.items()):
        writer.writerow([
            sub_id,
            details['item_title'],
            f"{details['amount']:.2f}",
            ', '.join(details['emails']),
            ', '.join(details['names']),
            details['payment_count'],
            details['first_payment'],
            details['last_payment']
        ])

print(f"✅ Exported {len(subscriptions)} subscriptions to CSV")
print("\nDone!")
