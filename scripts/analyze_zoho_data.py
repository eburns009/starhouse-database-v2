#!/usr/bin/env python3
"""
Analyze Zoho CSV data to identify enrichment opportunities
"""
import csv
import sys

csv_file = '/workspaces/starhouse-database-v2/data/production/v2_contacts.csv'

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    total = 0
    with_phone = 0
    with_address = 0
    with_both = 0
    with_zoho_id = 0

    for row in reader:
        total += 1

        has_phone = bool(row.get('phone', '').strip())
        has_address = bool(
            row.get('address_line_1', '').strip() or
            row.get('city', '').strip() or
            row.get('state', '').strip() or
            row.get('postal_code', '').strip()
        )
        has_zoho = bool(row.get('zoho_id', '').strip())

        if has_phone:
            with_phone += 1
        if has_address:
            with_address += 1
        if has_phone and has_address:
            with_both += 1
        if has_zoho:
            with_zoho_id += 1

    print(f"Total records: {total}")
    print(f"Records with phone: {with_phone}")
    print(f"Records with address: {with_address}")
    print(f"Records with both phone and address: {with_both}")
    print(f"Records with zoho_id: {with_zoho_id}")
    print(f"\nEnrichment potential: {with_phone + with_address} records have data to add")
