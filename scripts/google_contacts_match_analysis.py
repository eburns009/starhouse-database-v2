#!/usr/bin/env python3
"""
Quick match analysis: Google Contacts vs Database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Load Google Contacts
df = pd.read_csv('/workspaces/starhouse-database-v2/kajabi 3 files review/ascpr_google_contacts.csv')

# Connect to database
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres.lnagadkqejnopgfxwlkb',
    password='gqelzN6LRew4Cy9H',
    host='aws-1-us-east-2.pooler.supabase.com',
    port='5432'
)

cur = conn.cursor(cursor_factory=RealDictCursor)

# Get all database emails
cur.execute("SELECT email, paypal_email, phone, address_line_1, paypal_business_name, notes FROM contacts")
db_contacts = cur.fetchall()

db_emails = set()
for contact in db_contacts:
    if contact['email']:
        db_emails.add(contact['email'].lower().strip())
    if contact['paypal_email']:
        db_emails.add(contact['paypal_email'].lower().strip())

print(f"Database contacts: {len(db_contacts):,}")
print(f"Database email addresses: {len(db_emails):,}")

# Extract all Google emails
google_emails = set()
for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
    emails = df[col].dropna().astype(str)
    google_emails.update([e.lower().strip() for e in emails])

print(f"\nGoogle contacts: {len(df):,}")
print(f"Google email addresses: {len(google_emails):,}")

# Find matches
matched_emails = google_emails.intersection(db_emails)
new_emails = google_emails - db_emails

print(f"\nMatched emails: {len(matched_emails):,}")
print(f"New emails not in database: {len(new_emails):,}")

# Analyze matched contacts for enrichment
enrichment_opps = {
    'phone': 0,
    'address': 0,
    'organization': 0,
    'additional_emails': 0
}

for idx, row in df.iterrows():
    google_primary_email = row.get('E-mail 1 - Value')
    if pd.notna(google_primary_email):
        google_primary_email = google_primary_email.lower().strip()

        if google_primary_email in matched_emails:
            # This contact matches database
            # Check for enrichment opportunities
            if pd.notna(row.get('Phone 1 - Value')):
                enrichment_opps['phone'] += 1
            if pd.notna(row.get('Address 1 - Formatted')):
                enrichment_opps['address'] += 1
            if pd.notna(row.get('Organization Name')):
                enrichment_opps['organization'] += 1
            if pd.notna(row.get('E-mail 2 - Value')) or pd.notna(row.get('E-mail 3 - Value')):
                enrichment_opps['additional_emails'] += 1

print(f"\nEnrichment opportunities for matched contacts:")
print(f"  Can add phone: {enrichment_opps['phone']:,}")
print(f"  Can add address: {enrichment_opps['address']:,}")
print(f"  Can add organization: {enrichment_opps['organization']:,}")
print(f"  Have additional emails: {enrichment_opps['additional_emails']:,}")

# Analyze new contacts
new_contact_rows = []
for idx, row in df.iterrows():
    google_emails_in_row = []
    for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
        if pd.notna(row.get(col)):
            google_emails_in_row.append(row[col].lower().strip())

    # If any email in this contact is new, consider it a new contact
    if any(e in new_emails for e in google_emails_in_row):
        new_contact_rows.append(row)

print(f"\nNew contacts: {len(new_contact_rows):,}")

new_with_phone = sum(1 for c in new_contact_rows if pd.notna(c.get('Phone 1 - Value')))
new_with_address = sum(1 for c in new_contact_rows if pd.notna(c.get('Address 1 - Formatted')))

print(f"  With phone: {new_with_phone:,}")
print(f"  With address: {new_with_address:,}")

# Check priority labels in new contacts
priority_labels = ['Current Keepers', 'Preferred Keepers', 'Paid Members', 'Program Partner', '11-9-2025 Current Keepers']
new_priority = 0
for contact in new_contact_rows:
    labels = contact.get('Labels')
    if pd.notna(labels):
        for priority in priority_labels:
            if priority in str(labels):
                new_priority += 1
                break

print(f"  With priority labels (Keepers/Members/Partners): {new_priority:,}")

cur.close()
conn.close()
