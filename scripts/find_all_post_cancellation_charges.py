#!/usr/bin/env python3
"""
COMPREHENSIVE REVIEW: Find ALL cases where people are being charged after subscription cancellation
Checks all canceled/expired subscriptions (not just the PayPal-only ones)
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
print("COMPREHENSIVE POST-CANCELLATION CHARGE ANALYSIS")
print("Finding ALL subscriptions with charges after cancellation/expiration")
print("=" * 120)
print()

# Get all canceled or expired subscriptions
cur.execute("""
    SELECT
        s.id as subscription_id,
        s.contact_id,
        c.email,
        c.first_name || ' ' || c.last_name as contact_name,
        s.kajabi_subscription_id,
        s.paypal_subscription_reference,
        s.status,
        s.amount,
        s.billing_cycle,
        s.start_date,
        s.updated_at,
        s.created_at
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.status IN ('canceled', 'expired')
    ORDER BY s.updated_at DESC
""")

canceled_subs = cur.fetchall()

print(f"Found {len(canceled_subs)} canceled/expired subscriptions to check")
print()

# Track issues found
issues = []
total_post_cancel_charges = 0
total_amount_charged = 0.0

print("Checking each subscription for post-cancellation charges...")
print()

for i, sub in enumerate(canceled_subs):
    # Use updated_at as proxy for when it was canceled
    # (this is when the status was last changed)
    cancellation_date = sub['updated_at'].date()

    # Get contact ID
    contact_id = str(sub['contact_id'])

    # Get all PayPal transactions for this contact AFTER the cancellation
    # Look for transactions in the 30 days after cancellation (to catch the next billing cycle)
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

    post_cancel_transactions = cur.fetchall()

    if post_cancel_transactions:
        total_charged = sum(float(t['amount']) for t in post_cancel_transactions)

        issues.append({
            'subscription': sub,
            'transactions': post_cancel_transactions,
            'total_charged': total_charged,
            'cancellation_date': cancellation_date
        })

        total_post_cancel_charges += len(post_cancel_transactions)
        total_amount_charged += total_charged

    # Progress indicator
    if (i + 1) % 50 == 0:
        print(f"  Checked {i + 1}/{len(canceled_subs)} subscriptions...", end='\r')

print(f"\n✓ Checked all {len(canceled_subs)} canceled/expired subscriptions")
print()
print("=" * 120)
print()

if issues:
    print(f"🚨 FOUND {len(issues)} SUBSCRIPTION(S) WITH POST-CANCELLATION CHARGES!")
    print()
    print("=" * 120)
    print()

    # Sort by total charged (highest first)
    issues.sort(key=lambda x: x['total_charged'], reverse=True)

    for i, issue in enumerate(issues, 1):
        sub = issue['subscription']
        txns = issue['transactions']

        print(f"#{i}. {sub['contact_name']} ({sub['email']})")
        print(f"    {'─' * 112}")
        print(f"    Subscription ID:         {sub['subscription_id']}")
        print(f"    Kajabi Sub ID:           {sub['kajabi_subscription_id'] or 'NULL'}")
        print(f"    PayPal Reference:        {sub['paypal_subscription_reference'] or 'NULL'}")
        print(f"    Status:                  {sub['status']}")
        print(f"    Amount:                  ${sub['amount']} / {sub['billing_cycle']}")
        print(f"    Cancellation Date:       {issue['cancellation_date']}")
        print()
        print(f"    🚨 {len(txns)} PAYMENT(S) AFTER CANCELLATION:")
        print()

        for txn in txns:
            print(f"       • {txn['transaction_date'].strftime('%Y-%m-%d')}: ${txn['amount']} {txn['currency']} ({txn['transaction_type']})")

        print()
        print(f"    Total charged after cancellation: ${issue['total_charged']:.2f}")
        print()
        print()

    print("=" * 120)
    print()
    print("SUMMARY")
    print("=" * 120)
    print()
    print(f"🚨 CRITICAL BILLING ISSUES FOUND:")
    print(f"   {len(issues)} subscription(s) with charges after cancellation")
    print(f"   {total_post_cancel_charges} unauthorized payment(s)")
    print(f"   Total amount: ${total_amount_charged:.2f}")
    print()

    # Break down by severity
    severe = [i for i in issues if i['total_charged'] > 200]
    moderate = [i for i in issues if 50 < i['total_charged'] <= 200]
    minor = [i for i in issues if i['total_charged'] <= 50]

    print(f"SEVERITY BREAKDOWN:")
    print(f"   Severe (>$200):    {len(severe)} customers, ${sum(i['total_charged'] for i in severe):.2f}")
    print(f"   Moderate ($50-200): {len(moderate)} customers, ${sum(i['total_charged'] for i in moderate):.2f}")
    print(f"   Minor (<$50):      {len(minor)} customers, ${sum(i['total_charged'] for i in minor):.2f}")
    print()

    print(f"IMMEDIATE ACTIONS REQUIRED:")
    print(f"   1. Cancel these PayPal subscriptions IMMEDIATELY in PayPal dashboard")
    print(f"   2. Contact all {len(issues)} affected customers")
    print(f"   3. Process refunds totaling ${total_amount_charged:.2f}")
    print(f"   4. Review PayPal subscription management process")
    print()

    # Export to CSV for easy review
    csv_file = 'URGENT_post_cancellation_charges.csv'
    import csv
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Contact Name', 'Email', 'Subscription ID',
            'Kajabi Sub ID', 'PayPal Reference', 'Status',
            'Amount', 'Billing Cycle', 'Cancellation Date',
            'Post-Cancel Payments', 'Total Charged After Cancel',
            'Latest Charge Date'
        ])

        for issue in issues:
            sub = issue['subscription']
            txns = issue['transactions']
            latest_charge = max(t['transaction_date'] for t in txns) if txns else None

            writer.writerow([
                sub['contact_name'],
                sub['email'],
                sub['subscription_id'],
                sub['kajabi_subscription_id'] or '',
                sub['paypal_subscription_reference'] or '',
                sub['status'],
                f"${sub['amount']}",
                sub['billing_cycle'],
                issue['cancellation_date'],
                len(txns),
                f"${issue['total_charged']:.2f}",
                latest_charge.strftime('%Y-%m-%d') if latest_charge else ''
            ])

    print(f"✓ Exported details to: {csv_file}")

else:
    print("✅ GOOD NEWS:")
    print("   No post-cancellation charges found!")
    print("   All canceled subscriptions have stopped billing correctly.")

print()
print("=" * 120)
print()

cur.close()
conn.close()
