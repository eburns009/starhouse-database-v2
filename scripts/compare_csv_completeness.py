#!/usr/bin/env python3
"""
Compare v2_contacts.csv completeness against database
"""
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")  # SECURITY: No hardcoded credentials
CSV_FILE = '/workspaces/starhouse-database-v2/data/production/v2_contacts.csv'


def compare_completeness():
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print("CSV COMPLETENESS ANALYSIS")
    print(f"{'=' * 100}\n")

    # Count total contacts in database
    cur.execute("SELECT COUNT(*) as total FROM contacts")
    db_total = cur.fetchone()['total']

    # Count by source system in database
    cur.execute("""
        SELECT source_system, COUNT(*) as count
        FROM contacts
        GROUP BY source_system
        ORDER BY count DESC
    """)
    db_sources = cur.fetchall()

    print(f"DATABASE TOTALS:")
    print(f"  Total contacts: {db_total:,}\n")

    print(f"DATABASE BY SOURCE SYSTEM:")
    for source in db_sources:
        print(f"  {source['source_system']}: {source['count']:,}")
    print()

    # Read CSV and collect emails
    csv_emails = set()
    csv_sources = {}

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = row.get('email', '').strip().lower()
            source = row.get('source_system', '').strip()

            if email:
                csv_emails.add(email)

                if source not in csv_sources:
                    csv_sources[source] = 0
                csv_sources[source] += 1

    print(f"CSV TOTALS:")
    print(f"  Total contacts: {len(csv_emails):,}\n")

    print(f"CSV BY SOURCE SYSTEM:")
    for source, count in sorted(csv_sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count:,}")
    print()

    # Find contacts in database but not in CSV
    print(f"{'=' * 100}")
    print("FINDING CONTACTS IN DATABASE BUT NOT IN CSV...")
    print(f"{'=' * 100}\n")

    # Get all database emails
    cur.execute("SELECT email, source_system, created_at FROM contacts ORDER BY created_at DESC")
    db_contacts = cur.fetchall()

    missing_from_csv = []

    for contact in db_contacts:
        if contact['email'].lower() not in csv_emails:
            missing_from_csv.append(contact)

    print(f"Contacts in database but NOT in CSV: {len(missing_from_csv):,}\n")

    if missing_from_csv:
        # Group by source
        missing_by_source = {}
        for contact in missing_from_csv:
            source = contact['source_system']
            if source not in missing_by_source:
                missing_by_source[source] = []
            missing_by_source[source].append(contact)

        print(f"MISSING CONTACTS BY SOURCE:")
        for source, contacts in sorted(missing_by_source.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {source}: {len(contacts):,} contacts")
        print()

        # Show samples of missing contacts
        print(f"{'=' * 100}")
        print(f"SAMPLE MISSING CONTACTS (first 20, most recent first):")
        print(f"{'=' * 100}\n")

        for i, contact in enumerate(missing_from_csv[:20], 1):
            print(f"{i}. {contact['email']}")
            print(f"   Source: {contact['source_system']}")
            print(f"   Created: {contact['created_at']}")
            print()

    # Find contacts in CSV but not in database (shouldn't happen, but check)
    print(f"{'=' * 100}")
    print("CHECKING FOR CONTACTS IN CSV BUT NOT IN DATABASE...")
    print(f"{'=' * 100}\n")

    db_emails = {c['email'].lower() for c in db_contacts}
    csv_not_in_db = []

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = row.get('email', '').strip().lower()
            if email and email not in db_emails:
                csv_not_in_db.append(email)

    if csv_not_in_db:
        print(f"Contacts in CSV but NOT in database: {len(csv_not_in_db):,}")
        print(f"Examples: {csv_not_in_db[:10]}")
    else:
        print(f"✓ All CSV contacts exist in database")

    print()

    # Summary
    print(f"{'=' * 100}")
    print("SUMMARY")
    print(f"{'=' * 100}")
    print(f"Database total: {db_total:,}")
    print(f"CSV total: {len(csv_emails):,}")
    print(f"Difference: {db_total - len(csv_emails):,} contacts in DB not in CSV")
    print()

    if missing_from_csv:
        print(f"CONCLUSION:")
        print(f"  The CSV file is INCOMPLETE. It is missing {len(missing_from_csv):,} contacts that exist")
        print(f"  in the database. These are likely contacts added after the CSV was exported.")
        print()
        print(f"  Most missing contacts are from: {sorted(missing_by_source.items(), key=lambda x: len(x[1]), reverse=True)[0][0]}")
    else:
        print(f"CONCLUSION:")
        print(f"  The CSV file is COMPLETE. All database contacts exist in the CSV.")

    cur.close()
    conn.close()


if __name__ == '__main__':
    compare_completeness()
