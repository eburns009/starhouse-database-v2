#!/usr/bin/env python3
"""Quick check of subscription state"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

# Check subscription counts by status
print("\n📊 Subscriptions by status:")
print("-" * 60)
cur.execute("""
    SELECT
        status,
        COUNT(*) as count,
        COUNT(DISTINCT contact_id) as unique_contacts
    FROM subscriptions
    WHERE deleted_at IS NULL
    GROUP BY status
    ORDER BY count DESC
""")
for row in cur.fetchall():
    print(f"{row['status']:15} {row['count']:5} subscriptions, {row['unique_contacts']:5} unique contacts")

# Check contacts with multiple active subscriptions
print("\n🔍 Contacts with multiple ACTIVE subscriptions:")
print("-" * 60)
cur.execute("""
    SELECT
        contact_id,
        COUNT(*) as subscription_count
    FROM subscriptions
    WHERE deleted_at IS NULL
      AND status = 'active'
    GROUP BY contact_id
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")
multi = cur.fetchall()
print(f"Found: {len(multi)} contacts")
if multi:
    for row in multi[:10]:
        print(f"  Contact ID {row['contact_id']}: {row['subscription_count']} active subscriptions")

# Check PayPal subscriptions
print("\n💳 PayPal subscription references:")
print("-" * 60)
cur.execute("""
    SELECT COUNT(*) as count
    FROM subscriptions
    WHERE deleted_at IS NULL
      AND paypal_subscription_reference IS NOT NULL
""")
paypal_count = cur.fetchone()['count']
print(f"Total with PayPal reference: {paypal_count}")

# Check Kajabi subscriptions
print("\n🏢 Kajabi subscription IDs:")
print("-" * 60)
cur.execute("""
    SELECT COUNT(*) as count
    FROM subscriptions
    WHERE deleted_at IS NULL
      AND kajabi_subscription_id IS NOT NULL
""")
kajabi_count = cur.fetchone()['count']
print(f"Total with Kajabi ID: {kajabi_count}")

# Check PayPal IDs that look like they're in the wrong field
print("\n⚠️  PayPal IDs in kajabi_subscription_id field:")
print("-" * 60)
cur.execute("""
    SELECT COUNT(*) as count
    FROM subscriptions
    WHERE deleted_at IS NULL
      AND kajabi_subscription_id LIKE 'I-%'
""")
misplaced = cur.fetchone()['count']
print(f"PayPal IDs in wrong field: {misplaced}")

if misplaced > 0:
    print("\nSample misplaced IDs:")
    cur.execute("""
        SELECT id, contact_id, kajabi_subscription_id, status, amount
        FROM subscriptions
        WHERE deleted_at IS NULL
          AND kajabi_subscription_id LIKE 'I-%'
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  ID {row['id']}: {row['kajabi_subscription_id']} (${row['amount']}, {row['status']})")

cur.close()
conn.close()
print()
