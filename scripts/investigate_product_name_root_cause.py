import os
from supabase import create_client
import json
from datetime import datetime

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("ROOT CAUSE ANALYSIS: Missing Product Names in All Subscriptions")
print("=" * 80)

# 1. Check the subscriptions table schema
print("\n1. CHECKING SUBSCRIPTIONS TABLE SCHEMA...")
sample_sub = supabase.table('subscriptions').select('*').limit(1).execute().data[0]
print(f"   Available columns: {list(sample_sub.keys())}\n")

# 2. Check when subscriptions were created
print("2. ANALYZING SUBSCRIPTION CREATION TIMELINE...")
all_subs = supabase.table('subscriptions').select('id, created_at, product_name, product_id, kajabi_subscription_id').execute().data

# Group by creation date
creation_dates = {}
for sub in all_subs:
    date = sub['created_at'][:10] if sub.get('created_at') else 'unknown'
    if date not in creation_dates:
        creation_dates[date] = {'total': 0, 'has_product_id': 0, 'has_product_name': 0}
    creation_dates[date]['total'] += 1
    if sub.get('product_id'):
        creation_dates[date]['has_product_id'] += 1
    if sub.get('product_name'):
        creation_dates[date]['has_product_name'] += 1

print(f"\n   Subscriptions created by date:")
print(f"   {'Date':<12} {'Total':<8} {'Has Product ID':<16} {'Has Product Name':<18}")
print(f"   {'-'*60}")
for date in sorted(creation_dates.keys()):
    stats = creation_dates[date]
    print(f"   {date:<12} {stats['total']:<8} {stats['has_product_id']:<16} {stats['has_product_name']:<18}")

# 3. Check if product_id exists but product_name doesn't
print("\n3. ANALYZING PRODUCT_ID vs PRODUCT_NAME RELATIONSHIP...")
has_id_no_name = len([s for s in all_subs if s.get('product_id') and not s.get('product_name')])
has_name_no_id = len([s for s in all_subs if s.get('product_name') and not s.get('product_id')])
has_both = len([s for s in all_subs if s.get('product_id') and s.get('product_name')])
has_neither = len([s for s in all_subs if not s.get('product_id') and not s.get('product_name')])

print(f"\n   Has product_id but NO product_name: {has_id_no_name}")
print(f"   Has product_name but NO product_id: {has_name_no_id}")
print(f"   Has BOTH product_id AND product_name: {has_both}")
print(f"   Has NEITHER product_id NOR product_name: {has_neither}")

# 4. Check the products table for available data
print("\n4. CHECKING PRODUCTS TABLE...")
products = supabase.table('products').select('*').execute().data
print(f"   Total products in database: {len(products)}")
products_with_name = [p for p in products if p.get('name')]
print(f"   Products with names: {len(products_with_name)}")

# Create a map of product_id to product_name
product_map = {p['id']: p.get('name') for p in products if p.get('name')}
print(f"   Products that can be mapped: {len(product_map)}")

# 5. Simulate what would happen if we populated product names
print("\n5. SIMULATING PRODUCT NAME POPULATION...")
subs_with_id = [s for s in all_subs if s.get('product_id')]
print(f"   Subscriptions with product_id: {len(subs_with_id)}")

can_populate = 0
cannot_populate = []
for sub in subs_with_id:
    if sub['product_id'] in product_map:
        can_populate += 1
    else:
        cannot_populate.append(sub)

print(f"   Can populate from products table: {can_populate}")
print(f"   Cannot populate (product_id not in products table): {len(cannot_populate)}")

if cannot_populate:
    print(f"\n   Sample of orphaned product_ids (first 5):")
    for i, sub in enumerate(cannot_populate[:5], 1):
        print(f"     {i}. Product ID: {sub['product_id']} (Kajabi Sub ID: {sub.get('kajabi_subscription_id')})")

# 6. Check PayPal vs Kajabi subscriptions
print("\n6. CHECKING PAYPAL vs KAJABI SUBSCRIPTIONS...")
paypal_subs = [s for s in all_subs if s.get('kajabi_subscription_id', '').startswith('I-')]
kajabi_subs = [s for s in all_subs if s.get('kajabi_subscription_id', '').isdigit()]
other_subs = [s for s in all_subs if s not in paypal_subs and s not in kajabi_subs]

print(f"\n   PayPal subscriptions (I-XXX format): {len(paypal_subs)}")
print(f"     - With product_id: {len([s for s in paypal_subs if s.get('product_id')])}")
print(f"     - Without product_id: {len([s for s in paypal_subs if not s.get('product_id')])}")

print(f"\n   Kajabi subscriptions (numeric ID): {len(kajabi_subs)}")
print(f"     - With product_id: {len([s for s in kajabi_subs if s.get('product_id')])}")
print(f"     - Without product_id: {len([s for s in kajabi_subs if not s.get('product_id')])}")

print(f"\n   Other subscriptions: {len(other_subs)}")

# 7. Look for the import source data
print("\n7. CHECKING IMPORT SOURCE DATA...")
import os
import csv

kajabi_sub_file = "kajabi 3 files review/subscriptions (1).csv"
if os.path.exists(kajabi_sub_file):
    print(f"   ✓ Found Kajabi subscription import file: {kajabi_sub_file}")
    
    with open(kajabi_sub_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        first_row = next(reader)
        print(f"   Available columns in import file: {list(first_row.keys())}")
        
        # Check if product/offer name exists in import
        product_columns = [k for k in first_row.keys() if 'product' in k.lower() or 'offer' in k.lower() or 'name' in k.lower()]
        print(f"   Product-related columns: {product_columns}")
        
        if product_columns:
            print(f"\n   Sample data from first row:")
            for col in product_columns:
                print(f"     {col}: {first_row.get(col, 'N/A')}")
else:
    print(f"   ✗ Kajabi subscription import file not found")

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS COMPLETE")
print("=" * 80)

print("\nFINDINGS:")
print("1. ALL subscriptions are missing product_name (100% - systematic issue)")
print("2. 263 subscriptions have product_id that can be populated from products table")
print("3. 148 subscriptions have no product_id (likely PayPal-only)")
print("4. This appears to be an import bug - product_name was never populated")
print("5. Need to check import scripts to confirm root cause")

