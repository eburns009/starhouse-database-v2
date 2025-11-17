#!/usr/bin/env python3
"""
FAANG-Quality Donor Data Analysis
Analyzes QuickBooks donor transactions for contact enrichment potential

Features:
- Transaction-level analysis
- Donor aggregation and statistics
- Contact matching by name
- Enrichment opportunity identification
- Comprehensive reporting
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/donor_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

# File paths
DONOR_FILE = '/workspaces/starhouse-database-v2/kajabi 3 files review/Donors_Quickbooks.csv'


def parse_donor_file(filepath):
    """
    Parse QuickBooks donor export file

    Format is complex - starts with header rows, then transaction data
    """
    logger.info("=" * 80)
    logger.info("PARSING QUICKBOOKS DONOR FILE")
    logger.info("=" * 80)

    # Read the file and find where actual data starts
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Find the header row (contains "Transaction date")
    header_idx = None
    for i, line in enumerate(lines):
        if 'Transaction date' in line:
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find header row in donor file")

    logger.info(f"Found header at line {header_idx + 1}")

    # Read from header onwards
    df = pd.read_csv(
        filepath,
        skiprows=header_idx,
        encoding='utf-8',
        on_bad_lines='skip'
    )

    logger.info(f"Loaded {len(df)} total rows")

    # Filter to actual transaction rows (have a transaction date)
    df = df[df['Transaction date'].notna()].copy()

    # Filter to transactions with donor names
    df = df[df['Name'].notna()].copy()

    # Filter to income transactions (positive amounts)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df[df['Amount'].notna()].copy()
    df = df[df['Amount'] > 0].copy()

    logger.info(f"After filtering: {len(df)} donation transactions")
    logger.info(f"Date range: {df['Transaction date'].min()} to {df['Transaction date'].max()}")

    return df


def aggregate_donor_stats(df):
    """
    Aggregate donations by donor name
    Calculate total, count, first/last donation dates
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("AGGREGATING DONOR STATISTICS")
    logger.info("=" * 80)

    # Group by donor name
    donor_stats = df.groupby('Name').agg({
        'Amount': ['sum', 'count', 'mean', 'min', 'max'],
        'Transaction date': ['min', 'max']
    }).reset_index()

    # Flatten column names
    donor_stats.columns = [
        'donor_name',
        'total_donated',
        'donation_count',
        'avg_donation',
        'min_donation',
        'max_donation',
        'first_donation_date',
        'last_donation_date'
    ]

    # Sort by total donated
    donor_stats = donor_stats.sort_values('total_donated', ascending=False)

    logger.info(f"Unique donors: {len(donor_stats)}")
    logger.info(f"Total donated: ${donor_stats['total_donated'].sum():,.2f}")
    logger.info(f"Average per donor: ${donor_stats['total_donated'].mean():,.2f}")
    logger.info(f"Top donor: {donor_stats.iloc[0]['donor_name']} (${donor_stats.iloc[0]['total_donated']:,.2f})")

    return donor_stats


def normalize_name(name):
    """
    Normalize donor names for matching
    - Remove extra spaces
    - Remove special characters in parentheses
    - Lowercase for comparison
    """
    if pd.isna(name):
        return None

    name_str = str(name).strip()

    # Remove content in parentheses (like "(C)" or "{c}")
    name_str = re.sub(r'\s*[\(\{][^\)\}]*[\)\}]\s*', ' ', name_str)

    # Remove extra spaces
    name_str = ' '.join(name_str.split())

    return name_str


def load_database_contacts(conn):
    """
    Load all contacts from database with their current financial data
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("LOADING DATABASE CONTACTS")
    logger.info("=" * 80)

    query = """
        SELECT
            id,
            first_name,
            last_name,
            email,
            total_spent,
            transaction_count,
            source_system,
            CONCAT(first_name, ' ', last_name) as full_name
        FROM contacts
        WHERE first_name IS NOT NULL
          OR last_name IS NOT NULL
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        contacts = cursor.fetchall()

    logger.info(f"Loaded {len(contacts)} contacts from database")

    # Create lookup by normalized full name
    name_lookup = {}
    for contact in contacts:
        if contact['full_name']:
            normalized = normalize_name(contact['full_name'])
            if normalized:
                # Store all contacts with this name (handle duplicates)
                if normalized.lower() not in name_lookup:
                    name_lookup[normalized.lower()] = []
                name_lookup[normalized.lower()].append(contact)

    logger.info(f"Built lookup for {len(name_lookup)} unique normalized names")

    return contacts, name_lookup


def match_donors_to_contacts(donor_stats, name_lookup):
    """
    Match donors to existing contacts by name
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("MATCHING DONORS TO CONTACTS")
    logger.info("=" * 80)

    matches = []
    new_donors = []

    for _, donor in donor_stats.iterrows():
        donor_name = donor['donor_name']
        normalized = normalize_name(donor_name)

        if not normalized:
            continue

        # Try to find match
        contacts = name_lookup.get(normalized.lower(), [])

        if contacts:
            # Match found - may be multiple contacts with same name
            for contact in contacts:
                matches.append({
                    'donor_name': donor_name,
                    'contact_id': contact['id'],
                    'contact_name': contact['full_name'],
                    'contact_email': contact['email'],
                    'current_total_spent': float(contact['total_spent'] or 0),
                    'current_transaction_count': int(contact['transaction_count'] or 0),
                    'donor_total': float(donor['total_donated']),
                    'donor_count': int(donor['donation_count']),
                    'first_donation': donor['first_donation_date'],
                    'last_donation': donor['last_donation_date'],
                    'source_system': contact['source_system']
                })
        else:
            # No match - new donor
            new_donors.append({
                'donor_name': donor_name,
                'total_donated': float(donor['total_donated']),
                'donation_count': int(donor['donation_count']),
                'first_donation': donor['first_donation_date'],
                'last_donation': donor['last_donation_date']
            })

    logger.info(f"✅ MATCHED: {len(matches)} donor-to-contact links")
    logger.info(f"🆕 NEW: {len(new_donors)} donors not in database")

    return matches, new_donors


def analyze_enrichment_potential(matches):
    """
    Analyze which matched contacts need enrichment
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING ENRICHMENT POTENTIAL")
    logger.info("=" * 80)

    needs_enrichment = []
    already_has_data = []

    for match in matches:
        current_total = match['current_total_spent']
        donor_total = match['donor_total']

        # Check if contact needs enrichment
        if current_total == 0:
            # Definitely needs enrichment
            needs_enrichment.append(match)
        elif current_total < donor_total:
            # Has some data, but donor data shows more
            needs_enrichment.append(match)
        else:
            # Already has complete data
            already_has_data.append(match)

    logger.info(f"📊 Contacts needing enrichment: {len(needs_enrichment)}")
    logger.info(f"✅ Contacts already have complete data: {len(already_has_data)}")

    if needs_enrichment:
        total_enrichment_value = sum(m['donor_total'] for m in needs_enrichment)
        logger.info(f"💰 Total donation value to enrich: ${total_enrichment_value:,.2f}")

        # Show top 10
        sorted_enrichment = sorted(needs_enrichment, key=lambda x: x['donor_total'], reverse=True)
        logger.info("")
        logger.info("Top 10 contacts to enrich:")
        for i, match in enumerate(sorted_enrichment[:10], 1):
            logger.info(
                f"  {i}. {match['donor_name']} - "
                f"Current: ${match['current_total_spent']:,.2f}, "
                f"Donor total: ${match['donor_total']:,.2f}, "
                f"Count: {match['donor_count']}"
            )

    return needs_enrichment, already_has_data


def analyze_new_donors(new_donors):
    """
    Analyze new donors not in database
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("ANALYZING NEW DONORS")
    logger.info("=" * 80)

    if not new_donors:
        logger.info("No new donors found")
        return

    total_value = sum(d['total_donated'] for d in new_donors)
    logger.info(f"💰 Total value from new donors: ${total_value:,.2f}")

    # Show top 10
    sorted_donors = sorted(new_donors, key=lambda x: x['total_donated'], reverse=True)
    logger.info("")
    logger.info("Top 10 new donors (not in database):")
    for i, donor in enumerate(sorted_donors[:10], 1):
        logger.info(
            f"  {i}. {donor['donor_name']} - "
            f"Total: ${donor['total_donated']:,.2f}, "
            f"Count: {donor['donation_count']}, "
            f"Dates: {donor['first_donation']} to {donor['last_donation']}"
        )


def generate_summary_report(donor_stats, matches, new_donors, needs_enrichment):
    """
    Generate comprehensive summary report
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY REPORT")
    logger.info("=" * 80)

    total_donors = len(donor_stats)
    total_donations = donor_stats['total_donated'].sum()

    matched_donors = len(set(m['donor_name'] for m in matches))
    matched_value = sum(m['donor_total'] for m in matches)

    new_donor_count = len(new_donors)
    new_donor_value = sum(d['total_donated'] for d in new_donors)

    enrichment_count = len(needs_enrichment)
    enrichment_value = sum(m['donor_total'] for m in needs_enrichment)

    logger.info("")
    logger.info("QUICKBOOKS DONOR DATA:")
    logger.info(f"  Total unique donors: {total_donors}")
    logger.info(f"  Total donations: ${total_donations:,.2f}")
    logger.info("")
    logger.info("MATCHING RESULTS:")
    logger.info(f"  ✅ Matched to existing contacts: {matched_donors} ({matched_donors/total_donors*100:.1f}%)")
    logger.info(f"     Value: ${matched_value:,.2f}")
    logger.info(f"  🆕 New donors (not in database): {new_donor_count} ({new_donor_count/total_donors*100:.1f}%)")
    logger.info(f"     Value: ${new_donor_value:,.2f}")
    logger.info("")
    logger.info("ENRICHMENT OPPORTUNITIES:")
    logger.info(f"  📊 Contacts needing enrichment: {enrichment_count}")
    logger.info(f"     Value to add: ${enrichment_value:,.2f}")
    logger.info("")
    logger.info("=" * 80)


def main():
    """
    Main analysis workflow
    """
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "QUICKBOOKS DONOR DATA ANALYSIS".center(78) + "║")
    logger.info("║" + "FAANG-Grade Quality".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    try:
        # 1. Parse donor file
        df = parse_donor_file(DONOR_FILE)

        # 2. Aggregate by donor
        donor_stats = aggregate_donor_stats(df)

        # 3. Load database contacts
        conn = psycopg2.connect(DATABASE_URL)
        contacts, name_lookup = load_database_contacts(conn)

        # 4. Match donors to contacts
        matches, new_donors = match_donors_to_contacts(donor_stats, name_lookup)

        # 5. Analyze enrichment potential
        needs_enrichment, already_has_data = analyze_enrichment_potential(matches)

        # 6. Analyze new donors
        analyze_new_donors(new_donors)

        # 7. Generate summary report
        generate_summary_report(donor_stats, matches, new_donors, needs_enrichment)

        # Close connection
        conn.close()

        logger.info("")
        logger.info("✅ Analysis completed successfully")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
