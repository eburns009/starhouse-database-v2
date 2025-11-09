#!/usr/bin/env python3
"""
Update Contacts with Transaction Data
======================================
This script:
1. Reads the new transactions.csv file
2. Computes transaction summaries per contact
3. Updates contacts table with:
   - Address data (phone, address, city, state, zip, country)
   - Transaction summaries (total_spent, transaction_count, dates)
   - Subscription status
4. Updates products table with offer IDs

Requires: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
import requests
import json

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://lnagadkqejnopgfxwlkb.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
TRANSACTIONS_FILE = '/workspaces/starhouse-database-v2/data/production/transactions.csv'

# Headers for Supabase API
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def read_transactions():
    """Read and parse transactions CSV"""
    print("📖 Reading transactions.csv...")

    with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        transactions = list(reader)

    print(f"   Found {len(transactions)} transactions")
    return transactions

def compute_contact_summaries(transactions):
    """Compute transaction summaries per contact email"""
    print("\n📊 Computing contact summaries...")

    contact_data = defaultdict(lambda: {
        'email': None,
        'transactions': [],
        'addresses': [],
        'phones': set(),
        'customer_names': set(),
        'payment_methods': [],
        'coupons': 0,
        'offers': set()
    })

    for txn in transactions:
        email = txn['Customer Email'].strip().lower()
        if not email:
            continue

        data = contact_data[email]
        data['email'] = email

        # Transaction data
        if txn['Status'] == 'succeeded':
            try:
                amount = float(txn['Amount'])
                txn_date = txn['Created At']
                data['transactions'].append({
                    'amount': amount,
                    'date': txn_date,
                    'type': txn['Type']
                })

                # Payment method
                if txn['Payment Method']:
                    data['payment_methods'].append(txn['Payment Method'])

                # Coupons
                if txn['Coupon Used'].strip():
                    data['coupons'] += 1

                # Offers
                if txn['Offer ID'].strip():
                    data['offers'].add((txn['Offer ID'], txn['Offer Title']))

            except (ValueError, KeyError) as e:
                print(f"   ⚠️  Skipping invalid transaction: {e}")

        # Address data (take most recent/complete)
        if txn['Address'].strip():
            data['addresses'].append({
                'address_line_1': txn['Address'].strip(),
                'address_line_2': txn['Address 2'].strip(),
                'city': txn['City'].strip(),
                'state': txn['State'].strip(),
                'postal_code': txn['Zipcode'].strip(),
                'country': txn['Country'].strip()
            })

        # Phone
        if txn['Phone'].strip():
            data['phones'].add(txn['Phone'].strip())

        # Customer name
        if txn['Customer Name'].strip():
            data['customer_names'].add(txn['Customer Name'].strip())

    # Compute summaries
    summaries = {}
    for email, data in contact_data.items():
        if not data['transactions']:
            continue

        # Sort transactions by date
        sorted_txns = sorted(data['transactions'], key=lambda x: x['date'])

        summary = {
            'email': email,
            'total_spent': sum(t['amount'] for t in data['transactions']),
            'transaction_count': len(data['transactions']),
            'first_transaction_date': sorted_txns[0]['date'],
            'last_transaction_date': sorted_txns[-1]['date'],
            'favorite_payment_method': max(set(data['payment_methods']),
                                          key=data['payment_methods'].count) if data['payment_methods'] else None,
            'total_coupons_used': data['coupons'],
            'address': data['addresses'][-1] if data['addresses'] else {},
            'phone': list(data['phones'])[0] if data['phones'] else None,
            'offers': list(data['offers'])
        }
        summaries[email] = summary

    print(f"   Computed summaries for {len(summaries)} contacts")
    return summaries

def get_contact_by_email(email):
    """Fetch contact from database by email"""
    url = f"{SUPABASE_URL}/rest/v1/contacts"
    params = {'email': f'eq.{email}', 'select': 'id,email'}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        results = response.json()
        return results[0] if results else None
    return None

def update_contact(contact_id, updates):
    """Update a contact via Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/contacts"
    params = {'id': f'eq.{contact_id}'}

    response = requests.patch(url, headers=headers, params=params, json=updates)
    return response.status_code in [200, 204]

def get_active_subscriptions():
    """Get all active subscriptions grouped by contact_id"""
    print("\n💳 Checking active subscriptions...")
    url = f"{SUPABASE_URL}/rest/v1/subscriptions"
    params = {'status': 'eq.active', 'select': 'contact_id'}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        active_subs = set(s['contact_id'] for s in response.json())
        print(f"   Found {len(active_subs)} contacts with active subscriptions")
        return active_subs
    return set()

def update_contacts_batch(summaries):
    """Update all contacts with transaction data"""
    print("\n🔄 Updating contacts...")

    # Get active subscriptions
    active_subscription_contacts = get_active_subscriptions()

    updated = 0
    not_found = 0
    errors = 0

    for email, summary in summaries.items():
        # Find contact
        contact = get_contact_by_email(email)
        if not contact:
            not_found += 1
            continue

        # Prepare updates
        updates = {
            'total_spent': summary['total_spent'],
            'transaction_count': summary['transaction_count'],
            'first_transaction_date': summary['first_transaction_date'],
            'last_transaction_date': summary['last_transaction_date'],
            'favorite_payment_method': summary['favorite_payment_method'],
            'total_coupons_used': summary['total_coupons_used'],
            'has_active_subscription': contact['id'] in active_subscription_contacts,
            'updated_at': datetime.now().isoformat()
        }

        # Add address data if available and not already set
        if summary['address']:
            addr = summary['address']
            if addr.get('address_line_1'):
                updates['address_line_1'] = addr['address_line_1']
            if addr.get('address_line_2'):
                updates['address_line_2'] = addr['address_line_2']
            if addr.get('city'):
                updates['city'] = addr['city']
            if addr.get('state'):
                updates['state'] = addr['state']
            if addr.get('postal_code'):
                updates['postal_code'] = addr['postal_code']
            if addr.get('country'):
                updates['country'] = addr['country']

        # Add phone if available
        if summary['phone']:
            updates['phone'] = summary['phone']

        # Update contact
        if update_contact(contact['id'], updates):
            updated += 1
            if updated % 100 == 0:
                print(f"   Updated {updated} contacts...")
        else:
            errors += 1

    print(f"\n✅ Update complete:")
    print(f"   - Updated: {updated}")
    print(f"   - Not found: {not_found}")
    print(f"   - Errors: {errors}")

    return updated, not_found, errors

def extract_unique_offers(summaries):
    """Extract all unique offers from summaries"""
    print("\n🎁 Extracting unique offers...")

    offers = {}
    for summary in summaries.values():
        for offer_id, offer_title in summary['offers']:
            if offer_id:
                offers[offer_id] = offer_title

    print(f"   Found {len(offers)} unique offers")
    return offers

def main():
    """Main execution"""
    print("=" * 70)
    print("UPDATE CONTACTS FROM TRANSACTIONS")
    print("=" * 70)

    if not SUPABASE_KEY:
        print("❌ Error: SUPABASE_KEY environment variable not set")
        sys.exit(1)

    # Read transactions
    transactions = read_transactions()

    # Compute summaries
    summaries = compute_contact_summaries(transactions)

    # Update contacts
    updated, not_found, errors = update_contacts_batch(summaries)

    # Extract offers
    offers = extract_unique_offers(summaries)
    print(f"\n📝 Offer IDs that can be added to products table: {len(offers)}")

    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  - Contacts updated: {updated}")
    print(f"  - Contacts not found: {not_found}")
    print(f"  - Unique offers found: {len(offers)}")

    if not_found > 0:
        print(f"\n⚠️  {not_found} email addresses from transactions not found in contacts table")
        print("     These may be new contacts that need to be imported separately")

if __name__ == '__main__':
    main()
