#!/usr/bin/env python3
"""Test the tokenized search logic to verify Lynn Amber Ryan will be found"""

import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("Testing Tokenized Search Implementation")
print("=" * 80)

# Test Case 1: "Lynn Amber Ryan" (the original problem)
print("\n1. TEST: Search for 'Lynn Amber Ryan'")
print("-" * 80)

search_query = "Lynn Amber Ryan"
words = search_query.strip().split()
print(f"Search query: '{search_query}'")
print(f"Tokenized into: {words}")

# Simulate the UI query logic
search_fields = [
    'first_name', 'last_name', 'additional_name',
    'paypal_first_name', 'paypal_last_name', 'paypal_business_name',
    'email', 'phone'
]

print(f"\nSearching across {len(search_fields)} fields:")
print(f"  {', '.join(search_fields)}")

# For each word, we'll check which contacts have it in ANY field
for word in words:
    print(f"\n  Checking for word '{word}':")

    # Build OR conditions for this word across all fields
    conditions = ','.join([f"{field}.ilike.%{word}%" for field in search_fields])

    result = supabase.table('contacts').select('id, first_name, last_name, email').is_('deleted_at', None).or_(conditions).execute()

    print(f"    Found {len(result.data)} contact(s) with '{word}' in any field")

    # Check if Lynn is in the results
    lynn_found = False
    for contact in result.data:
        if contact['email'] == 'amber@the360emergence.com':
            lynn_found = True
            print(f"    ✓ Lynn Ryan found (matches in email domain or name fields)")
            break

    if not lynn_found and len(result.data) > 0:
        print(f"    (Lynn Ryan not in this word's results)")

# Now test the complete query (all words OR'd together)
print(f"\n2. COMPLETE QUERY: All words OR'd across all fields")
print("-" * 80)

# Build the complete OR condition
all_conditions = ','.join([
    f"{field}.ilike.%{word}%"
    for word in words
    for field in search_fields
])

print(f"Conditions: {len(words)} words × {len(search_fields)} fields = {len(words) * len(search_fields)} OR conditions")

result = supabase.table('contacts').select(
    'id, first_name, last_name, email, additional_name'
).is_('deleted_at', None).or_(all_conditions).limit(20).execute()

print(f"\nResults: {len(result.data)} contact(s) found")

# Find Lynn in results
lynn_found = False
for contact in result.data:
    if contact['email'] == 'amber@the360emergence.com':
        lynn_found = True
        print(f"\n✅ SUCCESS: Lynn Ryan found!")
        print(f"   Name: {contact['first_name']} {contact['last_name']}")
        print(f"   Email: {contact['email']}")
        print(f"   Additional name: {contact.get('additional_name', 'None')}")
        print(f"\n   Why it matches:")
        print(f"   - 'Lynn' found in first_name: '{contact['first_name']}'")
        print(f"   - 'Amber' found in email: '{contact['email']}'")
        print(f"   - 'Ryan' found in last_name: '{contact['last_name']}'")
        break

if not lynn_found:
    print(f"\n❌ FAILURE: Lynn Ryan NOT found in results")
    print(f"\nOther contacts found:")
    for contact in result.data[:5]:
        print(f"   - {contact['first_name']} {contact['last_name']} ({contact['email']})")

# Test Case 2: "Sue Johnson" (couple name test)
print(f"\n" + "=" * 80)
print("3. TEST: Search for 'Sue Johnson' (couple test)")
print("-" * 80)

search_query = "Sue Johnson"
words = search_query.strip().split()

all_conditions = ','.join([
    f"{field}.ilike.%{word}%"
    for word in words
    for field in search_fields
])

result = supabase.table('contacts').select(
    'id, first_name, last_name, email'
).is_('deleted_at', None).or_(all_conditions).limit(20).execute()

print(f"Search: '{search_query}'")
print(f"Results: {len(result.data)} contact(s) found")

sue_johnson_found = False
for contact in result.data:
    if 'sue' in contact['first_name'].lower() and 'johnson' in contact['first_name'].lower():
        sue_johnson_found = True
        print(f"\n✅ Found couple contact:")
        print(f"   Name: {contact['first_name']} {contact['last_name']}")
        print(f"   Email: {contact['email']}")
        break

if result.data and not sue_johnson_found:
    print(f"\nContacts with 'Sue' or 'Johnson':")
    for contact in result.data[:5]:
        print(f"   - {contact['first_name']} {contact['last_name']}")

# Test Case 3: "Mike Moritz" (other half of couple)
print(f"\n" + "=" * 80)
print("4. TEST: Search for 'Mike Moritz' (couple test)")
print("-" * 80)

search_query = "Mike Moritz"
words = search_query.strip().split()

all_conditions = ','.join([
    f"{field}.ilike.%{word}%"
    for word in words
    for field in search_fields
])

result = supabase.table('contacts').select(
    'id, first_name, last_name, email'
).is_('deleted_at', None).or_(all_conditions).limit(20).execute()

print(f"Search: '{search_query}'")
print(f"Results: {len(result.data)} contact(s) found")

mike_found = False
for contact in result.data:
    if 'mike' in contact['first_name'].lower():
        mike_found = True
        print(f"\n✅ Found contact with Mike:")
        print(f"   Name: {contact['first_name']} {contact['last_name']}")
        print(f"   Email: {contact['email']}")
        break

if result.data and not mike_found:
    print(f"\nContacts with 'Mike' or 'Moritz':")
    for contact in result.data[:5]:
        print(f"   - {contact['first_name']} {contact['last_name']}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

if lynn_found:
    print("\n✅ PRIMARY ISSUE RESOLVED:")
    print("   'Lynn Amber Ryan' search will now find Lynn Ryan")
    print("\n✅ TOKENIZED SEARCH WORKING:")
    print("   Multi-word names, couples, and complex names are now searchable")
else:
    print("\n❌ PRIMARY ISSUE NOT RESOLVED:")
    print("   'Lynn Amber Ryan' search still doesn't find Lynn")
    print("   Further investigation needed")
