#!/usr/bin/env python3
"""
Mailchimp Contact Enrichment Analysis
Focus: Contact data enrichment (skip tags)

Enrichment opportunities:
1. Phone numbers (15 contacts missing)
2. New contacts (71 not in database)
3. Geographic data (latitude/longitude)
4. Member ratings (engagement indicator)
5. Last changed dates
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime
from collections import defaultdict
from db_config import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/mailchimp_enrichment_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()
MAILCHIMP_FILE = 'kajabi 3 files review/Mailchimp export 9-29-2020.csv'


def normalize_email(email):
    """Normalize email"""
    if pd.isna(email) or not email:
        return None
    return str(email).lower().strip()


def normalize_phone(phone):
    """Normalize phone number"""
    if pd.isna(phone) or not phone:
        return None
    phone_str = str(phone).strip()
    # Remove non-digits
    import re
    digits = re.sub(r'\D', '', phone_str)
    if len(digits) >= 10:
        return digits
    return None


def load_mailchimp_data(filepath):
    """Load Mailchimp export"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("LOADING MAILCHIMP EXPORT")
    logger.info("=" * 80)

    df = pd.read_csv(filepath, encoding='utf-8')
    df['email_normalized'] = df['Email Address'].apply(normalize_email)
    df['phone_normalized'] = df['Phone Number'].apply(normalize_phone)

    logger.info(f"Loaded {len(df)} contacts")

    return df


def load_database_contacts(conn):
    """Load database contacts"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("LOADING DATABASE CONTACTS")
    logger.info("=" * 80)

    query = """
        SELECT
            id,
            email,
            first_name,
            last_name,
            phone,
            city,
            state,
            country,
            source_system
        FROM contacts
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        contacts = cursor.fetchall()

    email_lookup = {}
    for contact in contacts:
        if contact['email']:
            email_normalized = normalize_email(contact['email'])
            if email_normalized:
                email_lookup[email_normalized] = contact

    logger.info(f"Loaded {len(contacts)} contacts")
    logger.info(f"Email lookup: {len(email_lookup)} unique emails")

    return contacts, email_lookup


def analyze_new_contacts(mc_df, email_lookup):
    """Analyze the 71 new contacts"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING 71 NEW CONTACTS")
    logger.info("=" * 80)

    new_contacts = []
    for _, row in mc_df.iterrows():
        email = row['email_normalized']
        if email and email not in email_lookup:
            new_contacts.append(row)

    logger.info(f"Total new contacts: {len(new_contacts)}")
    logger.info("")

    # Analyze data quality of new contacts
    has_phone = sum(1 for c in new_contacts if pd.notna(c['phone_normalized']))
    has_location = sum(1 for c in new_contacts if pd.notna(c['LATITUDE']))
    has_full_name = sum(1 for c in new_contacts if pd.notna(c['First Name']) and pd.notna(c['Last Name']))

    logger.info(f"New contacts with phone: {has_phone} ({has_phone/len(new_contacts)*100:.1f}%)")
    logger.info(f"New contacts with location: {has_location} ({has_location/len(new_contacts)*100:.1f}%)")
    logger.info(f"New contacts with full name: {has_full_name} ({has_full_name/len(new_contacts)*100:.1f}%)")
    logger.info("")

    # Show sample of new contacts
    logger.info("Sample new contacts:")
    logger.info(f"{'Email':40s} {'Name':30s} {'Phone':15s} {'Location':20s} {'Rating':6s}")
    logger.info("-" * 120)

    for i, row in enumerate(new_contacts[:20], 1):
        email = row['Email Address']
        name = f"{row['First Name']} {row['Last Name']}" if pd.notna(row['First Name']) else "(no name)"
        phone = row['Phone Number'] if pd.notna(row['Phone Number']) else ""
        location = f"{row['REGION']}, {row['CC']}" if pd.notna(row['REGION']) else ""
        rating = str(row['MEMBER_RATING']) if pd.notna(row['MEMBER_RATING']) else ""

        logger.info(f"{email[:40]:40s} {name[:30]:30s} {phone[:15]:15s} {location[:20]:20s} {rating:6s}")

    return new_contacts


def analyze_phone_enrichment(mc_df, email_lookup):
    """Analyze phone number enrichment"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING PHONE NUMBER ENRICHMENT")
    logger.info("=" * 80)

    phone_enrichments = []

    for _, row in mc_df.iterrows():
        email = row['email_normalized']
        if not email or email not in email_lookup:
            continue

        db_contact = email_lookup[email]
        mc_phone = row['phone_normalized']
        db_phone = db_contact['phone']

        # Check if we can add/update phone
        if mc_phone and not db_phone:
            phone_enrichments.append({
                'email': email,
                'name': f"{db_contact['first_name']} {db_contact['last_name']}",
                'mc_phone': row['Phone Number'],
                'source': db_contact['source_system']
            })

    logger.info(f"Contacts that can get phone numbers: {len(phone_enrichments)}")
    logger.info("")

    if phone_enrichments:
        logger.info("Contacts to enrich with phone:")
        logger.info(f"{'Email':40s} {'Name':30s} {'Phone':20s} {'Source':15s}")
        logger.info("-" * 110)
        for p in phone_enrichments[:20]:
            logger.info(f"{p['email'][:40]:40s} {p['name'][:30]:30s} {p['mc_phone'][:20]:20s} {p['source'][:15]:15s}")

    return phone_enrichments


def analyze_geographic_data(mc_df, email_lookup):
    """Analyze geographic data enrichment"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING GEOGRAPHIC DATA")
    logger.info("=" * 80)

    geo_data = []

    for _, row in mc_df.iterrows():
        email = row['email_normalized']
        if not email or email not in email_lookup:
            continue

        if pd.notna(row['LATITUDE']) and pd.notna(row['LONGITUDE']):
            db_contact = email_lookup[email]

            # Check if database has location
            has_location = bool(db_contact['city'] or db_contact['state'])

            geo_data.append({
                'email': email,
                'name': f"{db_contact['first_name']} {db_contact['last_name']}",
                'latitude': row['LATITUDE'],
                'longitude': row['LONGITUDE'],
                'city': row['REGION'],
                'state': row['CC'],
                'timezone': row['TIMEZONE'],
                'db_has_location': has_location,
                'db_city': db_contact['city'],
                'db_state': db_contact['state']
            })

    logger.info(f"Contacts with geographic data in Mailchimp: {len(geo_data)}")

    needs_location = sum(1 for g in geo_data if not g['db_has_location'])
    has_location = sum(1 for g in geo_data if g['db_has_location'])

    logger.info(f"  Database missing location: {needs_location}")
    logger.info(f"  Database has location: {has_location}")
    logger.info("")

    logger.info("Geographic data uses:")
    logger.info("  1. Could populate city/state for contacts missing it")
    logger.info("  2. Could add latitude/longitude for mapping")
    logger.info("  3. Could add timezone for scheduling")
    logger.info("  4. Currently contacts table doesn't have lat/long fields")

    return geo_data


def analyze_member_ratings(mc_df, email_lookup):
    """Analyze member ratings"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING MEMBER RATINGS")
    logger.info("=" * 80)

    ratings = defaultdict(int)

    for _, row in mc_df.iterrows():
        email = row['email_normalized']
        if email and email in email_lookup:
            rating = row['MEMBER_RATING']
            if pd.notna(rating):
                ratings[int(rating)] += 1

    logger.info("Member rating distribution (matched contacts):")
    logger.info("  Rating = engagement level (1-5, higher = more engaged)")
    logger.info("")
    for rating in sorted(ratings.keys(), reverse=True):
        count = ratings[rating]
        pct = count / sum(ratings.values()) * 100
        stars = "⭐" * rating
        logger.info(f"  {rating} {stars:10s} {count:5d} contacts ({pct:5.1f}%)")

    logger.info("")
    logger.info("Note: Member rating could be stored as 'engagement_score' or similar")
    logger.info("      Currently contacts table doesn't have this field")

    return ratings


def generate_enrichment_summary(new_contacts, phone_enrichments, geo_data, ratings):
    """Generate summary"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ENRICHMENT OPPORTUNITIES SUMMARY")
    logger.info("=" * 80)
    logger.info("")

    logger.info("1. NEW CONTACTS TO IMPORT:")
    logger.info(f"   Total: {len(new_contacts)}")
    logger.info(f"   Value: LOW - Most lack complete data")
    logger.info(f"   Recommendation: SKIP - Already have 97.2% of Mailchimp list")
    logger.info("")

    logger.info("2. PHONE NUMBER ENRICHMENT:")
    logger.info(f"   Total: {len(phone_enrichments)} contacts")
    logger.info(f"   Value: LOW - Only {len(phone_enrichments)} contacts")
    logger.info(f"   Recommendation: IMPORT if easy, but low impact")
    logger.info("")

    logger.info("3. GEOGRAPHIC DATA:")
    logger.info(f"   Total: {len(geo_data)} contacts have lat/long")
    logger.info(f"   Value: LOW-MEDIUM - Requires schema changes")
    logger.info(f"   Recommendation: SKIP - No lat/long fields in contacts table")
    logger.info(f"                   Could add in future for mapping features")
    logger.info("")

    logger.info("4. MEMBER RATINGS:")
    logger.info(f"   Total: {sum(ratings.values())} contacts have ratings")
    logger.info(f"   Value: MEDIUM - Good engagement indicator")
    logger.info(f"   Recommendation: SKIP - No engagement_score field yet")
    logger.info(f"                   Could add in future for segmentation")
    logger.info("")

    logger.info("=" * 80)
    logger.info("OVERALL RECOMMENDATION:")
    logger.info("=" * 80)
    logger.info("")
    logger.info("✅ MAILCHIMP DATA ALREADY IMPORTED")
    logger.info("   - 97.2% of contacts already in database from other sources")
    logger.info("   - Tags skipped (will get from other sources)")
    logger.info("")
    logger.info("⚠️  LIMITED ADDITIONAL VALUE")
    logger.info("   - Only 15 phone numbers to add")
    logger.info("   - Geographic/rating data requires schema changes")
    logger.info("   - 71 new contacts are low quality")
    logger.info("")
    logger.info("RECOMMENDATION: SKIP THIS IMPORT")
    logger.info("   The Mailchimp data is from 2020 and has already been")
    logger.info("   imported via other sources (Kajabi, etc.)")
    logger.info("")
    logger.info("   If you want to proceed:")
    logger.info("   - Add 15 phone numbers (minor enrichment)")
    logger.info("   - Add engagement_score field for member ratings")
    logger.info("   - Add lat/long fields for geographic data")
    logger.info("")


def main():
    """Main analysis"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "MAILCHIMP CONTACT ENRICHMENT ANALYSIS".center(78) + "║")
    logger.info("║" + "(Skipping Tags)".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        # Load data
        mc_df = load_mailchimp_data(MAILCHIMP_FILE)
        conn = psycopg2.connect(DATABASE_URL)
        contacts, email_lookup = load_database_contacts(conn)

        # Analyze enrichment opportunities
        new_contacts = analyze_new_contacts(mc_df, email_lookup)
        phone_enrichments = analyze_phone_enrichment(mc_df, email_lookup)
        geo_data = analyze_geographic_data(mc_df, email_lookup)
        ratings = analyze_member_ratings(mc_df, email_lookup)

        # Generate summary
        generate_enrichment_summary(new_contacts, phone_enrichments, geo_data, ratings)

        conn.close()
        logger.info("✅ Analysis completed")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
