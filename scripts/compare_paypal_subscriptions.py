#!/usr/bin/env python3
"""
Compare PayPal Subscriptions Against Database

This script compares PayPal subscriptions found in Paypal_Import file
against the subscriptions table to identify which ones are missing.
"""

import os
import csv
import psycopg2
from psycopg2.extras import DictCursor

# Database connection
DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"

# Read PayPal subscriptions CSV
paypal_file = '/workspaces/starhouse-database-v2/data/paypal_subscriptions_analysis.csv'

print("Reading PayPal subscriptions...")
paypal_subs = {}

with open(paypal_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sub_id = row['subscription_id']
        paypal_subs[sub_id] = {
            'subscription_id': sub_id,
            'item_title': row['item_title'],
            'amount': float(row['amount']),
            'email': row['email'],
            'customer_name': row['customer_name'],
            'payment_count': int(row['payment_count']),
            'first_payment': row['first_payment'],
            'last_payment': row['last_payment']
        }

print(f"Found {len(paypal_subs)} PayPal subscriptions")

# Connect to database
print("\nConnecting to database...")
conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
cur = conn.cursor(cursor_factory=DictCursor)

# Get all subscriptions with PayPal references
print("Fetching database subscriptions...")
cur.execute("""
    SELECT
        id,
        contact_id,
        paypal_subscription_reference,
        kajabi_subscription_id,
        status,
        amount,
        billing_cycle,
        start_date
    FROM subscriptions
    WHERE paypal_subscription_reference IS NOT NULL
    ORDER BY paypal_subscription_reference
""")

db_subs = {}
for row in cur.fetchall():
    ref = row['paypal_subscription_reference']
    db_subs[ref] = dict(row)

print(f"Found {len(db_subs)} database subscriptions with PayPal references")

# Compare
print("\n" + "=" * 80)
print("COMPARISON RESULTS")
print("=" * 80)

# Normalize subscription IDs (some may have lost the I- prefix)
paypal_ids = set(paypal_subs.keys())
db_refs = set(db_subs.keys())

# Find missing
missing_from_db = paypal_ids - db_refs
in_db = paypal_ids & db_refs

print(f"\nPayPal subscriptions: {len(paypal_ids)}")
print(f"In database: {len(in_db)}")
print(f"Missing from database: {len(missing_from_db)}")

# Check for subscriptions stored without I- prefix or as numeric only
print("\n" + "=" * 80)
print("MISSING SUBSCRIPTIONS ANALYSIS")
print("=" * 80)

if missing_from_db:
    print(f"\n{len(missing_from_db)} subscriptions from PayPal not found in database:\n")

    # Group by item title
    from collections import defaultdict
    by_title = defaultdict(list)

    for sub_id in sorted(missing_from_db):
        sub = paypal_subs[sub_id]
        by_title[sub['item_title']].append(sub)

    for title in sorted(by_title.keys()):
        subs = by_title[title]
        print(f"\n{title} ({len(subs)} subscriptions):")
        print("-" * 80)
        for sub in subs[:5]:  # Show first 5
            print(f"  ID: {sub['subscription_id']}")
            print(f"  Email: {sub['email']}")
            print(f"  Amount: ${sub['amount']:.2f}")
            print(f"  Payments: {sub['payment_count']} ({sub['first_payment']} to {sub['last_payment']})")
            print()

        if len(subs) > 5:
            print(f"  ... and {len(subs) - 5} more\n")

    # Export missing to CSV
    output_file = '/workspaces/starhouse-database-v2/data/missing_paypal_subscriptions.csv'
    print(f"\nExporting missing subscriptions to {output_file}...")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'subscription_id', 'item_title', 'amount', 'email',
            'customer_name', 'payment_count', 'first_payment', 'last_payment'
        ])

        for sub_id in sorted(missing_from_db):
            sub = paypal_subs[sub_id]
            writer.writerow([
                sub['subscription_id'], sub['item_title'], sub['amount'],
                sub['email'], sub['customer_name'], sub['payment_count'],
                sub['first_payment'], sub['last_payment']
            ])

    print(f"✅ Exported {len(missing_from_db)} missing subscriptions")

else:
    print("\n✅ All PayPal subscriptions are in the database!")

# Check for amount mismatches
print("\n" + "=" * 80)
print("AMOUNT VERIFICATION")
print("=" * 80)

mismatches = []
for sub_id in in_db:
    paypal_amount = paypal_subs[sub_id]['amount']
    db_amount = float(db_subs[sub_id]['amount'])

    if abs(paypal_amount - db_amount) > 0.01:
        mismatches.append({
            'sub_id': sub_id,
            'paypal_amount': paypal_amount,
            'db_amount': db_amount,
            'email': paypal_subs[sub_id]['email']
        })

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} subscriptions with amount mismatches:\n")
    for m in mismatches[:10]:
        print(f"  {m['sub_id']}: PayPal=${m['paypal_amount']:.2f}, DB=${m['db_amount']:.2f} ({m['email']})")
else:
    print("\n✅ All amounts match between PayPal and database")

cur.close()
conn.close()

print("\nDone!")
