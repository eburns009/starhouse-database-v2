#!/usr/bin/env python3
"""Check Hildy Kane's subscription history"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(get_database_url())
cur = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 120)
print("HILDY KANE - SUBSCRIPTION HISTORY")
print("=" * 120)
print()

# Get contact info
cur.execute("""
    SELECT id, email, first_name, last_name
    FROM contacts
    WHERE email ILIKE '%hildy%kane%' OR email = 'hildykane@yahoo.com'
""")
contact = cur.fetchone()

if not contact:
    print("Contact not found!")
    sys.exit(1)

print(f"Contact: {contact['first_name']} {contact['last_name']} ({contact['email']})")
print(f"Contact ID: {contact['id']}")
print()
print("=" * 120)
print()

# Get ALL subscriptions for this contact (including deleted) - minimal fields
cur.execute("""
    SELECT *
    FROM subscriptions s
    WHERE s.contact_id = %s
    ORDER BY s.created_at DESC
""", (contact['id'],))

subscriptions = cur.fetchall()

print(f"Total Subscriptions: {len(subscriptions)}")
print()

for i, sub in enumerate(subscriptions, 1):
    print(f"#{i}. Subscription ID: {sub['id']}")
    print(f"    {'─' * 112}")
    print(f"    Kajabi Sub ID:       {sub.get('kajabi_subscription_id') or 'NULL'}")
    print(f"    PayPal Reference:    {sub.get('paypal_subscription_reference') or 'NULL'}")
    print(f"    Status:              {sub.get('status')}")
    print(f"    Amount:              ${sub.get('amount')} {sub.get('currency')}")
    print(f"    Billing Cycle:       {sub.get('billing_cycle')}")
    print(f"    Payment Processor:   {sub.get('payment_processor') or 'NULL'}")
    print()
    print(f"    Start Date:          {sub['start_date'].strftime('%Y-%m-%d') if sub.get('start_date') else 'NULL'}")
    print()
    print(f"    Created:             {sub['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    Updated:             {sub['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    Deleted:             {sub['deleted_at'].strftime('%Y-%m-%d %H:%M:%S') if sub.get('deleted_at') else 'NULL'}")
    print()

    # Identify subscription type
    kajabi_id = sub.get('kajabi_subscription_id')
    paypal_ref = sub.get('paypal_subscription_reference')

    if kajabi_id and kajabi_id.startswith('I-'):
        print(f"    🏷️  TYPE: PayPal-only (PayPal ID in wrong field)")
    elif kajabi_id and not kajabi_id.startswith('I-'):
        print(f"    🏷️  TYPE: Kajabi subscription (numeric ID)")
    elif paypal_ref:
        print(f"    🏷️  TYPE: PayPal-only (correct field)")
    else:
        print(f"    🏷️  TYPE: Unknown")
    print()
    print()

print("=" * 120)
print()

# Analysis
active_subs = [s for s in subscriptions if s.get('deleted_at') is None and s.get('status') == 'active']
print(f"ANALYSIS:")
print(f"  Total subscriptions (all time): {len(subscriptions)}")
print(f"  Active subscriptions (not deleted): {len(active_subs)}")
print(f"  Deleted subscriptions: {len([s for s in subscriptions if s.get('deleted_at') is not None])}")
print()

if len(active_subs) > 1:
    print("⚠️  ISSUE: Contact has multiple active subscriptions")
    print()
    print("Active subscriptions breakdown:")
    for i, sub in enumerate(active_subs, 1):
        kajabi_id = sub.get('kajabi_subscription_id')
        sub_type = "PayPal-only" if (kajabi_id and kajabi_id.startswith('I-')) else "Kajabi"
        print(f"  {i}. {sub_type}: ${sub['amount']} {sub['billing_cycle']} (Started: {sub['start_date']})")

print()

# Check if the PayPal subscription should be cancelled
paypal_only = [s for s in active_subs if s.get('kajabi_subscription_id') and s['kajabi_subscription_id'].startswith('I-')]
if paypal_only:
    print("🔍 PayPal-only subscription found in ACTIVE status:")
    for sub in paypal_only:
        print(f"   PayPal ID: {sub['paypal_subscription_reference']}")
        print(f"   Start: {sub['start_date']}")
        print(f"   User says ended: Sep 23, 2025")
        print()
        print("   ⚠️  STATUS ISSUE: Subscription shows as 'active' but user says it ended Sep 23, 2025")
        print(f"   RECOMMENDATION: Update status to 'canceled' or 'expired'")
        print()
        print(f"   SQL to fix:")
        print(f"   UPDATE subscriptions")
        print(f"   SET status = 'canceled', updated_at = NOW()")
        print(f"   WHERE id = '{sub['id']}';")

print()
print("=" * 120)
print()

cur.close()
conn.close()
