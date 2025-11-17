#!/usr/bin/env python3
"""
Google Contacts Address Import - Phase 2B
FAANG-Grade Implementation: Safe, auditable, reversible

Imports addresses from Google Contacts for contacts without addresses
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import sys
import re

# Configuration
DRY_RUN = True

def parse_google_address(row):
    """
    Extract address components from Google Contacts row.
    Prioritize component fields over formatted address.
    """
    address_data = {}

    # Use component fields if available (more structured)
    street = row.get('Address 1 - Street')
    city = row.get('Address 1 - City')
    state = row.get('Address 1 - Region')
    postal_code = row.get('Address 1 - Postal Code')
    country = row.get('Address 1 - Country')

    # Use formatted address as fallback
    formatted = row.get('Address 1 - Formatted')

    # Build address data
    if pd.notna(street):
        address_data['street'] = str(street).strip()
    elif pd.notna(formatted):
        # Try to extract street from formatted address (first line)
        lines = str(formatted).split('\n')
        if lines:
            address_data['street'] = lines[0].strip()

    if pd.notna(city):
        address_data['city'] = str(city).strip()

    if pd.notna(state):
        address_data['state'] = str(state).strip()

    if pd.notna(postal_code):
        # Clean postal code (remove extra text)
        postal = str(postal_code).strip()
        # Extract just the 5-digit or 5+4 digit ZIP
        match = re.search(r'\b(\d{5})(?:-(\d{4}))?\b', postal)
        if match:
            address_data['postal_code'] = match.group(0)
        else:
            address_data['postal_code'] = postal

    if pd.notna(country):
        address_data['country'] = str(country).strip()

    # Store original formatted address for reference
    if pd.notna(formatted):
        address_data['formatted'] = str(formatted).strip()

    return address_data if address_data else None

def is_valid_address(address_data):
    """
    Basic validation to ensure address has minimum required fields.
    """
    # Must have at least a street or postal code
    if not address_data:
        return False

    has_street = 'street' in address_data and address_data['street']
    has_postal = 'postal_code' in address_data and address_data['postal_code']

    # Must have at least one
    if not (has_street or has_postal):
        return False

    # If we have a street, prefer to also have city or postal code
    if has_street:
        has_city = 'city' in address_data and address_data['city']
        if has_city or has_postal:
            return True

    # If we only have postal code, that's acceptable
    if has_postal:
        return True

    return False

def import_addresses(dry_run=True):
    """Main import function"""

    print("=" * 80)
    print("GOOGLE CONTACTS ADDRESS IMPORT - PHASE 2B")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be committed)'}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Load Google Contacts
    print("📥 Loading Google Contacts...")
    df = pd.read_csv('/workspaces/starhouse-database-v2/kajabi 3 files review/ascpr_google_contacts.csv')
    print(f"   Loaded {len(df):,} contacts from Google\n")

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

    # Get all database contacts
    print("📊 Loading database contacts...")
    cur.execute("""
        SELECT id, email, paypal_email,
               address_line_1, address_line_2, city, state, postal_code, country
        FROM contacts
    """)
    db_contacts = cur.fetchall()

    email_to_contact = {}
    for contact in db_contacts:
        if contact['email']:
            email_to_contact[contact['email'].lower().strip()] = contact
        if contact['paypal_email']:
            email_to_contact[contact['paypal_email'].lower().strip()] = contact

    print(f"   Loaded {len(db_contacts):,} database contacts\n")

    # Process addresses
    print("🔍 Analyzing address enrichment opportunities...\n")

    updates = []
    stats = {
        'matched': 0,
        'has_google_address': 0,
        'already_has_db_address': 0,
        'can_enrich': 0,
        'invalid_address': 0,
        'unmatched': 0
    }

    for idx, row in df.iterrows():
        # Parse address from Google
        address_data = parse_google_address(row)

        if not address_data:
            continue  # No address in Google

        stats['has_google_address'] += 1

        # Validate address quality
        if not is_valid_address(address_data):
            stats['invalid_address'] += 1
            continue

        # Try to match contact
        google_emails = []
        for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
            if pd.notna(row.get(col)):
                google_emails.append(row[col].lower().strip())

        # Find match
        db_contact = None
        matched_email = None
        for email in google_emails:
            if email in email_to_contact:
                db_contact = email_to_contact[email]
                matched_email = email
                break

        if not db_contact:
            stats['unmatched'] += 1
            continue

        stats['matched'] += 1

        # Check if database already has address
        if db_contact['address_line_1']:
            stats['already_has_db_address'] += 1
            continue

        # Can enrich!
        stats['can_enrich'] += 1

        update = {
            'contact_id': db_contact['id'],
            'email': matched_email,
            'address_data': address_data,
            'changes': []
        }

        # Build change list
        if address_data.get('street'):
            update['changes'].append({
                'field': 'address_line_1',
                'old': None,
                'new': address_data['street']
            })

        if address_data.get('city'):
            update['changes'].append({
                'field': 'city',
                'old': None,
                'new': address_data['city']
            })

        if address_data.get('state'):
            update['changes'].append({
                'field': 'state',
                'old': None,
                'new': address_data['state']
            })

        if address_data.get('postal_code'):
            update['changes'].append({
                'field': 'postal_code',
                'old': None,
                'new': address_data['postal_code']
            })

        if address_data.get('country'):
            update['changes'].append({
                'field': 'country',
                'old': None,
                'new': address_data['country']
            })

        # Add source tracking
        update['changes'].append({
            'field': 'billing_address_source',
            'old': None,
            'new': 'google_contacts'
        })

        updates.append(update)

    # Print summary
    print("=" * 80)
    print("ADDRESS ENRICHMENT SUMMARY")
    print("=" * 80)

    print(f"\nGoogle contacts analyzed: {len(df):,}")
    print(f"  With addresses: {stats['has_google_address']:,}")
    print(f"  Matched to database: {stats['matched']:,}")
    print(f"  Already have database address: {stats['already_has_db_address']:,}")
    print(f"  Invalid/incomplete addresses: {stats['invalid_address']:,}")
    print(f"  Unmatched (new contacts): {stats['unmatched']:,}")
    print(f"\n⭐ Can enrich: {stats['can_enrich']:,} contacts")
    print(f"\nTotal updates to apply: {len(updates):,}\n")

    if not updates:
        print("✓ No addresses to import. Database is already complete!\n")
        cur.close()
        conn.close()
        return

    # Show sample updates
    print("=" * 80)
    print("SAMPLE UPDATES (first 10)")
    print("=" * 80)

    for i, update in enumerate(updates[:10]):
        print(f"\n{i+1}. Contact: {update['email']}")
        addr_data = update['address_data']
        if addr_data.get('street'):
            print(f"   Street: {addr_data['street']}")
        if addr_data.get('city'):
            print(f"   City: {addr_data['city']}")
        if addr_data.get('state'):
            print(f"   State: {addr_data['state']}")
        if addr_data.get('postal_code'):
            print(f"   ZIP: {addr_data['postal_code']}")
        if addr_data.get('formatted'):
            print(f"   (Original: {addr_data['formatted'][:60]}...)")

    # Execute updates if not dry run
    if not dry_run:
        print("\n" + "=" * 80)
        print("EXECUTING UPDATES")
        print("=" * 80)

        try:
            update_count = 0

            for update in updates:
                # Build SQL update
                set_clauses = []
                params = []

                # Add all changed fields
                for change in update['changes']:
                    set_clauses.append(f"{change['field']} = %s")
                    params.append(change['new'])

                # Add updated_at
                set_clauses.append("updated_at = now()")

                # Add contact_id for WHERE clause
                params.append(update['contact_id'])

                sql = f"""
                    UPDATE contacts
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """

                cur.execute(sql, params)
                update_count += 1

                if update_count % 25 == 0:
                    print(f"   Processed {update_count:,} / {len(updates):,} contacts...")

            # Commit transaction
            conn.commit()
            print(f"\n✓ Successfully updated {update_count:,} contacts")

            # Write audit log
            audit_data = []
            for update in updates:
                audit_data.append({
                    'contact_id': update['contact_id'],
                    'email': update['email'],
                    'street': update['address_data'].get('street', ''),
                    'city': update['address_data'].get('city', ''),
                    'state': update['address_data'].get('state', ''),
                    'postal_code': update['address_data'].get('postal_code', ''),
                    'timestamp': datetime.now().isoformat()
                })

            audit_df = pd.DataFrame(audit_data)
            audit_file = f'/workspaces/starhouse-database-v2/logs/google_addresses_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            audit_df.to_csv(audit_file, index=False)
            print(f"✓ Audit log written to: {audit_file}")

        except Exception as e:
            print(f"\n❌ Error during update: {e}")
            conn.rollback()
            print("✓ Transaction rolled back, no changes made")

    else:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute these updates, run:")
        print("  python3 scripts/import_google_addresses.py --live")

    # Cleanup
    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("ADDRESS IMPORT COMPLETE")
    print("=" * 80)

    return stats

if __name__ == '__main__':
    # Check for --live flag
    dry_run = '--live' not in sys.argv

    if not dry_run:
        print("\n⚠️  WARNING: Running in LIVE mode. Changes will be committed!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    stats = import_addresses(dry_run=dry_run)
