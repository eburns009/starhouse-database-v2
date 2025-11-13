#!/usr/bin/env python3
"""
Check what consent/GDPR tracking fields and data exist in the database.
"""
import os
import sys
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

# Get database URL
try:
    DATABASE_URL = get_database_url()
except Exception as e:
    print(f"ERROR: Could not get database URL: {e}")
    sys.exit(1)

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check what consent/email tracking fields we have in contacts table
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'contacts'
          AND (column_name LIKE '%consent%'
            OR column_name LIKE '%subscribe%'
            OR column_name LIKE '%opt%'
            OR column_name LIKE '%email%'
            OR column_name LIKE '%gdpr%')
        ORDER BY ordinal_position;
    """)

    print("=" * 80)
    print("CONSENT/EMAIL FIELDS IN DATABASE")
    print("=" * 80)
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[1]:<20} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")

    # Check if we have any consent tracking data
    cursor.execute("""
        SELECT
            COUNT(*) as total_contacts,
            COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed,
            COUNT(CASE WHEN email_subscribed = false THEN 1 END) as unsubscribed,
            COUNT(CASE WHEN email_subscribed IS NULL THEN 1 END) as unknown,
            MIN(created_at) as oldest_contact,
            MAX(created_at) as newest_contact
        FROM contacts
        WHERE deleted_at IS NULL;
    """)

    print("\n" + "=" * 80)
    print("CURRENT CONSENT STATUS")
    print("=" * 80)
    row = cursor.fetchone()
    print(f"  Total Contacts: {row[0]:,}")
    print(f"  Email Subscribed: {row[1]:,} ({row[1]/row[0]*100:.1f}%)")
    print(f"  Email Unsubscribed: {row[2]:,} ({row[2]/row[0]*100:.1f}%)")
    print(f"  Unknown Status: {row[3]:,} ({row[3]/row[0]*100:.1f}%)")
    print(f"  Date Range: {row[4]} to {row[5]}")

    # Check consent by source
    cursor.execute("""
        SELECT
            source_system,
            COUNT(*) as total,
            COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed,
            COUNT(CASE WHEN email_subscribed = false THEN 1 END) as unsubscribed,
            COUNT(CASE WHEN email_subscribed IS NULL THEN 1 END) as unknown
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY source_system
        ORDER BY COUNT(*) DESC;
    """)

    print("\n" + "=" * 80)
    print("CONSENT STATUS BY SOURCE")
    print("=" * 80)
    print(f"{'Source':<20} {'Total':>10} {'Subscribed':>12} {'Unsubscribed':>14} {'Unknown':>10}")
    print("-" * 80)
    for row in cursor.fetchall():
        source = row[0] or 'NULL'
        print(f"{source:<20} {row[1]:>10,} {row[2]:>12,} {row[3]:>14,} {row[4]:>10,}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
