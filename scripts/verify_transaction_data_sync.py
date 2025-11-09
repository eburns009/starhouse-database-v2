#!/usr/bin/env python3
"""
Verify that transaction data has already been synced to contacts
"""
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"
CSV_FILE = '/workspaces/starhouse-database-v2/data/production/transactions.csv'


def verify_sync():
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print("VERIFYING TRANSACTION DATA SYNC WITH CONTACTS")
    print(f"{'=' * 100}\n")

    # Get first 10 transactions with address/phone data
    samples = []

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = row.get('Customer Email', '').strip().lower()
            if not email:
                continue

            has_address = bool(row.get('Address', '').strip())
            has_phone = bool(row.get('Phone', '').strip())

            if has_address or has_phone:
                samples.append({
                    'email': email,
                    'txn_phone': row.get('Phone', '').strip(),
                    'txn_address': row.get('Address', '').strip(),
                    'txn_city': row.get('City', '').strip(),
                    'txn_state': row.get('State', '').strip(),
                    'txn_zip': row.get('Zipcode', '').strip()
                })

                if len(samples) >= 10:
                    break

    # Check each sample in database
    for i, sample in enumerate(samples, 1):
        cur.execute("""
            SELECT email, phone, address_line_1, city, state, postal_code
            FROM contacts
            WHERE LOWER(email) = %s
        """, (sample['email'],))

        contact = cur.fetchone()

        print(f"{i}. {sample['email']}")
        print(f"   Transaction Phone: {sample['txn_phone']}")
        print(f"   Database Phone:    {contact['phone'] if contact else 'NOT FOUND'}")
        print(f"   Transaction Addr:  {sample['txn_address']}, {sample['txn_city']}, {sample['txn_state']} {sample['txn_zip']}")
        print(f"   Database Addr:     {contact['address_line_1'] if contact else 'NOT FOUND'}, {contact['city'] if contact else ''}, {contact['state'] if contact else ''} {contact['postal_code'] if contact else ''}")

        if contact:
            if contact['phone']:
                print(f"   ✓ Phone already in DB")
            else:
                print(f"   ✗ Phone missing in DB")

            if contact['address_line_1']:
                print(f"   ✓ Address already in DB")
            else:
                print(f"   ✗ Address missing in DB")
        print()

    # Check if ANY contacts are missing data that exists in transactions
    print(f"\n{'=' * 100}")
    print("SEARCHING FOR ANY MISSING DATA OPPORTUNITIES...")
    print(f"{'=' * 100}\n")

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        missing_phone = []
        missing_address = []

        for row in reader:
            email = row.get('Customer Email', '').strip().lower()
            if not email:
                continue

            txn_phone = row.get('Phone', '').strip()
            txn_address = row.get('Address', '').strip()

            if not (txn_phone or txn_address):
                continue

            cur.execute("""
                SELECT email, phone, address_line_1
                FROM contacts
                WHERE LOWER(email) = %s
            """, (email,))

            contact = cur.fetchone()

            if contact:
                if txn_phone and not contact['phone']:
                    missing_phone.append(email)

                if txn_address and not contact['address_line_1']:
                    missing_address.append(email)

    print(f"Contacts missing phone (but have it in transactions): {len(missing_phone)}")
    if missing_phone:
        print("Examples:")
        for email in missing_phone[:5]:
            print(f"  - {email}")

    print(f"\nContacts missing address (but have it in transactions): {len(missing_address)}")
    if missing_address:
        print("Examples:")
        for email in missing_address[:5]:
            print(f"  - {email}")

    if not missing_phone and not missing_address:
        print("\n✓ All transaction data has already been synced to contacts!")
        print("  The database is fully up-to-date with transaction information.")

    cur.close()
    conn.close()


if __name__ == '__main__':
    verify_sync()
