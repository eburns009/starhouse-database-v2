#!/usr/bin/env python3
"""
Validate Google Contacts addresses using SmartyStreets API
FAANG-Grade Implementation: Safe, efficient, auditable

Prioritizes validating the 69 newly imported Google Contacts addresses
and optionally other billing addresses that need validation.

SmartyStreets Setup:
1. Sign up at: https://www.smarty.com/pricing/us-address-verification
2. Free tier: 250 lookups/month (no credit card required)
3. Set environment variables:
   export SMARTY_AUTH_ID='your_auth_id'
   export SMARTY_AUTH_TOKEN='your_auth_token'
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import time
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime
from db_config import get_database_url

# Configuration
SMARTY_API_URL = "https://us-street.api.smarty.com/street-address"
SMARTY_AUTH_ID = os.getenv("SMARTY_AUTH_ID", "")
SMARTY_AUTH_TOKEN = os.getenv("SMARTY_AUTH_TOKEN", "")
REQUESTS_PER_SECOND = 5  # Conservative rate limit
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

DRY_RUN = True  # Set via --live flag

def validate_address_smarty(auth_id, auth_token, address_data):
    """Validate a single address using SmartyStreets"""

    try:
        # Build request parameters
        params = {
            'auth-id': auth_id,
            'auth-token': auth_token,
            'street': address_data['street'],
            'candidates': '1',
            'match': 'strict'
        }

        # Add optional fields
        if address_data.get('city'):
            params['city'] = address_data['city']
        if address_data.get('state'):
            params['state'] = address_data['state']
        if address_data.get('postal_code'):
            # Extract just 5-digit ZIP
            import re
            match = re.search(r'(\d{5})', address_data['postal_code'])
            if match:
                params['zipcode'] = match.group(1)

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
                'success': False,
                'dpv_match_code': 'N',
                'error': 'No match found'
            }

        # Parse first (best) result
        result = results[0]
        components = result.get('components', {})
        metadata = result.get('metadata', {})
        analysis = result.get('analysis', {})

        # Build validated address data
        validated = {
            'success': True,
            'delivery_line_1': result.get('delivery_line_1', ''),
            'delivery_line_2': result.get('delivery_line_2', ''),
            'last_line': result.get('last_line', ''),
            'city': components.get('city_name', ''),
            'state': components.get('state_abbreviation', ''),
            'postal_code': components.get('zipcode', ''),
            'zip4': components.get('plus4_code', ''),
            'county': metadata.get('county_name', ''),
            'latitude': metadata.get('latitude'),
            'longitude': metadata.get('longitude'),
            'precision': metadata.get('precision', ''),
            'rdi': metadata.get('rdi', ''),  # Residential/Commercial
            'dpv_match_code': analysis.get('dpv_match_code', 'N'),  # Y/S/D/N
            'dpv_vacant': analysis.get('dpv_vacant', 'N') == 'Y',
            'active': analysis.get('active', 'Y') == 'Y',
            'dpv_footnotes': analysis.get('dpv_footnotes', '')
        }

        return validated

    except HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        if e.code == 401:
            error_msg = "Authentication failed - check your auth ID and token"
        elif e.code == 402:
            error_msg = "Payment required - exceeded free tier"
        return {'success': False, 'error': error_msg}

    except (URLError, json.JSONDecodeError, Exception) as e:
        return {'success': False, 'error': str(e)}

def validate_google_addresses(dry_run=True):
    """Main validation function"""

    print("=" * 80)
    print("GOOGLE CONTACTS ADDRESS VALIDATION - SMARTYSTREETS")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (validation will be committed)'}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Check for credentials
    if not SMARTY_AUTH_ID or not SMARTY_AUTH_TOKEN:
        print("⚠️  ERROR: SmartyStreets credentials not set\n")
        print("To use SmartyStreets (250 free lookups/month):")
        print("1. Sign up: https://www.smarty.com/pricing/us-address-verification")
        print("2. Get Auth ID and Token from dashboard")
        print("3. Set environment variables:")
        print("   export SMARTY_AUTH_ID='your_auth_id'")
        print("   export SMARTY_AUTH_TOKEN='your_auth_token'")
        print("\nCost after free tier: $0.007-0.015 per lookup")
        print("69 addresses = ~$0.48-1.04 total\n")
        sys.exit(1)

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.lnagadkqejnopgfxwlkb',
        password=get_database_url().split('@')[0].split(':')[-1],
        host='aws-1-us-east-2.pooler.supabase.com',
        port='5432'
    )
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("   Connected ✓\n")

    # Get addresses to validate (prioritize Google Contacts)
    print("📊 Loading addresses for validation...")

    # Priority 1: Google Contacts addresses (not yet validated)
    cur.execute("""
        SELECT id, email, address_line_1, address_line_2, city, state, postal_code, country,
               billing_address_source, billing_usps_validated_at
        FROM contacts
        WHERE billing_address_source = 'google_contacts'
          AND address_line_1 IS NOT NULL
          AND billing_usps_validated_at IS NULL
        ORDER BY updated_at DESC
    """)
    google_addresses = cur.fetchall()

    # Priority 2: Other unvalidated billing addresses (if we want to validate more)
    cur.execute("""
        SELECT id, email, address_line_1, address_line_2, city, state, postal_code, country,
               billing_address_source, billing_usps_validated_at
        FROM contacts
        WHERE billing_address_source != 'google_contacts'
          AND address_line_1 IS NOT NULL
          AND billing_usps_validated_at IS NULL
        LIMIT 50
    """)
    other_addresses = cur.fetchall()

    print(f"   Google Contacts addresses: {len(google_addresses):,}")
    print(f"   Other unvalidated addresses: {len(other_addresses):,}")
    print(f"   Total to validate: {len(google_addresses):,} (focusing on Google only)\n")

    if not google_addresses:
        print("✓ No Google Contacts addresses need validation!\n")
        cur.close()
        conn.close()
        return

    # Statistics
    stats = {
        'total': len(google_addresses),
        'validated': 0,
        'valid': 0,
        'invalid': 0,
        'errors': 0
    }

    # Estimate cost
    cost_estimate = len(google_addresses) * 0.015  # Upper bound
    print(f"Estimated cost: ${cost_estimate:.2f} (max, likely less with free tier)\n")

    if not dry_run:
        print(f"⚠️  This will validate {len(google_addresses)} addresses")
        print("Continue? (Press Ctrl+C to cancel)\n")
        time.sleep(2)

    # Validate each address
    print("🔍 Validating addresses...")
    print("-" * 80)

    start_time = time.time()
    updates = []

    for i, contact in enumerate(google_addresses, 1):
        # Build address data
        address_data = {
            'street': contact['address_line_1'],
            'city': contact['city'],
            'state': contact['state'],
            'postal_code': contact['postal_code']
        }

        # Validate
        result = validate_address_smarty(SMARTY_AUTH_ID, SMARTY_AUTH_TOKEN, address_data)

        stats['validated'] += 1

        if result['success']:
            # Check DPV match code
            dpv = result['dpv_match_code']
            if dpv in ['Y', 'S', 'D']:  # Y=Match, S=Missing secondary, D=Missing both
                stats['valid'] += 1
                status = "✓"
            else:
                stats['invalid'] += 1
                status = "⚠"
        else:
            stats['errors'] += 1
            status = "✗"

        # Store update
        update = {
            'contact_id': contact['id'],
            'email': contact['email'],
            'result': result
        }
        updates.append(update)

        # Print progress
        if i % 10 == 0 or not result['success']:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = stats['total'] - i
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60

            print(f"  {status} [{i}/{stats['total']}] {contact['email'][:30]:<30} "
                  f"Valid: {stats['valid']} | Invalid: {stats['invalid']} | "
                  f"Rate: {rate:.1f}/sec | ETA: {eta_minutes:.1f}min")

        # Rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Apply updates to database
    if not dry_run and updates:
        print("\n" + "=" * 80)
        print("UPDATING DATABASE")
        print("=" * 80)

        try:
            update_count = 0

            for update in updates:
                result = update['result']

                if not result['success']:
                    # Just mark as validated with error
                    cur.execute("""
                        UPDATE contacts
                        SET billing_usps_validated_at = now(),
                            updated_at = now()
                        WHERE id = %s
                    """, (update['contact_id'],))
                    continue

                # Update with full validation data
                cur.execute("""
                    UPDATE contacts
                    SET
                        billing_usps_validated_at = now(),
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
                        updated_at = now()
                    WHERE id = %s
                """, (
                    result['dpv_match_code'],
                    result['precision'],
                    result['delivery_line_1'],
                    result['delivery_line_2'],
                    result['last_line'],
                    result.get('latitude'),
                    result.get('longitude'),
                    result['county'],
                    result['rdi'],
                    result['dpv_footnotes'],
                    result['dpv_vacant'],
                    result['active'],
                    update['contact_id']
                ))

                update_count += 1

                if update_count % 25 == 0:
                    print(f"   Processed {update_count:,} / {len(updates):,} contacts...")

            conn.commit()
            print(f"\n✓ Successfully updated {update_count:,} contacts")

        except Exception as e:
            print(f"\n❌ Error during update: {e}")
            conn.rollback()
            print("✓ Transaction rolled back, no changes made")

    else:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes made")
        print("=" * 80)
        print("\nTo execute validation, run:")
        print("  python3 scripts/validate_google_addresses_smarty.py --live")

    # Print summary
    elapsed_total = time.time() - start_time

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total addresses validated: {stats['validated']:,}")
    print(f"  ✓ Valid (deliverable):   {stats['valid']:,} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"  ⚠ Invalid:               {stats['invalid']:,} ({stats['invalid']/stats['total']*100:.1f}%)")
    print(f"  ✗ Errors:                {stats['errors']:,}")
    print(f"\nTime elapsed: {elapsed_total/60:.1f} minutes")
    print(f"Rate: {stats['validated']/elapsed_total:.1f} addresses/second")
    print("=" * 80)

    # Cleanup
    cur.close()
    conn.close()

    return stats

if __name__ == '__main__':
    # Check for --live flag
    dry_run = '--live' not in sys.argv

    if not dry_run:
        print("\n⚠️  WARNING: Running in LIVE mode. Validation will be committed!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    stats = validate_google_addresses(dry_run=dry_run)
