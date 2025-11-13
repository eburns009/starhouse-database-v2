#!/usr/bin/env python3
"""
Subscription Duplicate Analysis - FAANG Quality
================================================
Comprehensive analysis of duplicate subscriptions to identify root cause
and design appropriate deduplication strategy.

This script performs:
1. Identification of all duplicate patterns
2. Root cause analysis (PayPal vs Kajabi collision)
3. Data integrity verification
4. Safe deduplication recommendations

Author: Claude Code
Date: 2025-11-12
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url


@dataclass
class Subscription:
    """Subscription record with metadata"""
    id: int
    contact_id: int
    kajabi_subscription_id: Optional[str]
    paypal_subscription_reference: Optional[str]
    status: str
    amount: Decimal
    billing_cycle: str
    start_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    payment_processor: Optional[str]

    @property
    def source(self) -> str:
        """Determine subscription source"""
        if self.kajabi_subscription_id and self.paypal_subscription_reference:
            # Check if kajabi_subscription_id looks like PayPal ID
            if self.kajabi_subscription_id.startswith('I-'):
                return 'paypal_only'
            return 'kajabi_and_paypal'
        elif self.kajabi_subscription_id:
            # Check if it's actually a PayPal ID in wrong field
            if self.kajabi_subscription_id.startswith('I-'):
                return 'paypal_misplaced'
            return 'kajabi_only'
        elif self.paypal_subscription_reference:
            return 'paypal_only'
        return 'unknown'

    def is_duplicate_of(self, other: 'Subscription') -> Tuple[bool, str]:
        """Check if this subscription is a duplicate of another"""
        if self.contact_id != other.contact_id:
            return False, "Different contacts"

        if self.status != other.status:
            return False, "Different statuses"

        # Amount match (within $1 tolerance)
        amount_diff = abs(float(self.amount) - float(other.amount))
        if amount_diff > 1.0:
            return False, f"Amount differs by ${amount_diff:.2f}"

        # Billing cycle match
        if self.billing_cycle != other.billing_cycle:
            return False, "Different billing cycles"

        # Check if one is from Kajabi and one from PayPal
        if self.source in ['kajabi_only', 'kajabi_and_paypal'] and \
           other.source in ['paypal_only', 'paypal_misplaced']:
            return True, "Kajabi-PayPal duplicate"

        if self.source in ['paypal_only', 'paypal_misplaced'] and \
           other.source in ['kajabi_only', 'kajabi_and_paypal']:
            return True, "PayPal-Kajabi duplicate"

        return False, "Not a duplicate"


@dataclass
class DuplicateGroup:
    """Group of duplicate subscriptions for a contact"""
    contact_id: int
    contact_email: str
    contact_name: str
    subscriptions: List[Subscription]

    @property
    def total_subscriptions(self) -> int:
        return len(self.subscriptions)

    @property
    def kajabi_subscriptions(self) -> List[Subscription]:
        return [s for s in self.subscriptions if s.source in ['kajabi_only', 'kajabi_and_paypal']]

    @property
    def paypal_subscriptions(self) -> List[Subscription]:
        return [s for s in self.subscriptions if s.source in ['paypal_only', 'paypal_misplaced']]

    @property
    def duplicate_count(self) -> int:
        """Number of duplicates (total - 1)"""
        return max(0, self.total_subscriptions - 1)

    def get_canonical_subscription(self) -> Optional[Subscription]:
        """Get the subscription that should be kept (Kajabi preferred)"""
        # Prefer Kajabi subscriptions
        kajabi_subs = self.kajabi_subscriptions
        if kajabi_subs:
            # Return the oldest Kajabi subscription
            return min(kajabi_subs, key=lambda s: s.created_at)

        # Otherwise return oldest PayPal subscription
        if self.subscriptions:
            return min(self.subscriptions, key=lambda s: s.created_at)

        return None

    def get_duplicates_to_remove(self) -> List[Subscription]:
        """Get subscriptions that should be removed"""
        canonical = self.get_canonical_subscription()
        if not canonical:
            return []

        return [s for s in self.subscriptions if s.id != canonical.id]


class SubscriptionDuplicateAnalyzer:
    """Comprehensive subscription duplicate analyzer"""

    def __init__(self):
        self.conn = psycopg2.connect(get_database_url())
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        self.duplicate_groups: List[DuplicateGroup] = []

    def load_subscriptions(self) -> Dict[int, List[Subscription]]:
        """Load all subscriptions grouped by contact"""
        print("📊 Loading all subscriptions from database...")

        self.cur.execute("""
            SELECT
                s.id,
                s.contact_id,
                s.kajabi_subscription_id,
                s.paypal_subscription_reference,
                s.status,
                s.amount,
                s.billing_cycle,
                s.start_date,
                s.created_at,
                s.updated_at,
                s.payment_processor,
                c.email as contact_email,
                c.first_name || ' ' || c.last_name as contact_name
            FROM subscriptions s
            JOIN contacts c ON s.contact_id = c.id
            WHERE s.deleted_at IS NULL
            ORDER BY s.contact_id, s.created_at
        """)

        rows = self.cur.fetchall()
        print(f"✓ Loaded {len(rows)} subscriptions\n")

        # Group by contact
        by_contact: Dict[int, List[Tuple[Subscription, str, str]]] = {}
        for row in rows:
            sub = Subscription(
                id=row['id'],
                contact_id=row['contact_id'],
                kajabi_subscription_id=row['kajabi_subscription_id'],
                paypal_subscription_reference=row['paypal_subscription_reference'],
                status=row['status'],
                amount=Decimal(str(row['amount'])),
                billing_cycle=row['billing_cycle'],
                start_date=row['start_date'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                payment_processor=row['payment_processor']
            )

            if row['contact_id'] not in by_contact:
                by_contact[row['contact_id']] = []

            by_contact[row['contact_id']].append((sub, row['contact_email'], row['contact_name']))

        return by_contact

    def identify_duplicates(self, by_contact: Dict[int, List[Tuple[Subscription, str, str]]]):
        """Identify duplicate subscription groups"""
        print("🔍 Identifying duplicate subscription patterns...\n")

        for contact_id, subs_with_info in by_contact.items():
            # Filter to active subscriptions only
            active_subs = [
                (s, email, name) for s, email, name in subs_with_info
                if s.status == 'active'
            ]

            if len(active_subs) <= 1:
                continue

            # Extract subscriptions and metadata
            subscriptions = [s for s, _, _ in active_subs]
            email = active_subs[0][1]
            name = active_subs[0][2]

            # Check if they're actually duplicates
            is_duplicate_group = False
            for i, sub1 in enumerate(subscriptions):
                for sub2 in subscriptions[i+1:]:
                    is_dup, reason = sub1.is_duplicate_of(sub2)
                    if is_dup:
                        is_duplicate_group = True
                        break
                if is_duplicate_group:
                    break

            if is_duplicate_group:
                self.duplicate_groups.append(DuplicateGroup(
                    contact_id=contact_id,
                    contact_email=email,
                    contact_name=name,
                    subscriptions=subscriptions
                ))

        print(f"✓ Found {len(self.duplicate_groups)} contacts with duplicate subscriptions\n")

    def analyze_patterns(self) -> Dict:
        """Analyze duplicate patterns"""
        print("📈 Analyzing duplicate patterns...\n")

        total_duplicates = sum(g.duplicate_count for g in self.duplicate_groups)
        total_subscriptions = sum(g.total_subscriptions for g in self.duplicate_groups)

        # Analyze by pattern type
        kajabi_paypal_duplicates = sum(
            1 for g in self.duplicate_groups
            if len(g.kajabi_subscriptions) > 0 and len(g.paypal_subscriptions) > 0
        )

        paypal_only_duplicates = sum(
            1 for g in self.duplicate_groups
            if len(g.kajabi_subscriptions) == 0 and len(g.paypal_subscriptions) > 1
        )

        kajabi_only_duplicates = sum(
            1 for g in self.duplicate_groups
            if len(g.paypal_subscriptions) == 0 and len(g.kajabi_subscriptions) > 1
        )

        # Analyze subscription sources
        source_counts = {}
        for group in self.duplicate_groups:
            for sub in group.subscriptions:
                source = sub.source
                source_counts[source] = source_counts.get(source, 0) + 1

        # Analyze misplaced PayPal IDs
        misplaced_paypal_ids = sum(
            1 for g in self.duplicate_groups
            for s in g.subscriptions
            if s.source == 'paypal_misplaced'
        )

        analysis = {
            'total_contacts_with_duplicates': len(self.duplicate_groups),
            'total_subscriptions_involved': total_subscriptions,
            'total_duplicate_records': total_duplicates,
            'patterns': {
                'kajabi_paypal_collision': kajabi_paypal_duplicates,
                'paypal_only_duplicates': paypal_only_duplicates,
                'kajabi_only_duplicates': kajabi_only_duplicates
            },
            'source_distribution': source_counts,
            'root_cause': {
                'misplaced_paypal_ids': misplaced_paypal_ids,
                'description': 'PayPal IDs stored in kajabi_subscription_id field' if misplaced_paypal_ids > 0 else 'Genuine duplicates'
            }
        }

        return analysis

    def generate_deduplication_plan(self) -> Dict:
        """Generate safe deduplication plan"""
        print("📋 Generating deduplication plan...\n")

        plan = {
            'safe_to_remove': [],
            'needs_review': [],
            'statistics': {
                'total_to_remove': 0,
                'total_to_keep': 0,
                'estimated_time_seconds': 0
            }
        }

        for group in self.duplicate_groups:
            canonical = group.get_canonical_subscription()
            to_remove = group.get_duplicates_to_remove()

            if not canonical or not to_remove:
                continue

            # Check if safe to remove
            is_safe = True
            reason = "Safe: Clear Kajabi-PayPal duplicate"

            # Red flags that need review
            if len(group.kajabi_subscriptions) > 1:
                is_safe = False
                reason = "REVIEW: Multiple Kajabi subscriptions"

            if len(group.paypal_subscriptions) > 1 and len(group.kajabi_subscriptions) == 0:
                is_safe = False
                reason = "REVIEW: Multiple PayPal subscriptions without Kajabi"

            # Check amount differences
            amounts = [float(s.amount) for s in group.subscriptions]
            if max(amounts) - min(amounts) > 0.5:
                is_safe = False
                reason = "REVIEW: Amounts differ by more than $0.50"

            removal_plan = {
                'contact_id': group.contact_id,
                'contact_email': group.contact_email,
                'contact_name': group.contact_name,
                'canonical_subscription_id': canonical.id,
                'canonical_source': canonical.source,
                'subscriptions_to_remove': [
                    {
                        'id': s.id,
                        'source': s.source,
                        'amount': float(s.amount),
                        'kajabi_subscription_id': s.kajabi_subscription_id,
                        'paypal_subscription_reference': s.paypal_subscription_reference,
                        'created_at': s.created_at.isoformat()
                    }
                    for s in to_remove
                ],
                'reason': reason
            }

            if is_safe:
                plan['safe_to_remove'].append(removal_plan)
                plan['statistics']['total_to_remove'] += len(to_remove)
            else:
                plan['needs_review'].append(removal_plan)

            plan['statistics']['total_to_keep'] += 1

        # Estimate time (pessimistic: 100ms per removal)
        plan['statistics']['estimated_time_seconds'] = plan['statistics']['total_to_remove'] * 0.1

        return plan

    def print_summary(self, analysis: Dict, plan: Dict):
        """Print comprehensive summary"""
        print("=" * 80)
        print("SUBSCRIPTION DUPLICATE ANALYSIS - SUMMARY")
        print("=" * 80)
        print()

        print("📊 DUPLICATE STATISTICS")
        print("-" * 80)
        print(f"Contacts with duplicates:     {analysis['total_contacts_with_duplicates']}")
        print(f"Total subscriptions involved: {analysis['total_subscriptions_involved']}")
        print(f"Duplicate records to remove:  {analysis['total_duplicate_records']}")
        print()

        print("🔍 PATTERN ANALYSIS")
        print("-" * 80)
        patterns = analysis['patterns']
        print(f"Kajabi-PayPal collisions:     {patterns['kajabi_paypal_collision']}")
        print(f"PayPal-only duplicates:       {patterns['paypal_only_duplicates']}")
        print(f"Kajabi-only duplicates:       {patterns['kajabi_only_duplicates']}")
        print()

        print("🎯 ROOT CAUSE")
        print("-" * 80)
        rc = analysis['root_cause']
        print(f"Misplaced PayPal IDs:         {rc['misplaced_paypal_ids']}")
        print(f"Description:                  {rc['description']}")
        print()

        print("📋 DEDUPLICATION PLAN")
        print("-" * 80)
        stats = plan['statistics']
        print(f"Safe to auto-remove:          {len(plan['safe_to_remove'])} contacts ({stats['total_to_remove']} subscriptions)")
        print(f"Needs manual review:          {len(plan['needs_review'])} contacts")
        print(f"Will keep (canonical):        {stats['total_to_keep']} subscriptions")
        print(f"Estimated time:               {stats['estimated_time_seconds']:.1f} seconds")
        print()

        if plan['needs_review']:
            print("⚠️  ITEMS REQUIRING REVIEW")
            print("-" * 80)
            for item in plan['needs_review'][:5]:
                print(f"  • {item['contact_email']}: {item['reason']}")
            if len(plan['needs_review']) > 5:
                print(f"  ... and {len(plan['needs_review']) - 5} more")
            print()

        print("=" * 80)
        print()

    def export_results(self, analysis: Dict, plan: Dict, output_dir: str = '.'):
        """Export analysis results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export analysis JSON
        analysis_file = f"{output_dir}/subscription_duplicate_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"✓ Exported analysis to: {analysis_file}")

        # Export deduplication plan
        plan_file = f"{output_dir}/subscription_deduplication_plan_{timestamp}.json"
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2, default=str)
        print(f"✓ Exported deduplication plan to: {plan_file}")

        # Export CSV for easy review
        csv_file = f"{output_dir}/subscription_duplicates_review_{timestamp}.csv"
        import csv
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Contact Email', 'Contact Name', 'Total Subs', 'Kajabi Subs',
                'PayPal Subs', 'Canonical ID', 'To Remove', 'Status'
            ])

            for item in plan['safe_to_remove']:
                writer.writerow([
                    item['contact_email'],
                    item['contact_name'],
                    len(item['subscriptions_to_remove']) + 1,
                    sum(1 for s in item['subscriptions_to_remove'] if 'kajabi' in s['source']) +
                        (1 if 'kajabi' in item['canonical_source'] else 0),
                    sum(1 for s in item['subscriptions_to_remove'] if 'paypal' in s['source']) +
                        (1 if 'paypal' in item['canonical_source'] else 0),
                    item['canonical_subscription_id'],
                    ','.join(str(s['id']) for s in item['subscriptions_to_remove']),
                    'Safe to remove'
                ])

            for item in plan['needs_review']:
                writer.writerow([
                    item['contact_email'],
                    item['contact_name'],
                    len(item['subscriptions_to_remove']) + 1,
                    sum(1 for s in item['subscriptions_to_remove'] if 'kajabi' in s['source']) +
                        (1 if 'kajabi' in item['canonical_source'] else 0),
                    sum(1 for s in item['subscriptions_to_remove'] if 'paypal' in s['source']) +
                        (1 if 'paypal' in item['canonical_source'] else 0),
                    item['canonical_subscription_id'],
                    ','.join(str(s['id']) for s in item['subscriptions_to_remove']),
                    f'NEEDS REVIEW: {item["reason"]}'
                ])

        print(f"✓ Exported CSV review to: {csv_file}")
        print()

        return analysis_file, plan_file, csv_file

    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()


def main():
    """Main execution"""
    print()
    print("=" * 80)
    print("SUBSCRIPTION DUPLICATE ANALYSIS")
    print("=" * 80)
    print()

    analyzer = SubscriptionDuplicateAnalyzer()

    try:
        # Load and analyze
        by_contact = analyzer.load_subscriptions()
        analyzer.identify_duplicates(by_contact)

        if not analyzer.duplicate_groups:
            print("✓ No duplicate subscriptions found!")
            return

        analysis = analyzer.analyze_patterns()
        plan = analyzer.generate_deduplication_plan()

        # Print summary
        analyzer.print_summary(analysis, plan)

        # Export results
        analyzer.export_results(analysis, plan)

        print("✓ Analysis complete!")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        analyzer.close()


if __name__ == '__main__':
    main()
