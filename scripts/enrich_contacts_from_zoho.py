#!/usr/bin/env python3
"""
Enrich existing contacts with data from Zoho CSV without overwriting existing data.

This script:
1. Reads the v2_contacts.csv file
2. Matches contacts by email
3. Updates ONLY NULL/empty fields with data from CSV:
   - Phone numbers
   - Address fields (address_line_1, address_line_2, city, state, postal_code, country)
4. Tracks and reports all changes
"""
import csv
import sys
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"

# CSV file path
CSV_FILE = '/workspaces/starhouse-database-v2/data/production/v2_contacts.csv'


def connect_db():
    """Connect to the database"""
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    return conn


def enrich_contacts(dry_run=True):
    """
    Enrich contacts with data from CSV

    Args:
        dry_run: If True, only report what would be updated without making changes
    """
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 80}")
    print(f"Contact Enrichment Script")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE UPDATE'}")
    print(f"{'=' * 80}\n")

    # Statistics
    stats = {
        'total_csv_records': 0,
        'csv_records_with_data': 0,
        'contacts_matched': 0,
        'contacts_enriched': 0,
        'phone_added': 0,
        'address_added': 0,
        'contacts_not_found': 0
    }

    enrichment_log = []
    not_found_log = []

    # Read CSV and process
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats['total_csv_records'] += 1

            email = row.get('email', '').strip().lower()
            if not email:
                continue

            # Check if this CSV row has enrichment data
            csv_phone = row.get('phone', '').strip()
            csv_address_line_1 = row.get('address_line_1', '').strip()
            csv_address_line_2 = row.get('address_line_2', '').strip()
            csv_city = row.get('city', '').strip()
            csv_state = row.get('state', '').strip()
            csv_postal_code = row.get('postal_code', '').strip()
            csv_country = row.get('country', '').strip()

            has_enrichment_data = csv_phone or csv_address_line_1 or csv_city or csv_state or csv_postal_code

            if not has_enrichment_data:
                continue

            stats['csv_records_with_data'] += 1

            # Find matching contact in database
            cur.execute("""
                SELECT id, email, phone, address_line_1, address_line_2,
                       city, state, postal_code, country
                FROM contacts
                WHERE LOWER(email) = %s
            """, (email,))

            contact = cur.fetchone()

            if not contact:
                stats['contacts_not_found'] += 1
                not_found_log.append({
                    'email': email,
                    'has_phone': bool(csv_phone),
                    'has_address': bool(csv_address_line_1 or csv_city)
                })
                continue

            stats['contacts_matched'] += 1

            # Determine what needs to be updated (only NULL/empty fields)
            updates = {}
            changes = []

            # Check phone
            if csv_phone and not contact['phone']:
                updates['phone'] = csv_phone
                updates['phone_source'] = 'zoho'
                changes.append(f"phone: NULL -> {csv_phone}")
                stats['phone_added'] += 1

            # Check address fields
            address_updated = False

            if csv_address_line_1 and not contact['address_line_1']:
                updates['address_line_1'] = csv_address_line_1
                changes.append(f"address_line_1: NULL -> {csv_address_line_1}")
                address_updated = True

            if csv_address_line_2 and not contact['address_line_2']:
                updates['address_line_2'] = csv_address_line_2
                changes.append(f"address_line_2: NULL -> {csv_address_line_2}")
                address_updated = True

            if csv_city and not contact['city']:
                updates['city'] = csv_city
                changes.append(f"city: NULL -> {csv_city}")
                address_updated = True

            if csv_state and not contact['state']:
                updates['state'] = csv_state
                changes.append(f"state: NULL -> {csv_state}")
                address_updated = True

            if csv_postal_code and not contact['postal_code']:
                updates['postal_code'] = csv_postal_code
                changes.append(f"postal_code: NULL -> {csv_postal_code}")
                address_updated = True

            if csv_country and not contact['country']:
                updates['country'] = csv_country
                changes.append(f"country: NULL -> {csv_country}")
                address_updated = True

            # Set billing address metadata if address was updated
            if address_updated:
                updates['billing_address_source'] = 'zoho'
                updates['billing_address_updated_at'] = datetime.now()
                stats['address_added'] += 1

            # If there are updates to make, execute them
            if updates:
                stats['contacts_enriched'] += 1

                enrichment_log.append({
                    'email': email,
                    'contact_id': str(contact['id']),
                    'changes': changes
                })

                if not dry_run:
                    # Build UPDATE query dynamically
                    set_clauses = ', '.join([f"{key} = %s" for key in updates.keys()])
                    values = list(updates.values())
                    values.append(contact['id'])

                    update_query = f"""
                        UPDATE contacts
                        SET {set_clauses}, updated_at = NOW()
                        WHERE id = %s
                    """

                    cur.execute(update_query, values)

    # Commit if not dry run
    if not dry_run:
        conn.commit()
        print("✓ Changes committed to database\n")
    else:
        print("ℹ DRY RUN - No changes were made\n")

    # Print statistics
    print(f"{'=' * 80}")
    print("ENRICHMENT STATISTICS")
    print(f"{'=' * 80}")
    print(f"Total CSV records processed: {stats['total_csv_records']}")
    print(f"CSV records with enrichment data: {stats['csv_records_with_data']}")
    print(f"Contacts matched by email: {stats['contacts_matched']}")
    print(f"Contacts enriched: {stats['contacts_enriched']}")
    print(f"  - Phone numbers added: {stats['phone_added']}")
    print(f"  - Addresses added: {stats['address_added']}")
    print(f"Contacts not found in database: {stats['contacts_not_found']}")
    print()

    # Print sample enrichments
    if enrichment_log:
        print(f"{'=' * 80}")
        print(f"SAMPLE ENRICHMENTS (first 10):")
        print(f"{'=' * 80}")
        for i, log_entry in enumerate(enrichment_log[:10]):
            print(f"\n{i+1}. {log_entry['email']}")
            for change in log_entry['changes']:
                print(f"   - {change}")

        if len(enrichment_log) > 10:
            print(f"\n... and {len(enrichment_log) - 10} more contacts")

    # Print contacts not found
    if not_found_log:
        print(f"\n{'=' * 80}")
        print(f"CONTACTS NOT FOUND IN DATABASE (first 10):")
        print(f"{'=' * 80}")
        for i, log_entry in enumerate(not_found_log[:10]):
            print(f"{i+1}. {log_entry['email']} - "
                  f"Has phone: {log_entry['has_phone']}, "
                  f"Has address: {log_entry['has_address']}")

        if len(not_found_log) > 10:
            print(f"... and {len(not_found_log) - 10} more")

    cur.close()
    conn.close()

    return stats, enrichment_log


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Enrich contacts from Zoho CSV')
    parser.add_argument('--live', action='store_true',
                       help='Run in LIVE mode (default is DRY RUN)')
    args = parser.parse_args()

    try:
        stats, log = enrich_contacts(dry_run=not args.live)

        if not args.live and stats['contacts_enriched'] > 0:
            print(f"\n{'=' * 80}")
            print("To apply these changes, run with --live flag:")
            print("  python3 scripts/enrich_contacts_from_zoho.py --live")
            print(f"{'=' * 80}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
