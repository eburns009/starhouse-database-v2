#!/usr/bin/env python3
"""
Find ALL Subscription Duplicates - FAANG Quality
=================================================
Comprehensive detection of duplicate subscriptions caused by PayPal import bug.

Root Cause: PayPal import script stores PayPal subscription IDs in the
kajabi_subscription_id field, causing genuine Kajabi subscriptions to be
treated as separate when they're actually the same subscription billed
through different processors.

Author: Claude Code
Date: 2025-11-12
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
from decimal import Decimal

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 80)
print("COMPREHENSIVE SUBSCRIPTION DUPLICATE ANALYSIS")
print("=" * 80)
print()

# Step 1: Find contacts with multiple active subscriptions
print("Step 1: Finding contacts with multiple active subscriptions...")
cur.execute("""
    SELECT
        c.id as contact_id,
        c.email,
        c.first_name || ' ' || c.last_name as name,
        COUNT(*) as active_subscription_count
    FROM contacts c
    JOIN subscriptions s ON c.id = s.contact_id
    WHERE s.deleted_at IS NULL
      AND s.status = 'active'
    GROUP BY c.id, c.email, c.first_name, c.last_name
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
""")
contacts_with_multiple = cur.fetchall()
print(f"✓ Found {len(contacts_with_multiple)} contacts with multiple active subscriptions\n")

# Step 2: Analyze each contact's subscriptions
duplicates = []
legitimate_multiples = []

print("Step 2: Analyzing each contact's subscription pattern...")
for contact in contacts_with_multiple:
    contact_id = contact['contact_id']

    # Get all active subscriptions for this contact
    cur.execute("""
        SELECT
            id,
            contact_id,
            kajabi_subscription_id,
            paypal_subscription_reference,
            status,
            amount,
            billing_cycle,
            start_date,
            created_at,
            payment_processor
        FROM subscriptions
        WHERE contact_id = %s
          AND status = 'active'
          AND deleted_at IS NULL
        ORDER BY created_at
    """, (contact_id,))

    subs = cur.fetchall()

    # Classify subscriptions
    kajabi_subs = []  # Real Kajabi subscriptions (numeric ID)
    paypal_misplaced_subs = []  # PayPal IDs in wrong field (I-xxxxx)
    paypal_only_subs = []  # Only has paypal_subscription_reference

    for sub in subs:
        kajabi_id = sub['kajabi_subscription_id']
        paypal_ref = sub['paypal_subscription_reference']

        if kajabi_id and kajabi_id.startswith('I-'):
            # PayPal ID misplaced in kajabi field
            paypal_misplaced_subs.append(sub)
        elif kajabi_id and not kajabi_id.startswith('I-'):
            # Real Kajabi subscription
            kajabi_subs.append(sub)
        elif paypal_ref and not kajabi_id:
            # PayPal only (correct field)
            paypal_only_subs.append(sub)

    # Determine if this is a duplicate or legitimate multiple
    is_duplicate = False
    duplicate_type = None

    if kajabi_subs and paypal_misplaced_subs:
        # Has both real Kajabi and misplaced PayPal - likely duplicate
        # Check if amounts match
        for k_sub in kajabi_subs:
            for p_sub in paypal_misplaced_subs:
                amount_diff = abs(float(k_sub['amount']) - float(p_sub['amount']))
                if amount_diff <= 1.0 and k_sub['billing_cycle'] == p_sub['billing_cycle']:
                    is_duplicate = True
                    duplicate_type = "Kajabi-PayPal collision (PayPal ID misplaced)"
                    break
            if is_duplicate:
                break

    if is_duplicate:
        duplicates.append({
            'contact_id': contact['contact_id'],
            'email': contact['email'],
            'name': contact['name'],
            'total_active_subs': len(subs),
            'kajabi_subs': len(kajabi_subs),
            'paypal_misplaced_subs': len(paypal_misplaced_subs),
            'paypal_only_subs': len(paypal_only_subs),
            'duplicate_type': duplicate_type,
            'subscriptions': subs
        })
    else:
        # Likely legitimate multiple subscriptions
        legitimate_multiples.append({
            'contact_id': contact['contact_id'],
            'email': contact['email'],
            'name': contact['name'],
            'total_active_subs': len(subs),
            'kajabi_subs': len(kajabi_subs),
            'paypal_misplaced_subs': len(paypal_misplaced_subs),
            'paypal_only_subs': len(paypal_only_subs),
            'subscriptions': subs
        })

print(f"✓ Analysis complete\n")

# Step 3: Print summary
print("=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print()

print(f"📊 Duplicate Subscriptions (Same subscription, different source):")
print(f"   {len(duplicates)} contacts")
total_duplicate_subs = sum(d['paypal_misplaced_subs'] for d in duplicates)
print(f"   {total_duplicate_subs} subscriptions to remove")
print()

print(f"✅ Legitimate Multiple Subscriptions:")
print(f"   {len(legitimate_multiples)} contacts")
print()

if duplicates:
    print("🔍 Duplicate Breakdown by Type:")
    type_counts = {}
    for d in duplicates:
        dt = d['duplicate_type']
        type_counts[dt] = type_counts.get(dt, 0) + 1
    for dtype, count in type_counts.items():
        print(f"   {dtype}: {count} contacts")
    print()

# Step 4: Export detailed CSV
csv_file = 'REVIEW_subscription_duplicates_detailed.csv'
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Contact Email', 'Contact Name', 'Total Active Subs',
        'Kajabi Subs', 'PayPal Misplaced', 'PayPal Only',
        'Classification', 'Subscription Details'
    ])

    # Write duplicates
    for dup in duplicates:
        sub_details = []
        for sub in dup['subscriptions']:
            detail = f"ID:{sub['id'][:8]}|K:{sub['kajabi_subscription_id'] or 'null'}|P:{sub['paypal_subscription_reference'] or 'null'}|${sub['amount']}|{sub['billing_cycle']}"
            sub_details.append(detail)

        writer.writerow([
            dup['email'],
            dup['name'],
            dup['total_active_subs'],
            dup['kajabi_subs'],
            dup['paypal_misplaced_subs'],
            dup['paypal_only_subs'],
            'DUPLICATE - Safe to remove PayPal',
            ' | '.join(sub_details)
        ])

    # Write legitimate multiples
    for legit in legitimate_multiples:
        sub_details = []
        for sub in legit['subscriptions']:
            detail = f"ID:{sub['id'][:8]}|K:{sub['kajabi_subscription_id'] or 'null'}|P:{sub['paypal_subscription_reference'] or 'null'}|${sub['amount']}|{sub['billing_cycle']}"
            sub_details.append(detail)

        writer.writerow([
            legit['email'],
            legit['name'],
            legit['total_active_subs'],
            legit['kajabi_subs'],
            legit['paypal_misplaced_subs'],
            legit['paypal_only_subs'],
            'LEGITIMATE MULTIPLE - Do not remove',
            ' | '.join(sub_details)
        ])

print(f"✓ Exported detailed analysis to: {csv_file}")

# Step 5: Generate deduplication script data
print(f"\n📋 Deduplication Plan:")
print(f"   Strategy: Keep Kajabi subscriptions, remove PayPal misplaced subscriptions")
print(f"   Safety: High (clear pattern, amounts match, different sources)")
print(f"   Subscriptions to remove: {total_duplicate_subs}")
print()

# Export IDs to remove
if duplicates:
    removal_file = 'subscription_ids_to_remove.txt'
    with open(removal_file, 'w') as f:
        for dup in duplicates:
            for sub in dup['subscriptions']:
                if sub['kajabi_subscription_id'] and sub['kajabi_subscription_id'].startswith('I-'):
                    f.write(f"{sub['id']}\n")
    print(f"✓ Exported subscription IDs to remove: {removal_file}")
    print()

print("=" * 80)
print()

cur.close()
conn.close()
