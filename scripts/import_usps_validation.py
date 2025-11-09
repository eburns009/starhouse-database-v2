#!/usr/bin/env python3
"""
Import USPS validation data from CSV into contacts table.

This script reads the validated address CSV file and updates the contacts table
with USPS validation metadata including standardized addresses, geocodes, and
delivery point validation status.
"""

import csv
import os
import sys
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection details
DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")  # SECURITY: No hardcoded credentials

def get_db_connection():
    """Create database connection."""
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    return conn

def normalize_name(name):
    """Normalize name for matching."""
    if not name:
        return ""
    return name.strip().lower()

def parse_csv_row(row):
    """Parse a CSV row and extract relevant USPS validation data."""
    return {
        'first_name': row.get('FirstName', '').strip(),
        'last_name': row.get('LastName', '').strip(),
        'full_name': row.get('FullName', '').strip(),
        'business_name': row.get('BusinessName', '').strip(),
        'original_address_line_1': row.get('AddressLine1', '').strip(),
        'original_address_line_2': row.get('AddressLine2', '').strip(),
        'original_city': row.get('City', '').strip(),
        'original_state': row.get('State', '').strip(),
        'original_postal_code': row.get('PostalCode', '').strip(),
        'validation_flag': row.get('ValidationFlag', ''),
        'validation_notes': row.get('ValidationNotes', ''),
        'summary': row.get('[summary]', ''),
        'delivery_line_1': row.get('[delivery_line_1]', '').strip(),
        'delivery_line_2': row.get('[delivery_line_2]', '').strip(),
        'city_name': row.get('[city_name]', '').strip(),
        'state_abbreviation': row.get('[state_abbreviation]', '').strip(),
        'full_zipcode': row.get('[full_zipcode]', '').strip(),
        'notes': row.get('[notes]', ''),
        'county_name': row.get('[county_name]', ''),
        'rdi': row.get('[rdi]', ''),
        'latitude': row.get('[latitude]', ''),
        'longitude': row.get('[longitude]', ''),
        'precision': row.get('[precision]', ''),
        'dpv_match_code': row.get('[dpv_match_code]', ''),
        'dpv_vacant': row.get('[dpv_vacant]', '') == 'Y',
        'active': row.get('[active]', '') == 'Y',
        'last_line': row.get('[last_line]', ''),
    }

def find_contact(cursor, data):
    """
    Find a contact in the database by matching on name and address.

    Strategy:
    1. Try exact match on email (if we had it)
    2. Try match on first_name, last_name, and address_line_1
    3. Try match on business_name and address_line_1
    4. Try match on full_name and address_line_1
    """

    # Strategy 1: Match on first_name, last_name, and address
    if data['first_name'] and data['last_name'] and data['original_address_line_1']:
        cursor.execute("""
            SELECT id, email, first_name, last_name,
                   address_line_1, city, state, postal_code
            FROM contacts
            WHERE LOWER(first_name) = LOWER(%s)
              AND LOWER(last_name) = LOWER(%s)
              AND LOWER(address_line_1) = LOWER(%s)
            LIMIT 1
        """, (data['first_name'], data['last_name'], data['original_address_line_1']))

        result = cursor.fetchone()
        if result:
            return result

    # Strategy 2: Match on business name and address
    if data['business_name'] and data['original_address_line_1']:
        cursor.execute("""
            SELECT id, email, first_name, last_name,
                   address_line_1, city, state, postal_code
            FROM contacts
            WHERE LOWER(paypal_business_name) = LOWER(%s)
              AND LOWER(address_line_1) = LOWER(%s)
            LIMIT 1
        """, (data['business_name'], data['original_address_line_1']))

        result = cursor.fetchone()
        if result:
            return result

    # Strategy 3: Try matching on standardized address if original didn't work
    if data['first_name'] and data['last_name'] and data['delivery_line_1']:
        cursor.execute("""
            SELECT id, email, first_name, last_name,
                   address_line_1, city, state, postal_code
            FROM contacts
            WHERE LOWER(first_name) = LOWER(%s)
              AND LOWER(last_name) = LOWER(%s)
              AND (
                LOWER(address_line_1) = LOWER(%s)
                OR LOWER(billing_usps_delivery_line_1) = LOWER(%s)
              )
            LIMIT 1
        """, (data['first_name'], data['last_name'],
              data['delivery_line_1'], data['delivery_line_1']))

        result = cursor.fetchone()
        if result:
            return result

    return None

def update_contact_usps_data(cursor, contact_id, data):
    """Update contact with USPS validation data."""

    # Parse numeric values
    latitude = None
    longitude = None
    try:
        if data['latitude']:
            latitude = float(data['latitude'])
        if data['longitude']:
            longitude = float(data['longitude'])
    except (ValueError, TypeError):
        pass

    # Update billing address USPS validation fields
    cursor.execute("""
        UPDATE contacts
        SET
            billing_usps_validated_at = %s,
            billing_usps_dpv_match_code = %s,
            billing_usps_precision = %s,
            billing_usps_delivery_line_1 = %s,
            billing_usps_delivery_line_2 = %s,
            billing_usps_last_line = %s,
            billing_usps_latitude = %s,
            billing_usps_longitude = %s,
            billing_usps_county = %s,
            billing_usps_rdi = %s,
            billing_usps_footnotes = %s,
            billing_usps_vacant = %s,
            billing_usps_active = %s,
            billing_address_verified = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (
        datetime.now(),  # validated_at
        data['dpv_match_code'],
        data['precision'],
        data['delivery_line_1'],
        data['delivery_line_2'] if data['delivery_line_2'] else None,
        data['last_line'],
        latitude,
        longitude,
        data['county_name'] if data['county_name'] else None,
        data['rdi'] if data['rdi'] else None,
        data['notes'] if data['notes'] else data['summary'],
        data['dpv_vacant'],
        data['active'],
        data['dpv_match_code'] == 'Y',  # Set billing_address_verified based on match
        contact_id
    ))

def main():
    """Main import function."""

    # Check if CSV file path is provided
    if len(sys.argv) < 2:
        csv_file = '/workspaces/starhouse-database-v2/data/donors_us_ready_for_validation-output (1).csv'
        print(f"No CSV file specified, using default: {csv_file}")
    else:
        csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    print(f"Reading USPS validation data from: {csv_file}")

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Statistics
    stats = {
        'total_rows': 0,
        'matched': 0,
        'not_matched': 0,
        'updated': 0,
        'errors': 0
    }

    unmatched_contacts = []

    try:
        # Read and process CSV
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                stats['total_rows'] += 1

                # Parse row data
                data = parse_csv_row(row)

                # Skip rows with no validation (failed validation)
                if data['validation_flag'] != 'OK':
                    stats['not_matched'] += 1
                    continue

                # Find matching contact
                contact = find_contact(cursor, data)

                if contact:
                    stats['matched'] += 1
                    try:
                        # Update contact with USPS data
                        update_contact_usps_data(cursor, contact['id'], data)
                        stats['updated'] += 1

                        if stats['updated'] % 10 == 0:
                            print(f"Updated {stats['updated']} contacts...")
                            conn.commit()  # Commit periodically

                    except Exception as e:
                        stats['errors'] += 1
                        print(f"Error updating contact {contact['email']}: {e}")
                        conn.rollback()
                else:
                    stats['not_matched'] += 1
                    unmatched_contacts.append({
                        'name': f"{data['first_name']} {data['last_name']}".strip() or data['business_name'],
                        'address': data['original_address_line_1']
                    })

        # Final commit
        conn.commit()

        # Print statistics
        print("\n" + "="*60)
        print("IMPORT STATISTICS")
        print("="*60)
        print(f"Total rows processed:    {stats['total_rows']}")
        print(f"Contacts matched:        {stats['matched']}")
        print(f"Contacts updated:        {stats['updated']}")
        print(f"Not matched:             {stats['not_matched']}")
        print(f"Errors:                  {stats['errors']}")
        print("="*60)

        # Show sample of unmatched contacts
        if unmatched_contacts:
            print(f"\nSample of unmatched contacts (first 10):")
            for contact in unmatched_contacts[:10]:
                print(f"  - {contact['name']:30} | {contact['address']}")

            if len(unmatched_contacts) > 10:
                print(f"  ... and {len(unmatched_contacts) - 10} more")

        print("\n✓ Import completed successfully!")

    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
