#!/usr/bin/env python3
"""
Export TrueNCOA Exceptions with Corrected ZIP Codes

Creates a CSV file with the 706 exception records, using correct ZIP codes
from input_PostalCode field. This CSV can be uploaded back to TrueNCOA for
re-processing to detect moves.

Author: StarHouse CRM
Date: 2025-11-15
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import get_database_url

DATABASE_URL = get_database_url()

def main():
    # Read TrueNCOA exceptions
    print("Reading TrueNCOA exceptions...")
    exceptions = []

    with open('kajabi 3 files review/truencoa.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process exception records (Status = 'N')
            if row.get('Address Status') == 'N':
                # Get correct ZIP from input
                correct_zip = row.get('input_PostalCode', '').strip()

                # Skip if no valid address data
                if not correct_zip:
                    continue

                exceptions.append({
                    'id': row['input_ID'],
                    'first_name': row['input_FirstName'],
                    'last_name': row['input_LastName'],
                    'address1': row['input_Address1'],
                    'address2': row['input_Address2'],
                    'city': row['input_City'],
                    'state': row['input_State'],
                    'postal_code': correct_zip,  # CORRECTED ZIP
                    'email': row['input_Email'],
                    'phone': row['input_Phone'],
                    'total_spent': row['input_TotalSpent'],
                    'dpv': row['input_DPV']
                })

    print(f"Found {len(exceptions)} exception records with valid data")

    # Get additional data from database (if needed)
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Create export CSV
    output_file = 'truencoa_exceptions_corrected.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['ID', 'FirstName', 'LastName', 'Address1', 'Address2',
                     'City', 'State', 'PostalCode', 'Email', 'Phone', 'TotalSpent', 'DPV']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for exc in exceptions:
            writer.writerow({
                'ID': exc['id'],
                'FirstName': exc['first_name'],
                'LastName': exc['last_name'],
                'Address1': exc['address1'],
                'Address2': exc['address2'],
                'City': exc['city'],
                'State': exc['state'],
                'PostalCode': exc['postal_code'],  # CORRECTED
                'Email': exc['email'],
                'Phone': exc['phone'],
                'TotalSpent': exc['total_spent'],
                'DPV': exc['dpv']
            })

    cursor.close()
    conn.close()

    print(f"\n✅ Export complete!")
    print(f"File: {output_file}")
    print(f"Records: {len(exceptions):,}")
    print(f"\nThis file can now be uploaded to TrueNCOA for re-processing.")
    print(f"TrueNCOA will detect moves for these {len(exceptions)} contacts.")

if __name__ == '__main__':
    main()
