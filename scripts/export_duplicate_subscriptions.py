#!/usr/bin/env python3
"""
Export contacts with duplicate active subscriptions for manual review in Kajabi
Creates CSV file with subscription details for cross-reference
"""

import os
import sys
import csv
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def main():
    """Export duplicate subscriptions for manual review"""
    print("="*80)
    print("DUPLICATE SUBSCRIPTIONS EXPORT")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*80)

    conn = get_db_connection()

    # Query to get contacts with multiple active subscriptions
    query = """
    SELECT
      c.id as contact_id,
      c.email,
      c.first_name,
      c.last_name,
      c.kajabi_id,
      c.kajabi_member_id,
      COUNT(s.id) as active_subscription_count,
      STRING_AGG(
        s.id::text || '|' ||
        COALESCE(s.kajabi_subscription_id, 'NO_ID') || '|' ||
        COALESCE(s.billing_cycle, '') || '|' ||
        COALESCE(s.amount::text, '0') || '|' ||
        COALESCE(s.status::text, '') || '|' ||
        COALESCE(TO_CHAR(s.created_at, 'YYYY-MM-DD'), '') || '|' ||
        COALESCE(TO_CHAR(s.updated_at, 'YYYY-MM-DD'), ''),
        ';;'
        ORDER BY s.amount DESC, s.created_at DESC
      ) as subscription_details,
      SUM(s.amount) as total_subscription_value
    FROM contacts c
    JOIN subscriptions s ON c.id = s.contact_id
    WHERE s.status = 'active'
      AND s.deleted_at IS NULL
      AND c.deleted_at IS NULL
    GROUP BY c.id, c.email, c.first_name, c.last_name, c.kajabi_id, c.kajabi_member_id
    HAVING COUNT(s.id) > 1
    ORDER BY COUNT(s.id) DESC, c.last_name, c.first_name;
    """

    print("\nQuerying database for contacts with multiple active subscriptions...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()

    print(f"✓ Found {len(results)} contacts with multiple active subscriptions")

    # Parse subscription details and create detailed rows
    detailed_rows = []

    for contact in results:
        # Parse subscription details
        sub_details = contact['subscription_details'].split(';;')

        for i, sub_detail in enumerate(sub_details, 1):
            parts = sub_detail.split('|')
            if len(parts) == 7:
                db_id, kajabi_sub_id, billing_cycle, amount, status, created, updated = parts

                detailed_rows.append({
                    'contact_id': contact['contact_id'],
                    'email': contact['email'],
                    'first_name': contact['first_name'],
                    'last_name': contact['last_name'],
                    'kajabi_id': contact['kajabi_id'] or '',
                    'kajabi_member_id': contact['kajabi_member_id'] or '',
                    'total_active_subs': contact['active_subscription_count'],
                    'total_value': float(contact['total_subscription_value']),
                    'sub_number': i,
                    'db_subscription_id': db_id,
                    'kajabi_subscription_id': kajabi_sub_id,
                    'billing_cycle': billing_cycle,
                    'amount': float(amount) if amount != '0' else 0,
                    'status': status,
                    'created_date': created,
                    'updated_date': updated
                })

    # Write to CSV
    output_file = 'REVIEW_duplicate_subscriptions.csv'

    print(f"\nWriting detailed export to {output_file}...")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'contact_id', 'email', 'first_name', 'last_name',
            'kajabi_id', 'kajabi_member_id',
            'total_active_subs', 'total_value',
            'sub_number', 'db_subscription_id', 'kajabi_subscription_id',
            'billing_cycle', 'amount', 'status',
            'created_date', 'updated_date'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_rows)

    print(f"✓ Wrote {len(detailed_rows)} subscription rows for {len(results)} contacts")

    # Also create a summary file
    summary_file = 'REVIEW_duplicate_subscriptions_summary.csv'

    print(f"\nWriting summary export to {summary_file}...")

    summary_rows = []
    for contact in results:
        # Parse subscription details for summary
        sub_details = contact['subscription_details'].split(';;')

        subscriptions_list = []
        for sub_detail in sub_details:
            parts = sub_detail.split('|')
            if len(parts) == 7:
                _, kajabi_sub_id, billing_cycle, amount, status, _, _ = parts
                subscriptions_list.append(f"{billing_cycle} ${amount} (ID:{kajabi_sub_id})")

        summary_rows.append({
            'email': contact['email'],
            'full_name': f"{contact['first_name']} {contact['last_name']}",
            'kajabi_id': contact['kajabi_id'] or '',
            'kajabi_member_id': contact['kajabi_member_id'] or '',
            'active_sub_count': contact['active_subscription_count'],
            'total_monthly_value': float(contact['total_subscription_value']),
            'subscription_1': subscriptions_list[0] if len(subscriptions_list) > 0 else '',
            'subscription_2': subscriptions_list[1] if len(subscriptions_list) > 1 else '',
            'subscription_3': subscriptions_list[2] if len(subscriptions_list) > 2 else '',
            'action_needed': 'Review in Kajabi - which subscription(s) are actually active?'
        })

    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'email', 'full_name', 'kajabi_id', 'kajabi_member_id',
            'active_sub_count', 'total_monthly_value',
            'subscription_1', 'subscription_2', 'subscription_3',
            'action_needed'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"✓ Wrote {len(summary_rows)} contacts to summary file")

    # Print statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)

    total_subs = sum(r['active_subscription_count'] for r in results)
    total_value = sum(float(r['total_subscription_value']) for r in results)
    three_or_more = sum(1 for r in results if r['active_subscription_count'] >= 3)

    print(f"\nContacts with duplicate subscriptions: {len(results)}")
    print(f"Total active subscriptions for these contacts: {total_subs}")
    print(f"Expected unique subscriptions: {len(results)}")
    print(f"Duplicate subscriptions to review: {total_subs - len(results)}")
    print(f"Contacts with 3+ active subscriptions: {three_or_more}")
    print(f"Total monthly value (including duplicates): ${total_value:.2f}")

    # Show top 10 examples
    print("\n" + "="*80)
    print("TOP 10 EXAMPLES")
    print("="*80)

    for i, contact in enumerate(results[:10], 1):
        print(f"\n{i}. {contact['first_name']} {contact['last_name']} ({contact['email']})")
        print(f"   Kajabi ID: {contact['kajabi_id']}")
        print(f"   Active subscriptions: {contact['active_subscription_count']}")
        print(f"   Total value: ${float(contact['total_subscription_value']):.2f}/month")

        sub_details = contact['subscription_details'].split(';;')
        for j, sub_detail in enumerate(sub_details, 1):
            parts = sub_detail.split('|')
            if len(parts) == 7:
                _, kajabi_sub_id, billing_cycle, amount, status, created, _ = parts
                print(f"   Sub {j}: {billing_cycle} ${amount} (Kajabi ID: {kajabi_sub_id}, Created: {created})")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print(f"\n1. Open {summary_file} for a quick overview")
    print(f"2. Open {output_file} for detailed subscription data")
    print("3. Cross-reference with Kajabi using the kajabi_id or email")
    print("4. Determine which subscriptions are actually active in Kajabi")
    print("5. Return to this session with your findings")
    print("\nRecommended: Focus on contacts with 3+ subscriptions first (highest priority)")

    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
