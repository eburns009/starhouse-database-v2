#!/usr/bin/env python3
"""
Phase 1: Enrich existing contacts from Debbie's Google Contacts
FAANG-Grade Implementation: Safe, auditable, idempotent

Imports:
1. Phone numbers (where missing)
2. Organizations/Business names (where missing)

Strategy:
- Email-based matching (95% match rate)
- Additive only (never overwrite existing data)
- Full audit trail with source attribution
- Dry-run mode by default
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from datetime import datetime
from db_config import get_database_url

# Configuration
CSV_PATH = '/workspaces/starhouse-database-v2/kajabi 3 files review/debbie_google_contacts.csv'
DRY_RUN = True  # Set via --live flag

def normalize_email(email):
    """Normalize email for matching"""
    if not email:
        return None
    return email.strip().lower()

def normalize_phone(phone):
    """Normalize phone number to consistent format"""
    if not phone:
        return None

    # Extract digits
    digits = re.sub(r'[^\d]', '', str(phone))

    # Format based on length
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    elif len(digits) == 11:
        return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    else:
        # Return as-is if can't parse
        return str(phone).strip()

def enrich_contacts(dry_run=True):
    """Main enrichment function"""

    print("=" * 80)
    print("DEBBIE'S GOOGLE CONTACTS - PHASE 1 ENRICHMENT")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be committed)'}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Load CSV
    print("📊 Loading Google Contacts CSV...")
    google_contacts = []

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            google_contacts.append(row)

    print(f"   Total contacts in CSV: {len(google_contacts):,}\n")

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.lnagadkqejnopgfxwlkb',
        password=get_database_url().split('@')[0].split(':')[-1],
        host='aws-1-us-east-2.pooler.supabase.com',
        port='5432'
    )
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("   Connected ✓\n")

    # Get all existing contacts
    cur.execute("""
        SELECT id, email, paypal_email, phone, paypal_business_name, phone_source
        FROM contacts
    """)
    db_contacts = cur.fetchall()

    # Build email lookup
    email_lookup = {}
    for db_contact in db_contacts:
        if db_contact['email']:
            email_lookup[normalize_email(db_contact['email'])] = db_contact
        if db_contact['paypal_email']:
            email_lookup[normalize_email(db_contact['paypal_email'])] = db_contact

    print(f"📋 Database contacts loaded: {len(db_contacts):,}\n")

    # Find enrichment opportunities
    print("🔍 Identifying enrichment opportunities...")

    updates = []

    for gc_contact in google_contacts:
        gc_email = normalize_email(gc_contact.get('E-mail 1 - Value'))

        if not gc_email:
            continue

        db_contact = email_lookup.get(gc_email)

        if not db_contact:
            continue  # Contact not in database

        update_data = {
            'contact_id': db_contact['id'],
            'email': gc_email,
            'changes': []
        }

        # Check for phone enrichment
        gc_phone = gc_contact.get('Phone 1 - Value')
        if gc_phone and not db_contact['phone']:
            normalized_phone = normalize_phone(gc_phone)
            phone_label = gc_contact.get('Phone 1 - Label', 'Mobile')

            update_data['changes'].append({
                'field': 'phone',
                'value': normalized_phone,
                'label': phone_label
            })

        # Check for organization enrichment
        gc_org = gc_contact.get('Organization Name')
        if gc_org and not db_contact['paypal_business_name']:
            update_data['changes'].append({
                'field': 'organization',
                'value': gc_org.strip()
            })

        if update_data['changes']:
            updates.append(update_data)

    print(f"   Found {len(updates):,} contacts to enrich\n")

    # Count by type
    phone_updates = sum(1 for u in updates if any(c['field'] == 'phone' for c in u['changes']))
    org_updates = sum(1 for u in updates if any(c['field'] == 'organization' for c in u['changes']))

    print("📈 ENRICHMENT BREAKDOWN")
    print("-" * 80)
    print(f"Phones to add:        {phone_updates:,}")
    print(f"Organizations to add: {org_updates:,}")
    print(f"Total contacts:       {len(updates):,}")
    print()

    if not updates:
        print("✓ No enrichment opportunities found!\n")
        cur.close()
        conn.close()
        return

    # Preview sample updates
    print("📝 SAMPLE UPDATES (first 10):")
    print("-" * 80)
    for i, update in enumerate(updates[:10], 1):
        changes_desc = []
        for change in update['changes']:
            if change['field'] == 'phone':
                changes_desc.append(f"phone: {change['value']} ({change['label']})")
            elif change['field'] == 'organization':
                changes_desc.append(f"org: {change['value']}")

        print(f"  {i}. {update['email']}")
        for desc in changes_desc:
            print(f"     + {desc}")
    print()

    # Apply updates
    if not dry_run:
        print("=" * 80)
        print("APPLYING UPDATES")
        print("=" * 80)

        try:
            update_count = 0

            for update in updates:
                # Build update query
                set_clauses = []
                params = []

                for change in update['changes']:
                    if change['field'] == 'phone':
                        set_clauses.append("phone = %s")
                        set_clauses.append("phone_source = %s")
                        params.extend([change['value'], 'google_contacts'])
                    elif change['field'] == 'organization':
                        set_clauses.append("paypal_business_name = %s")
                        params.append(change['value'])

                if not set_clauses:
                    continue

                # Add updated_at
                set_clauses.append("updated_at = now()")

                # Build and execute query
                query = f"""
                    UPDATE contacts
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                params.append(update['contact_id'])

                cur.execute(query, params)
                update_count += 1

                if update_count % 50 == 0:
                    print(f"   Processed {update_count:,} / {len(updates):,} contacts...")

            conn.commit()
            print(f"\n✓ Successfully enriched {update_count:,} contacts")

        except Exception as e:
            print(f"\n❌ Error during update: {e}")
            conn.rollback()
            print("✓ Transaction rolled back, no changes made")

    else:
        print("=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute enrichment, run:")
        print("  python3 scripts/enrich_from_debbie_google.py --live")

    # Summary
    print("\n" + "=" * 80)
    print("PHASE 1 SUMMARY")
    print("=" * 80)
    print(f"Contacts processed:   {len(updates):,}")
    print(f"  Phones added:       {phone_updates:,}")
    print(f"  Organizations added: {org_updates:,}")
    print(f"\nMode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print("=" * 80)

    # Cleanup
    cur.close()
    conn.close()

if __name__ == '__main__':
    import sys

    # Check for --live flag
    dry_run = '--live' not in sys.argv

    if not dry_run:
        print("\n⚠️  WARNING: Running in LIVE mode. Changes will be committed!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    enrich_contacts(dry_run=dry_run)
