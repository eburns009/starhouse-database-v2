#!/usr/bin/env python3
"""
FAANG-Quality JotForm Data Analysis for Contact Enrichment
Systematically analyze all JotForm exports to identify enhancement opportunities
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import defaultdict
import re
from db_config import get_database_url

DATABASE_URL = get_database_url()

JOTFORM_FILES = [
    '2022_Donation_.csv',
    '2024_End_of_Year_Donation.csv',
    '30th_Birthday.csv',
    'Donation_Acknowledgement.csv',
    'GivingTuesday.csv',
    'Hosting_an_Event_at_the_StarHouse_.csv',
    'How_did_you_hear_about_the_StarHouse_.csv',
    'StarHouse_Donation.csv',
    'StarHouse_Silent_Auction_Bidding_.csv',
    '_One_Time_Donation_and_or_Subscription_.csv',
]

JOTFORM_DIR = './kajabi 3 files review/Jotform'


def parse_paypal_payer_address(address_field):
    """
    Parse PayPal payer address field into components.
    Example: "Name: stefanie smith Street: 11247 W Radcliffe Drive City: Littleton State/Region: CO Zip/Postal: 80127 Country: United States"
    """
    if not address_field or pd.isna(address_field):
        return {}

    result = {}

    # Extract components using regex
    name_match = re.search(r'Name:\s*([^S][^:]*?)(?=\s*(?:Street|$))', address_field)
    street_match = re.search(r'Street:\s*([^C][^:]*?)(?=\s*(?:City|$))', address_field)
    city_match = re.search(r'City:\s*([^S][^:]*?)(?=\s*(?:State|$))', address_field)
    state_match = re.search(r'State/Region:\s*([^Z][^:]*?)(?=\s*(?:Zip|$))', address_field)
    zip_match = re.search(r'Zip/Postal:\s*([^C][^:]*?)(?=\s*(?:Country|$))', address_field)
    country_match = re.search(r'Country:\s*(.+?)$', address_field)

    if name_match:
        result['name'] = name_match.group(1).strip()
    if street_match:
        result['street'] = street_match.group(1).strip()
    if city_match:
        result['city'] = city_match.group(1).strip()
    if state_match:
        result['state'] = state_match.group(1).strip()
    if zip_match:
        result['zip'] = zip_match.group(1).strip()
    if country_match:
        result['country'] = country_match.group(1).strip()

    return result


def parse_paypal_payer_info(payer_field):
    """
    Parse PayPal payer info field.
    Example: "First Name: Diana Last Name: O. Verschoor Transaction ID: 5RS93720239869415"
    """
    if not payer_field:
        return {}

    result = {}

    first_name_match = re.search(r'First Name:\s*([^L][^:]*?)(?=\s*(?:Last|Transaction|Email|$))', payer_field)
    last_name_match = re.search(r'Last Name:\s*([^T][^:]*?)(?=\s*(?:Transaction|Email|$))', payer_field)
    txn_match = re.search(r'Transaction ID:\s*([A-Z0-9]+)', payer_field)
    email_match = re.search(r'Email:\s*([^\s]+@[^\s]+)', payer_field)

    if first_name_match:
        result['first_name'] = first_name_match.group(1).strip()
    if last_name_match:
        result['last_name'] = last_name_match.group(1).strip()
    if txn_match:
        result['transaction_id'] = txn_match.group(1).strip()
    if email_match:
        result['email'] = email_match.group(1).strip()

    return result


def analyze_file(filepath, filename):
    """Analyze a single JotForm file."""
    print(f"\n{'='*80}")
    print(f"FILE: {filename}")
    print(f"{'='*80}")

    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return None

    file_size = os.path.getsize(filepath)
    print(f"Size: {file_size:,} bytes")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Records: {len(rows)}")

        if not rows:
            print("⚠️  No data rows")
            return None

        # Analyze column structure
        columns = list(rows[0].keys())
        print(f"\nColumns ({len(columns)}):")
        for col in columns:
            print(f"  - {col}")

        # Analyze data richness
        enrichment_opportunities = {
            'emails': set(),
            'phones': set(),
            'addresses': [],
            'donations': [],
            'business_names': set(),
            'websites': set(),
            'tags': set(),
            'engagement_notes': [],
            'transaction_ids': set(),
        }

        for row in rows:
            # Email
            for col in ['Email', 'Your E-mail', 'E-mail']:
                if col in row and row[col]:
                    enrichment_opportunities['emails'].add(row[col].lower().strip())

            # Phone
            for col in ['Phone Number', 'Phone']:
                if col in row and row[col]:
                    enrichment_opportunities['phones'].add(row[col].strip())

            # Business info
            if 'Business Name' in row and row['Business Name']:
                enrichment_opportunities['business_names'].add(row['Business Name'].strip())

            if 'Website' in row and row['Website']:
                enrichment_opportunities['websites'].add(row['Website'].strip())

            # Donation data
            for col in ['Amount (hidden)', 'Donation Amount']:
                if col in row and row[col]:
                    try:
                        amount = float(row[col])
                        enrichment_opportunities['donations'].append({
                            'email': row.get('Email') or row.get('Your E-mail', ''),
                            'amount': amount,
                            'date': row.get('Submission Date') or row.get('Date', ''),
                            'reason': row.get('Reason for Donation') or row.get('Donation Reason', ''),
                            'note': row.get('Note to StarHouse', ''),
                        })
                    except ValueError:
                        pass

            # Parse PayPal payer address for shipping addresses
            for col in row.keys():
                if 'Payer Address' in col and row[col]:
                    addr = parse_paypal_payer_address(row[col])
                    if addr:
                        addr['email'] = row.get('Email') or row.get('Your E-mail', '')
                        addr['source'] = filename
                        enrichment_opportunities['addresses'].append(addr)

            # Parse PayPal transaction IDs
            for col in row.keys():
                if 'Payer Info' in col and row[col]:
                    payer_info = parse_paypal_payer_info(row[col])
                    if 'transaction_id' in payer_info:
                        enrichment_opportunities['transaction_ids'].add(payer_info['transaction_id'])

            # Tags from event types and donation reasons
            for col in ['What best describes your event / offering?', 'Reason for Donation',
                       'Donation Reason', 'Your Relationship with StarHouse']:
                if col in row and row[col]:
                    enrichment_opportunities['tags'].add(row[col].strip())

            # Engagement notes
            for col in ['Event Description / Comments', 'Note to StarHouse',
                       'Why do you see StarHouse as the space for your offering?']:
                if col in row and row[col] and len(row[col]) > 10:
                    enrichment_opportunities['engagement_notes'].append({
                        'email': row.get('Email') or row.get('Your E-mail', ''),
                        'note': row[col].strip()[:200],  # First 200 chars
                    })

        # Print enrichment summary
        print(f"\n📊 ENRICHMENT OPPORTUNITIES:")
        print(f"  ✉️  Unique Emails: {len(enrichment_opportunities['emails'])}")
        print(f"  📞 Phone Numbers: {len(enrichment_opportunities['phones'])}")
        print(f"  🏠 Addresses: {len(enrichment_opportunities['addresses'])}")
        print(f"  💰 Donation Records: {len(enrichment_opportunities['donations'])}")
        print(f"  🏢 Business Names: {len(enrichment_opportunities['business_names'])}")
        print(f"  🌐 Websites: {len(enrichment_opportunities['websites'])}")
        print(f"  🏷️  Tags/Categories: {len(enrichment_opportunities['tags'])}")
        print(f"  📝 Engagement Notes: {len(enrichment_opportunities['engagement_notes'])}")
        print(f"  💳 PayPal Transaction IDs: {len(enrichment_opportunities['transaction_ids'])}")

        if enrichment_opportunities['donations']:
            total_amount = sum(d['amount'] for d in enrichment_opportunities['donations'])
            print(f"  💵 Total Donation Value: ${total_amount:,.2f}")

        return enrichment_opportunities

    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return None


def main():
    print("=" * 80)
    print("JOTFORM DATA ANALYSIS - FAANG-QUALITY CONTACT ENRICHMENT")
    print("=" * 80)

    all_opportunities = {
        'emails': set(),
        'phones': set(),
        'addresses': [],
        'donations': [],
        'business_names': set(),
        'websites': set(),
        'tags': set(),
        'engagement_notes': [],
        'transaction_ids': set(),
    }

    for filename in JOTFORM_FILES:
        filepath = os.path.join(JOTFORM_DIR, filename)
        result = analyze_file(filepath, filename)

        if result:
            # Merge results
            all_opportunities['emails'].update(result['emails'])
            all_opportunities['phones'].update(result['phones'])
            all_opportunities['addresses'].extend(result['addresses'])
            all_opportunities['donations'].extend(result['donations'])
            all_opportunities['business_names'].update(result['business_names'])
            all_opportunities['websites'].update(result['websites'])
            all_opportunities['tags'].update(result['tags'])
            all_opportunities['engagement_notes'].extend(result['engagement_notes'])
            all_opportunities['transaction_ids'].update(result['transaction_ids'])

    # OVERALL SUMMARY
    print(f"\n\n{'='*80}")
    print("OVERALL ENRICHMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Total Unique Emails: {len(all_opportunities['emails'])}")
    print(f"Total Phone Numbers: {len(all_opportunities['phones'])}")
    print(f"Total Addresses: {len(all_opportunities['addresses'])}")
    print(f"Total Donation Records: {len(all_opportunities['donations'])}")
    print(f"Total Business Names: {len(all_opportunities['business_names'])}")
    print(f"Total Websites: {len(all_opportunities['websites'])}")
    print(f"Total Tags: {len(all_opportunities['tags'])}")
    print(f"Total Engagement Notes: {len(all_opportunities['engagement_notes'])}")
    print(f"Total PayPal Transaction IDs: {len(all_opportunities['transaction_ids'])}")

    if all_opportunities['donations']:
        total_donation_value = sum(d['amount'] for d in all_opportunities['donations'])
        print(f"\n💰 TOTAL DONATION VALUE IN JOTFORM DATA: ${total_donation_value:,.2f}")

    # Check database overlap
    print(f"\n{'='*80}")
    print("DATABASE OVERLAP ANALYSIS")
    print(f"{'='*80}")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Check how many emails are already in database
    if all_opportunities['emails']:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM contacts
            WHERE email = ANY(%s)
        """, (list(all_opportunities['emails']),))

        existing_count = cursor.fetchone()['count']
        new_count = len(all_opportunities['emails']) - existing_count

        print(f"Emails already in database: {existing_count}")
        print(f"New emails to add: {new_count}")

    # Check transaction ID overlap
    if all_opportunities['transaction_ids']:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM transactions
            WHERE external_transaction_id = ANY(%s)
        """, (list(all_opportunities['transaction_ids']),))

        existing_txns = cursor.fetchone()['count']
        missing_txns = len(all_opportunities['transaction_ids']) - existing_txns

        print(f"\nPayPal transactions already in database: {existing_txns}")
        print(f"PayPal transactions MISSING from database: {missing_txns}")

        if missing_txns > 0:
            print("⚠️  WARNING: You may be missing donation data!")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("KEY ENRICHMENT OPPORTUNITIES")
    print("=" * 80)

    print("\n1. 🏠 ADDRESS DATA")
    print(f"   - {len(all_opportunities['addresses'])} addresses available from JotForm")
    print("   - Can enrich contacts with validated shipping addresses")
    print("   - Especially valuable for mailing list quality")

    print("\n2. 💰 DONATION INTELLIGENCE")
    print(f"   - {len(all_opportunities['donations'])} donation records with context")
    print("   - Donation reasons/motivations captured")
    print("   - Can build donor personas and engagement strategies")

    print("\n3. 🏢 BUSINESS CONTACTS")
    print(f"   - {len(all_opportunities['business_names'])} business names")
    print(f"   - {len(all_opportunities['websites'])} websites")
    print("   - Can segment B2B vs B2C contacts")
    print("   - Opportunity for event hosting partnerships")

    print("\n4. 🏷️  TAGGING & SEGMENTATION")
    print(f"   - {len(all_opportunities['tags'])} unique tags/categories")
    print("   - Event interests (yoga, sound healing, meditation, etc.)")
    print("   - Relationship types (attendee, donor, event host)")
    print("   - Enables sophisticated campaign targeting")

    print("\n5. 📝 ENGAGEMENT CONTEXT")
    print(f"   - {len(all_opportunities['engagement_notes'])} rich engagement notes")
    print("   - Why people donated")
    print("   - Why they chose StarHouse")
    print("   - Event histories and experiences")

    print("\n6. 📞 CONTACT COMPLETENESS")
    print(f"   - {len(all_opportunities['phones'])} phone numbers")
    print("   - Can fill gaps in contact records")
    print("   - Enable SMS/text outreach campaigns")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    # Import pandas if available for better data parsing
    try:
        import pandas as pd
    except ImportError:
        print("Note: pandas not available, using basic parsing")
        pd = None

    main()
