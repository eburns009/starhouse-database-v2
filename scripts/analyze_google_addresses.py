#!/usr/bin/env python3
"""
Analyze Google Contacts address data
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import re

# Load Google Contacts
df = pd.read_csv('/workspaces/starhouse-database-v2/kajabi 3 files review/ascpr_google_contacts.csv')

print("=" * 80)
print("GOOGLE CONTACTS ADDRESS ANALYSIS")
print("=" * 80)

# Count addresses
total_with_address1 = df['Address 1 - Formatted'].notna().sum()
total_with_address2 = df['Address 2 - Formatted'].notna().sum()

print(f"\nContacts with Address 1: {total_with_address1:,}")
print(f"Contacts with Address 2: {total_with_address2:,}")

# Show sample addresses
print("\n" + "=" * 80)
print("SAMPLE ADDRESSES (Address 1 - Formatted)")
print("=" * 80)

sample_addresses = df[df['Address 1 - Formatted'].notna()]['Address 1 - Formatted'].head(20)
for i, addr in enumerate(sample_addresses, 1):
    print(f"\n{i}. {addr}")

# Check individual address components
print("\n" + "=" * 80)
print("ADDRESS COMPONENT AVAILABILITY")
print("=" * 80)

components = {
    'Address 1 - Street': df['Address 1 - Street'].notna().sum(),
    'Address 1 - City': df['Address 1 - City'].notna().sum(),
    'Address 1 - Region': df['Address 1 - Region'].notna().sum(),
    'Address 1 - Postal Code': df['Address 1 - Postal Code'].notna().sum(),
    'Address 1 - Country': df['Address 1 - Country'].notna().sum(),
}

for component, count in components.items():
    pct = (count / len(df)) * 100
    print(f"{component:30} {count:5,} ({pct:5.1f}%)")

# Connect to database to check for matches
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres.lnagadkqejnopgfxwlkb',
    password='gqelzN6LRew4Cy9H',
    host='aws-1-us-east-2.pooler.supabase.com',
    port='5432'
)

cur = conn.cursor(cursor_factory=RealDictCursor)

# Get database contacts with addresses
cur.execute("""
    SELECT email, paypal_email, address_line_1, city, state, postal_code
    FROM contacts
    WHERE address_line_1 IS NOT NULL
""")
db_contacts_with_addresses = cur.fetchall()

print(f"\n" + "=" * 80)
print("DATABASE ADDRESS COVERAGE")
print("=" * 80)

cur.execute("SELECT COUNT(*) as total FROM contacts")
total_db_contacts = cur.fetchone()['total']

print(f"\nTotal database contacts: {total_db_contacts:,}")
print(f"Contacts with address_line_1: {len(db_contacts_with_addresses):,}")
print(f"Address coverage: {len(db_contacts_with_addresses)/total_db_contacts*100:.1f}%")

# Build email lookup
email_to_contact = {}
cur.execute("SELECT email, paypal_email, address_line_1 FROM contacts")
for contact in cur.fetchall():
    if contact['email']:
        email_to_contact[contact['email'].lower().strip()] = contact
    if contact['paypal_email']:
        email_to_contact[contact['paypal_email'].lower().strip()] = contact

# Match Google contacts with addresses
matched_with_address = 0
matched_without_db_address = 0
unmatched = 0

for idx, row in df.iterrows():
    if pd.isna(row.get('Address 1 - Formatted')):
        continue  # No address in Google

    # Try to match contact
    google_emails = []
    for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
        if pd.notna(row.get(col)):
            google_emails.append(row[col].lower().strip())

    matched = False
    has_db_address = False
    for email in google_emails:
        if email in email_to_contact:
            matched = True
            if email_to_contact[email]['address_line_1']:
                has_db_address = True
            break

    if matched:
        matched_with_address += 1
        if not has_db_address:
            matched_without_db_address += 1
    else:
        unmatched += 1

print(f"\n" + "=" * 80)
print("ENRICHMENT OPPORTUNITY ANALYSIS")
print("=" * 80)

print(f"\nGoogle contacts with addresses: {total_with_address1:,}")
print(f"  Matched to database: {matched_with_address:,}")
print(f"  Database already has address: {matched_with_address - matched_without_db_address:,}")
print(f"  Database missing address (can enrich): {matched_without_db_address:,}")
print(f"  Unmatched (new contacts): {unmatched:,}")

print(f"\n⭐ Enrichment Opportunity: {matched_without_db_address:,} contacts")

cur.close()
conn.close()
