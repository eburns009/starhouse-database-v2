#!/usr/bin/env python3
"""Show the 11 PayPal-only subscriptions that were preserved"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 120)
print("PAYPAL-ONLY SUBSCRIPTIONS (11 Preserved)")
print("=" * 120)
print()

# Get PayPal-only subscriptions (active ones with PayPal ID in kajabi field)
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
        s.currency,
        s.billing_cycle,
        s.start_date,
        s.payment_processor,
        s.membership_product_id,
        s.created_at,
        s.updated_at
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.status = 'active'
      AND s.kajabi_subscription_id LIKE 'I-%'
      AND s.paypal_subscription_reference = s.kajabi_subscription_id
    ORDER BY c.email
""")

subscriptions = cur.fetchall()

print(f"Found {len(subscriptions)} PayPal-only active subscriptions\n")
print("=" * 120)
print()

for i, sub in enumerate(subscriptions, 1):
    print(f"#{i}. {sub['contact_name']} ({sub['email']})")
    print(f"    {'─' * 112}")
    print(f"    Subscription ID:     {sub['id']}")
    print(f"    PayPal Reference:    {sub['paypal_subscription_reference']}")
    print(f"    Status:              {sub['status']}")
    print(f"    Amount:              ${sub['amount']} {sub['currency']}")
    print(f"    Billing Cycle:       {sub['billing_cycle']}")
    print(f"    Payment Processor:   {sub['payment_processor']}")
    print(f"    Start Date:          {sub['start_date'].strftime('%Y-%m-%d') if sub['start_date'] else 'N/A'}")
    print(f"    Created:             {sub['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check if there's a membership_product_id
    if sub['membership_product_id']:
        print(f"    📦 PRODUCT:")
        print(f"       Product ID:       {sub['membership_product_id']}")

        # Try to get product details if membership_products table exists
        try:
            cur.execute("""
                SELECT * FROM membership_products WHERE id = %s
            """, (sub['membership_product_id'],))
            product = cur.fetchone()
            if product:
                # Print all available columns
                print(f"       Product Details:  {dict(product)}")
        except Exception as e:
            print(f"       (Could not fetch product details: {e})")
    else:
        print(f"    📦 PRODUCT: None (no membership_product_id)")

    # Check for other subscriptions for this contact
    cur.execute("""
        SELECT COUNT(*) as count
        FROM subscriptions
        WHERE contact_id = %s
          AND deleted_at IS NULL
          AND status = 'active'
    """, (sub['contact_id'],))
    total_subs = cur.fetchone()['count']

    if total_subs > 1:
        print(f"    ⚠️  Contact has {total_subs} total active subscriptions")

    print()
    print()

print("=" * 120)
print()

# Summary by amount and billing cycle
print("SUMMARY BY AMOUNT & BILLING CYCLE:")
print("-" * 120)

cur.execute("""
    SELECT
        amount,
        billing_cycle,
        COUNT(*) as subscription_count,
        STRING_AGG(c.email, ', ') as emails
    FROM subscriptions s
    JOIN contacts c ON s.contact_id = c.id
    WHERE s.deleted_at IS NULL
      AND s.status = 'active'
      AND s.kajabi_subscription_id LIKE 'I-%'
      AND s.paypal_subscription_reference = s.kajabi_subscription_id
    GROUP BY amount, billing_cycle
    ORDER BY amount DESC, billing_cycle
""")

summary = cur.fetchall()

for row in summary:
    print(f"\n${row['amount']} / {row['billing_cycle']}")
    print(f"  Count: {row['subscription_count']} subscription(s)")
    print(f"  Emails: {row['emails'][:100]}{'...' if len(row['emails']) > 100 else ''}")

print()
print("=" * 120)
print()

cur.close()
conn.close()
