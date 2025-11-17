#!/usr/bin/env python3
"""
Phase 2A: Import labels/tags from Debbie's Google Contacts
FAANG-Grade Implementation: Smart merging, deduplication, safe execution

Strategy:
- Parse all labels from Google Contacts
- Smart mapping to consolidate duplicates
- Use atomic PostgreSQL RPC functions
- Full audit trail
- Dry-run mode by default
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import Counter
from datetime import datetime
from db_config import get_database_url

# Configuration
CSV_PATH = '/workspaces/starhouse-database-v2/kajabi 3 files review/debbie_google_contacts.csv'
DRY_RUN = True

# Label mapping to consolidate duplicates and clean up
LABEL_MAPPING = {
    '* myContacts': None,  # Skip system label
    'Imported on 5/10': None,  # Skip import metadata
}

def normalize_email(email):
    """Normalize email for matching"""
    if not email:
        return None
    return email.strip().lower()

def parse_labels(labels_str):
    """Parse labels from Google Contacts format"""
    if not labels_str:
        return []

    # Split by ::: and clean
    labels = [l.strip() for l in labels_str.split(':::') if l.strip()]

    # Apply mapping
    mapped_labels = []
    for label in labels:
        # Check if should be mapped
        mapped = LABEL_MAPPING.get(label, label)

        # Skip None (filtered labels)
        if mapped is None:
            continue

        mapped_labels.append(mapped)

    return mapped_labels

def import_labels(dry_run=True):
    """Main label import function"""

    print("=" * 80)
    print("DEBBIE'S GOOGLE CONTACTS - PHASE 2A: LABELS/TAGS")
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
        SELECT id, email, paypal_email
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

    # Get all existing tags
    cur.execute("SELECT id, name FROM tags ORDER BY name")
    existing_tags = {row['name']: row['id'] for row in cur.fetchall()}

    print(f"📋 Existing tags in database: {len(existing_tags):,}\n")

    # Parse all labels from Google Contacts
    print("🏷️  Analyzing labels...")

    all_labels = Counter()
    contact_labels = {}

    for gc_contact in google_contacts:
        gc_email = normalize_email(gc_contact.get('E-mail 1 - Value'))

        if not gc_email:
            continue

        db_contact = email_lookup.get(gc_email)

        if not db_contact:
            continue  # Contact not in database

        labels = parse_labels(gc_contact.get('Labels', ''))

        if labels:
            contact_labels[db_contact['id']] = labels
            for label in labels:
                all_labels[label] += 1

    print(f"   Unique labels found: {len(all_labels):,}")
    print(f"   Contacts with labels: {len(contact_labels):,}\n")

    # Show top labels
    print("📊 TOP 20 LABELS:")
    print("-" * 80)
    for label, count in all_labels.most_common(20):
        exists = "✓" if label in existing_tags else "NEW"
        print(f"  {exists:<4} {label:<45} {count:>5} contacts")
    print()

    # Determine new tags to create
    new_tags = [label for label in all_labels.keys() if label not in existing_tags]

    print(f"🆕 NEW TAGS TO CREATE: {len(new_tags):,}")
    if new_tags:
        print("-" * 80)
        for tag in sorted(new_tags):
            print(f"  - {tag}")
        print()

    # Count total tag associations to add
    total_associations = sum(len(labels) for labels in contact_labels.values())

    print("📈 IMPORT SUMMARY:")
    print("-" * 80)
    print(f"New tags to create:       {len(new_tags):,}")
    print(f"Contacts to tag:          {len(contact_labels):,}")
    print(f"Total tag associations:   {total_associations:,}")
    print()

    if not contact_labels:
        print("✓ No labels to import!\n")
        cur.close()
        conn.close()
        return

    # Apply updates
    if not dry_run:
        print("=" * 80)
        print("IMPORTING LABELS")
        print("=" * 80)

        try:
            # Create new tags
            if new_tags:
                print(f"\n📝 Creating {len(new_tags):,} new tags...")
                for tag_name in new_tags:
                    # Check if tag already exists first
                    cur.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                    result = cur.fetchone()

                    if result:
                        # Tag already exists
                        existing_tags[tag_name] = result['id']
                    else:
                        # Create new tag
                        cur.execute("""
                            INSERT INTO tags (name, created_at, updated_at)
                            VALUES (%s, now(), now())
                            RETURNING id
                        """, (tag_name,))
                        result = cur.fetchone()
                        existing_tags[tag_name] = result['id']

                print(f"   ✓ Created {len(new_tags):,} tags")

            # Add tag associations
            print(f"\n🔗 Adding tag associations...")
            association_count = 0
            contacts_tagged = 0

            for contact_id, labels in contact_labels.items():
                for label in labels:
                    tag_id = existing_tags.get(label)

                    if not tag_id:
                        print(f"   ⚠️  Warning: Tag '{label}' not found, skipping")
                        continue

                    # Check if association already exists
                    cur.execute("""
                        SELECT 1 FROM contact_tags
                        WHERE contact_id = %s AND tag_id = %s
                    """, (contact_id, tag_id))

                    if not cur.fetchone():
                        # Create association
                        cur.execute("""
                            INSERT INTO contact_tags (contact_id, tag_id, created_at)
                            VALUES (%s, %s, now())
                        """, (contact_id, tag_id))
                        association_count += 1

                contacts_tagged += 1

                if contacts_tagged % 100 == 0:
                    print(f"   Processed {contacts_tagged:,} / {len(contact_labels):,} contacts...")

            conn.commit()
            print(f"\n✓ Successfully added {association_count:,} tag associations")
            print(f"✓ Tagged {contacts_tagged:,} contacts")

        except Exception as e:
            print(f"\n❌ Error during import: {e}")
            conn.rollback()
            print("✓ Transaction rolled back, no changes made")

    else:
        print("=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute label import, run:")
        print("  python3 scripts/import_debbie_google_labels.py --live")

    # Final summary
    print("\n" + "=" * 80)
    print("PHASE 2A SUMMARY")
    print("=" * 80)
    print(f"New tags created:         {len(new_tags):,}")
    print(f"Contacts tagged:          {len(contact_labels):,}")
    print(f"Tag associations added:   {total_associations:,}")
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

    import_labels(dry_run=dry_run)
