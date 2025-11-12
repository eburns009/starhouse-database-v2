#!/usr/bin/env python3
"""Quick script to check shipping address availability."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
cursor = conn.cursor()

# Check contacts table for shipping fields
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'contacts'
      AND column_name LIKE '%shipping%'
    ORDER BY ordinal_position
""")

shipping_columns = cursor.fetchall()
print("Shipping-related columns in contacts table:")
for col in shipping_columns:
    print(f"  - {col['column_name']}")

# Check how many contacts have shipping addresses
cursor.execute("""
    SELECT
        COUNT(*) as total_contacts,
        COUNT(shipping_address_line_1) as has_shipping
    FROM contacts
    WHERE deleted_at IS NULL
""")

result = cursor.fetchone()
print(f"\nContacts with shipping addresses: {result['has_shipping']} / {result['total_contacts']}")

# Check by source system
cursor.execute("""
    SELECT
        source_system,
        COUNT(*) as total,
        COUNT(shipping_address_line_1) as has_shipping
    FROM contacts
    WHERE deleted_at IS NULL
    GROUP BY source_system
    ORDER BY has_shipping DESC
""")

print("\nShipping addresses by source:")
for row in cursor.fetchall():
    pct = (row['has_shipping'] / row['total'] * 100) if row['total'] > 0 else 0
    print(f"  {row['source_system']:15} {row['has_shipping']:4} / {row['total']:4} ({pct:5.1f}%)")

cursor.close()
conn.close()
