#!/usr/bin/env python3
"""
Verify UI Display: Check what transaction data UI receives
Shows exactly what will be displayed in the interface
"""

import os
from supabase import create_client

supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("Error: Supabase credentials not found")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# Find Ed Burns
print("Checking Ed Burns transaction display data...\n")
contact = supabase.table('contacts').select('id, first_name, last_name, email').eq(
    'email', 'eburns009@gmail.com'
).execute()

if not contact.data:
    print("Contact not found!")
    exit(1)

contact_id = contact.data[0]['id']
print(f"Contact: {contact.data[0]['first_name']} {contact.data[0]['last_name']}")
print(f"Email: {contact.data[0]['email']}\n")

# Simulate exact UI query
print("="*80)
print("SIMULATING UI QUERY (What the frontend receives)")
print("="*80)

transactions = supabase.table('transactions').select('''
    *,
    products (
      name,
      product_type
    ),
    subscriptions (
      id,
      products (
        name,
        product_type
      )
    )
''').eq('contact_id', contact_id).order('transaction_date', desc=True).limit(5).execute()

print(f"\nFound {len(transactions.data)} transactions\n")

for idx, txn in enumerate(transactions.data, 1):
    print(f"Transaction {idx}:")
    print(f"  Transaction Type: {txn['transaction_type']}")
    print(f"  Amount: ${txn['amount']} {txn['currency']}")
    print(f"  Date: {txn['transaction_date']}")

    # Check what data is available
    print(f"\n  Data Available:")
    print(f"    product_id: {txn.get('product_id', 'NULL')}")
    print(f"    subscription_id: {txn.get('subscription_id', 'NULL')}")
    print(f"    offer_id (for matching): {txn.get('offer_id', 'NULL')}")

    # Simulate getTransactionDisplayName() function
    direct_product = txn.get('products', {}).get('name') if txn.get('products') else None
    subscription_product = None
    if txn.get('subscriptions') and txn['subscriptions'].get('products'):
        subscription_product = txn['subscriptions']['products'].get('name')

    # This is exactly what the UI displays
    display_name = (
        direct_product or
        subscription_product or
        txn['transaction_type'].replace('_', ' ')
    )

    print(f"\n  🎨 UI DISPLAYS: '{display_name}'")

    if display_name == txn['transaction_type'].replace('_', ' '):
        print(f"  ⚠️  SHOWING FALLBACK (no product linked)")
        print(f"  ✅ AFTER MIGRATION WILL SHOW: Product name from offer_id {txn.get('offer_id')}")
    else:
        print(f"  ✅ SHOWING PRODUCT NAME (already linked)")

    print("-" * 80)

print("\nSUMMARY:")
print("- Transactions with product_id populated → Show product name")
print("- Transactions without product_id → Show 'purchase', 'subscription', etc.")
print("\n💡 Solution: Run migration script to populate product_id from offer_id")
