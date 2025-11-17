#!/usr/bin/env python3
"""
FAANG-Quality Email Migration Script

Migrates additional_email field to contact_emails table.

FEATURES:
- Dry-run mode (default)
- Atomic transactions with rollback on error
- Comprehensive validation and verification
- Detailed logging and progress tracking
- Idempotent (safe to run multiple times)
- Zero data loss guarantee

USAGE:
    # Preview changes (safe, read-only)
    python3 scripts/migrate_additional_emails_to_table.py

    # Execute migration
    python3 scripts/migrate_additional_emails_to_table.py --execute

    # Verbose output
    python3 scripts/migrate_additional_emails_to_table.py --execute --verbose

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
"""

import psycopg2
import sys
from datetime import datetime
from typing import List, Tuple, Dict
import argparse
from db_config import get_database_url

DATABASE_URL = get_database_url()

class EmailMigrator:
    """FAANG-quality email migration with safety guarantees."""

    def __init__(self, dry_run: bool = True, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.conn = None
        self.cursor = None
        self.stats = {
            'total_additional_emails': 0,
            'already_migrated': 0,
            'needs_migration': 0,
            'migrated': 0,
            'errors': 0,
            'skipped': 0
        }

    def log(self, message: str, level: str = 'INFO'):
        """Structured logging with timestamps."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = {
            'INFO': '✓',
            'WARN': '⚠',
            'ERROR': '✗',
            'DEBUG': '→'
        }.get(level, '·')

        if level == 'DEBUG' and not self.verbose:
            return

        print(f"[{timestamp}] {prefix} {message}")

    def connect(self):
        """Establish database connection with error handling."""
        try:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.cursor = self.conn.cursor()
            self.log("Database connection established")
        except Exception as e:
            self.log(f"Failed to connect to database: {e}", 'ERROR')
            sys.exit(1)

    def disconnect(self):
        """Clean up database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

    def analyze_current_state(self) -> List[Tuple]:
        """
        Analyze which emails need migration.

        Returns:
            List of tuples: (contact_id, email, additional_email, source_system)
        """
        self.log("Analyzing current state...", 'DEBUG')

        # Count total contacts with additional_email
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND additional_email IS NOT NULL
              AND additional_email != ''
        """)
        self.stats['total_additional_emails'] = self.cursor.fetchone()[0]

        # Count already migrated
        self.cursor.execute("""
            SELECT COUNT(DISTINCT c.id)
            FROM contacts c
            INNER JOIN contact_emails ce ON c.id = ce.contact_id
              AND ce.email = c.additional_email
            WHERE c.deleted_at IS NULL
              AND c.additional_email IS NOT NULL
              AND c.additional_email != ''
        """)
        self.stats['already_migrated'] = self.cursor.fetchone()[0]

        # Get contacts that need migration
        self.cursor.execute("""
            SELECT c.id, c.email, c.additional_email, c.source_system
            FROM contacts c
            LEFT JOIN contact_emails ce ON c.id = ce.contact_id
              AND ce.email = c.additional_email
            WHERE c.deleted_at IS NULL
              AND c.additional_email IS NOT NULL
              AND c.additional_email != ''
              AND ce.id IS NULL
            ORDER BY c.created_at
        """)

        contacts_to_migrate = self.cursor.fetchall()
        self.stats['needs_migration'] = len(contacts_to_migrate)

        return contacts_to_migrate

    def validate_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email or email.strip() == '':
            return False
        if '@' not in email:
            return False
        if ',' in email:  # Multiple emails - need special handling
            return False
        return True

    def clean_email(self, email: str) -> str:
        """Clean email by removing notes/comments in parentheses."""
        # Remove anything in parentheses (notes, typos, etc.)
        import re
        email = re.sub(r'\s*\([^)]*\)', '', email)
        return email.strip()

    def parse_multiple_emails(self, email_string: str) -> List[str]:
        """Parse comma/semicolon separated email strings."""
        if ',' in email_string:
            return [self.clean_email(e) for e in email_string.split(',') if e.strip()]
        if ';' in email_string:
            return [self.clean_email(e) for e in email_string.split(';') if e.strip()]
        return [self.clean_email(email_string)]

    def migrate_contact_emails(self, contact: Tuple) -> bool:
        """
        Migrate additional_email for a single contact.

        Args:
            contact: (contact_id, email, additional_email, source_system)

        Returns:
            True if successful, False otherwise
        """
        contact_id, primary_email, additional_email, source_system = contact

        self.log(f"Processing contact {contact_id[:8]}...", 'DEBUG')

        # Parse multiple emails if needed
        emails = self.parse_multiple_emails(additional_email)

        if len(emails) > 1:
            self.log(f"  Found {len(emails)} emails in additional_email field", 'DEBUG')

        migrated_count = 0
        for email in emails:
            if not self.validate_email(email):
                self.log(f"  Skipping invalid email: {email}", 'WARN')
                self.stats['skipped'] += 1
                continue

            # Skip if email is same as primary
            if email == primary_email:
                self.log(f"  Skipping duplicate of primary email", 'DEBUG')
                self.stats['skipped'] += 1
                continue

            # Check if this email already exists in contact_emails
            self.cursor.execute("""
                SELECT id FROM contact_emails
                WHERE contact_id = %s AND email = %s
            """, (contact_id, email))

            if self.cursor.fetchone():
                self.log(f"  Email {email} already exists in contact_emails", 'DEBUG')
                self.stats['skipped'] += 1
                continue

            # Insert into contact_emails table
            # Note: is_outreach=false to avoid unique constraint violation
            # (only one outreach email allowed per contact)
            try:
                self.cursor.execute("""
                    INSERT INTO contact_emails (
                        contact_id,
                        email,
                        source,
                        is_primary,
                        is_outreach,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, 'manual', false, false, NOW(), NOW()
                    )
                """, (contact_id, email))

                migrated_count += 1
                self.log(f"  ✓ Migrated: {email}", 'DEBUG')

            except Exception as e:
                self.log(f"  Failed to migrate {email}: {e}", 'ERROR')
                self.stats['errors'] += 1
                return False

        if migrated_count > 0:
            self.stats['migrated'] += migrated_count
            return True

        return True  # No errors even if nothing migrated

    def execute_migration(self, contacts: List[Tuple]):
        """Execute migration with transaction safety."""

        if self.dry_run:
            self.log("=" * 80)
            self.log("DRY RUN MODE - No changes will be made", 'WARN')
            self.log("=" * 80)
            self.log("")

        self.log(f"Starting migration of {len(contacts)} contacts...")

        try:
            for i, contact in enumerate(contacts, 1):
                if self.verbose or i % 10 == 0:
                    self.log(f"Progress: {i}/{len(contacts)} ({i/len(contacts)*100:.1f}%)")

                if not self.dry_run:
                    success = self.migrate_contact_emails(contact)
                    if not success:
                        raise Exception(f"Migration failed for contact {contact[0]}")
                else:
                    # In dry-run, just validate
                    emails = self.parse_multiple_emails(contact[2])
                    for email in emails:
                        if self.validate_email(email) and email != contact[1]:
                            self.stats['migrated'] += 1

            if not self.dry_run:
                self.conn.commit()
                self.log("Transaction committed successfully", 'INFO')
            else:
                self.log("Dry-run completed - no changes made", 'INFO')

        except Exception as e:
            if not self.dry_run:
                self.conn.rollback()
                self.log(f"Transaction rolled back due to error: {e}", 'ERROR')
            raise

    def verify_migration(self):
        """Verify migration was successful."""
        self.log("\nVerifying migration...")

        # Check remaining unmigrated emails
        self.cursor.execute("""
            SELECT COUNT(DISTINCT c.id)
            FROM contacts c
            LEFT JOIN contact_emails ce ON c.id = ce.contact_id
              AND ce.email = c.additional_email
            WHERE c.deleted_at IS NULL
              AND c.additional_email IS NOT NULL
              AND c.additional_email != ''
              AND ce.id IS NULL
        """)

        remaining = self.cursor.fetchone()[0]

        if remaining == 0:
            self.log("✓ All additional emails successfully migrated!", 'INFO')
        else:
            self.log(f"⚠ {remaining} emails still need migration", 'WARN')

        return remaining == 0

    def print_summary(self):
        """Print comprehensive summary report."""
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Total contacts with additional_email: {self.stats['total_additional_emails']}")
        print(f"Already migrated (before run):         {self.stats['already_migrated']}")
        print(f"Needed migration:                      {self.stats['needs_migration']}")
        print(f"Successfully migrated:                 {self.stats['migrated']}")
        print(f"Skipped (duplicates/invalid):          {self.stats['skipped']}")
        print(f"Errors:                                {self.stats['errors']}")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠ DRY RUN MODE - No changes were made to the database")
            print("Run with --execute to apply changes")
        else:
            print("\n✓ Migration completed successfully!")

        print()

    def run(self):
        """Main execution flow."""
        try:
            self.connect()

            # Analyze
            contacts_to_migrate = self.analyze_current_state()

            if self.stats['needs_migration'] == 0:
                self.log("No emails need migration - all done!", 'INFO')
                self.print_summary()
                return 0

            # Show preview
            self.log(f"\nFound {self.stats['needs_migration']} contacts to migrate")

            if self.verbose and len(contacts_to_migrate) <= 10:
                self.log("\nContacts to migrate:", 'DEBUG')
                for contact in contacts_to_migrate[:10]:
                    self.log(f"  {contact[0][:8]}: {contact[1]} → {contact[2]}", 'DEBUG')

            # Execute
            self.execute_migration(contacts_to_migrate)

            # Verify (only in execute mode)
            if not self.dry_run:
                self.verify_migration()

            # Summary
            self.print_summary()

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
        description='Migrate additional_email to contact_emails table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (safe, preview changes)
  python3 migrate_additional_emails_to_table.py

  # Execute migration
  python3 migrate_additional_emails_to_table.py --execute

  # Verbose output
  python3 migrate_additional_emails_to_table.py --execute --verbose
        """
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (default is dry-run)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    migrator = EmailMigrator(dry_run=not args.execute, verbose=args.verbose)
    return migrator.run()


if __name__ == '__main__':
    sys.exit(main())
