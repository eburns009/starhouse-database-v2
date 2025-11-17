#!/usr/bin/env python3
"""
Export validated addresses for TrueNCOA NCOA processing
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

def main():
    logger.info("")
    logger.info("=" * 80)
    logger.info("EXPORTING ADDRESSES FOR TRUENCOA NCOA PROCESSING")
    logger.info("=" * 80)
    logger.info("")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get all validated addresses
    # Prioritize by: 1) Paying customers, 2) Total spent, 3) Recent activity
    cursor.execute("""
        SELECT
            id,
            first_name,
            last_name,
            email,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            phone,
            total_spent,
            usps_dpv_confirmation,
            created_at,
            updated_at
        FROM contacts
        WHERE address_validated = true
          AND usps_dpv_confirmation IN ('Y', 'D', 'S')
        ORDER BY
            total_spent DESC NULLS LAST,
            updated_at DESC
    """)

    contacts = cursor.fetchall()

    logger.info(f"Found {len(contacts)} validated addresses")
    logger.info("")

    # Categorize
    paying = [c for c in contacts if c['total_spent'] and c['total_spent'] > 0]
    non_paying = [c for c in contacts if not c['total_spent'] or c['total_spent'] == 0]

    logger.info(f"Breakdown:")
    logger.info(f"  Paying customers:     {len(paying):,}")
    logger.info(f"  Non-paying contacts:  {len(non_paying):,}")
    logger.info("")

    # Export to TrueNCOA format
    output_file = '/tmp/truencoa_mailing_list.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        # TrueNCOA required/recommended fields
        fieldnames = [
            'ID',           # Input ID (for tracking)
            'FirstName',
            'LastName',
            'Address1',
            'Address2',
            'City',
            'State',
            'PostalCode',
            'Email',        # Optional but useful
            'Phone',        # Optional but useful
            'TotalSpent',   # For your reference
            'DPV'          # For your reference
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for contact in contacts:
            # Format postal code - preserve leading zeros
            postal = contact['postal_code'] or ''
            if postal and '-' not in postal and len(postal) == 5:
                postal = f"'{postal}"  # Prevent Excel from dropping leading zeros

            writer.writerow({
                'ID': contact['id'],
                'FirstName': contact['first_name'] or '',
                'LastName': contact['last_name'] or '',
                'Address1': contact['address_line_1'] or '',
                'Address2': contact['address_line_2'] or '',
                'City': contact['city'] or '',
                'State': contact['state'] or '',
                'PostalCode': postal,
                'Email': contact['email'] or '',
                'Phone': contact['phone'] or '',
                'TotalSpent': f"${contact['total_spent']:.2f}" if contact['total_spent'] else '$0.00',
                'DPV': contact['usps_dpv_confirmation'] or ''
            })

    logger.info("=" * 80)
    logger.info("✅ EXPORT COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"File: {output_file}")
    logger.info(f"Total records: {len(contacts):,}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Go to https://app.truencoa.com/")
    logger.info("2. Log in to your account")
    logger.info("3. Upload: truencoa_mailing_list.csv")
    logger.info("4. Wait for NCOA processing")
    logger.info("5. Download results with updated addresses")
    logger.info("")
    logger.info("Expected results:")
    logger.info("  • 5-10% of addresses will have move updates")
    logger.info(f"  • Estimated: {int(len(contacts) * 0.075):,} address updates")
    logger.info("  • You'll get new addresses + move dates")
    logger.info("")

    conn.close()

if __name__ == '__main__':
    main()
