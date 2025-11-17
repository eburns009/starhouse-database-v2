#!/usr/bin/env python3
"""
Export Mailing List - Smart Address Selection

This script exports a mailing list using the mailing_list_priority system.
It selects the best address (billing or shipping) for each contact based on
quality scoring, and allows filtering by confidence level.

Usage:
  # Export high-confidence contacts only
  python3 scripts/export_mailing_list.py --min-confidence high

  # Export all contacts with very_high confidence
  python3 scripts/export_mailing_list.py --min-confidence very_high

  # Export all contacts (including low confidence)
  python3 scripts/export_mailing_list.py --min-confidence low

  # Include recent customers only (last 365 days)
  python3 scripts/export_mailing_list.py --min-confidence high --recent-customers 365

  # Export to custom file
  python3 scripts/export_mailing_list.py --output /tmp/my_mailing_list.csv
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import argparse

DB_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

CONFIDENCE_LEVELS = {
    'very_high': 1,
    'high': 2,
    'medium': 3,
    'low': 4,
    'very_low': 5
}

def export_mailing_list(
    min_confidence='high',
    recent_customers_days=None,
    output_file='/tmp/mailing_list_export.csv',
    include_metadata=True
):
    """
    Export mailing list with smart address selection.

    Args:
        min_confidence: Minimum confidence level (very_high, high, medium, low, very_low)
        recent_customers_days: Only include customers with transactions in last N days
        output_file: Path to output CSV file
        include_metadata: Include scoring metadata in export
    """

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Build query
    confidence_threshold = CONFIDENCE_LEVELS[min_confidence]

    query = """
        SELECT
            first_name,
            last_name,
            email,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country,
            address_source,
            confidence,
            billing_score,
            shipping_score,
            is_manual_override,
            last_transaction_date
        FROM mailing_list_export
        WHERE 1=1
    """

    params = []

    # Filter by confidence
    confidence_values = [k for k, v in CONFIDENCE_LEVELS.items() if v <= confidence_threshold]
    query += f" AND confidence = ANY(%s)"
    params.append(confidence_values)

    # Filter by recent customers
    if recent_customers_days:
        query += f" AND last_transaction_date > NOW() - INTERVAL '{recent_customers_days} days'"

    # Order by confidence and score
    query += """
        ORDER BY
            CASE confidence
                WHEN 'very_high' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                WHEN 'very_low' THEN 5
            END,
            GREATEST(billing_score, shipping_score) DESC
    """

    cursor.execute(query, params)
    contacts = cursor.fetchall()

    # Write to CSV
    if contacts:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            # Base fields
            fieldnames = [
                'first_name',
                'last_name',
                'email',
                'address_line_1',
                'address_line_2',
                'city',
                'state',
                'postal_code',
                'country'
            ]

            # Add metadata fields if requested
            if include_metadata:
                fieldnames.extend([
                    'address_source',
                    'confidence',
                    'score',
                    'billing_score',
                    'shipping_score',
                    'manual_override',
                    'last_transaction_date'
                ])

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for contact in contacts:
                row = {
                    'first_name': contact['first_name'] or '',
                    'last_name': contact['last_name'] or '',
                    'email': contact['email'] or '',
                    'address_line_1': contact['address_line_1'] or '',
                    'address_line_2': contact['address_line_2'] or '',
                    'city': contact['city'] or '',
                    'state': contact['state'] or '',
                    'postal_code': contact['postal_code'] or '',
                    'country': contact['country'] or 'US',
                }

                if include_metadata:
                    row.update({
                        'address_source': contact['address_source'],
                        'confidence': contact['confidence'],
                        'score': max(contact['billing_score'] or 0, contact['shipping_score'] or 0),
                        'billing_score': contact['billing_score'] or 0,
                        'shipping_score': contact['shipping_score'] or 0,
                        'manual_override': 'yes' if contact['is_manual_override'] else 'no',
                        'last_transaction_date': contact['last_transaction_date'].strftime('%Y-%m-%d') if contact['last_transaction_date'] else ''
                    })

                writer.writerow(row)

    # Print summary
    print("=" * 80)
    print("MAILING LIST EXPORT")
    print("=" * 80)
    print()
    print(f"Minimum Confidence: {min_confidence}")
    if recent_customers_days:
        print(f"Recent Customers: Last {recent_customers_days} days")
    print(f"Total Contacts: {len(contacts)}")
    print(f"Output File: {output_file}")
    print()

    # Confidence breakdown
    confidence_counts = {}
    for contact in contacts:
        conf = contact['confidence']
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    print("Confidence Breakdown:")
    for conf in ['very_high', 'high', 'medium', 'low', 'very_low']:
        if conf in confidence_counts:
            print(f"  {conf:12s}: {confidence_counts[conf]:4d} contacts")
    print()

    # Address source breakdown
    source_counts = {}
    for contact in contacts:
        src = contact['address_source']
        source_counts[src] = source_counts.get(src, 0) + 1

    print("Address Source:")
    for src in ['billing', 'shipping']:
        if src in source_counts:
            pct = source_counts[src] * 100.0 / len(contacts)
            print(f"  {src:12s}: {source_counts[src]:4d} contacts ({pct:.1f}%)")
    print()

    # Sample contacts
    print("Sample Contacts (first 5):")
    for i, contact in enumerate(contacts[:5], 1):
        print(f"\n{i}. {contact['first_name']} {contact['last_name']} <{contact['email']}>")
        print(f"   {contact['address_line_1']}")
        if contact['address_line_2']:
            print(f"   {contact['address_line_2']}")
        print(f"   {contact['city']}, {contact['state']} {contact['postal_code']}")
        print(f"   Source: {contact['address_source']}, Confidence: {contact['confidence']}, Score: {max(contact['billing_score'] or 0, contact['shipping_score'] or 0)}")

    print()
    print("=" * 80)
    print(f"✓ Export complete - {len(contacts)} contacts written to {output_file}")
    print("=" * 80)

    cursor.close()
    conn.close()

    return len(contacts)


def main():
    parser = argparse.ArgumentParser(
        description='Export mailing list with smart address selection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export only very high confidence contacts
  python3 scripts/export_mailing_list.py --min-confidence very_high

  # Export high and very_high confidence contacts
  python3 scripts/export_mailing_list.py --min-confidence high

  # Export recent active customers (last year) with high confidence
  python3 scripts/export_mailing_list.py --min-confidence high --recent-customers 365

  # Export without metadata (clean mailing list)
  python3 scripts/export_mailing_list.py --min-confidence high --no-metadata
        """
    )

    parser.add_argument(
        '--min-confidence',
        choices=['very_high', 'high', 'medium', 'low', 'very_low'],
        default='high',
        help='Minimum confidence level to include (default: high)'
    )

    parser.add_argument(
        '--recent-customers',
        type=int,
        metavar='DAYS',
        help='Only include customers with transactions in last N days'
    )

    parser.add_argument(
        '--output',
        default='/tmp/mailing_list_export.csv',
        help='Output CSV file path (default: /tmp/mailing_list_export.csv)'
    )

    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Exclude scoring metadata from export (cleaner for mail merge)'
    )

    args = parser.parse_args()

    export_mailing_list(
        min_confidence=args.min_confidence,
        recent_customers_days=args.recent_customers,
        output_file=args.output,
        include_metadata=not args.no_metadata
    )


if __name__ == '__main__':
    main()
