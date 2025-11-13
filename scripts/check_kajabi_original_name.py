#!/usr/bin/env python3
"""
Check if there's a kajabi_original_name or similar field for Lynn
"""

import os
from supabase import create_client, Client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(url, key)

print("Checking contacts table schema for name-related columns...")
print("=" * 80)

# Get Lynn's full record
response = supabase.table('contacts').select('*').eq('email', 'amber@the360emergence.com').execute()

if response.data:
    contact = response.data[0]
    print("\nAll name-related fields for Lynn Amber Ryan:")
    print("-" * 80)

    name_fields = [
        'first_name', 'last_name', 'additional_name',
        'paypal_first_name', 'paypal_last_name', 'paypal_business_name',
        'kajabi_id', 'email'
    ]

    # Show all fields
    for key in sorted(contact.keys()):
        if 'name' in key.lower() or 'kajabi' in key.lower():
            print(f"{key:30} = {contact.get(key)}")

    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("=" * 80)

    # Check if the name "Lynn Amber Ryan" appears anywhere
    full_search = "Lynn Amber Ryan"
    found_in = []

    for key, value in contact.items():
        if value and isinstance(value, str) and full_search.lower() in value.lower():
            found_in.append(key)

    if found_in:
        print(f"✓ Full name '{full_search}' found in fields: {', '.join(found_in)}")
    else:
        print(f"✗ Full name '{full_search}' NOT found in any single field")
        print("\nName is split across fields:")
        print("  - 'Lynn' → first_name")
        print("  - 'Amber' → email (amber@...)")
        print("  - 'Ryan' → last_name")
        print("\nThis is why tokenized search is needed!")
