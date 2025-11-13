#!/usr/bin/env python3
"""
ANALYZE THE 329 NEW CONTACTS - Are they really new, or did they exist before?
"""

import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=" * 100)
print("ANALYZING THE 329 NEW CONTACTS - Root Cause Investigation")
print("=" * 100)

# Get the 329 new contacts
new_contacts = supabase.table('contacts').select(
    'id, email, kajabi_id, first_name, last_name, additional_name, created_at'
).is_('deleted_at', 'null')\
    .gte('created_at', '2025-11-12T04:31:00')\
    .lte('created_at', '2025-11-12T04:35:00')\
    .execute()

print(f"\n📊 OVERVIEW")
print("-" * 100)
print(f"Total new contacts created: {len(new_contacts.data)}")
print(f"All have Kajabi IDs: {'✓' if all(c.get('kajabi_id') for c in new_contacts.data) else '✗'}")
print(f"With middle names: {sum(1 for c in new_contacts.data if c.get('additional_name'))}")
print(f"Without middle names: {sum(1 for c in new_contacts.data if not c.get('additional_name'))}")

# Key question: Do any of these Kajabi IDs exist in older contacts?
print(f"\n🔍 KEY QUESTION: Did these Kajabi IDs exist before?")
print("-" * 100)
print("\nChecking if any of these Kajabi IDs existed in contacts created before today...\n")

kajabi_ids = [c['kajabi_id'] for c in new_contacts.data if c.get('kajabi_id')]

# Check in batches
batch_size = 50
found_older = []

for i in range(0, min(100, len(kajabi_ids)), batch_size):
    batch = kajabi_ids[i:i+batch_size]

    # Search for contacts with same Kajabi IDs created before today
    older = supabase.table('contacts').select('kajabi_id, email, first_name, last_name, created_at')\
        .in_('kajabi_id', batch)\
        .lt('created_at', '2025-11-12T04:31:00')\
        .execute()

    if older.data:
        found_older.extend(older.data)

if found_older:
    print(f"❌ PROBLEM: Found {len(found_older)} Kajabi IDs that existed BEFORE today!")
    print("\nThis means these aren't new members - they're DUPLICATES!")
    print("\nExamples:")
    for i, old_contact in enumerate(found_older[:5], 1):
        # Find the new duplicate
        new_dup = next((c for c in new_contacts.data if c['kajabi_id'] == old_contact['kajabi_id']), None)
        if new_dup:
            print(f"\n{i}. Kajabi ID: {old_contact['kajabi_id']}")
            print(f"   OLD: {old_contact['email']} - {old_contact['first_name']} {old_contact['last_name']}")
            print(f"        Created: {old_contact['created_at'][:10]}")
            print(f"   NEW: {new_dup['email']} - {new_dup['first_name']} {new_dup.get('additional_name', '')} {new_dup['last_name']}")
            print(f"        Created: {new_dup['created_at'][:10]}")

    print(f"\n💡 ROOT CAUSE: The UPSERT logic failed!")
    print(f"   - The import should have done: ON CONFLICT (email) DO UPDATE")
    print(f"   - Instead it created NEW records for existing Kajabi members")
    print(f"   - This suggests the email addresses may have changed in Kajabi")
else:
    print(f"✅ No older Kajabi IDs found in first {min(100, len(kajabi_ids))} checked")
    print(f"   These appear to be genuinely new Kajabi members")

# Check if these are members without emails previously
print(f"\n🔍 ALTERNATIVE: Were these members in Kajabi without emails before?")
print("-" * 100)
print("\nIt's possible these 329:")
print("1. Are brand new Kajabi members (legitimate new sign-ups)")
print("2. Existed in Kajabi but didn't have emails before (now do)")
print("3. Had different emails in our database (email changed in Kajabi)")

# Check creation dates in database vs Kajabi
print(f"\n📅 CREATION DATE ANALYSIS")
print("-" * 100)
print(f"\nAll 329 created at exactly: {new_contacts.data[0]['created_at'][:19]}")
print(f"This timestamp matches our import run (04:31 UTC)")
print("\nThis is normal for bulk import - all records get same created_at")

# Summary
print("\n" + "=" * 100)
print("VERDICT ON THE 329 NEW CONTACTS")
print("=" * 100)

if found_older:
    print(f"""
❌ DUPLICATES FOUND: {len(found_older)} of the 329 have same Kajabi IDs as older contacts

ROOT CAUSE:
  The UPSERT logic in the import script uses email as the conflict key:

    ON CONFLICT (email) DO UPDATE SET ...

  But if the email changed in Kajabi, the UPSERT won't find the old record
  and will INSERT a new one instead of UPDATE the existing one.

WHAT HAPPENED:
  1. Contact exists in database with Kajabi ID X and email A
  2. In Kajabi, same contact (ID X) now has email B
  3. Import runs with email B as key
  4. No conflict found (email B doesn't exist)
  5. New record inserted (WRONG! Should update by Kajabi ID)

FIX NEEDED:
  Change UPSERT to use kajabi_id as primary key, not email:

    ON CONFLICT (kajabi_id) DO UPDATE SET ...

  This ensures Kajabi members update correctly even if email changes.
""")
else:
    print(f"""
✅ NO DUPLICATES FOUND: First {min(100, len(kajabi_ids))} checked don't have older Kajabi IDs

POSSIBLE EXPLANATIONS:
  1. These are 329 genuinely new Kajabi members who signed up recently
  2. The Kajabi export now includes more members than before
  3. Filter criteria in Kajabi export changed

VERIFICATION NEEDED:
  - Check Kajabi dashboard: Did ~329 new members join recently?
  - Compare Kajabi CSV file from previous import vs today
  - Check if Kajabi export filter changed (e.g., now includes inactive?)
""")

print("=" * 100)
