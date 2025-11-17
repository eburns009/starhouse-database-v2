#!/usr/bin/env python3
"""
Investigate billing discrepancies for contacts charged after cancellation.
"""

import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import get_database_url

# Database connection
DATABASE_URL = get_database_url()

# Affected contacts with cancellation dates
AFFECTED_CONTACTS = [
    {
        'email': 'anthony@crowninternational.us',
        'name': 'Anthony Smith',
        'kajabi_canceled': '2023-08-16',
        'payments_after': 21,
        'amount_per_payment': 22,
        'total_overcharged': 462,
        'last_charge': '2025-09-16'
    },
    {
        'email': 'chris@inspire.graphics',
        'name': 'Chris Loving-Campos',
        'kajabi_canceled': '2024-11-16',
        'payments_after': 10,
        'amount_per_payment': 22,
        'total_overcharged': 220,
        'last_charge': '2025-10-16'
    },
    {
        'email': 'denisehatzis@gmail.com',
        'name': 'Dionisia Hatzis',
        'kajabi_canceled': '2025-03-03',
        'payments_after': 8,
        'amount_per_payment': 33,
        'total_overcharged': 264,
        'last_charge': '2025-10-03'
    },
    {
        'email': 'hildykane@yahoo.com',
        'name': 'Hildy Kane',
        'kajabi_canceled': '2025-09-23',
        'payments_after': 2,
        'amount_per_payment': 22,
        'total_overcharged': 44,
        'last_charge': '2025-10-23'
    }
]

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("BILLING DISCREPANCY INVESTIGATION")
    print("=" * 80)
    print()

    total_found_overcharges = 0

    for contact_info in AFFECTED_CONTACTS:
        email = contact_info['email']
        name = contact_info['name']
        canceled_date = datetime.strptime(contact_info['kajabi_canceled'], '%Y-%m-%d')

        print(f"\n{'=' * 80}")
        print(f"Contact: {name} ({email})")
        print(f"Kajabi Cancellation Date: {contact_info['kajabi_canceled']}")
        print(f"Expected overcharges: ${contact_info['total_overcharged']}")
        print('=' * 80)

        # Find contact in database
        cursor.execute("""
            SELECT
                id,
                first_name,
                last_name,
                email,
                paypal_email,
                paypal_subscription_reference
            FROM contacts
            WHERE email = %s OR paypal_email = %s
        """, (email, email))

        contact = cursor.fetchone()

        if not contact:
            print(f"⚠️  WARNING: Contact not found in database!")
            continue

        print(f"\n✓ Found contact: {contact['first_name']} {contact['last_name']}")
        print(f"  Contact ID: {contact['id']}")
        print(f"  PayPal Email: {contact['paypal_email']}")
        print(f"  PayPal Subscription: {contact['paypal_subscription_reference']}")

        # Find all PayPal transactions after cancellation date
        cursor.execute("""
            SELECT
                id,
                transaction_date,
                amount,
                status,
                external_transaction_id,
                source_system,
                payment_processor,
                created_at
            FROM transactions
            WHERE contact_id = %s
                AND (source_system = 'paypal' OR payment_processor = 'paypal')
                AND transaction_date >= %s
            ORDER BY transaction_date ASC
        """, (contact['id'], canceled_date))

        transactions = cursor.fetchall()

        if not transactions:
            print(f"\n⚠️  No PayPal transactions found after {contact_info['kajabi_canceled']}")
            continue

        print(f"\n📋 Found {len(transactions)} PayPal transactions after cancellation:")
        print(f"\n{'Date':<12} {'Amount':<10} {'Status':<15} {'External ID':<30}")
        print('-' * 80)

        contact_total = 0
        for txn in transactions:
            print(f"{str(txn['transaction_date']):<12} ${txn['amount']:<9.2f} {txn['status']:<15} {txn['external_transaction_id'] or 'N/A':<30}")
            contact_total += float(txn['amount'])

        print('-' * 80)
        print(f"Total charged after cancellation: ${contact_total:.2f}")
        print(f"Expected from report: ${contact_info['total_overcharged']:.2f}")

        if abs(contact_total - contact_info['total_overcharged']) < 1:
            print("✓ Matches expected amount")
        else:
            print(f"⚠️  Discrepancy: ${abs(contact_total - contact_info['total_overcharged']):.2f}")

        total_found_overcharges += contact_total

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total overcharges found in database: ${total_found_overcharges:.2f}")
    print(f"Total expected from report: $990.00")
    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
