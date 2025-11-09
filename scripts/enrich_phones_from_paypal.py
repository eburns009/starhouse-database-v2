#!/usr/bin/env python3
"""
Phone Number Enrichment from PayPal Transactions
================================================
Extract phone numbers from PayPal 2024 transaction data and enrich contacts

Data Source: paypal 2024.CSV
- Total records: 2,695
- With phone + email: 1,309 (48.6%)

Strategy:
1. Extract "Contact Phone Number" + "From Email Address" from PayPal CSV
2. Normalize phone numbers (handle various formats)
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
    # Remove leading 1 (US country code) if present and phone is 11 digits
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    # Must have at least 10 digits to be valid
    if len(digits) >= 10:
        return digits
    return None

def extract_phones_from_paypal():
    """Extract phone numbers from PayPal CSV"""
    paypal_file = "/workspaces/starhouse-database-v2/kajabi 3 files review/paypal 2024.CSV"
    phone_map = {}  # email -> phone

    # Track duplicates (keep most recent by row order)
    duplicate_count = 0

    with open(paypal_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('From Email Address', '').strip().lower()
            phone = row.get('Contact Phone Number', '').strip()

            phone_normalized = normalize_phone(phone)

            if email and phone_normalized:
                if email in phone_map and phone_map[email] != phone_normalized:
                    duplicate_count += 1
                # Keep the last occurrence (most recent transaction)
                phone_map[email] = phone_normalized

    return phone_map, duplicate_count

def main():
    print("=" * 70)
    print("PHONE NUMBER ENRICHMENT FROM PAYPAL 2024 TRANSACTIONS")
    print("=" * 70)
    print()

    # Extract phone numbers from PayPal
    print("Step 1: Extracting phone numbers from PayPal CSV...")
    paypal_phones, duplicate_count = extract_phones_from_paypal()
    print(f"  ✓ Found {len(paypal_phones)} unique emails with phones in PayPal")
    if duplicate_count > 0:
        print(f"  ℹ {duplicate_count} emails had multiple transactions (kept most recent)")

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
    print("\nStep 4: Matching contacts with PayPal data...")
    updates = []
    for contact_id, email, first_name, last_name, old_phone in contacts_needing_phone:
        email_lower = email.lower()
        if email_lower in paypal_phones:
            new_phone = paypal_phones[email_lower]
            updates.append((
                contact_id,
                new_phone,
                f"{first_name} {last_name}".strip(),
                email
            ))

    print(f"  ✓ Matched {len(updates)} contacts with phone numbers")

    if not updates:
        print("\n⚠ No contacts to update. Exiting.")
        conn.close()
        return

    # Backup and update
    print("\nStep 5: Creating backups and updating contacts...")
    for contact_id, new_phone, name, email in updates:
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
            'paypal_csv',
            'Enriched from PayPal 2024 transaction data'
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

    print(f"\nPayPal 2024 Enrichment:")
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
          AND enriched_at > NOW() - INTERVAL '4 hours'
    """)
    total_phone_enrichments = cur.fetchone()[0]

    cur.execute("""
        SELECT
            enrichment_type,
            COUNT(*) as count
        FROM contacts_enrichment_backup
        WHERE field_name = 'phone'
          AND enriched_at > NOW() - INTERVAL '4 hours'
        GROUP BY enrichment_type
        ORDER BY COUNT(*) DESC
    """)
    by_source = cur.fetchall()

    print(f"\nCumulative Phone Enrichments (This Session):")
    print(f"  Total: {total_phone_enrichments} contacts")
    for source, count in by_source:
        source_name = {
            'csv_import': 'Zoho',
            'ticket_tailor_csv': 'Ticket Tailor',
            'paypal_csv': 'PayPal'
        }.get(source, source)
        print(f"  {source_name}: {count} contacts")

    # Verification
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    cur.execute("""
        SELECT COUNT(*) FROM contacts_enrichment_backup
        WHERE enrichment_type = 'paypal_csv'
          AND enriched_at > NOW() - INTERVAL '5 minutes'
    """)
    backup_count = cur.fetchone()[0]
    print(f"  Backup records created: {backup_count}")
    print(f"  Updates committed: {len(updates)}")
    print(f"  Status: {'✓ PASS' if backup_count == len(updates) else '✗ FAIL'}")

    # Sample enriched contacts
    print("\n" + "=" * 70)
    print("SAMPLE ENRICHED CONTACTS (First 20)")
    print("=" * 70)
    for i, (contact_id, new_phone, name, email) in enumerate(updates[:20], 1):
        print(f"  {i:2}. {name[:30]:<30} → {new_phone:<12} ({email})")

    if len(updates) > 20:
        print(f"  ... and {len(updates) - 20} more")

    # Remaining opportunities
    remaining = len(contacts_needing_phone) - len(updates)
    print(f"\n" + "=" * 70)
    print(f"REMAINING OPPORTUNITIES")
    print(f"=" * 70)
    print(f"  Contacts still missing phone: {remaining}")
    print(f"  PayPal emails not in database: {len(paypal_phones) - len(updates)}")

    conn.close()
    print("\n✓ PayPal phone enrichment complete!")

if __name__ == '__main__':
    main()
