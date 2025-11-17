#!/usr/bin/env python3
"""
Analyze Debbie's Google Contacts CSV for enrichment opportunities
FAANG-Grade Analysis: Comprehensive data quality assessment

This script analyzes the Google Contacts export to identify:
1. Total contacts and field completeness
2. Match rate with existing database contacts
3. Enrichment opportunities (phones, addresses, organizations, labels)
4. Data quality issues and recommendations
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import Counter
import re

# Configuration
CSV_PATH = '/workspaces/starhouse-database-v2/kajabi 3 files review/debbie_google_contacts.csv'

def normalize_email(email):
    """Normalize email for matching"""
    if not email:
        return None
    return email.strip().lower()

def normalize_phone(phone):
    """Extract digits from phone for comparison"""
    if not phone:
        return None
    digits = re.sub(r'[^\d]', '', str(phone))
    if len(digits) >= 10:
        return digits[-10:]  # Last 10 digits
    return None

def analyze_google_contacts():
    """Main analysis function"""

    print("=" * 80)
    print("DEBBIE'S GOOGLE CONTACTS - ENRICHMENT ANALYSIS")
    print("=" * 80)
    print()

    # Load CSV
    print("📊 Loading Google Contacts CSV...")
    contacts = []

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(row)

    print(f"   Total contacts in CSV: {len(contacts):,}\n")

    # Field analysis
    print("📋 FIELD COMPLETENESS")
    print("-" * 80)

    stats = {
        'has_email': 0,
        'has_phone': 0,
        'has_address': 0,
        'has_organization': 0,
        'has_labels': 0,
        'has_notes': 0,
        'has_name': 0
    }

    for contact in contacts:
        # Email
        if contact.get('E-mail 1 - Value'):
            stats['has_email'] += 1

        # Phone
        if contact.get('Phone 1 - Value'):
            stats['has_phone'] += 1

        # Address
        if contact.get('Address 1 - Street') or contact.get('Address 1 - Formatted'):
            stats['has_address'] += 1

        # Organization
        if contact.get('Organization Name'):
            stats['has_organization'] += 1

        # Labels
        if contact.get('Labels'):
            stats['has_labels'] += 1

        # Notes
        if contact.get('Notes'):
            stats['has_notes'] += 1

        # Name
        if contact.get('First Name') or contact.get('Last Name'):
            stats['has_name'] += 1

    total = len(contacts)
    print(f"Emails:        {stats['has_email']:,} ({stats['has_email']/total*100:.1f}%)")
    print(f"Phones:        {stats['has_phone']:,} ({stats['has_phone']/total*100:.1f}%)")
    print(f"Addresses:     {stats['has_address']:,} ({stats['has_address']/total*100:.1f}%)")
    print(f"Organizations: {stats['has_organization']:,} ({stats['has_organization']/total*100:.1f}%)")
    print(f"Labels/Tags:   {stats['has_labels']:,} ({stats['has_labels']/total*100:.1f}%)")
    print(f"Notes:         {stats['has_notes']:,} ({stats['has_notes']/total*100:.1f}%)")
    print(f"Names:         {stats['has_name']:,} ({stats['has_name']/total*100:.1f}%)")
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.lnagadkqejnopgfxwlkb',
        password='gqelzN6LRew4Cy9H',
        host='aws-1-us-east-2.pooler.supabase.com',
        port='5432'
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get all existing contacts
    cur.execute("""
        SELECT id, email, paypal_email, phone, paypal_business_name,
               address_line_1, city, state, postal_code,
               phone_source, billing_address_source
        FROM contacts
    """)
    db_contacts = cur.fetchall()
    print(f"   Database contacts: {len(db_contacts):,}\n")

    # Build email lookup
    email_lookup = {}
    for db_contact in db_contacts:
        if db_contact['email']:
            email_lookup[normalize_email(db_contact['email'])] = db_contact
        if db_contact['paypal_email']:
            email_lookup[normalize_email(db_contact['paypal_email'])] = db_contact

    # Match analysis
    print("🔍 MATCHING ANALYSIS")
    print("-" * 80)

    matches = {
        'total_matched': 0,
        'with_phone': 0,
        'with_organization': 0,
        'with_address': 0,
        'with_labels': 0
    }

    enrichment_opportunities = {
        'phones': [],
        'organizations': [],
        'addresses': [],
        'labels': []
    }

    unmatched_contacts = []

    for gc_contact in contacts:
        gc_email = normalize_email(gc_contact.get('E-mail 1 - Value'))

        if not gc_email:
            continue

        db_contact = email_lookup.get(gc_email)

        if db_contact:
            matches['total_matched'] += 1

            # Check for enrichment opportunities
            gc_phone = gc_contact.get('Phone 1 - Value')
            if gc_phone and not db_contact['phone']:
                matches['with_phone'] += 1
                enrichment_opportunities['phones'].append({
                    'email': gc_email,
                    'phone': gc_phone,
                    'label': gc_contact.get('Phone 1 - Label', 'Mobile')
                })

            gc_org = gc_contact.get('Organization Name')
            if gc_org and not db_contact['paypal_business_name']:
                matches['with_organization'] += 1
                enrichment_opportunities['organizations'].append({
                    'email': gc_email,
                    'organization': gc_org
                })

            gc_address = gc_contact.get('Address 1 - Street') or gc_contact.get('Address 1 - Formatted')
            if gc_address and not db_contact['address_line_1']:
                matches['with_address'] += 1
                enrichment_opportunities['addresses'].append({
                    'email': gc_email,
                    'street': gc_contact.get('Address 1 - Street'),
                    'city': gc_contact.get('Address 1 - City'),
                    'state': gc_contact.get('Address 1 - Region'),
                    'postal_code': gc_contact.get('Address 1 - Postal Code')
                })

            gc_labels = gc_contact.get('Labels')
            if gc_labels:
                matches['with_labels'] += 1
                enrichment_opportunities['labels'].append({
                    'email': gc_email,
                    'labels': gc_labels
                })
        else:
            # New contact not in database
            if gc_email:
                unmatched_contacts.append({
                    'email': gc_email,
                    'first_name': gc_contact.get('First Name'),
                    'last_name': gc_contact.get('Last Name'),
                    'phone': gc_contact.get('Phone 1 - Value'),
                    'organization': gc_contact.get('Organization Name')
                })

    match_rate = matches['total_matched'] / stats['has_email'] * 100 if stats['has_email'] > 0 else 0

    print(f"Matched contacts: {matches['total_matched']:,} ({match_rate:.1f}% of contacts with email)")
    print(f"Unmatched (new):  {len(unmatched_contacts):,}")
    print()

    # Enrichment opportunities
    print("✨ ENRICHMENT OPPORTUNITIES")
    print("-" * 80)
    print(f"Phones to add:        {len(enrichment_opportunities['phones']):,}")
    print(f"Organizations to add: {len(enrichment_opportunities['organizations']):,}")
    print(f"Addresses to add:     {len(enrichment_opportunities['addresses']):,}")
    print(f"Contacts with labels: {len(enrichment_opportunities['labels']):,}")
    print()

    # Label analysis
    print("🏷️  LABEL ANALYSIS")
    print("-" * 80)

    all_labels = []
    for contact in contacts:
        labels_str = contact.get('Labels', '')
        if labels_str:
            # Split by ::: and clean
            labels = [l.strip() for l in labels_str.split(':::') if l.strip()]
            all_labels.extend(labels)

    label_counts = Counter(all_labels)
    print(f"Total unique labels: {len(label_counts):,}")
    print(f"\nTop 20 labels:")
    for label, count in label_counts.most_common(20):
        print(f"  {label:<50} {count:>5} contacts")
    print()

    # Sample enrichments
    print("📝 SAMPLE ENRICHMENT DATA")
    print("-" * 80)

    if enrichment_opportunities['phones']:
        print("\nSample phones to add (first 5):")
        for i, opp in enumerate(enrichment_opportunities['phones'][:5], 1):
            print(f"  {i}. {opp['email']}: {opp['phone']} ({opp['label']})")

    if enrichment_opportunities['organizations']:
        print("\nSample organizations to add (first 5):")
        for i, opp in enumerate(enrichment_opportunities['organizations'][:5], 1):
            print(f"  {i}. {opp['email']}: {opp['organization']}")

    if enrichment_opportunities['addresses']:
        print("\nSample addresses to add (first 5):")
        for i, opp in enumerate(enrichment_opportunities['addresses'][:5], 1):
            city_state = f"{opp.get('city', '')}, {opp.get('state', '')}".strip(', ')
            print(f"  {i}. {opp['email']}: {opp.get('street', 'N/A')} - {city_state}")

    if unmatched_contacts:
        print(f"\nSample new contacts (first 5 of {len(unmatched_contacts):,}):")
        for i, contact in enumerate(unmatched_contacts[:5], 1):
            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            print(f"  {i}. {name} ({contact['email']})")

    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total contacts in Google:     {len(contacts):,}")
    print(f"Matched in database:          {matches['total_matched']:,} ({match_rate:.1f}%)")
    print(f"New contacts (not in DB):     {len(unmatched_contacts):,}")
    print()
    print("ENRICHMENT POTENTIAL:")
    print(f"  Phones:        {len(enrichment_opportunities['phones']):,} contacts")
    print(f"  Organizations: {len(enrichment_opportunities['organizations']):,} contacts")
    print(f"  Addresses:     {len(enrichment_opportunities['addresses']):,} contacts")
    print(f"  Labels/Tags:   {len(enrichment_opportunities['labels']):,} contacts")
    print()
    total_enrichments = (
        len(enrichment_opportunities['phones']) +
        len(enrichment_opportunities['organizations']) +
        len(enrichment_opportunities['addresses'])
    )
    print(f"TOTAL DATA POINTS TO ADD: ~{total_enrichments:,}")
    print("=" * 80)

    # Cleanup
    cur.close()
    conn.close()

if __name__ == '__main__':
    analyze_google_contacts()
