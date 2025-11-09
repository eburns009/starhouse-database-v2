#!/usr/bin/env python3
"""Apply Zoho schema migration"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("Applying Zoho contact fields schema migration...")

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.set_session(autocommit=False)

try:
    with conn.cursor() as cursor:
        with open('schema/add_zoho_contact_fields.sql', 'r') as f:
            sql = f.read()
            cursor.execute(sql)

    conn.commit()
    print("Schema migration applied successfully!")

except Exception as e:
    print(f"ERROR: {e}")
    conn.rollback()
    raise
finally:
    conn.close()
