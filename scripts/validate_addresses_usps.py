#!/usr/bin/env python3
"""
Validate shipping addresses using USPS Web Tools API (free service).

USPS Web Tools API Documentation:
https://www.usps.com/business/web-tools-apis/

Requirements:
1. USPS User ID (register at https://www.usps.com/business/web-tools-apis/)
2. Rate limit: 5 requests per second (we'll use 4/sec to be safe)
3. US addresses only

This script:
- Reads addresses from CSV
- Validates them one by one with rate limiting
- Saves progress after every 10 records (resumable)
- Outputs validation results in the expected format
"""

import csv
import os
import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote
from urllib.request import urlopen
from datetime import datetime

# USPS Web Tools API Configuration
USPS_API_URL = "https://secure.shippingapis.com/ShippingAPI.dll"
USPS_USER_ID = os.getenv("USPS_USER_ID", "")

# Rate limiting: 4 requests per second (conservative)
REQUESTS_PER_SECOND = 4
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

def validate_address_usps(user_id, sequence, address_data):
    """
    Validate a single address using USPS Address Validation API.

    Returns dict with validation results or error information.
    """

    # Build XML request
    xml_request = f"""<AddressValidateRequest USERID="{user_id}">
    <Revision>1</Revision>
    <Address ID="{sequence}">
        <Address1>{address_data.get('addressline2', '')}</Address1>
        <Address2>{address_data['addressline1']}</Address2>
        <City>{address_data['city']}</City>
        <State>{address_data['state']}</State>
        <Zip5>{address_data['postalcode'][:5]}</Zip5>
        <Zip4></Zip4>
    </Address>
</AddressValidateRequest>"""

    try:
        # Make API request
        params = {
            'API': 'Verify',
            'XML': xml_request
        }

        url = f"{USPS_API_URL}?{urlencode(params)}"
        response = urlopen(url, timeout=10)
        response_xml = response.read().decode('utf-8')

        # Parse response
        root = ET.fromstring(response_xml)

        # Check for errors
        error = root.find('.//Error')
        if error is not None:
            error_desc = error.find('Description')
            return {
                'sequence': sequence,
                'ValidationFlag': 'ERROR',
                'error_message': error_desc.text if error_desc is not None else 'Unknown error',
                'success': False
            }

        # Extract validated address
        address = root.find('.//Address')
        if address is None:
            return {
                'sequence': sequence,
                'ValidationFlag': 'ERROR',
                'error_message': 'No address in response',
                'success': False
            }

        # Get DPV confirmation (Y = confirmed, N = not confirmed)
        dpv_confirmation = address.find('DPVConfirmation')
        dpv_code = dpv_confirmation.text if dpv_confirmation is not None else 'N'

        # Map DPV codes
        dpv_match_code = dpv_code  # Y, N, S, D

        # Extract address components
        addr2 = address.find('Address2')
        addr1 = address.find('Address1')  # Apt/Suite
        city = address.find('City')
        state = address.find('State')
        zip5 = address.find('Zip5')
        zip4 = address.find('Zip4')

        delivery_line_1 = addr2.text if addr2 is not None else ''
        delivery_line_2 = addr1.text if addr1 is not None else ''
        city_name = city.text if city is not None else ''
        state_abbr = state.text if state is not None else ''
        zip5_text = zip5.text if zip5 is not None else ''
        zip4_text = zip4.text if zip4 is not None else ''

        # Build full zipcode
        if zip4_text:
            full_zipcode = f"{zip5_text}-{zip4_text}"
        else:
            full_zipcode = zip5_text

        last_line = f"{city_name}, {state_abbr} {full_zipcode}"

        # Determine precision based on ZIP+4
        if zip4_text:
            precision = 'Zip9'  # ZIP+4 is rooftop level
        else:
            precision = 'Zip5'

        # Check for footnotes/notes
        footnotes = address.find('Footnotes')
        notes = footnotes.text if footnotes is not None else ''

        # Determine if active (no specific field, assume Y if validated)
        active = 'Y' if dpv_code in ['Y', 'S', 'D'] else 'N'

        return {
            'sequence': sequence,
            'ValidationFlag': 'OK' if dpv_code in ['Y', 'S', 'D'] else 'ERROR',
            '[summary]': f"DPV: {dpv_code}",
            '[delivery_line_1]': delivery_line_1,
            '[delivery_line_2]': delivery_line_2,
            '[city_name]': city_name,
            '[state_abbreviation]': state_abbr,
            '[full_zipcode]': full_zipcode,
            '[notes]': notes,
            '[county_name]': '',  # USPS API doesn't return county
            '[rdi]': '',  # USPS API doesn't return RDI
            '[latitude]': '',  # USPS API doesn't return geocoding
            '[longitude]': '',
            '[precision]': precision,
            '[dpv_match_code]': dpv_match_code,
            '[dpv_vacant]': '',  # USPS API doesn't return vacant status
            '[active]': active,
            '[last_line]': last_line,
            'success': True
        }

    except Exception as e:
        return {
            'sequence': sequence,
            'ValidationFlag': 'ERROR',
            'error_message': str(e),
            'success': False
        }

def read_input_csv(filepath):
    """Read the input CSV with addresses to validate."""
    addresses = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            addresses.append(row)
    return addresses

def write_output_csv(filepath, results):
    """Write validation results to output CSV."""
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

def load_progress(progress_file):
    """Load previously validated results to resume."""
    if not os.path.exists(progress_file):
        return []

    results = []
    with open(progress_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def main():
    """Main validation function."""

    # Check for USPS User ID
    if not USPS_USER_ID:
        print("=" * 70)
        print("ERROR: USPS_USER_ID environment variable not set")
        print("=" * 70)
        print()
        print("To use the free USPS Web Tools API, you need to register:")
        print("1. Go to: https://www.usps.com/business/web-tools-apis/")
        print("2. Register for a free User ID")
        print("3. Set the environment variable:")
        print("   export USPS_USER_ID='your_user_id_here'")
        print()
        print("Alternative: Use a commercial service (SmartyStreets, Lob, etc.)")
        print("See: docs/PHASE2_SHIPPING_VALIDATION.md")
        sys.exit(1)

    # File paths
    input_file = '/tmp/shipping_addresses_for_validation.csv'
    output_file = '/tmp/shipping_addresses_validated.csv'
    progress_file = '/tmp/usps_validation_progress.csv'

    # Allow override via command line
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]

    # Verify input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    print("=" * 70)
    print("USPS ADDRESS VALIDATION - FREE SERVICE")
    print("=" * 70)
    print(f"Input file:     {input_file}")
    print(f"Output file:    {output_file}")
    print(f"Progress file:  {progress_file}")
    print(f"Rate limit:     {REQUESTS_PER_SECOND} requests/second")
    print()

    # Read input addresses
    print("Reading input addresses...")
    addresses = read_input_csv(input_file)
    print(f"  ✓ Loaded {len(addresses)} addresses")

    # Load previous progress
    print("Checking for previous progress...")
    previous_results = load_progress(progress_file)
    completed_sequences = {int(r['[sequence]']) for r in previous_results}

    if previous_results:
        print(f"  ✓ Found {len(previous_results)} previously validated addresses")
        print(f"  → Will resume from address #{len(previous_results) + 1}")
    else:
        print("  → Starting fresh validation")
    print()

    # Statistics
    stats = {
        'total': len(addresses),
        'completed': len(previous_results),
        'remaining': len(addresses) - len(previous_results),
        'successful': sum(1 for r in previous_results if r['ValidationFlag'] == 'OK'),
        'failed': sum(1 for r in previous_results if r['ValidationFlag'] == 'ERROR')
    }

    # Start validation
    print("Starting validation...")
    print("-" * 70)
    print(f"Progress: {stats['completed']}/{stats['total']} | Success: {stats['successful']} | Failed: {stats['failed']}")
    print("-" * 70)

    results = previous_results.copy()
    start_time = time.time()

    for i, address in enumerate(addresses, 1):
        sequence = int(address['sequence'])

        # Skip if already validated
        if sequence in completed_sequences:
            continue

        # Validate address
        result = validate_address_usps(USPS_USER_ID, sequence, address)
        results.append(result)

        # Update stats
        stats['completed'] += 1
        stats['remaining'] -= 1
        if result['success'] and result['ValidationFlag'] == 'OK':
            stats['successful'] += 1
        else:
            stats['failed'] += 1

        # Print progress
        if stats['completed'] % 10 == 0:
            elapsed = time.time() - start_time
            rate = stats['completed'] / elapsed if elapsed > 0 else 0
            eta_seconds = stats['remaining'] / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60

            print(f"  [{stats['completed']}/{stats['total']}] "
                  f"Success: {stats['successful']} | Failed: {stats['failed']} | "
                  f"Rate: {rate:.1f}/sec | ETA: {eta_minutes:.1f}min")

            # Save progress every 10 records
            write_output_csv(progress_file, results)

        # Rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Final save
    write_output_csv(output_file, results)
    write_output_csv(progress_file, results)

    # Print final statistics
    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Total addresses:        {stats['total']}")
    print(f"Successfully validated: {stats['successful']}")
    print(f"Failed validation:      {stats['failed']}")
    print(f"Success rate:           {stats['successful']/stats['total']*100:.1f}%")
    print()
    print(f"Output saved to: {output_file}")
    print()
    print("Next step: Run the import script:")
    print("  python3 scripts/import_usps_validation_shipping.py")
    print("=" * 70)

if __name__ == '__main__':
    main()
