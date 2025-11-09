#!/usr/bin/env python3
"""
Validate Contact Updates
=========================
This script validates the contact and product updates to check for errors.
"""

import csv
import os
import requests
from collections import defaultdict

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://lnagadkqejnopgfxwlkb.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
TRANSACTIONS_FILE = '/workspaces/starhouse-database-v2/data/production/transactions.csv'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

print("=" * 70)
print("DATABASE UPDATE VALIDATION")
print("=" * 70)

# Read transactions CSV to compute expected values
print("\n📖 Reading source data...")
with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    transactions = list(reader)

print(f"   Total transactions in CSV: {len(transactions)}")

# Compute expected values per email
expected_data = defaultdict(lambda: {
    'total_spent': 0.0,
    'transaction_count': 0,
    'transactions': []
})

for txn in transactions:
    if txn['Status'] != 'succeeded':
        continue

    email = txn['Customer Email'].strip().lower()
    if not email:
        continue

    try:
        amount = float(txn['Amount'])
        expected_data[email]['total_spent'] += amount
        expected_data[email]['transaction_count'] += 1
        expected_data[email]['transactions'].append({
            'amount': amount,
            'date': txn['Created At']
        })
    except (ValueError, KeyError):
        pass

print(f"   Expected contacts to update: {len(expected_data)}")

# Fetch all contacts with transaction data from database
print("\n🔍 Fetching updated contacts from database...")
url = f"{SUPABASE_URL}/rest/v1/contacts"
params = {'select': 'email,total_spent,transaction_count,first_transaction_date,last_transaction_date,has_active_subscription,address_line_1,phone'}
response = requests.get(url, headers=headers, params=params)

if response.status_code != 200:
    print(f"❌ Error fetching contacts: {response.status_code}")
    exit(1)

contacts = response.json()
print(f"   Fetched {len(contacts)} contacts from database")

# Validation checks
print("\n" + "=" * 70)
print("VALIDATION CHECKS")
print("=" * 70)

errors = []
warnings = []

# Check 1: Verify transaction counts match
print("\n✓ Check 1: Transaction count accuracy")
mismatches = 0
for contact in contacts:
    email = contact['email'].lower()
    if email in expected_data:
        expected = expected_data[email]
        actual_count = contact.get('transaction_count', 0) or 0
        expected_count = expected['transaction_count']

        if actual_count != expected_count:
            mismatches += 1
            errors.append(f"  {email}: Expected {expected_count} transactions, got {actual_count}")

if mismatches == 0:
    print(f"  ✅ All transaction counts match ({len(expected_data)} contacts)")
else:
    print(f"  ❌ Found {mismatches} mismatches")
    for error in errors[:5]:
        print(error)

# Check 2: Verify total_spent calculations
print("\n✓ Check 2: Total spent accuracy")
errors_spent = []
for contact in contacts:
    email = contact['email'].lower()
    if email in expected_data:
        expected = expected_data[email]
        actual_spent = float(contact.get('total_spent', 0) or 0)
        expected_spent = expected['total_spent']

        # Allow for floating point precision differences (within $0.01)
        if abs(actual_spent - expected_spent) > 0.01:
            errors_spent.append(f"  {email}: Expected ${expected_spent:.2f}, got ${actual_spent:.2f}")

if len(errors_spent) == 0:
    print(f"  ✅ All amounts match")
else:
    print(f"  ❌ Found {len(errors_spent)} mismatches")
    for error in errors_spent[:5]:
        print(error)

# Check 3: Contacts that should have been updated but weren't
print("\n✓ Check 3: Missing updates")
missing_updates = []
for email in expected_data.keys():
    found = False
    for contact in contacts:
        if contact['email'].lower() == email:
            if contact.get('total_spent', 0) and contact.get('total_spent', 0) > 0:
                found = True
                break

    if not found:
        missing_updates.append(email)

if len(missing_updates) == 0:
    print(f"  ✅ All expected contacts were updated")
else:
    print(f"  ❌ {len(missing_updates)} contacts not updated:")
    for email in missing_updates[:5]:
        print(f"    - {email}")

# Check 4: Data consistency
print("\n✓ Check 4: Data consistency")
consistency_issues = []
for contact in contacts:
    total_spent = float(contact.get('total_spent', 0) or 0)
    transaction_count = contact.get('transaction_count', 0) or 0
    first_date = contact.get('first_transaction_date')
    last_date = contact.get('last_transaction_date')

    # If total_spent > 0, should have transaction_count > 0
    if total_spent > 0 and transaction_count == 0:
        consistency_issues.append(f"  {contact['email']}: Has total_spent but no transaction_count")

    # If transaction_count > 0, should have dates
    if transaction_count > 0 and not first_date:
        consistency_issues.append(f"  {contact['email']}: Has transactions but no first_transaction_date")

    # If has transactions, should have last_date
    if transaction_count > 0 and not last_date:
        consistency_issues.append(f"  {contact['email']}: Has transactions but no last_transaction_date")

if len(consistency_issues) == 0:
    print(f"  ✅ All data is consistent")
else:
    print(f"  ❌ Found {len(consistency_issues)} consistency issues:")
    for issue in consistency_issues[:5]:
        print(issue)

# Check 5: Address data quality
print("\n✓ Check 5: Address data quality")
contacts_with_addresses = sum(1 for c in contacts if c.get('address_line_1'))
contacts_with_phones = sum(1 for c in contacts if c.get('phone'))
print(f"  ✅ Contacts with addresses: {contacts_with_addresses}")
print(f"  ✅ Contacts with phones: {contacts_with_phones}")

# Check 6: Products validation
print("\n✓ Check 6: Products with offer IDs")
url = f"{SUPABASE_URL}/rest/v1/products"
params = {'select': 'name,kajabi_offer_id'}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    products = response.json()
    products_with_offers = sum(1 for p in products if p.get('kajabi_offer_id'))
    print(f"  ✅ Products with offer IDs: {products_with_offers}/{len(products)}")

    # Check for duplicate offer IDs
    offer_ids = [p['kajabi_offer_id'] for p in products if p.get('kajabi_offer_id')]
    duplicates = len(offer_ids) - len(set(offer_ids))
    if duplicates > 0:
        print(f"  ⚠️  Warning: {duplicates} duplicate offer IDs found")
    else:
        print(f"  ✅ No duplicate offer IDs")

# Check 7: Active subscription validation
print("\n✓ Check 7: Active subscription accuracy")
url = f"{SUPABASE_URL}/rest/v1/subscriptions"
params = {'select': 'contact_id,status'}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    subscriptions = response.json()
    active_sub_ids = set(s['contact_id'] for s in subscriptions if s['status'] == 'active')

    # Fetch contacts marked as having active subscriptions
    url = f"{SUPABASE_URL}/rest/v1/contacts"
    params = {'select': 'id,has_active_subscription', 'has_active_subscription': 'eq.true'}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        contacts_marked_active = set(c['id'] for c in response.json())

        # Check if they match
        if active_sub_ids == contacts_marked_active:
            print(f"  ✅ Active subscription flags are accurate ({len(active_sub_ids)} contacts)")
        else:
            missing = active_sub_ids - contacts_marked_active
            extra = contacts_marked_active - active_sub_ids
            if missing:
                print(f"  ⚠️  {len(missing)} contacts have active subs but not flagged")
            if extra:
                print(f"  ⚠️  {len(extra)} contacts flagged but no active subs")

# Summary
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

total_errors = len(errors) + len(errors_spent) + len(missing_updates) + len(consistency_issues)

if total_errors == 0:
    print("\n✅ ALL CHECKS PASSED - No errors found!")
    print("\n   The database update was 100% successful.")
else:
    print(f"\n❌ Found {total_errors} total issues")
    print("\n   Review the errors above for details.")

print("\n" + "=" * 70)
