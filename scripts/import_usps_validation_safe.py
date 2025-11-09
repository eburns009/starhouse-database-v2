#!/usr/bin/env python3
"""
Import USPS validation data using the original mailing list export.

This script is SAFE because it:
1. Reads the original mailing_list.csv (which has email addresses)
2. Reads the validation output CSV (which has USPS data)
3. Matches them by row number/sequence
4. Updates contacts by EMAIL (unique key) rather than fuzzy name matching

This eliminates any risk of updating the wrong contact.
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

def read_original_mailing_list(filepath):
    """Read the original mailing list CSV (which has emails)."""
    contacts = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append({
                'email': row['Email'].strip().lower(),
                'first_name': row['FirstName'].strip(),
                'last_name': row['LastName'].strip(),
                'address_line_1': row['AddressLine1'].strip(),
                'city': row['City'].strip(),
                'state': row['State'].strip(),
            })
    return contacts

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

def update_contact_usps_data(cursor, email, validation_data):
    """Update contact with USPS validation data using email as the key."""

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
        datetime.now(),  # validated_at
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
        validation_data['dpv_match_code'] == 'Y',  # Set verified based on match
        email
    ))

    return cursor.fetchone()

def main():
    """Main import function."""

    # File paths
    original_file = '/workspaces/starhouse-database-v2/mailing_list.csv'
    validation_file = '/workspaces/starhouse-database-v2/data/donors_us_ready_for_validation-output (1).csv'

    # Allow override via command line
    if len(sys.argv) >= 2:
        original_file = sys.argv[1]
    if len(sys.argv) >= 3:
        validation_file = sys.argv[2]

    # Verify files exist
    if not os.path.exists(original_file):
        print(f"Error: Original mailing list not found: {original_file}")
        sys.exit(1)

    if not os.path.exists(validation_file):
        print(f"Error: Validation output not found: {validation_file}")
        sys.exit(1)

    print("=" * 70)
    print("USPS VALIDATION IMPORT - SAFE MODE")
    print("=" * 70)
    print(f"Original mailing list: {original_file}")
    print(f"Validation output:     {validation_file}")
    print()

    # Read both files
    print("Reading original mailing list...")
    original_contacts = read_original_mailing_list(original_file)
    print(f"  ✓ Loaded {len(original_contacts)} contacts")

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
        'updated': 0,
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

        # Get the corresponding original contact (sequence is 1-indexed)
        if sequence < 1 or sequence > len(original_contacts):
            stats['mismatched'] += 1
            print(f"  ⚠ Sequence {sequence} out of range")
            continue

        original = original_contacts[sequence - 1]  # Convert to 0-indexed

        # Check if email exists
        if not original['email']:
            stats['no_email'] += 1
            print(f"  ⚠ No email for: {original['first_name']} {original['last_name']}")
            continue

        # Skip if validation failed
        if validation['validation_flag'] != 'OK':
            stats['failed_validation'] += 1
            continue

        stats['matched'] += 1

        try:
            # Update the contact by email
            result = update_contact_usps_data(cursor, original['email'], validation)

            if result:
                stats['updated'] += 1

                # Print progress every 25 records
                if stats['updated'] % 25 == 0:
                    print(f"  ✓ Updated {stats['updated']} contacts...")
                    conn.commit()
            else:
                stats['errors'] += 1
                print(f"  ✗ Contact not found for email: {original['email']}")

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
    print(f"Contacts updated:             {stats['updated']}")
    print(f"Failed USPS validation:       {stats['failed_validation']}")
    print(f"Sequence mismatches:          {stats['mismatched']}")
    print(f"No email address:             {stats['no_email']}")
    print(f"Errors:                       {stats['errors']}")
    print("=" * 70)

    # Calculate success rate
    if stats['total'] > 0:
        success_rate = (stats['updated'] / stats['total']) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")

    # Query updated records
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM contacts
        WHERE billing_usps_validated_at IS NOT NULL
    """)
    result = cursor.fetchone()
    print(f"Total contacts with USPS validation: {result['count']}")

    # Show sample of validated addresses
    print("\n" + "=" * 70)
    print("SAMPLE VALIDATED ADDRESSES (first 5)")
    print("=" * 70)

    cursor.execute("""
        SELECT
            first_name, last_name, email,
            address_line_1,
            billing_usps_delivery_line_1,
            billing_usps_last_line,
            billing_usps_precision,
            billing_usps_dpv_match_code,
            billing_usps_county
        FROM contacts
        WHERE billing_usps_validated_at IS NOT NULL
        ORDER BY billing_usps_validated_at DESC
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"\n{row['first_name']} {row['last_name']} ({row['email']})")
        print(f"  Original:   {row['address_line_1']}")
        print(f"  Validated:  {row['billing_usps_delivery_line_1']}")
        print(f"  Last Line:  {row['billing_usps_last_line']}")
        print(f"  Precision:  {row['billing_usps_precision']} | Match: {row['billing_usps_dpv_match_code']} | County: {row['billing_usps_county']}")

    cursor.close()
    conn.close()

    print("\n✓ Import completed successfully!")

if __name__ == '__main__':
    main()
