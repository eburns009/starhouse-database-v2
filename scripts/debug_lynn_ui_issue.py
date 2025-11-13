import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("DEBUGGING: Why Lynn Doesn't Show in UI")
print("=" * 80)

# 1. Check if Lynn exists at all
print("\n1. CHECKING IF CONTACT EXISTS...")
lynn_search = supabase.table('contacts').select('*').eq('email', 'amber@the360emergence.com').execute()

if not lynn_search.data:
    print("   ❌ CRITICAL: Lynn's contact record NOT FOUND!")
    print("   Email searched: amber@the360emergence.com")
    exit(1)

lynn = lynn_search.data[0]
print(f"   ✓ Contact found: {lynn['first_name']} {lynn['last_name']}")
print(f"   ID: {lynn['id']}")
print(f"   Email: {lynn['email']}")
print(f"   Deleted: {lynn.get('deleted_at')}")

# 2. Check if she's marked as deleted
if lynn.get('deleted_at'):
    print(f"\n   ⚠️  PROBLEM FOUND: Contact is marked as DELETED")
    print(f"   Deleted at: {lynn['deleted_at']}")
    print(f"   The UI filters out deleted contacts!")

# 3. Test the EXACT search query the UI uses
print("\n2. TESTING UI SEARCH QUERY (ContactSearchResults)...")
search_query = supabase.table('contacts').select('*').is_('deleted_at', 'null').or_('first_name.ilike.%Lynn%,last_name.ilike.%Ryan%')
search_results = search_query.execute()

lynn_in_results = False
for contact in search_results.data:
    if contact['email'] == 'amber@the360emergence.com':
        lynn_in_results = True
        print(f"   ✓ Lynn found in search results")
        break

if not lynn_in_results:
    print(f"   ❌ Lynn NOT in search results")
    print(f"   This is why she doesn't show up!")
    print(f"\n   Checking why...")
    
    # Check the filter conditions
    print(f"   - deleted_at is null: {lynn.get('deleted_at') is None}")
    print(f"   - first_name contains 'Lynn': {'lynn' in lynn.get('first_name', '').lower()}")
    print(f"   - last_name contains 'Ryan': {'ryan' in lynn.get('last_name', '').lower()}")

# 4. Check subscriptions with the EXACT UI query
print("\n3. TESTING UI SUBSCRIPTION QUERY (ContactDetailCard)...")
contact_id = lynn['id']

# This is EXACTLY what the UI queries
subs_query = supabase.table('subscriptions').select('''
    *,
    products (
        id,
        name,
        product_type
    )
''').eq('contact_id', contact_id).not_.is_('product_id', 'null').order('created_at', desc=True)

subs_result = subs_query.execute()

print(f"   Query returned: {len(subs_result.data)} subscription(s)")

if len(subs_result.data) == 0:
    print(f"   ❌ NO SUBSCRIPTIONS RETURNED")
    print(f"\n   Checking why...")
    
    # Get ALL subscriptions without filter
    all_subs = supabase.table('subscriptions').select('*').eq('contact_id', contact_id).execute()
    print(f"   Total subscriptions (no filter): {len(all_subs.data)}")
    
    for sub in all_subs.data:
        print(f"\n   Subscription {sub['id'][:8]}...")
        print(f"     - status: {sub.get('status')}")
        print(f"     - product_id: {sub.get('product_id')}")
        print(f"     - amount: ${sub.get('amount')}")
        print(f"     - Passes filter (product_id not null): {sub.get('product_id') is not None}")
else:
    print(f"   ✓ Subscriptions returned")
    for i, sub in enumerate(subs_result.data, 1):
        print(f"\n   Subscription {i}:")
        print(f"     Status: {sub.get('status')}")
        print(f"     Amount: ${sub.get('amount')}")
        print(f"     Product ID: {sub.get('product_id')}")
        
        product = sub.get('products')
        if product:
            print(f"     ✓ Product: {product.get('name')}")
        else:
            print(f"     ❌ No product data (JOIN failed)")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if lynn.get('deleted_at'):
    print("\n🔴 ROOT CAUSE: Contact is marked as DELETED")
    print(f"   deleted_at: {lynn['deleted_at']}")
    print(f"   The UI query filters: .is_('deleted_at', 'null')")
    print(f"   Solution: Un-delete the contact")
elif not lynn_in_results:
    print("\n🔴 ROOT CAUSE: Contact doesn't match search criteria")
    print(f"   UI searches for deleted_at IS NULL + name match")
    print(f"   Check if contact was accidentally soft-deleted")
elif len(subs_result.data) == 0:
    print("\n🔴 ROOT CAUSE: No subscriptions pass the filter")
    print(f"   UI filters: .not_.is_('product_id', 'null')")
    print(f"   Either no subscriptions or all have null product_id")
else:
    print("\n✅ Everything looks correct!")
    print(f"   Contact exists, searchable, has subscriptions with products")
    print(f"   UI should show Lynn correctly")
    print(f"\n   If still not showing, check:")
    print(f"   1. Browser cache - try hard refresh (Ctrl+Shift+R)")
    print(f"   2. Vercel deployment - verify it completed")
    print(f"   3. Environment variables - check SUPABASE_URL matches")

