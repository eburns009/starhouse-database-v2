import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("DATABASE STRUCTURE ANALYSIS")
print("=" * 80)

# 1. Check subscriptions table schema
print("\n1. SUBSCRIPTIONS TABLE SCHEMA:")
sub = supabase.table('subscriptions').select('*').limit(1).execute().data[0]
print(f"   Columns: {', '.join(sub.keys())}")
print(f"\n   Key fields:")
print(f"     - product_id: {sub.get('product_id')}")
print(f"     - membership_product_id: {sub.get('membership_product_id')}")

# 2. Check if products table exists
print("\n2. PRODUCTS TABLE:")
try:
    products = supabase.table('products').select('*').limit(1).execute().data
    if products:
        print(f"   ✓ Products table exists")
        print(f"   Columns: {', '.join(products[0].keys())}")
        total = supabase.table('products').select('id', count='exact').execute().count
        print(f"   Total products: {total}")
except Exception as e:
    print(f"   ✗ Error accessing products table: {e}")

# 3. Check if membership_products table exists
print("\n3. MEMBERSHIP_PRODUCTS TABLE:")
try:
    membership_products = supabase.table('membership_products').select('*').limit(1).execute().data
    if membership_products:
        print(f"   ✓ Membership_products table exists")
        print(f"   Columns: {', '.join(membership_products[0].keys())}")
        total = supabase.table('membership_products').select('id', count='exact').execute().count
        print(f"   Total membership products: {total}")
except Exception as e:
    print(f"   ✗ Error accessing membership_products table: {e}")

# 4. Analyze the relationships
print("\n4. RELATIONSHIP ANALYSIS:")

# Count subscriptions with product_id
subs_with_product_id = supabase.table('subscriptions').select('id', count='exact').not_.is_('product_id', 'null').execute().count
subs_with_membership_product_id = supabase.table('subscriptions').select('id', count='exact').not_.is_('membership_product_id', 'null').execute().count
total_subs = supabase.table('subscriptions').select('id', count='exact').execute().count

print(f"   Total subscriptions: {total_subs}")
print(f"   Subscriptions with product_id: {subs_with_product_id}")
print(f"   Subscriptions with membership_product_id: {subs_with_membership_product_id}")

# 5. Check what the CSV import file has
print("\n5. ANALYZING CSV IMPORT FILE:")
import csv
csv_file = "kajabi 3 files review/subscriptions (1).csv"
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    sample = next(reader)
    print(f"   CSV columns: {', '.join(sample.keys())}")
    print(f"\n   Sample data:")
    print(f"     Offer ID: {sample.get('Offer ID')}")
    print(f"     Offer Title: {sample.get('Offer Title')}")

# 6. Check if we can map Offer Title to products
print("\n6. CHECKING PRODUCT MAPPING:")
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    offer_titles = set()
    for row in reader:
        if row.get('Offer Title'):
            offer_titles.add(row['Offer Title'])

print(f"   Unique Offer Titles in CSV: {len(offer_titles)}")
print(f"   Sample offer titles:")
for i, title in enumerate(sorted(offer_titles)[:10], 1):
    print(f"     {i}. {title}")

# Check how many products match these titles
products_list = supabase.table('products').select('*').execute().data
product_names = {p.get('name') for p in products_list if p.get('name')}

matches = offer_titles.intersection(product_names)
print(f"\n   Products matching CSV titles: {len(matches)}")
if matches:
    print(f"   Examples:")
    for title in sorted(matches)[:5]:
        print(f"     - {title}")

print("\n" + "=" * 80)
print("ROOT CAUSE SUMMARY")
print("=" * 80)

print("\n🔍 FINDINGS:")
print("1. subscriptions table has NO product_name column (by design)")
print("2. subscriptions table has product_id and membership_product_id columns")
print("3. CSV import file has 'Offer Title' with product names")
print("4. Import script did NOT map Offer Title to product_id or product_name")
print("5. Import script only tried to map to membership_product_id (which failed for most)")

print("\n💡 ROOT CAUSE:")
print("The import script (import_kajabi_subscriptions.py) does NOT:")
print("  - Add a product_name column")
print("  - Populate product_id from the 'Offer Title' field")
print("  - Store the product name anywhere accessible")
print("\nThe script only tries to find membership_product_id, which doesn't exist for most offers.")

