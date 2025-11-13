import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

contact_id = '8109792b-9bcb-4cef-87e4-0fb658fe372e'

print("=" * 80)
print("LYNN AMBER RYAN - UI DISPLAY ISSUE INVESTIGATION")
print("=" * 80)

# Get full contact details
contact = supabase.table('contacts').select('*').eq('id', contact_id).single().execute().data

print("\n1. CHECKING ALL CONTACT FIELDS FOR MISSING DATA:")
print(f"   First Name: '{contact.get('first_name')}' {'✗ MISSING' if not contact.get('first_name') else '✓'}")
print(f"   Last Name: '{contact.get('last_name')}' {'✗ MISSING' if not contact.get('last_name') else '✓'}")
print(f"   Email: '{contact.get('email')}' {'✗ MISSING' if not contact.get('email') else '✓'}")
print(f"   Phone: '{contact.get('phone')}' {'✗ MISSING' if not contact.get('phone') else '✓'}")
print(f"   Address: '{contact.get('address_line_1')}' {'✗ MISSING' if not contact.get('address_line_1') else '✓'}")
print(f"   City: '{contact.get('city')}' {'✗ MISSING' if not contact.get('city') else '✓'}")
print(f"   State: '{contact.get('state')}' {'✗ MISSING' if not contact.get('state') else '✓'}")
print(f"   Postal Code: '{contact.get('postal_code')}' {'✗ MISSING' if not contact.get('postal_code') else '✓'}")
print(f"   Country: '{contact.get('country')}' {'✗ MISSING' if not contact.get('country') else '✓'}")

# Get full subscription details
print("\n2. CHECKING SUBSCRIPTION DETAILS:")
subs = supabase.table('subscriptions').select('*').eq('contact_id', contact_id).execute().data

for i, sub in enumerate(subs, 1):
    print(f"\n   Subscription {i} (ID: {sub['id']}):")
    print(f"     kajabi_subscription_id: '{sub.get('kajabi_subscription_id')}' {' (PayPal format)' if sub.get('kajabi_subscription_id', '').startswith('I-') else ' (Kajabi format)'}")
    print(f"     product_name: '{sub.get('product_name')}' {'✗ MISSING!' if not sub.get('product_name') else '✓'}")
    print(f"     product_id: '{sub.get('product_id')}' {'✗ MISSING' if not sub.get('product_id') else '✓'}")
    print(f"     amount: ${sub.get('amount')}")
    print(f"     billing_cycle: '{sub.get('billing_cycle')}'")
    print(f"     status: '{sub.get('status')}'")
    print(f"     start_date: {sub.get('start_date')}")
    print(f"     end_date: {sub.get('end_date')}")
    print(f"     next_billing_date: {sub.get('next_billing_date')}")

# Check if this is a duplicate case
print("\n3. DUPLICATE SUBSCRIPTION CHECK:")
print(f"   Total active subscriptions: {len([s for s in subs if s['status'] == 'active'])}")
print(f"   PayPal subscriptions: {len([s for s in subs if s.get('kajabi_subscription_id', '').startswith('I-')])}")
print(f"   Kajabi subscriptions: {len([s for s in subs if s.get('kajabi_subscription_id', '').isdigit()])}")

paypal_sub = next((s for s in subs if s.get('kajabi_subscription_id', '').startswith('I-')), None)
kajabi_sub = next((s for s in subs if s.get('kajabi_subscription_id', '').isdigit()), None)

if paypal_sub and kajabi_sub:
    print("\n   ⚠️ DUPLICATE DETECTED:")
    print(f"     PayPal: ${paypal_sub.get('amount')} / {paypal_sub.get('billing_cycle')}")
    print(f"     Kajabi: ${kajabi_sub.get('amount')} / {kajabi_sub.get('billing_cycle')}")
    
    if paypal_sub.get('amount') == kajabi_sub.get('amount'):
        print(f"     ✓ Same amount - This is a duplicate!")
        print(f"\n   RECOMMENDATION: Remove PayPal subscription {paypal_sub['id']}")

# Check products table
print("\n4. CHECKING PRODUCTS TABLE:")
response = supabase.table('products').select('*').execute()
products = response.data
print(f"   Total products in database: {len(products)}")

# Look for $22 monthly products
monthly_22 = [p for p in products if p.get('price') == 22 or p.get('amount') == 22]
if monthly_22:
    print(f"   Products matching $22: {len(monthly_22)}")
    for p in monthly_22[:3]:
        print(f"     - {p.get('name', 'N/A')} (ID: {p.get('id')}, ${p.get('price', p.get('amount'))})")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

print("\nPOSSIBLE REASONS SHE DOESN'T SHOW IN UI:")
print("1. ✓ Has duplicate subscriptions (needs deduplication)")
print("2. ? Product name is missing on subscription (check if UI requires it)")
print("3. ? Check if UI filters by specific fields that might be missing")
print("4. ? Lock level FULL_LOCK might prevent display in some UI views")

