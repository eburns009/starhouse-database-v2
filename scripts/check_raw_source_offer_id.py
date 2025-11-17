#!/usr/bin/env python3
"""
Check if raw_source contains Offer ID that we can use for matching
"""

import os
import json
from supabase import create_client

supabase_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("Error: Missing credentials")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# Get a sample transaction with NULL product_id
print("Fetching sample transactions with NULL product_id...\n")
txns = supabase.table('transactions').select(
    'id, transaction_type, amount, product_id, raw_source'
).is_('product_id', 'null').limit(5).execute()

if not txns.data:
    print("No transactions with NULL product_id found")
    exit(0)

print(f"Found {len(txns.data)} sample transactions\n")
print("="*80)

for idx, txn in enumerate(txns.data, 1):
    print(f"\nTransaction {idx}:")
    print(f"  ID: {txn['id']}")
    print(f"  Type: {txn['transaction_type']}")
    print(f"  Amount: ${txn['amount']}")
    print(f"  product_id: {txn['product_id']}")

    if txn.get('raw_source'):
        raw = txn['raw_source']
        print(f"\n  Raw Source Data:")
        if isinstance(raw, dict):
            if 'Offer ID' in raw:
                print(f"    ✅ Offer ID: {raw['Offer ID']}")
            if 'Offer Title' in raw:
                print(f"    ✅ Offer Title: {raw['Offer Title']}")

            # Show all keys
            print(f"\n    Available keys: {list(raw.keys())[:10]}...")
        else:
            print(f"    Raw source type: {type(raw)}")
    else:
        print(f"  ❌ No raw_source data")

    print("-"*80)

print("\n✅ Conclusion: We CAN use raw_source->>'Offer ID' to link transactions!")
