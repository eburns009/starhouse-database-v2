#!/usr/bin/env python3
"""
Generate a simple mailing list for the team with key donor information.

Includes:
- Contact information with USPS validated addresses
- Current member status (monthly/yearly subscriptions)
- Email subscription status
- Last activity date
- Total amount spent
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

def get_mailing_list(conn):
    """
    Get all contacts with addresses, including USPS validated data.
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = r"""
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.paypal_business_name,

            -- Use USPS validated address if available, otherwise use original
            COALESCE(c.billing_usps_delivery_line_1, c.address_line_1) as address_line_1,
            COALESCE(c.billing_usps_delivery_line_2, c.address_line_2) as address_line_2,

            -- Properly parse USPS last_line using regex to handle multi-word cities
            -- Format is: "CITY ST ZIP" where city can have multiple words
            COALESCE(
                (regexp_match(c.billing_usps_last_line, '^(.*)\s+([A-Z]{2})\s+(\d{5})(-\d{4})?$'))[1],
                c.city
            ) as city,
            COALESCE(
                (regexp_match(c.billing_usps_last_line, '^(.*)\s+([A-Z]{2})\s+(\d{5})(-\d{4})?$'))[2],
                c.state
            ) as state,
            -- Extract only 5-digit zip code (preserves leading zeros as text)
            COALESCE(
                (regexp_match(c.billing_usps_last_line, '^(.*)\s+([A-Z]{2})\s+(\d{5})(-\d{4})?$'))[3],
                SUBSTRING(c.postal_code FROM 1 FOR 5)
            ) as postal_code,
            c.country,

            -- Member status
            c.has_active_subscription,
            c.membership_tier,
            c.membership_level,
            c.membership_group,

            -- Email subscription
            c.email_subscribed,

            -- Financial info
            c.total_spent,
            c.transaction_count,
            c.last_transaction_date,

            -- Activity tracking
            c.created_at,
            c.updated_at,

            -- USPS validation info
            c.billing_usps_validated_at,
            c.billing_usps_precision,
            c.billing_address_verified

        FROM contacts c
        WHERE
            (c.address_line_1 IS NOT NULL AND c.address_line_1 != '')
            OR (c.billing_usps_delivery_line_1 IS NOT NULL)
        ORDER BY
            c.has_active_subscription DESC,
            c.total_spent DESC,
            COALESCE(c.last_name, ''),
            COALESCE(c.first_name, '')
    """

    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    return results


def determine_subscription_type(contact):
    """
    Determine if contact has a monthly or yearly subscription.
    """
    cursor = contact['_cursor']

    cursor.execute("""
        SELECT
            billing_cycle,
            status,
            product_id
        FROM subscriptions
        WHERE contact_id = %s
          AND status IN ('active', 'trial')
        ORDER BY created_at DESC
        LIMIT 1
    """, (contact['id'],))

    sub = cursor.fetchone()

    if sub:
        cycle = sub['billing_cycle'] or ''
        if 'month' in cycle.lower():
            return 'Monthly'
        elif 'year' in cycle.lower():
            return 'Yearly'
        elif sub['status'] == 'active':
            return 'Active'

    return ''


def get_last_activity_date(contact):
    """
    Get the most recent activity date for a contact.
    """
    dates = [
        contact['last_transaction_date'],
        contact['updated_at'],
        contact['created_at']
    ]

    # Filter out None values and get the most recent
    valid_dates = [d for d in dates if d is not None]

    if valid_dates:
        return max(valid_dates)

    return None


def main():
    print("=" * 70)
    print("TEAM MAILING LIST GENERATOR")
    print("=" * 70)
    print()

    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("Fetching contacts with mailing addresses...")
    contacts = get_mailing_list(conn)

    print(f"✓ Found {len(contacts)} contacts with mailing addresses")
    print()

    # Prepare data for CSV export
    mailing_list = []

    print("Processing contact data...")
    for i, contact in enumerate(contacts, 1):
        # Store cursor reference for subscription lookup
        contact['_cursor'] = cursor

        # Determine subscription type
        subscription_type = determine_subscription_type(contact)

        # Get last activity
        last_activity = get_last_activity_date(contact)

        # Format full name
        full_name = f"{contact['first_name'] or ''} {contact['last_name'] or ''}".strip()

        # Format member status
        if contact['has_active_subscription']:
            if contact['membership_tier']:
                member_status = f"{contact['membership_tier']}"
            elif contact['membership_level']:
                member_status = f"{contact['membership_level']}"
            elif contact['membership_group']:
                member_status = f"{contact['membership_group']}"
            else:
                member_status = 'Active Member'
        else:
            member_status = 'Inactive'

        # Format spending
        total_spent = float(contact['total_spent']) if contact['total_spent'] else 0.00

        mailing_list.append({
            'FirstName': contact['first_name'] or '',
            'LastName': contact['last_name'] or '',
            'FullName': full_name,
            'BusinessName': contact['paypal_business_name'] or '',
            'Email': contact['email'] or '',
            'Phone': contact['phone'] or '',
            'AddressLine1': contact['address_line_1'] or '',
            'AddressLine2': contact['address_line_2'] or '',
            'City': contact['city'] or '',
            'State': contact['state'] or '',
            'PostalCode': contact['postal_code'] or '',
            'Country': contact['country'] or 'US',
            'CurrentMember': 'Yes' if contact['has_active_subscription'] else 'No',
            'SubscriptionType': subscription_type,
            'MembershipTier': member_status,
            'EmailSubscriber': 'Yes' if contact['email_subscribed'] else 'No',
            'TotalSpent': f"${total_spent:.2f}",
            'TransactionCount': contact['transaction_count'] or 0,
            'LastActivity': last_activity.strftime('%Y-%m-%d') if last_activity else '',
            'LastTransaction': contact['last_transaction_date'].strftime('%Y-%m-%d') if contact['last_transaction_date'] else '',
            'AddressValidated': 'Yes' if contact['billing_address_verified'] else 'No',
            'ValidationDate': contact['billing_usps_validated_at'].strftime('%Y-%m-%d') if contact['billing_usps_validated_at'] else '',
        })

        if i % 100 == 0:
            print(f"  Processed {i} contacts...")

    # Write to CSV
    output_file = '/workspaces/starhouse-database-v2/team_mailing_list.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'FirstName', 'LastName', 'FullName', 'BusinessName',
            'Email', 'Phone',
            'AddressLine1', 'AddressLine2', 'City', 'State', 'PostalCode', 'Country',
            'CurrentMember', 'SubscriptionType', 'MembershipTier',
            'EmailSubscriber',
            'TotalSpent', 'TransactionCount',
            'LastActivity', 'LastTransaction',
            'AddressValidated', 'ValidationDate'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mailing_list)

    print()
    print("=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"Output file: {output_file}")
    print(f"Total contacts: {len(mailing_list)}")
    print()

    # Statistics
    current_members = sum(1 for c in mailing_list if c['CurrentMember'] == 'Yes')
    monthly_subs = sum(1 for c in mailing_list if c['SubscriptionType'] == 'Monthly')
    yearly_subs = sum(1 for c in mailing_list if c['SubscriptionType'] == 'Yearly')
    email_subscribers = sum(1 for c in mailing_list if c['EmailSubscriber'] == 'Yes')
    validated_addresses = sum(1 for c in mailing_list if c['AddressValidated'] == 'Yes')

    # Address breakdown
    us_count = sum(1 for c in mailing_list if c['Country'].upper() in ['', 'US', 'USA', 'UNITED STATES'])
    intl_count = len(mailing_list) - us_count

    # Spending statistics
    total_spending = sum(float(c['TotalSpent'].replace('$', '').replace(',', '')) for c in mailing_list)
    avg_spending = total_spending / len(mailing_list) if mailing_list else 0

    print("STATISTICS")
    print("-" * 70)
    print(f"Current Members:          {current_members}")
    print(f"  - Monthly subscriptions: {monthly_subs}")
    print(f"  - Yearly subscriptions:  {yearly_subs}")
    print(f"Email Subscribers:        {email_subscribers}")
    print(f"Validated Addresses:      {validated_addresses}")
    print()
    print(f"Address Breakdown:")
    print(f"  US addresses:            {us_count}")
    print(f"  International:           {intl_count}")
    print()
    print(f"Financial Summary:")
    print(f"  Total Spending:          ${total_spending:,.2f}")
    print(f"  Average per Contact:     ${avg_spending:,.2f}")
    print("=" * 70)

    # Show sample
    print()
    print("SAMPLE RECORDS (first 5):")
    print("-" * 70)

    for i, contact in enumerate(mailing_list[:5], 1):
        print(f"\n{i}. {contact['FullName']}")
        if contact['BusinessName']:
            print(f"   Business: {contact['BusinessName']}")
        print(f"   {contact['AddressLine1']}")
        if contact['AddressLine2']:
            print(f"   {contact['AddressLine2']}")
        print(f"   {contact['City']}, {contact['State']} {contact['PostalCode']}")
        print(f"   Email: {contact['Email']}")
        print(f"   Member: {contact['CurrentMember']} ({contact['SubscriptionType']}) | Email Sub: {contact['EmailSubscriber']}")
        print(f"   Spent: {contact['TotalSpent']} ({contact['TransactionCount']} transactions)")
        print(f"   Last Activity: {contact['LastActivity']} | Address Validated: {contact['AddressValidated']}")

    cursor.close()
    conn.close()

    print()
    print("✓ Team mailing list generated successfully!")

if __name__ == '__main__':
    main()
