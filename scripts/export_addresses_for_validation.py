#!/usr/bin/env python3
"""
Export addresses for SmartyStreets validation
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import csv

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Get all addresses needing validation
cursor.execute("""
    SELECT
        id,
        address_line_1,
        address_line_2,
        city,
        state,
        postal_code
    FROM contacts
    WHERE address_line_1 IS NOT NULL
      AND city IS NOT NULL
      AND state IS NOT NULL
      AND postal_code IS NOT NULL
      AND (address_validated = false OR address_validated IS NULL)
    ORDER BY total_spent DESC, id
""")

contacts = cursor.fetchall()

print(f"Found {len(contacts)} addresses to validate")

# Write to CSV in SmartyStreets format
with open('/tmp/shipping_addresses_for_validation.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['sequence', 'contact_id', 'addressline1', 'addressline2', 'city', 'state', 'postalcode'])

    for i, contact in enumerate(contacts, 1):
        writer.writerow([
            i,  # sequence
            contact['id'],  # contact_id
            contact['address_line_1'] or '',
            contact['address_line_2'] or '',
            contact['city'] or '',
            contact['state'] or '',
            contact['postal_code'] or ''
        ])

print(f"✅ Exported {len(contacts)} addresses to /tmp/shipping_addresses_for_validation.csv")

conn.close()
