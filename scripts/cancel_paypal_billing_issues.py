#!/usr/bin/env python3
"""
Cancel the 4 PayPal subscriptions with billing issues
(Kajabi canceled but PayPal still charging)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 120)
print("CANCEL PAYPAL SUBSCRIPTIONS WITH BILLING ISSUES")
print("=" * 120)
print()

# The 4 subscriptions to cancel
subscriptions_to_cancel = [
    {
        'id': '74a3d5d7-3605-4b4b-aa7b-18d1c27e3a8a',
        'name': 'Anthony Smith',
        'email': 'anthony@crowninternational.us',
        'amount_overcharged': 462.00
    },
    {
        'id': '2ac71c9e-d429-4b0d-8e4f-2544acb15200',
        'name': 'Chris Loving-Campos',
        'email': 'chris@inspire.graphics',
        'amount_overcharged': 220.00
    },
    {
        'id': '8394aa12-3b19-4647-8b88-32a56b06f9fa',
        'name': 'Dionisia Hatzis',
        'email': 'denisehatzis@gmail.com',
        'amount_overcharged': 264.00
    },
    {
        'id': 'deae52b1-6395-4ea8-a859-08e0e87348bd',
        'name': 'Hildy Kane',
        'email': 'hildykane@yahoo.com',
        'amount_overcharged': 44.00
    }
]

print("BEFORE UPDATE:")
print("-" * 120)

for sub in subscriptions_to_cancel:
    cur.execute("""
        SELECT
            s.id,
            s.kajabi_subscription_id,
            s.paypal_subscription_reference,
            s.status,
            s.amount,
            s.billing_cycle
        FROM subscriptions s
        WHERE s.id = %s
    """, (sub['id'],))

    current = cur.fetchone()
    if current:
        print(f"  {sub['name']} ({sub['email']})")
        print(f"    ID: {current['id']}")
        print(f"    Status: {current['status']}")
        print(f"    Amount: ${current['amount']} / {current['billing_cycle']}")
        print(f"    Overcharged: ${sub['amount_overcharged']:.2f}")
        print()

print()
print("=" * 120)
print()
print("EXECUTING UPDATE...")
print()

# Update each subscription to canceled
updated_count = 0

for sub in subscriptions_to_cancel:
    # Update status to canceled
    cur.execute("""
        UPDATE subscriptions
        SET status = 'canceled',
            updated_at = NOW()
        WHERE id = %s
          AND status = 'active'
        RETURNING id
    """, (sub['id'],))

    result = cur.fetchone()
    if result:
        updated_count += 1
        print(f"  ✓ Canceled: {sub['name']} ({sub['email']})")
    else:
        print(f"  ⚠️  Not updated: {sub['name']} (already canceled or not found)")

print()
print(f"✓ Updated {updated_count} subscription(s)")
print()

# Commit transaction
conn.commit()
print("✓ Transaction committed")
print()

print("=" * 120)
print()
print("AFTER UPDATE - VERIFICATION:")
print("-" * 120)

for sub in subscriptions_to_cancel:
    cur.execute("""
        SELECT
            s.id,
            s.status,
            s.amount,
            s.billing_cycle,
            s.updated_at
        FROM subscriptions s
        WHERE s.id = %s
    """, (sub['id'],))

    current = cur.fetchone()
    if current:
        status_icon = "✓" if current['status'] == 'canceled' else "✗"
        print(f"  {sub['name']} ({sub['email']})")
        print(f"    Status: {current['status']} {status_icon}")
        print(f"    Updated: {current['updated_at']}")
        print()

print()
print("=" * 120)
print()
print("SUMMARY:")
print("-" * 120)
print(f"  Subscriptions canceled: {updated_count}")
print(f"  Total amount overcharged: $990.00")
print()
print("NEXT STEPS:")
print("  1. ✅ Database updated (subscriptions marked as canceled)")
print("  2. ⚠️  Cancel these subscriptions in PayPal dashboard to stop future charges")
print("  3. ⚠️  Contact customers about refunds:")
print()
for sub in subscriptions_to_cancel:
    print(f"       • {sub['name']} ({sub['email']}): ${sub['amount_overcharged']:.2f}")

print()
print("=" * 120)
print()

cur.close()
conn.close()
