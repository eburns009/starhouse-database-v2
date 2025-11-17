#!/usr/bin/env python3
"""
Import USPS validation data for ALL addresses (billing AND shipping).

This script handles both address types by reading the 'address_type' column
from the original export CSV and updating the appropriate fields.

Safety features:
1. Reads the original export (which has email + address_type)
2. Reads the validation output CSV (which has USPS data)
3. Matches by row number/sequence
4. Updates by EMAIL (unique key) + address type
"""

import csv
import os
import sys
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import get_database_url

# Database connection
DB_URL = get_database_url()

def get_db_connection():
    """Create database connection."""
    conn = psycopg2.connect(DB_URL)
    return conn

def read_original_list(filepath):
    """Read the original address CSV (which has emails and address_type)."""
    addresses = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            addresses.append({
                'email': row['email'].strip().lower(),
                'firstname': row['firstname'].strip(),
                'lastname': row['lastname'].strip(),
                'addressline1': row['addressline1'].strip(),
                'city': row['city'].strip(),
                'state': row['state'].strip(),
                'address_type': row.get('address_type', 'billing').strip()  # Default to billing
            })
    return addresses

def read_validation_output(filepath):
    """Read the USPS validation output CSV."""
    validations = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse numeric values safely
            latitude = None
            longitude = None
            try:
                lat_str = row.get('[latitude]', '').strip()
                lon_str = row.get('[longitude]', '').strip()
                if lat_str and lat_str != '0':
                    latitude = float(lat_str)
                if lon_str and lon_str != '0':
                    longitude = float(lon_str)
            except (ValueError, TypeError):
                pass

            validations.append({
                'sequence': int(row.get('[sequence]', '0')),
                'validation_flag': row.get('ValidationFlag', ''),
                'summary': row.get('[summary]', ''),
                'delivery_line_1': row.get('[delivery_line_1]', '').strip(),
                'delivery_line_2': row.get('[delivery_line_2]', '').strip(),
                'city_name': row.get('[city_name]', '').strip(),
                'state_abbreviation': row.get('[state_abbreviation]', '').strip(),
                'full_zipcode': row.get('[full_zipcode]', '').strip(),
                'notes': row.get('[notes]', ''),
                'county_name': row.get('[county_name]', ''),
                'rdi': row.get('[rdi]', ''),
                'latitude': latitude,
                'longitude': longitude,
                'precision': row.get('[precision]', ''),
                'dpv_match_code': row.get('[dpv_match_code]', ''),
                'dpv_vacant': row.get('[dpv_vacant]', '') == 'Y',
                'active': row.get('[active]', '') == 'Y',
                'last_line': row.get('[last_line]', ''),
            })
    return validations

def update_billing_usps_data(cursor, email, validation_data):
    """Update contact BILLING address with USPS validation data."""
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
        WHERE email = %s
        RETURNING id, email, first_name, last_name
    """, (
        datetime.now(),
        validation_data['dpv_match_code'] or None,
        validation_data['precision'] or None,
        validation_data['delivery_line_1'] or None,
        validation_data['delivery_line_2'] or None,
        validation_data['last_line'] or None,
        validation_data['latitude'],
        validation_data['longitude'],
        validation_data['county_name'] or None,
        validation_data['rdi'] or None,
        validation_data['notes'] or validation_data['summary'],
        validation_data['dpv_vacant'],
        validation_data['active'],
        validation_data['dpv_match_code'] == 'Y',
        email
    ))
    return cursor.fetchone()

def update_shipping_usps_data(cursor, email, validation_data):
    """Update contact SHIPPING address with USPS validation data."""
    cursor.execute("""
        UPDATE contacts
        SET
            shipping_usps_validated_at = %s,
            shipping_usps_dpv_match_code = %s,
            shipping_usps_precision = %s,
            shipping_usps_delivery_line_1 = %s,
            shipping_usps_delivery_line_2 = %s,
            shipping_usps_last_line = %s,
            shipping_usps_latitude = %s,
            shipping_usps_longitude = %s,
            shipping_usps_county = %s,
            shipping_usps_rdi = %s,
            shipping_usps_footnotes = %s,
            shipping_usps_vacant = %s,
            shipping_usps_active = %s,
            shipping_address_verified = %s,
            updated_at = NOW()
        WHERE email = %s
        RETURNING id, email, first_name, last_name
    """, (
        datetime.now(),
        validation_data['dpv_match_code'] or None,
        validation_data['precision'] or None,
        validation_data['delivery_line_1'] or None,
        validation_data['delivery_line_2'] or None,
        validation_data['last_line'] or None,
        validation_data['latitude'],
        validation_data['longitude'],
        validation_data['county_name'] or None,
        validation_data['rdi'] or None,
        validation_data['notes'] or validation_data['summary'],
        validation_data['dpv_vacant'],
        validation_data['active'],
        validation_data['dpv_match_code'] == 'Y',
        email
    ))
    return cursor.fetchone()

def main():
    """Main import function."""

    # File paths
    original_file = '/tmp/all_addresses_for_validation.csv'
    validation_file = '/tmp/all_addresses_validated.csv'

    # Allow override via command line
    if len(sys.argv) >= 2:
        original_file = sys.argv[1]
    if len(sys.argv) >= 3:
        validation_file = sys.argv[2]

    # Verify files exist
    if not os.path.exists(original_file):
        print(f"Error: Original address list not found: {original_file}")
        sys.exit(1)

    if not os.path.exists(validation_file):
        print(f"Error: Validation output not found: {validation_file}")
        print()
        print("Instructions:")
        print("1. Run validation script: python3 scripts/validate_all_addresses.py")
        print("2. Wait for completion")
        print("3. Run this import script again")
        sys.exit(1)

    print("=" * 70)
    print("USPS VALIDATION IMPORT - ALL ADDRESSES")
    print("=" * 70)
    print(f"Original list: {original_file}")
    print(f"Validation:    {validation_file}")
    print()

    # Read both files
    print("Reading original address list...")
    original_addresses = read_original_list(original_file)
    print(f"  ✓ Loaded {len(original_addresses)} addresses")

    billing_count = sum(1 for a in original_addresses if a['address_type'] == 'billing')
    shipping_count = sum(1 for a in original_addresses if a['address_type'] == 'shipping')
    print(f"    - Billing:  {billing_count}")
    print(f"    - Shipping: {shipping_count}")

    print("Reading validation output...")
    validations = read_validation_output(validation_file)
    print(f"  ✓ Loaded {len(validations)} validated addresses")
    print()

    # Connect to database
    print("Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("  ✓ Connected")
    print()

    # Statistics
    stats = {
        'total': 0,
        'matched': 0,
        'updated_billing': 0,
        'updated_shipping': 0,
        'failed_validation': 0,
        'mismatched': 0,
        'no_email': 0,
        'errors': 0
    }

    # Process each validation result
    print("Processing validations...")
    print("-" * 70)

    for validation in validations:
        stats['total'] += 1
        sequence = validation['sequence']

        # Get the corresponding original address
        if sequence < 1 or sequence > len(original_addresses):
            stats['mismatched'] += 1
            print(f"  ⚠ Sequence {sequence} out of range")
            continue

        original = original_addresses[sequence - 1]

        # Check if email exists
        if not original['email']:
            stats['no_email'] += 1
            print(f"  ⚠ No email for: {original['firstname']} {original['lastname']}")
            continue

        # Skip if validation failed
        if validation['validation_flag'] != 'OK':
            stats['failed_validation'] += 1
            continue

        stats['matched'] += 1

        try:
            # Update based on address type
            if original['address_type'] == 'billing':
                result = update_billing_usps_data(cursor, original['email'], validation)
                if result:
                    stats['updated_billing'] += 1
            else:  # shipping
                result = update_shipping_usps_data(cursor, original['email'], validation)
                if result:
                    stats['updated_shipping'] += 1

            # Print progress every 50 records
            if (stats['updated_billing'] + stats['updated_shipping']) % 50 == 0:
                total_updated = stats['updated_billing'] + stats['updated_shipping']
                print(f"  ✓ Updated {total_updated} contacts...")
                print(f"     Billing: {stats['updated_billing']} | Shipping: {stats['updated_shipping']}")
                conn.commit()

        except Exception as e:
            stats['errors'] += 1
            print(f"  ✗ Error updating {original['email']}: {e}")
            conn.rollback()

    # Final commit
    conn.commit()

    # Print final statistics
    print()
    print("=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"Total validation records:     {stats['total']}")
    print(f"Successfully matched:         {stats['matched']}")
    print(f"Billing addresses updated:    {stats['updated_billing']}")
    print(f"Shipping addresses updated:   {stats['updated_shipping']}")
    print(f"Total addresses updated:      {stats['updated_billing'] + stats['updated_shipping']}")
    print(f"Failed USPS validation:       {stats['failed_validation']}")
    print(f"Sequence mismatches:          {stats['mismatched']}")
    print(f"No email address:             {stats['no_email']}")
    print(f"Errors:                       {stats['errors']}")
    print("=" * 70)

    # Calculate success rate
    if stats['total'] > 0:
        success_rate = ((stats['updated_billing'] + stats['updated_shipping']) / stats['total']) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")

    # Query updated counts
    cursor.execute("""
        SELECT
            COUNT(*) FILTER (WHERE billing_usps_validated_at IS NOT NULL) as billing_validated,
            COUNT(*) FILTER (WHERE shipping_usps_validated_at IS NOT NULL) as shipping_validated
        FROM contacts;
    """)
    result = cursor.fetchone()

    print()
    print("TOTAL USPS VALIDATED ADDRESSES IN DATABASE:")
    print(f"  Billing:  {result['billing_validated']:,}")
    print(f"  Shipping: {result['shipping_validated']:,}")
    print()

    cursor.close()
    conn.close()

    print("\n✓ Import completed successfully!")
    print()
    print("Next: Check updated mailing list statistics:")
    print("  python3 -c \"import psycopg2; conn=psycopg2.connect('$DATABASE_URL'); ")
    print("  cursor=conn.cursor(); cursor.execute('SELECT * FROM mailing_list_stats'); ")
    print("  print(cursor.fetchone())\"")

if __name__ == '__main__':
    main()
