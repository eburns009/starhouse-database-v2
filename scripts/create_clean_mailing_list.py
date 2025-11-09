#!/usr/bin/env python3
"""
Create a clean mailing list from USPS validated data.
- No segmentation or filtering
- Keep leading zeros in ZIP codes
- Remove +4 extension (use 5-digit ZIP only)
"""

import csv

def create_clean_mailing_list():
    input_file = 'data/donors_us_ready_for_validation-output (1).csv'
    output_file = 'clean_mailing_list.csv'

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)

        # Define output columns for clean mailing list
        fieldnames = [
            'FirstName',
            'LastName',
            'FullName',
            'BusinessName',
            'AddressLine1',
            'AddressLine2',
            'City',
            'State',
            'PostalCode',
            'Country'
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        valid_count = 0
        skipped_count = 0

        for row in reader:
            # Use USPS validated data (columns have square brackets)
            city = row.get('[city_name]', '').strip()
            state = row.get('[state_abbreviation]', '').strip()

            # Skip if no valid address
            if not city or not state:
                skipped_count += 1
                continue

            # Use the standardized delivery line from USPS validation
            address_line1 = row.get('[delivery_line_1]', '').strip()
            address_line2 = row.get('[delivery_line_2]', '').strip()

            # If no standardized address, fall back to original
            if not address_line1:
                address_line1 = row.get('AddressLine1', '').strip()
                address_line2 = row.get('AddressLine2', '').strip()

            # Get 5-digit ZIP code only (no +4)
            # The '[zipcode]' field is the base 5-digit code
            postal_code = row.get('[zipcode]', '').strip()

            # Ensure leading zero is preserved by treating as string
            if postal_code and len(postal_code) < 5:
                postal_code = postal_code.zfill(5)

            clean_row = {
                'FirstName': row.get('FirstName', '').strip(),
                'LastName': row.get('LastName', '').strip(),
                'FullName': row.get('FullName', '').strip(),
                'BusinessName': row.get('BusinessName', '').strip(),
                'AddressLine1': address_line1,
                'AddressLine2': address_line2,
                'City': city,
                'State': state,
                'PostalCode': postal_code,
                'Country': 'US'
            }

            writer.writerow(clean_row)
            valid_count += 1

        print(f"\n✓ Clean mailing list created: {output_file}")
        print(f"  - Valid addresses: {valid_count:,}")
        print(f"  - Skipped (no valid address): {skipped_count:,}")
        print(f"\nFormat:")
        print(f"  - 5-digit ZIP codes only (no +4)")
        print(f"  - Leading zeros preserved")
        print(f"  - No segmentation or filtering")
        print(f"  - Standardized USPS addresses")

if __name__ == '__main__':
    create_clean_mailing_list()
