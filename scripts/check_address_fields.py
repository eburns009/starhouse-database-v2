#!/usr/bin/env python3
"""Check address field names in contacts table"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'contacts'
        AND column_name LIKE '%address%'
        ORDER BY column_name
    """)

    print("Address fields in contacts table:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

conn.close()
