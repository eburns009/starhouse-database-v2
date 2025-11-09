#!/usr/bin/env python3
"""
Enrich contact data from transactions.csv

This script:
1. Reads transaction data from CSV
2. Groups by customer email and takes most recent transaction
3. Matches contacts by email
4. Updates ONLY NULL/empty fields with transaction data:
   - Phone numbers
   - Billing address fields
5. Tracks source and updates metadata
"""
import csv
import sys
import re
from datetime import datetime
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")  # SECURITY: No hardcoded credentials

# CSV file path
CSV_FILE = '/workspaces/starhouse-database-v2/data/production/transactions.csv'


def normalize_phone(phone):
    """
    Normalize phone number by removing non-digits and handling country codes

    PayPal format appears to be: [country_code][phone_number] without separators
    Example: 16109734304 = 1 (US) + 610-973-4304
    """
    if not phone:
        return None

    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)

    if not digits:
        return None

    # If it's 11 digits starting with 1 (US), format as US number
    if len(digits) == 11 and digits.startswith('1'):
        # Format: +1 (XXX) XXX-XXXX
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

    # If it's 10 digits (US without country code)
    elif len(digits) == 10:
        return f"+1 ({digits[0:3]}) {digits[3:6]}-{digits[6:]}"

    # Otherwise return with + prefix if 10+ digits
    elif len(digits) >= 10:
        return f"+{digits}"

    # For shorter numbers, return as-is with dashes every 3 digits
    else:
        return phone


def connect_db():
    """Connect to the database"""
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    return conn


def parse_transaction_date(date_str):
    """Parse transaction date string to datetime"""
    try:
        # Format: "2025-10-30 04:33:07 -0600"
        return datetime.strptime(date_str.split()[0] + ' ' + date_str.split()[1], '%Y-%m-%d %H:%M:%S')
    except:
        return datetime.min


def enrich_from_transactions(dry_run=True):
    """
    Enrich contacts with data from transactions CSV

    Args:
        dry_run: If True, only report what would be updated without making changes
    """
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print(f"Contact Enrichment from Transactions")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE UPDATE'}")
    print(f"{'=' * 100}\n")

    print("Step 1: Reading transactions.csv and grouping by customer email...\n")

    # Read CSV and group by email, keeping most recent transaction per email
    transactions_by_email = {}

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = row.get('Customer Email', '').strip().lower()
            if not email:
                continue

            # Parse date
            date = parse_transaction_date(row.get('Created At', ''))

            # Check if this transaction has enrichment data
            has_data = bool(
                row.get('Address', '').strip() or
                row.get('City', '').strip() or
                row.get('Phone', '').strip()
            )

            if not has_data:
                continue

            # Keep most recent transaction for each email
            if email not in transactions_by_email or date > transactions_by_email[email]['date']:
                transactions_by_email[email] = {
                    'date': date,
                    'phone': row.get('Phone', '').strip(),
                    'address_line_1': row.get('Address', '').strip(),
                    'address_line_2': row.get('Address 2', '').strip(),
                    'city': row.get('City', '').strip(),
                    'state': row.get('State', '').strip(),
                    'postal_code': row.get('Zipcode', '').strip(),
                    'country': row.get('Country', '').strip(),
                }

    print(f"Found {len(transactions_by_email):,} unique customers with address/phone data in transactions\n")

    print("Step 2: Matching with database contacts and identifying enrichment opportunities...\n")

    # Statistics
    stats = {
        'transactions_processed': len(transactions_by_email),
        'contacts_matched': 0,
        'contacts_enriched': 0,
        'phone_added': 0,
        'address_added': 0,
        'both_added': 0,
        'contacts_not_found': 0,
        'already_complete': 0
    }

    enrichment_log = []
    not_found_log = []
    sample_updates = []

    # Process each email
    for email, txn_data in transactions_by_email.items():
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
            not_found_log.append(email)
            continue

        stats['contacts_matched'] += 1

        # Determine what needs to be updated (only NULL/empty fields)
        updates = {}
        changes = []

        # Check phone
        if txn_data['phone'] and not contact['phone']:
            normalized_phone = normalize_phone(txn_data['phone'])
            if normalized_phone:
                updates['phone'] = normalized_phone
                updates['phone_source'] = 'paypal_transaction'
                changes.append(f"phone: NULL -> {normalized_phone}")
                stats['phone_added'] += 1

        # Check address fields
        address_updated = False

        if txn_data['address_line_1'] and not contact['address_line_1']:
            updates['address_line_1'] = txn_data['address_line_1']
            changes.append(f"address_line_1: NULL -> {txn_data['address_line_1']}")
            address_updated = True

        if txn_data['address_line_2'] and not contact['address_line_2']:
            updates['address_line_2'] = txn_data['address_line_2']
            changes.append(f"address_line_2: NULL -> {txn_data['address_line_2']}")
            address_updated = True

        if txn_data['city'] and not contact['city']:
            updates['city'] = txn_data['city']
            changes.append(f"city: NULL -> {txn_data['city']}")
            address_updated = True

        if txn_data['state'] and not contact['state']:
            updates['state'] = txn_data['state']
            changes.append(f"state: NULL -> {txn_data['state']}")
            address_updated = True

        if txn_data['postal_code'] and not contact['postal_code']:
            updates['postal_code'] = txn_data['postal_code']
            changes.append(f"postal_code: NULL -> {txn_data['postal_code']}")
            address_updated = True

        if txn_data['country'] and not contact['country']:
            updates['country'] = txn_data['country']
            changes.append(f"country: NULL -> {txn_data['country']}")
            address_updated = True

        # Set billing address metadata if address was updated
        if address_updated:
            updates['billing_address_source'] = 'paypal_transaction'
            updates['billing_address_updated_at'] = datetime.now()
            stats['address_added'] += 1

        # Track if both were added
        if 'phone' in updates and address_updated:
            stats['both_added'] += 1

        # If there are updates to make, execute them
        if updates:
            stats['contacts_enriched'] += 1

            enrichment_log.append({
                'email': email,
                'contact_id': str(contact['id']),
                'changes': changes
            })

            if len(sample_updates) < 20:
                sample_updates.append({
                    'email': email,
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
        else:
            stats['already_complete'] += 1

    # Commit if not dry run
    if not dry_run:
        conn.commit()
        print("✓ Changes committed to database\n")
    else:
        print("ℹ DRY RUN - No changes were made\n")

    # Print statistics
    print(f"{'=' * 100}")
    print("ENRICHMENT STATISTICS")
    print(f"{'=' * 100}")
    print(f"Transaction customers processed: {stats['transactions_processed']:,}")
    print(f"Contacts matched by email: {stats['contacts_matched']:,}")
    print(f"Contacts enriched: {stats['contacts_enriched']:,}")
    print(f"  - Phone numbers added: {stats['phone_added']:,}")
    print(f"  - Addresses added: {stats['address_added']:,}")
    print(f"  - Both phone and address added: {stats['both_added']:,}")
    print(f"Contacts already complete (no updates needed): {stats['already_complete']:,}")
    print(f"Transaction emails not found in contacts: {stats['contacts_not_found']:,}")
    print()

    # Print sample enrichments
    if sample_updates:
        print(f"{'=' * 100}")
        print(f"SAMPLE ENRICHMENTS (showing {min(len(sample_updates), 20)}):")
        print(f"{'=' * 100}")
        for i, update in enumerate(sample_updates, 1):
            print(f"\n{i}. {update['email']}")
            for change in update['changes']:
                print(f"   ✓ {change}")

        if len(enrichment_log) > 20:
            print(f"\n... and {len(enrichment_log) - 20} more contacts")

    # Summary by category
    print(f"\n{'=' * 100}")
    print("ENRICHMENT BREAKDOWN")
    print(f"{'=' * 100}")
    print(f"Phone only: {stats['phone_added'] - stats['both_added']:,}")
    print(f"Address only: {stats['address_added'] - stats['both_added']:,}")
    print(f"Both phone and address: {stats['both_added']:,}")
    print()

    # Not found emails
    if not_found_log:
        print(f"{'=' * 100}")
        print(f"TRANSACTION EMAILS NOT IN CONTACTS DATABASE (first 10 of {len(not_found_log)}):")
        print(f"{'=' * 100}")
        for i, email in enumerate(not_found_log[:10], 1):
            print(f"{i}. {email}")
        print("\nThese customers made purchases but don't have contact records.")
        print("Consider importing them as new contacts.")
        print()

    cur.close()
    conn.close()

    return stats, enrichment_log


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Enrich contacts from transaction data')
    parser.add_argument('--live', action='store_true',
                       help='Run in LIVE mode (default is DRY RUN)')
    args = parser.parse_args()

    try:
        stats, log = enrich_from_transactions(dry_run=not args.live)

        if not args.live and stats['contacts_enriched'] > 0:
            print(f"{'=' * 100}")
            print("READY TO APPLY CHANGES")
            print(f"{'=' * 100}")
            print(f"\nThis will enrich {stats['contacts_enriched']:,} contacts with:")
            print(f"  - {stats['phone_added']:,} phone numbers")
            print(f"  - {stats['address_added']:,} addresses")
            print(f"\nTo apply these changes, run with --live flag:")
            print("  python3 scripts/enrich_from_transactions.py --live")
            print(f"{'=' * 100}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
