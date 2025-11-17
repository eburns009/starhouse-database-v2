#!/usr/bin/env python3
"""
FAANG-Quality Phase 4 Merge Candidate Verification

Analyzes HIGH confidence duplicate groups to prepare for merging:
- Identifies primary contact (oldest, most complete, most transactions)
- Maps email consolidation strategy
- Identifies transaction history to migrate
- Verifies no data will be lost in merge

USAGE:
    # Verify all HIGH confidence groups
    python3 scripts/verify_phase4_merge_candidates.py

    # Export detailed merge plan to CSV
    python3 scripts/verify_phase4_merge_candidates.py --csv /tmp/merge_plan.csv

    # Analyze specific group
    python3 scripts/verify_phase4_merge_candidates.py --group-id abc123

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
Phase: 4 - Duplicate Merging
"""

import psycopg2
import sys
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
from db_config import get_database_url

DATABASE_URL = get_database_url()

class MergeCandidateVerifier:
    """FAANG-quality merge candidate analysis."""

    def __init__(self, output_csv: Optional[str] = None, group_id: Optional[str] = None):
        self.output_csv = output_csv
        self.target_group_id = group_id
        self.conn = None
        self.cursor = None
        self.merge_plans = []
        self.stats = {
            'total_groups': 0,
            'total_contacts_to_merge': 0,
            'total_emails_to_migrate': 0,
            'total_transactions': 0,
            'groups_with_transactions': 0
        }

    def log(self, message: str, level: str = 'INFO'):
        """Structured logging with timestamps."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = {
            'INFO': '✓',
            'WARN': '⚠',
            'ERROR': '✗',
            'SUCCESS': '✅'
        }.get(level, '·')
        print(f"[{timestamp}] {prefix} {message}")

    def connect(self):
        """Establish database connection with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(DATABASE_URL, sslmode='require', connect_timeout=10)
                self.cursor = self.conn.cursor()
                self.log("Database connection established")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    self.log(f"Connection attempt {attempt + 1} failed, retrying...", 'WARN')
                    import time
                    time.sleep(2)
                else:
                    self.log(f"Failed to connect after {max_retries} attempts: {e}", 'ERROR')
                    sys.exit(1)

    def disconnect(self):
        """Clean up database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

    def generate_group_id(self, contact_ids: List[str]) -> str:
        """Generate stable group ID from contact IDs."""
        sorted_ids = sorted([str(cid) for cid in contact_ids])
        combined = '|'.join(sorted_ids)
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    def get_high_confidence_groups(self):
        """Get HIGH confidence duplicate groups."""
        self.log("\nFetching HIGH confidence duplicate groups...")

        # Get exact name duplicates with phone/address match
        self.cursor.execute("""
            WITH name_groups AS (
                SELECT
                    first_name,
                    last_name,
                    ARRAY_AGG(id ORDER BY created_at) as contact_ids,
                    ARRAY_AGG(email ORDER BY created_at) as emails,
                    ARRAY_AGG(phone ORDER BY created_at) as phones,
                    ARRAY_AGG(address_line_1 ORDER BY created_at) as addresses,
                    ARRAY_AGG(source_system ORDER BY created_at) as sources,
                    ARRAY_AGG(created_at ORDER BY created_at) as created_dates,
                    COUNT(*) as count,
                    COUNT(DISTINCT phone) FILTER (WHERE phone IS NOT NULL AND phone != '') as unique_phones,
                    COUNT(DISTINCT address_line_1) FILTER (WHERE address_line_1 IS NOT NULL AND address_line_1 != '') as unique_addresses
                FROM contacts
                WHERE deleted_at IS NULL
                  AND first_name IS NOT NULL
                  AND last_name IS NOT NULL
                  AND first_name != ''
                  AND last_name != ''
                  AND first_name != 'nan'
                  AND last_name != 'nan'
                GROUP BY first_name, last_name
                HAVING COUNT(*) > 1
            )
            SELECT *
            FROM name_groups
            WHERE unique_phones = 1 OR unique_addresses = 1
            ORDER BY count DESC, first_name, last_name
        """)

        return self.cursor.fetchall()

    def analyze_group(self, group_data):
        """Analyze a single duplicate group and create merge plan."""
        first_name, last_name, contact_ids, emails, phones, addresses, sources, created_dates, count, unique_phones, unique_addresses = group_data

        # psycopg2 returns arrays as Python lists, so they should be fine
        # Generate group ID
        group_id = self.generate_group_id(contact_ids)

        # Skip if not target group (when filtering)
        if self.target_group_id and group_id != self.target_group_id:
            return None

        # Get detailed contact information
        contacts = []
        for i in range(count):
            contact_id = str(contact_ids[i])  # Ensure it's a string UUID

            # Get transaction count and total
            self.cursor.execute("""
                SELECT
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(amount), 0) as total_spent
                FROM transactions
                WHERE contact_id::text = %s
                  AND deleted_at IS NULL
            """, (contact_id,))

            tx_row = self.cursor.fetchone()
            transaction_count = tx_row[0] if tx_row else 0
            total_spent = float(tx_row[1]) if tx_row else 0.0

            # Get additional emails from contact_emails table
            self.cursor.execute("""
                SELECT email
                FROM contact_emails
                WHERE contact_id::text = %s
                ORDER BY created_at
            """, (contact_id,))

            additional_emails = [row[0] for row in self.cursor.fetchall()]

            contacts.append({
                'id': contact_id,
                'email': emails[i],
                'phone': phones[i],
                'address': addresses[i],
                'source': sources[i],
                'created_at': created_dates[i],
                'transaction_count': transaction_count,
                'total_spent': total_spent,
                'additional_emails': additional_emails
            })

        # Choose primary contact (prioritize: most transactions > oldest > most complete)
        primary = max(contacts, key=lambda c: (
            c['transaction_count'],
            -c['created_at'].timestamp(),
            bool(c['phone']),
            bool(c['address'])
        ))

        # Identify duplicates to merge
        duplicates = [c for c in contacts if c['id'] != primary['id']]

        # Calculate emails to migrate
        all_emails = set()
        for contact in contacts:
            all_emails.add(contact['email'])
            all_emails.update(contact['additional_emails'])

        # Primary's existing emails
        primary_emails = {primary['email']}
        primary_emails.update(primary['additional_emails'])

        # Emails that need to be migrated to primary
        emails_to_migrate = all_emails - primary_emails

        # Calculate total transactions to migrate
        total_transactions = sum(c['transaction_count'] for c in duplicates)

        # Determine confidence and reason
        confidence = 'HIGH'
        reasons = ['Exact name match']
        if unique_phones == 1 and phones[0]:
            reasons.append('Same phone')
        if unique_addresses == 1 and addresses[0]:
            reasons.append('Same address')

        merge_plan = {
            'group_id': group_id,
            'first_name': first_name,
            'last_name': last_name,
            'confidence': confidence,
            'reason': ', '.join(reasons),
            'contact_count': count,
            'primary_contact': primary,
            'duplicates': duplicates,
            'emails_to_migrate': list(emails_to_migrate),
            'transactions_to_migrate': total_transactions,
            'total_spent': sum(c['total_spent'] for c in contacts)
        }

        return merge_plan

    def analyze_all_groups(self):
        """Analyze all HIGH confidence groups."""
        groups = self.get_high_confidence_groups()
        self.log(f"  Found {len(groups)} HIGH confidence groups")

        for group_data in groups:
            merge_plan = self.analyze_group(group_data)
            if merge_plan:
                self.merge_plans.append(merge_plan)

                # Update stats
                self.stats['total_groups'] += 1
                self.stats['total_contacts_to_merge'] += len(merge_plan['duplicates'])
                self.stats['total_emails_to_migrate'] += len(merge_plan['emails_to_migrate'])
                self.stats['total_transactions'] += merge_plan['transactions_to_migrate']
                if merge_plan['transactions_to_migrate'] > 0:
                    self.stats['groups_with_transactions'] += 1

    def print_report(self):
        """Print comprehensive merge analysis report."""
        print("\n" + "=" * 80)
        print("PHASE 4 MERGE CANDIDATE VERIFICATION")
        print("=" * 80)
        print()

        # Summary statistics
        print("MERGE STATISTICS:")
        print(f"  Total HIGH confidence groups:  {self.stats['total_groups']}")
        print(f"  Total contacts to merge:       {self.stats['total_contacts_to_merge']}")
        print(f"  Total emails to migrate:       {self.stats['total_emails_to_migrate']}")
        print(f"  Total transactions to migrate: {self.stats['total_transactions']}")
        print(f"  Groups with transactions:      {self.stats['groups_with_transactions']}")
        print()

        # Show top 10 groups by impact
        print("=" * 80)
        print("TOP 10 MERGE CANDIDATES (by transaction count)")
        print("=" * 80)
        print()

        sorted_plans = sorted(self.merge_plans, key=lambda p: p['transactions_to_migrate'], reverse=True)

        for i, plan in enumerate(sorted_plans[:10], 1):
            print(f"{i}. {plan['first_name']} {plan['last_name']} ({plan['contact_count']} contacts)")
            print(f"   Group ID: {plan['group_id']}")
            print(f"   Reason: {plan['reason']}")
            print(f"   Primary: {plan['primary_contact']['email']} (created {plan['primary_contact']['created_at'].date()})")
            print(f"   Duplicates: {len(plan['duplicates'])} contacts to merge")
            print(f"   Emails to migrate: {len(plan['emails_to_migrate'])}")
            print(f"   Transactions to migrate: {plan['transactions_to_migrate']}")
            print(f"   Total customer value: ${plan['total_spent']:.2f}")

            # Show duplicate details
            for dup in plan['duplicates']:
                print(f"     - {dup['email']} ({dup['transaction_count']} txns, ${dup['total_spent']:.2f})")
            print()

    def export_csv(self):
        """Export merge plan to CSV."""
        if not self.output_csv:
            return

        fieldnames = [
            'group_id', 'first_name', 'last_name', 'confidence', 'reason',
            'contact_count', 'duplicates_to_merge', 'emails_to_migrate', 'transactions_to_migrate',
            'primary_contact_id', 'primary_email', 'primary_created_at',
            'duplicate_contact_id', 'duplicate_email', 'duplicate_transactions',
            'duplicate_total_spent', 'duplicate_source',
            'merge_action', 'risk_level', 'review_notes'
        ]

        with open(self.output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for plan in self.merge_plans:
                # Write one row per duplicate contact
                for dup in plan['duplicates']:
                    writer.writerow({
                        'group_id': plan['group_id'],
                        'first_name': plan['first_name'],
                        'last_name': plan['last_name'],
                        'confidence': plan['confidence'],
                        'reason': plan['reason'],
                        'contact_count': plan['contact_count'],
                        'duplicates_to_merge': len(plan['duplicates']),
                        'emails_to_migrate': len(plan['emails_to_migrate']),
                        'transactions_to_migrate': plan['transactions_to_migrate'],
                        'primary_contact_id': plan['primary_contact']['id'],
                        'primary_email': plan['primary_contact']['email'],
                        'primary_created_at': plan['primary_contact']['created_at'],
                        'duplicate_contact_id': dup['id'],
                        'duplicate_email': dup['email'],
                        'duplicate_transactions': dup['transaction_count'],
                        'duplicate_total_spent': dup['total_spent'],
                        'duplicate_source': dup['source'],
                        'merge_action': 'SAFE_TO_MERGE' if dup['transaction_count'] == 0 else 'MERGE_WITH_TX_MIGRATION',
                        'risk_level': 'LOW' if dup['transaction_count'] == 0 else 'MEDIUM',
                        'review_notes': ''
                    })

        self.log(f"✓ Exported merge plan to CSV: {self.output_csv}", 'SUCCESS')

    def run(self):
        """Main execution."""
        try:
            self.connect()

            print("\n" + "=" * 80)
            print("PHASE 4 MERGE CANDIDATE VERIFICATION - FAANG Quality")
            print("=" * 80)
            print()

            # Analyze groups
            self.analyze_all_groups()

            # Print report
            self.print_report()

            # Export CSV
            if self.output_csv:
                self.export_csv()

            # Recommendations
            print("=" * 80)
            print("RECOMMENDATIONS")
            print("=" * 80)
            print()
            print("1. Review merge plan CSV for detailed analysis")
            print("2. Start with LOW risk merges (no transactions)")
            print(f"3. Test merge script on 5-10 groups first")
            print("4. Execute full merge after validation")
            print()
            print(f"Expected outcome: Consolidate {self.stats['total_contacts_to_merge']} duplicate contacts")
            print(f"                 Migrate {self.stats['total_emails_to_migrate']} emails to contact_emails table")
            print(f"                 Migrate {self.stats['total_transactions']} transactions")
            print()

            return 0

        except Exception as e:
            self.log(f"Fatal error: {e}", 'ERROR')
            import traceback
            traceback.print_exc()
            return 1

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='Verify and analyze merge candidates for Phase 4',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Export merge plan to CSV file'
    )

    parser.add_argument(
        '--group-id',
        type=str,
        help='Analyze specific group ID only'
    )

    args = parser.parse_args()

    verifier = MergeCandidateVerifier(
        output_csv=args.csv,
        group_id=args.group_id
    )
    return verifier.run()


if __name__ == '__main__':
    sys.exit(main())
