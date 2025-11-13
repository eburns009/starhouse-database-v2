#!/usr/bin/env python3
"""
Review all 11 PayPal-only subscriptions to see if they should be canceled
based on having matching canceled Kajabi subscriptions
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
print("REVIEW: PayPal-Only Subscriptions - Check for Canceled Equivalents")
print("=" * 120)
print()

# Get all PayPal-only active subscriptions
cur.execute("""
    SELECT
        s.id,
        s.contact_id,
        c.email,
        c.first_name || ' ' || c.last_name as contact_name,
        s.kajabi_subscription_id,
        s.paypal_subscription_reference,
        s.status,
        s.amount,
        s.billing_cycle,
        s.start_date,
        s.created_at
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.status = 'active'
      AND s.kajabi_subscription_id LIKE 'I-%'
      AND s.paypal_subscription_reference = s.kajabi_subscription_id
    ORDER BY c.email
""")

paypal_subs = cur.fetchall()

print(f"Found {len(paypal_subs)} PayPal-only active subscriptions to review\n")
print("=" * 120)
print()

subscriptions_to_cancel = []

for i, paypal_sub in enumerate(paypal_subs, 1):
    print(f"#{i}. {paypal_sub['contact_name']} ({paypal_sub['email']})")
    print(f"    {'─' * 112}")
    print(f"    PayPal Sub ID:       {paypal_sub['id']}")
    print(f"    PayPal Reference:    {paypal_sub['paypal_subscription_reference']}")
    print(f"    Amount:              ${paypal_sub['amount']} / {paypal_sub['billing_cycle']}")
    print(f"    Start Date:          {paypal_sub['start_date']}")
    print(f"    Status:              {paypal_sub['status']}")
    print()

    # Look for matching Kajabi subscriptions for same contact
    contact_id = str(paypal_sub['contact_id'])
    cur.execute("""
        SELECT
            id,
            kajabi_subscription_id,
            status,
            amount,
            billing_cycle,
            start_date,
            created_at
        FROM subscriptions
        WHERE contact_id::text = %s
          AND deleted_at IS NULL
          AND kajabi_subscription_id IS NOT NULL
          AND kajabi_subscription_id NOT LIKE 'I-%%'
        ORDER BY created_at DESC
    """, (contact_id,))

    kajabi_subs = cur.fetchall()

    if kajabi_subs:
        print(f"    📋 Found {len(kajabi_subs)} Kajabi subscription(s) for this contact:")
        print()

        # Check if any Kajabi subs match the PayPal sub (same amount, similar billing cycle)
        matching_kajabi = []
        for k_sub in kajabi_subs:
            # Normalize billing cycles
            paypal_cycle = paypal_sub['billing_cycle'].lower()
            kajabi_cycle = k_sub['billing_cycle'].lower()

            cycle_map = {
                'month': 'monthly',
                'monthly': 'monthly',
                'year': 'annual',
                'annual': 'annual',
                'yearly': 'annual'
            }

            normalized_paypal = cycle_map.get(paypal_cycle, paypal_cycle)
            normalized_kajabi = cycle_map.get(kajabi_cycle, kajabi_cycle)

            # Check if amounts and cycles match
            amount_diff = abs(float(paypal_sub['amount']) - float(k_sub['amount']))

            if amount_diff <= 1.0 and normalized_paypal == normalized_kajabi:
                matching_kajabi.append(k_sub)

        if matching_kajabi:
            print(f"    ✅ MATCH FOUND - Kajabi subscription exists with same amount/cycle:")
            for k_sub in matching_kajabi:
                print(f"       • Kajabi ID: {k_sub['kajabi_subscription_id']}")
                print(f"         Amount: ${k_sub['amount']} / {k_sub['billing_cycle']}")
                print(f"         Status: {k_sub['status']}")
                print(f"         Start Date: {k_sub['start_date']}")

                if k_sub['status'] == 'canceled':
                    print(f"         🚨 CANCELED - PayPal sub should also be canceled!")
                elif k_sub['status'] == 'expired':
                    print(f"         ⏰ EXPIRED - PayPal sub should also be expired!")
                elif k_sub['status'] == 'active':
                    print(f"         ✅ ACTIVE - This was a duplicate (already removed in dedup)")
                print()

            # If any matching Kajabi sub is canceled/expired, mark PayPal for cancellation
            canceled_or_expired = [k for k in matching_kajabi if k['status'] in ['canceled', 'expired']]
            if canceled_or_expired:
                subscriptions_to_cancel.append({
                    'paypal_sub': paypal_sub,
                    'matching_kajabi': canceled_or_expired,
                    'reason': f"Kajabi equivalent is {canceled_or_expired[0]['status']}"
                })
        else:
            print(f"    ℹ️  NO MATCH - Kajabi subscriptions exist but different amounts/cycles:")
            for k_sub in kajabi_subs:
                amount_diff = abs(float(paypal_sub['amount']) - float(k_sub['amount']))
                print(f"       • Kajabi ID: {k_sub['kajabi_subscription_id']}")
                print(f"         Amount: ${k_sub['amount']} / {k_sub['billing_cycle']} (diff: ${amount_diff:.2f})")
                print(f"         Status: {k_sub['status']}")
            print()
            print(f"    → PayPal subscription is legitimate (different product/tier)")
    else:
        print(f"    ℹ️  NO KAJABI SUBSCRIPTIONS - This is a PayPal-only customer")
        print(f"    → PayPal subscription is legitimate")

    print()
    print()

print("=" * 120)
print()
print("SUMMARY")
print("=" * 120)
print()

if subscriptions_to_cancel:
    print(f"🚨 Found {len(subscriptions_to_cancel)} PayPal subscription(s) that should be canceled:")
    print()

    for item in subscriptions_to_cancel:
        paypal = item['paypal_sub']
        kajabi = item['matching_kajabi'][0]
        print(f"  • {paypal['contact_name']} ({paypal['email']})")
        print(f"    PayPal Sub: ${paypal['amount']} / {paypal['billing_cycle']} (Started: {paypal['start_date']})")
        print(f"    Kajabi Sub: {kajabi['status']} (Started: {kajabi['start_date']})")
        print(f"    Reason: {item['reason']}")
        print(f"    PayPal Sub ID to cancel: {paypal['id']}")
        print()

    print()
    print("SQL to fix all at once:")
    print("BEGIN;")
    for item in subscriptions_to_cancel:
        print(f"UPDATE subscriptions SET status = 'canceled', updated_at = NOW() WHERE id = '{item['paypal_sub']['id']}';")
    print("COMMIT;")
    print()
else:
    print("✅ All PayPal-only subscriptions are legitimate!")
    print("   No cancellations needed.")

print()
print("=" * 120)
print()

cur.close()
conn.close()
