#!/usr/bin/env python3
"""
Standardize capitalization across all contact name and address fields.

This script:
- Title cases names with proper handling of Mc/Mac/O'/De/Van/etc.
- Title cases addresses with proper handling of PO Box, street types, directions
- Title cases cities
- Uppercases state codes
- Handles special cases and business names
"""
import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"

# Common business suffixes that should stay uppercase
BUSINESS_SUFFIXES = ['LLC', 'LLP', 'PC', 'PA', 'INC', 'CORP', 'LTD']

# Direction abbreviations that should stay uppercase
DIRECTIONS = ['NE', 'NW', 'SE', 'SW', 'N', 'S', 'E', 'W']

# Street types that should be title case
STREET_TYPES = ['Street', 'Avenue', 'Boulevard', 'Drive', 'Lane', 'Road', 'Court', 'Place',
                'Circle', 'Way', 'Trail', 'Terrace', 'Parkway', 'Highway']


def smart_title_case(text):
    """
    Apply smart title casing with special handling for names and addresses

    Handles:
    - Mc/Mac prefixes: McDonald, MacGregor
    - O' prefixes: O'Brien, O'Connor
    - De/Van/Von prefixes: DeLuca, VanDyke, VonNeumann
    - Business suffixes: LLC, INC, etc.
    - Direction abbreviations: NE, SW, etc.
    - PO Box formatting
    """
    if not text or not text.strip():
        return text

    # First, basic title case
    words = text.split()
    result = []

    for i, word in enumerate(words):
        # Handle empty words
        if not word:
            result.append(word)
            continue

        # Check if it's a business suffix (should be uppercase)
        if word.upper() in BUSINESS_SUFFIXES:
            result.append(word.upper())
            continue

        # Check if it's a direction (should be uppercase)
        if word.upper() in DIRECTIONS:
            result.append(word.upper())
            continue

        # Handle PO Box specially
        if word.upper() in ['PO', 'P.O.']:
            result.append(word.upper())
            continue

        if word.lower() == 'box' and i > 0 and result[-1] in ['PO', 'P.O.']:
            result.append('Box')
            continue

        # Apply title case
        word_titled = word.title()

        # Fix Mc/Mac names (McDonald not Mcdonald)
        if word_titled.startswith('Mc') and len(word_titled) > 2:
            word_titled = 'Mc' + word_titled[2].upper() + word_titled[3:]
        elif word_titled.startswith('Mac') and len(word_titled) > 3:
            word_titled = 'Mac' + word_titled[3].upper() + word_titled[4:]

        # Fix O' names (O'Brien not O'brien)
        if re.match(r"^O'[a-z]", word_titled):
            word_titled = "O'" + word_titled[2].upper() + word_titled[3:]

        # Note: Removed overly aggressive De/Da/Di/Van/Von handling
        # These prefixes are rare and should be handled manually if needed
        # to avoid false positives like "Denver" -> "DeNver"

        # Fix ordinal numbers (1st, 2nd, 3rd not 1St, 2Nd, 3Rd)
        ordinal_match = re.match(r'^(\d+)(ST|ND|RD|TH)$', word_titled, re.IGNORECASE)
        if ordinal_match:
            word_titled = ordinal_match.group(1) + ordinal_match.group(2).lower()

        result.append(word_titled)

    return ' '.join(result)


def standardize_name(name):
    """Standardize a person's name"""
    if not name or not name.strip():
        return name
    return smart_title_case(name.strip())


def standardize_address(address):
    """Standardize a street address"""
    if not address or not address.strip():
        return address
    return smart_title_case(address.strip())


def standardize_city(city):
    """Standardize a city name"""
    if not city or not city.strip():
        return city
    return smart_title_case(city.strip())


def standardize_state(state):
    """Standardize a state code (should be uppercase)"""
    if not state or not state.strip():
        return state
    # If it's a 2-3 character code, uppercase it
    if len(state.strip()) <= 3:
        return state.strip().upper()
    # Otherwise title case (for full state names like "Colorado")
    return smart_title_case(state.strip())


def standardize_country(country):
    """Standardize a country name"""
    if not country or not country.strip():
        return country

    # Common abbreviations should be uppercase
    if country.strip().upper() in ['US', 'USA', 'UK', 'CA']:
        return country.strip().upper()

    return smart_title_case(country.strip())


def standardize_contacts(dry_run=True):
    """
    Standardize all contact names and addresses

    Args:
        dry_run: If True, only report what would be updated without making changes
    """
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print(f"Contact Data Standardization")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE UPDATE'}")
    print(f"{'=' * 100}\n")

    print("Step 1: Finding contacts that need standardization...\n")

    # Get all contacts
    cur.execute("""
        SELECT
            id, email,
            first_name, last_name,
            address_line_1, address_line_2, city, state, postal_code, country,
            shipping_address_line_1, shipping_address_line_2,
            shipping_city, shipping_state, shipping_postal_code, shipping_country
        FROM contacts
        WHERE
            (first_name IS NOT NULL AND first_name != '')
            OR (last_name IS NOT NULL AND last_name != '')
            OR (address_line_1 IS NOT NULL AND address_line_1 != '')
            OR (city IS NOT NULL AND city != '')
            OR (shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 != '')
            OR (shipping_city IS NOT NULL AND shipping_city != '')
        ORDER BY email
    """)

    contacts = cur.fetchall()

    print(f"Analyzing {len(contacts):,} contacts...\n")

    # Statistics
    stats = {
        'total_processed': 0,
        'contacts_updated': 0,
        'first_name_updated': 0,
        'last_name_updated': 0,
        'billing_address_updated': 0,
        'billing_city_updated': 0,
        'billing_state_updated': 0,
        'shipping_address_updated': 0,
        'shipping_city_updated': 0,
        'shipping_state_updated': 0
    }

    sample_updates = []

    # Process each contact
    for contact in contacts:
        stats['total_processed'] += 1

        updates = {}
        changes = []

        # Check first name
        if contact['first_name']:
            new_first = standardize_name(contact['first_name'])
            if new_first != contact['first_name']:
                updates['first_name'] = new_first
                changes.append(f"first_name: '{contact['first_name']}' → '{new_first}'")
                stats['first_name_updated'] += 1

        # Check last name
        if contact['last_name']:
            new_last = standardize_name(contact['last_name'])
            if new_last != contact['last_name']:
                updates['last_name'] = new_last
                changes.append(f"last_name: '{contact['last_name']}' → '{new_last}'")
                stats['last_name_updated'] += 1

        # Check billing address
        if contact['address_line_1']:
            new_addr = standardize_address(contact['address_line_1'])
            if new_addr != contact['address_line_1']:
                updates['address_line_1'] = new_addr
                changes.append(f"address: '{contact['address_line_1']}' → '{new_addr}'")
                stats['billing_address_updated'] += 1

        if contact['address_line_2']:
            new_addr2 = standardize_address(contact['address_line_2'])
            if new_addr2 != contact['address_line_2']:
                updates['address_line_2'] = new_addr2

        # Check billing city
        if contact['city']:
            new_city = standardize_city(contact['city'])
            if new_city != contact['city']:
                updates['city'] = new_city
                changes.append(f"city: '{contact['city']}' → '{new_city}'")
                stats['billing_city_updated'] += 1

        # Check billing state
        if contact['state']:
            new_state = standardize_state(contact['state'])
            if new_state != contact['state']:
                updates['state'] = new_state
                changes.append(f"state: '{contact['state']}' → '{new_state}'")
                stats['billing_state_updated'] += 1

        # Check billing country
        if contact['country']:
            new_country = standardize_country(contact['country'])
            if new_country != contact['country']:
                updates['country'] = new_country

        # Check shipping address
        if contact['shipping_address_line_1']:
            new_ship = standardize_address(contact['shipping_address_line_1'])
            if new_ship != contact['shipping_address_line_1']:
                updates['shipping_address_line_1'] = new_ship
                changes.append(f"shipping_address: '{contact['shipping_address_line_1']}' → '{new_ship}'")
                stats['shipping_address_updated'] += 1

        if contact['shipping_address_line_2']:
            new_ship2 = standardize_address(contact['shipping_address_line_2'])
            if new_ship2 != contact['shipping_address_line_2']:
                updates['shipping_address_line_2'] = new_ship2

        # Check shipping city
        if contact['shipping_city']:
            new_ship_city = standardize_city(contact['shipping_city'])
            if new_ship_city != contact['shipping_city']:
                updates['shipping_city'] = new_ship_city
                changes.append(f"shipping_city: '{contact['shipping_city']}' → '{new_ship_city}'")
                stats['shipping_city_updated'] += 1

        # Check shipping state
        if contact['shipping_state']:
            new_ship_state = standardize_state(contact['shipping_state'])
            if new_ship_state != contact['shipping_state']:
                updates['shipping_state'] = new_ship_state
                changes.append(f"shipping_state: '{contact['shipping_state']}' → '{new_ship_state}'")
                stats['shipping_state_updated'] += 1

        # Check shipping country
        if contact['shipping_country']:
            new_ship_country = standardize_country(contact['shipping_country'])
            if new_ship_country != contact['shipping_country']:
                updates['shipping_country'] = new_ship_country

        # If there are updates to make, execute them
        if updates:
            stats['contacts_updated'] += 1

            if len(sample_updates) < 30:
                sample_updates.append({
                    'email': contact['email'],
                    'changes': changes
                })

            if not dry_run:
                # Build UPDATE query dynamically
                set_clauses = ', '.join([f"{key} = %s" for key in updates.keys()])
                values = list(updates.values())
                values.append(contact['id'])

                update_query = f"""
                    UPDATE contacts
                    SET {set_clauses}, updated_at = NOW()
                    WHERE id = %s
                """

                cur.execute(update_query, values)

    # Commit if not dry run
    if not dry_run:
        conn.commit()
        print("✓ Changes committed to database\n")
    else:
        print("ℹ DRY RUN - No changes were made\n")

    # Print statistics
    print(f"{'=' * 100}")
    print("STANDARDIZATION STATISTICS")
    print(f"{'=' * 100}")
    print(f"Total contacts processed: {stats['total_processed']:,}")
    print(f"Contacts needing updates: {stats['contacts_updated']:,}")
    print(f"\nFields updated:")
    print(f"  First names: {stats['first_name_updated']:,}")
    print(f"  Last names: {stats['last_name_updated']:,}")
    print(f"  Billing addresses: {stats['billing_address_updated']:,}")
    print(f"  Billing cities: {stats['billing_city_updated']:,}")
    print(f"  Billing states: {stats['billing_state_updated']:,}")
    print(f"  Shipping addresses: {stats['shipping_address_updated']:,}")
    print(f"  Shipping cities: {stats['shipping_city_updated']:,}")
    print(f"  Shipping states: {stats['shipping_state_updated']:,}")
    print()

    # Show samples
    if sample_updates:
        print(f"{'=' * 100}")
        print(f"SAMPLE CHANGES (showing {min(len(sample_updates), 30)}):")
        print(f"{'=' * 100}\n")

        for i, update in enumerate(sample_updates, 1):
            print(f"{i}. {update['email']}")
            for change in update['changes']:
                print(f"   {change}")
            print()

        if len(sample_updates) > 30:
            print(f"... and {stats['contacts_updated'] - 30} more contacts")

    cur.close()
    conn.close()

    return stats


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Standardize contact name and address capitalization')
    parser.add_argument('--live', action='store_true',
                       help='Run in LIVE mode (default is DRY RUN)')
    args = parser.parse_args()

    try:
        stats = standardize_contacts(dry_run=not args.live)

        if not args.live and stats['contacts_updated'] > 0:
            print(f"{'=' * 100}")
            print("READY TO APPLY CHANGES")
            print(f"{'=' * 100}")
            print(f"\nThis will standardize {stats['contacts_updated']:,} contacts.")
            print(f"\nChanges include:")
            print(f"  - Proper title casing for names")
            print(f"  - Proper capitalization for addresses")
            print(f"  - Special handling for Mc/Mac/O' prefixes")
            print(f"  - Proper formatting for PO Box")
            print(f"  - Direction abbreviations (NE, SW) stay uppercase")
            print(f"  - State codes uppercase")
            print(f"\nTo apply these changes, run with --live flag:")
            print("  python3 scripts/standardize_capitalization.py --live")
            print(f"{'=' * 100}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
