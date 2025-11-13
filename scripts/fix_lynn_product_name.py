import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("CHECKING PRODUCT FOR LYNN'S SUBSCRIPTION")
print("=" * 80)

product_id = 'd0d9b06e-acc6-4e92-86a8-0d601ef34731'
contact_id = '8109792b-9bcb-4cef-87e4-0fb658fe372e'

# Get the product
try:
    product = supabase.table('products').select('*').eq('id', product_id).single().execute().data
    print(f"\n✓ Product Found:")
    print(f"  ID: {product['id']}")
    print(f"  Name: {product.get('name', 'N/A')}")
    print(f"  Price: ${product.get('price', product.get('amount', 'N/A'))}")
    print(f"  Kajabi ID: {product.get('kajabi_id', 'N/A')}")
    
    product_name = product.get('name')
except Exception as e:
    print(f"\n✗ Error finding product: {e}")
    product_name = None

# Get all subscriptions with missing product names
print("\n" + "="*80)
print("CHECKING HOW MANY SUBSCRIPTIONS HAVE MISSING PRODUCT NAMES")
print("="*80)

all_subs = supabase.table('subscriptions').select('*').execute().data
missing_names = [s for s in all_subs if not s.get('product_name')]

print(f"\nTotal subscriptions: {len(all_subs)}")
print(f"Subscriptions with missing product_name: {len(missing_names)}")
print(f"Percentage missing: {len(missing_names)/len(all_subs)*100:.1f}%")

# Check how many of those have product_id
with_product_id = [s for s in missing_names if s.get('product_id')]
print(f"\nMissing name BUT have product_id: {len(with_product_id)}")
print(f"Missing name AND missing product_id: {len(missing_names) - len(with_product_id)}")

# Show status breakdown
print(f"\nBy status:")
statuses = {}
for s in missing_names:
    status = s.get('status', 'unknown')
    statuses[status] = statuses.get(status, 0) + 1

for status, count in statuses.items():
    print(f"  {status}: {count}")

# Check if these are preventing UI display
active_missing = [s for s in missing_names if s.get('status') == 'active']
print(f"\n🚨 ACTIVE subscriptions with missing product name: {len(active_missing)}")

if len(active_missing) > 0:
    print(f"\nThis could explain why contacts don't show in UI!")
    print(f"\nSample of affected contacts (first 10):")
    
    for i, sub in enumerate(active_missing[:10], 1):
        contact = supabase.table('contacts').select('first_name, last_name, email').eq('id', sub['contact_id']).single().execute().data
        print(f"  {i}. {contact.get('first_name')} {contact.get('last_name')} ({contact.get('email')})")
        print(f"     Subscription: ${sub.get('amount')} / {sub.get('billing_cycle')} (ID: {sub.get('kajabi_subscription_id')})")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
print("\nWe should:")
print("1. Fix Lynn's duplicate subscription (remove PayPal, keep Kajabi)")
print("2. Populate missing product_name for all subscriptions that have product_id")
print("3. Investigate subscriptions with missing product_id")

