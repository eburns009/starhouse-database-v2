#!/usr/bin/env python3
"""
Phone Number Enrichment from Ticket Tailor
==========================================
Extract phone numbers from Ticket Tailor event data and enrich contacts

Data Source: ticket_tailor_data.csv
- Total records: 4,400
- With mobile + email: 3,919 (89.1%)

Strategy:
1. Extract mobile number + email from Ticket Tailor CSV
2. Normalize phone numbers (remove country code, formatting)
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
DATABASE_URL = os.getenv('DATABASE_URL', 'PLACEHOLDER_USE_ENV_VAR')

def normalize_phone(phone):
    """Normalize phone number to digits only"""
    if not phone:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Remove leading 1 (US country code) if present and phone is 11 digits
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    # Must have at least 10 digits to be valid
    if len(digits) >= 10:
        return digits
    return None

def extract_phones_from_ticket_tailor():
    """Extract phone numbers from Ticket Tailor CSV"""
    tt_file = "/workspaces/starhouse-database-v2/kajabi 3 files review/ticket_tailor_data.csv"
    phone_map = {}  # email -> phone

    with open(tt_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            mobile = row.get('Mobile number', '').strip()

            phone_normalized = normalize_phone(mobile)

            if email and phone_normalized:
                # Keep the most recent entry if duplicates (last one wins)
                phone_map[email] = phone_normalized

    return phone_map

def main():
    print("=" * 70)
    print("PHONE NUMBER ENRICHMENT FROM TICKET TAILOR")
    print("=" * 70)
    print()

    # Extract phone numbers from Ticket Tailor
    print("Step 1: Extracting phone numbers from Ticket Tailor CSV...")
    tt_phones = extract_phones_from_ticket_tailor()
    print(f"  ✓ Found {len(tt_phones)} unique emails with phones in Ticket Tailor")

    # Connect to database
    print("\nStep 2: Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Ensure backup table exists
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
    print("\nStep 3: Finding contacts to enrich...")
    cur.execute("""
        SELECT id, email, first_name, last_name, phone
        FROM contacts
        WHERE (phone IS NULL OR phone = '')
          AND email IS NOT NULL
    """)
    contacts_needing_phone = cur.fetchall()
    print(f"  ✓ Found {len(contacts_needing_phone)} contacts without phone in database")

    # Match and prepare updates
    print("\nStep 4: Matching contacts with Ticket Tailor data...")
    updates = []
    for contact_id, email, first_name, last_name, old_phone in contacts_needing_phone:
        email_lower = email.lower()
        if email_lower in tt_phones:
            new_phone = tt_phones[email_lower]
            updates.append((
                contact_id,
                new_phone,
                f"{first_name} {last_name}".strip()
            ))

    print(f"  ✓ Matched {len(updates)} contacts with phone numbers")

    if not updates:
        print("\n⚠ No contacts to update. Exiting.")
        conn.close()
        return

    # Backup and update
    print("\nStep 5: Creating backups and updating contacts...")
    for contact_id, new_phone, name in updates:
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
            'ticket_tailor_csv',
            'Enriched from Ticket Tailor event data'
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

    print(f"\nTicket Tailor Enrichment:")
    print(f"  Total enriched: {len(updates)}")

    # Current completeness
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone <> '') as with_phone,
            COUNT(*) as total
        FROM contacts
    """)
    with_phone, total = cur.fetchone()
    completeness = 100.0 * with_phone / total

    # Previous completeness (before this run)
    previous_with_phone = with_phone - len(updates)
    previous_completeness = 100.0 * previous_with_phone / total

    print(f"\nPhone Completeness:")
    print(f"  Before: {previous_completeness:.1f}% ({previous_with_phone}/{total})")
    print(f"  After: {completeness:.1f}% ({with_phone}/{total})")
    print(f"  Improvement: +{completeness - previous_completeness:.1f}% (+{len(updates)} contacts)")

    # Cumulative this session
    cur.execute("""
        SELECT COUNT(*) FROM contacts_enrichment_backup
        WHERE field_name = 'phone'
          AND enriched_at > NOW() - INTERVAL '3 hours'
    """)
    total_phone_enrichments = cur.fetchone()[0]
    print(f"\nCumulative Phone Enrichments (This Session):")
    print(f"  Total: {total_phone_enrichments} contacts")
    print(f"  Zoho: 214 contacts")
    print(f"  Ticket Tailor: {len(updates)} contacts")

    # Verification
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    cur.execute("""
        SELECT COUNT(*) FROM contacts_enrichment_backup
        WHERE enrichment_type = 'ticket_tailor_csv'
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
    for i, (contact_id, new_phone, name) in enumerate(updates[:10], 1):
        print(f"  {i}. {name[:40]:<40} → {new_phone}")

    if len(updates) > 10:
        print(f"  ... and {len(updates) - 10} more")

    conn.close()
    print("\n✓ Ticket Tailor phone enrichment complete!")

if __name__ == '__main__':
    main()
