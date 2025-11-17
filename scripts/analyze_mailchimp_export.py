#!/usr/bin/env python3
"""
FAANG-Quality Mailchimp Export Analysis
Analyzes Mailchimp export to identify enrichment opportunities

Features:
- Email matching with database
- Tag analysis and categorization
- Phone number extraction
- Geographic data review
- New contact identification
- Comprehensive reporting
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime
from collections import defaultdict, Counter
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/mailchimp_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL',
    "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres")

# File path
MAILCHIMP_FILE = 'kajabi 3 files review/Mailchimp export 9-29-2020.csv'


def normalize_email(email):
    """Normalize email to lowercase and strip whitespace"""
    if pd.isna(email) or not email:
        return None
    return str(email).lower().strip()


def parse_tags(tags_str):
    """Parse tags from Mailchimp format: "Tag1","Tag2","Tag3" """
    if pd.isna(tags_str) or not tags_str:
        return []

    # Tags are in format: "Tag1","Tag2"
    # Find all quoted strings
    import re
    tags = re.findall(r'"([^"]+)"', tags_str)

    return tags


def load_mailchimp_data(filepath):
    """Load and parse Mailchimp export"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("LOADING MAILCHIMP EXPORT")
    logger.info("=" * 80)

    df = pd.read_csv(filepath, encoding='utf-8')

    logger.info(f"Loaded {len(df)} total contacts")
    logger.info(f"Columns: {list(df.columns)}")

    # Normalize email addresses
    df['email_normalized'] = df['Email Address'].apply(normalize_email)

    # Parse tags
    df['tags_list'] = df['TAGS'].apply(parse_tags)

    # Count contacts with data
    has_phone = df['Phone Number'].notna().sum()
    has_tags = df['tags_list'].apply(lambda x: len(x) > 0).sum()
    has_location = df['LATITUDE'].notna().sum()

    logger.info(f"Contacts with phone: {has_phone} ({has_phone/len(df)*100:.1f}%)")
    logger.info(f"Contacts with tags: {has_tags} ({has_tags/len(df)*100:.1f}%)")
    logger.info(f"Contacts with location: {has_location} ({has_location/len(df)*100:.1f}%)")

    return df


def load_database_contacts(conn):
    """Load all contacts from database"""
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
            source_system,
            total_spent,
            created_at
        FROM contacts
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        contacts = cursor.fetchall()

    logger.info(f"Loaded {len(contacts)} contacts from database")

    # Create lookup by email
    email_lookup = {}
    for contact in contacts:
        if contact['email']:
            email_normalized = normalize_email(contact['email'])
            if email_normalized:
                email_lookup[email_normalized] = contact

    logger.info(f"Built lookup for {len(email_lookup)} unique emails")

    return contacts, email_lookup


def match_mailchimp_to_database(mc_df, email_lookup):
    """Match Mailchimp contacts to database"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("MATCHING MAILCHIMP TO DATABASE")
    logger.info("=" * 80)

    matches = []
    new_contacts = []

    for _, row in mc_df.iterrows():
        email = row['email_normalized']
        if not email:
            continue

        if email in email_lookup:
            # Match found
            db_contact = email_lookup[email]
            matches.append({
                'email': email,
                'mc_first_name': row['First Name'],
                'mc_last_name': row['Last Name'],
                'mc_phone': row['Phone Number'],
                'mc_tags': row['tags_list'],
                'mc_rating': row['MEMBER_RATING'],
                'db_id': db_contact['id'],
                'db_first_name': db_contact['first_name'],
                'db_last_name': db_contact['last_name'],
                'db_phone': db_contact['phone'],
                'db_source': db_contact['source_system'],
            })
        else:
            # New contact
            new_contacts.append({
                'email': email,
                'first_name': row['First Name'],
                'last_name': row['Last Name'],
                'phone': row['Phone Number'],
                'tags': row['tags_list'],
                'rating': row['MEMBER_RATING'],
            })

    logger.info(f"✅ MATCHED: {len(matches)} contacts")
    logger.info(f"🆕 NEW: {len(new_contacts)} contacts")

    return matches, new_contacts


def analyze_tags(mc_df):
    """Analyze tag distribution"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING MAILCHIMP TAGS")
    logger.info("=" * 80)

    # Collect all tags
    all_tags = []
    for tags_list in mc_df['tags_list']:
        all_tags.extend(tags_list)

    tag_counts = Counter(all_tags)

    logger.info(f"Total unique tags: {len(tag_counts)}")
    logger.info(f"Total tag assignments: {len(all_tags)}")
    logger.info("")
    logger.info("Top 20 most common tags:")

    for i, (tag, count) in enumerate(tag_counts.most_common(20), 1):
        pct = count / len(mc_df) * 100
        logger.info(f"  {i:2d}. {tag:40s} {count:5d} ({pct:5.1f}%)")

    return tag_counts


def analyze_enrichment_opportunities(matches):
    """Analyze what data can enrich existing contacts"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING ENRICHMENT OPPORTUNITIES")
    logger.info("=" * 80)

    # Phone numbers
    needs_phone = [m for m in matches if not m['db_phone'] and pd.notna(m['mc_phone'])]

    # Tags (all matches have tags we could import)
    has_tags = [m for m in matches if len(m['mc_tags']) > 0]

    # Name corrections (where Mailchimp has different name)
    name_diffs = []
    for m in matches:
        mc_name = f"{m['mc_first_name']} {m['mc_last_name']}"
        db_name = f"{m['db_first_name']} {m['db_last_name']}"
        if mc_name.lower().strip() != db_name.lower().strip():
            name_diffs.append(m)

    logger.info(f"📞 Contacts needing phone: {len(needs_phone)}")
    logger.info(f"🏷️  Contacts with tags: {len(has_tags)}")
    logger.info(f"📝 Contacts with name differences: {len(name_diffs)}")

    if needs_phone:
        logger.info("")
        logger.info("Sample contacts needing phone:")
        for i, m in enumerate(needs_phone[:5], 1):
            logger.info(f"  {i}. {m['email']:35s} Phone: {m['mc_phone']}")

    if name_diffs:
        logger.info("")
        logger.info("Sample name differences:")
        for i, m in enumerate(name_diffs[:5], 1):
            logger.info(f"  {i}. {m['email']:35s}")
            logger.info(f"      Mailchimp: {m['mc_first_name']} {m['mc_last_name']}")
            logger.info(f"      Database:  {m['db_first_name']} {m['db_last_name']}")

    return {
        'needs_phone': needs_phone,
        'has_tags': has_tags,
        'name_diffs': name_diffs
    }


def generate_summary_report(mc_df, matches, new_contacts, tag_counts, enrichment):
    """Generate comprehensive summary"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("MAILCHIMP ANALYSIS SUMMARY")
    logger.info("=" * 80)

    logger.info("")
    logger.info("MAILCHIMP DATA:")
    logger.info(f"  Total contacts in export: {len(mc_df)}")
    logger.info(f"  Export date: September 29, 2020")
    logger.info("")

    logger.info("MATCHING RESULTS:")
    logger.info(f"  ✅ Already in database: {len(matches)} ({len(matches)/len(mc_df)*100:.1f}%)")
    logger.info(f"  🆕 New contacts: {len(new_contacts)} ({len(new_contacts)/len(mc_df)*100:.1f}%)")
    logger.info("")

    logger.info("ENRICHMENT OPPORTUNITIES:")
    logger.info(f"  Phone numbers to add: {len(enrichment['needs_phone'])}")
    logger.info(f"  Contacts with tags: {len(enrichment['has_tags'])}")
    logger.info(f"  Total unique tags: {len(tag_counts)}")
    logger.info(f"  Name differences to review: {len(enrichment['name_diffs'])}")
    logger.info("")

    logger.info("TAG CATEGORIES:")

    # Categorize tags
    member_tags = [t for t in tag_counts if 'member' in t.lower() or 'paid' in t.lower()]
    event_tags = [t for t in tag_counts if any(x in t.lower() for x in ['keeper', 'training', 'participant', 'invite'])]
    program_tags = [t for t in tag_counts if any(x in t.lower() for x in ['trines', 'starwisdom', 'astrology', 'senses'])]

    logger.info(f"  Membership-related: {len(member_tags)} tags")
    logger.info(f"  Event-related: {len(event_tags)} tags")
    logger.info(f"  Program-related: {len(program_tags)} tags")
    logger.info("")

    logger.info("=" * 80)


def main():
    """Main analysis workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "MAILCHIMP EXPORT ANALYSIS".center(78) + "║")
    logger.info("║" + "FAANG-Grade Quality".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    try:
        # 1. Load Mailchimp data
        mc_df = load_mailchimp_data(MAILCHIMP_FILE)

        # 2. Load database contacts
        conn = psycopg2.connect(DATABASE_URL)
        contacts, email_lookup = load_database_contacts(conn)

        # 3. Match to database
        matches, new_contacts = match_mailchimp_to_database(mc_df, email_lookup)

        # 4. Analyze tags
        tag_counts = analyze_tags(mc_df)

        # 5. Analyze enrichment opportunities
        enrichment = analyze_enrichment_opportunities(matches)

        # 6. Generate summary
        generate_summary_report(mc_df, matches, new_contacts, tag_counts, enrichment)

        # Close connection
        conn.close()

        logger.info("")
        logger.info("✅ Analysis completed successfully")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
