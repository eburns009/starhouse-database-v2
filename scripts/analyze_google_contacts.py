#!/usr/bin/env python3
"""
FAANG-Grade Analysis: Google Contacts Import Opportunities
Analyzes Google Contacts CSV for enrichment opportunities
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from collections import defaultdict
import re

def analyze_google_contacts():
    """Comprehensive analysis of Google Contacts data"""

    # Load Google Contacts
    print("=" * 80)
    print("GOOGLE CONTACTS ANALYSIS - FAANG ENGINEERING PRINCIPLES")
    print("=" * 80)

    df = pd.read_csv('/workspaces/starhouse-database-v2/kajabi 3 files review/ascpr_google_contacts.csv')

    print(f"\n📊 DATASET OVERVIEW")
    print(f"Total records: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    # Analyze field population
    print(f"\n📋 FIELD POPULATION ANALYSIS")
    print("-" * 80)

    key_fields = {
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'E-mail 1 - Value': 'email1',
        'E-mail 2 - Value': 'email2',
        'E-mail 3 - Value': 'email3',
        'Phone 1 - Value': 'phone1',
        'Phone 2 - Value': 'phone2',
        'Phone 3 - Value': 'phone3',
        'Address 1 - Formatted': 'address1',
        'Address 2 - Formatted': 'address2',
        'Organization Name': 'organization',
        'Organization Title': 'title',
        'Birthday': 'birthday',
        'Notes': 'notes',
        'Labels': 'labels',
        'Website 1 - Value': 'website'
    }

    population_stats = {}
    for field, short_name in key_fields.items():
        if field in df.columns:
            populated = df[field].notna().sum()
            pct = (populated / len(df)) * 100
            population_stats[short_name] = {
                'count': populated,
                'percentage': pct,
                'field': field
            }
            print(f"{field:30} {populated:5,} ({pct:5.1f}%)")

    # Email analysis
    print(f"\n📧 EMAIL DATA QUALITY")
    print("-" * 80)
    total_contacts_with_email = df[df['E-mail 1 - Value'].notna()].shape[0]
    contacts_with_multiple_emails = df[df['E-mail 2 - Value'].notna()].shape[0]
    contacts_with_3_emails = df[df['E-mail 3 - Value'].notna()].shape[0]

    print(f"Contacts with at least 1 email: {total_contacts_with_email:,}")
    print(f"Contacts with 2+ emails: {contacts_with_multiple_emails:,}")
    print(f"Contacts with 3 emails: {contacts_with_3_emails:,}")

    # Extract all unique emails
    all_emails = set()
    for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
        if col in df.columns:
            emails = df[col].dropna().astype(str)
            all_emails.update(emails)

    print(f"Total unique email addresses: {len(all_emails):,}")

    # Phone analysis
    print(f"\n📱 PHONE DATA QUALITY")
    print("-" * 80)
    total_with_phone = df[df['Phone 1 - Value'].notna()].shape[0]
    multiple_phones = df[df['Phone 2 - Value'].notna()].shape[0]

    print(f"Contacts with phone: {total_with_phone:,}")
    print(f"Contacts with multiple phones: {multiple_phones:,}")

    # Address analysis
    print(f"\n🏠 ADDRESS DATA QUALITY")
    print("-" * 80)
    total_with_address = df[df['Address 1 - Formatted'].notna()].shape[0]
    multiple_addresses = df[df['Address 2 - Formatted'].notna()].shape[0]

    print(f"Contacts with address: {total_with_address:,}")
    print(f"Contacts with 2 addresses: {multiple_addresses:,}")

    # Labels/Tags analysis
    print(f"\n🏷️  LABEL/TAG ANALYSIS")
    print("-" * 80)
    labels_data = df[df['Labels'].notna()]['Labels']
    all_labels = set()
    for labels in labels_data:
        if pd.notna(labels):
            # Split by ::: to get individual labels
            label_list = [l.strip() for l in str(labels).split(':::')]
            all_labels.update(label_list)

    print(f"Contacts with labels: {len(labels_data):,}")
    print(f"Unique labels found: {len(all_labels)}")

    # Show top labels
    label_counts = defaultdict(int)
    for labels in labels_data:
        if pd.notna(labels):
            label_list = [l.strip() for l in str(labels).split(':::')]
            for label in label_list:
                label_counts[label] += 1

    print("\nTop 15 labels:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {label:40} {count:5,}")

    # Notes analysis
    print(f"\n📝 NOTES/CUSTOM FIELDS")
    print("-" * 80)
    notes_with_mailchimp = df[df['Notes'].notna() & df['Notes'].str.contains('MailChimp', na=False)]
    print(f"Contacts with notes: {df['Notes'].notna().sum():,}")
    print(f"Contacts with MailChimp status in notes: {len(notes_with_mailchimp):,}")

    # Parse MailChimp status
    subscribed = df[df['Notes'].notna() & df['Notes'].str.contains('MailChimp Status: Subscribed', na=False)]
    unsubscribed = df[df['Notes'].notna() & df['Notes'].str.contains('MailChimp Status: Unsubscribed', na=False)]

    print(f"  MailChimp Subscribed: {len(subscribed):,}")
    print(f"  MailChimp Unsubscribed: {len(unsubscribed):,}")

    # Organization analysis
    print(f"\n🏢 ORGANIZATION DATA")
    print("-" * 80)
    print(f"Contacts with organization: {df['Organization Name'].notna().sum():,}")
    print(f"Contacts with title: {df['Organization Title'].notna().sum():,}")

    # Now compare with database
    print(f"\n" + "=" * 80)
    print("DATABASE ENRICHMENT OPPORTUNITY ANALYSIS")
    print("=" * 80)

    # Connect to database
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.lnagadkqejnopgfxwlkb',
        password='gqelzN6LRew4Cy9H',
        host='aws-1-us-east-2.pooler.supabase.com',
        port='5432'
    )

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get all database contacts
    cur.execute("""
        SELECT id, first_name, last_name, additional_name,
               email, email_2, email_3,
               phone, phone_2, phone_3,
               street_address, city, state, postal_code,
               organization, notes,
               email_subscribed
        FROM contacts
        WHERE is_deleted = false
    """)

    db_contacts = cur.fetchall()
    print(f"\n📊 Current database: {len(db_contacts):,} active contacts")

    # Build email lookup
    db_emails = {}
    for contact in db_contacts:
        for email_field in ['email', 'email_2', 'email_3']:
            if contact[email_field]:
                email = contact[email_field].lower().strip()
                db_emails[email] = contact

    print(f"Total email addresses in database: {len(db_emails):,}")

    # Match Google contacts to database
    matches = []
    new_contacts = []
    enrichment_opportunities = []

    for idx, row in df.iterrows():
        google_emails = []
        for col in ['E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value']:
            if pd.notna(row.get(col)):
                google_emails.append(row[col].lower().strip())

        # Try to match
        matched_contact = None
        for email in google_emails:
            if email in db_emails:
                matched_contact = db_emails[email]
                break

        if matched_contact:
            matches.append({
                'google_row': row,
                'db_contact': matched_contact
            })
        else:
            if google_emails:  # Only count as new if has email
                new_contacts.append(row)

    print(f"\n🔍 MATCHING RESULTS")
    print("-" * 80)
    print(f"Google contacts matched to database: {len(matches):,}")
    print(f"New contacts not in database: {len(new_contacts):,}")

    # Analyze enrichment opportunities for matched contacts
    print(f"\n💎 ENRICHMENT OPPORTUNITIES (Matched Contacts)")
    print("-" * 80)

    enrichment_stats = {
        'phone_additions': 0,
        'address_additions': 0,
        'organization_additions': 0,
        'birthday_additions': 0,
        'additional_emails': 0,
        'notes_additions': 0,
        'labels_available': 0
    }

    for match in matches:
        google = match['google_row']
        db = match['db_contact']

        # Phone enrichment
        google_phones = [google.get('Phone 1 - Value'), google.get('Phone 2 - Value'), google.get('Phone 3 - Value')]
        google_phones = [p for p in google_phones if pd.notna(p)]
        db_phones = [db['phone'], db['phone_2'], db['phone_3']]
        db_phones = [p for p in db_phones if p]

        if google_phones and len(google_phones) > len(db_phones):
            enrichment_stats['phone_additions'] += 1

        # Address enrichment
        if pd.notna(google.get('Address 1 - Formatted')) and not db['street_address']:
            enrichment_stats['address_additions'] += 1

        # Organization enrichment
        if pd.notna(google.get('Organization Name')) and not db['organization']:
            enrichment_stats['organization_additions'] += 1

        # Birthday enrichment
        if pd.notna(google.get('Birthday')):
            enrichment_stats['birthday_additions'] += 1

        # Additional emails
        google_email_count = len([e for e in [google.get('E-mail 1 - Value'), google.get('E-mail 2 - Value'), google.get('E-mail 3 - Value')] if pd.notna(e)])
        db_email_count = len([e for e in [db['email'], db['email_2'], db['email_3']] if e])

        if google_email_count > db_email_count:
            enrichment_stats['additional_emails'] += 1

        # Notes enrichment
        if pd.notna(google.get('Notes')):
            enrichment_stats['notes_additions'] += 1

        # Labels
        if pd.notna(google.get('Labels')):
            enrichment_stats['labels_available'] += 1

    for stat, count in enrichment_stats.items():
        pct = (count / len(matches) * 100) if matches else 0
        print(f"{stat.replace('_', ' ').title():30} {count:5,} ({pct:5.1f}%)")

    # New contact analysis
    print(f"\n🆕 NEW CONTACT ANALYSIS")
    print("-" * 80)
    print(f"Total new contacts: {len(new_contacts):,}")

    new_with_phone = sum(1 for c in new_contacts if pd.notna(c.get('Phone 1 - Value')))
    new_with_address = sum(1 for c in new_contacts if pd.notna(c.get('Address 1 - Formatted')))
    new_with_org = sum(1 for c in new_contacts if pd.notna(c.get('Organization Name')))

    print(f"New contacts with phone: {new_with_phone:,}")
    print(f"New contacts with address: {new_with_address:,}")
    print(f"New contacts with organization: {new_with_org:,}")

    # Priority labels in new contacts
    priority_labels = ['Current Keepers', 'Preferred Keepers', 'Paid Members', 'Program Partner']
    new_with_priority_labels = 0
    for contact in new_contacts:
        labels = contact.get('Labels')
        if pd.notna(labels):
            for priority in priority_labels:
                if priority in str(labels):
                    new_with_priority_labels += 1
                    break

    print(f"New contacts with priority labels: {new_with_priority_labels:,}")

    # FAANG Recommendations
    print(f"\n" + "=" * 80)
    print("FAANG-LEVEL RECOMMENDATIONS")
    print("=" * 80)

    print("\n🎯 PRIORITY 1: HIGH-VALUE ENRICHMENT (Immediate Action)")
    print("-" * 80)
    print(f"1. Phone Number Enrichment: {enrichment_stats['phone_additions']:,} contacts")
    print(f"   Impact: Enables SMS/text communication channel")
    print(f"   Effort: Low (direct field mapping)")

    print(f"\n2. Address Enrichment: {enrichment_stats['address_additions']:,} contacts")
    print(f"   Impact: Enables mailing list, physical outreach")
    print(f"   Effort: Medium (needs parsing/validation)")

    print(f"\n3. Additional Email Addresses: {enrichment_stats['additional_emails']:,} contacts")
    print(f"   Impact: Better deliverability, contact redundancy")
    print(f"   Effort: Low (direct field mapping)")

    print("\n🎯 PRIORITY 2: SEGMENTATION & ENGAGEMENT")
    print("-" * 80)
    print(f"1. Label/Tag Import: {enrichment_stats['labels_available']:,} contacts have labels")
    print(f"   Impact: Better segmentation, targeted campaigns")
    print(f"   Effort: Medium (mapping Google labels to tags)")
    print(f"   Unique labels found: {len(all_labels)}")

    print(f"\n2. MailChimp Status Reconciliation:")
    print(f"   Subscribed: {len(subscribed):,}")
    print(f"   Unsubscribed: {len(unsubscribed):,}")
    print(f"   Impact: GDPR compliance, reduce bounce rate")
    print(f"   Effort: Low (parse notes field)")

    print("\n🎯 PRIORITY 3: NEW CONTACT ACQUISITION")
    print("-" * 80)
    print(f"1. Import {len(new_contacts):,} new contacts")
    print(f"   High-value subset: {new_with_priority_labels:,} with priority labels")
    print(f"   Data quality: {new_with_phone:,} have phone, {new_with_address:,} have address")
    print(f"   Impact: Expand database, reach new audience")
    print(f"   Effort: Medium (deduplication, validation)")

    print("\n🎯 PRIORITY 4: METADATA ENRICHMENT")
    print("-" * 80)
    print(f"1. Birthday Data: {enrichment_stats['birthday_additions']:,} contacts")
    print(f"   Impact: Personalized engagement, birthday campaigns")
    print(f"   Effort: Low (direct field mapping)")

    print(f"\n2. Organization Data: {enrichment_stats['organization_additions']:,} contacts")
    print(f"   Impact: B2B opportunities, segmentation")
    print(f"   Effort: Low (direct field mapping)")

    print(f"\n3. Notes/Context: {enrichment_stats['notes_additions']:,} contacts have notes")
    print(f"   Impact: Historical context, relationship intelligence")
    print(f"   Effort: Low (append to notes field)")

    # Implementation recommendations
    print("\n" + "=" * 80)
    print("IMPLEMENTATION STRATEGY (FAANG Best Practices)")
    print("=" * 80)

    print("""
Phase 1: Data Quality & Validation (Week 1)
  □ Run deduplication analysis (email-based matching)
  □ Validate phone numbers (format normalization)
  □ Validate addresses (USPS/SmartyStreets API)
  □ Parse and normalize labels/tags
  □ Generate data quality report

Phase 2: Low-Risk Enrichment (Week 1-2)
  □ Import additional email addresses for matched contacts
  □ Import phone numbers for matched contacts
  □ Import birthday data
  □ Import organization data
  □ Append notes (non-destructive)

Phase 3: Address Enrichment (Week 2-3)
  □ Import validated addresses
  □ Run USPS validation on new addresses
  □ Update mailing list eligibility
  □ Generate address quality scores

Phase 4: Tag/Label Migration (Week 3-4)
  □ Map Google labels to database tags
  □ Create new tags where needed
  □ Import label associations
  □ Update segmentation rules

Phase 5: New Contact Import (Week 4-5)
  □ Start with priority labeled contacts (Keepers, Members, Partners)
  □ Validate all data before import
  □ Run final deduplication check
  □ Import with audit trail
  □ Send welcome/re-engagement emails

Phase 6: MailChimp Reconciliation (Week 5)
  □ Parse MailChimp subscription status
  □ Update email_subscribed field
  □ Handle unsubscribes (compliance)
  □ Sync with current email platform

Technical Requirements:
  • Idempotent import script (safe to re-run)
  • Full audit logging (who, what, when)
  • Rollback capability
  • Data validation at each step
  • Incremental processing (batches of 100-500)
  • Error handling and retry logic
  • Dry-run mode for testing
  • Comprehensive test coverage

Data Quality Metrics to Track:
  • Match rate (email-based)
  • Data completeness improvement (before/after)
  • Validation pass rate (addresses, phones)
  • Deduplication effectiveness
  • Import error rate
  • Data enrichment coverage
""")

    print("\n" + "=" * 80)
    print("RISK ANALYSIS")
    print("=" * 80)
    print("""
LOW RISK (proceed with confidence):
  ✓ Additional email addresses
  ✓ Phone numbers (with validation)
  ✓ Birthday data
  ✓ Organization names
  ✓ Notes (append-only)

MEDIUM RISK (needs validation):
  ⚠ Address data (validate before import)
  ⚠ Labels/tags (map carefully)
  ⚠ New contacts (deduplication critical)

HIGH RISK (careful implementation):
  ⚠ MailChimp unsubscribe status (legal compliance)
  ⚠ Overwriting existing data (prefer merge)
  ⚠ Bulk imports without validation

COMPLIANCE CONSIDERATIONS:
  • Respect unsubscribe status (GDPR/CAN-SPAM)
  • Don't re-subscribe previously unsubscribed contacts
  • Maintain audit trail for all changes
  • Allow for data correction/deletion
""")

    cur.close()
    conn.close()

if __name__ == '__main__':
    analyze_google_contacts()
