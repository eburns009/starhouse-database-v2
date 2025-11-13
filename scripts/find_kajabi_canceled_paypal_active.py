#!/usr/bin/env python3
"""
Find all cases where Kajabi subscription is canceled but PayPal is still charging
(comprehensive - checks all contacts, not just the 11 PayPal-only ones)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 120)
print("KAJABI CANCELED + PAYPAL ACTIVE ANALYSIS")
print("Finding cases where Kajabi is canceled but PayPal transactions continue")
print("=" * 120)
print()

# Get all canceled Kajabi subscriptions
cur.execute("""
    SELECT
        s.id as subscription_id,
        s.contact_id,
        c.email,
        c.first_name || ' ' || c.last_name as contact_name,
        s.kajabi_subscription_id,
        s.status,
        s.amount,
        s.billing_cycle,
        s.start_date,
        s.updated_at
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.status IN ('canceled', 'expired')
      AND s.kajabi_subscription_id IS NOT NULL
      AND s.kajabi_subscription_id NOT LIKE 'I-%%'
    ORDER BY s.updated_at DESC
""")

canceled_kajabi_subs = cur.fetchall()

print(f"Found {len(canceled_kajabi_subs)} canceled/expired Kajabi subscriptions")
print()
print("Checking for continued PayPal billing...")
print()

issues = []
total_post_cancel_charges = 0
total_amount_charged = 0.0

for i, sub in enumerate(canceled_kajabi_subs):
    cancellation_date = sub['updated_at'].date()
    contact_id = str(sub['contact_id'])

    # Check for PayPal transactions AFTER cancellation with matching amount
    cur.execute("""
        SELECT
            t.id,
            t.external_transaction_id,
            t.transaction_date,
            t.amount,
            t.currency,
            t.transaction_type,
            t.status
        FROM transactions t
        WHERE t.contact_id::text = %s
          AND t.source_system = 'paypal'
          AND t.transaction_date::date > %s
          AND t.deleted_at IS NULL
          AND t.transaction_type IN ('subscription', 'purchase')
          AND t.status = 'completed'
          AND ABS(t.amount - %s) <= 1.0
        ORDER BY t.transaction_date DESC
    """, (contact_id, cancellation_date, float(sub['amount'])))

    post_cancel_txns = cur.fetchall()

    if post_cancel_txns:
        # Check if there's an active PayPal subscription for this contact
        cur.execute("""
            SELECT
                id,
                kajabi_subscription_id,
                paypal_subscription_reference,
                status,
                amount,
                billing_cycle
            FROM subscriptions
            WHERE contact_id::text = %s
              AND deleted_at IS NULL
              AND status = 'active'
              AND (
                  paypal_subscription_reference IS NOT NULL
                  OR (kajabi_subscription_id LIKE 'I-%%')
              )
              AND ABS(amount - %s) <= 1.0
        """, (contact_id, float(sub['amount'])))

        active_paypal_subs = cur.fetchall()

        total_charged = sum(float(t['amount']) for t in post_cancel_txns)

        issues.append({
            'kajabi_subscription': sub,
            'paypal_subscriptions': active_paypal_subs,
            'transactions': post_cancel_txns,
            'total_charged': total_charged,
            'cancellation_date': cancellation_date
        })

        total_post_cancel_charges += len(post_cancel_txns)
        total_amount_charged += total_charged

    if (i + 1) % 50 == 0:
        print(f"  Checked {i + 1}/{len(canceled_kajabi_subs)} subscriptions...", end='\r')

print(f"\n✓ Checked all {len(canceled_kajabi_subs)} canceled Kajabi subscriptions")
print()
print("=" * 120)
print()

if issues:
    print(f"🚨 FOUND {len(issues)} CASE(S) WHERE KAJABI IS CANCELED BUT PAYPAL IS STILL CHARGING!")
    print()
    print("=" * 120)
    print()

    # Sort by total charged
    issues.sort(key=lambda x: x['total_charged'], reverse=True)

    for i, issue in enumerate(issues, 1):
        kajabi_sub = issue['kajabi_subscription']
        paypal_subs = issue['paypal_subscriptions']
        txns = issue['transactions']

        print(f"#{i}. {kajabi_sub['contact_name']} ({kajabi_sub['email']})")
        print(f"    {'─' * 112}")
        print()
        print(f"    KAJABI SUBSCRIPTION (CANCELED):")
        print(f"      ID:                {kajabi_sub['subscription_id']}")
        print(f"      Kajabi Sub ID:     {kajabi_sub['kajabi_subscription_id']}")
        print(f"      Status:            {kajabi_sub['status']}")
        print(f"      Amount:            ${kajabi_sub['amount']} / {kajabi_sub['billing_cycle']}")
        print(f"      Canceled:          {issue['cancellation_date']}")
        print()

        if paypal_subs:
            print(f"    PAYPAL SUBSCRIPTION(S) (STILL ACTIVE IN DB):")
            for ps in paypal_subs:
                print(f"      ID:                {ps['id']}")
                print(f"      PayPal Ref:        {ps['paypal_subscription_reference'] or ps['kajabi_subscription_id']}")
                print(f"      Status:            {ps['status']} ⚠️")
                print(f"      Amount:            ${ps['amount']} / {ps['billing_cycle']}")
                print()

        print(f"    PAYPAL CHARGES AFTER KAJABI CANCELLATION ({len(txns)} payments):")
        for txn in txns:
            print(f"      • {txn['transaction_date'].strftime('%Y-%m-%d')}: ${txn['amount']} {txn['currency']}")
        print()
        print(f"    Total charged after cancellation: ${issue['total_charged']:.2f}")
        print()

        if paypal_subs:
            print(f"    🔧 FIX: Update PayPal subscription(s) to 'canceled':")
            for ps in paypal_subs:
                print(f"       UPDATE subscriptions SET status = 'canceled' WHERE id = '{ps['id']}';")
        print()
        print()

    print("=" * 120)
    print()
    print("SUMMARY")
    print("=" * 120)
    print()
    print(f"🚨 BILLING DISCONNECT FOUND:")
    print(f"   {len(issues)} customer(s) with Kajabi canceled but PayPal still charging")
    print(f"   {total_post_cancel_charges} unauthorized payment(s)")
    print(f"   Total amount: ${total_amount_charged:.2f}")
    print()

    # Count active PayPal subs that need to be canceled
    paypal_subs_to_cancel = sum(len(i['paypal_subscriptions']) for i in issues)
    print(f"ACTION REQUIRED:")
    print(f"   {paypal_subs_to_cancel} PayPal subscription(s) need to be canceled in database")
    print(f"   {len(issues)} customer(s) need to be contacted")
    print(f"   ${total_amount_charged:.2f} in potential refunds")
    print()

    # Generate SQL
    print("SQL TO UPDATE DATABASE:")
    print("BEGIN;")
    for issue in issues:
        for ps in issue['paypal_subscriptions']:
            print(f"UPDATE subscriptions SET status = 'canceled', updated_at = NOW() WHERE id = '{ps['id']}';")
    print("COMMIT;")
    print()

else:
    print("✅ NO ISSUES FOUND:")
    print("   All Kajabi cancellations are properly reflected in PayPal billing")

print()
print("=" * 120)
print()

cur.close()
conn.close()
