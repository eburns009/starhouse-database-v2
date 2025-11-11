#!/usr/bin/env python3
"""
Research where a specific contact opted in across all data sources.
"""

import csv
import os
import psycopg2
from datetime import datetime

def get_db_connection():
    """Get database connection from environment variable."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)

def research_contact(email_to_find):
    """Research a contact's opt-in history across all sources."""

    email_lower = email_to_find.lower()

    print("="*80)
    print(f"OPT-IN RESEARCH FOR: {email_to_find}")
    print("="*80)
    print()

    # Check Kajabi subscribed list
    print("-"*80)
    print("KAJABI SUBSCRIBED LIST (as of 10/11)")
    print("-"*80)
    found_in_kajabi_subscribed = False
    with open("kajabi 3 files review/1011_email_subscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Email', '').strip().lower() == email_lower:
                found_in_kajabi_subscribed = True
                print(f"✓ FOUND in Kajabi subscribed list")
                print(f"  Name: {row.get('Name', '')}")
                print(f"  First Name: {row.get('First Name', '')}")
                print(f"  Last Name: {row.get('Last Name', '')}")
                print(f"  Created At: {row.get('Created At', '')}")
                print(f"  Member Created At: {row.get('Member Created At', '')}")
                break

    if not found_in_kajabi_subscribed:
        print("✗ NOT in Kajabi subscribed list")
    print()

    # Check Kajabi unsubscribed list
    print("-"*80)
    print("KAJABI UNSUBSCRIBED LIST (as of 11/10/2025)")
    print("-"*80)
    found_in_kajabi_unsubscribed = False
    with open("kajabi 3 files review/11102025unsubscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Email', '').strip().lower() == email_lower:
                found_in_kajabi_unsubscribed = True
                print(f"✓ FOUND in Kajabi unsubscribed list")
                print(f"  Name: {row.get('Name', '')}")
                print(f"  First Name: {row.get('First Name', '')}")
                print(f"  Last Name: {row.get('Last Name', '')}")
                print(f"  Created At: {row.get('Created At', '')}")
                break

    if not found_in_kajabi_unsubscribed:
        print("✗ NOT in Kajabi unsubscribed list")
    print()

    # Check Ticket Tailor
    print("-"*80)
    print("TICKET TAILOR DATA")
    print("-"*80)
    ticket_tailor_records = []
    with open("kajabi 3 files review/ticket_tailor_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Email', '').strip().lower() == email_lower:
                ticket_tailor_records.append(row)

    if ticket_tailor_records:
        print(f"✓ FOUND {len(ticket_tailor_records)} order(s) in Ticket Tailor")
        print()
        for i, record in enumerate(ticket_tailor_records, 1):
            print(f"Order #{i}:")
            print(f"  Order ID: {record.get('Order ID', '')}")
            print(f"  Order Date: {record.get('Order date', '')}")
            print(f"  Event Name: {record.get('Event name', '')}")
            print(f"  Event Start: {record.get('Event start', '')}")
            print(f"  Name: {record.get('Name', '')}")
            print(f"  First Name: {record.get('First Name', '')}")
            print(f"  Last Name: {record.get('Last Name', '')}")
            print(f"  Email Consent: {record.get('Are you open to receive emails from StarHouse?', '')}")
            print(f"  Total Paid: {record.get('Total paid', '')}")
            print(f"  Tickets Purchased: {record.get('Tickets purchased', '')}")
            print()
    else:
        print("✗ NOT in Ticket Tailor data")
        print()

    # Check Database
    print("-"*80)
    print("DATABASE STATUS")
    print("-"*80)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    email,
                    first_name,
                    last_name,
                    phone,
                    email_subscribed,
                    created_at,
                    updated_at,
                    kajabi_id,
                    zoho_id,
                    paypal_email
                FROM contacts
                WHERE LOWER(email) = %s
            """, (email_lower,))

            result = cur.fetchone()
            if result:
                print("✓ FOUND in database")
                print(f"  ID: {result[0]}")
                print(f"  Email: {result[1]}")
                print(f"  First Name: {result[2]}")
                print(f"  Last Name: {result[3]}")
                print(f"  Phone: {result[4]}")
                print(f"  Email Subscribed: {result[5]}")
                print(f"  Created At: {result[6]}")
                print(f"  Updated At: {result[7]}")
                print(f"  Kajabi ID: {result[8]}")
                print(f"  Zoho ID: {result[9]}")
                print(f"  PayPal Email: {result[10]}")
            else:
                print("✗ NOT in database")
        conn.close()
    except Exception as e:
        print(f"✗ Error checking database: {e}")
    print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    if found_in_kajabi_subscribed:
        print("✓ In Kajabi subscribed list - already receiving emails via Kajabi")

    if found_in_kajabi_unsubscribed:
        print("⚠️  In Kajabi unsubscribed list - has previously unsubscribed")

    if ticket_tailor_records:
        consents = [r.get('Are you open to receive emails from StarHouse?', '').strip()
                   for r in ticket_tailor_records]
        yes_count = sum(1 for c in consents if c.lower() == 'yes')
        no_count = sum(1 for c in consents if c.lower() == 'no')
        blank_count = sum(1 for c in consents if not c)

        print(f"✓ Has {len(ticket_tailor_records)} Ticket Tailor order(s):")
        if yes_count:
            print(f"  - {yes_count} order(s) with 'Yes' to email consent")
        if no_count:
            print(f"  - {no_count} order(s) with 'No' to email consent")
        if blank_count:
            print(f"  - {blank_count} order(s) with blank/no response")

    print()

    # Import recommendation
    print("-"*80)
    print("IMPORT RECOMMENDATION")
    print("-"*80)

    if found_in_kajabi_subscribed:
        print("✗ Do NOT import - already in Kajabi subscribed list")
    elif found_in_kajabi_unsubscribed:
        print("✗ Do NOT import - has previously unsubscribed (must respect preference)")
    elif ticket_tailor_records and any(r.get('Are you open to receive emails from StarHouse?', '').strip().lower() == 'yes'
                                       for r in ticket_tailor_records):
        print("✓ SAFE TO IMPORT - said 'Yes' in Ticket Tailor and not in Kajabi")
    else:
        print("✗ Do NOT import - no clear opt-in consent")

    print()

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "akibaba01@gmail.com"

    research_contact(email)
