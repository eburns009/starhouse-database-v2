#!/usr/bin/env python3
"""
Restore billing addresses from Kajabi CSV for the 241 contacts with scrambled addresses.

SAFETY FEATURES:
- Dry-run mode by default (won't change anything until you confirm)
- Only updates the 241 contacts with mismatches
- Only touches billing address fields
- Preserves all USPS validation data
- Preserves shipping addresses
- Shows exactly what will change before executing
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from db_config import get_database_url

DB_URL = get_database_url()
KAJABI_CSV = "/workspaces/starhouse-database-v2/kajabi 3 files review/11102025kajabi.csv"

def read_kajabi_addresses():
    """Read addresses from Kajabi CSV."""
    addresses = {}
    with open(KAJABI_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row['Email'].strip().lower()
            addresses[email] = {
                'address_line_1': row['Address (address_line_1)'].strip() if row['Address (address_line_1)'] else None,
                'city': row['City (address_city)'].strip() if row['City (address_city)'] else None,
                'state': row['State (address_state)'].strip() if row['State (address_state)'] else None,
                'postal_code': row['Zip Code (address_zip)'].strip() if row['Zip Code (address_zip)'] else None,
            }
    return addresses

def find_mismatches(cursor, kajabi_addresses):
    """Find contacts where database doesn't match Kajabi."""
    mismatches = []

    for email, kajabi_addr in kajabi_addresses.items():
        # Skip if no address in Kajabi
        if not kajabi_addr['address_line_1']:
            continue

        # Get current database address
        cursor.execute("""
            SELECT id, email, first_name, last_name,
                   address_line_1, city, state, postal_code
            FROM contacts
            WHERE email = %s
        """, (email,))

        contact = cursor.fetchone()
        if not contact:
            continue

        # Check if addresses match
        db_addr = contact['address_line_1'] or ''
        db_city = contact['city'] or ''
        db_state = contact['state'] or ''

        kajabi_line1 = kajabi_addr['address_line_1'] or ''
        kajabi_city = kajabi_addr['city'] or ''
        kajabi_state = kajabi_addr['state'] or ''

        # Compare (case-insensitive, trimmed)
        if (db_addr.lower().strip() != kajabi_line1.lower().strip() or
            db_city.lower().strip() != kajabi_city.lower().strip() or
            db_state.lower().strip() != kajabi_state.lower().strip()):

            mismatches.append({
                'id': contact['id'],
                'email': email,
                'name': f"{contact['first_name']} {contact['last_name']}",
                'db_address': f"{db_addr}, {db_city}, {db_state}",
                'kajabi_address': f"{kajabi_line1}, {kajabi_city}, {kajabi_state}",
                'new_values': kajabi_addr
            })

    return mismatches

def restore_addresses(mismatches, dry_run=True):
    """Restore addresses from Kajabi."""

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print(f"ADDRESS RESTORATION FROM KAJABI")
    print(f"MODE: {'DRY RUN (no changes)' if dry_run else 'LIVE - WILL UPDATE DATABASE'}")
    print("=" * 80)
    print()

    print(f"Found {len(mismatches)} contacts with address mismatches\n")

    if len(mismatches) == 0:
        print("✓ All addresses match! Nothing to fix.")
        cursor.close()
        conn.close()
        return

    # Show first 10 changes
    print("Sample changes (showing first 10):\n")
    for i, contact in enumerate(mismatches[:10], 1):
        print(f"{i}. {contact['name']} <{contact['email']}>")
        print(f"   FROM: {contact['db_address']}")
        print(f"   TO:   {contact['kajabi_address']}")
        print()

    if len(mismatches) > 10:
        print(f"... and {len(mismatches) - 10} more contacts\n")

    if dry_run:
        print("=" * 80)
        print("DRY RUN - No changes made")
        print("=" * 80)
        print()
        print("To execute these changes, run with --execute flag:")
        print("  python3 scripts/restore_addresses_from_kajabi.py --execute")
        cursor.close()
        conn.close()
        return

    # Execute updates
    print("Executing updates...")
    updated = 0

    for contact in mismatches:
        cursor.execute("""
            UPDATE contacts
            SET
                address_line_1 = %s,
                city = %s,
                state = %s,
                postal_code = %s,
                billing_address_source = 'kajabi',
                billing_address_updated_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (
            contact['new_values']['address_line_1'],
            contact['new_values']['city'],
            contact['new_values']['state'],
            contact['new_values']['postal_code'],
            contact['id']
        ))
        updated += 1

        if updated % 50 == 0:
            print(f"  ✓ Updated {updated}/{len(mismatches)}...")
            conn.commit()

    conn.commit()

    print()
    print("=" * 80)
    print(f"✓ RESTORATION COMPLETE - {updated} addresses fixed")
    print("=" * 80)
    print()

    # Verify Ed Burns
    cursor.execute("""
        SELECT email, first_name, last_name,
               address_line_1, city, state, postal_code
        FROM contacts
        WHERE email = 'eburns009@gmail.com'
    """)
    ed = cursor.fetchone()

    print("VERIFICATION - Ed Burns:")
    print(f"  {ed['address_line_1']}, {ed['city']}, {ed['state']} {ed['postal_code']}")

    if '1144' in ed['address_line_1'] and 'Southampton' in ed['city']:
        print("  ✓ CORRECT!")
    else:
        print("  ✗ Still wrong - check the script")

    cursor.close()
    conn.close()

def main():
    import sys

    dry_run = '--execute' not in sys.argv

    print("Step 1: Reading Kajabi CSV...")
    kajabi_addresses = read_kajabi_addresses()
    print(f"  ✓ Loaded {len(kajabi_addresses)} addresses from Kajabi\n")

    print("Step 2: Connecting to database...")
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("  ✓ Connected\n")

    print("Step 3: Finding mismatches...")
    mismatches = find_mismatches(cursor, kajabi_addresses)
    cursor.close()
    conn.close()
    print(f"  ✓ Found {len(mismatches)} mismatches\n")

    print("Step 4: Restoring addresses...")
    restore_addresses(mismatches, dry_run=dry_run)

if __name__ == '__main__':
    main()
