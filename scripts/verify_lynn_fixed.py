import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("FINAL VERIFICATION: Lynn Amber Ryan")
print("=" * 80)

# Get Lynn
lynn = supabase.table('contacts').select('*').eq('email', 'amber@the360emergence.com').single().execute().data

print(f"\n✓ Contact: {lynn['first_name']} {lynn['last_name']}")
print(f"  Email: {lynn['email']}")
print(f"  Kajabi ID: {lynn.get('kajabi_id')}")
print(f"  Source: {lynn.get('source_system')}")

# Get subscriptions with product JOIN
subs = supabase.table('subscriptions').select('*, products(name, product_type)').eq('contact_id', lynn['id']).execute().data

print(f"\n📋 SUBSCRIPTIONS: {len(subs)}")

for i, sub in enumerate(subs, 1):
    print(f"\n  Subscription {i}:")
    print(f"    Kajabi Sub ID: {sub.get('kajabi_subscription_id')}")
    print(f"    Status: {sub.get('status')}")
    print(f"    Amount: ${sub.get('amount')} / {sub.get('billing_cycle')}")
    print(f"    Product ID: {sub.get('product_id')}")
    
    if sub.get('products'):
        product = sub['products']
        print(f"    ✅ Product: {product.get('name')} ({product.get('product_type')})")
    else:
        print(f"    ❌ NO PRODUCT LINKED")

# Check active subscriptions
active_subs = [s for s in subs if s.get('status') == 'active']

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

print(f"\n✅ SUCCESS INDICATORS:")
print(f"  ✓ Total subscriptions: {len(subs)} (down from 2)")
print(f"  ✓ Active subscriptions: {len(active_subs)}")
print(f"  ✓ All subscriptions have product_id: {all(s.get('product_id') for s in subs)}")
print(f"  ✓ All active have product: {all(s.get('products') for s in active_subs)}")

if len(active_subs) == 1 and active_subs[0].get('products'):
    print(f"\n🎉 Lynn Amber Ryan is FIXED!")
    print(f"  - Has 1 active subscription (was 2)")
    print(f"  - Product: {active_subs[0]['products']['name']}")
    print(f"  - Product ID: {active_subs[0].get('product_id')}")
    print(f"  - Should now appear in UI!")
else:
    print(f"\n⚠️  Issue detected:")
    print(f"  - Expected 1 active subscription, found {len(active_subs)}")

