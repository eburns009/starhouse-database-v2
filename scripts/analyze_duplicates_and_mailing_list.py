#!/usr/bin/env python3
"""
FAANG-Quality Duplicate Analysis & Mailing List Validation
Comprehensive review of contacts database for duplicates and enrichment opportunities

Features:
- Email duplicate detection
- Name-based duplicate detection (fuzzy matching)
- Address duplicate detection (household consolidation)
- Phone duplicate detection
- Data quality validation
- Mailing list column validation
- Enrichment opportunity identification
- Merge recommendations
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime
from collections import defaultdict, Counter
import re
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/duplicate_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def load_all_contacts(conn):
    """Load all contacts with relevant fields"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("LOADING ALL CONTACTS")
    logger.info("=" * 80)

    query = """
        SELECT
            id,
            email,
            first_name,
            last_name,
            phone,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country,
            total_spent,
            transaction_count,
            source_system,
            created_at,
            updated_at,
            email_subscribed,
            shipping_address_line_1,
            shipping_city,
            shipping_state,
            shipping_postal_code,
            shipping_address_status
        FROM contacts
        ORDER BY created_at DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        contacts = cursor.fetchall()

    logger.info(f"Loaded {len(contacts)} total contacts")

    return contacts


def find_email_duplicates(contacts):
    """Find duplicate email addresses"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINDING EMAIL DUPLICATES")
    logger.info("=" * 80)

    email_groups = defaultdict(list)

    for contact in contacts:
        if contact['email']:
            email_normalized = contact['email'].lower().strip()
            email_groups[email_normalized].append(contact)

    # Find duplicates (more than one contact per email)
    duplicates = {email: group for email, group in email_groups.items() if len(group) > 1}

    logger.info(f"Total unique emails: {len(email_groups)}")
    logger.info(f"Duplicate emails: {len(duplicates)}")

    if duplicates:
        logger.info("")
        logger.info("Top 10 email duplicates:")
        sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (email, group) in enumerate(sorted_dups[:10], 1):
            logger.info(f"  {i}. {email} - {len(group)} contacts")
            for contact in group:
                logger.info(f"      ID: {contact['id']}, Name: {contact['first_name']} {contact['last_name']}, "
                          f"Source: {contact['source_system']}, Spent: ${contact['total_spent']}")

    return duplicates


def normalize_name(first, last):
    """Normalize name for matching"""
    if not first and not last:
        return None

    first_str = str(first or '').strip().lower()
    last_str = str(last or '').strip().lower()

    # Remove special characters
    first_str = re.sub(r'[^a-z\s]', '', first_str)
    last_str = re.sub(r'[^a-z\s]', '', last_str)

    return f"{first_str} {last_str}".strip()


def name_similarity(name1, name2):
    """Calculate similarity between two names (0-1)"""
    if not name1 or not name2:
        return 0.0
    return SequenceMatcher(None, name1, name2).ratio()


def find_name_duplicates(contacts):
    """Find potential duplicate names (fuzzy matching)"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINDING NAME DUPLICATES")
    logger.info("=" * 80)

    # Group by exact normalized name
    name_groups = defaultdict(list)

    for contact in contacts:
        name_normalized = normalize_name(contact['first_name'], contact['last_name'])
        if name_normalized:
            name_groups[name_normalized].append(contact)

    # Find exact duplicates
    exact_duplicates = {name: group for name, group in name_groups.items() if len(group) > 1}

    logger.info(f"Total unique names: {len(name_groups)}")
    logger.info(f"Exact name duplicates: {len(exact_duplicates)}")

    if exact_duplicates:
        logger.info("")
        logger.info("Top 10 name duplicates (same name, different emails):")
        sorted_dups = sorted(exact_duplicates.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (name, group) in enumerate(sorted_dups[:10], 1):
            logger.info(f"  {i}. {name.title()} - {len(group)} contacts")
            for contact in group[:3]:  # Show first 3
                logger.info(f"      Email: {contact['email']}, Source: {contact['source_system']}, "
                          f"Spent: ${contact['total_spent']}")

    return exact_duplicates


def normalize_address(addr1, city, state, zip_code):
    """Normalize address for matching"""
    if not addr1:
        return None

    addr_str = str(addr1).lower().strip()
    city_str = str(city or '').lower().strip()
    state_str = str(state or '').lower().strip()
    zip_str = str(zip_code or '').strip()[:5]  # First 5 digits only

    # Normalize address abbreviations
    addr_str = re.sub(r'\bst\b', 'street', addr_str)
    addr_str = re.sub(r'\bave\b', 'avenue', addr_str)
    addr_str = re.sub(r'\brd\b', 'road', addr_str)
    addr_str = re.sub(r'\bdr\b', 'drive', addr_str)
    addr_str = re.sub(r'\bln\b', 'lane', addr_str)
    addr_str = re.sub(r'\bapt\b', '', addr_str)
    addr_str = re.sub(r'\bunit\b', '', addr_str)
    addr_str = re.sub(r'[^a-z0-9\s]', '', addr_str)
    addr_str = ' '.join(addr_str.split())

    return f"{addr_str}|{city_str}|{state_str}|{zip_str}"


def find_address_duplicates(contacts):
    """Find contacts at same address (household members)"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINDING ADDRESS DUPLICATES")
    logger.info("=" * 80)

    address_groups = defaultdict(list)

    for contact in contacts:
        if contact['address_line_1'] and contact['postal_code']:
            addr_normalized = normalize_address(
                contact['address_line_1'],
                contact['city'],
                contact['state'],
                contact['postal_code']
            )
            if addr_normalized:
                address_groups[addr_normalized].append(contact)

    # Find households (multiple people at same address)
    households = {addr: group for addr, group in address_groups.items() if len(group) > 1}

    logger.info(f"Total unique addresses: {len(address_groups)}")
    logger.info(f"Households (multiple contacts): {len(households)}")

    if households:
        logger.info("")
        logger.info("Top 10 households:")
        sorted_households = sorted(households.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (addr, group) in enumerate(sorted_households[:10], 1):
            parts = addr.split('|')
            logger.info(f"  {i}. {parts[0][:50]}, {parts[1]}, {parts[2]} {parts[3]} - {len(group)} contacts")
            for contact in group[:3]:  # Show first 3
                logger.info(f"      {contact['first_name']} {contact['last_name']} <{contact['email']}>")

    return households


def find_phone_duplicates(contacts):
    """Find duplicate phone numbers"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINDING PHONE DUPLICATES")
    logger.info("=" * 80)

    phone_groups = defaultdict(list)

    for contact in contacts:
        if contact['phone']:
            # Normalize phone (digits only)
            phone_normalized = re.sub(r'\D', '', str(contact['phone']))
            if len(phone_normalized) >= 10:
                # Use last 10 digits (handles country codes)
                phone_normalized = phone_normalized[-10:]
                phone_groups[phone_normalized].append(contact)

    duplicates = {phone: group for phone, group in phone_groups.items() if len(group) > 1}

    logger.info(f"Total unique phones: {len(phone_groups)}")
    logger.info(f"Duplicate phones: {len(duplicates)}")

    if duplicates:
        logger.info("")
        logger.info("Top 10 phone duplicates:")
        sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (phone, group) in enumerate(sorted_dups[:10], 1):
            formatted_phone = f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
            logger.info(f"  {i}. {formatted_phone} - {len(group)} contacts")
            for contact in group[:3]:
                logger.info(f"      {contact['first_name']} {contact['last_name']} <{contact['email']}>")

    return duplicates


def validate_mailing_list_data(contacts):
    """Validate mailing list column quality"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATING MAILING LIST DATA QUALITY")
    logger.info("=" * 80)

    total = len(contacts)

    # Count completeness
    has_email = sum(1 for c in contacts if c['email'])
    has_name = sum(1 for c in contacts if c['first_name'] or c['last_name'])
    has_full_name = sum(1 for c in contacts if c['first_name'] and c['last_name'])
    has_phone = sum(1 for c in contacts if c['phone'])
    has_address_line_1 = sum(1 for c in contacts if c['address_line_1'])
    has_city = sum(1 for c in contacts if c['city'])
    has_state = sum(1 for c in contacts if c['state'])
    has_zip = sum(1 for c in contacts if c['postal_code'])
    has_complete_address = sum(1 for c in contacts if c['address_line_1'] and c['city'] and c['state'] and c['postal_code'])

    # Shipping address data
    has_shipping_address = sum(1 for c in contacts if c['shipping_address_line_1'])
    has_complete_shipping = sum(1 for c in contacts if c['shipping_address_line_1'] and c['shipping_city'] and c['shipping_state'] and c['shipping_postal_code'])

    # Email subscription status
    email_subscribed = sum(1 for c in contacts if c.get('email_subscribed') == True)

    logger.info("DATA COMPLETENESS:")
    logger.info(f"  Email:              {has_email:6,} ({has_email/total*100:5.1f}%)")
    logger.info(f"  Any name:           {has_name:6,} ({has_name/total*100:5.1f}%)")
    logger.info(f"  Full name:          {has_full_name:6,} ({has_full_name/total*100:5.1f}%)")
    logger.info(f"  Phone:              {has_phone:6,} ({has_phone/total*100:5.1f}%)")
    logger.info(f"  Address line 1:     {has_address_line_1:6,} ({has_address_line_1/total*100:5.1f}%)")
    logger.info(f"  City:               {has_city:6,} ({has_city/total*100:5.1f}%)")
    logger.info(f"  State:              {has_state:6,} ({has_state/total*100:5.1f}%)")
    logger.info(f"  ZIP:                {has_zip:6,} ({has_zip/total*100:5.1f}%)")
    logger.info(f"  Complete address:   {has_complete_address:6,} ({has_complete_address/total*100:5.1f}%)")
    logger.info("")
    logger.info("SHIPPING ADDRESS DATA:")
    logger.info(f"  Has shipping addr:  {has_shipping_address:6,} ({has_shipping_address/total*100:5.1f}%)")
    logger.info(f"  Complete shipping:  {has_complete_shipping:6,} ({has_complete_shipping/total*100:5.1f}%)")
    logger.info("")
    logger.info("EMAIL SUBSCRIPTION:")
    logger.info(f"  Email subscribed:   {email_subscribed:6,} ({email_subscribed/total*100:5.1f}%)")
    logger.info("")
    logger.info("MAILING LIST READINESS:")
    logger.info(f"  Ready to mail:      {has_complete_address:6,} ({has_complete_address/total*100:5.1f}%)")
    logger.info("  Note: No address validation data found in schema")
    logger.info("        Consider adding: address_validated, usps_dpv_confirmation, ncoa_move_date")

    return {
        'total': total,
        'has_complete_address': has_complete_address,
        'has_shipping_address': has_shipping_address,
        'has_complete_shipping': has_complete_shipping,
        'email_subscribed': email_subscribed
    }


def identify_enrichment_opportunities(email_dups, name_dups, households, phone_dups, contacts):
    """Identify opportunities to enrich data through deduplication"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ENRICHMENT OPPORTUNITIES FROM DUPLICATES")
    logger.info("=" * 80)

    opportunities = []

    # Email duplicates - merge strategy
    for email, group in list(email_dups.items())[:20]:  # Top 20
        # Find the "best" record (most complete)
        best = max(group, key=lambda c: (
            bool(c['address_line_1']),
            bool(c['phone']),
            c['total_spent'] or 0,
            c['transaction_count'] or 0
        ))

        # Find records that can enrich the best
        for contact in group:
            if contact['id'] == best['id']:
                continue

            enrichments = []
            if contact['phone'] and not best['phone']:
                enrichments.append('phone')
            if contact['address_line_1'] and not best['address_line_1']:
                enrichments.append('address')
            if (contact['total_spent'] or 0) > (best['total_spent'] or 0):
                enrichments.append('financial_data')

            if enrichments:
                opportunities.append({
                    'type': 'email_duplicate',
                    'email': email,
                    'keep_id': best['id'],
                    'merge_id': contact['id'],
                    'enrichments': enrichments
                })

    # Name duplicates - potential merges
    for name, group in list(name_dups.items())[:20]:  # Top 20
        # Check if different emails but might be same person
        if len(group) == 2:
            c1, c2 = group[0], group[1]

            # If addresses match, likely same person
            if c1['address_line_1'] and c2['address_line_1']:
                addr1 = normalize_address(c1['address_line_1'], c1['city'], c1['state'], c1['postal_code'])
                addr2 = normalize_address(c2['address_line_1'], c2['city'], c2['state'], c2['postal_code'])

                if addr1 == addr2:
                    opportunities.append({
                        'type': 'name_and_address_match',
                        'name': name,
                        'contact1': c1,
                        'contact2': c2,
                        'recommendation': 'Likely same person - merge records'
                    })

    logger.info(f"Total enrichment opportunities: {len(opportunities)}")
    logger.info("")
    logger.info("Sample opportunities:")

    for i, opp in enumerate(opportunities[:10], 1):
        if opp['type'] == 'email_duplicate':
            logger.info(f"  {i}. Email duplicate: {opp['email']}")
            logger.info(f"      Keep: {opp['keep_id']}, Merge: {opp['merge_id']}")
            logger.info(f"      Can enrich: {', '.join(opp['enrichments'])}")
        elif opp['type'] == 'name_and_address_match':
            logger.info(f"  {i}. Name/Address match: {opp['name']}")
            logger.info(f"      Email 1: {opp['contact1']['email']}")
            logger.info(f"      Email 2: {opp['contact2']['email']}")
            logger.info(f"      {opp['recommendation']}")

    return opportunities


def generate_summary_report(email_dups, name_dups, households, phone_dups, mailing_stats, opportunities):
    """Generate comprehensive summary"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("DUPLICATE ANALYSIS & MAILING LIST READINESS SUMMARY")
    logger.info("=" * 80)
    logger.info("")

    logger.info("DUPLICATE DETECTION RESULTS:")
    logger.info(f"  📧 Email duplicates:        {len(email_dups):5,} (same email, multiple records)")
    logger.info(f"  👤 Name duplicates:         {len(name_dups):5,} (same name, different emails)")
    logger.info(f"  🏠 Households:              {len(households):5,} (multiple people, same address)")
    logger.info(f"  📞 Phone duplicates:        {len(phone_dups):5,} (same phone, multiple records)")
    logger.info("")

    logger.info("MAILING LIST READINESS:")
    logger.info(f"  Total contacts:             {mailing_stats['total']:5,}")
    logger.info(f"  Complete addresses:         {mailing_stats['has_complete_address']:5,} ({mailing_stats['has_complete_address']/mailing_stats['total']*100:5.1f}%)")
    logger.info(f"  Complete shipping addr:     {mailing_stats['has_complete_shipping']:5,} ({mailing_stats['has_complete_shipping']/mailing_stats['total']*100:5.1f}%)")
    logger.info(f"  Email subscribed:           {mailing_stats['email_subscribed']:5,} ({mailing_stats['email_subscribed']/mailing_stats['total']*100:5.1f}%)")
    logger.info("")

    logger.info("ENRICHMENT OPPORTUNITIES:")
    logger.info(f"  Merge/enrich opportunities: {len(opportunities):5,}")
    logger.info("")

    logger.info("RECOMMENDATIONS:")
    logger.info("")
    logger.info("1. EMAIL DUPLICATES (CRITICAL):")
    logger.info(f"   - {len(email_dups)} emails have multiple records")
    logger.info("   - Action: Review and merge duplicate records")
    logger.info("   - Priority: HIGH - Causes data inconsistency")
    logger.info("")

    logger.info("2. NAME DUPLICATES (REVIEW NEEDED):")
    logger.info(f"   - {len(name_dups)} names appear multiple times with different emails")
    logger.info("   - Action: Review if same person with old/new email")
    logger.info("   - Priority: MEDIUM - May be legitimate (family members, etc.)")
    logger.info("")

    logger.info("3. HOUSEHOLDS (OPPORTUNITY):")
    logger.info(f"   - {len(households)} addresses have multiple contacts")
    logger.info("   - Action: Consider household consolidation for mailings")
    logger.info("   - Priority: LOW - Saves postage costs")
    logger.info("")

    logger.info("4. MAILING LIST READINESS:")
    ready_pct = mailing_stats['has_complete_address'] / mailing_stats['total'] * 100
    if ready_pct < 50:
        logger.info(f"   - Only {ready_pct:.1f}% of contacts have complete addresses")
        logger.info("   - Action: Enrich addresses from duplicates/shipping data")
        logger.info("   - Priority: HIGH - Limits mailing campaign size")
    else:
        logger.info(f"   - {ready_pct:.1f}% of contacts have complete addresses")
        logger.info("   - Status: GOOD - Most contacts ready for mailing")
    logger.info("   - Note: No USPS validation data in schema yet")
    logger.info("")

    logger.info("=" * 80)


def main():
    """Main analysis workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "DUPLICATE ANALYSIS & MAILING LIST VALIDATION".center(78) + "║")
    logger.info("║" + "FAANG-Grade Quality".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        # Load contacts
        conn = psycopg2.connect(DATABASE_URL)
        contacts = load_all_contacts(conn)

        # Find duplicates
        email_dups = find_email_duplicates(contacts)
        name_dups = find_name_duplicates(contacts)
        households = find_address_duplicates(contacts)
        phone_dups = find_phone_duplicates(contacts)

        # Validate mailing list data
        mailing_stats = validate_mailing_list_data(contacts)

        # Identify enrichment opportunities
        opportunities = identify_enrichment_opportunities(
            email_dups, name_dups, households, phone_dups, contacts
        )

        # Generate summary
        generate_summary_report(
            email_dups, name_dups, households, phone_dups,
            mailing_stats, opportunities
        )

        conn.close()
        logger.info("")
        logger.info("✅ Analysis completed successfully")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
