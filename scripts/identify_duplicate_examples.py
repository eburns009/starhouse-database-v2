#!/usr/bin/env python3
"""
IDENTIFY DUPLICATE EXAMPLES - Show specific cases of duplicates
"""

import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=" * 100)
print("DUPLICATE EXAMPLES - Understanding the Problem")
print("=" * 100)

# Get examples of Kajabi+Zoho duplicates
print("\n1️⃣  KAJABI + ZOHO DUPLICATES (Same person, two source IDs)")
print("-" * 100)

duplicates = supabase.table('contacts').select(
    'id, email, first_name, last_name, additional_name, '
    'kajabi_id, zoho_id, source_system, created_at'
).is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .not_.is_('zoho_id', 'null')\
    .limit(10).execute()

print(f"\nFound {len(duplicates.data)} examples (showing first 10 of 1,425 total):\n")

for i, contact in enumerate(duplicates.data, 1):
    print(f"{i}. {contact['email']}")
    print(f"   Name: {contact.get('first_name', '')} {contact.get('additional_name', '')} {contact.get('last_name', '')}".replace('  ', ' '))
    print(f"   Kajabi ID: {contact['kajabi_id']}")
    print(f"   Zoho ID: {contact['zoho_id']}")
    print(f"   Source: {contact.get('source_system', 'unknown')}")
    print(f"   Created: {contact['created_at'][:10]}")
    print()

# Get examples of Zoho-only contacts
print("\n2️⃣  ZOHO-ONLY CONTACTS (Legacy orphans, not in Kajabi)")
print("-" * 100)

zoho_only = supabase.table('contacts').select(
    'id, email, first_name, last_name, zoho_id, created_at'
).is_('deleted_at', 'null')\
    .is_('kajabi_id', 'null')\
    .not_.is_('zoho_id', 'null')\
    .limit(10).execute()

print(f"\nFound {len(zoho_only.data)} examples (showing first 10 of 530 total):\n")

for i, contact in enumerate(zoho_only.data, 1):
    print(f"{i}. {contact['email']}")
    print(f"   Name: {contact.get('first_name', '')} {contact.get('last_name', '')}".replace('  ', ' '))
    print(f"   Zoho ID: {contact['zoho_id']}")
    print(f"   Created: {contact['created_at'][:10]}")
    print()

# Get examples of today's 329 new contacts
print("\n3️⃣  TODAY'S 329 NEW CONTACTS (Created during import)")
print("-" * 100)

new_today = supabase.table('contacts').select(
    'id, email, first_name, last_name, additional_name, kajabi_id, created_at'
).is_('deleted_at', 'null')\
    .gte('created_at', '2025-11-12T04:31:00')\
    .lte('created_at', '2025-11-12T04:35:00')\
    .limit(10).execute()

print(f"\nFound {len(new_today.data)} examples (showing first 10 of 329 total):\n")

for i, contact in enumerate(new_today.data, 1):
    print(f"{i}. {contact['email']}")
    full_name = f"{contact.get('first_name', '')} {contact.get('additional_name', '')} {contact.get('last_name', '')}".replace('  ', ' ')
    print(f"   Name: {full_name}")
    print(f"   Kajabi ID: {contact.get('kajabi_id', 'None')}")
    print(f"   Has middle name: {'✓' if contact.get('additional_name') else '✗'}")
    print(f"   Created: {contact['created_at']}")
    print()

# Check if any of the 329 are duplicates
print("\n4️⃣  CHECKING IF THE 329 ARE DUPLICATES")
print("-" * 100)
print("\nSearching for duplicate emails (same email, different contact IDs)...\n")

# Get all 329 contacts
all_new = supabase.table('contacts').select('id, email')\
    .is_('deleted_at', 'null')\
    .gte('created_at', '2025-11-12T04:31:00')\
    .lte('created_at', '2025-11-12T04:35:00')\
    .execute()

duplicate_emails = []
checked = 0

for contact in all_new.data[:50]:  # Check first 50 to avoid rate limits
    checked += 1
    email = contact['email']

    # Find all contacts with this email
    all_with_email = supabase.table('contacts').select('id', count='exact')\
        .eq('email', email)\
        .is_('deleted_at', 'null')\
        .execute()

    if all_with_email.count > 1:
        duplicate_emails.append(email)
        if len(duplicate_emails) <= 5:
            print(f"  ⚠️  {email}: {all_with_email.count} total contacts with this email (DUPLICATE)")

if duplicate_emails:
    print(f"\n❌ FOUND {len(duplicate_emails)} DUPLICATES in first {checked} checked")
    print(f"   The 329 contacts include duplicates that should have been updates!")
else:
    print(f"\n✅ NO DUPLICATES found in first {checked} checked")
    print(f"   The 329 appear to be legitimate new contacts")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"""
DUPLICATE PROBLEMS IDENTIFIED:

1. KAJABI + ZOHO DUPLICATES: 1,425 contacts
   - Same person exists in both systems
   - Kajabi should be winner (primary source)
   - Need to merge or mark Zoho data as superseded

2. ZOHO-ONLY ORPHANS: 530 contacts
   - Only in Zoho, not in Kajabi
   - Likely old customers who never migrated
   - Decision needed: keep as historical or remove

3. TODAY'S 329 NEW CONTACTS:
   - Created during Kajabi import today
   - Need to verify if duplicates or legitimate new members
   - First {checked} checked: {"DUPLICATES FOUND" if duplicate_emails else "No duplicates"}

RECOMMENDATION:
- Fix Kajabi+Zoho duplicates first (1,425 contacts)
- Decide on Zoho orphans (530 contacts)
- Investigate why 329 were created (should existing contacts update?)
""")
print("=" * 100)
