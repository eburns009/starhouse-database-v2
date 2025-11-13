import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("FINDING REMAINING DUPLICATE SUBSCRIPTIONS")
print("=" * 80)

# Get all active subscriptions
all_subs = supabase.table('subscriptions').select('*').eq('status', 'active').execute().data

print(f"\nTotal active subscriptions: {len(all_subs)}")

# Group by contact_id
contact_subs = {}
for sub in all_subs:
    contact_id = sub['contact_id']
    if contact_id not in contact_subs:
        contact_subs[contact_id] = []
    contact_subs[contact_id].append(sub)

# Find contacts with multiple subscriptions
duplicates = {cid: subs for cid, subs in contact_subs.items() if len(subs) > 1}

print(f"Contacts with multiple active subscriptions: {len(duplicates)}")
print(f"Total duplicate subscription records: {sum(len(subs) - 1 for subs in duplicates.values())}")

# Analyze the duplicates
print("\n" + "=" * 80)
print("DUPLICATE ANALYSIS")
print("=" * 80)

paypal_kajabi_duplicates = []
legitimate_multiples = []

for contact_id, subs in duplicates.items():
    # Get contact info
    contact = supabase.table('contacts').select('first_name, last_name, email').eq('id', contact_id).single().execute().data
    
    # Check if this is PayPal/Kajabi duplicate pattern
    paypal_subs = [s for s in subs if s.get('kajabi_subscription_id') and s.get('kajabi_subscription_id').startswith('I-')]
    kajabi_subs = [s for s in subs if s.get('kajabi_subscription_id') and s.get('kajabi_subscription_id').isdigit()]
    
    if len(paypal_subs) > 0 and len(kajabi_subs) > 0:
        # Check if they're the same amount (indicating duplicate)
        for p_sub in paypal_subs:
            for k_sub in kajabi_subs:
                # Match if same amount and billing cycle matches
                p_cycle = p_sub.get('billing_cycle', '').lower()
                k_cycle = k_sub.get('billing_cycle', '').lower()
                same_amount = p_sub['amount'] == k_sub['amount']
                same_cycle = (p_cycle.startswith('month') and k_cycle.startswith('month')) or \
                           (p_cycle.startswith('year') and k_cycle.startswith('year') or p_cycle.startswith('annual') and k_cycle.startswith('annual'))
                
                if same_amount and same_cycle:
                    paypal_kajabi_duplicates.append({
                        'contact_id': contact_id,
                        'contact_name': f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                        'email': contact.get('email'),
                        'paypal_sub_id': p_sub['id'],
                        'paypal_kajabi_id': p_sub.get('kajabi_subscription_id'),
                        'kajabi_sub_id': k_sub['id'],
                        'kajabi_kajabi_id': k_sub.get('kajabi_subscription_id'),
                        'amount': p_sub['amount'],
                        'billing_cycle': p_sub['billing_cycle']
                    })
                    break
    
    # If not duplicate, might be legitimate multiple
    is_duplicate = any(d['contact_id'] == contact_id for d in paypal_kajabi_duplicates)
    if not is_duplicate:
        legitimate_multiples.append({
            'contact_id': contact_id,
            'contact_name': f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
            'email': contact.get('email'),
            'subs': subs
        })

print(f"\n📊 BREAKDOWN:")
print(f"   PayPal/Kajabi duplicates: {len(paypal_kajabi_duplicates)} pairs")
print(f"   Legitimate multiple subscriptions: {len(legitimate_multiples)} contacts")

# Show PayPal/Kajabi duplicates (like Lynn)
if paypal_kajabi_duplicates:
    print(f"\n🚨 PAYPAL/KAJABI DUPLICATES (Need to remove PayPal version):")
    print(f"   {'Name':<30} {'Email':<40} {'Amount':<15}")
    print(f"   {'-'*85}")
    for dup in paypal_kajabi_duplicates:
        name = dup['contact_name'] if dup['contact_name'] else 'N/A'
        email = dup['email'] if dup['email'] else 'N/A'
        print(f"   {name:<30} {email:<40} ${dup['amount']:<9} / {dup['billing_cycle']}")
        print(f"     PayPal Sub to remove: {dup['paypal_sub_id']} (Kajabi ID: {dup['paypal_kajabi_id']})")
        print(f"     Kajabi Sub to keep:   {dup['kajabi_sub_id']} (Kajabi ID: {dup['kajabi_kajabi_id']})")
        print()

# Show legitimate multiples
if legitimate_multiples:
    print(f"\n✅ LEGITIMATE MULTIPLE SUBSCRIPTIONS:")
    print(f"   (These contacts have different subscriptions, not duplicates)")
    for dup in legitimate_multiples[:5]:  # Show first 5
        print(f"\n   {dup['contact_name']} ({dup['email']}):")
        for sub in dup['subs']:
            kajabi_id = sub.get('kajabi_subscription_id', 'N/A')
            print(f"     - ${sub['amount']} / {sub.get('billing_cycle')} (Kajabi ID: {kajabi_id})")
    if len(legitimate_multiples) > 5:
        print(f"\n   ... and {len(legitimate_multiples) - 5} more contacts")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nFound {len(paypal_kajabi_duplicates)} PayPal/Kajabi duplicate pairs")
print(f"These should be removed (keep Kajabi version, remove PayPal version)")

if paypal_kajabi_duplicates:
    print(f"\n⚠️ Will remove {len(paypal_kajabi_duplicates)} PayPal subscription records")
    
    # Save to file for reference
    import json
    with open('remaining_duplicates_to_remove.json', 'w') as f:
        json.dump(paypal_kajabi_duplicates, f, indent=2, default=str)
    print(f"✓ Saved details to: remaining_duplicates_to_remove.json")

