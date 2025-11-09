#!/usr/bin/env python3
"""
Compare CSV data vs database to understand data overlap
"""
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"
CSV_FILE = '/workspaces/starhouse-database-v2/data/production/v2_contacts.csv'


def compare_data():
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("Comparing CSV vs Database data...\n")

    # Sample records from CSV with phone or address
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        samples_checked = 0
        samples_with_enrichment = []

        for row in reader:
            if samples_checked >= 20:
                break

            email = row.get('email', '').strip().lower()
            csv_phone = row.get('phone', '').strip()
            csv_address = row.get('address_line_1', '').strip()

            # Only look at records with phone or address
            if not (csv_phone or csv_address):
                continue

            # Check database
            cur.execute("""
                SELECT email, phone, address_line_1, city, state
                FROM contacts
                WHERE LOWER(email) = %s
            """, (email,))

            contact = cur.fetchone()

            if contact:
                samples_checked += 1
                samples_with_enrichment.append({
                    'email': email,
                    'csv_phone': csv_phone,
                    'db_phone': contact['phone'],
                    'csv_address': csv_address,
                    'db_address': contact['address_line_1'],
                    'csv_city': row.get('city', '').strip(),
                    'db_city': contact['city']
                })

    print(f"{'=' * 100}")
    print("SAMPLE COMPARISON: CSV vs Database")
    print(f"{'=' * 100}\n")

    for i, sample in enumerate(samples_with_enrichment[:10], 1):
        print(f"{i}. {sample['email']}")
        print(f"   Phone:")
        print(f"     CSV: {sample['csv_phone'] or 'NULL'}")
        print(f"     DB:  {sample['db_phone'] or 'NULL'}")
        print(f"   Address:")
        print(f"     CSV: {sample['csv_address'] or 'NULL'}")
        print(f"     DB:  {sample['db_address'] or 'NULL'}")
        print(f"   City:")
        print(f"     CSV: {sample['csv_city'] or 'NULL'}")
        print(f"     DB:  {sample['db_city'] or 'NULL'}")
        print()

    # Check for records in DB without phone/address but in CSV with them
    print(f"\n{'=' * 100}")
    print("Looking for potential enrichment opportunities...")
    print(f"{'=' * 100}\n")

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        found_opportunities = []

        for row in reader:
            email = row.get('email', '').strip().lower()
            csv_phone = row.get('phone', '').strip()
            csv_address = row.get('address_line_1', '').strip()

            if not (csv_phone or csv_address):
                continue

            cur.execute("""
                SELECT email, phone, address_line_1
                FROM contacts
                WHERE LOWER(email) = %s
                AND (
                    (phone IS NULL AND %s != '')
                    OR (address_line_1 IS NULL AND %s != '')
                )
            """, (email, csv_phone, csv_address))

            contact = cur.fetchone()

            if contact:
                found_opportunities.append({
                    'email': email,
                    'csv_phone': csv_phone,
                    'db_phone': contact['phone'],
                    'csv_address': csv_address,
                    'db_address': contact['address_line_1']
                })

                if len(found_opportunities) >= 10:
                    break

    if found_opportunities:
        print(f"Found {len(found_opportunities)} enrichment opportunities:\n")
        for i, opp in enumerate(found_opportunities, 1):
            print(f"{i}. {opp['email']}")
            if not opp['db_phone'] and opp['csv_phone']:
                print(f"   Can add phone: {opp['csv_phone']}")
            if not opp['db_address'] and opp['csv_address']:
                print(f"   Can add address: {opp['csv_address']}")
            print()
    else:
        print("No enrichment opportunities found.")
        print("All contacts in CSV already have complete data in the database.")

    cur.close()
    conn.close()


if __name__ == '__main__':
    compare_data()
