#!/usr/bin/env python3
"""
Verify Lynn Amber Ryan's current state in the database using Supabase client.
"""

import os
import sys
from supabase import create_client, Client

# Supabase connection
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)

supabase: Client = create_client(url, key)

print("=" * 80)
print("LYNN AMBER RYAN - CURRENT STATE VERIFICATION")
print("=" * 80)

# 1. Find Lynn by email
print("\n1. SEARCHING FOR LYNN BY EMAIL (amber@the360emergence.com)")
print("-" * 80)

response = supabase.table('contacts').select('*').eq('email', 'amber@the360emergence.com').execute()

if not response.data or len(response.data) == 0:
    print("❌ ERROR: Lynn not found by email!")
    sys.exit(1)

contact = response.data[0]
contact_id = contact['id']

print(f"✓ Found contact:")
print(f"  ID: {contact_id}")
print(f"  First Name: {contact.get('first_name')}")
print(f"  Last Name: {contact.get('last_name')}")
print(f"  Additional Name: {contact.get('additional_name')}")
print(f"  Email: {contact.get('email')}")
print(f"  PayPal First Name: {contact.get('paypal_first_name')}")
print(f"  PayPal Last Name: {contact.get('paypal_last_name')}")
print(f"  PayPal Business Name: {contact.get('paypal_business_name')}")
print(f"  Kajabi ID: {contact.get('kajabi_id')}")
print(f"  Deleted At: {contact.get('deleted_at')}")

# 2. Check if contact is deleted
print("\n2. DELETION STATUS")
print("-" * 80)
if contact.get('deleted_at'):
    print(f"❌ CRITICAL: Contact is DELETED! deleted_at = {contact.get('deleted_at')}")
    print("   This is why she doesn't show up in the UI!")
else:
    print("✓ Contact is NOT deleted (deleted_at IS NULL)")

# 3. Check subscriptions
print("\n3. ACTIVE SUBSCRIPTIONS")
print("-" * 80)

subs_response = supabase.table('subscriptions')\
    .select('*, products(id, name)')\
    .eq('contact_id', contact_id)\
    .eq('status', 'active')\
    .execute()

subscriptions = subs_response.data
print(f"✓ Found {len(subscriptions)} active subscription(s)")
for sub in subscriptions:
    print(f"\n  Subscription ID: {sub['id']}")
    print(f"  Kajabi Sub ID: {sub.get('kajabi_subscription_id')}")
    print(f"  Status: {sub.get('status')}")
    print(f"  Amount: ${sub.get('amount')}/{sub.get('billing_cycle')}")
    print(f"  Product ID: {sub.get('product_id')}")
    if sub.get('products'):
        print(f"  Product Name: {sub['products'].get('name')}")

# 4. Simulate tokenized search with AND logic
print("\n4. SIMULATING TOKENIZED SEARCH: 'Lynn Amber Ryan'")
print("-" * 80)

search_query = "Lynn Amber Ryan"
words = search_query.lower().split()
print(f"Search words: {words}")

search_fields = [
    ('first_name', contact.get('first_name')),
    ('last_name', contact.get('last_name')),
    ('additional_name', contact.get('additional_name')),
    ('paypal_first_name', contact.get('paypal_first_name')),
    ('paypal_last_name', contact.get('paypal_last_name')),
    ('paypal_business_name', contact.get('paypal_business_name')),
    ('email', contact.get('email')),
    ('phone', contact.get('phone')),
]

print("\nChecking if ALL words match (AND logic):")
all_words_match = True
for word in words:
    print(f"\n  Word: '{word}'")
    word_found_in_field = False
    for field_name, field_value in search_fields:
        if field_value and word in str(field_value).lower():
            print(f"    ✓ Found in {field_name}: {field_value}")
            word_found_in_field = True

    if not word_found_in_field:
        print(f"    ❌ NOT found in any field!")
        all_words_match = False

# 5. Test actual database query that UI would use (OR logic)
print("\n5. TESTING ACTUAL UI QUERY (with OR conditions, then AND filter)")
print("-" * 80)

# Build OR conditions like the UI does
conditions = []
for word in words:
    for field in ['first_name', 'last_name', 'additional_name', 'paypal_first_name',
                   'paypal_last_name', 'paypal_business_name', 'email', 'phone']:
        conditions.append(f"{field}.ilike.%{word}%")

# Supabase query with OR
or_query = ','.join(conditions)
results = supabase.table('contacts')\
    .select('*')\
    .is_('deleted_at', 'null')\
    .or_(or_query)\
    .limit(200)\
    .execute()

print(f"✓ Database returned {len(results.data)} contact(s) using OR logic")

# Check if Lynn is in results
lynn_in_results = False
for result in results.data:
    if result['id'] == contact_id:
        lynn_in_results = True
        break

if lynn_in_results:
    print("✓ Lynn IS in the database OR query results")
else:
    print("❌ Lynn is NOT in the database OR query results")

# Simulate client-side AND filtering (like the UI does)
print("\n6. SIMULATING CLIENT-SIDE AND FILTERING")
print("-" * 80)

filtered_contacts = []
for c in results.data:
    # Check if ALL words match in at least one field
    all_match = True
    for word in words:
        word_matches = False
        for field in ['first_name', 'last_name', 'additional_name', 'paypal_first_name',
                       'paypal_last_name', 'paypal_business_name', 'email', 'phone']:
            field_value = c.get(field)
            if field_value and word in str(field_value).lower():
                word_matches = True
                break
        if not word_matches:
            all_match = False
            break

    if all_match:
        filtered_contacts.append(c)

print(f"✓ After AND filtering: {len(filtered_contacts)} contact(s)")

lynn_in_filtered = False
for c in filtered_contacts:
    if c['id'] == contact_id:
        lynn_in_filtered = True
        break

if lynn_in_filtered:
    print("✓ Lynn PASSES the AND filter")
else:
    print("❌ Lynn is FILTERED OUT by AND logic")

# 7. Final verdict
print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if contact.get('deleted_at'):
    print("❌ PROBLEM FOUND: Contact is DELETED (deleted_at IS NOT NULL)")
    print("   SOLUTION: Set deleted_at = NULL to restore the contact")
elif not lynn_in_results:
    print("❌ PROBLEM: Lynn not found by UI OR query")
    print("   Need to investigate query logic")
elif not lynn_in_filtered:
    print("❌ PROBLEM: Client-side AND filtering excludes Lynn")
    print("   Need to check which word is not matching")
    print("\n   Analysis:")
    for word in words:
        print(f"\n   '{word}' matches:")
        for field_name, field_value in search_fields:
            if field_value and word in str(field_value).lower():
                print(f"     ✓ {field_name}")
else:
    print("✅ NO PROBLEMS FOUND: Lynn should show up in UI")
    print("   If she doesn't, check:")
    print("   1. Browser cache (hard refresh: Ctrl+Shift+R or Cmd+Shift+R)")
    print("   2. Deployment status on Vercel")
    print("   3. Check browser console for errors")
    print("   4. Verify the latest code is deployed (commit 97758d2)")

print("\n" + "=" * 80)
