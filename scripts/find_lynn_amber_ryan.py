import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("SEARCHING FOR: Lynn Amber Ryan")
print("=" * 80)

# Search by first_name and last_name
print("\n1. Searching for Lynn Ryan (first + last name)...")
response = supabase.table('contacts').select('*').ilike('first_name', '%lynn%').ilike('last_name', '%ryan%').execute()
lynn_ryan = response.data
print(f"Found {len(lynn_ryan)} contact(s) with first name 'Lynn' and last name 'Ryan'")

if lynn_ryan:
    for contact in lynn_ryan:
        print(f"\n{'='*80}")
        print(f"📧 MATCH FOUND: {contact.get('first_name', '')} {contact.get('last_name', '')}")
        print(f"{'='*80}")
        print(f"ID: {contact['id']}")
        print(f"Email: {contact.get('email', 'N/A')}")
        print(f"First Name: {contact.get('first_name', 'N/A')}")
        print(f"Last Name: {contact.get('last_name', 'N/A')}")
        print(f"Source: {contact.get('source_system', 'N/A')}")
        print(f"Kajabi ID: {contact.get('kajabi_id', 'N/A')}")
        print(f"Lock Level: {contact.get('lock_level', 'N/A')}")
        print(f"Email Subscribed: {contact.get('email_subscribed', 'N/A')}")
        print(f"Created: {contact.get('created_at', 'N/A')}")
        print(f"Updated: {contact.get('updated_at', 'N/A')}")
        
        # Get subscriptions
        print(f"\n📋 SUBSCRIPTIONS:")
        subs = supabase.table('subscriptions').select('*').eq('contact_id', contact['id']).execute().data
        
        if subs:
            print(f"✓ {len(subs)} subscription(s) found\n")
            for i, sub in enumerate(subs, 1):
                print(f"  Subscription {i}:")
                print(f"    Status: {sub.get('status', 'N/A')}")
                print(f"    Product: {sub.get('product_name', 'N/A')}")
                print(f"    Amount: ${sub.get('amount', 0)} / {sub.get('billing_cycle', 'N/A')}")
                print(f"    Kajabi Sub ID: {sub.get('kajabi_subscription_id', 'N/A')}")
                print(f"    Start: {sub.get('start_date', 'N/A')}")
                print(f"    Updated: {sub.get('updated_at', 'N/A')}")
                print()
        else:
            print("✗ No subscriptions found")
        
        # Get transactions
        print(f"💰 TRANSACTIONS:")
        trans = supabase.table('transactions').select('*').eq('contact_id', contact['id']).order('transaction_date', desc=True).limit(5).execute().data
        
        if trans:
            print(f"✓ {len(trans)} recent transaction(s)\n")
            for i, t in enumerate(trans, 1):
                print(f"  Transaction {i}: ${t.get('amount', 0)} on {t.get('transaction_date', 'N/A')} ({t.get('status', 'N/A')})")
        else:
            print("✗ No transactions found")

else:
    print("\nNo exact match found. Trying broader searches...\n")
    
    # Try searching for "Amber" in middle name or first name
    print("2. Searching for contacts with 'Amber' in first name...")
    response = supabase.table('contacts').select('*').ilike('first_name', '%amber%').execute()
    amber_contacts = response.data
    print(f"Found {len(amber_contacts)} contact(s)")
    
    # Check if any have "Ryan" in last name
    for c in amber_contacts:
        if 'ryan' in c.get('last_name', '').lower():
            print(f"\n  → {c.get('first_name')} {c.get('last_name')} ({c.get('email')})")
    
    # Try searching email for "lynn" AND "amber" AND "ryan"
    print("\n3. Searching emails for all three parts...")
    response = supabase.table('contacts').select('*').execute()
    all_contacts = response.data
    
    matches = []
    for c in all_contacts:
        email = c.get('email', '').lower()
        first = c.get('first_name', '').lower()
        last = c.get('last_name', '').lower()
        full_text = f"{email} {first} {last}"
        
        if 'lynn' in full_text and 'amber' in full_text and 'ryan' in full_text:
            matches.append(c)
    
    if matches:
        print(f"Found {len(matches)} potential match(es):")
        for c in matches:
            print(f"\n  → {c.get('first_name')} {c.get('last_name')} ({c.get('email')})")
            print(f"     Kajabi ID: {c.get('kajabi_id')}")
            # Check subscriptions
            subs = supabase.table('subscriptions').select('status').eq('contact_id', c['id']).execute().data
            print(f"     Subscriptions: {len(subs)} ({', '.join([s['status'] for s in subs])})")
    else:
        print("No contacts found with all three parts (Lynn, Amber, Ryan)")

print("\n" + "="*80)
print("END OF SEARCH")
print("="*80)

