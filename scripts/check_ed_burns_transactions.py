#!/usr/bin/env python3
"""
Check Ed Burns transactions to identify what the purchase is
"""

import os
from supabase import create_client

# Initialize Supabase client
supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("Error: Supabase credentials not found")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# Find Ed Burns
print("Looking up Ed Burns (eburns009@gmail.com)...\n")
contact = supabase.table('contacts').select('*').eq('email', 'eburns009@gmail.com').execute()

if not contact.data:
    print("Contact not found!")
    exit(1)

contact_id = contact.data[0]['id']
print(f"Found: {contact.data[0]['first_name']} {contact.data[0]['last_name']}")
print(f"Contact ID: {contact_id}\n")

# Get transactions with product info
print("Fetching transactions...\n")
transactions = supabase.table('transactions').select(
    '*, products(name, product_type), subscriptions(id, products(name, product_type))'
).eq('contact_id', contact_id).order('transaction_date', desc=True).execute()

if not transactions.data:
    print("No transactions found!")
    exit(0)

print(f"Found {len(transactions.data)} transaction(s):\n")
print("-" * 100)

for idx, txn in enumerate(transactions.data, 1):
    print(f"\nTransaction {idx}:")
    print(f"  ID: {txn['id']}")
    print(f"  Type: {txn['transaction_type']}")
    print(f"  Status: {txn['status']}")
    print(f"  Amount: ${txn['amount']} {txn['currency']}")
    print(f"  Date: {txn['transaction_date']}")
    print(f"  Product ID: {txn.get('product_id', 'None')}")
    print(f"  Subscription ID: {txn.get('subscription_id', 'None')}")

    # Check for product info
    if txn.get('products'):
        print(f"  ✅ Direct Product: {txn['products']['name']} ({txn['products']['product_type']})")
    elif txn.get('subscriptions') and txn['subscriptions'].get('products'):
        print(f"  ✅ Subscription Product: {txn['subscriptions']['products']['name']}")
    else:
        print(f"  ❌ No product information found")

    print(f"  Payment Method: {txn.get('payment_method', 'Unknown')}")
    print("-" * 100)
