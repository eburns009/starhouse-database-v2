#!/usr/bin/env python3
"""
Import Kajabi subscriptions from CSV to database
Fills in the missing subscription records for contacts
"""

import csv
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

# Database connection string
DB_CONNECTION_STRING = 'PLACEHOLDER_USE_ENV_VAR'

def parse_date(date_str):
    """Parse Kajabi date format: 'Nov 28, 2025' or 'Sep 28, 2022'"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%b %d, %Y')
    except:
        return None

def map_kajabi_status(kajabi_status):
    """Map Kajabi status to our enum"""
    status_map = {
        'Active': 'active',
        'Canceled': 'canceled',
        'Expired': 'expired',
        'Paused': 'paused',
        'Trial': 'trial'
    }
    return status_map.get(kajabi_status, 'active')

def get_billing_cycle(interval):
    """Convert Kajabi interval to billing cycle"""
    if interval and 'month' in interval.lower():
        return 'monthly'
    elif interval and 'year' in interval.lower():
        return 'annual'
    return 'monthly'

def is_annual(interval):
    """Check if subscription is annual"""
    if not interval:
        return False
    return 'year' in interval.lower()

def main():
    print("🚀 Starting Kajabi Subscriptions Import...")

    conn = psycopg2.connect(DB_CONNECTION_STRING)
    cur = conn.cursor()

    try:
        # Read CSV
        csv_path = '/workspaces/starhouse-database-v2/data/kajabi_subscriptions.csv'

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            subscriptions = list(reader)

        print(f"📄 Found {len(subscriptions)} subscriptions in CSV")

        # Check existing
        cur.execute("SELECT kajabi_subscription_id FROM subscriptions WHERE kajabi_subscription_id IS NOT NULL")
        existing_kajabi_ids = {row[0] for row in cur.fetchall()}
        print(f"✅ {len(existing_kajabi_ids)} already in database")

        # Prepare data for insertion
        to_insert = []
        skipped = []
        errors = []

        for row in subscriptions:
            kajabi_sub_id = row.get('Kajabi Subscription ID', '').strip()
            customer_email = row.get('Customer Email', '').strip().lower()
            offer_id = row.get('Offer ID', '').strip()

            # Skip if already imported
            if kajabi_sub_id in existing_kajabi_ids:
                skipped.append(f"Already exists: {kajabi_sub_id}")
                continue

            # Skip if no essential data
            if not kajabi_sub_id or not customer_email:
                errors.append(f"Missing data: sub_id={kajabi_sub_id}, email={customer_email}")
                continue

            # Find contact by email
            cur.execute("""
                SELECT id FROM contacts
                WHERE LOWER(email) = %s
                   OR LOWER(email) LIKE %s
                LIMIT 1
            """, (customer_email, f"%{customer_email}%"))

            contact_result = cur.fetchone()
            if not contact_result:
                errors.append(f"Contact not found for email: {customer_email}")
                continue

            contact_id = contact_result[0]

            # Find membership product by offer_id
            membership_product_id = None
            if offer_id:
                # Check if this offer_id matches a PayPal item title in membership_products
                cur.execute("""
                    SELECT id FROM membership_products
                    WHERE %s = ANY(paypal_item_titles)
                    LIMIT 1
                """, (offer_id,))

                product_result = cur.fetchone()
                if product_result:
                    membership_product_id = product_result[0]

            # Parse dates
            status = map_kajabi_status(row.get('Status', 'Active'))
            amount = float(row.get('Amount', '0').replace('$', '').replace(',', ''))
            currency = row.get('Currency', 'USD')
            interval = row.get('Interval', 'Month')
            billing_cycle = get_billing_cycle(interval)
            is_annual_sub = is_annual(interval)
            created_at = parse_date(row.get('Created At'))
            next_payment_date = parse_date(row.get('Next Payment Date'))
            canceled_on = parse_date(row.get('Canceled On'))
            provider = row.get('Provider', 'PayPal')
            provider_id = row.get('Provider ID', '')

            to_insert.append({
                'contact_id': contact_id,
                'membership_product_id': membership_product_id,
                'kajabi_subscription_id': kajabi_sub_id,
                'status': status,
                'amount': amount,
                'currency': currency,
                'billing_cycle': billing_cycle,
                'is_annual': is_annual_sub,
                'start_date': created_at,
                'next_billing_date': next_payment_date,
                'cancellation_date': canceled_on,
                'payment_processor': provider,
                'paypal_subscription_reference': provider_id if provider.lower() == 'paypal' else None
            })

        print(f"\n📊 Summary:")
        print(f"  - To insert: {len(to_insert)}")
        print(f"  - Skipped (already exist): {len(skipped)}")
        print(f"  - Errors: {len(errors)}")

        if errors:
            print(f"\n⚠️  Errors encountered:")
            for err in errors[:10]:  # Show first 10
                print(f"    {err}")
            if len(errors) > 10:
                print(f"    ... and {len(errors) - 10} more")

        # Insert subscriptions
        if to_insert:
            print(f"\n💾 Inserting {len(to_insert)} subscriptions...")

            insert_query = """
                INSERT INTO subscriptions (
                    contact_id, membership_product_id, kajabi_subscription_id,
                    status, amount, currency, billing_cycle, is_annual,
                    start_date, next_billing_date, cancellation_date,
                    payment_processor, paypal_subscription_reference
                ) VALUES (
                    %(contact_id)s, %(membership_product_id)s, %(kajabi_subscription_id)s,
                    %(status)s, %(amount)s, %(currency)s, %(billing_cycle)s, %(is_annual)s,
                    %(start_date)s, %(next_billing_date)s, %(cancellation_date)s,
                    %(payment_processor)s, %(paypal_subscription_reference)s
                )
                ON CONFLICT (kajabi_subscription_id) DO NOTHING
            """

            inserted = 0
            for sub_data in to_insert:
                try:
                    cur.execute(insert_query, sub_data)
                    inserted += 1
                except Exception as e:
                    print(f"  ❌ Error inserting {sub_data['kajabi_subscription_id']}: {e}")

            conn.commit()
            print(f"✅ Successfully inserted {inserted} subscriptions!")

        # Verify for Bjorn
        print(f"\n🔍 Checking Bjorn's subscription...")
        cur.execute("""
            SELECT s.status, s.amount, mp.membership_level
            FROM subscriptions s
            LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
            WHERE s.kajabi_subscription_id = '2182427555'
        """)
        bjorn_sub = cur.fetchone()
        if bjorn_sub:
            print(f"✅ Bjorn's subscription found: status={bjorn_sub[0]}, amount=${bjorn_sub[1]}, level={bjorn_sub[2]}")
        else:
            print(f"⚠️  Bjorn's subscription not found in database")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    print(f"\n🎉 Import complete!")

if __name__ == '__main__':
    main()
