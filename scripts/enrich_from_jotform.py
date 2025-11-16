#!/usr/bin/env python3
"""
FAANG-Quality JotForm Contact Enrichment
Systematically import and enrich contact data from all JotForm exports
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import re
from decimal import Decimal

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

JOTFORM_FILES = [
    '2022_Donation_.csv',
    '2024_End_of_Year_Donation.csv',
    '30th_Birthday.csv',
    'Donation_Acknowledgement.csv',
    'GivingTuesday.csv',
    'Hosting_an_Event_at_the_StarHouse_.csv',
    'How_did_you_hear_about_the_StarHouse_.csv',
    'StarHouse_Donation.csv',
    'StarHouse_Silent_Auction_Bidding_.csv',
    '_One_Time_Donation_and_or_Subscription_.csv',
]

JOTFORM_DIR = './kajabi 3 files review/Jotform'


def normalize_email(email):
    """Normalize email address."""
    if not email:
        return None
    return email.lower().strip()


def parse_phone(phone):
    """Normalize phone number."""
    if not phone:
        return None
    # Remove common separators
    phone = re.sub(r'[^\d+]', '', phone.strip())
    return phone if phone else None


def parse_paypal_payer_address(address_field):
    """Parse PayPal payer address field into components."""
    if not address_field:
        return {}

    result = {}

    # Extract components using regex
    name_match = re.search(r'Name:\s*([^S][^:]*?)(?=\s*(?:Street|$))', address_field)
    street_match = re.search(r'Street:\s*([^C][^:]*?)(?=\s*(?:City|$))', address_field)
    city_match = re.search(r'City:\s*([^S][^:]*?)(?=\s*(?:State|$))', address_field)
    state_match = re.search(r'State/Region:\s*([^Z][^:]*?)(?=\s*(?:Zip|$))', address_field)
    zip_match = re.search(r'Zip/Postal:\s*([^C][^:]*?)(?=\s*(?:Country|$))', address_field)
    country_match = re.search(r'Country:\s*(.+?)$', address_field)

    if street_match:
        result['street'] = street_match.group(1).strip()
    if city_match:
        result['city'] = city_match.group(1).strip()
    if state_match:
        result['state'] = state_match.group(1).strip()
    if zip_match:
        result['zip'] = zip_match.group(1).strip()
    if country_match:
        result['country'] = country_match.group(1).strip()

    return result


def parse_paypal_payer_info(payer_field):
    """Parse PayPal payer info field."""
    if not payer_field:
        return {}

    result = {}

    first_name_match = re.search(r'First Name:\s*([^L][^:]*?)(?=\s*(?:Last|Transaction|Email|$))', payer_field)
    last_name_match = re.search(r'Last Name:\s*([^T][^:]*?)(?=\s*(?:Transaction|Email|$))', payer_field)
    txn_match = re.search(r'Transaction ID:\s*([A-Z0-9]+)', payer_field)
    email_match = re.search(r'Email:\s*([^\s]+@[^\s]+)', payer_field)

    if first_name_match:
        result['first_name'] = first_name_match.group(1).strip()
    if last_name_match:
        result['last_name'] = last_name_match.group(1).strip()
    if txn_match:
        result['transaction_id'] = txn_match.group(1).strip()
    if email_match:
        result['email'] = email_match.group(1).strip()

    return result


def get_or_create_contact(cursor, email, first_name=None, last_name=None):
    """Get existing contact or create placeholder for new contact."""
    email = normalize_email(email)
    if not email:
        return None

    # Try to find existing contact
    cursor.execute("""
        SELECT id, first_name, last_name
        FROM contacts
        WHERE email = %s
        LIMIT 1
    """, (email,))

    contact = cursor.fetchone()

    if contact:
        return contact['id']

    # Create new contact (use 'manual' as source_system since 'jotform' is not allowed)
    cursor.execute("""
        INSERT INTO contacts (email, first_name, last_name, source_system, created_at, updated_at)
        VALUES (%s, %s, %s, 'manual', NOW(), NOW())
        RETURNING id
    """, (email, first_name, last_name))

    new_id = cursor.fetchone()['id']
    print(f"  ✨ Created new contact: {first_name} {last_name} ({email})")
    return new_id


def enrich_contact_data(cursor, contact_id, data):
    """Enrich existing contact with new data."""
    updates = []
    params = []

    # Phone number
    if data.get('phone'):
        phone = parse_phone(data['phone'])
        if phone:
            updates.append("phone = COALESCE(phone, %s)")
            params.append(phone)

    # Business info
    if data.get('business_name'):
        updates.append("paypal_business_name = COALESCE(paypal_business_name, %s)")
        params.append(data['business_name'])

    # Address data (billing)
    if data.get('street'):
        updates.append("address_line_1 = COALESCE(address_line_1, %s)")
        params.append(data['street'])
    if data.get('city'):
        updates.append("city = COALESCE(city, %s)")
        params.append(data['city'])
    if data.get('state'):
        updates.append("state = COALESCE(state, %s)")
        params.append(data['state'])
    if data.get('postal_code'):
        updates.append("postal_code = COALESCE(postal_code, %s)")
        params.append(data['postal_code'])

    # Shipping address if different
    if data.get('shipping_street'):
        updates.append("shipping_address_line_1 = COALESCE(shipping_address_line_1, %s)")
        params.append(data['shipping_street'])
    if data.get('shipping_city'):
        updates.append("shipping_city = COALESCE(shipping_city, %s)")
        params.append(data['shipping_city'])
    if data.get('shipping_state'):
        updates.append("shipping_state = COALESCE(shipping_state, %s)")
        params.append(data['shipping_state'])
    if data.get('shipping_postal_code'):
        updates.append("shipping_postal_code = COALESCE(shipping_postal_code, %s)")
        params.append(data['shipping_postal_code'])

    if updates:
        params.append(contact_id)
        query = f"""
            UPDATE contacts
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, params)
        return True

    return False


def process_donation_file(cursor, filepath, filename):
    """Process donation-related JotForm files."""
    print(f"\n📄 Processing: {filename}")

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"   Found {len(rows)} submissions")

    enriched_count = 0
    new_contacts = 0
    donations_added = 0

    for row in rows:
        # Extract email
        email = normalize_email(
            row.get('Email') or row.get('Your E-mail') or row.get('E-mail')
        )

        if not email:
            continue

        # Extract names
        first_name = row.get('First Name', '').strip()
        last_name = row.get('Last Name', '').strip()

        # Get or create contact
        contact_id = get_or_create_contact(cursor, email, first_name, last_name)
        if not contact_id:
            continue

        # Prepare enrichment data
        enrichment_data = {}

        # Phone
        if row.get('Phone Number'):
            enrichment_data['phone'] = row['Phone Number']

        # Business
        if row.get('Business Name'):
            enrichment_data['business_name'] = row['Business Name']

        # Manual address fields (from some forms)
        if row.get('Street Address'):
            enrichment_data['street'] = row['Street Address']
        if row.get('City'):
            enrichment_data['city'] = row['City']
        if row.get('State') or row.get('State / Province'):
            enrichment_data['state'] = row.get('State') or row.get('State / Province')
        if row.get('Postal / Zip Code') or row.get('Zip Code'):
            enrichment_data['postal_code'] = row.get('Postal / Zip Code') or row.get('Zip Code')

        # PayPal payer address (shipping)
        for col in row.keys():
            if 'Payer Address' in col and row[col]:
                addr = parse_paypal_payer_address(row[col])
                if addr:
                    enrichment_data['shipping_street'] = addr.get('street')
                    enrichment_data['shipping_city'] = addr.get('city')
                    enrichment_data['shipping_state'] = addr.get('state')
                    enrichment_data['shipping_postal_code'] = addr.get('zip')
                break

        # Enrich contact
        if enrich_contact_data(cursor, contact_id, enrichment_data):
            enriched_count += 1

        # Extract donation/transaction data
        amount = None
        if row.get('Amount (hidden)'):
            try:
                amount = Decimal(row['Amount (hidden)'])
            except:
                pass
        elif row.get('Donation Amount'):
            try:
                amount = Decimal(row['Donation Amount'])
            except:
                pass

        # PayPal transaction ID
        txn_id = None
        for col in row.keys():
            if 'Payer Info' in col and row[col]:
                payer_info = parse_paypal_payer_info(row[col])
                txn_id = payer_info.get('transaction_id')
                break

        # Create transaction if we have amount and it doesn't exist
        if amount and txn_id:
            # Check if transaction exists
            cursor.execute("""
                SELECT id FROM transactions
                WHERE external_transaction_id = %s
            """, (txn_id,))

            if not cursor.fetchone():
                # Parse submission date
                submission_date = None
                if row.get('Submission Date'):
                    try:
                        submission_date = datetime.strptime(row['Submission Date'], '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            submission_date = datetime.strptime(row['Submission Date'], '%m-%d-%Y')
                        except:
                            pass

                # Create transaction (use 'paypal' as source_system)
                cursor.execute("""
                    INSERT INTO transactions (
                        contact_id,
                        amount,
                        transaction_date,
                        status,
                        payment_method,
                        payment_processor,
                        source_system,
                        external_transaction_id,
                        transaction_type,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, 'completed', 'paypal', 'paypal', 'paypal',
                        %s, 'purchase', NOW(), NOW()
                    )
                """, (contact_id, amount, submission_date or datetime.now(), txn_id))

                donations_added += 1
                print(f"  💰 Added donation: ${amount} (txn: {txn_id})")

    print(f"   ✅ Enriched {enriched_count} contacts")
    print(f"   💰 Added {donations_added} donation transactions")

    return enriched_count, new_contacts, donations_added


def process_event_hosting_file(cursor, filepath):
    """Process event hosting form - rich B2B data."""
    print(f"\n📄 Processing: Hosting_an_Event_at_the_StarHouse_.csv")

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"   Found {len(rows)} event hosting inquiries")

    enriched_count = 0

    for row in rows:
        email = normalize_email(row.get('Email'))
        if not email:
            continue

        first_name = row.get('First Name', '').strip()
        last_name = row.get('Last Name', '').strip()

        contact_id = get_or_create_contact(cursor, email, first_name, last_name)
        if not contact_id:
            continue

        enrichment_data = {
            'phone': row.get('Phone Number'),
            'business_name': row.get('Business Name'),
        }

        if enrich_contact_data(cursor, contact_id, enrichment_data):
            enriched_count += 1

    print(f"   ✅ Enriched {enriched_count} event host contacts")

    return enriched_count


def main():
    print("=" * 80)
    print("JOTFORM CONTACT ENRICHMENT - FAANG QUALITY")
    print("=" * 80)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    total_enriched = 0
    total_new_contacts = 0
    total_donations = 0

    try:
        # Process donation files
        donation_files = [
            '2022_Donation_.csv',
            '2024_End_of_Year_Donation.csv',
            '30th_Birthday.csv',
            'StarHouse_Donation.csv',
            'GivingTuesday.csv',
            '_One_Time_Donation_and_or_Subscription_.csv',
        ]

        for filename in donation_files:
            filepath = os.path.join(JOTFORM_DIR, filename)
            if os.path.exists(filepath):
                enriched, new, donations = process_donation_file(cursor, filepath, filename)
                total_enriched += enriched
                total_new_contacts += new
                total_donations += donations

        # Process event hosting file (B2B data)
        hosting_file = os.path.join(JOTFORM_DIR, 'Hosting_an_Event_at_the_StarHouse_.csv')
        if os.path.exists(hosting_file):
            enriched = process_event_hosting_file(cursor, hosting_file)
            total_enriched += enriched

        # Commit changes
        conn.commit()

        print("\n" + "=" * 80)
        print("ENRICHMENT COMPLETE")
        print("=" * 80)
        print(f"✅ Total contacts enriched: {total_enriched}")
        print(f"✨ New contacts created: {total_new_contacts}")
        print(f"💰 Donation transactions added: {total_donations}")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
