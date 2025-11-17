#!/usr/bin/env python3
"""
FAANG-Quality Name Enrichment for High-Value Customers
Priority 1: Fix 37 paying customers with missing names ($5,928 total revenue)

Enrichment sources:
1. Debbie's Google Contacts export
2. Email address parsing (first.last@domain pattern)
3. Website/domain research
4. Manual review list for remaining
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import re
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/enrich_high_value_names_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
GOOGLE_CONTACTS_FILE = "kajabi 3 files review/debbie Google Contacts.csv"


def load_high_value_customers(conn):
    """Load the 37 paying customers with missing names"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("LOADING HIGH-VALUE CUSTOMERS WITH MISSING NAMES")
    logger.info("=" * 80)
    logger.info("")

    query = """
        SELECT
            id,
            email,
            first_name,
            last_name,
            phone,
            address_line_1,
            city,
            state,
            postal_code,
            source_system,
            total_spent,
            transaction_count,
            paypal_business_name
        FROM contacts
        WHERE (first_name IS NULL OR first_name = '' OR TRIM(first_name) = '')
           OR (last_name IS NULL OR last_name = '' OR TRIM(last_name) = '')
        AND total_spent > 0
        ORDER BY total_spent DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        customers = cursor.fetchall()

    total_revenue = sum(c['total_spent'] for c in customers)

    logger.info(f"Found {len(customers)} paying customers with missing names")
    logger.info(f"Total revenue: ${total_revenue:,.2f}")
    logger.info("")

    logger.info("Top 10 by revenue:")
    for i, c in enumerate(customers[:10], 1):
        logger.info(f"  {i:2d}. {c['email']:45s} ${c['total_spent']:8.2f}")
    logger.info("")

    return customers


def load_google_contacts():
    """Load Debbie's Google Contacts export"""
    logger.info("=" * 80)
    logger.info("LOADING GOOGLE CONTACTS EXPORT")
    logger.info("=" * 80)
    logger.info("")

    google_file = Path(GOOGLE_CONTACTS_FILE)

    if not google_file.exists():
        logger.warning(f"Google Contacts file not found: {GOOGLE_CONTACTS_FILE}")
        logger.warning("Will skip Google Contacts enrichment")
        logger.info("")
        return {}

    google_lookup = {}

    with open(google_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get email addresses from Google export
            emails = []
            for i in range(1, 10):  # E-mail 1 Address through E-mail 9 Address
                email_key = f'E-mail {i} - Value'
                if email_key in row and row[email_key]:
                    emails.append(row[email_key].lower().strip())

            # Get name
            given_name = row.get('Given Name', '').strip()
            family_name = row.get('Family Name', '').strip()

            # Store in lookup by email
            for email in emails:
                if email and (given_name or family_name):
                    google_lookup[email] = {
                        'first_name': given_name,
                        'last_name': family_name,
                        'full_name': f"{given_name} {family_name}".strip()
                    }

    logger.info(f"Loaded {len(google_lookup)} contacts from Google export")
    logger.info("")

    return google_lookup


def parse_name_from_email(email):
    """
    Try to extract name from email address patterns like:
    - first.last@domain.com
    - firstname.lastname@domain.com
    - flast@domain.com
    """
    if not email:
        return None, None

    # Get local part (before @)
    local_part = email.split('@')[0].lower()

    # Remove numbers and special chars except dots and underscores
    cleaned = re.sub(r'[0-9]+', '', local_part)

    # Common patterns to try
    patterns = [
        # first.last or first_last
        (r'^([a-z]+)[._]([a-z]+)$', lambda m: (m.group(1).title(), m.group(2).title())),
        # firstname (no last name)
        (r'^([a-z]{3,})$', lambda m: (m.group(1).title(), None)),
    ]

    for pattern, extractor in patterns:
        match = re.match(pattern, cleaned)
        if match:
            try:
                first, last = extractor(match)
                # Validate - must be reasonable names
                if first and len(first) >= 2:
                    return first, last
            except:
                continue

    return None, None


def enrich_from_domain_research(email):
    """
    For professional emails, try to extract business name or useful info
    Returns: (first_name, last_name, notes)
    """
    if not email or '@' not in email:
        return None, None, None

    domain = email.split('@')[1].lower()
    local_part = email.split('@')[0].lower()

    # Known professional domains that might have name patterns
    professional_patterns = {
        'healingharmonyllc.com': 'Healing Harmony',
        'rootsofwellnessayurveda.com': 'Roots of Wellness Ayurveda',
        'depthsoffeminine.earth': 'Depths of Feminine',
        'sollunahealing.org': 'Sol Luna Healing',
    }

    # Check if domain matches known business
    for known_domain, business_name in professional_patterns.items():
        if domain == known_domain:
            # Try to extract name from local part
            first, last = parse_name_from_email(email)
            if first:
                return first, last, f"Business: {business_name}"

    return None, None, None


def analyze_enrichment_potential(customers, google_lookup):
    """Analyze which customers can be enriched from which sources"""
    logger.info("=" * 80)
    logger.info("ANALYZING ENRICHMENT POTENTIAL")
    logger.info("=" * 80)
    logger.info("")

    enrichable = {
        'google_contacts': [],
        'email_parsing': [],
        'domain_research': [],
        'manual_review': []
    }

    for customer in customers:
        email = customer['email'].lower()
        enriched = False

        # Check Google Contacts
        if email in google_lookup:
            google_data = google_lookup[email]
            if google_data['first_name'] or google_data['last_name']:
                enrichable['google_contacts'].append({
                    'customer': customer,
                    'source': 'Google Contacts',
                    'first_name': google_data['first_name'],
                    'last_name': google_data['last_name']
                })
                enriched = True
                continue

        # Try email parsing
        if not enriched:
            first, last = parse_name_from_email(customer['email'])
            if first:
                enrichable['email_parsing'].append({
                    'customer': customer,
                    'source': 'Email Pattern',
                    'first_name': first,
                    'last_name': last,
                    'confidence': 'MEDIUM - Needs verification'
                })
                enriched = True
                continue

        # Try domain research
        if not enriched:
            first, last, notes = enrich_from_domain_research(customer['email'])
            if first or notes:
                enrichable['domain_research'].append({
                    'customer': customer,
                    'source': 'Domain Research',
                    'first_name': first,
                    'last_name': last,
                    'notes': notes
                })
                enriched = True
                continue

        # Needs manual review
        if not enriched:
            enrichable['manual_review'].append({
                'customer': customer,
                'source': 'MANUAL REVIEW NEEDED'
            })

    # Report results
    logger.info("Enrichment source breakdown:")
    logger.info(f"  Google Contacts:     {len(enrichable['google_contacts']):3d} ({len(enrichable['google_contacts'])/len(customers)*100:5.1f}%)")
    logger.info(f"  Email parsing:       {len(enrichable['email_parsing']):3d} ({len(enrichable['email_parsing'])/len(customers)*100:5.1f}%)")
    logger.info(f"  Domain research:     {len(enrichable['domain_research']):3d} ({len(enrichable['domain_research'])/len(customers)*100:5.1f}%)")
    logger.info(f"  Manual review:       {len(enrichable['manual_review']):3d} ({len(enrichable['manual_review'])/len(customers)*100:5.1f}%)")
    logger.info("")

    return enrichable


def preview_enrichments(enrichable):
    """Preview what will be enriched"""
    logger.info("=" * 80)
    logger.info("PREVIEW: PROPOSED NAME ENRICHMENTS")
    logger.info("=" * 80)
    logger.info("")

    # Google Contacts enrichments
    if enrichable['google_contacts']:
        logger.info("FROM GOOGLE CONTACTS (High Confidence):")
        logger.info("")
        for i, item in enumerate(enrichable['google_contacts'][:10], 1):
            c = item['customer']
            logger.info(f"{i:2d}. {c['email']:45s} ${c['total_spent']:8.2f}")
            logger.info(f"    Current: (no name)")
            logger.info(f"    New:     {item['first_name']} {item['last_name']}")
            logger.info("")

    # Email parsing enrichments
    if enrichable['email_parsing']:
        logger.info("FROM EMAIL PATTERN PARSING (Medium Confidence - Verify):")
        logger.info("")
        for i, item in enumerate(enrichable['email_parsing'][:10], 1):
            c = item['customer']
            logger.info(f"{i:2d}. {c['email']:45s} ${c['total_spent']:8.2f}")
            logger.info(f"    Parsed:  {item['first_name']} {item.get('last_name', '(unknown)')}")
            logger.info(f"    Confidence: {item.get('confidence', 'MEDIUM')}")
            logger.info("")

    # Manual review needed
    if enrichable['manual_review']:
        logger.info("NEEDS MANUAL REVIEW (No auto-enrichment available):")
        logger.info("")
        for i, item in enumerate(enrichable['manual_review'][:10], 1):
            c = item['customer']
            logger.info(f"{i:2d}. {c['email']:45s} ${c['total_spent']:8.2f}")
            if c['paypal_business_name']:
                logger.info(f"    Business: {c['paypal_business_name']}")
            logger.info("")


def execute_enrichment(conn, enrichable, dry_run=True):
    """Execute the name enrichment"""
    logger.info("=" * 80)
    if dry_run:
        logger.info("DRY RUN: Simulating Enrichment")
    else:
        logger.info("EXECUTING: Name Enrichment for High-Value Customers")
    logger.info("=" * 80)
    logger.info("")

    # Combine all enrichable items
    all_enrichments = (
        enrichable['google_contacts'] +
        enrichable['email_parsing'] +
        enrichable['domain_research']
    )

    if not all_enrichments:
        logger.warning("No enrichments available to execute")
        return 0

    logger.info(f"Total enrichments to apply: {len(all_enrichments)}")
    logger.info("")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Would update {len(all_enrichments)} customer names")
        logger.info("")
        return len(all_enrichments)

    # Execute updates
    updated_count = 0

    try:
        with conn.cursor() as cursor:
            for item in all_enrichments:
                customer = item['customer']
                first_name = item.get('first_name')
                last_name = item.get('last_name')

                if not first_name and not last_name:
                    continue

                # Build UPDATE statement
                # Escape single quotes for SQL
                escaped_first = first_name.replace("'", "''") if first_name else None
                escaped_last = last_name.replace("'", "''") if last_name else None

                updates = []
                if escaped_first:
                    updates.append(f"first_name = '{escaped_first}'")
                if escaped_last:
                    updates.append(f"last_name = '{escaped_last}'")

                updates.append("updated_at = NOW()")

                update_sql = f"""
                    UPDATE contacts
                    SET {', '.join(updates)}
                    WHERE id = '{customer['id']}'
                """

                cursor.execute(update_sql)
                updated_count += 1

                logger.info(f"✅ Updated: {customer['email']} → {first_name} {last_name}")

            conn.commit()
            logger.info("")
            logger.info(f"✅ Successfully updated {updated_count} customers")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}")
        conn.rollback()
        raise

    return updated_count


def export_manual_review_list(enrichable):
    """Export customers needing manual review"""
    manual_review = enrichable['manual_review']

    if not manual_review:
        logger.info("No customers need manual review - all enriched!")
        return None

    output_file = "/tmp/high_value_manual_review.csv"

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Email', 'Revenue', 'Transactions', 'Phone', 'Address',
            'PayPal Business', 'Source System', 'Suggested First Name', 'Suggested Last Name'
        ])

        for item in manual_review:
            c = item['customer']
            writer.writerow([
                c['email'],
                f"${c['total_spent']:.2f}",
                c['transaction_count'],
                c['phone'] or '',
                f"{c['address_line_1'] or ''}, {c['city'] or ''}, {c['state'] or ''}".strip(', '),
                c['paypal_business_name'] or '',
                c['source_system'],
                '',  # Suggested first name - to fill manually
                ''   # Suggested last name - to fill manually
            ])

    logger.info("")
    logger.info(f"✅ Exported {len(manual_review)} customers for manual review: {output_file}")
    logger.info("")

    return output_file


def main():
    """Main enrichment workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "PRIORITY 1: HIGH-VALUE CUSTOMER NAME ENRICHMENT".center(78) + "║")
    logger.info("║" + "Target: 37 Paying Customers ($5,928 Revenue)".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")

        # Load high-value customers
        customers = load_high_value_customers(conn)

        # Load Google Contacts
        google_lookup = load_google_contacts()

        # Analyze enrichment potential
        enrichable = analyze_enrichment_potential(customers, google_lookup)

        # Preview enrichments
        preview_enrichments(enrichable)

        # Execute enrichment (DRY RUN first)
        logger.info("=" * 80)
        logger.info("EXECUTION MODE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Running in DRY RUN mode - no changes will be made")
        logger.info("")
        logger.info("To execute enrichment:")
        logger.info("  1. Review the preview above")
        logger.info("  2. Edit this script: execute_enrichment(conn, enrichable, dry_run=False)")
        logger.info("  3. Re-run the script")
        logger.info("")

        # DRY RUN
        execute_enrichment(conn, enrichable, dry_run=True)

        # Export manual review list
        export_manual_review_list(enrichable)

        # Uncomment to execute for real:
        # execute_enrichment(conn, enrichable, dry_run=False)

        conn.close()

        logger.info("=" * 80)
        logger.info("✅ ANALYSIS COMPLETE")
        logger.info("=" * 80)
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
