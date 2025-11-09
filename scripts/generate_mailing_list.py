#!/usr/bin/env python3
"""
Generate a mailing list from contacts with valid addresses.
Produces a CSV file ready for mail merge or mailing labels.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import csv

# Database connection parameters
DB_PARAMS = {
    'host': '***REMOVED***',
    'port': '6543',
    'database': 'postgres',
    'user': '***REMOVED***',
    'password': '***REMOVED***'
}

def get_contacts_with_addresses(conn):
    """
    Get all contacts that have either billing or shipping addresses.
    Returns contacts sorted by last name, first name.
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.address_line_1 as billing_address_line_1,
            c.address_line_2 as billing_address_line_2,
            c.city as billing_city,
            c.state as billing_state,
            c.postal_code as billing_postal_code,
            c.country as billing_country,
            c.shipping_address_line_1,
            c.shipping_address_line_2,
            c.shipping_city,
            c.shipping_state,
            c.shipping_postal_code,
            c.shipping_country,
            c.paypal_business_name,
            c.total_spent,
            c.last_transaction_date,
            c.has_active_subscription,
            c.membership_tier,
            c.membership_level,
            c.membership_group,
            c.transaction_count,
            c.created_at,
            c.updated_at
        FROM contacts c
        WHERE
            (c.address_line_1 IS NOT NULL AND c.address_line_1 != '')
            OR (c.shipping_address_line_1 IS NOT NULL AND c.shipping_address_line_1 != '')
        ORDER BY
            COALESCE(c.last_name, ''),
            COALESCE(c.first_name, '')
    """

    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    return results


def format_name(first_name, last_name, business_name):
    """Format the full name for mailing."""
    if business_name:
        # If there's a business name, use it
        if first_name or last_name:
            # Add personal name if available
            personal = f"{first_name or ''} {last_name or ''}".strip()
            if personal:
                return f"{business_name}\nAttn: {personal}"
        return business_name
    else:
        # Just use personal name
        return f"{first_name or ''} {last_name or ''}".strip()


def format_address(addr_line1, addr_line2, city, state, postal, country):
    """Format a complete mailing address."""
    if not addr_line1:
        return None

    lines = []
    lines.append(addr_line1)

    if addr_line2:
        lines.append(addr_line2)

    # City, State ZIP
    city_state_zip = []
    if city:
        city_state_zip.append(city)
    if state:
        city_state_zip.append(state)
    if postal:
        city_state_zip.append(postal)

    if city_state_zip:
        lines.append(' '.join(city_state_zip))

    # Only add country if it's not US
    if country and country.upper() not in ['US', 'USA', 'UNITED STATES']:
        lines.append(country)

    return '\n'.join(lines)


def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)

    print("Fetching contacts with mailing addresses...")
    contacts = get_contacts_with_addresses(conn)

    conn.close()

    print(f"\nFound {len(contacts)} contacts with mailing addresses")

    # Prepare data for CSV export
    mailing_list = []

    for contact in contacts:
        # Determine which address to use (prefer shipping if available, otherwise billing)
        use_shipping = bool(contact['shipping_address_line_1'])

        if use_shipping:
            address_line1 = contact['shipping_address_line_1']
            address_line2 = contact['shipping_address_line_2']
            city = contact['shipping_city']
            state = contact['shipping_state']
            postal = contact['shipping_postal_code']
            country = contact['shipping_country']
        else:
            address_line1 = contact['billing_address_line_1']
            address_line2 = contact['billing_address_line_2']
            city = contact['billing_city']
            state = contact['billing_state']
            postal = contact['billing_postal_code']
            country = contact['billing_country']

        # Format full name
        full_name = f"{contact['first_name'] or ''} {contact['last_name'] or ''}".strip()

        # Determine member status
        member_status = 'Inactive'
        if contact['has_active_subscription']:
            if contact['membership_tier']:
                member_status = f"Active - {contact['membership_tier']}"
            elif contact['membership_level']:
                member_status = f"Active - {contact['membership_level']}"
            elif contact['membership_group']:
                member_status = f"Active - {contact['membership_group']}"
            else:
                member_status = 'Active Member'
        elif contact['total_spent'] and contact['total_spent'] > 0:
            member_status = 'Past Customer'
        else:
            member_status = 'Contact Only'

        # Determine last activity date
        last_activity = None
        if contact['last_transaction_date'] and contact['updated_at']:
            # Use the most recent of the two
            last_activity = max(contact['last_transaction_date'], contact['updated_at'])
        elif contact['last_transaction_date']:
            last_activity = contact['last_transaction_date']
        elif contact['updated_at']:
            last_activity = contact['updated_at']
        else:
            last_activity = contact['created_at']

        # Format spending amount
        spending_amount = float(contact['total_spent']) if contact['total_spent'] else 0.00

        mailing_list.append({
            'FirstName': contact['first_name'] or '',
            'LastName': contact['last_name'] or '',
            'FullName': full_name,
            'BusinessName': contact['paypal_business_name'] or '',
            'AddressLine1': address_line1 or '',
            'AddressLine2': address_line2 or '',
            'City': city or '',
            'State': state or '',
            'PostalCode': postal or '',
            'Country': country or '',
            'Email': contact['email'] or '',
            'Phone': contact['phone'] or '',
            'SpendingAmount': f"${spending_amount:.2f}",
            'TransactionCount': contact['transaction_count'] or 0,
            'MemberStatus': member_status,
            'LastActivity': str(last_activity.date()) if last_activity else '',
            'LastTransactionDate': str(contact['last_transaction_date'].date()) if contact['last_transaction_date'] else ''
        })

    # Write to CSV
    output_file = '/workspaces/starhouse-database-v2/mailing_list.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'FirstName', 'LastName', 'FullName', 'BusinessName',
            'AddressLine1', 'AddressLine2', 'City', 'State', 'PostalCode', 'Country',
            'Email', 'Phone',
            'SpendingAmount', 'TransactionCount', 'MemberStatus', 'LastActivity', 'LastTransactionDate'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mailing_list)

    print(f"\nMailing list exported to: {output_file}")
    print(f"Total contacts: {len(mailing_list)}")

    # Statistics
    us_count = sum(1 for c in mailing_list if c['Country'].upper() in ['', 'US', 'USA', 'UNITED STATES'])
    intl_count = len(mailing_list) - us_count

    # Member status breakdown
    active_members = sum(1 for c in mailing_list if 'Active' in c['MemberStatus'])
    past_customers = sum(1 for c in mailing_list if c['MemberStatus'] == 'Past Customer')
    contact_only = sum(1 for c in mailing_list if c['MemberStatus'] == 'Contact Only')

    # Spending statistics
    total_spending = sum(float(c['SpendingAmount'].replace('$', '').replace(',', '')) for c in mailing_list)
    avg_spending = total_spending / len(mailing_list) if mailing_list else 0

    print(f"\nAddress Breakdown:")
    print(f"  US addresses: {us_count}")
    print(f"  International: {intl_count}")

    print(f"\nMember Status Breakdown:")
    print(f"  Active Members: {active_members}")
    print(f"  Past Customers: {past_customers}")
    print(f"  Contact Only: {contact_only}")

    print(f"\nSpending Statistics:")
    print(f"  Total Spending: ${total_spending:,.2f}")
    print(f"  Average per Contact: ${avg_spending:,.2f}")

    # Show sample
    print(f"\n{'='*80}")
    print("SAMPLE CONTACTS (first 10):")
    print('='*80)

    for i, contact in enumerate(mailing_list[:10], 1):
        print(f"\n{i}. {contact['FullName']}")
        if contact['BusinessName']:
            print(f"   Business: {contact['BusinessName']}")
        print(f"   {contact['AddressLine1']}")
        if contact['AddressLine2']:
            print(f"   {contact['AddressLine2']}")
        print(f"   {contact['City']}, {contact['State']} {contact['PostalCode']}")
        if contact['Country'] and contact['Country'].upper() not in ['US', 'USA', 'UNITED STATES']:
            print(f"   {contact['Country']}")
        print(f"   Status: {contact['MemberStatus']} | Spent: {contact['SpendingAmount']} | Last Activity: {contact['LastActivity']}")


if __name__ == '__main__':
    main()
