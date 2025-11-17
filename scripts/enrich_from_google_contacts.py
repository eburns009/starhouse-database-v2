#!/usr/bin/env python3
"""
Google Contacts Enrichment Script
FAANG-Grade Implementation: Safe, auditable, reversible

Phase 1: Low-Risk Enrichment
- MailChimp subscription status
- Phone numbers
- Organization names
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from datetime import datetime
import sys
from db_config import get_database_url

# Configuration
DRY_RUN = True  # Set to False to actually execute updates
BATCH_SIZE = 100

# Phone normalization regex
PHONE_PATTERN = re.compile(r'[\d\(\)\-\s\+\.]+')

def normalize_phone(phone):
    """Normalize phone number to consistent format"""
    if pd.isna(phone) or not phone:
        return None

    # Extract digits only
    digits = re.sub(r'[^\d]', '', str(phone))

    # US numbers
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    else:
        # Keep original if we can't parse
        return str(phone).strip()

def extract_mailchimp_status(notes):
    """Extract MailChimp subscription status from notes"""
    if pd.isna(notes):
        return None

    notes_str = str(notes)
    if 'MailChimp Status: Subscribed' in notes_str:
        return True
    elif 'MailChimp Status: Unsubscribed' in notes_str:
        return False
    return None

def enrich_contacts(dry_run=True):
    """Main enrichment function"""

    print("=" * 80)
    print("GOOGLE CONTACTS ENRICHMENT - PHASE 1")
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
    conn.autocommit = False  # Use transactions
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("   Connected ✓\n")

    # Get all database contacts
    print("📊 Loading database contacts...")
    cur.execute("""
        SELECT id, email, paypal_email, phone, paypal_business_name,
               email_subscribed, notes
        FROM contacts
    """)
    db_contacts = cur.fetchall()
    print(f"   Loaded {len(db_contacts):,} database contacts\n")

    # Build email lookup
    email_to_contact = {}
    for contact in db_contacts:
        if contact['email']:
            email_to_contact[contact['email'].lower().strip()] = contact
        if contact['paypal_email']:
            email_to_contact[contact['paypal_email'].lower().strip()] = contact

    # Track enrichment opportunities
    stats = {
        'matched': 0,
        'phone_enriched': 0,
        'org_enriched': 0,
        'mailchimp_subscribed': 0,
        'mailchimp_unsubscribed': 0,
        'skipped_already_has_phone': 0,
        'skipped_already_has_org': 0,
        'skipped_already_unsubscribed': 0,
        'errors': 0
    }

    updates = []
    audit_log = []

    print("🔍 Analyzing enrichment opportunities...\n")

    # Process each Google contact
    for idx, row in df.iterrows():
        # Try to find matching contact
        google_emails = []
        for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
            if pd.notna(row.get(col)):
                google_emails.append(row[col].lower().strip())

        # Find match
        db_contact = None
        matched_email = None
        for email in google_emails:
            if email in email_to_contact:
                db_contact = email_to_contact[email]
                matched_email = email
                break

        if not db_contact:
            continue  # No match, skip

        stats['matched'] += 1

        # Build update for this contact
        update = {
            'contact_id': db_contact['id'],
            'email': matched_email,
            'changes': []
        }

        # Check MailChimp status
        mailchimp_status = extract_mailchimp_status(row.get('Notes'))
        if mailchimp_status is not None:
            # CRITICAL: Never re-subscribe someone who unsubscribed
            if db_contact['email_subscribed'] == False and mailchimp_status == True:
                # DB says unsubscribed, Google says subscribed -> trust unsubscribe
                stats['skipped_already_unsubscribed'] += 1
            elif db_contact['email_subscribed'] != mailchimp_status:
                update['changes'].append({
                    'field': 'email_subscribed',
                    'old': db_contact['email_subscribed'],
                    'new': mailchimp_status,
                    'source': 'google_contacts_mailchimp'
                })
                if mailchimp_status:
                    stats['mailchimp_subscribed'] += 1
                else:
                    stats['mailchimp_unsubscribed'] += 1

        # Check phone enrichment
        google_phone = row.get('Phone 1 - Value')
        if pd.notna(google_phone) and google_phone:
            normalized_phone = normalize_phone(google_phone)
            if not db_contact['phone']:
                # DB has no phone, add it
                update['changes'].append({
                    'field': 'phone',
                    'old': None,
                    'new': normalized_phone,
                    'source': 'google_contacts'
                })
                stats['phone_enriched'] += 1
            else:
                stats['skipped_already_has_phone'] += 1

        # Check organization enrichment
        google_org = row.get('Organization Name')
        if pd.notna(google_org) and google_org:
            if not db_contact['paypal_business_name']:
                # DB has no organization, add it
                update['changes'].append({
                    'field': 'paypal_business_name',
                    'old': None,
                    'new': str(google_org).strip(),
                    'source': 'google_contacts'
                })
                stats['org_enriched'] += 1
            else:
                stats['skipped_already_has_org'] += 1

        # If we have changes, queue the update
        if update['changes']:
            updates.append(update)
            audit_log.append({
                'contact_id': db_contact['id'],
                'email': matched_email,
                'timestamp': datetime.now().isoformat(),
                'changes': update['changes']
            })

    # Print preview
    print("=" * 80)
    print("ENRICHMENT SUMMARY")
    print("=" * 80)
    print(f"\nMatched contacts: {stats['matched']:,}")
    print(f"\nProposed changes:")
    print(f"  📧 MailChimp subscribed updates: {stats['mailchimp_subscribed']:,}")
    print(f"  📧 MailChimp unsubscribed updates: {stats['mailchimp_unsubscribed']:,}")
    print(f"  📱 Phone number additions: {stats['phone_enriched']:,}")
    print(f"  🏢 Organization additions: {stats['org_enriched']:,}")
    print(f"\nSkipped (already have data):")
    print(f"  📱 Already have phone: {stats['skipped_already_has_phone']:,}")
    print(f"  🏢 Already have organization: {stats['skipped_already_has_org']:,}")
    print(f"  ⚠️  Already unsubscribed (protected): {stats['skipped_already_unsubscribed']:,}")
    print(f"\nTotal contacts to update: {len(updates):,}\n")

    if not updates:
        print("✓ No updates needed. Database is already enriched!\n")
        cur.close()
        conn.close()
        return

    # Show sample updates
    print("=" * 80)
    print("SAMPLE UPDATES (first 10)")
    print("=" * 80)
    for i, update in enumerate(updates[:10]):
        print(f"\n{i+1}. Contact: {update['email']}")
        for change in update['changes']:
            print(f"   {change['field']}: {change['old']} → {change['new']}")

    # Execute updates if not dry run
    if not dry_run:
        print("\n" + "=" * 80)
        print("EXECUTING UPDATES")
        print("=" * 80)

        try:
            update_count = 0
            for update in updates:
                # Build SQL update
                set_clauses = []
                params = []

                for change in update['changes']:
                    set_clauses.append(f"{change['field']} = %s")
                    params.append(change['new'])

                # Add updated_at
                set_clauses.append("updated_at = now()")

                # Add contact_id for WHERE clause
                params.append(update['contact_id'])

                sql = f"""
                    UPDATE contacts
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """

                cur.execute(sql, params)
                update_count += 1

                if update_count % BATCH_SIZE == 0:
                    print(f"   Processed {update_count:,} / {len(updates):,} contacts...")

            # Commit transaction
            conn.commit()
            print(f"\n✓ Successfully updated {update_count:,} contacts")

            # Write audit log
            audit_df = pd.DataFrame(audit_log)
            audit_file = f'/workspaces/starhouse-database-v2/logs/google_contacts_enrichment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            audit_df.to_csv(audit_file, index=False)
            print(f"✓ Audit log written to: {audit_file}")

        except Exception as e:
            print(f"\n❌ Error during update: {e}")
            conn.rollback()
            print("✓ Transaction rolled back, no changes made")
            stats['errors'] += 1

    else:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute these updates, run:")
        print("  python3 scripts/enrich_from_google_contacts.py --live")

    # Cleanup
    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("ENRICHMENT COMPLETE")
    print("=" * 80)

    return stats

if __name__ == '__main__':
    # Check for --live flag
    dry_run = '--live' not in sys.argv

    if not dry_run:
        print("\n⚠️  WARNING: Running in LIVE mode. Changes will be committed!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    stats = enrich_contacts(dry_run=dry_run)
