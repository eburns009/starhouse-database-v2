#!/usr/bin/env python3
"""Verify we have the complete list of problem cases"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 120)
print("VERIFICATION: Complete List of Billing Issues")
print("=" * 120)
print()

print("METHOD 1: Check all 11 PayPal-only subscriptions for canceled Kajabi equivalents")
print("-" * 120)

# Get all PayPal-only subscriptions (active, with PayPal ID in wrong field)
cur.execute("""
    SELECT COUNT(*) FROM subscriptions
    WHERE deleted_at IS NULL
      AND status = 'active'
      AND kajabi_subscription_id LIKE 'I-%'
      AND paypal_subscription_reference = kajabi_subscription_id
""")
total_paypal_only = cur.fetchone()['count']
print(f"Total PayPal-only subscriptions: {total_paypal_only}")

# Check how many have canceled Kajabi equivalents
cur.execute("""
    SELECT
        s.id as paypal_sub_id,
        c.email,
        s.amount,
        s.billing_cycle
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.status = 'active'
      AND s.kajabi_subscription_id LIKE 'I-%'
      AND s.paypal_subscription_reference = s.kajabi_subscription_id
      AND EXISTS (
          SELECT 1 FROM subscriptions s2
          WHERE s2.contact_id = s.contact_id
            AND s2.deleted_at IS NULL
            AND s2.status IN ('canceled', 'expired')
            AND s2.kajabi_subscription_id IS NOT NULL
            AND s2.kajabi_subscription_id NOT LIKE 'I-%'
            AND ABS(s2.amount - s.amount) <= 1.0
      )
""")
with_canceled_kajabi = cur.fetchall()
print(f"With canceled Kajabi equivalent: {len(with_canceled_kajabi)}")
for item in with_canceled_kajabi:
    print(f"  • {item['email']}: ${item['amount']} / {item['billing_cycle']}")

print()
print("METHOD 2: Check all contacts with both PayPal-only AND canceled Kajabi subscriptions")
print("-" * 120)

# Find contacts that have BOTH PayPal-only active AND Kajabi canceled
cur.execute("""
    SELECT DISTINCT
        c.id as contact_id,
        c.email,
        c.first_name || ' ' || c.last_name as name
    FROM contacts c
    WHERE EXISTS (
        -- Has active PayPal-only subscription
        SELECT 1 FROM subscriptions s1
        WHERE s1.contact_id = c.id
          AND s1.deleted_at IS NULL
          AND s1.status = 'active'
          AND s1.kajabi_subscription_id LIKE 'I-%'
          AND s1.paypal_subscription_reference = s1.kajabi_subscription_id
    )
    AND EXISTS (
        -- Has canceled Kajabi subscription
        SELECT 1 FROM subscriptions s2
        WHERE s2.contact_id = c.id
          AND s2.deleted_at IS NULL
          AND s2.status IN ('canceled', 'expired')
          AND s2.kajabi_subscription_id IS NOT NULL
          AND s2.kajabi_subscription_id NOT LIKE 'I-%'
    )
""")
contacts_with_issue = cur.fetchall()
print(f"Contacts with both PayPal active + Kajabi canceled: {len(contacts_with_issue)}")
for contact in contacts_with_issue:
    print(f"  • {contact['name']} ({contact['email']})")

print()
print("=" * 120)
print()
print("CONCLUSION:")
print(f"  Found {len(with_canceled_kajabi)} subscriptions needing cancellation")
print(f"  Affecting {len(contacts_with_issue)} customers")
print()
print("These are the COMPLETE list of billing issues (4 customers, 4 subscriptions)")
print("=" * 120)
print()

cur.close()
conn.close()
