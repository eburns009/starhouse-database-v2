#!/usr/bin/env python3
"""Quick check for Zoho-related fields in contacts table"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'contacts'
        AND column_name LIKE '%zoho%'
        ORDER BY ordinal_position
    """)

    print("Zoho-related fields in contacts table:")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:30} {row[1]:20} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")

    print()

    # Also check if zoho_id, zoho_email, zoho_phone exist
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'contacts'
        AND column_name IN ('zoho_id', 'zoho_email', 'zoho_phone', 'zoho_phone_source')
    """)

    fields = {row[0]: row[1] for row in cursor.fetchall()}

    print("Required fields check:")
    print("-" * 60)
    for field in ['zoho_id', 'zoho_email', 'zoho_phone', 'zoho_phone_source']:
        status = f"EXISTS ({fields[field]})" if field in fields else "MISSING"
        print(f"{field:30} {status}")

conn.close()
