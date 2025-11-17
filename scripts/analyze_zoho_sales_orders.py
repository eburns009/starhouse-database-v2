#!/usr/bin/env python3
"""
FAANG-Quality Zoho Sales Orders Analysis
Analyzes Zoho CRM export to identify contact enrichment opportunities

This is B2B sales data tracking:
- Organizations (Account Names)
- Contact persons
- Sales orders (events, donations, candle drives)
- Billing addresses

Engineering Principles:
- Comprehensive data profiling
- Database comparison for gaps
- Actionable recommendations
- Detailed metrics and reporting
"""

import csv
import psycopg2
from collections import defaultdict, Counter
from datetime import datetime
from decimal import Decimal
import re
from db_config import get_database_url

DATABASE_URL = get_database_url()

def analyze_zoho_file():
    """Analyze the Zoho Sales Orders CSV file structure and content."""

    print("=" * 80)
    print("ZOHO SALES ORDERS ANALYSIS - FAANG Engineering")
    print("=" * 80)
    print()

    file_path = '/workspaces/starhouse-database-v2/kajabi 3 files review/Zoho/Zoho-Sales-Orders.csv'

    orders = []
    headers = []

    # Read and parse CSV
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        orders = list(reader)

    print(f"📊 FILE OVERVIEW")
    print(f"   Total Orders: {len(orders):,}")
    print(f"   Columns: {len(headers)}")
    print()

    # Analyze key fields
    account_names = Counter()  # Organizations
    contact_names = Counter()  # People
    subjects = Counter()  # Order types
    addresses = []

    total_value = Decimal('0')
    date_range = {'earliest': None, 'latest': None}

    orders_with_contact = 0
    orders_with_account = 0
    orders_with_address = 0
    excluded_test_orders = 0

    for order in orders:
        # Account (Organization)
        account = order.get('Account Name', '').strip()
        if account:
            account_names[account] += 1
            orders_with_account += 1

        # Contact (Person)
        contact = order.get('Contact Name', '').strip()
        if contact:
            contact_names[contact] += 1
            orders_with_contact += 1

        # Order subject/type
        subject = order.get('Subject', '').strip()

        # FILTER OUT TEST ORDERS - FAANG Data Quality
        # Skip test orders and unrealistic amounts
        is_test_order = False
        if subject:
            if 'test' in subject.lower():
                is_test_order = True
                excluded_test_orders += 1

        if subject and not is_test_order:
            subjects[subject] += 1

        # Address data
        billing_addr = {
            'street': order.get('Billing Street', '').strip(),
            'city': order.get('Billing City', '').strip(),
            'state': order.get('Billing State', '').strip(),
            'zip': order.get('Billing Code', '').strip(),
            'account': account,
            'contact': contact
        }

        if billing_addr['street'] or billing_addr['city']:
            addresses.append(billing_addr)
            orders_with_address += 1

        # Financial data
        if not is_test_order:
            try:
                amount = order.get('Grand Total', '') or '0'
                amount = amount.replace('$', '').replace(',', '').strip()
                if amount:
                    amount_decimal = Decimal(amount)
                    # Exclude unrealistic amounts (>$100k likely data errors)
                    if amount_decimal <= 100000:
                        total_value += amount_decimal
                    else:
                        excluded_test_orders += 1
            except:
                pass

        # Date range
        date_str = order.get('Created Time', '')
        if date_str:
            try:
                # Format: 2019-03-12 14:48:20
                order_date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                if not date_range['earliest'] or order_date < date_range['earliest']:
                    date_range['earliest'] = order_date
                if not date_range['latest'] or order_date > date_range['latest']:
                    date_range['latest'] = order_date
            except:
                pass

    # Display analysis results
    print("📈 DATA SUMMARY")
    print(f"   Unique Organizations (Accounts): {len(account_names):,}")
    print(f"   Unique People (Contacts): {len(contact_names):,}")
    print(f"   Orders with Account: {orders_with_account:,} ({orders_with_account/len(orders)*100:.1f}%)")
    print(f"   Orders with Contact Person: {orders_with_contact:,} ({orders_with_contact/len(orders)*100:.1f}%)")
    print(f"   Orders with Address: {orders_with_address:,} ({orders_with_address/len(orders)*100:.1f}%)")
    if excluded_test_orders > 0:
        print(f"   ⚠️  Excluded Test/Invalid Orders: {excluded_test_orders}")
    print(f"   Total Order Value: ${total_value:,.2f}")
    print()

    if date_range['earliest']:
        print(f"📅 DATE RANGE")
        print(f"   Earliest Order: {date_range['earliest'].strftime('%Y-%m-%d')}")
        print(f"   Latest Order: {date_range['latest'].strftime('%Y-%m-%d')}")
        print(f"   Span: {(date_range['latest'] - date_range['earliest']).days:,} days ({(date_range['latest'] - date_range['earliest']).days/365:.1f} years)")
        print()

    print(f"🏢 TOP 15 ORGANIZATIONS (by order count)")
    for i, (account, count) in enumerate(account_names.most_common(15), 1):
        print(f"   {i:2d}. {count:3d} orders | {account[:60]}")
    print()

    print(f"👥 TOP 15 CONTACT PERSONS (by order count)")
    for i, (contact, count) in enumerate(contact_names.most_common(15), 1):
        print(f"   {i:2d}. {count:3d} orders | {contact[:60]}")
    print()

    # Categorize order types
    event_keywords = ['wedding', 'event', 'party', 'reception', 'celebration', 'birthday']
    donation_keywords = ['donation', 'gift', 'contribution', 'fund']
    candle_keywords = ['candle', 'drive']

    events = 0
    donations = 0
    candles = 0
    other = 0

    for subject in subjects:
        subject_lower = subject.lower()
        if any(kw in subject_lower for kw in event_keywords):
            events += subjects[subject]
        elif any(kw in subject_lower for kw in donation_keywords):
            donations += subjects[subject]
        elif any(kw in subject_lower for kw in candle_keywords):
            candles += subjects[subject]
        else:
            other += subjects[subject]

    print(f"📊 ORDER TYPES")
    print(f"   Events/Weddings: {events:,} orders ({events/len(orders)*100:.1f}%)")
    print(f"   Donations/Gifts: {donations:,} orders ({donations/len(orders)*100:.1f}%)")
    print(f"   Candle Drives: {candles:,} orders ({candles/len(orders)*100:.1f}%)")
    print(f"   Other: {other:,} orders ({other/len(orders)*100:.1f}%)")
    print()

    return {
        'orders': orders,
        'headers': headers,
        'account_names': account_names,
        'contact_names': contact_names,
        'addresses': addresses,
        'total_value': total_value,
        'date_range': date_range,
        'subjects': subjects
    }


def compare_with_database(zoho_data):
    """Compare Zoho data with existing database to find gaps."""

    print("=" * 80)
    print("DATABASE COMPARISON")
    print("=" * 80)
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Get existing contacts with business names
    cursor.execute("""
        SELECT
            COALESCE(paypal_business_name, '') as org_name,
            CONCAT_WS(' ', first_name, last_name) as person_name,
            email,
            phone,
            address_line_1,
            city,
            state,
            postal_code,
            source_system,
            id
        FROM contacts
    """)

    db_contacts = []
    db_orgs = {}  # org name -> contact records
    db_persons = {}  # person name -> contact records

    for row in cursor.fetchall():
        contact = {
            'org_name': row[0].strip() if row[0] else '',
            'person_name': row[1].strip() if row[1] else '',
            'email': row[2],
            'phone': row[3],
            'address': row[4],
            'city': row[5],
            'state': row[6],
            'zip': row[7],
            'source': row[8],
            'id': row[9]
        }
        db_contacts.append(contact)

        if contact['org_name']:
            org_key = contact['org_name'].lower()
            if org_key not in db_orgs:
                db_orgs[org_key] = []
            db_orgs[org_key].append(contact)

        if contact['person_name']:
            person_key = contact['person_name'].lower()
            if person_key not in db_persons:
                db_persons[person_key] = []
            db_persons[person_key].append(contact)

    # Get transaction data
    cursor.execute("""
        SELECT
            c.id as contact_id,
            COALESCE(c.paypal_business_name, '') as org_name,
            CONCAT_WS(' ', c.first_name, c.last_name) as person_name,
            COUNT(t.id) as transaction_count,
            SUM(t.amount) as total_spent,
            MAX(t.transaction_date) as last_transaction
        FROM transactions t
        JOIN contacts c ON c.id = t.contact_id
        GROUP BY c.id, org_name, person_name
    """)

    db_transactions = {}  # contact_id -> transaction data
    for row in cursor.fetchall():
        db_transactions[row[0]] = {
            'org_name': row[1],
            'person_name': row[2],
            'count': row[3],
            'total': row[4] or Decimal('0'),
            'last_date': row[5]
        }

    cursor.close()
    conn.close()

    # Analyze matching
    matched_orgs = []
    new_orgs = []
    matched_persons = []
    new_persons = []

    for account_name, count in zoho_data['account_names'].items():
        account_key = account_name.lower()
        if account_key in db_orgs:
            matched_orgs.append((account_name, count, len(db_orgs[account_key])))
        else:
            new_orgs.append((account_name, count))

    for contact_name, count in zoho_data['contact_names'].items():
        contact_key = contact_name.lower()
        if contact_key in db_persons:
            matched_persons.append((contact_name, count, len(db_persons[contact_key])))
        else:
            new_persons.append((contact_name, count))

    # Display results
    print(f"🏢 ORGANIZATION MATCHING")
    print(f"   Zoho Organizations: {len(zoho_data['account_names']):,}")
    print(f"   Already in Database: {len(matched_orgs):,} ({len(matched_orgs)/len(zoho_data['account_names'])*100:.1f}%)")
    print(f"   NEW Organizations: {len(new_orgs):,} ({len(new_orgs)/len(zoho_data['account_names'])*100:.1f}%)")
    print()

    if new_orgs:
        print(f"   Top 15 NEW Organizations (not in database):")
        new_orgs.sort(key=lambda x: x[1], reverse=True)
        for i, (org, count) in enumerate(new_orgs[:15], 1):
            print(f"   {i:2d}. {count:3d} orders | {org[:60]}")
        print()

    print(f"👥 CONTACT PERSON MATCHING")
    print(f"   Zoho Contact Persons: {len(zoho_data['contact_names']):,}")
    print(f"   Already in Database: {len(matched_persons):,} ({len(matched_persons)/len(zoho_data['contact_names']) *100 if zoho_data['contact_names'] else 0:.1f}%)")
    print(f"   NEW Persons: {len(new_persons):,} ({len(new_persons)/len(zoho_data['contact_names'])*100 if zoho_data['contact_names'] else 0:.1f}%)")
    print()

    # Address enrichment opportunities
    addresses_for_enrichment = []
    for addr in zoho_data['addresses']:
        account_key = addr['account'].lower() if addr['account'] else ''

        if account_key and account_key in db_orgs:
            # Found matching org in database
            for db_contact in db_orgs[account_key]:
                if not db_contact['address'] and addr['street']:
                    # DB contact missing address, Zoho has it
                    addresses_for_enrichment.append({
                        'db_contact_id': db_contact['id'],
                        'org_name': addr['account'],
                        'zoho_address': addr,
                        'db_contact': db_contact
                    })

    if addresses_for_enrichment:
        print(f"🏠 ADDRESS ENRICHMENT")
        print(f"   Contacts with missing addresses that Zoho has: {len(addresses_for_enrichment)}")
        print()

    return {
        'matched_orgs': matched_orgs,
        'new_orgs': new_orgs,
        'matched_persons': matched_persons,
        'new_persons': new_persons,
        'addresses_for_enrichment': addresses_for_enrichment,
        'db_orgs': db_orgs,
        'db_persons': db_persons
    }


def generate_recommendations(zoho_data, comparison_data):
    """Generate actionable recommendations."""

    print("=" * 80)
    print("RECOMMENDATIONS - FAANG Action Plan")
    print("=" * 80)
    print()

    recommendations = []

    # Calculate total order value for new organizations
    new_org_value = Decimal('0')
    for org_name, count in comparison_data['new_orgs']:
        for order in zoho_data['orders']:
            if order.get('Account Name', '').strip() == org_name:
                # Exclude test orders
                subject = order.get('Subject', '').strip().lower()
                if 'test' in subject:
                    continue

                try:
                    amount = order.get('Grand Total', '') or '0'
                    amount = amount.replace('$', '').replace(',', '').strip()
                    if amount:
                        amount_decimal = Decimal(amount)
                        # Exclude unrealistic amounts
                        if amount_decimal <= 100000:
                            new_org_value += amount_decimal
                except:
                    pass

    # Recommendation 1: Import new organizations
    if comparison_data['new_orgs']:
        total_new_orders = sum(count for org, count in comparison_data['new_orgs'])
        rec = {
            'priority': 'HIGH',
            'action': 'Import New Organizations from Zoho',
            'impact': f"{len(comparison_data['new_orgs'])} organizations, {total_new_orders} orders, ${new_org_value:,.2f} value",
            'value': 'Expand B2B customer base, track corporate relationships',
            'effort': 'Medium - need to map to contacts schema (business_name field)'
        }
        recommendations.append(rec)

    # Recommendation 2: Enrich addresses
    if comparison_data['addresses_for_enrichment']:
        rec = {
            'priority': 'HIGH',
            'action': 'Enrich Missing Addresses from Zoho',
            'impact': f"{len(comparison_data['addresses_for_enrichment'])} contacts",
            'value': 'Improve mailing list quality for existing customers',
            'effort': 'Low - direct address import + USPS validation'
        }
        recommendations.append(rec)

    # Recommendation 3: Import contact persons
    if comparison_data['new_persons']:
        total_person_orders = sum(count for person, count in comparison_data['new_persons'])
        rec = {
            'priority': 'MEDIUM',
            'action': 'Import Contact Persons from Zoho',
            'impact': f"{len(comparison_data['new_persons'])} people, {total_person_orders} orders",
            'value': 'Build individual relationships within organizations',
            'effort': 'Medium - need to link to organizations'
        }
        recommendations.append(rec)

    # Recommendation 4: Create Zoho sales order tracking
    real_order_count = len(zoho_data['orders']) - (2 if zoho_data['total_value'] < 10000000 else 0)  # Approximate
    rec = {
        'priority': 'MEDIUM',
        'action': 'Import Zoho Sales Orders as Transactions',
        'impact': f"{len(zoho_data['orders']):,} orders worth ${zoho_data['total_value']:,.2f}",
        'value': 'Complete transaction history including B2B/event sales',
        'effort': 'High - need to map order types to products/services'
    }
    recommendations.append(rec)

    # Recommendation 5: Segment by order type
    rec = {
        'priority': 'LOW',
        'action': 'Create Tags for Zoho Order Types',
        'impact': 'Event customers, Candle Drive participants, Donors',
        'value': 'Enable targeted campaigns (wedding venue marketing, fundraising outreach)',
        'effort': 'Low - use existing tag system'
    }
    recommendations.append(rec)

    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['priority']}] {rec['action']}")
        print(f"   Impact: {rec['impact']}")
        print(f"   Value: {rec['value']}")
        print(f"   Effort: {rec['effort']}")
        print()

    return recommendations


def main():
    """Main execution function."""

    # Step 1: Analyze Zoho file
    zoho_data = analyze_zoho_file()

    # Step 2: Compare with database
    comparison_data = compare_with_database(zoho_data)

    # Step 3: Generate recommendations
    recommendations = generate_recommendations(zoho_data, comparison_data)

    # Final summary
    print("=" * 80)
    print("EXECUTIVE SUMMARY")
    print("=" * 80)
    print()
    print(f"📊 Zoho Sales Orders: {len(zoho_data['orders']):,} orders")
    print(f"💰 Total Order Value: ${zoho_data['total_value']:,.2f}")
    print(f"🏢 Organizations: {len(zoho_data['account_names']):,}")
    print(f"👥 Contact Persons: {len(zoho_data['contact_names']):,}")
    print(f"🏠 Addresses: {len(zoho_data['addresses']):,}")
    print()
    print(f"🆕 New Organizations: {len(comparison_data['new_orgs']):,}")
    print(f"🆕 New Persons: {len(comparison_data['new_persons']):,}")
    print(f"💎 Address Enrichment Opportunities: {len(comparison_data['addresses_for_enrichment']):,}")
    print()
    print(f"📝 Actionable Recommendations: {len(recommendations)}")
    print()
    print("=" * 80)
    print("✅ Analysis Complete - Review Recommendations Above")
    print("=" * 80)


if __name__ == '__main__':
    main()
