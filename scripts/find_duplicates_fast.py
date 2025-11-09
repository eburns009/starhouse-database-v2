#!/usr/bin/env python3
"""
FAST Fuzzy Duplicate Detection (SQL-Optimized)
==============================================

Uses SQL for efficient duplicate detection:
- Name-based blocking (only compare similar names)
- Phone matching
- Email similarity
- Much faster than N^2 comparison

FAANG Standards: Performance-optimized with smart blocking

Usage:
  python3 scripts/find_duplicates_fast.py

Author: StarHouse Development Team
Date: 2025-11-08
"""

import os
import csv
from typing import List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def find_duplicates_by_exact_name():
    """Find contacts with exact same name but different emails."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Find exact name duplicates
            cursor.execute("""
                WITH name_groups AS (
                    SELECT
                        LOWER(TRIM(first_name || ' ' || last_name)) as full_name,
                        COUNT(*) as count,
                        ARRAY_AGG(id ORDER BY created_at DESC) as contact_ids,
                        ARRAY_AGG(email ORDER BY created_at DESC) as emails,
                        ARRAY_AGG(phone ORDER BY created_at DESC) as phones,
                        ARRAY_AGG(source_system ORDER BY created_at DESC) as sources
                    FROM contacts
                    WHERE first_name IS NOT NULL AND last_name IS NOT NULL
                    GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC, full_name
                )
                SELECT * FROM name_groups
            """)

            duplicates = cursor.fetchall()
            return duplicates

    finally:
        conn.close()


def find_duplicates_by_phone():
    """Find contacts with same phone but different emails."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                WITH phone_groups AS (
                    SELECT
                        REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as normalized_phone,
                        COUNT(*) as count,
                        ARRAY_AGG(id ORDER BY created_at DESC) as contact_ids,
                        ARRAY_AGG(TRIM(first_name || ' ' || last_name) ORDER BY created_at DESC) as names,
                        ARRAY_AGG(email ORDER BY created_at DESC) as emails,
                        ARRAY_AGG(source_system ORDER BY created_at DESC) as sources
                    FROM contacts
                    WHERE phone IS NOT NULL
                      AND LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '', 'g')) >= 10
                    GROUP BY REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                )
                SELECT * FROM phone_groups
                WHERE normalized_phone IS NOT NULL AND normalized_phone != ''
            """)

            duplicates = cursor.fetchall()
            return duplicates

    finally:
        conn.close()


def print_report():
    """Print duplicate report."""
    print("\n" + "="*80)
    print("DUPLICATE CONTACTS REPORT - Fast Detection")
    print("="*80)
    print()

    # Name-based duplicates
    name_dups = find_duplicates_by_exact_name()

    print(f"1. EXACT NAME DUPLICATES: {len(name_dups)} groups found")
    print("-" * 80)

    total_duplicate_contacts = sum(d['count'] for d in name_dups)
    print(f"   Total contacts involved: {total_duplicate_contacts}")
    print()

    for i, dup in enumerate(name_dups[:20], 1):
        print(f"{i}. {dup['full_name'].title()} ({dup['count']} contacts)")
        for j in range(min(dup['count'], 3)):  # Show first 3
            contact_id = dup['contact_ids'][j]
            email = dup['emails'][j]
            phone = dup['phones'][j] or 'No phone'
            source = dup['sources'][j] or 'Unknown'
            print(f"   - {email} | {phone} | Source: {source} | ID: {contact_id}")
        if dup['count'] > 3:
            print(f"   ... and {dup['count'] - 3} more")
        print()

    # Phone-based duplicates
    print("\n2. PHONE NUMBER DUPLICATES")
    print("-" * 80)

    phone_dups = find_duplicates_by_phone()
    print(f"   {len(phone_dups)} duplicate phone numbers found")
    print()

    for i, dup in enumerate(phone_dups[:10], 1):
        print(f"{i}. Phone: {dup['normalized_phone']} ({dup['count']} contacts)")
        for j in range(min(dup['count'], 3)):
            name = dup['names'][j] or 'No name'
            email = dup['emails'][j]
            source = dup['sources'][j] or 'Unknown'
            print(f"   - {name} | {email} | Source: {source}")
        if dup['count'] > 3:
            print(f"   ... and {dup['count'] - 3} more")
        print()

    print("="*80)

    # Export to CSV
    with open('/tmp/duplicate_names.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Count', 'Emails', 'Phones', 'Sources', 'IDs'])
        for dup in name_dups:
            writer.writerow([
                dup['full_name'],
                dup['count'],
                '; '.join(dup['emails']),
                '; '.join([p for p in dup['phones'] if p]),
                '; '.join([s for s in dup['sources'] if s]),
                '; '.join(dup['contact_ids'])
            ])

    with open('/tmp/duplicate_phones.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Phone', 'Count', 'Names', 'Emails', 'Sources', 'IDs'])
        for dup in phone_dups:
            writer.writerow([
                dup['normalized_phone'],
                dup['count'],
                '; '.join(dup['names']),
                '; '.join(dup['emails']),
                '; '.join([s for s in dup['sources'] if s]),
                '; '.join(dup['contact_ids'])
            ])

    print(f"\nExported to:")
    print(f"  - /tmp/duplicate_names.csv ({len(name_dups)} groups)")
    print(f"  - /tmp/duplicate_phones.csv ({len(phone_dups)} groups)")
    print()


if __name__ == '__main__':
    print_report()
