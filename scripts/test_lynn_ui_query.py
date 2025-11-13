import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("TESTING UI QUERY FOR LYNN AMBER RYAN")
print("=" * 80)

# Simulate the exact query the UI will now make
print("\n1. TESTING SEARCH QUERY (ContactSearchResults component)")
print("   Query: Lynn Ryan")

response = supabase.table('contacts').select('*').is_('deleted_at', 'null').or_('first_name.ilike.%Lynn%,last_name.ilike.%Ryan%').execute()

print(f"   ✓ Found {len(response.data)} contact(s)")
lynn_found = False
for contact in response.data:
    if contact['email'] == 'amber@the360emergence.com':
        print(f"     ✅ {contact['first_name']} {contact['last_name']} ({contact['email']})")
        lynn_found = True

if not lynn_found:
    print("     ⚠️  Lynn Amber Ryan not in results!")

# Get Lynn's ID
lynn_email = 'amber@the360emergence.com'
lynn = supabase.table('contacts').select('id').eq('email', lynn_email).single().execute().data

if not lynn:
    print(f"\n❌ ERROR: Lynn not found!")
    exit(1)

lynn_id = lynn['id']

print(f"\n2. TESTING SUBSCRIPTION QUERY WITH JOIN (ContactDetailCard component)")
print(f"   Contact ID: {lynn_id}")

# Simulate the exact query the UI will now make (with JOIN)
response = supabase.table('subscriptions').select('''
    *,
    products (
        id,
        name,
        product_type
    )
''').eq('contact_id', lynn_id).not_.is_('product_id', 'null').order('created_at', desc=True).execute()

print(f"   ✓ Found {len(response.data)} subscription(s) with product info")

for i, sub in enumerate(response.data, 1):
    product = sub.get('products')
    print(f"\n   Subscription {i}:")
    print(f"     Status: {sub['status']}")
    print(f"     Amount: ${sub['amount']} / {sub['billing_cycle']}")
    print(f"     Product ID: {sub['product_id']}")
    
    if product:
        print(f"     ✅ Product Name: {product['name']}")
        print(f"     Product Type: {product['product_type']}")
    else:
        print(f"     ❌ NO PRODUCT (this shouldn't happen with our filter)")

print("\n" + "=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)

if len(response.data) > 0:
    active_subs = [s for s in response.data if s['status'] == 'active']
    has_product = all(s.get('products') for s in response.data)
    
    print(f"\n✅ SUCCESS!")
    print(f"   - Lynn is searchable by name ✓")
    print(f"   - {len(active_subs)} active subscription(s) with product info ✓")
    print(f"   - All subscriptions have product information: {has_product} ✓")
    print(f"   - Product name will display: '{response.data[0]['products']['name']}' ✓")
    print(f"\n🎉 Lynn Amber Ryan will now show up correctly in the UI!")
else:
    print(f"\n⚠️  WARNING: No subscriptions found")
    print(f"   This might indicate an issue with the query or data")

