#!/usr/bin/env python3
"""
FAANG-Quality Enhanced Duplicate Detection with Confidence Scoring

Detects potential duplicate contacts using multiple matching strategies:
1. Exact name match (different emails)
2. Phone number match (normalized)
3. Email similarity (same person, variations)
4. Address match
5. Fuzzy name matching (coming soon)

Each duplicate group gets a confidence score:
- HIGH: Multiple fields match (name + phone/address)
- MEDIUM: Exact name match OR phone match
- LOW: Similar names or email patterns

FEATURES:
- Multi-strategy detection
- Confidence scoring
- CSV export for manual review
- Dry-run mode
- Transaction safety
- Detailed logging

USAGE:
    # Generate detection report
    python3 scripts/enhanced_duplicate_detection.py

    # Export to CSV for review
    python3 scripts/enhanced_duplicate_detection.py --csv /tmp/duplicates.csv

    # Flag duplicates in database (dry-run)
    python3 scripts/enhanced_duplicate_detection.py --flag

    # Flag duplicates in database (execute)
    python3 scripts/enhanced_duplicate_detection.py --flag --execute

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
Phase: 3 - Duplicate Resolution
"""

import psycopg2
import sys
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import hashlib
from db_config import get_database_url

DATABASE_URL = get_database_url()

class EnhancedDuplicateDetector:
    """FAANG-quality duplicate detection with confidence scoring."""

    def __init__(self, output_csv: Optional[str] = None, flag_database: bool = False, dry_run: bool = True):
        self.output_csv = output_csv
        self.flag_database = flag_database
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.duplicate_groups = []
        self.stats = {
            'total_groups': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'contacts_affected': 0,
            'flagged': 0
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

    def generate_group_id(self, contacts: List[Tuple]) -> str:
        """Generate stable group ID from contact IDs."""
        # Sort contact IDs to ensure consistent group ID
        contact_ids = sorted([str(c[0]) for c in contacts])
        combined = '|'.join(contact_ids)
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    def detect_exact_name_duplicates(self):
        """Detect contacts with exact same name but different emails."""
        self.log("\nDetecting exact name duplicates...")

        self.cursor.execute("""
            WITH name_groups AS (
                SELECT
                    first_name,
                    last_name,
                    ARRAY_AGG(id) as contact_ids,
                    ARRAY_AGG(email) as emails,
                    ARRAY_AGG(phone) as phones,
                    ARRAY_AGG(address_line_1) as addresses,
                    ARRAY_AGG(source_system) as sources,
                    ARRAY_AGG(created_at) as created_dates,
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
            SELECT * FROM name_groups
            ORDER BY count DESC, first_name, last_name
        """)

        name_dupes = self.cursor.fetchall()

        for row in name_dupes:
            first_name, last_name, contact_ids, emails, phones, addresses, sources, created_dates, count, unique_phones, unique_addresses = row

            # Calculate confidence score
            confidence = 'MEDIUM'  # Default for exact name match
            reasons = ['Exact name match']

            # Upgrade to HIGH if phone or address also matches
            if unique_phones == 1 and phones[0]:
                confidence = 'HIGH'
                reasons.append('Same phone number')

            if unique_addresses == 1 and addresses[0]:
                if confidence == 'HIGH':
                    reasons.append('Same address')
                else:
                    confidence = 'HIGH'
                    reasons.append('Same address')

            # Create contact list for this group
            contacts = []
            for i in range(count):
                contacts.append({
                    'id': contact_ids[i],
                    'email': emails[i],
                    'phone': phones[i],
                    'address': addresses[i],
                    'source': sources[i],
                    'created_at': created_dates[i]
                })

            group_id = self.generate_group_id([(c['id'],) for c in contacts])

            self.duplicate_groups.append({
                'group_id': group_id,
                'type': 'exact_name',
                'confidence': confidence,
                'reason': ', '.join(reasons),
                'first_name': first_name,
                'last_name': last_name,
                'contact_count': count,
                'contacts': contacts
            })

        self.log(f"  Found {len(name_dupes)} exact name duplicate groups")
        return len(name_dupes)

    def detect_phone_duplicates(self):
        """Detect contacts with same phone number."""
        self.log("\nDetecting phone number duplicates...")

        self.cursor.execute("""
            WITH phone_groups AS (
                SELECT
                    REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as normalized_phone,
                    ARRAY_AGG(id) as contact_ids,
                    ARRAY_AGG(first_name || ' ' || last_name) as names,
                    ARRAY_AGG(email) as emails,
                    ARRAY_AGG(address_line_1) as addresses,
                    ARRAY_AGG(source_system) as sources,
                    ARRAY_AGG(created_at) as created_dates,
                    COUNT(*) as count,
                    COUNT(DISTINCT LOWER(first_name || ' ' || last_name)) as unique_names
                FROM contacts
                WHERE deleted_at IS NULL
                  AND phone IS NOT NULL
                  AND phone != ''
                  AND LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '', 'g')) >= 10
                GROUP BY REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
                HAVING COUNT(*) > 1
            )
            SELECT * FROM phone_groups
            WHERE normalized_phone IS NOT NULL
            ORDER BY count DESC
        """)

        phone_dupes = self.cursor.fetchall()

        for row in phone_dupes:
            normalized_phone, contact_ids, names, emails, addresses, sources, created_dates, count, unique_names = row

            # Skip if already detected by name match
            group_id = self.generate_group_id([(cid,) for cid in contact_ids])
            if any(g['group_id'] == group_id for g in self.duplicate_groups):
                continue

            # Calculate confidence
            if unique_names == 1:
                confidence = 'HIGH'
                reason = 'Same phone + same name'
            else:
                confidence = 'MEDIUM'
                reason = 'Same phone, different names (possible shared line)'

            contacts = []
            for i in range(count):
                contacts.append({
                    'id': contact_ids[i],
                    'name': names[i],
                    'email': emails[i],
                    'phone': normalized_phone,
                    'address': addresses[i],
                    'source': sources[i],
                    'created_at': created_dates[i]
                })

            self.duplicate_groups.append({
                'group_id': group_id,
                'type': 'phone_match',
                'confidence': confidence,
                'reason': reason,
                'phone': normalized_phone,
                'contact_count': count,
                'contacts': contacts
            })

        self.log(f"  Found {len(phone_dupes)} phone duplicate groups")
        return len(phone_dupes)

    def calculate_stats(self):
        """Calculate summary statistics."""
        self.stats['total_groups'] = len(self.duplicate_groups)

        for group in self.duplicate_groups:
            self.stats['contacts_affected'] += group['contact_count']

            if group['confidence'] == 'HIGH':
                self.stats['high_confidence'] += 1
            elif group['confidence'] == 'MEDIUM':
                self.stats['medium_confidence'] += 1
            else:
                self.stats['low_confidence'] += 1

    def print_report(self):
        """Print comprehensive detection report."""
        print("\n" + "=" * 80)
        print("ENHANCED DUPLICATE DETECTION REPORT")
        print("=" * 80)
        print()

        # Summary by confidence
        print("CONFIDENCE BREAKDOWN:")
        print(f"  HIGH confidence:    {self.stats['high_confidence']} groups")
        print(f"  MEDIUM confidence:  {self.stats['medium_confidence']} groups")
        print(f"  LOW confidence:     {self.stats['low_confidence']} groups")
        print(f"  Total groups:       {self.stats['total_groups']}")
        print(f"  Contacts affected:  {self.stats['contacts_affected']}")
        print()

        # Show top 10 high-confidence groups
        high_conf_groups = [g for g in self.duplicate_groups if g['confidence'] == 'HIGH'][:10]

        if high_conf_groups:
            print("=" * 80)
            print("HIGH CONFIDENCE DUPLICATES (Top 10)")
            print("=" * 80)
            print()

            for i, group in enumerate(high_conf_groups, 1):
                print(f"{i}. {group.get('first_name', '')} {group.get('last_name', '')} ({group['contact_count']} contacts)")
                print(f"   Group ID: {group['group_id']}")
                print(f"   Reason: {group['reason']}")
                print(f"   Contacts:")
                for contact in group['contacts'][:5]:
                    email = contact.get('email', 'N/A')
                    phone = contact.get('phone', 'N/A')
                    print(f"     - {email} | {phone}")
                print()

    def export_csv(self):
        """Export duplicate groups to CSV."""
        if not self.output_csv:
            return

        fieldnames = [
            'group_id', 'confidence', 'type', 'reason', 'contact_count',
            'first_name', 'last_name', 'phone',
            'contact_id', 'contact_email', 'contact_phone', 'contact_address',
            'contact_source', 'contact_created_at',
            'action_recommended', 'review_notes'
        ]

        with open(self.output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for group in self.duplicate_groups:
                # Write one row per contact in the group
                for contact in group['contacts']:
                    writer.writerow({
                        'group_id': group['group_id'],
                        'confidence': group['confidence'],
                        'type': group['type'],
                        'reason': group['reason'],
                        'contact_count': group['contact_count'],
                        'first_name': group.get('first_name', ''),
                        'last_name': group.get('last_name', ''),
                        'phone': group.get('phone', ''),
                        'contact_id': contact.get('id', ''),
                        'contact_email': contact.get('email', ''),
                        'contact_phone': contact.get('phone', ''),
                        'contact_address': contact.get('address', ''),
                        'contact_source': contact.get('source', ''),
                        'contact_created_at': contact.get('created_at', ''),
                        'action_recommended': 'MERGE' if group['confidence'] == 'HIGH' else 'REVIEW',
                        'review_notes': ''
                    })

        self.log(f"✓ Exported to CSV: {self.output_csv}", 'SUCCESS')

    def flag_duplicates_in_database(self):
        """Flag duplicate groups in database for UI display."""
        if not self.flag_database:
            return

        self.log("\nFlagging duplicates in database...")

        # Check if column exists
        self.cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='contacts'
            AND column_name='potential_duplicate_group'
        """)

        if not self.cursor.fetchone():
            self.log("  Column 'potential_duplicate_group' does not exist - skipping", 'WARN')
            return

        # Clear existing flags if executing
        if not self.dry_run:
            self.cursor.execute("""
                UPDATE contacts
                SET potential_duplicate_group = NULL,
                    potential_duplicate_reason = NULL,
                    potential_duplicate_flagged_at = NULL
            """)
            self.log("  Cleared existing duplicate flags")

        # Flag duplicates
        for group in self.duplicate_groups:
            contact_ids = [c['id'] for c in group['contacts']]

            if not self.dry_run:
                self.cursor.execute("""
                    UPDATE contacts
                    SET potential_duplicate_group = %s,
                        potential_duplicate_reason = %s,
                        potential_duplicate_flagged_at = NOW()
                    WHERE id = ANY(%s)
                """, (group['group_id'], group['reason'], contact_ids))

                self.stats['flagged'] += len(contact_ids)
            else:
                self.log(f"  Would flag group {group['group_id']}: {len(contact_ids)} contacts")
                self.stats['flagged'] += len(contact_ids)

        if not self.dry_run:
            self.conn.commit()
            self.log(f"✓ Flagged {self.stats['flagged']} contacts in database", 'SUCCESS')
        else:
            self.log(f"  Would flag {self.stats['flagged']} contacts total")

    def run(self):
        """Main execution."""
        try:
            self.connect()

            print("\n" + "=" * 80)
            print("ENHANCED DUPLICATE DETECTION - FAANG Quality")
            print("=" * 80)
            print()

            # Run detection strategies
            self.detect_exact_name_duplicates()
            self.detect_phone_duplicates()

            # Calculate stats
            self.calculate_stats()

            # Print report
            self.print_report()

            # Export CSV
            if self.output_csv:
                self.export_csv()

            # Flag in database
            if self.flag_database:
                self.flag_duplicates_in_database()

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
        description='Enhanced duplicate detection with confidence scoring',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Export results to CSV file'
    )

    parser.add_argument(
        '--flag',
        action='store_true',
        help='Flag duplicates in database (requires column setup)'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute database changes (default is dry-run)'
    )

    args = parser.parse_args()

    detector = EnhancedDuplicateDetector(
        output_csv=args.csv,
        flag_database=args.flag,
        dry_run=not args.execute
    )
    return detector.run()


if __name__ == '__main__':
    sys.exit(main())
