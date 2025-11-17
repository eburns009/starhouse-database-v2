#!/usr/bin/env python3
"""
FAANG-Quality Manual Review Investigation Tool

Generates detailed research report for 45 contacts with 'nan' names.
Provides all available data to aid manual name recovery.

FEATURES:
- Extracts all available contact data
- Analyzes email patterns and domains
- Checks for transaction history
- Identifies potential business accounts
- Exports to CSV for manual research
- Generates prioritized review list

USAGE:
    # Generate investigation report
    python3 scripts/investigate_nan_names.py

    # Export to CSV
    python3 scripts/investigate_nan_names.py --csv /tmp/nan_names_review.csv

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
"""

import psycopg2
import sys
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import argparse
import csv
import re
from db_config import get_database_url

DATABASE_URL = get_database_url()

class NanNameInvestigator:
    """Systematic investigation tool for contacts with 'nan' names."""

    def __init__(self, output_csv: Optional[str] = None):
        self.output_csv = output_csv
        self.conn = None
        self.cursor = None
        self.contacts = []

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.cursor = self.conn.cursor()
            print("✓ Database connection established")
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            sys.exit(1)

    def disconnect(self):
        """Clean up connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def extract_potential_name_from_email(self, email: str) -> Dict:
        """
        Analyze email for name extraction possibilities.

        Returns dict with:
        - potential_first: extracted first name (if any)
        - potential_last: extracted last name (if any)
        - confidence: low/none
        - pattern: description of email pattern
        """
        if not email or '@' not in email:
            return {'potential_first': None, 'potential_last': None,
                   'confidence': 'none', 'pattern': 'invalid'}

        local_part = email.split('@')[0]
        domain = email.split('@')[1]

        # Check for common business patterns
        business_prefixes = ['info', 'team', 'sales', 'payment', 'admin',
                            'contact', 'support', 'office', 'hello']

        if local_part.lower() in business_prefixes:
            return {'potential_first': None, 'potential_last': None,
                   'confidence': 'none',
                   'pattern': f'business_account ({local_part})'}

        # Try firstname.lastname pattern
        for separator in ['.', '_', '-']:
            if separator in local_part:
                parts = local_part.split(separator)
                if len(parts) >= 2:
                    first = parts[0].capitalize()
                    last = parts[-1].capitalize()
                    # Only consider if both are alphabetic
                    if first.isalpha() and last.isalpha() and len(first) > 1 and len(last) > 1:
                        return {
                            'potential_first': first,
                            'potential_last': last,
                            'confidence': 'low',
                            'pattern': f'firstname{separator}lastname'
                        }

        # Check if local part is all alphabetic (single word name?)
        if local_part.isalpha() and len(local_part) > 2:
            return {
                'potential_first': local_part.capitalize(),
                'potential_last': None,
                'confidence': 'very_low',
                'pattern': 'single_word'
            }

        # Check for numbers (usernames, unlikely to be names)
        if any(char.isdigit() for char in local_part):
            return {
                'potential_first': None,
                'potential_last': None,
                'confidence': 'none',
                'pattern': 'username_with_numbers'
            }

        return {
            'potential_first': None,
            'potential_last': None,
            'confidence': 'none',
            'pattern': 'unknown'
        }

    def analyze_domain(self, email: str) -> Dict:
        """
        Analyze email domain for business/organization clues.
        """
        if not email or '@' not in email:
            return {'domain': None, 'type': 'unknown', 'organization_hint': None}

        domain = email.split('@')[1]

        # Common personal email providers
        personal_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com',
            'outlook.com', 'icloud.com', 'me.com', 'mac.com',
            'comcast.net', 'verizon.net', 'sbcglobal.net'
        ]

        if domain in personal_domains:
            return {
                'domain': domain,
                'type': 'personal',
                'organization_hint': None
            }

        # Extract potential organization name from domain
        org_name = domain.split('.')[0]

        return {
            'domain': domain,
            'type': 'business/organization',
            'organization_hint': org_name.replace('-', ' ').title()
        }

    def get_transaction_info(self, contact_id: str) -> Dict:
        """Get transaction summary for contact."""
        self.cursor.execute("""
            SELECT
                COUNT(*) as transaction_count,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction,
                SUM(amount) as total_amount
            FROM transactions
            WHERE contact_id = %s
              AND deleted_at IS NULL
        """, (contact_id,))

        row = self.cursor.fetchone()
        if row and row[0] > 0:
            return {
                'has_transactions': True,
                'transaction_count': row[0],
                'first_transaction': row[1].strftime('%Y-%m-%d') if row[1] else None,
                'last_transaction': row[2].strftime('%Y-%m-%d') if row[2] else None,
                'total_amount': float(row[3]) if row[3] else 0
            }

        return {
            'has_transactions': False,
            'transaction_count': 0,
            'first_transaction': None,
            'last_transaction': None,
            'total_amount': 0
        }

    def investigate_contacts(self):
        """Gather comprehensive data for all nan contacts."""
        print("\n" + "=" * 80)
        print("INVESTIGATING CONTACTS WITH 'NAN' NAMES")
        print("=" * 80)
        print()

        self.cursor.execute("""
            SELECT
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                c.phone,
                c.source_system,
                c.paypal_first_name,
                c.paypal_last_name,
                c.paypal_business_name,
                c.additional_name,
                c.created_at,
                c.address_line_1,
                c.city,
                c.state,
                c.postal_code
            FROM contacts c
            WHERE c.deleted_at IS NULL
              AND (c.first_name = 'nan' OR c.last_name = 'nan')
            ORDER BY c.email
        """)

        raw_contacts = self.cursor.fetchall()
        print(f"Found {len(raw_contacts)} contacts to investigate\n")

        for row in raw_contacts:
            contact_id = row[0]
            email = row[3]

            # Email analysis
            email_analysis = self.extract_potential_name_from_email(email)
            domain_analysis = self.analyze_domain(email)

            # Transaction info
            transaction_info = self.get_transaction_info(contact_id)

            # Compile all data
            contact_data = {
                'id': contact_id,
                'email': email,
                'phone': row[4],
                'source_system': row[5],
                'paypal_first_name': row[6],
                'paypal_last_name': row[7],
                'paypal_business_name': row[8],
                'additional_name': row[9],
                'created_at': row[10].strftime('%Y-%m-%d') if row[10] else None,
                'address_line_1': row[11],
                'city': row[12],
                'state': row[13],
                'postal_code': row[14],
                # Analysis results
                'email_pattern': email_analysis['pattern'],
                'potential_first': email_analysis['potential_first'],
                'potential_last': email_analysis['potential_last'],
                'name_confidence': email_analysis['confidence'],
                'domain_type': domain_analysis['type'],
                'organization_hint': domain_analysis['organization_hint'],
                'has_transactions': transaction_info['has_transactions'],
                'transaction_count': transaction_info['transaction_count'],
                'first_transaction': transaction_info['first_transaction'],
                'last_transaction': transaction_info['last_transaction'],
                'total_spent': transaction_info['total_amount']
            }

            self.contacts.append(contact_data)

    def prioritize_contacts(self):
        """Assign priority scores for manual review."""
        for contact in self.contacts:
            priority_score = 0
            priority_reasons = []

            # Higher priority if has transactions
            if contact['has_transactions']:
                priority_score += 10
                priority_reasons.append(f"customer ({contact['transaction_count']} transactions)")

            # Higher priority if spent money
            if contact['total_spent'] > 0:
                if contact['total_spent'] > 1000:
                    priority_score += 20
                    priority_reasons.append(f"high-value (${contact['total_spent']:.2f})")
                elif contact['total_spent'] > 100:
                    priority_score += 10
                    priority_reasons.append(f"paid customer (${contact['total_spent']:.2f})")

            # Higher priority if name extractable from email
            if contact['name_confidence'] in ['low', 'very_low']:
                priority_score += 5
                priority_reasons.append("name extractable from email")

            # Higher priority if business/org (might have lookup info)
            if contact['domain_type'] == 'business/organization':
                priority_score += 5
                priority_reasons.append(f"business domain ({contact['organization_hint']})")

            # Lower priority if business account email pattern
            if contact['email_pattern'].startswith('business_account'):
                priority_score -= 5
                priority_reasons.append("likely org account (not individual)")

            # Assign priority tier
            if priority_score >= 20:
                priority_tier = "HIGH"
            elif priority_score >= 10:
                priority_tier = "MEDIUM"
            elif priority_score >= 5:
                priority_tier = "LOW"
            else:
                priority_tier = "OPTIONAL"

            contact['priority_score'] = priority_score
            contact['priority_tier'] = priority_tier
            contact['priority_reasons'] = ', '.join(priority_reasons) if priority_reasons else 'no special factors'

        # Sort by priority score descending
        self.contacts.sort(key=lambda x: x['priority_score'], reverse=True)

    def print_report(self):
        """Print comprehensive investigation report."""
        print("\n" + "=" * 80)
        print("MANUAL REVIEW INVESTIGATION REPORT")
        print("=" * 80)
        print()

        # Summary by priority
        by_priority = {}
        for c in self.contacts:
            tier = c['priority_tier']
            by_priority[tier] = by_priority.get(tier, 0) + 1

        print("PRIORITY BREAKDOWN:")
        for tier in ['HIGH', 'MEDIUM', 'LOW', 'OPTIONAL']:
            count = by_priority.get(tier, 0)
            print(f"  {tier}: {count} contacts")
        print()

        # Detailed contact list
        print("=" * 80)
        print("DETAILED CONTACT REVIEW LIST")
        print("=" * 80)
        print()

        for i, contact in enumerate(self.contacts, 1):
            print(f"{i}. [{contact['priority_tier']}] {contact['email']}")
            print(f"   ID: {contact['id'][:8]}...")
            print(f"   Priority: {contact['priority_score']} ({contact['priority_reasons']})")

            if contact['potential_first'] or contact['potential_last']:
                print(f"   💡 Suggested Name: {contact['potential_first'] or '?'} {contact['potential_last'] or '?'} (confidence: {contact['name_confidence']})")

            if contact['organization_hint']:
                print(f"   🏢 Organization Hint: {contact['organization_hint']}")

            if contact['has_transactions']:
                print(f"   💰 Transactions: {contact['transaction_count']} (${contact['total_spent']:.2f} total)")
                print(f"      First: {contact['first_transaction']}, Last: {contact['last_transaction']}")

            if contact['phone']:
                print(f"   📞 Phone: {contact['phone']}")

            if contact['address_line_1']:
                address = f"{contact['address_line_1']}"
                if contact['city']:
                    address += f", {contact['city']}"
                if contact['state']:
                    address += f", {contact['state']}"
                if contact['postal_code']:
                    address += f" {contact['postal_code']}"
                print(f"   📍 Address: {address}")

            print(f"   📊 Source: {contact['source_system']}")
            print(f"   📅 Created: {contact['created_at']}")
            print()

    def export_csv(self):
        """Export to CSV for manual review."""
        if not self.output_csv:
            return

        fieldnames = [
            'priority_tier', 'priority_score', 'email', 'id',
            'suggested_first_name', 'suggested_last_name', 'name_confidence',
            'phone', 'organization_hint', 'domain_type',
            'has_transactions', 'transaction_count', 'total_spent',
            'first_transaction', 'last_transaction',
            'address_line_1', 'city', 'state', 'postal_code',
            'source_system', 'created_at', 'priority_reasons',
            'research_notes'  # Empty field for manual notes
        ]

        with open(self.output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for contact in self.contacts:
                writer.writerow({
                    'priority_tier': contact['priority_tier'],
                    'priority_score': contact['priority_score'],
                    'email': contact['email'],
                    'id': contact['id'],
                    'suggested_first_name': contact['potential_first'] or '',
                    'suggested_last_name': contact['potential_last'] or '',
                    'name_confidence': contact['name_confidence'],
                    'phone': contact['phone'] or '',
                    'organization_hint': contact['organization_hint'] or '',
                    'domain_type': contact['domain_type'],
                    'has_transactions': contact['has_transactions'],
                    'transaction_count': contact['transaction_count'],
                    'total_spent': contact['total_spent'],
                    'first_transaction': contact['first_transaction'] or '',
                    'last_transaction': contact['last_transaction'] or '',
                    'address_line_1': contact['address_line_1'] or '',
                    'city': contact['city'] or '',
                    'state': contact['state'] or '',
                    'postal_code': contact['postal_code'] or '',
                    'source_system': contact['source_system'],
                    'created_at': contact['created_at'] or '',
                    'priority_reasons': contact['priority_reasons'],
                    'research_notes': ''  # For manual entry
                })

        print(f"✓ Exported to CSV: {self.output_csv}")
        print(f"  Open in spreadsheet software to add research notes")
        print()

    def run(self):
        """Main execution."""
        try:
            self.connect()
            self.investigate_contacts()
            self.prioritize_contacts()
            self.print_report()

            if self.output_csv:
                self.export_csv()

            # Summary
            print("=" * 80)
            print("NEXT STEPS")
            print("=" * 80)
            print()
            print("1. Review HIGH priority contacts first (customers with transactions)")
            print("2. For business domains, search company website for contact info")
            print("3. For personal emails, use suggested names if confidence is acceptable")
            print("4. For organization accounts (team@, info@), consider:")
            print("   - Mark as business account (set first_name='Organization', last_name=org name)")
            print("   - Or leave as-is if truly unidentifiable")
            print()
            print("5. Update database using:")
            print("   UPDATE contacts SET first_name='...', last_name='...' WHERE id='...'")
            print()

            return 0

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='Investigate contacts with nan names for manual review',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Export results to CSV file for manual review'
    )

    args = parser.parse_args()

    investigator = NanNameInvestigator(output_csv=args.csv)
    return investigator.run()


if __name__ == '__main__':
    sys.exit(main())
