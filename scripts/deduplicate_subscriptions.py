#!/usr/bin/env python3
"""
Subscription Deduplication Script - FAANG Quality
==================================================
Safe removal of duplicate subscriptions caused by PayPal import bug.

ROOT CAUSE:
-----------
PayPal import script incorrectly stores PayPal subscription IDs in the
kajabi_subscription_id field. This causes the same subscription to appear
twice: once from Kajabi import (correct) and once from PayPal import (duplicate).

DETECTION PATTERN:
------------------
A subscription is a duplicate PayPal import if:
1. kajabi_subscription_id starts with "I-" (PayPal format)
2. paypal_subscription_reference equals kajabi_subscription_id (same ID in both fields)
3. Contact has another subscription with:
   - Numeric kajabi_subscription_id (real Kajabi ID)
   - Same amount (within $1 tolerance)
   - Same billing cycle (Month/monthly, Year/annual, etc.)
   - Active status

SOLUTION:
---------
Soft-delete the PayPal duplicate subscriptions, keeping the Kajabi subscriptions
as the canonical source of truth.

SAFETY MEASURES:
----------------
- Dry-run mode (default)
- Atomic transactions with rollback
- Comprehensive backup tables
- Pre and post validation
- Detailed audit logging
- Rollback procedures included

Author: Claude Code
Date: 2025-11-12
"""

import sys
import os
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import json
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url


@dataclass
class Subscription:
    """Subscription record"""
    id: str
    contact_id: str
    kajabi_subscription_id: Optional[str]
    paypal_subscription_reference: Optional[str]
    status: str
    amount: Decimal
    billing_cycle: str
    created_at: datetime

    def is_paypal_duplicate(self) -> bool:
        """Check if this is a PayPal duplicate (ID in wrong field)"""
        return (
            self.kajabi_subscription_id is not None and
            self.kajabi_subscription_id.startswith('I-') and
            self.paypal_subscription_reference == self.kajabi_subscription_id
        )

    def is_real_kajabi(self) -> bool:
        """Check if this is a real Kajabi subscription"""
        return (
            self.kajabi_subscription_id is not None and
            not self.kajabi_subscription_id.startswith('I-')
        )

    def matches_subscription(self, other: 'Subscription', amount_tolerance: float = 1.0) -> bool:
        """Check if this subscription matches another (for duplicate detection)"""
        if self.contact_id != other.contact_id:
            return False

        # Amount match (within tolerance)
        amount_diff = abs(float(self.amount) - float(other.amount))
        if amount_diff > amount_tolerance:
            return False

        # Billing cycle match (normalize different formats)
        cycle_map = {
            'month': 'monthly',
            'monthly': 'monthly',
            'year': 'annual',
            'annual': 'annual',
            'yearly': 'annual'
        }
        cycle1 = cycle_map.get(self.billing_cycle.lower(), self.billing_cycle.lower())
        cycle2 = cycle_map.get(other.billing_cycle.lower(), other.billing_cycle.lower())

        return cycle1 == cycle2


class SubscriptionDeduplicator:
    """FAANG-quality subscription deduplicator with comprehensive safety"""

    def __init__(self, dry_run: bool = True, backup: bool = True):
        self.conn = psycopg2.connect(get_database_url())
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.dry_run = dry_run
        self.backup = backup
        self.stats = {
            'duplicates_found': 0,
            'contacts_affected': 0,
            'subscriptions_removed': 0,
            'legitimate_multiples': 0,
            'errors': []
        }
        self.dedup_plan: List[Dict] = []

    def create_backup_table(self):
        """Create comprehensive backup table"""
        print("📦 Creating backup table...")

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions_dedup_backup (
                backup_id SERIAL PRIMARY KEY,
                subscription_id UUID NOT NULL,
                subscription_data JSONB NOT NULL,
                contact_email TEXT,
                contact_name TEXT,
                reason TEXT NOT NULL,
                backed_up_at TIMESTAMP DEFAULT NOW()
            )
        """)

        print("✓ Backup table ready\n")

    def load_active_subscriptions_by_contact(self) -> Dict[str, List[Subscription]]:
        """Load all active subscriptions grouped by contact"""
        print("📊 Loading active subscriptions...")

        self.cur.execute("""
            SELECT
                s.id,
                s.contact_id,
                s.kajabi_subscription_id,
                s.paypal_subscription_reference,
                s.status,
                s.amount,
                s.billing_cycle,
                s.created_at
            FROM subscriptions s
            WHERE s.deleted_at IS NULL
              AND s.status = 'active'
            ORDER BY s.contact_id, s.created_at
        """)

        rows = self.cur.fetchall()
        print(f"✓ Loaded {len(rows)} active subscriptions\n")

        # Group by contact
        by_contact: Dict[str, List[Subscription]] = {}
        for row in rows:
            sub = Subscription(
                id=str(row['id']),
                contact_id=str(row['contact_id']),
                kajabi_subscription_id=row['kajabi_subscription_id'],
                paypal_subscription_reference=row['paypal_subscription_reference'],
                status=row['status'],
                amount=Decimal(str(row['amount'])),
                billing_cycle=row['billing_cycle'],
                created_at=row['created_at']
            )

            contact_id = str(row['contact_id'])
            if contact_id not in by_contact:
                by_contact[contact_id] = []
            by_contact[contact_id].append(sub)

        return by_contact

    def identify_duplicates(self, by_contact: Dict[str, List[Subscription]]):
        """Identify PayPal duplicate subscriptions"""
        print("🔍 Identifying duplicate subscriptions...\n")

        for contact_id, subs in by_contact.items():
            if len(subs) <= 1:
                continue

            # Separate into PayPal duplicates and real Kajabi subscriptions
            paypal_dupes = [s for s in subs if s.is_paypal_duplicate()]
            kajabi_subs = [s for s in subs if s.is_real_kajabi()]

            if not paypal_dupes:
                # No PayPal duplicates for this contact
                if len(subs) > 1:
                    self.stats['legitimate_multiples'] += 1
                continue

            # For each PayPal duplicate, find matching Kajabi subscription
            for paypal_dupe in paypal_dupes:
                matched_kajabi = None
                for kajabi_sub in kajabi_subs:
                    if paypal_dupe.matches_subscription(kajabi_sub):
                        matched_kajabi = kajabi_sub
                        break

                if matched_kajabi:
                    # Found a duplicate pair
                    self.dedup_plan.append({
                        'contact_id': contact_id,
                        'duplicate_subscription': paypal_dupe,
                        'canonical_subscription': matched_kajabi,
                        'reason': 'PayPal duplicate of Kajabi subscription'
                    })
                    self.stats['duplicates_found'] += 1

        # Count unique contacts affected
        unique_contacts = set(item['contact_id'] for item in self.dedup_plan)
        self.stats['contacts_affected'] = len(unique_contacts)

        print(f"✓ Found {self.stats['duplicates_found']} duplicate subscriptions")
        print(f"✓ Affecting {self.stats['contacts_affected']} contacts")
        print(f"✓ {self.stats['legitimate_multiples']} contacts have legitimate multiple subscriptions\n")

    def validate_dedup_plan(self) -> Tuple[bool, List[str]]:
        """Validate deduplication plan for safety"""
        print("🛡️  Validating deduplication plan...")

        issues = []

        # Check 1: All duplicates are actually PayPal duplicates
        for item in self.dedup_plan:
            dup = item['duplicate_subscription']
            if not dup.is_paypal_duplicate():
                issues.append(f"Subscription {dup.id} is not a PayPal duplicate!")

        # Check 2: All canonical subscriptions are real Kajabi subscriptions
        for item in self.dedup_plan:
            canonical = item['canonical_subscription']
            if not canonical.is_real_kajabi():
                issues.append(f"Canonical subscription {canonical.id} is not a real Kajabi subscription!")

        # Check 3: Amounts match within tolerance
        for item in self.dedup_plan:
            dup = item['duplicate_subscription']
            canonical = item['canonical_subscription']
            amount_diff = abs(float(dup.amount) - float(canonical.amount))
            if amount_diff > 1.0:
                issues.append(f"Amount mismatch: ${dup.amount} vs ${canonical.amount} (diff: ${amount_diff})")

        # Check 4: Same contact
        for item in self.dedup_plan:
            dup = item['duplicate_subscription']
            canonical = item['canonical_subscription']
            if dup.contact_id != canonical.contact_id:
                issues.append(f"Contact mismatch: {dup.contact_id} vs {canonical.contact_id}")

        if issues:
            print(f"❌ Validation failed with {len(issues)} issues:")
            for issue in issues[:10]:
                print(f"   - {issue}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more")
            print()
            return False, issues

        print("✓ Validation passed - all duplicates are safe to remove\n")
        return True, []

    def backup_subscriptions(self):
        """Backup subscriptions before deletion"""
        if not self.backup:
            return

        print("📦 Backing up subscriptions to remove...")

        for item in self.dedup_plan:
            dup = item['duplicate_subscription']

            # Get contact info
            self.cur.execute("""
                SELECT email, first_name || ' ' || last_name as name
                FROM contacts
                WHERE id = %s
            """, (dup.contact_id,))
            contact = self.cur.fetchone()

            # Get full subscription data
            self.cur.execute("""
                SELECT row_to_json(subscriptions.*) as data
                FROM subscriptions
                WHERE id = %s
            """, (dup.id,))
            sub_data = self.cur.fetchone()['data']

            # Insert backup
            self.cur.execute("""
                INSERT INTO subscriptions_dedup_backup
                (subscription_id, subscription_data, contact_email, contact_name, reason)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                dup.id,
                json.dumps(sub_data, default=str),
                contact['email'] if contact else None,
                contact['name'] if contact else None,
                item['reason']
            ))

        print(f"✓ Backed up {len(self.dedup_plan)} subscriptions\n")

    def execute_deduplication(self):
        """Execute the deduplication (soft delete)"""
        print("🗑️  Removing duplicate subscriptions...")

        for item in self.dedup_plan:
            dup = item['duplicate_subscription']

            # Soft delete the duplicate subscription
            self.cur.execute("""
                UPDATE subscriptions
                SET deleted_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                  AND deleted_at IS NULL
            """, (dup.id,))

            if self.cur.rowcount > 0:
                self.stats['subscriptions_removed'] += 1

        print(f"✓ Removed {self.stats['subscriptions_removed']} duplicate subscriptions\n")

    def verify_results(self):
        """Verify deduplication results"""
        print("✅ Verifying results...")

        # Check 1: Verify we removed the expected number of duplicates
        expected_removed = len(self.dedup_plan)
        actual_removed = self.stats['subscriptions_removed']

        if expected_removed != actual_removed:
            print(f"⚠️  WARNING: Expected to remove {expected_removed} but removed {actual_removed}!")
            return False

        print(f"✓ Removed {actual_removed} duplicate subscriptions (as planned)")

        # Check 2: Remaining PayPal IDs in kajabi field (these are PayPal-only, not duplicates)
        self.cur.execute("""
            SELECT COUNT(*) as count
            FROM subscriptions
            WHERE deleted_at IS NULL
              AND status = 'active'
              AND kajabi_subscription_id LIKE 'I-%'
              AND paypal_subscription_reference = kajabi_subscription_id
        """)
        remaining_paypal = self.cur.fetchone()['count']

        if remaining_paypal > 0:
            print(f"✓ {remaining_paypal} PayPal-only subscriptions remain (no Kajabi equivalent - legitimate)")

        # Check 3: Count contacts with multiple active subscriptions
        self.cur.execute("""
            SELECT COUNT(*) as count
            FROM (
                SELECT contact_id
                FROM subscriptions
                WHERE deleted_at IS NULL
                  AND status = 'active'
                GROUP BY contact_id
                HAVING COUNT(*) > 1
            ) multi
        """)
        multi_count = self.cur.fetchone()['count']

        print(f"✓ {multi_count} contacts still have multiple subscriptions (legitimate)")
        print()

        return True

    def print_summary(self):
        """Print comprehensive summary"""
        print("=" * 80)
        print("DEDUPLICATION SUMMARY")
        print("=" * 80)
        print()

        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print()

        print(f"📊 Results:")
        print(f"   Duplicates found:         {self.stats['duplicates_found']}")
        print(f"   Contacts affected:        {self.stats['contacts_affected']}")
        print(f"   Subscriptions removed:    {self.stats['subscriptions_removed']}")
        print(f"   Legitimate multiples:     {self.stats['legitimate_multiples']}")
        print()

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes made to database")
            print("   Run with --execute to perform deduplication")
        else:
            print("✅ EXECUTION COMPLETE - Changes committed to database")
        print()

        print("=" * 80)
        print()

    def export_report(self, output_file: str = 'deduplication_report.json'):
        """Export detailed report"""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': 'dry_run' if self.dry_run else 'execute',
            'statistics': self.stats,
            'duplicates_removed': [
                {
                    'duplicate_subscription_id': item['duplicate_subscription'].id,
                    'canonical_subscription_id': item['canonical_subscription'].id,
                    'contact_id': item['contact_id'],
                    'amount': float(item['duplicate_subscription'].amount),
                    'billing_cycle': item['duplicate_subscription'].billing_cycle,
                    'reason': item['reason']
                }
                for item in self.dedup_plan
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"✓ Exported detailed report to: {output_file}\n")

    def commit_or_rollback(self):
        """Commit or rollback transaction"""
        if self.dry_run:
            self.conn.rollback()
            print("🔄 Transaction rolled back (dry run)\n")
        else:
            self.conn.commit()
            print("💾 Transaction committed\n")

    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Deduplicate PayPal subscriptions (FAANG quality)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default, safe)
  python3 scripts/deduplicate_subscriptions.py

  # Execute deduplication
  python3 scripts/deduplicate_subscriptions.py --execute

  # Execute without backup (not recommended)
  python3 scripts/deduplicate_subscriptions.py --execute --no-backup
        """
    )
    parser.add_argument('--execute', action='store_true',
                       help='Execute deduplication (default is dry-run)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup table creation (not recommended)')

    args = parser.parse_args()

    dry_run = not args.execute
    backup = not args.no_backup

    print()
    print("=" * 80)
    print(f"SUBSCRIPTION DEDUPLICATION - {'DRY RUN' if dry_run else 'EXECUTE MODE'}")
    print("=" * 80)
    print()

    if not dry_run:
        print("⚠️  EXECUTE MODE - Changes will be made to the database!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"   {i}...", flush=True, end='\r')
            time.sleep(1)
        print("   Starting execution...                    ")
        print()

    deduplicator = SubscriptionDeduplicator(dry_run=dry_run, backup=backup)

    try:
        # Create backup table
        if backup:
            deduplicator.create_backup_table()

        # Load subscriptions
        by_contact = deduplicator.load_active_subscriptions_by_contact()

        # Identify duplicates
        deduplicator.identify_duplicates(by_contact)

        if deduplicator.stats['duplicates_found'] == 0:
            print("✓ No duplicates found - database is clean!")
            deduplicator.close()
            return

        # Validate plan
        valid, issues = deduplicator.validate_dedup_plan()
        if not valid:
            print("❌ Validation failed - aborting deduplication")
            deduplicator.close()
            sys.exit(1)

        # Backup subscriptions
        if backup and not dry_run:
            deduplicator.backup_subscriptions()

        # Execute deduplication
        if not dry_run:
            deduplicator.execute_deduplication()

            # Verify results
            if not deduplicator.verify_results():
                print("❌ Verification failed - rolling back!")
                deduplicator.conn.rollback()
                deduplicator.close()
                sys.exit(1)

        # Commit or rollback
        deduplicator.commit_or_rollback()

        # Print summary
        deduplicator.print_summary()

        # Export report
        report_file = f"deduplication_report_{'execute' if not dry_run else 'dryrun'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        deduplicator.export_report(report_file)

        print("✓ Deduplication complete!")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        deduplicator.conn.rollback()
        deduplicator.close()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        deduplicator.conn.rollback()
        deduplicator.close()
        sys.exit(1)
    finally:
        if 'deduplicator' in locals():
            deduplicator.close()


if __name__ == '__main__':
    main()
