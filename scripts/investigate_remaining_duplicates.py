#!/usr/bin/env python3
"""Investigate the 11 remaining PayPal duplicates that weren't caught"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n🔍 Investigating remaining PayPal duplicates...\n")

# Find PayPal duplicates (PayPal ID in kajabi_subscription_id field)
cur.execute("""
    SELECT
        s.id,
        s.contact_id,
        s.kajabi_subscription_id,
        s.paypal_subscription_reference,
        s.status,
        s.amount,
        s.billing_cycle,
        c.email,
        c.first_name || ' ' || c.last_name as name
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.kajabi_subscription_id LIKE 'I-%'
      AND s.paypal_subscription_reference = s.kajabi_subscription_id
    ORDER BY c.email, s.amount
""")

paypal_dupes = cur.fetchall()
print(f"Found {len(paypal_dupes)} PayPal duplicates (PayPal ID in wrong field)\n")

# For each PayPal duplicate, check if there's a matching Kajabi subscription
print("Checking for matching Kajabi subscriptions:\n")
print("-" * 100)

for dupe in paypal_dupes:
    # Look for Kajabi subscription for same contact with similar amount
    cur.execute("""
        SELECT
            id,
            kajabi_subscription_id,
            status,
            amount,
            billing_cycle
        FROM subscriptions
        WHERE contact_id = %s
          AND deleted_at IS NULL
          AND kajabi_subscription_id IS NOT NULL
          AND kajabi_subscription_id NOT LIKE 'I-%'
          AND ABS(amount - %s) <= 1.0
    """, (dupe['contact_id'], dupe['amount']))

    matching_kajabi = cur.fetchall()

    if matching_kajabi:
        print(f"✓ MATCHED: {dupe['email']}")
        print(f"  PayPal Dupe: ID={dupe['id'][:8]}... | ${dupe['amount']} | {dupe['billing_cycle']} | Status={dupe['status']}")
        for match in matching_kajabi:
            print(f"  Kajabi Sub:  ID={match['id'][:8]}... | ${match['amount']} | {match['billing_cycle']} | Status={match['status']}")
    else:
        print(f"❌ NO MATCH: {dupe['email']}")
        print(f"  PayPal Dupe: ID={dupe['id'][:8]}... | ${dupe['amount']} | {dupe['billing_cycle']} | Status={dupe['status']}")
        print(f"  Reason: No Kajabi subscription found with matching amount")

        # Check if there are ANY Kajabi subscriptions for this contact
        cur.execute("""
            SELECT
                id,
                kajabi_subscription_id,
                status,
                amount,
                billing_cycle
            FROM subscriptions
            WHERE contact_id = %s
              AND deleted_at IS NULL
              AND kajabi_subscription_id IS NOT NULL
              AND kajabi_subscription_id NOT LIKE 'I-%'
        """, (dupe['contact_id'],))

        all_kajabi = cur.fetchall()
        if all_kajabi:
            print(f"  BUT contact has these Kajabi subscriptions:")
            for sub in all_kajabi:
                amount_diff = abs(float(sub['amount']) - float(dupe['amount']))
                print(f"    - ${sub['amount']} ({sub['billing_cycle']}, {sub['status']}) - Amount diff: ${amount_diff:.2f}")
        else:
            print(f"  Contact has NO Kajabi subscriptions - PayPal only!")

    print()

print("-" * 100)

cur.close()
conn.close()
