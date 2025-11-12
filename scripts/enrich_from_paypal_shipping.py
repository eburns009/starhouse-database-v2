#!/usr/bin/env python3
"""
Enrich Kajabi contacts with shipping addresses from PayPal transaction data.

This script reads the PayPal CSV file and extracts shipping address information
for contacts that don't have address data in the database.

FAANG Quality Standards:
- Dry-run mode by default
- Never overwrites existing address data
- Tracks data provenance (shipping_address_source = 'paypal')
- Idempotent operations
- Comprehensive logging
- Only uses most recent address for each email

Usage:
    python3 scripts/enrich_from_paypal_shipping.py --dry-run
    python3 scripts/enrich_from_paypal_shipping.py --execute
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, level: str = 'INFO') -> None:
    """Log message with timestamp and color."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    colors = {
        'INFO': Colors.BLUE,
        'SUCCESS': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'HEADER': Colors.HEADER,
    }
    color = colors.get(level, '')
    print(f"{color}[{timestamp}] {level}: {message}{Colors.ENDC}")

class ShippingAddress:
    """Data class for shipping address."""

    def __init__(self, line_1: str, line_2: str, city: str, state: str,
                 postal_code: str, country: str, date: str, phone: str = None):
        self.line_1 = line_1.strip() if line_1 else None
        self.line_2 = line_2.strip() if line_2 else None
        self.city = city.strip() if city else None
        self.state = state.strip() if state else None
        self.postal_code = postal_code.strip() if postal_code else None
        self.country = country.strip() if country else None
        self.phone = phone.strip() if phone else None
        self.date = date

    def is_valid(self) -> bool:
        """Check if address has minimum required fields."""
        return bool(self.line_1 and self.city)

    def __repr__(self):
        return f"{self.line_1}, {self.city}, {self.state} {self.postal_code}"

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse PayPal date string to datetime."""
    try:
        return datetime.strptime(date_str, '%m/%d/%Y')
    except:
        return None

def load_shipping_addresses_from_paypal() -> Dict[str, ShippingAddress]:
    """
    Load shipping addresses from PayPal CSV.

    Returns: Dict mapping email -> most recent ShippingAddress
    """
    csv_path = 'kajabi 3 files review/paypal 2024.CSV'
    if not os.path.exists(csv_path):
        log(f"CSV file not found: {csv_path}", 'ERROR')
        sys.exit(1)

    # Track all addresses per email with date
    email_addresses = {}  # email -> List[(date, address)]

    log("Loading PayPal CSV...", 'INFO')

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get customer email
            email = row.get('From Email Address', '').strip().lower()
            if not email:
                continue

            # Get address fields
            line_1 = row.get('Address Line 1', '')
            line_2 = row.get('Address Line 2/District/Neighborhood', '')
            city = row.get('Town/City', '')
            state = row.get('State/Province/Region/County/Territory/Prefecture/Republic', '')
            postal_code = row.get('Zip/Postal Code', '')
            country = row.get('Country', '')
            phone = row.get('Contact Phone Number', '')
            date_str = row.get('Date', '')

            # Skip if no meaningful address data
            if not line_1 and not city:
                continue

            # Parse date
            date = parse_date(date_str)
            if not date:
                continue

            # Create address object
            address = ShippingAddress(
                line_1=line_1,
                line_2=line_2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                date=date,
                phone=phone
            )

            if not address.is_valid():
                continue

            # Track this address with date
            if email not in email_addresses:
                email_addresses[email] = []
            email_addresses[email].append((date, address))

    # For each email, keep only the most recent address
    most_recent = {}
    for email, addresses in email_addresses.items():
        # Sort by date descending and take most recent
        addresses.sort(key=lambda x: x[0], reverse=True)
        most_recent[email] = addresses[0][1]

    log(f"Loaded shipping addresses for {len(most_recent)} unique emails", 'SUCCESS')
    return most_recent

def get_kajabi_contacts_without_addresses(cursor) -> List[Dict]:
    """Get Kajabi contacts that don't have address data."""
    cursor.execute("""
        SELECT
            id,
            email,
            first_name,
            last_name,
            address_line_1,
            shipping_address_line_1,
            phone
        FROM contacts
        WHERE source_system = 'kajabi'
          AND (address_line_1 IS NULL OR address_line_1 = '')
          AND (shipping_address_line_1 IS NULL OR shipping_address_line_1 = '')
          AND deleted_at IS NULL
        ORDER BY email
    """)

    contacts = cursor.fetchall()
    log(f"Found {len(contacts)} Kajabi contacts without addresses", 'INFO')
    return contacts

def enrich_contacts(shipping_addresses: Dict[str, ShippingAddress], dry_run: bool) -> Dict:
    """Enrich contacts with shipping addresses from PayPal."""
    log(f"\n{'='*80}", 'HEADER')
    log(f"ENRICHMENT MODE: {'DRY-RUN' if dry_run else 'EXECUTE'}", 'HEADER')
    log(f"{'='*80}\n", 'HEADER')

    # Connect to database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        log("DATABASE_URL not set", 'ERROR')
        sys.exit(1)

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    results = {
        'total_missing_addresses': 0,
        'paypal_addresses_available': len(shipping_addresses),
        'enriched_address': 0,
        'enriched_phone': 0,
        'no_match': 0,
        'details': []
    }

    try:
        # Get contacts without addresses
        contacts = get_kajabi_contacts_without_addresses(cursor)
        results['total_missing_addresses'] = len(contacts)

        if not contacts:
            log("No contacts need address enrichment", 'INFO')
            return results

        log(f"\nProcessing {len(contacts)} contacts...\n", 'INFO')

        for contact in contacts:
            email = contact['email'].lower()

            # Check if shipping address available
            if email not in shipping_addresses:
                results['no_match'] += 1
                continue

            address = shipping_addresses[email]

            # Prepare update
            updates = []
            params = []

            # Add shipping address fields
            updates.append("shipping_address_line_1 = %s")
            params.append(address.line_1)

            updates.append("shipping_address_line_2 = %s")
            params.append(address.line_2)

            updates.append("shipping_city = %s")
            params.append(address.city)

            updates.append("shipping_state = %s")
            params.append(address.state)

            updates.append("shipping_postal_code = %s")
            params.append(address.postal_code)

            updates.append("shipping_country = %s")
            params.append(address.country)

            updates.append("shipping_address_source = %s")
            params.append('paypal')

            updates.append("shipping_address_updated_at = NOW()")

            # Also enrich phone if contact doesn't have one
            enrich_phone = False
            if address.phone and (not contact['phone'] or contact['phone'] == ''):
                updates.append("phone = %s")
                params.append(address.phone)
                updates.append("phone_source = %s")
                params.append('paypal_shipping')
                enrich_phone = True

            updates.append("updated_at = NOW()")

            # Add WHERE clause params
            params.append(contact['id'])

            # Perform update
            if not dry_run:
                query = f"""
                    UPDATE contacts
                    SET {', '.join(updates)}
                    WHERE id = %s
                      AND (shipping_address_line_1 IS NULL OR shipping_address_line_1 = '')
                      AND deleted_at IS NULL
                """
                cursor.execute(query, params)

                if cursor.rowcount == 0:
                    log(f"⊘ Race condition for {email}", 'WARNING')
                    continue

            results['enriched_address'] += 1
            if enrich_phone:
                results['enriched_phone'] += 1

            results['details'].append({
                'email': email,
                'name': f"{contact['first_name']} {contact['last_name']}",
                'address': str(address),
                'phone_added': enrich_phone,
                'phone': address.phone if enrich_phone else None
            })

            if results['enriched_address'] % 100 == 0:
                log(f"✓ Enriched {results['enriched_address']} contacts...", 'INFO')

        # Commit changes
        if not dry_run:
            conn.commit()
            log(f"\n✓ Changes committed to database", 'SUCCESS')
        else:
            conn.rollback()
            log(f"\n⊘ Dry-run complete - no changes made", 'INFO')

    except Exception as e:
        conn.rollback()
        log(f"Error during enrichment: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    return results

def print_summary(results: Dict, dry_run: bool) -> None:
    """Print enrichment summary."""
    log(f"\n{'='*80}", 'HEADER')
    log(f"PAYPAL SHIPPING ENRICHMENT SUMMARY ({'DRY-RUN' if dry_run else 'EXECUTED'})", 'HEADER')
    log(f"{'='*80}", 'HEADER')

    log(f"Total Kajabi contacts without addresses: {results['total_missing_addresses']}", 'INFO')
    log(f"PayPal shipping addresses available: {results['paypal_addresses_available']}", 'INFO')
    log(f"✓ Contacts enriched with address: {results['enriched_address']}", 'SUCCESS')
    log(f"✓ Contacts also enriched with phone: {results['enriched_phone']}", 'SUCCESS')
    log(f"⊘ No PayPal data available: {results['no_match']}", 'WARNING')

    if results['enriched_address'] > 0:
        improvement_pct = (results['enriched_address'] / results['total_missing_addresses'] * 100) if results['total_missing_addresses'] > 0 else 0
        log(f"\n📈 Coverage improvement: {improvement_pct:.1f}%", 'SUCCESS')

        # Show sample enrichments
        log(f"\n{'='*80}", 'HEADER')
        log("SAMPLE ENRICHMENTS (first 10):", 'HEADER')
        log(f"{'='*80}", 'HEADER')

        for detail in results['details'][:10]:
            log(f"\n✓ {detail['name']} ({detail['email']})", 'SUCCESS')
            log(f"  Address: {detail['address']}", 'INFO')
            if detail['phone_added']:
                log(f"  Phone: {detail['phone']}", 'INFO')

        if len(results['details']) > 10:
            log(f"\n... and {len(results['details']) - 10} more", 'INFO')

    log(f"\n{'='*80}\n", 'HEADER')

def main():
    """Main execution function."""
    # Parse arguments
    dry_run = True
    if len(sys.argv) > 1:
        if sys.argv[1] == '--execute':
            dry_run = False
        elif sys.argv[1] == '--dry-run':
            dry_run = True
        else:
            log("Usage: python3 scripts/enrich_from_paypal_shipping.py [--dry-run|--execute]", 'ERROR')
            sys.exit(1)

    # Load shipping addresses from PayPal
    shipping_addresses = load_shipping_addresses_from_paypal()

    # Enrich contacts
    results = enrich_contacts(shipping_addresses, dry_run)

    # Print summary
    print_summary(results, dry_run)

    # Save results
    if results['enriched_address'] > 0:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode = 'dryrun' if dry_run else 'execute'
        output_file = f"paypal_shipping_enrichment_{mode}_{timestamp}.json"

        import json
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'mode': mode,
                'results': results
            }, f, indent=2, default=str)

        log(f"Report saved to: {output_file}", 'SUCCESS')

    if dry_run:
        log("\n⚠️  Run with --execute to apply changes", 'WARNING')

if __name__ == '__main__':
    main()
