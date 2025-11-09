#!/usr/bin/env python3
"""
Generate enhanced mailing list with USPS validated addresses only.

This script generates a comprehensive mailing list that includes:
- Only contacts with USPS validated addresses
- Active member status
- Total spending amount
- Email subscription status
- Original created date
- Last activity date
- Complete validated address information
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
from datetime import datetime

# Database connection parameters
DB_PARAMS = {
    'host': '***REMOVED***',
    'port': '6543',
    'database': 'postgres',
    'user': '***REMOVED***',
    'password': os.getenv('DB_PASSWORD')
}

def get_validated_contacts(conn):
    """
    Get all contacts that have USPS validated addresses.
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
            c.email_subscribed,

            -- Address information (use USPS validated delivery lines)
            COALESCE(c.billing_usps_delivery_line_1, c.address_line_1) as address_line_1,
            COALESCE(c.billing_usps_delivery_line_2, c.address_line_2) as address_line_2,
            c.city,
            c.state,
            c.postal_code,
            c.billing_usps_last_line,
            COALESCE(c.country, 'US') as country,

            -- Business information
            c.paypal_business_name,

            -- Financial information
            c.total_spent,
            c.transaction_count,

            -- Membership information
            c.has_active_subscription,
            c.membership_tier,
            c.membership_level,
            c.membership_group,

            -- Date information
            c.created_at,
            c.updated_at,
            c.last_transaction_date,

            -- USPS validation metadata
            c.billing_usps_validated_at,
            c.billing_usps_dpv_match_code,
            c.billing_usps_precision,
            c.billing_usps_county,
            c.billing_usps_rdi,
            c.billing_usps_active,
            c.billing_address_verified

        FROM contacts c
        WHERE
            -- Only include contacts with USPS validated addresses
            c.billing_usps_validated_at IS NOT NULL
            AND c.billing_address_verified = true
            AND c.billing_usps_dpv_match_code = 'Y'
        ORDER BY
            COALESCE(c.last_name, ''),
            COALESCE(c.first_name, '')
    """

    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    return results


def determine_active_member_status(contact):
    """
    Determine if contact is an active member and return status.
    """
    if contact['has_active_subscription']:
        # Active member - include tier/level if available
        if contact['membership_tier']:
            return 'Yes', contact['membership_tier']
        elif contact['membership_level']:
            return 'Yes', contact['membership_level']
        elif contact['membership_group']:
            return 'Yes', contact['membership_group']
        else:
            return 'Yes', 'Member'
    else:
        return 'No', ''


def calculate_last_activity_date(contact):
    """
    Calculate the most recent activity date from available timestamps.
    """
    dates = []

    if contact['last_transaction_date']:
        dates.append(contact['last_transaction_date'])
    if contact['updated_at']:
        dates.append(contact['updated_at'])

    if dates:
        return max(dates)

    # Fallback to created_at if no other activity
    return contact['created_at']


def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)

    print("Fetching contacts with USPS validated addresses...")
    contacts = get_validated_contacts(conn)

    conn.close()

    print(f"\nFound {len(contacts)} contacts with USPS validated addresses")

    # Prepare data for CSV export
    mailing_list = []

    for contact in contacts:
        # Determine active member status
        is_active_member, membership_info = determine_active_member_status(contact)

        # Calculate last activity date
        last_activity = calculate_last_activity_date(contact)

        # Format total amount
        total_amount = float(contact['total_spent']) if contact['total_spent'] else 0.00

        # Email subscriber status
        email_subscriber = 'Yes' if contact['email_subscribed'] else 'No'

        # Format full name
        full_name = f"{contact['first_name'] or ''} {contact['last_name'] or ''}".strip()

        # Format postal code based on country
        country = contact['country'] or 'US'

        # Try to extract ZIP from USPS validated data first, then fall back to postal_code
        postal_code = ''
        usps_last_line = contact.get('billing_usps_last_line', '')
        original_postal = contact.get('postal_code', '')

        if usps_last_line:
            # Extract ZIP from USPS last_line (format: "City Name ST 12345-6789")
            # The ZIP is the last part after the last space
            parts = usps_last_line.strip().split()
            if parts:
                postal_code = parts[-1].split('-')[0]  # Get just the 5-digit part

        if not postal_code and original_postal:
            # Fall back to original postal code
            postal_code = original_postal.split('-')[0]

        if postal_code:
            # For US addresses, ensure 5-digit format with leading zeros
            if country.upper() in ['US', 'USA', 'UNITED STATES', '']:
                postal_code = postal_code.replace(' ', '')
                if postal_code.isdigit():
                    postal_code = postal_code.zfill(5)
            else:
                # For international addresses, just remove spaces but keep format
                postal_code = postal_code.replace(' ', '')

        mailing_list.append({
            'FirstName': contact['first_name'] or '',
            'LastName': contact['last_name'] or '',
            'FullName': full_name,
            'BusinessName': contact['paypal_business_name'] or '',
            'Email': contact['email'] or '',
            'Phone': contact['phone'] or '',

            # Address (USPS validated)
            'AddressLine1': contact['address_line_1'] or '',
            'AddressLine2': contact['address_line_2'] or '',
            'City': contact['city'] or '',
            'State': contact['state'] or '',
            'PostalCode': postal_code,
            'Country': contact['country'] or '',

            # Requested columns
            'ActiveMember': is_active_member,
            'MembershipInfo': membership_info,
            'TotalAmount': f"${total_amount:.2f}",
            'EmailSubscriber': email_subscriber,
            'OriginalCreatedDate': str(contact['created_at'].date()) if contact['created_at'] else '',
            'LastActivityDate': str(last_activity.date()) if last_activity else '',

            # Additional useful information
            'TransactionCount': contact['transaction_count'] or 0,

            # USPS validation metadata
            'USPSValidatedDate': str(contact['billing_usps_validated_at'].date()) if contact['billing_usps_validated_at'] else '',
            'USPSPrecision': contact['billing_usps_precision'] or '',
            'USPSCounty': contact['billing_usps_county'] or '',
            'USPSRDI': contact['billing_usps_rdi'] or '',
        })

    # Write to CSV
    output_file = '/workspaces/starhouse-database-v2/validated_mailing_list.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'FirstName', 'LastName', 'FullName', 'BusinessName',
            'Email', 'Phone',
            'AddressLine1', 'AddressLine2', 'City', 'State', 'PostalCode', 'Country',
            'ActiveMember', 'MembershipInfo', 'TotalAmount', 'EmailSubscriber',
            'OriginalCreatedDate', 'LastActivityDate', 'TransactionCount',
            'USPSValidatedDate', 'USPSPrecision', 'USPSCounty', 'USPSRDI'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mailing_list)

    print(f"\nValidated mailing list exported to: {output_file}")
    print(f"Total contacts: {len(mailing_list)}")

    # Statistics
    us_count = sum(1 for c in mailing_list if c['Country'].upper() in ['', 'US', 'USA', 'UNITED STATES'])
    intl_count = len(mailing_list) - us_count

    # Active member breakdown
    active_members = sum(1 for c in mailing_list if c['ActiveMember'] == 'Yes')
    inactive_members = len(mailing_list) - active_members

    # Email subscriber breakdown
    email_subscribers = sum(1 for c in mailing_list if c['EmailSubscriber'] == 'Yes')
    non_subscribers = len(mailing_list) - email_subscribers

    # Spending statistics
    total_spending = sum(float(c['TotalAmount'].replace('$', '').replace(',', '')) for c in mailing_list)
    avg_spending = total_spending / len(mailing_list) if mailing_list else 0

    print(f"\n{'='*80}")
    print("STATISTICS")
    print('='*80)

    print(f"\nAddress Breakdown:")
    print(f"  US addresses:      {us_count}")
    print(f"  International:     {intl_count}")

    print(f"\nMembership Status:")
    print(f"  Active Members:    {active_members} ({active_members/len(mailing_list)*100:.1f}%)")
    print(f"  Inactive Members:  {inactive_members} ({inactive_members/len(mailing_list)*100:.1f}%)")

    print(f"\nEmail Subscription:")
    print(f"  Subscribed:        {email_subscribers} ({email_subscribers/len(mailing_list)*100:.1f}%)")
    print(f"  Not Subscribed:    {non_subscribers} ({non_subscribers/len(mailing_list)*100:.1f}%)")

    print(f"\nFinancial Summary:")
    print(f"  Total Spending:    ${total_spending:,.2f}")
    print(f"  Average per Contact: ${avg_spending:,.2f}")

    # Show sample
    print(f"\n{'='*80}")
    print("SAMPLE CONTACTS (first 5):")
    print('='*80)

    for i, contact in enumerate(mailing_list[:5], 1):
        print(f"\n{i}. {contact['FullName']}")
        if contact['BusinessName']:
            print(f"   Business: {contact['BusinessName']}")
        print(f"   Email: {contact['Email']} (Subscriber: {contact['EmailSubscriber']})")
        print(f"   {contact['AddressLine1']}")
        if contact['AddressLine2']:
            print(f"   {contact['AddressLine2']}")
        print(f"   {contact['City']}, {contact['State']} {contact['PostalCode']}")
        if contact['USPSCounty']:
            print(f"   County: {contact['USPSCounty']}")
        print(f"   Active Member: {contact['ActiveMember']} {contact['MembershipInfo']}")
        print(f"   Total Spent: {contact['TotalAmount']} | Transactions: {contact['TransactionCount']}")
        print(f"   Created: {contact['OriginalCreatedDate']} | Last Activity: {contact['LastActivityDate']}")
        print(f"   USPS Validated: {contact['USPSValidatedDate']} (Precision: {contact['USPSPrecision']})")

    print(f"\n{'='*80}")
    print("✓ Validated mailing list generation complete!")
    print('='*80)


if __name__ == '__main__':
    main()
