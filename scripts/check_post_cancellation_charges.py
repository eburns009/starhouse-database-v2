#!/usr/bin/env python3
"""
Check if the 4 people with canceled Kajabi subscriptions are still being charged on PayPal
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 120)
print("POST-CANCELLATION CHARGE ANALYSIS")
print("Checking if people are still being charged after Kajabi cancellation")
print("=" * 120)
print()

# The 4 PayPal subscriptions that should be canceled
subscriptions_to_check = [
    {
        'name': 'Anthony Smith',
        'email': 'anthony@crowninternational.us',
        'paypal_sub_id': '74a3d5d7-3605-4b4b-aa7b-18d1c27e3a8a',
        'paypal_reference': 'I-3EGRVB085SRA',
        'kajabi_canceled': '2023-08-16'
    },
    {
        'name': 'Chris Loving-Campos',
        'email': 'chris@inspire.graphics',
        'paypal_sub_id': '2ac71c9e-d429-4b0d-8e4f-2544acb15200',
        'paypal_reference': 'I-A23T0X7HBSCG',
        'kajabi_canceled': '2024-11-16'
    },
    {
        'name': 'Dionisia Hatzis',
        'email': 'denisehatzis@gmail.com',
        'paypal_sub_id': '8394aa12-3b19-4647-8b88-32a56b06f9fa',
        'paypal_reference': 'I-HPW0LXHEETMU',
        'kajabi_canceled': '2025-03-03'
    },
    {
        'name': 'Hildy Kane',
        'email': 'hildykane@yahoo.com',
        'paypal_sub_id': 'deae52b1-6395-4ea8-a859-08e0e87348bd',
        'paypal_reference': 'I-TTKSECE0NDBT',
        'kajabi_canceled': '2025-09-23'
    }
]

total_post_cancel_charges = 0
total_amount_charged = 0.0

for i, sub in enumerate(subscriptions_to_check, 1):
    print(f"#{i}. {sub['name']} ({sub['email']})")
    print(f"    {'─' * 112}")
    print(f"    PayPal Reference:    {sub['paypal_reference']}")
    print(f"    Kajabi Canceled:     {sub['kajabi_canceled']}")
    print()

    # Get contact ID
    cur.execute("""
        SELECT id FROM contacts WHERE email = %s
    """, (sub['email'],))
    contact = cur.fetchone()

    if not contact:
        print(f"    ⚠️  Contact not found!")
        print()
        continue

    contact_id = str(contact['id'])

    # Get all PayPal transactions for this contact AFTER the Kajabi cancellation date
    cur.execute("""
        SELECT
            t.id,
            t.external_transaction_id,
            t.transaction_date,
            t.amount,
            t.currency,
            t.transaction_type,
            t.status,
            t.order_number
        FROM transactions t
        WHERE t.contact_id::text = %s
          AND t.source_system = 'paypal'
          AND t.transaction_date > %s
          AND t.deleted_at IS NULL
          AND t.transaction_type IN ('subscription', 'purchase')
          AND t.status = 'completed'
        ORDER BY t.transaction_date DESC
    """, (contact_id, sub['kajabi_canceled']))

    post_cancel_transactions = cur.fetchall()

    if post_cancel_transactions:
        print(f"    🚨 FOUND {len(post_cancel_transactions)} PAYMENT(S) AFTER CANCELLATION!")
        print()

        total_charged = sum(float(t['amount']) for t in post_cancel_transactions)
        total_post_cancel_charges += len(post_cancel_transactions)
        total_amount_charged += total_charged

        print(f"    Transactions after {sub['kajabi_canceled']}:")
        for txn in post_cancel_transactions:
            print(f"       • {txn['transaction_date'].strftime('%Y-%m-%d')}: ${txn['amount']} {txn['currency']} ({txn['transaction_type']})")

        print()
        print(f"    Total charged after cancellation: ${total_charged:.2f}")
        print(f"    ⚠️  THIS PERSON IS STILL BEING CHARGED ON PAYPAL!")

    else:
        print(f"    ✅ NO CHARGES after {sub['kajabi_canceled']}")
        print(f"    PayPal subscription appears to be inactive (no recent charges)")

    print()
    print()

print("=" * 120)
print()
print("SUMMARY")
print("=" * 120)
print()

if total_post_cancel_charges > 0:
    print(f"🚨 CRITICAL ISSUE FOUND:")
    print(f"   {total_post_cancel_charges} payment(s) charged AFTER Kajabi cancellation")
    print(f"   Total amount: ${total_amount_charged:.2f}")
    print()
    print(f"RECOMMENDATION:")
    print(f"   1. Update these PayPal subscriptions to 'canceled' status in database")
    print(f"   2. Contact these customers - they may be owed refunds!")
    print(f"   3. Cancel the PayPal subscriptions in PayPal dashboard to stop future charges")
else:
    print(f"✅ GOOD NEWS:")
    print(f"   No payments found after Kajabi cancellation dates")
    print(f"   PayPal subscriptions appear to have stopped billing")
    print()
    print(f"RECOMMENDATION:")
    print(f"   Update database to mark these subscriptions as 'canceled' for accuracy")

print()
print("=" * 120)
print()

cur.close()
conn.close()
