#!/usr/bin/env python3
"""
Validate shipping addresses using SmartyStreets API.

SmartyStreets offers:
- Street-level validation (very accurate)
- 250 free lookups/month (no credit card required)
- Pay-as-you-go: $0.007-0.015 per lookup
- Instant setup, no approval process

To get started:
1. Sign up at: https://www.smarty.com/pricing/us-address-verification
2. Get your Auth ID and Auth Token from the dashboard
3. Set environment variables:
   export SMARTY_AUTH_ID='your_auth_id'
   export SMARTY_AUTH_TOKEN='your_auth_token'

This script:
- Validates addresses using SmartyStreets US Street API
- Rate limit: Up to 250/sec (we'll use 10/sec to be safe)
- Saves progress after every 10 records (resumable)
- Returns full USPS data including DPV, geocoding, county, RDI, etc.
"""

import csv
import os
import sys
import time
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# SmartyStreets API Configuration
SMARTY_API_URL = "https://us-street.api.smarty.com/street-address"
SMARTY_AUTH_ID = os.getenv("SMARTY_AUTH_ID", "")
SMARTY_AUTH_TOKEN = os.getenv("SMARTY_AUTH_TOKEN", "")

# Rate limiting: 10 requests per second (conservative)
REQUESTS_PER_SECOND = 10
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

def validate_address_smarty(auth_id, auth_token, sequence, address_data):
    """
    Validate a single address using SmartyStreets US Street API.

    Returns dict with validation results or error information.
    """

    try:
        # Build request parameters
        params = {
            'auth-id': auth_id,
            'auth-token': auth_token,
            'street': address_data['addressline1'],
            'city': address_data['city'],
            'state': address_data['state'],
            'zipcode': address_data['postalcode'][:5],
            'candidates': '1',  # Return best match only
            'match': 'strict'   # Strict matching
        }

        if address_data.get('addressline2'):
            params['street2'] = address_data['addressline2']

        # Make API request
        url = f"{SMARTY_API_URL}?{urlencode(params)}"
        request = Request(url)
        request.add_header('User-Agent', 'StarHouse-CRM/1.0')

        response = urlopen(request, timeout=10)
        response_data = response.read().decode('utf-8')
        results = json.loads(response_data)

        # Check if we got results
        if not results or len(results) == 0:
            return {
                'sequence': sequence,
                'ValidationFlag': 'ERROR',
                '[summary]': 'Address not found',
                'error_message': 'No match found',
                'success': False
            }

        # Parse the first (best) result
        result = results[0]
        components = result.get('components', {})
        metadata = result.get('metadata', {})
        analysis = result.get('analysis', {})

        # Get DPV match code
        dpv_match_code = analysis.get('dpv_match_code', 'N')  # Y, N, S, D
        dpv_vacant = analysis.get('dpv_vacant', 'N')  # Y or N

        # Build delivery lines
        delivery_line_1 = result.get('delivery_line_1', '')
        delivery_line_2 = result.get('delivery_line_2', '')
        last_line = result.get('last_line', '')

        # Get full zipcode
        zip5 = components.get('zipcode', '')
        zip4 = components.get('plus4_code', '')
        if zip4:
            full_zipcode = f"{zip5}-{zip4}"
        else:
            full_zipcode = zip5

        # Get geocoding
        latitude = metadata.get('latitude', '')
        longitude = metadata.get('longitude', '')
        precision = metadata.get('precision', '')  # Zip9, Zip8, Zip7, etc.

        # Get county
        county_name = metadata.get('county_name', '')

        # Get RDI (Residential Delivery Indicator)
        rdi = metadata.get('rdi', '')  # Residential, Commercial, or empty

        # Get footnotes
        footnotes = analysis.get('dpv_footnotes', '')

        # Check if active
        active_flag = analysis.get('active', 'Y')  # Y or N

        # Build notes/summary
        notes_parts = []
        if footnotes:
            notes_parts.append(f"DPV: {footnotes}")
        if analysis.get('dpv_cmra') == 'Y':
            notes_parts.append("CMRA (mail receiving agency)")
        if analysis.get('ews_match') == 'true':
            notes_parts.append("EWS: Early Warning System match")

        notes = '; '.join(notes_parts) if notes_parts else ''

        # Determine validation flag
        validation_flag = 'OK' if dpv_match_code in ['Y', 'S', 'D'] else 'ERROR'

        return {
            '[sequence]': sequence,
            'ValidationFlag': validation_flag,
            '[summary]': f"DPV: {dpv_match_code}",
            '[delivery_line_1]': delivery_line_1,
            '[delivery_line_2]': delivery_line_2,
            '[city_name]': components.get('city_name', ''),
            '[state_abbreviation]': components.get('state_abbreviation', ''),
            '[full_zipcode]': full_zipcode,
            '[notes]': notes,
            '[county_name]': county_name,
            '[rdi]': rdi,
            '[latitude]': str(latitude) if latitude else '',
            '[longitude]': str(longitude) if longitude else '',
            '[precision]': precision,
            '[dpv_match_code]': dpv_match_code,
            '[dpv_vacant]': dpv_vacant,
            '[active]': active_flag,
            '[last_line]': last_line,
            'success': True
        }

    except HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        if e.code == 401:
            error_msg = "Authentication failed - check your auth ID and token"
        elif e.code == 402:
            error_msg = "Payment required - you've exceeded your free tier"
        return {
            '[sequence]': sequence,
            'ValidationFlag': 'ERROR',
            '[summary]': error_msg,
            'error_message': error_msg,
            'success': False
        }

    except (URLError, json.JSONDecodeError) as e:
        return {
            '[sequence]': sequence,
            'ValidationFlag': 'ERROR',
            '[summary]': str(e),
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

    # Check for SmartyStreets credentials
    if not SMARTY_AUTH_ID or not SMARTY_AUTH_TOKEN:
        print("=" * 70)
        print("ERROR: SmartyStreets credentials not set")
        print("=" * 70)
        print()
        print("To use SmartyStreets (250 free lookups/month):")
        print("1. Sign up at: https://www.smarty.com/pricing/us-address-verification")
        print("2. Get your Auth ID and Auth Token from dashboard")
        print("3. Set environment variables:")
        print("   export SMARTY_AUTH_ID='your_auth_id'")
        print("   export SMARTY_AUTH_TOKEN='your_auth_token'")
        print()
        print("Cost after free tier: $0.007-0.015 per lookup")
        print("571 addresses = $4-9 total")
        print()
        print("Alternative: Use USPS Web Tools (free but requires registration)")
        print("Run: python3 scripts/validate_addresses_usps.py")
        sys.exit(1)

    # File paths
    input_file = '/tmp/shipping_addresses_for_validation.csv'
    output_file = '/tmp/shipping_addresses_validated.csv'
    progress_file = '/tmp/smarty_validation_progress.csv'

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
    print("ADDRESS VALIDATION - SMARTYSTREETS")
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
    completed_sequences = {int(r['[sequence]']) for r in previous_results if r.get('[sequence]', '').strip()}

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

    # Estimate cost
    remaining_cost = stats['remaining'] * 0.01  # Assume $0.01 per lookup as upper bound
    print(f"Estimated cost: ${remaining_cost:.2f} (if not using free tier)")
    print()

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
        result = validate_address_smarty(SMARTY_AUTH_ID, SMARTY_AUTH_TOKEN, sequence, address)
        results.append(result)

        # Update stats
        stats['completed'] += 1
        stats['remaining'] -= 1
        if result['success'] and result['ValidationFlag'] == 'OK':
            stats['successful'] += 1
        else:
            stats['failed'] += 1

        # Print progress
        if stats['completed'] % 10 == 0 or not result['success']:
            elapsed = time.time() - start_time
            rate = (stats['completed'] - len(previous_results)) / elapsed if elapsed > 0 else 0
            eta_seconds = stats['remaining'] / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60

            status = "✓" if result['success'] else "✗"
            print(f"  {status} [{stats['completed']}/{stats['total']}] "
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
    elapsed_total = time.time() - start_time
    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Total addresses:        {stats['total']}")
    print(f"Successfully validated: {stats['successful']}")
    print(f"Failed validation:      {stats['failed']}")
    print(f"Success rate:           {stats['successful']/stats['total']*100:.1f}%")
    print(f"Time elapsed:           {elapsed_total/60:.1f} minutes")
    print()
    print(f"Output saved to: {output_file}")
    print()
    print("Next step: Run the import script:")
    print("  python3 scripts/import_usps_validation_shipping.py")
    print("=" * 70)

if __name__ == '__main__':
    main()
