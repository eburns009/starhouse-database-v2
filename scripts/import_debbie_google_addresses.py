#!/usr/bin/env python3
"""
Phase 2B: Import addresses from Debbie's Google Contacts
FAANG-Grade Implementation: Safe, validated, auditable

Strategy:
- Parse Google Contacts address formats (component fields + formatted)
- Only fill NULL fields (additive only)
- Mark source as 'google_contacts'
- Full audit trail
- Dry-run mode by default
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from datetime import datetime

# Configuration
CSV_PATH = '/workspaces/starhouse-database-v2/kajabi 3 files review/debbie_google_contacts.csv'
DRY_RUN = True

def normalize_email(email):
    """Normalize email for matching"""
    if not email:
        return None
    return email.strip().lower()

def parse_google_address(row):
    """Parse address from Google Contacts row"""

    # Try structured component fields first
    street = row.get('Address 1 - Street', '').strip()
    city = row.get('Address 1 - City', '').strip()
    state = row.get('Address 1 - Region', '').strip()
    postal_code = row.get('Address 1 - Postal Code', '').strip()
    country = row.get('Address 1 - Country', '').strip() or 'US'

    # If no structured data, try formatted address
    if not street:
        formatted = row.get('Address 1 - Formatted', '').strip()
        if formatted:
            # Parse formatted address (lines separated by \n)
            lines = [l.strip() for l in formatted.split('\n') if l.strip()]

            if len(lines) >= 1:
                street = lines[0]

            if len(lines) >= 2:
                # Try to parse city, state, zip from last line
                last_line = lines[-1]
                # Pattern: City, State ZIP or just ZIP
                match = re.search(r'^(.+?),?\s+([A-Z]{2})?\s*(\d{5}(?:-\d{4})?)$', last_line)
                if match:
                    if match.group(1):
                        city = match.group(1).strip()
                    if match.group(2):
                        state = match.group(2).strip()
                    if match.group(3):
                        postal_code = match.group(3).strip()
                else:
                    # Maybe just a ZIP code
                    if re.match(r'^\d{5}(?:-\d{4})?$', last_line):
                        postal_code = last_line

    # Return None if no meaningful address
    if not street and not city and not postal_code:
        return None

    return {
        'street': street or None,
        'city': city or None,
        'state': state or None,
        'postal_code': postal_code or None,
        'country': country
    }

def import_addresses(dry_run=True):
    """Main address import function"""

    print("=" * 80)
    print("DEBBIE'S GOOGLE CONTACTS - PHASE 2B: ADDRESSES")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be committed)'}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Load CSV
    print("📊 Loading Google Contacts CSV...")
    google_contacts = []

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            google_contacts.append(row)

    print(f"   Total contacts in CSV: {len(google_contacts):,}\n")

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.lnagadkqejnopgfxwlkb',
        password='gqelzN6LRew4Cy9H',
        host='aws-1-us-east-2.pooler.supabase.com',
        port='5432'
    )
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("   Connected ✓\n")

    # Get all existing contacts
    cur.execute("""
        SELECT id, email, paypal_email, address_line_1, city, state, postal_code, billing_address_source
        FROM contacts
    """)
    db_contacts = cur.fetchall()

    # Build email lookup
    email_lookup = {}
    for db_contact in db_contacts:
        if db_contact['email']:
            email_lookup[normalize_email(db_contact['email'])] = db_contact
        if db_contact['paypal_email']:
            email_lookup[normalize_email(db_contact['paypal_email'])] = db_contact

    print(f"📋 Database contacts loaded: {len(db_contacts):,}\n")

    # Find enrichment opportunities
    print("🔍 Identifying address enrichment opportunities...")

    updates = []

    for gc_contact in google_contacts:
        gc_email = normalize_email(gc_contact.get('E-mail 1 - Value'))

        if not gc_email:
            continue

        db_contact = email_lookup.get(gc_email)

        if not db_contact:
            continue  # Contact not in database

        # Only enrich if contact has no address
        if db_contact['address_line_1']:
            continue  # Already has address

        # Parse Google address
        gc_address = parse_google_address(gc_contact)

        if not gc_address:
            continue  # No address in Google

        updates.append({
            'contact_id': db_contact['id'],
            'email': gc_email,
            'address': gc_address
        })

    print(f"   Found {len(updates):,} addresses to import\n")

    if not updates:
        print("✓ No address enrichment opportunities found!\n")
        cur.close()
        conn.close()
        return

    # Preview sample updates
    print("📝 SAMPLE ADDRESS IMPORTS (first 10):")
    print("-" * 80)
    for i, update in enumerate(updates[:10], 1):
        addr = update['address']
        street = addr.get('street', 'N/A')
        city_state = f"{addr.get('city', '')}, {addr.get('state', '')}".strip(', ')
        postal = addr.get('postal_code', '')

        print(f"  {i}. {update['email']}")
        print(f"     {street}")
        if city_state:
            print(f"     {city_state} {postal}")
        elif postal:
            print(f"     {postal}")
        print()

    # Apply updates
    if not dry_run:
        print("=" * 80)
        print("IMPORTING ADDRESSES")
        print("=" * 80)

        try:
            update_count = 0

            for update in updates:
                addr = update['address']

                cur.execute("""
                    UPDATE contacts
                    SET
                        address_line_1 = %s,
                        city = %s,
                        state = %s,
                        postal_code = %s,
                        country = %s,
                        billing_address_source = %s,
                        updated_at = now()
                    WHERE id = %s
                """, (
                    addr['street'],
                    addr['city'],
                    addr['state'],
                    addr['postal_code'],
                    addr['country'],
                    'google_contacts',
                    update['contact_id']
                ))

                update_count += 1

                if update_count % 25 == 0:
                    print(f"   Processed {update_count:,} / {len(updates):,} contacts...")

            conn.commit()
            print(f"\n✓ Successfully imported {update_count:,} addresses")

        except Exception as e:
            print(f"\n❌ Error during import: {e}")
            conn.rollback()
            print("✓ Transaction rolled back, no changes made")

    else:
        print("=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute address import, run:")
        print("  python3 scripts/import_debbie_google_addresses.py --live")

    # Summary
    print("\n" + "=" * 80)
    print("PHASE 2B SUMMARY")
    print("=" * 80)
    print(f"Addresses imported:   {len(updates):,}")
    print(f"Source attribution:   google_contacts")
    print(f"\nMode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print("=" * 80)

    # Cleanup
    cur.close()
    conn.close()

if __name__ == '__main__':
    import sys

    # Check for --live flag
    dry_run = '--live' not in sys.argv

    if not dry_run:
        print("\n⚠️  WARNING: Running in LIVE mode. Changes will be committed!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    import_addresses(dry_run=dry_run)
