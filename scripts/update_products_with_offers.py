#!/usr/bin/env python3
"""
Update Products with Offer IDs
================================
This script:
1. Reads the transactions.csv file
2. Extracts unique offer IDs and titles
3. Matches offers to existing products by name
4. Updates products table with kajabi_offer_id
5. Reports any new offers that don't match existing products

Requires: SUPABASE_URL and SUPABASE_KEY environment variables
"""

import csv
import os
import sys
import requests
from difflib import SequenceMatcher

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

def similarity(a, b):
    """Calculate string similarity ratio"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_offers_from_transactions():
    """Extract unique offers from transactions CSV"""
    print("📖 Reading transactions.csv...")

    offers = {}
    with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            offer_id = row['Offer ID'].strip()
            offer_title = row['Offer Title'].strip()
            if offer_id and offer_title:
                offers[offer_id] = offer_title

    print(f"   Found {len(offers)} unique offers")
    return offers

def get_all_products():
    """Fetch all products from database"""
    print("\n📦 Fetching existing products...")

    url = f"{SUPABASE_URL}/rest/v1/products"
    params = {'select': 'id,name,kajabi_offer_id'}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        products = response.json()
        print(f"   Found {len(products)} existing products")
        return products
    else:
        print(f"   ❌ Error fetching products: {response.status_code}")
        return []

def match_offers_to_products(offers, products):
    """Match offer titles to product names"""
    print("\n🔗 Matching offers to products...")

    matches = []
    unmatched_offers = []

    # Create a dict of products by normalized name
    products_by_name = {p['name'].lower().strip(): p for p in products}

    for offer_id, offer_title in offers.items():
        offer_lower = offer_title.lower().strip()

        # Try exact match first
        if offer_lower in products_by_name:
            product = products_by_name[offer_lower]
            matches.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'offer_id': offer_id,
                'offer_title': offer_title,
                'match_type': 'exact'
            })
        else:
            # Try fuzzy match
            best_match = None
            best_score = 0.0

            for product_name, product in products_by_name.items():
                score = similarity(offer_title, product_name)
                if score > best_score:
                    best_score = score
                    best_match = product

            # Use fuzzy match if similarity > 80%
            if best_score > 0.80 and best_match:
                matches.append({
                    'product_id': best_match['id'],
                    'product_name': best_match['name'],
                    'offer_id': offer_id,
                    'offer_title': offer_title,
                    'match_type': 'fuzzy',
                    'similarity': best_score
                })
            else:
                unmatched_offers.append({
                    'offer_id': offer_id,
                    'offer_title': offer_title
                })

    print(f"   Matched {len(matches)} offers to products")
    print(f"   Unmatched offers: {len(unmatched_offers)}")

    return matches, unmatched_offers

def update_product(product_id, offer_id):
    """Update a product with offer ID"""
    url = f"{SUPABASE_URL}/rest/v1/products"
    params = {'id': f'eq.{product_id}'}
    updates = {'kajabi_offer_id': offer_id}

    response = requests.patch(url, headers=headers, params=params, json=updates)
    return response.status_code in [200, 204]

def update_products_batch(matches):
    """Update all matched products"""
    print("\n🔄 Updating products with offer IDs...")

    updated = 0
    errors = 0

    for match in matches:
        if update_product(match['product_id'], match['offer_id']):
            updated += 1
            if updated % 10 == 0:
                print(f"   Updated {updated} products...")
        else:
            errors += 1
            print(f"   ❌ Failed to update: {match['product_name']}")

    print(f"\n✅ Update complete:")
    print(f"   - Updated: {updated}")
    print(f"   - Errors: {errors}")

    return updated, errors

def save_unmatched_offers(unmatched_offers):
    """Save unmatched offers to a CSV file for review"""
    if not unmatched_offers:
        return

    output_file = '/workspaces/starhouse-database-v2/data/unmatched_offers.csv'
    print(f"\n💾 Saving unmatched offers to {output_file}")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['offer_id', 'offer_title'])
        writer.writeheader()
        writer.writerows(unmatched_offers)

    print(f"   Saved {len(unmatched_offers)} unmatched offers")

def main():
    """Main execution"""
    print("=" * 70)
    print("UPDATE PRODUCTS WITH OFFER IDs")
    print("=" * 70)

    if not SUPABASE_KEY:
        print("❌ Error: SUPABASE_KEY environment variable not set")
        sys.exit(1)

    # Extract offers from transactions
    offers = extract_offers_from_transactions()

    # Get existing products
    products = get_all_products()

    # Match offers to products
    matches, unmatched = match_offers_to_products(offers, products)

    # Show sample matches
    print("\n📋 Sample matches:")
    for match in matches[:5]:
        match_type = match['match_type']
        if match_type == 'fuzzy':
            print(f"   {match['offer_title']} → {match['product_name']} ({match_type}, {match['similarity']:.0%})")
        else:
            print(f"   {match['offer_title']} → {match['product_name']} ({match_type})")

    # Update products
    updated, errors = update_products_batch(matches)

    # Save unmatched offers
    save_unmatched_offers(unmatched)

    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  - Total offers: {len(offers)}")
    print(f"  - Products updated: {updated}")
    print(f"  - Unmatched offers: {len(unmatched)}")

    if unmatched:
        print(f"\n⚠️  {len(unmatched)} offers could not be matched to existing products")
        print("     Review data/unmatched_offers.csv to create new product entries")

if __name__ == '__main__':
    main()
