#!/usr/bin/env python3
"""
FAANG-Quality Batch Update for High-Confidence 'nan' Names

Updates 16 contacts with high-confidence name recovery:
- 11 firstname@domain.com patterns
- 5 organization accounts

FEATURES:
- Dry-run mode (default)
- Atomic transaction with rollback
- Before/after verification
- Detailed logging

USAGE:
    # Dry-run (preview)
    python3 scripts/batch_update_nan_names.py

    # Execute updates
    python3 scripts/batch_update_nan_names.py --execute

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
"""

import psycopg2
import sys
from datetime import datetime
import argparse

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

# High-confidence name updates
HIGH_CONFIDENCE_NAMES = [
    ('eb59cf50-6653-481e-ae76-9917456b0f55', 'Carrie', None, 'carrie@solbreath.com'),
    ('6cd5c902-864a-4fcb-befe-54ea00c7d505', 'Christian', None, 'christian@soulfulpower.com'),
    ('948fdad3-5b8e-4f7d-baa4-cc9c949316c6', 'Claudia', None, 'claudia@topmobility.cl'),
    ('bbb98aa8-5b15-40e6-91f0-3c1395c17aca', 'Craig', None, 'craig@electricalteacher.com'),
    ('843e0670-280b-49f3-aa96-78f0d44631ac', 'Cynthia', None, 'cynthia@successbydesign.net'),
    ('1c105293-90bb-4ffb-8373-325fdd3370cd', 'Diana', None, 'diana@transformationagency.com'),
    ('f2b30705-86c3-427e-bf91-887f68e8368f', 'Edwin', None, 'edwin@tergar.org'),
    ('1c7ca7aa-67c4-4e74-a30d-67c5882c29d6', 'Gayatri', None, 'gayatri@divineunionfoundation.org'),
    ('cbfbfd0b-91eb-41d5-b277-5e1b0877a2b5', 'Jamie', None, 'jamie@flowgenomeproject.com'),
    ('a763a61d-9f42-481d-8d40-12e96df9f626', 'Jason', None, 'jason@bowman.net'),
    ('bc79a6d4-6660-4e8a-a943-5987b349d4a6', 'Lexi', None, 'lexi@ritualreturn.com'),
]

# Organization accounts
ORGANIZATION_ACCOUNTS = [
    ('83697259-9e54-4b46-b4ef-c4efeae1b076', 'Organization', 'Free Range Human', 'info@freerangehuman.com'),
    ('e7e47d7d-e61f-4e3e-af79-0f1da2d6de3c', 'Organization', 'Turning The Wheel', 'info@turningthewheel.org'),
    ('ea0194b6-1a9c-49ce-a1d3-8088a79fac05', 'Organization', 'Embracing Your Wholeness', 'payment@embracingyourwholeness.com'),
    ('1bbf773c-f72b-49ba-b8c3-50dd50f6a63c', 'Organization', 'Woombie', 'sales@woombie.com'),
    ('13566340-efc7-494f-8c03-f18ebeac3bc3', 'Organization', 'Mia Magik', 'team@miamagik.com'),
]

class BatchNameUpdater:
    """FAANG-quality batch name updater."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'name_updates': 0,
            'org_updates': 0,
            'errors': 0,
            'verified': 0
        }

    def log(self, message: str, level: str = 'INFO'):
        """Structured logging."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = {
            'INFO': '✓',
            'WARN': '⚠',
            'ERROR': '✗',
            'SUCCESS': '✅'
        }.get(level, '·')
        print(f"[{timestamp}] {prefix} {message}")

    def connect(self):
        """Establish connection."""
        try:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.cursor = self.conn.cursor()
            self.log("Database connection established")
        except Exception as e:
            self.log(f"Failed to connect: {e}", 'ERROR')
            sys.exit(1)

    def disconnect(self):
        """Clean up."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

    def verify_before(self):
        """Verify contacts have 'nan' names before update."""
        all_ids = [c[0] for c in HIGH_CONFIDENCE_NAMES] + [c[0] for c in ORGANIZATION_ACCOUNTS]

        self.cursor.execute("""
            SELECT id, first_name, last_name, email
            FROM contacts
            WHERE id::text = ANY(%s)
        """, (all_ids,))

        results = self.cursor.fetchall()

        print("\n" + "=" * 80)
        print("BEFORE UPDATE - CURRENT STATE")
        print("=" * 80)

        nan_count = 0
        for row in results:
            if row[1] == 'nan' or row[2] == 'nan':
                print(f"✓ {row[3]}: '{row[1]}' '{row[2]}'")
                nan_count += 1
            else:
                print(f"⚠ {row[3]}: '{row[1]}' '{row[2]}' (already updated?)")

        print(f"\nContacts with 'nan': {nan_count}/{len(all_ids)}")
        return nan_count

    def update_high_confidence_names(self):
        """Update firstname@domain.com patterns."""
        self.log("\nUpdating high-confidence names (firstname@domain.com pattern)...")

        for contact_id, first_name, _, email in HIGH_CONFIDENCE_NAMES:
            try:
                if not self.dry_run:
                    self.cursor.execute("""
                        UPDATE contacts
                        SET first_name = %s, updated_at = NOW()
                        WHERE id = %s AND first_name = 'nan'
                    """, (first_name, contact_id))

                    if self.cursor.rowcount > 0:
                        self.stats['name_updates'] += 1
                        self.log(f"  ✓ {email} → {first_name}")
                    else:
                        self.log(f"  ⚠ {email} - no update needed", 'WARN')
                else:
                    self.log(f"  Would update: {email} → {first_name}")
                    self.stats['name_updates'] += 1

            except Exception as e:
                self.log(f"  Failed to update {email}: {e}", 'ERROR')
                self.stats['errors'] += 1

    def update_organization_accounts(self):
        """Update organization accounts."""
        self.log("\nUpdating organization accounts...")

        for contact_id, first_name, last_name, email in ORGANIZATION_ACCOUNTS:
            try:
                if not self.dry_run:
                    self.cursor.execute("""
                        UPDATE contacts
                        SET first_name = %s, last_name = %s, updated_at = NOW()
                        WHERE id = %s AND first_name = 'nan'
                    """, (first_name, last_name, contact_id))

                    if self.cursor.rowcount > 0:
                        self.stats['org_updates'] += 1
                        self.log(f"  ✓ {email} → {first_name} {last_name}")
                    else:
                        self.log(f"  ⚠ {email} - no update needed", 'WARN')
                else:
                    self.log(f"  Would update: {email} → {first_name} {last_name}")
                    self.stats['org_updates'] += 1

            except Exception as e:
                self.log(f"  Failed to update {email}: {e}", 'ERROR')
                self.stats['errors'] += 1

    def verify_after(self):
        """Verify updates were successful."""
        if self.dry_run:
            return

        self.log("\nVerifying updates...")

        all_ids = [c[0] for c in HIGH_CONFIDENCE_NAMES] + [c[0] for c in ORGANIZATION_ACCOUNTS]

        self.cursor.execute("""
            SELECT id, first_name, last_name, email
            FROM contacts
            WHERE id::text = ANY(%s)
        """, (all_ids,))

        results = self.cursor.fetchall()

        print("\n" + "=" * 80)
        print("AFTER UPDATE - VERIFICATION")
        print("=" * 80)

        success_count = 0
        for row in results:
            if row[1] != 'nan' and row[2] != 'nan':
                print(f"✓ {row[3]}: '{row[1]}' '{row[2]}'")
                success_count += 1
                self.stats['verified'] += 1
            else:
                print(f"✗ {row[3]}: '{row[1]}' '{row[2]}' (STILL HAS NAN!)")

        print(f"\nSuccessfully updated: {success_count}/{len(all_ids)}")

        # Check remaining nan names
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND (first_name = 'nan' OR last_name = 'nan')
        """)

        remaining = self.cursor.fetchone()[0]
        print(f"Remaining 'nan' names in database: {remaining}")

    def print_summary(self):
        """Print summary report."""
        print("\n" + "=" * 80)
        print("BATCH UPDATE SUMMARY")
        print("=" * 80)
        print(f"High-confidence name updates: {self.stats['name_updates']}")
        print(f"Organization account updates:  {self.stats['org_updates']}")
        print(f"Total updates:                 {self.stats['name_updates'] + self.stats['org_updates']}")
        print(f"Errors:                        {self.stats['errors']}")
        if not self.dry_run:
            print(f"Verified successful:           {self.stats['verified']}")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠ DRY RUN MODE - No changes were made")
            print("Run with --execute to apply changes")
        else:
            print("\n✅ Updates completed successfully!")

    def run(self):
        """Main execution."""
        try:
            self.connect()

            if self.dry_run:
                print("\n" + "=" * 80)
                print("DRY RUN MODE - Preview Changes")
                print("=" * 80)

            # Verify before
            nan_count = self.verify_before()

            if nan_count == 0:
                self.log("\nNo contacts with 'nan' names found - all done!", 'SUCCESS')
                return 0

            # Execute updates
            self.update_high_confidence_names()
            self.update_organization_accounts()

            # Commit transaction
            if not self.dry_run:
                if self.stats['errors'] == 0:
                    self.conn.commit()
                    self.log("Transaction committed successfully", 'SUCCESS')
                else:
                    self.conn.rollback()
                    self.log("Transaction rolled back due to errors", 'ERROR')
                    return 1

            # Verify after
            self.verify_after()

            # Summary
            self.print_summary()

            return 0

        except Exception as e:
            self.log(f"Fatal error: {e}", 'ERROR')
            if not self.dry_run and self.conn:
                self.conn.rollback()
                self.log("Transaction rolled back", 'ERROR')
            import traceback
            traceback.print_exc()
            return 1

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='Batch update high-confidence nan names',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute updates (default is dry-run)'
    )

    args = parser.parse_args()

    updater = BatchNameUpdater(dry_run=not args.execute)
    return updater.run()


if __name__ == '__main__':
    sys.exit(main())
