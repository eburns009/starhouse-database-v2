#!/usr/bin/env python3
"""
Fix Subscription Product Mappings

This script updates subscriptions with the correct membership_product_id
based on their amount, then updates contacts.membership_level accordingly.

Problem: 129/225 active subscriptions have NULL membership_product_id
Solution: Match by subscription amount to membership product prices
"""

import os
from supabase import create_client, Client

# Initialize Supabase
SUPABASE_URL = "https://lnagadkqejnopgfxwlkb.supabase.co"
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxuYWdhZGtxZWpub3BnZnh3bGtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjk1Mzg4NjAsImV4cCI6MjA0NTExNDg2MH0.rJGlxJdWm17zxZ_FL0RdW4GVwfbjvnq75a3nfYTc1PQ')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Price to membership product mapping
PRICE_TO_PRODUCT = {
    12.00: {'slug': 'nova-individual', 'level': 'Nova', 'type': 'monthly'},
    22.00: {'slug': 'antares-individual', 'level': 'Antares', 'type': 'monthly'},
    33.00: {'slug': 'luminary-partner', 'level': 'Luminary Partner', 'type': 'monthly'},
    44.00: {'slug': 'aldebaran-individual', 'level': 'Aldebaran', 'type': 'monthly'},
    55.00: {'slug': 'celestial-partner', 'level': 'Celestial Partner', 'type': 'monthly'},
    88.00: {'slug': 'spica-individual', 'level': 'Spica', 'type': 'monthly'},
    99.00: {'slug': 'astral-partner', 'level': 'Astral Partner', 'type': 'monthly'},
    144.00: {'slug': 'nova-individual', 'level': 'Nova', 'type': 'annual'},
    242.00: {'slug': 'antares-individual', 'level': 'Antares', 'type': 'annual'},
    363.00: {'slug': 'luminary-partner', 'level': 'Luminary Partner', 'type': 'annual'},
    484.00: {'slug': 'aldebaran-individual', 'level': 'Aldebaran', 'type': 'annual'},
    605.00: {'slug': 'celestial-partner', 'level': 'Celestial Partner', 'type': 'annual'},
    968.00: {'slug': 'spica-individual', 'level': 'Spica', 'type': 'annual'},
    1089.00: {'slug': 'astral-partner', 'level': 'Astral Partner', 'type': 'annual'}
}


def get_membership_products():
    """Fetch all membership products"""
    response = supabase.table('membership_products').select('*').execute()
    return {p['product_slug']: p for p in response.data}


def get_subscriptions_without_product():
    """Get all active subscriptions without membership_product_id"""
    response = supabase.table('subscriptions')\
        .select('id, contact_id, amount, billing_cycle, is_annual')\
        .eq('status', 'active')\
        .is_('membership_product_id', 'null')\
        .execute()
    return response.data


def update_subscription(subscription_id, membership_product_id):
    """Update a subscription with its membership product"""
    response = supabase.table('subscriptions')\
        .update({'membership_product_id': membership_product_id})\
        .eq('id', subscription_id)\
        .execute()
    return response


def update_contact_membership_level(contact_id, membership_level):
    """Update contact's membership level"""
    response = supabase.table('contacts')\
        .update({'membership_level': membership_level})\
        .eq('id', contact_id)\
        .execute()
    return response


def main():
    print("=" * 80)
    print("FIX SUBSCRIPTION PRODUCT MAPPINGS")
    print("=" * 80)

    # Fetch membership products
    print("\n1. Fetching membership products...")
    products = get_membership_products()
    print(f"   Found {len(products)} membership products")

    # Fetch subscriptions without product
    print("\n2. Fetching subscriptions without membership_product_id...")
    subscriptions = get_subscriptions_without_product()
    print(f"   Found {len(subscriptions)} subscriptions to fix")

    if len(subscriptions) == 0:
        print("\n✅ All subscriptions already have membership_product_id!")
        return

    # Group by amount
    by_amount = {}
    for sub in subscriptions:
        amount = float(sub['amount'])
        if amount not in by_amount:
            by_amount[amount] = []
        by_amount[amount].append(sub)

    print(f"\n   Subscription amounts found: {sorted(by_amount.keys())}")

    # Show mapping plan
    print("\n3. Mapping plan:")
    print("-" * 80)
    for amount in sorted(by_amount.keys()):
        count = len(by_amount[amount])
        if amount in PRICE_TO_PRODUCT:
            mapping = PRICE_TO_PRODUCT[amount]
            product_slug = mapping['slug']
            level = mapping['level']
            sub_type = mapping['type']
            print(f"   ${amount:7.2f} x {count:3d} → {level:20s} ({sub_type})")
        else:
            print(f"   ${amount:7.2f} x {count:3d} → ⚠️  NO MAPPING FOUND")
    print("-" * 80)

    # Confirm
    print("\n4. Ready to update subscriptions and contacts")
    response = input("   Continue? (yes/no): ").strip().lower()

    if response != 'yes':
        print("\n❌ Aborted by user")
        return

    # Update subscriptions
    print("\n5. Updating subscriptions...")
    updated_count = 0
    skipped_count = 0
    contact_updates = {}  # Track contact membership levels

    for sub in subscriptions:
        amount = float(sub['amount'])

        if amount not in PRICE_TO_PRODUCT:
            print(f"   ⚠️  Skipping ${amount} - no mapping found")
            skipped_count += 1
            continue

        mapping = PRICE_TO_PRODUCT[amount]
        product_slug = mapping['slug']
        membership_level = mapping['level']

        if product_slug not in products:
            print(f"   ⚠️  Product slug '{product_slug}' not found in database")
            skipped_count += 1
            continue

        product = products[product_slug]

        # Update subscription
        try:
            update_subscription(sub['id'], product['id'])
            updated_count += 1

            # Track contact for level update
            contact_id = sub['contact_id']
            if contact_id not in contact_updates:
                contact_updates[contact_id] = membership_level

            if updated_count % 10 == 0:
                print(f"   Updated {updated_count} subscriptions...")

        except Exception as e:
            print(f"   ❌ Error updating subscription {sub['id']}: {e}")
            skipped_count += 1

    print(f"\n   ✅ Updated {updated_count} subscriptions")
    if skipped_count > 0:
        print(f"   ⚠️  Skipped {skipped_count} subscriptions")

    # Update contact membership levels
    print(f"\n6. Updating {len(contact_updates)} contacts with membership levels...")
    contact_updated = 0

    for contact_id, level in contact_updates.items():
        try:
            update_contact_membership_level(contact_id, level)
            contact_updated += 1
            if contact_updated % 10 == 0:
                print(f"   Updated {contact_updated} contacts...")
        except Exception as e:
            print(f"   ❌ Error updating contact {contact_id}: {e}")

    print(f"\n   ✅ Updated {contact_updated} contacts")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Subscriptions updated: {updated_count}")
    print(f"Subscriptions skipped: {skipped_count}")
    print(f"Contacts updated: {contact_updated}")
    print("=" * 80)

    # Verify
    print("\n7. Verification...")
    remaining = supabase.table('subscriptions')\
        .select('id', count='exact')\
        .eq('status', 'active')\
        .is_('membership_product_id', 'null')\
        .execute()

    remaining_count = remaining.count if hasattr(remaining, 'count') else 0
    print(f"   Remaining subscriptions without product: {remaining_count}")

    if remaining_count == 0:
        print("\n🎉 SUCCESS! All active subscriptions now have membership products!")
    else:
        print(f"\n⚠️  {remaining_count} subscriptions still need attention")

    print("\nDone!")


if __name__ == '__main__':
    main()
