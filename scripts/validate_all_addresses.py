#!/usr/bin/env python3
"""
EASY MODE: Validate ALL unvalidated addresses (billing + shipping) in one command.

This script:
- Uses SmartyStreets API (recommended for speed and data quality)
- Validates 1,356 addresses (785 billing + 571 shipping)
- Takes ~2-3 minutes total
- Automatically imports results when done

Requirements:
- export SMARTY_AUTH_ID='your_auth_id'
- export SMARTY_AUTH_TOKEN='your_token'

Get credentials (5 minutes):
https://www.smarty.com/pricing/us-address-verification
"""

import csv
import os
import sys
import time
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# SmartyStreets API Configuration
SMARTY_API_URL = "https://us-street.api.smarty.com/street-address"
SMARTY_AUTH_ID = os.getenv("SMARTY_AUTH_ID", "")
SMARTY_AUTH_TOKEN = os.getenv("SMARTY_AUTH_TOKEN", "")

# Database connection
DB_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# Rate limiting
REQUESTS_PER_SECOND = 10
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

def validate_address_smarty(auth_id, auth_token, sequence, address_data):
    """Validate address using SmartyStreets."""
    try:
        params = {
            'auth-id': auth_id,
            'auth-token': auth_token,
            'street': address_data['addressline1'],
            'city': address_data['city'],
            'state': address_data['state'],
            'zipcode': address_data['postalcode'][:5],
            'candidates': '1',
            'match': 'strict'
        }

        if address_data.get('addressline2'):
            params['street2'] = address_data['addressline2']

        url = f"{SMARTY_API_URL}?{urlencode(params)}"
        request = Request(url)
        request.add_header('User-Agent', 'StarHouse-CRM/1.0')

        response = urlopen(request, timeout=10)
        response_data = response.read().decode('utf-8')
        results = json.loads(response_data)

        if not results:
            return {
                '[sequence]': sequence,
                'ValidationFlag': 'ERROR',
                '[summary]': 'Address not found',
                'success': False
            }

        result = results[0]
        components = result.get('components', {})
        metadata = result.get('metadata', {})
        analysis = result.get('analysis', {})

        dpv_match_code = analysis.get('dpv_match_code', 'N')
        dpv_vacant = analysis.get('dpv_vacant', 'N')

        zip5 = components.get('zipcode', '')
        zip4 = components.get('plus4_code', '')
        full_zipcode = f"{zip5}-{zip4}" if zip4 else zip5

        return {
            '[sequence]': sequence,
            'ValidationFlag': 'OK' if dpv_match_code in ['Y', 'S', 'D'] else 'ERROR',
            '[summary]': f"DPV: {dpv_match_code}",
            '[delivery_line_1]': result.get('delivery_line_1', ''),
            '[delivery_line_2]': result.get('delivery_line_2', ''),
            '[city_name]': components.get('city_name', ''),
            '[state_abbreviation]': components.get('state_abbreviation', ''),
            '[full_zipcode]': full_zipcode,
            '[notes]': analysis.get('dpv_footnotes', ''),
            '[county_name]': metadata.get('county_name', ''),
            '[rdi]': metadata.get('rdi', ''),
            '[latitude]': str(metadata.get('latitude', '')),
            '[longitude]': str(metadata.get('longitude', '')),
            '[precision]': metadata.get('precision', ''),
            '[dpv_match_code]': dpv_match_code,
            '[dpv_vacant]': dpv_vacant,
            '[active]': analysis.get('active', 'Y'),
            '[last_line]': result.get('last_line', ''),
            'success': True
        }

    except HTTPError as e:
        error_msg = f"HTTP {e.code}"
        if e.code == 401:
            error_msg = "Auth failed - check credentials"
        elif e.code == 402:
            error_msg = "Payment required - exceeded free tier"
        return {
            '[sequence]': sequence,
            'ValidationFlag': 'ERROR',
            '[summary]': error_msg,
            'success': False
        }
    except Exception as e:
        return {
            '[sequence]': sequence,
            'ValidationFlag': 'ERROR',
            '[summary]': str(e),
            'success': False
        }

def read_input_csv(filepath):
    """Read input CSV."""
    addresses = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            addresses.append(row)
    return addresses

def write_output_csv(filepath, results):
    """Write validation results."""
    if not results:
        return

    fieldnames = [
        '[sequence]', 'ValidationFlag', '[summary]',
        '[delivery_line_1]', '[delivery_line_2]',
        '[city_name]', '[state_abbreviation]', '[full_zipcode]',
        '[notes]', '[county_name]', '[rdi]',
        '[latitude]', '[longitude]', '[precision]',
        '[dpv_match_code]', '[dpv_vacant]', '[active]', '[last_line]'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

def update_billing_usps_data(cursor, email, validation_data):
    """Update billing address."""
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
        RETURNING id
    """, (
        datetime.now(),
        validation_data.get('[dpv_match_code]'),
        validation_data.get('[precision]'),
        validation_data.get('[delivery_line_1]'),
        validation_data.get('[delivery_line_2]'),
        validation_data.get('[last_line]'),
        float(validation_data.get('[latitude]')) if validation_data.get('[latitude]') else None,
        float(validation_data.get('[longitude]')) if validation_data.get('[longitude]') else None,
        validation_data.get('[county_name]'),
        validation_data.get('[rdi]'),
        validation_data.get('[notes]'),
        validation_data.get('[dpv_vacant]') == 'Y',
        validation_data.get('[active]') == 'Y',
        validation_data.get('[dpv_match_code]') == 'Y',
        email
    ))
    return cursor.fetchone()

def update_shipping_usps_data(cursor, email, validation_data):
    """Update shipping address."""
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
        RETURNING id
    """, (
        datetime.now(),
        validation_data.get('[dpv_match_code]'),
        validation_data.get('[precision]'),
        validation_data.get('[delivery_line_1]'),
        validation_data.get('[delivery_line_2]'),
        validation_data.get('[last_line]'),
        float(validation_data.get('[latitude]')) if validation_data.get('[latitude]') else None,
        float(validation_data.get('[longitude]')) if validation_data.get('[longitude]') else None,
        validation_data.get('[county_name]'),
        validation_data.get('[rdi]'),
        validation_data.get('[notes]'),
        validation_data.get('[dpv_vacant]') == 'Y',
        validation_data.get('[active]') == 'Y',
        validation_data.get('[dpv_match_code]') == 'Y',
        email
    ))
    return cursor.fetchone()

def main():
    """Main validation and import function."""

    # Check credentials
    if not SMARTY_AUTH_ID or not SMARTY_AUTH_TOKEN:
        print("=" * 70)
        print("ERROR: SmartyStreets credentials not set")
        print("=" * 70)
        print()
        print("Get credentials (5 minutes):")
        print("https://www.smarty.com/pricing/us-address-verification")
        print()
        print("Then set environment variables:")
        print("  export SMARTY_AUTH_ID='your_auth_id'")
        print("  export SMARTY_AUTH_TOKEN='your_token'")
        sys.exit(1)

    input_file = '/tmp/all_addresses_for_validation.csv'
    output_file = '/tmp/all_addresses_validated.csv'
    progress_file = '/tmp/validation_progress.csv'

    print("=" * 70)
    print("VALIDATE ALL ADDRESSES - EASY MODE")
    print("=" * 70)
    print()

    # Read addresses
    print("Reading addresses...")
    addresses = read_input_csv(input_file)
    billing_count = sum(1 for a in addresses if a['address_type'] == 'billing')
    shipping_count = sum(1 for a in addresses if a['address_type'] == 'shipping')
    print(f"  ✓ {len(addresses)} addresses to validate")
    print(f"    - Billing:  {billing_count}")
    print(f"    - Shipping: {shipping_count}")
    print()

    # Load progress
    previous_results = []
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            reader = csv.DictReader(f)
            previous_results = list(reader)
        print(f"  ✓ Resuming from {len(previous_results)} previous validations")
        print()

    completed_sequences = {int(r['[sequence]']) for r in previous_results}

    # Validate
    print("Validating with SmartyStreets...")
    print(f"Rate: {REQUESTS_PER_SECOND} req/sec | ETA: ~{len(addresses)/REQUESTS_PER_SECOND/60:.1f} minutes")
    print("-" * 70)

    results = previous_results.copy()
    stats = {'success': len([r for r in previous_results if r['ValidationFlag'] == 'OK']),
             'failed': len([r for r in previous_results if r['ValidationFlag'] == 'ERROR'])}
    start_time = time.time()

    for i, address in enumerate(addresses, 1):
        sequence = int(address['sequence'])
        if sequence in completed_sequences:
            continue

        result = validate_address_smarty(SMARTY_AUTH_ID, SMARTY_AUTH_TOKEN, sequence, address)
        results.append(result)

        if result['success'] and result['ValidationFlag'] == 'OK':
            stats['success'] += 1
        else:
            stats['failed'] += 1

        if len(results) % 50 == 0:
            elapsed = time.time() - start_time
            rate = len(results) / elapsed if elapsed > 0 else 0
            remaining = len(addresses) - len(results)
            eta = remaining / rate / 60 if rate > 0 else 0
            print(f"  [{len(results)}/{len(addresses)}] Success: {stats['success']} | Failed: {stats['failed']} | ETA: {eta:.1f}min")
            write_output_csv(progress_file, results)

        time.sleep(DELAY_BETWEEN_REQUESTS)

    write_output_csv(output_file, results)

    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Success: {stats['success']}/{len(addresses)} ({stats['success']/len(addresses)*100:.1f}%)")
    print(f"Failed:  {stats['failed']}/{len(addresses)}")
    print()

    # Import results
    print("Importing results to database...")
    print("-" * 70)

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    import_stats = {'billing': 0, 'shipping': 0}

    for i, (address, validation) in enumerate(zip(addresses, results), 1):
        if validation['ValidationFlag'] != 'OK':
            continue

        try:
            email = address['email'].strip().lower()
            addr_type = address['address_type']

            if addr_type == 'billing':
                if update_billing_usps_data(cursor, email, validation):
                    import_stats['billing'] += 1
            else:
                if update_shipping_usps_data(cursor, email, validation):
                    import_stats['shipping'] += 1

            if (import_stats['billing'] + import_stats['shipping']) % 50 == 0:
                print(f"  ✓ Imported {import_stats['billing'] + import_stats['shipping']} | Billing: {import_stats['billing']} | Shipping: {import_stats['shipping']}")
                conn.commit()

        except Exception as e:
            print(f"  ✗ Error importing {address['email']}: {e}")

    conn.commit()

    # Final stats
    cursor.execute("""
        SELECT
            COUNT(*) FILTER (WHERE billing_usps_validated_at IS NOT NULL) as billing,
            COUNT(*) FILTER (WHERE shipping_usps_validated_at IS NOT NULL) as shipping
        FROM contacts;
    """)
    db_stats = cursor.fetchone()

    cursor.execute("SELECT * FROM mailing_list_stats")
    ml_stats = cursor.fetchone()

    cursor.close()
    conn.close()

    print()
    print("=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print(f"Imported: {import_stats['billing']} billing + {import_stats['shipping']} shipping")
    print()
    print("DATABASE TOTALS:")
    print(f"  Billing addresses validated:  {db_stats['billing']:,}")
    print(f"  Shipping addresses validated: {db_stats['shipping']:,}")
    print()
    print("MAILING LIST QUALITY:")
    print(f"  Total contacts:     {ml_stats[0]:,}")
    print(f"  High confidence:    {ml_stats[3] + ml_stats[4]:,} ({(ml_stats[3]+ml_stats[4])/ml_stats[0]*100:.1f}%)")
    print(f"  Average score:      {ml_stats[9]}")
    print("=" * 70)
    print()
    print("✅ All addresses validated and imported!")

if __name__ == '__main__':
    main()
