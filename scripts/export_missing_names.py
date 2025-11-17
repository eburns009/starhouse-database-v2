#!/usr/bin/env python3
"""
Export Contacts with Missing Names for Review
Identifies data quality issues and provides enrichment opportunities
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import logging
from datetime import datetime
from pathlib import Path
from db_config import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/export_missing_names_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = get_database_url()
OUTPUT_FILE = "/tmp/contacts_missing_names.csv"


def export_missing_names(conn):
    """Export contacts with missing first_name or last_name"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("EXPORTING CONTACTS WITH MISSING NAMES")
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
            created_at,
            updated_at,
            paypal_email,
            paypal_first_name,
            paypal_last_name,
            paypal_business_name
        FROM contacts
        WHERE (first_name IS NULL OR first_name = '' OR TRIM(first_name) = '')
           OR (last_name IS NULL OR last_name = '' OR TRIM(last_name) = '')
        ORDER BY total_spent DESC NULLS LAST, created_at DESC
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        contacts = cursor.fetchall()

    logger.info(f"Found {len(contacts)} contacts with missing names")
    logger.info("")

    # Write to CSV
    if contacts:
        fieldnames = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'address_line_1', 'city', 'state', 'postal_code',
            'source_system', 'total_spent', 'transaction_count',
            'created_at', 'updated_at',
            'paypal_email', 'paypal_first_name', 'paypal_last_name', 'paypal_business_name',
            'enrichment_notes'
        ]

        with open(OUTPUT_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for contact in contacts:
                row = dict(contact)
                # Add enrichment notes
                notes = []
                if contact['paypal_first_name'] and contact['paypal_last_name']:
                    notes.append(f"PayPal has: {contact['paypal_first_name']} {contact['paypal_last_name']}")
                if contact['paypal_business_name']:
                    notes.append(f"Business: {contact['paypal_business_name']}")
                if contact['total_spent'] and contact['total_spent'] > 0:
                    notes.append(f"Customer (${contact['total_spent']:.2f})")

                row['enrichment_notes'] = '; '.join(notes) if notes else 'No enrichment available'
                writer.writerow(row)

        logger.info(f"✅ Exported to: {OUTPUT_FILE}")
        logger.info("")

    return contacts


def analyze_missing_names(contacts):
    """Analyze missing names by source and enrichment potential"""
    logger.info("=" * 80)
    logger.info("ANALYSIS OF MISSING NAMES")
    logger.info("=" * 80)
    logger.info("")

    # By source
    by_source = {}
    for contact in contacts:
        source = contact['source_system'] or 'unknown'
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(contact)

    logger.info("Breakdown by source:")
    for source, group in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"  {source:20s} {len(group):4d} contacts")
    logger.info("")

    # Enrichment potential from PayPal data
    has_paypal_names = sum(1 for c in contacts if c['paypal_first_name'] and c['paypal_last_name'])
    has_business_name = sum(1 for c in contacts if c['paypal_business_name'])
    has_revenue = sum(1 for c in contacts if c['total_spent'] and c['total_spent'] > 0)

    logger.info("Enrichment potential:")
    logger.info(f"  Has PayPal name:         {has_paypal_names:4d} ({has_paypal_names/len(contacts)*100:.1f}%)")
    logger.info(f"  Has business name:       {has_business_name:4d} ({has_business_name/len(contacts)*100:.1f}%)")
    logger.info(f"  Has revenue (priority):  {has_revenue:4d} ({has_revenue/len(contacts)*100:.1f}%)")
    logger.info("")

    # High-value contacts (paid customers)
    high_value = [c for c in contacts if c['total_spent'] and c['total_spent'] > 0]
    if high_value:
        logger.info(f"HIGH PRIORITY: {len(high_value)} paying customers with missing names")
        logger.info("")
        logger.info("Top 10 by revenue:")
        for i, c in enumerate(sorted(high_value, key=lambda x: x['total_spent'], reverse=True)[:10], 1):
            paypal_name = f"{c['paypal_first_name'] or ''} {c['paypal_last_name'] or ''}".strip()
            business = c['paypal_business_name'] or ''
            enrichment = paypal_name or business or '(no data)'
            logger.info(f"  {i:2d}. {c['email']:40s} ${c['total_spent']:8.2f} → {enrichment}")
        logger.info("")


def generate_enrichment_script(contacts):
    """Generate SQL script to enrich from PayPal data"""
    logger.info("=" * 80)
    logger.info("GENERATING ENRICHMENT SCRIPT")
    logger.info("=" * 80)
    logger.info("")

    enrichable = [
        c for c in contacts
        if c['paypal_first_name'] and c['paypal_last_name']
    ]

    if enrichable:
        script_file = "/tmp/enrich_missing_names_from_paypal.sql"

        with open(script_file, 'w') as f:
            f.write("-- Auto-generated script to enrich missing names from PayPal data\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write(f"-- Contacts to enrich: {len(enrichable)}\n\n")
            f.write("BEGIN;\n\n")

            for contact in enrichable:
                # Escape single quotes for SQL
                first_name = contact['paypal_first_name'].replace("'", "''")
                last_name = contact['paypal_last_name'].replace("'", "''")

                f.write(f"-- {contact['email']} (${contact['total_spent'] or 0:.2f})\n")
                f.write(f"UPDATE contacts\nSET\n")
                f.write(f"    first_name = '{first_name}',\n")
                f.write(f"    last_name = '{last_name}',\n")
                f.write(f"    updated_at = NOW()\n")
                f.write(f"WHERE id = '{contact['id']}'\n")
                f.write(f"  AND (first_name IS NULL OR first_name = '');\n\n")

            f.write("COMMIT;\n")
            f.write(f"\n-- Run verification:\n")
            f.write(f"-- SELECT COUNT(*) FROM contacts WHERE (first_name IS NULL OR first_name = '');\n")

        logger.info(f"✅ Generated enrichment script: {script_file}")
        logger.info(f"   Will enrich {len(enrichable)} contacts from PayPal data")
        logger.info("")
        logger.info("To apply:")
        logger.info(f"  psql $DATABASE_URL < {script_file}")
        logger.info("")

        return script_file

    else:
        logger.info("⚠️  No contacts can be auto-enriched from PayPal data")
        logger.info("")
        return None


def main():
    """Main export workflow"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + "EXPORT CONTACTS WITH MISSING NAMES".center(78) + "║")
    logger.info("║" + "Data Quality Review & Enrichment Opportunities".center(78) + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connected to database")

        # Export missing names
        contacts = export_missing_names(conn)

        if not contacts:
            logger.info("✅ No contacts with missing names found!")
            logger.info("   Database quality is excellent.")
            logger.info("")
            return

        # Analyze missing names
        analyze_missing_names(contacts)

        # Generate enrichment script
        script_file = generate_enrichment_script(contacts)

        conn.close()

        logger.info("=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info("")
        logger.info(f"Total missing names:     {len(contacts)}")
        logger.info(f"Exported to CSV:         {OUTPUT_FILE}")
        if script_file:
            logger.info(f"Enrichment script:       {script_file}")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info(f"1. Review CSV: {OUTPUT_FILE}")
        logger.info("2. Cross-reference with:")
        logger.info("   - Google Contacts (Debbie's export)")
        logger.info("   - Original QuickBooks data")
        logger.info("   - PayPal transaction records")
        if script_file:
            logger.info(f"3. Run enrichment script to auto-fix PayPal data")
            logger.info("4. Manually enrich remaining contacts")
            logger.info("5. Consider removing low-value contacts with no data")
        logger.info("")
        logger.info("✅ EXPORT COMPLETED SUCCESSFULLY")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Export failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
