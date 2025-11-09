#!/usr/bin/env python3
"""
Analyze addresses in transactions.csv to identify enrichment opportunities
"""
import csv
import sys

csv_file = '/workspaces/starhouse-database-v2/data/production/transactions.csv'

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    total = 0
    with_address = 0
    with_phone = 0
    with_both = 0
    unique_emails = set()
    unique_emails_with_address = set()
    unique_emails_with_phone = set()

    samples_with_data = []

    for row in reader:
        total += 1

        email = row.get('Customer Email', '').strip().lower()
        if email:
            unique_emails.add(email)

        has_address = bool(
            row.get('Address', '').strip() or
            row.get('City', '').strip() or
            row.get('State', '').strip() or
            row.get('Zipcode', '').strip()
        )
        has_phone = bool(row.get('Phone', '').strip())

        if has_address:
            with_address += 1
            if email:
                unique_emails_with_address.add(email)

        if has_phone:
            with_phone += 1
            if email:
                unique_emails_with_phone.add(email)

        if has_address and has_phone:
            with_both += 1

        if has_address or has_phone:
            if len(samples_with_data) < 10:
                samples_with_data.append({
                    'email': email,
                    'address': row.get('Address', ''),
                    'city': row.get('City', ''),
                    'state': row.get('State', ''),
                    'zipcode': row.get('Zipcode', ''),
                    'phone': row.get('Phone', ''),
                    'amount': row.get('Amount', ''),
                    'date': row.get('Created At', '')
                })

    print(f"{'=' * 100}")
    print("TRANSACTION ADDRESS DATA ANALYSIS")
    print(f"{'=' * 100}\n")

    print(f"Total transactions: {total:,}")
    print(f"Transactions with address data: {with_address:,} ({with_address/total*100:.1f}%)")
    print(f"Transactions with phone data: {with_phone:,} ({with_phone/total*100:.1f}%)")
    print(f"Transactions with both address and phone: {with_both:,} ({with_both/total*100:.1f}%)")
    print()

    print(f"Unique customer emails: {len(unique_emails):,}")
    print(f"Unique customers with addresses: {len(unique_emails_with_address):,} ({len(unique_emails_with_address)/len(unique_emails)*100:.1f}%)")
    print(f"Unique customers with phones: {len(unique_emails_with_phone):,} ({len(unique_emails_with_phone)/len(unique_emails)*100:.1f}%)")
    print()

    print(f"{'=' * 100}")
    print("ENRICHMENT POTENTIAL")
    print(f"{'=' * 100}")
    print(f"Up to {len(unique_emails_with_address):,} contacts could have addresses added")
    print(f"Up to {len(unique_emails_with_phone):,} contacts could have phone numbers added")
    print()

    print(f"{'=' * 100}")
    print("SAMPLE TRANSACTIONS WITH ADDRESS/PHONE DATA (first 10)")
    print(f"{'=' * 100}\n")

    for i, sample in enumerate(samples_with_data, 1):
        print(f"{i}. {sample['email']} - {sample['date']} - ${sample['amount']}")
        if sample['address'] or sample['city']:
            print(f"   Address: {sample['address']}, {sample['city']}, {sample['state']} {sample['zipcode']}")
        if sample['phone']:
            print(f"   Phone: {sample['phone']}")
        print()
