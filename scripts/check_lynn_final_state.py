import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("CHECKING LYNN'S CURRENT SUBSCRIPTION STATE")
print("=" * 80)

# Get Lynn
lynn = supabase.table('contacts').select('id, first_name, last_name, email').eq('email', 'amber@the360emergence.com').single().execute().data

print(f"\n✓ Contact: {lynn['first_name']} {lynn['last_name']} ({lynn['email']})")

# Get her subscriptions WITH product information via JOIN
subs = supabase.table('subscriptions').select('*, products(*)').eq('contact_id', lynn['id']).execute().data

print(f"\n📋 Subscriptions: {len(subs)}")

for i, sub in enumerate(subs, 1):
    print(f"\n  Subscription {i}:")
    print(f"    ID: {sub['id']}")
    print(f"    Kajabi Sub ID: {sub.get('kajabi_subscription_id')}")
    print(f"    Status: {sub.get('status')}")
    print(f"    Amount: ${sub.get('amount')} / {sub.get('billing_cycle')}")
    print(f"    Product ID: {sub.get('product_id')}")
    
    # Check if products JOIN worked
    if sub.get('products'):
        product = sub['products']
        print(f"    Product (from JOIN):")
        print(f"      Name: {product.get('name')}")
        print(f"      Type: {product.get('product_type')}")
        print(f"      Active: {product.get('active')}")
    else:
        print(f"    ⚠️  No product information (product_id might be null)")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

print("\nThe subscriptions table doesn't have a 'product_name' column.")
print("It only has 'product_id' which is a foreign key to the products table.")
print("\nThe UI needs to:")
print("  1. JOIN subscriptions with products table using product_id")
print("  2. Display products.name as the product name")
print("\nIf Lynn's subscription has product_id populated, the UI should work.")
print("If it's null, that's why she doesn't show up.")

