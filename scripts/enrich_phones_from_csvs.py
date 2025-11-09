#!/usr/bin/env python3
"""
Phone Number Enrichment from Kajabi and Zoho CSVs
=================================================
Extract phone numbers from source CSV files and enrich contacts table

Data Sources:
- Kajabi: 318 contacts with phone numbers (5.6%)
- Zoho: 363 contacts with phone numbers (11.0%)
- Potential: Up to 681 contacts enriched

Strategy:
1. Extract phone+email from Kajabi CSV
2. Extract phone+email from Zoho CSV
3. Match by email (case-insensitive)
4. Update contacts missing phone
5. Backup and verify
"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_values
import re

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://***REMOVED***:***REMOVED***@***REMOVED***:6543/postgres')

def normalize_phone(phone):
    """Normalize phone number to digits only"""
    if not phone:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Must have at least 10 digits to be valid
    if len(digits) >= 10:
        return digits
    return None

def extract_phones_from_kajabi():
    """Extract phone numbers from Kajabi CSV"""
    kajabi_file = "/workspaces/starhouse-database-v2/kajabi 3 files review/kajabi contacts.csv"
    phone_map = {}  # email -> phone

    with open(kajabi_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            phone = row.get('Phone Number (phone_number)', '').strip()
            mobile = row.get('Mobile Phone Number (mobile_phone_number)', '').strip()

            # Prefer phone, fallback to mobile
            phone_raw = phone or mobile
            phone_normalized = normalize_phone(phone_raw)

            if email and phone_normalized:
                phone_map[email] = phone_normalized

    return phone_map

def extract_phones_from_zoho():
    """Extract phone numbers from Zoho CSV"""
    zoho_file = "/workspaces/starhouse-database-v2/kajabi 3 files review/Zoho_Contacts_2025_11_08.csv"
    phone_map = {}  # email -> phone

    with open(zoho_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            phone = row.get('Phone', '').strip()

            phone_normalized = normalize_phone(phone)

            if email and phone_normalized:
                phone_map[email] = phone_normalized

    return phone_map

def main():
    print("=" * 70)
    print("PHONE NUMBER ENRICHMENT FROM KAJABI AND ZOHO CSVs")
    print("=" * 70)
    print()

    # Extract phone numbers from CSVs
    print("Step 1: Extracting phone numbers from Kajabi CSV...")
    kajabi_phones = extract_phones_from_kajabi()
    print(f"  ✓ Found {len(kajabi_phones)} contacts with phones in Kajabi")

    print("\nStep 2: Extracting phone numbers from Zoho CSV...")
    zoho_phones = extract_phones_from_zoho()
    print(f"  ✓ Found {len(zoho_phones)} contacts with phones in Zoho")

    # Merge phone maps (Zoho takes precedence if both exist)
    print("\nStep 3: Merging phone data...")
    all_phones = {**kajabi_phones, **zoho_phones}
    print(f"  ✓ Total unique emails with phones: {len(all_phones)}")
    print(f"  ✓ Overlap (both sources): {len(kajabi_phones) + len(zoho_phones) - len(all_phones)}")

    # Connect to database
    print("\nStep 4: Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create backup table if needed
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts_enrichment_backup (
            backup_id SERIAL PRIMARY KEY,
            contact_id UUID NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            enrichment_type TEXT NOT NULL,
            enriched_at TIMESTAMP DEFAULT NOW(),
            notes TEXT
        );
    """)

    # Find contacts that need phone enrichment
    print("\nStep 5: Finding contacts to enrich...")
    cur.execute("""
        SELECT id, email, first_name, last_name, phone
        FROM contacts
        WHERE (phone IS NULL OR phone = '')
          AND email IS NOT NULL
    """)
    contacts_needing_phone = cur.fetchall()
    print(f"  ✓ Found {len(contacts_needing_phone)} contacts without phone in database")

    # Match and prepare updates
    print("\nStep 6: Matching contacts...")
    updates = []
    for contact_id, email, first_name, last_name, old_phone in contacts_needing_phone:
        email_lower = email.lower()
        if email_lower in all_phones:
            new_phone = all_phones[email_lower]
            source = "Kajabi" if email_lower in kajabi_phones else "Zoho"
            if email_lower in kajabi_phones and email_lower in zoho_phones:
                source = "Both (Zoho priority)"

            updates.append((
                contact_id,
                new_phone,
                source,
                f"{first_name} {last_name}".strip()
            ))

    print(f"  ✓ Matched {len(updates)} contacts with phone numbers")

    if not updates:
        print("\n⚠ No contacts to update. Exiting.")
        conn.close()
        return

    # Backup and update
    print("\nStep 7: Creating backups and updating contacts...")
    for contact_id, new_phone, source, name in updates:
        # Backup
        cur.execute("""
            INSERT INTO contacts_enrichment_backup
            (contact_id, field_name, old_value, new_value, enrichment_type, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            contact_id,
            'phone',
            None,
            new_phone,
            'csv_import',
            f'Enriched from {source} CSV'
        ))

        # Update
        cur.execute("""
            UPDATE contacts
            SET phone = %s, updated_at = NOW()
            WHERE id = %s
        """, (new_phone, contact_id))

    conn.commit()
    print(f"  ✓ Updated {len(updates)} contacts")

    # Summary
    print("\n" + "=" * 70)
    print("ENRICHMENT SUMMARY")
    print("=" * 70)

    # By source
    kajabi_count = sum(1 for _, _, src, _ in updates if 'Kajabi' in src)
    zoho_count = sum(1 for _, _, src, _ in updates if src == 'Zoho')
    both_count = sum(1 for _, _, src, _ in updates if 'Both' in src)

    print(f"\nBy Source:")
    print(f"  Kajabi only: {kajabi_count}")
    print(f"  Zoho only: {zoho_count}")
    print(f"  Both (Zoho priority): {both_count}")
    print(f"  TOTAL: {len(updates)}")

    # Current completeness
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone <> '') as with_phone,
            COUNT(*) as total
        FROM contacts
    """)
    with_phone, total = cur.fetchone()
    completeness = 100.0 * with_phone / total

    print(f"\nPhone Completeness:")
    print(f"  Before: 35.7%")
    print(f"  After: {completeness:.1f}%")
    print(f"  Improvement: +{completeness - 35.7:.1f}%")
    print(f"  Contacts with phone: {with_phone}/{total}")

    # Verification
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    cur.execute("""
        SELECT COUNT(*) FROM contacts_enrichment_backup
        WHERE enrichment_type = 'csv_import'
          AND enriched_at > NOW() - INTERVAL '5 minutes'
    """)
    backup_count = cur.fetchone()[0]
    print(f"  Backup records created: {backup_count}")
    print(f"  Updates committed: {len(updates)}")
    print(f"  Status: {'✓ PASS' if backup_count == len(updates) else '✗ FAIL'}")

    # Sample enriched contacts
    print("\n" + "=" * 70)
    print("SAMPLE ENRICHED CONTACTS (First 10)")
    print("=" * 70)
    for i, (contact_id, new_phone, source, name) in enumerate(updates[:10], 1):
        print(f"  {i}. {name} → {new_phone} (from {source})")

    if len(updates) > 10:
        print(f"  ... and {len(updates) - 10} more")

    conn.close()
    print("\n✓ Phone enrichment complete!")

if __name__ == '__main__':
    main()
