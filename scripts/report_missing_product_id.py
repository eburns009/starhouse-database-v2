import os
from supabase import create_client
import json
from datetime import datetime

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("SUBSCRIPTIONS MISSING PRODUCT_ID - DETAILED REPORT")
print("=" * 80)

# Get all subscriptions without product_id
subs_no_product = supabase.table('subscriptions').select('*, contacts(first_name, last_name, email)').is_('product_id', 'null').execute().data

print(f"\nTotal subscriptions without product_id: {len(subs_no_product)}")

# Analyze by status
by_status = {}
for sub in subs_no_product:
    status = sub.get('status', 'unknown')
    by_status[status] = by_status.get(status, 0) + 1

print(f"\nBy status:")
for status, count in sorted(by_status.items()):
    print(f"  {status}: {count}")

# Analyze by kajabi_subscription_id type
paypal_only = [s for s in subs_no_product if s.get('kajabi_subscription_id') and s.get('kajabi_subscription_id').startswith('I-')]
no_kajabi_id = [s for s in subs_no_product if not s.get('kajabi_subscription_id')]
numeric_id = [s for s in subs_no_product if s.get('kajabi_subscription_id') and s.get('kajabi_subscription_id').isdigit()]

print(f"\nBy ID type:")
print(f"  PayPal subscriptions (I-XXX): {len(paypal_only)}")
print(f"  Kajabi subscriptions (numeric): {len(numeric_id)}")
print(f"  No Kajabi ID: {len(no_kajabi_id)}")

# Show samples
print(f"\n{'='*80}")
print("SAMPLES OF SUBSCRIPTIONS WITHOUT PRODUCT_ID")
print("=" * 80)

print(f"\n1. PAYPAL-ONLY SUBSCRIPTIONS (sample of 10):")
for i, sub in enumerate(paypal_only[:10], 1):
    contact = sub.get('contacts', {})
    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or 'N/A'
    email = contact.get('email', 'N/A')
    print(f"   {i}. {name} ({email})")
    print(f"      PayPal ID: {sub.get('kajabi_subscription_id')}")
    print(f"      Amount: ${sub.get('amount')} / {sub.get('billing_cycle')}")
    print(f"      Status: {sub.get('status')}")

if numeric_id:
    print(f"\n2. KAJABI SUBSCRIPTIONS WITHOUT PRODUCT_ID (all {len(numeric_id)}):")
    for i, sub in enumerate(numeric_id, 1):
        contact = sub.get('contacts', {})
        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or 'N/A'
        email = contact.get('email', 'N/A')
        print(f"   {i}. {name} ({email})")
        print(f"      Kajabi Sub ID: {sub.get('kajabi_subscription_id')}")
        print(f"      Amount: ${sub.get('amount')} / {sub.get('billing_cycle')}")
        print(f"      Status: {sub.get('status')}")
        print(f"      ⚠️  This should have a product_id!")

# Generate JSON report
report = {
    'timestamp': datetime.now().isoformat(),
    'summary': {
        'total_without_product_id': len(subs_no_product),
        'by_status': by_status,
        'paypal_only': len(paypal_only),
        'kajabi_numeric': len(numeric_id),
        'no_kajabi_id': len(no_kajabi_id)
    },
    'paypal_only_subscriptions': [
        {
            'subscription_id': s['id'],
            'contact_name': f"{s.get('contacts', {}).get('first_name', '')} {s.get('contacts', {}).get('last_name', '')}".strip(),
            'email': s.get('contacts', {}).get('email'),
            'paypal_subscription_id': s.get('kajabi_subscription_id'),
            'amount': s.get('amount'),
            'billing_cycle': s.get('billing_cycle'),
            'status': s.get('status')
        }
        for s in paypal_only
    ],
    'kajabi_without_product_id': [
        {
            'subscription_id': s['id'],
            'contact_name': f"{s.get('contacts', {}).get('first_name', '')} {s.get('contacts', {}).get('last_name', '')}".strip(),
            'email': s.get('contacts', {}).get('email'),
            'kajabi_subscription_id': s.get('kajabi_subscription_id'),
            'amount': s.get('amount'),
            'billing_cycle': s.get('billing_cycle'),
            'status': s.get('status')
        }
        for s in numeric_id
    ]
}

report_file = f"missing_product_id_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f"\n{'='*80}")
print(f"✅ Report saved to: {report_file}")
print("=" * 80)

print("\n📊 SUMMARY:")
print(f"   {len(paypal_only)} PayPal-only subscriptions (expected - these were never in Kajabi)")
print(f"   {len(numeric_id)} Kajabi subscriptions missing product_id (needs investigation)")
print(f"   {len(no_kajabi_id)} subscriptions with no Kajabi ID")

