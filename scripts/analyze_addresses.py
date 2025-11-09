#!/usr/bin/env python3
"""
Analyze contact addresses to identify:
1. Physical addresses vs mailing addresses (PO Boxes)
2. Billing vs shipping addresses
3. Differences between billing and shipping
"""
import re
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = "***REMOVED***"


def is_po_box(address_line):
    """Check if an address line is a PO Box"""
    if not address_line:
        return False

    address_upper = address_line.upper()
    # Common PO Box patterns
    po_box_patterns = [
        r'\bP\.?\s*O\.?\s*BOX\b',
        r'\bPOB\b',
        r'\bPOST\s+OFFICE\s+BOX\b',
        r'\bBOX\s+\d+',
        r'^\s*BOX\b',
    ]

    for pattern in po_box_patterns:
        if re.search(pattern, address_upper):
            return True
    return False


def addresses_match(addr1_line1, addr1_line2, addr1_city, addr1_state, addr1_zip,
                   addr2_line1, addr2_line2, addr2_city, addr2_state, addr2_zip):
    """Check if two addresses match (normalized comparison)"""
    def normalize(s):
        if not s:
            return ''
        return s.upper().strip()

    return (normalize(addr1_line1) == normalize(addr2_line1) and
            normalize(addr1_line2) == normalize(addr2_line2) and
            normalize(addr1_city) == normalize(addr2_city) and
            normalize(addr1_state) == normalize(addr2_state) and
            normalize(addr1_zip) == normalize(addr2_zip))


def analyze_addresses():
    """Analyze all contact addresses"""
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print("CONTACT ADDRESS ANALYSIS")
    print(f"{'=' * 100}\n")

    # Get all contacts with address data
    cur.execute("""
        SELECT
            id,
            email,
            first_name,
            last_name,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country,
            shipping_address_line_1,
            shipping_address_line_2,
            shipping_city,
            shipping_state,
            shipping_postal_code,
            shipping_country,
            billing_address_source,
            shipping_address_source
        FROM contacts
        WHERE
            address_line_1 IS NOT NULL
            OR shipping_address_line_1 IS NOT NULL
        ORDER BY email
    """)

    contacts = cur.fetchall()

    # Statistics
    stats = {
        'total_contacts': 0,
        'with_billing_address': 0,
        'with_shipping_address': 0,
        'with_both_addresses': 0,
        'billing_po_box': 0,
        'billing_physical': 0,
        'shipping_po_box': 0,
        'shipping_physical': 0,
        'addresses_match': 0,
        'addresses_different': 0,
        'only_billing': 0,
        'only_shipping': 0,
    }

    # Detailed lists
    po_box_billing_samples = []
    po_box_shipping_samples = []
    different_addresses_samples = []
    billing_po_shipping_physical = []

    cur.execute("SELECT COUNT(*) as total FROM contacts")
    total_in_db = cur.fetchone()['total']
    stats['total_contacts'] = total_in_db

    for contact in contacts:
        has_billing = bool(contact['address_line_1'])
        has_shipping = bool(contact['shipping_address_line_1'])

        if has_billing:
            stats['with_billing_address'] += 1

            if is_po_box(contact['address_line_1']):
                stats['billing_po_box'] += 1
                if len(po_box_billing_samples) < 10:
                    po_box_billing_samples.append({
                        'email': contact['email'],
                        'address': contact['address_line_1'],
                        'city': contact['city'],
                        'state': contact['state']
                    })
            else:
                stats['billing_physical'] += 1

        if has_shipping:
            stats['with_shipping_address'] += 1

            if is_po_box(contact['shipping_address_line_1']):
                stats['shipping_po_box'] += 1
                if len(po_box_shipping_samples) < 10:
                    po_box_shipping_samples.append({
                        'email': contact['email'],
                        'address': contact['shipping_address_line_1'],
                        'city': contact['shipping_city'],
                        'state': contact['shipping_state']
                    })
            else:
                stats['shipping_physical'] += 1

        if has_billing and has_shipping:
            stats['with_both_addresses'] += 1

            if addresses_match(
                contact['address_line_1'], contact['address_line_2'],
                contact['city'], contact['state'], contact['postal_code'],
                contact['shipping_address_line_1'], contact['shipping_address_line_2'],
                contact['shipping_city'], contact['shipping_state'], contact['shipping_postal_code']
            ):
                stats['addresses_match'] += 1
            else:
                stats['addresses_different'] += 1
                if len(different_addresses_samples) < 10:
                    different_addresses_samples.append({
                        'email': contact['email'],
                        'billing': f"{contact['address_line_1']}, {contact['city']}, {contact['state']} {contact['postal_code']}",
                        'shipping': f"{contact['shipping_address_line_1']}, {contact['shipping_city']}, {contact['shipping_state']} {contact['shipping_postal_code']}"
                    })

                # Special case: billing is PO Box but shipping is physical
                if is_po_box(contact['address_line_1']) and not is_po_box(contact['shipping_address_line_1']):
                    if len(billing_po_shipping_physical) < 10:
                        billing_po_shipping_physical.append({
                            'email': contact['email'],
                            'billing': contact['address_line_1'],
                            'shipping': contact['shipping_address_line_1']
                        })

        elif has_billing and not has_shipping:
            stats['only_billing'] += 1
        elif has_shipping and not has_billing:
            stats['only_shipping'] += 1

    # Print statistics
    print(f"{'=' * 100}")
    print("OVERALL STATISTICS")
    print(f"{'=' * 100}")
    print(f"Total contacts in database: {stats['total_contacts']:,}")
    print(f"Contacts with billing address: {stats['with_billing_address']:,} ({stats['with_billing_address']/stats['total_contacts']*100:.1f}%)")
    print(f"Contacts with shipping address: {stats['with_shipping_address']:,} ({stats['with_shipping_address']/stats['total_contacts']*100:.1f}%)")
    print(f"Contacts without any address: {stats['total_contacts'] - len(contacts):,}")
    print()

    print(f"{'=' * 100}")
    print("ADDRESS TYPE BREAKDOWN")
    print(f"{'=' * 100}")
    print(f"\nBilling Addresses:")
    print(f"  Physical addresses: {stats['billing_physical']:,} ({stats['billing_physical']/max(stats['with_billing_address'], 1)*100:.1f}%)")
    print(f"  PO Boxes: {stats['billing_po_box']:,} ({stats['billing_po_box']/max(stats['with_billing_address'], 1)*100:.1f}%)")

    print(f"\nShipping Addresses:")
    print(f"  Physical addresses: {stats['shipping_physical']:,} ({stats['shipping_physical']/max(stats['with_shipping_address'], 1)*100:.1f}%)")
    print(f"  PO Boxes: {stats['shipping_po_box']:,} ({stats['shipping_po_box']/max(stats['with_shipping_address'], 1)*100:.1f}%)")
    print()

    print(f"{'=' * 100}")
    print("BILLING vs SHIPPING COMPARISON")
    print(f"{'=' * 100}")
    print(f"Contacts with both addresses: {stats['with_both_addresses']:,}")
    print(f"  Addresses match: {stats['addresses_match']:,} ({stats['addresses_match']/max(stats['with_both_addresses'], 1)*100:.1f}%)")
    print(f"  Addresses different: {stats['addresses_different']:,} ({stats['addresses_different']/max(stats['with_both_addresses'], 1)*100:.1f}%)")
    print(f"\nContacts with only billing address: {stats['only_billing']:,}")
    print(f"Contacts with only shipping address: {stats['only_shipping']:,}")
    print()

    # Print samples
    if po_box_billing_samples:
        print(f"{'=' * 100}")
        print("SAMPLE BILLING ADDRESSES - PO BOXES (first 10)")
        print(f"{'=' * 100}")
        for i, sample in enumerate(po_box_billing_samples, 1):
            print(f"{i}. {sample['email']}")
            print(f"   {sample['address']}, {sample['city']}, {sample['state']}")
        print()

    if po_box_shipping_samples:
        print(f"{'=' * 100}")
        print("SAMPLE SHIPPING ADDRESSES - PO BOXES (first 10)")
        print(f"{'=' * 100}")
        for i, sample in enumerate(po_box_shipping_samples, 1):
            print(f"{i}. {sample['email']}")
            print(f"   {sample['address']}, {sample['city']}, {sample['state']}")
        print()

    if different_addresses_samples:
        print(f"{'=' * 100}")
        print("SAMPLE DIFFERENT BILLING vs SHIPPING (first 10)")
        print(f"{'=' * 100}")
        for i, sample in enumerate(different_addresses_samples, 1):
            print(f"{i}. {sample['email']}")
            print(f"   Billing:  {sample['billing']}")
            print(f"   Shipping: {sample['shipping']}")
            print()

    if billing_po_shipping_physical:
        print(f"{'=' * 100}")
        print("CONTACTS WITH PO BOX BILLING + PHYSICAL SHIPPING (first 10)")
        print(f"{'=' * 100}")
        print("These contacts likely want mail at PO Box but packages at home")
        for i, sample in enumerate(billing_po_shipping_physical, 1):
            print(f"{i}. {sample['email']}")
            print(f"   Billing (PO Box): {sample['billing']}")
            print(f"   Shipping (Physical): {sample['shipping']}")
            print()

    cur.close()
    conn.close()

    return stats


if __name__ == '__main__':
    try:
        analyze_addresses()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
