#!/usr/bin/env python3
"""
Google Contacts Label/Tag Import - Phase 2A
FAANG-Grade Implementation: Safe, auditable, reversible

Imports labels from Google Contacts as tags in the database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import sys
from db_config import get_database_url

# Configuration
DRY_RUN = True

# Label mapping configuration
LABEL_MAPPING = {
    # SKIP - System/metadata labels (no business value)
    '* myContacts': None,
    '* starred': None,
    'Imported on 5/10': None,
    'Imported on 11/9': None,
    'Imported on 11/9 1': None,

    # MERGE - Multiple Google labels map to same tag
    'Current Keepers': 'Current Keeper',
    '11-9-2025 Current Keepers': 'Current Keeper',

    'New Keeper 4/12/25': 'New Keeper',
    'New Keeper 4/13 2024': 'New Keeper',
    'New Keeper 9/7/2024': 'New Keeper',
    'New Keeper 11/23 Scott and Shanti': 'New Keeper',

    'StarHouse Mysteries': 'StarHouse Mysteries',
    'StarHouse Mysteries 2/10/25': 'StarHouse Mysteries',

    # DIRECT MAP - One-to-one mapping
    'Paid Members': 'Paid Member',
    'Complimentary Members': 'Complimentary Member',
    'Program Partner': 'Program Partners',  # Maps to existing tag
    'Preferred Keepers': 'Preferred Keeper',
    'Past Keepers': 'Past Keeper',
    'Tech Keeper': 'Tech Keeper',
    'Past Member': 'Past Member',
    'Made Donation': 'Donor',
    'GAP Friends Group': 'GAP Friends',
    'Star Wisdom': 'Star Wisdom',
    'GAP Initiative Parents': 'GAP Parents',
    'SFPD Board Members': 'Board Member',
    'Founder': 'Founder',
    'Neighbor': 'Neighbor',
    'YPO': 'YPO',
    'Retreat Cabin': 'Retreat Cabin',
    'Transformations': 'Transformations',
    'Catering': 'Catering',
    '12 Senses': '12 Senses',
    'EarthStar Experience': 'EarthStar Experiences interest',  # Maps to existing
    'Volunteer': 'Volunteer',
}

def import_labels_as_tags(dry_run=True):
    """Main import function"""

    print("=" * 80)
    print("GOOGLE CONTACTS LABEL/TAG IMPORT - PHASE 2A")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be committed)'}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Load Google Contacts
    print("📥 Loading Google Contacts...")
    df = pd.read_csv('/workspaces/starhouse-database-v2/kajabi 3 files review/ascpr_google_contacts.csv')
    print(f"   Loaded {len(df):,} contacts from Google\n")

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

    # Get existing tags
    print("📊 Loading existing tags...")
    cur.execute("SELECT id, name, description FROM tags ORDER BY name")
    existing_tags = cur.fetchall()

    tag_name_to_id = {tag['name']: tag['id'] for tag in existing_tags}
    print(f"   Loaded {len(existing_tags):,} existing tags\n")

    # Get all database contacts with emails
    print("📊 Loading database contacts...")
    cur.execute("SELECT id, email, paypal_email FROM contacts")
    db_contacts = cur.fetchall()

    email_to_contact_id = {}
    for contact in db_contacts:
        if contact['email']:
            email_to_contact_id[contact['email'].lower().strip()] = contact['id']
        if contact['paypal_email']:
            email_to_contact_id[contact['paypal_email'].lower().strip()] = contact['id']

    print(f"   Loaded {len(db_contacts):,} database contacts\n")

    # Analyze labels
    print("🔍 Analyzing labels from Google Contacts...")
    label_contacts = {}  # tag_name -> list of contact_ids

    skipped_labels = set()
    matched_contacts = 0
    unmatched_contacts = 0

    for idx, row in df.iterrows():
        labels = row.get('Labels')

        if pd.isna(labels):
            continue

        # Get contact emails
        google_emails = []
        for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
            if pd.notna(row.get(col)):
                google_emails.append(row[col].lower().strip())

        # Find matching contact in database
        contact_id = None
        for email in google_emails:
            if email in email_to_contact_id:
                contact_id = email_to_contact_id[email]
                matched_contacts += 1
                break

        if not contact_id:
            unmatched_contacts += 1
            continue

        # Parse labels
        label_list = [l.strip() for l in str(labels).split(':::')]

        for google_label in label_list:
            # Map Google label to database tag name
            if google_label in LABEL_MAPPING:
                tag_name = LABEL_MAPPING[google_label]

                if tag_name is None:
                    # Skip this label
                    skipped_labels.add(google_label)
                    continue

                # Add contact to this tag
                if tag_name not in label_contacts:
                    label_contacts[tag_name] = set()

                label_contacts[tag_name].add(contact_id)

    print(f"   Matched contacts: {matched_contacts:,}")
    print(f"   Unmatched contacts: {unmatched_contacts:,}")
    print(f"   Skipped labels: {len(skipped_labels)} ({', '.join(sorted(skipped_labels)[:5])}...)")
    print(f"   Unique tags to import: {len(label_contacts)}\n")

    # Determine which tags need to be created
    tags_to_create = []
    for tag_name in label_contacts.keys():
        if tag_name not in tag_name_to_id:
            tags_to_create.append(tag_name)

    print("=" * 80)
    print("TAG CREATION PLAN")
    print("=" * 80)
    print(f"\nTags to create: {len(tags_to_create)}\n")

    for tag_name in sorted(tags_to_create):
        contact_count = len(label_contacts[tag_name])
        print(f"  CREATE: {tag_name:40} ({contact_count:,} contacts)")

    print(f"\nExisting tags to use: {len([t for t in label_contacts.keys() if t in tag_name_to_id])}\n")

    for tag_name in sorted([t for t in label_contacts.keys() if t in tag_name_to_id]):
        contact_count = len(label_contacts[tag_name])
        print(f"  USE:    {tag_name:40} ({contact_count:,} contacts)")

    # Create new tags if not dry run
    if not dry_run and tags_to_create:
        print("\n📝 Creating new tags...")
        for tag_name in tags_to_create:
            cur.execute("""
                INSERT INTO tags (name, description, created_at, updated_at)
                VALUES (%s, %s, now(), now())
                RETURNING id
            """, (tag_name, f'Imported from Google Contacts on {datetime.now().strftime("%Y-%m-%d")}'))

            tag_id = cur.fetchone()['id']
            tag_name_to_id[tag_name] = tag_id
            print(f"   Created: {tag_name} (ID: {tag_id})")

        conn.commit()
        print(f"   ✓ Created {len(tags_to_create)} tags\n")

    # Plan tag associations
    print("=" * 80)
    print("TAG ASSOCIATION PLAN")
    print("=" * 80)

    total_associations = sum(len(contacts) for contacts in label_contacts.values())
    print(f"\nTotal tag associations to create: {total_associations:,}\n")

    # Show top 10 tags by contact count
    print("Top 10 tags by contact count:\n")
    sorted_tags = sorted(label_contacts.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for tag_name, contact_ids in sorted_tags:
        print(f"  {len(contact_ids):5,} | {tag_name}")

    # Import tag associations
    if not dry_run:
        print("\n📝 Creating tag associations...")

        # Get existing associations to avoid duplicates
        cur.execute("SELECT contact_id, tag_id FROM contact_tags")
        existing_associations = set((row['contact_id'], row['tag_id']) for row in cur.fetchall())

        associations_created = 0
        associations_skipped = 0

        for tag_name, contact_ids in label_contacts.items():
            tag_id = tag_name_to_id.get(tag_name)

            if not tag_id:
                print(f"   ⚠️  Skipping {tag_name} - tag not found in database")
                continue

            for contact_id in contact_ids:
                # Check if association already exists
                if (contact_id, tag_id) in existing_associations:
                    associations_skipped += 1
                    continue

                # Create association
                cur.execute("""
                    INSERT INTO contact_tags (contact_id, tag_id, created_at)
                    VALUES (%s, %s, now())
                    ON CONFLICT (contact_id, tag_id) DO NOTHING
                """, (contact_id, tag_id))

                associations_created += 1

                if associations_created % 500 == 0:
                    print(f"   Processed {associations_created:,} / {total_associations:,} associations...")

        conn.commit()
        print(f"\n   ✓ Created {associations_created:,} tag associations")
        print(f"   ⏭️  Skipped {associations_skipped:,} existing associations")

        # Write audit log
        audit_data = []
        for tag_name, contact_ids in label_contacts.items():
            audit_data.append({
                'tag_name': tag_name,
                'tag_id': tag_name_to_id.get(tag_name),
                'contact_count': len(contact_ids),
                'timestamp': datetime.now().isoformat()
            })

        audit_df = pd.DataFrame(audit_data)
        audit_file = f'/workspaces/starhouse-database-v2/logs/google_labels_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        audit_df.to_csv(audit_file, index=False)
        print(f"   ✓ Audit log written to: {audit_file}")

    else:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute these changes, run:")
        print("  python3 scripts/import_google_labels_as_tags.py --live")

    # Cleanup
    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("LABEL/TAG IMPORT COMPLETE")
    print("=" * 80)

    return {
        'tags_to_create': len(tags_to_create),
        'total_associations': total_associations,
        'matched_contacts': matched_contacts
    }

if __name__ == '__main__':
    # Check for --live flag
    dry_run = '--live' not in sys.argv

    if not dry_run:
        print("\n⚠️  WARNING: Running in LIVE mode. Changes will be committed!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    stats = import_labels_as_tags(dry_run=dry_run)
