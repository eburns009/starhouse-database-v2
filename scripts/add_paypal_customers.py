#!/usr/bin/env python3
"""
Add New PayPal Customers to Contacts Database
==============================================
Extract PayPal customers who are not currently in contacts database
and add them as new contact records.

Strategy:
1. Extract all unique PayPal customers (email, name, phone, address)
2. Check which emails are NOT in contacts database
3. Parse names into first/last
4. Normalize phone numbers and addresses
5. Insert as new contacts with source_system = 'PayPal'
6. Track all additions for audit
"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_values
import re
from datetime import datetime

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'PLACEHOLDER_USE_ENV_VAR')

def normalize_phone(phone):
    """Normalize phone number to digits only"""
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) >= 10:
        return digits
    return None

def parse_name(full_name):
    """Parse full name into first and last"""
    if not full_name:
        return None, None

    # Title case the name
    full_name = full_name.strip().title()

    parts = full_name.split()
    if len(parts) == 0:
        return None, None
    elif len(parts) == 1:
        return parts[0], None
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Multiple parts: first is first name, rest is last name
        return parts[0], ' '.join(parts[1:])

def extract_paypal_customers():
    """Extract unique PayPal customers with all available data"""
    paypal_file = "/workspaces/starhouse-database-v2/kajabi 3 files review/paypal 2024.CSV"
    customers = {}  # email -> customer data (keep most recent transaction)

    with open(paypal_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('From Email Address', '').strip().lower()
            if not email:
                continue

            # Extract all available data
            name = row.get('Name', '').strip()
            phone = normalize_phone(row.get('Contact Phone Number', '').strip())
            address1 = row.get('Address Line 1', '').strip()
            address2 = row.get('Address Line 2/District/Neighborhood', '').strip()
            city = row.get('Town/City', '').strip()
            state = row.get('State/Province/Region/County/Territory/Prefecture/Republic', '').strip()
            zipcode = row.get('Zip/Postal Code', '').strip()
            country = row.get('Country', '').strip()

            # Parse name
            first_name, last_name = parse_name(name)

            # Prefer records with more complete data
            # If email already exists, keep the one with more data
            if email not in customers or (
                # Prefer records with address data
                (address1 and not customers[email].get('address1')) or
                # Prefer records with phone
                (phone and not customers[email].get('phone'))
            ):
                customers[email] = {
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'address1': address1 if address1 else None,
                    'address2': address2 if address2 else None,
                    'city': city if city else None,
                    'state': state if state else None,
                    'zipcode': zipcode if zipcode else None,
                    'country': country if country else None,
                    'full_name': name  # Keep original for reference
                }

    return customers

def main():
    print("=" * 70)
    print("ADD NEW PAYPAL CUSTOMERS TO CONTACTS DATABASE")
    print("=" * 70)
    print()

    # Extract PayPal customers
    print("Step 1: Extracting PayPal customer data...")
    paypal_customers = extract_paypal_customers()
    print(f"  ✓ Found {len(paypal_customers)} unique PayPal customer emails")

    # Connect to database
    print("\nStep 2: Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get existing contact emails
    print("\nStep 3: Checking which customers are already in database...")
    cur.execute("SELECT LOWER(email) FROM contacts WHERE email IS NOT NULL")
    existing_emails = set(email[0] for email in cur.fetchall())
    print(f"  ✓ Found {len(existing_emails)} existing contact emails in database")

    # Find new customers
    new_customers = {
        email: data for email, data in paypal_customers.items()
        if email not in existing_emails
    }
    print(f"  ✓ Found {len(new_customers)} NEW PayPal customers to add")

    if not new_customers:
        print("\n⚠ No new customers to add. All PayPal emails already in database.")
        conn.close()
        return

    # Analyze data completeness
    print("\nStep 4: Analyzing data completeness of new customers...")
    with_phone = sum(1 for c in new_customers.values() if c['phone'])
    with_address = sum(1 for c in new_customers.values() if c['address1'])
    with_city_state = sum(1 for c in new_customers.values() if c['city'] and c['state'])
    with_zip = sum(1 for c in new_customers.values() if c['zipcode'])
    with_last_name = sum(1 for c in new_customers.values() if c['last_name'])

    print(f"  Data completeness of {len(new_customers)} new customers:")
    print(f"    Email:          {len(new_customers)} (100.0%)")
    print(f"    First Name:     {sum(1 for c in new_customers.values() if c['first_name'])} ({100*sum(1 for c in new_customers.values() if c['first_name'])/len(new_customers):.1f}%)")
    print(f"    Last Name:      {with_last_name} ({100*with_last_name/len(new_customers):.1f}%)")
    print(f"    Phone:          {with_phone} ({100*with_phone/len(new_customers):.1f}%)")
    print(f"    Address:        {with_address} ({100*with_address/len(new_customers):.1f}%)")
    print(f"    City/State:     {with_city_state} ({100*with_city_state/len(new_customers):.1f}%)")
    print(f"    Zip Code:       {with_zip} ({100*with_zip/len(new_customers):.1f}%)")

    # Create backup table for new contacts
    print("\nStep 5: Creating backup table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts_additions_backup (
            backup_id SERIAL PRIMARY KEY,
            contact_email TEXT NOT NULL,
            contact_data JSONB NOT NULL,
            source_system TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT NOW(),
            notes TEXT
        );
    """)

    # Insert new contacts
    print("\nStep 6: Adding new contacts to database...")
    added_count = 0

    for email, customer in new_customers.items():
        try:
            # Backup record
            cur.execute("""
                INSERT INTO contacts_additions_backup
                (contact_email, contact_data, source_system, notes)
                VALUES (%s, %s, %s, %s)
            """, (
                email,
                psycopg2.extras.Json(customer),
                'paypal',
                f'New customer from PayPal 2024 transactions: {customer["full_name"]}'
            ))

            # Insert new contact
            cur.execute("""
                INSERT INTO contacts (
                    email,
                    first_name,
                    last_name,
                    phone,
                    address_line_1,
                    address_line_2,
                    city,
                    state,
                    zipcode,
                    country,
                    source_system,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                customer['email'],
                customer['first_name'],
                customer['last_name'],
                customer['phone'],
                customer['address1'],
                customer['address2'],
                customer['city'],
                customer['state'],
                customer['zipcode'],
                customer['country'],
                'paypal'
            ))

            added_count += 1

        except Exception as e:
            print(f"  ⚠ Error adding {email}: {e}")
            continue

    conn.commit()
    print(f"  ✓ Added {added_count} new contacts")

    # Summary
    print("\n" + "=" * 70)
    print("ADDITION SUMMARY")
    print("=" * 70)

    # New database size
    cur.execute("SELECT COUNT(*) FROM contacts")
    total_contacts = cur.fetchone()[0]
    previous_total = total_contacts - added_count

    print(f"\nDatabase Growth:")
    print(f"  Before: {previous_total} contacts")
    print(f"  After:  {total_contacts} contacts")
    print(f"  Added:  {added_count} new contacts (+{100*added_count/previous_total:.1f}%)")

    # Completeness impact
    if added_count > 0:
        print(f"\nData Quality of New Contacts:")
        print(f"  {with_phone}/{added_count} with phone ({100*with_phone/added_count:.1f}%)")
        print(f"  {with_address}/{added_count} with address ({100*with_address/added_count:.1f}%)")
        print(f"  {with_zip}/{added_count} with zip code ({100*with_zip/added_count:.1f}%)")

    # Updated overall completeness
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone <> '') as with_phone,
            COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL AND address_line_1 <> '') as with_address,
            COUNT(*) FILTER (WHERE zipcode IS NOT NULL AND zipcode <> '') as with_zip,
            COUNT(*) as total
        FROM contacts
    """)
    with_phone_total, with_address_total, with_zip_total, total = cur.fetchone()

    print(f"\nOverall Database Completeness (After Addition):")
    print(f"  Phone:      {100*with_phone_total/total:.1f}%")
    print(f"  Address:    {100*with_address_total/total:.1f}%")
    print(f"  Zip Code:   {100*with_zip_total/total:.1f}%")

    # Verification
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    cur.execute("""
        SELECT COUNT(*) FROM contacts_additions_backup
        WHERE source_system = 'paypal'
          AND added_at > NOW() - INTERVAL '5 minutes'
    """)
    backup_count = cur.fetchone()[0]
    print(f"  Backup records created: {backup_count}")
    print(f"  Contacts added: {added_count}")
    print(f"  Status: {'✓ PASS' if backup_count == added_count else '✗ FAIL'}")

    # Sample new contacts
    print("\n" + "=" * 70)
    print("SAMPLE NEW CONTACTS (First 20)")
    print("=" * 70)

    sample_customers = list(new_customers.items())[:20]
    for i, (email, customer) in enumerate(sample_customers, 1):
        phone_display = customer['phone'] if customer['phone'] else 'No phone'
        location = f"{customer['city']}, {customer['state']}" if customer['city'] and customer['state'] else 'No location'
        print(f"  {i:2}. {customer['full_name'][:30]:<30} | {phone_display:<12} | {location}")

    if len(new_customers) > 20:
        print(f"  ... and {len(new_customers) - 20} more")

    conn.close()
    print("\n✓ PayPal customer addition complete!")

if __name__ == '__main__':
    main()
