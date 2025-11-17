#!/usr/bin/env python3
"""
FAANG-Quality PayPal Email Migration

Migrates different PayPal emails to contact_emails table.
Handles contacts where paypal_email differs from primary email.

FEATURES:
- Dry-run mode (default)
- Atomic transaction with rollback
- Before/after verification
- Email validation and deduplication
- Detailed logging with timestamps
- Idempotent (safe to re-run)

USAGE:
    # Dry-run (preview)
    python3 scripts/migrate_paypal_emails.py

    # Execute migration
    python3 scripts/migrate_paypal_emails.py --execute

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
Phase: 2.2 - Contact Data Enhancement
"""

import psycopg2
import sys
import re
from datetime import datetime
from typing import Optional
import argparse
from db_config import get_database_url

DATABASE_URL = get_database_url()

class PayPalEmailMigrator:
    """FAANG-quality PayPal email migration to contact_emails table."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'migrated': 0,
            'already_exists': 0,
            'invalid_email': 0,
            'errors': 0,
            'verified': 0
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
                self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
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

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email or '@' not in email:
            return False

        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    def clean_email(self, email: str) -> str:
        """Clean email by removing notes/comments in parentheses."""
        if not email:
            return email

        # Remove parenthetical notes
        email = re.sub(r'\s*\([^)]*\)', '', email)
        return email.strip().lower()

    def email_exists_in_table(self, contact_id: str, email: str) -> bool:
        """Check if email already exists in contact_emails table."""
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM contact_emails
            WHERE contact_id = %s
              AND LOWER(email) = LOWER(%s)
        """, (contact_id, email))

        return self.cursor.fetchone()[0] > 0

    def get_contacts_with_different_paypal_emails(self):
        """Get contacts where paypal_email differs from primary email."""
        self.cursor.execute("""
            SELECT
                id,
                email,
                paypal_email
            FROM contacts
            WHERE deleted_at IS NULL
              AND paypal_email IS NOT NULL
              AND paypal_email != ''
              AND paypal_email != email
            ORDER BY email
        """)

        return self.cursor.fetchall()

    def print_before_state(self, contacts):
        """Display current state before migration."""
        print("\n" + "=" * 80)
        print("BEFORE MIGRATION - CURRENT STATE")
        print("=" * 80)
        print(f"\nFound {len(contacts)} contacts with different PayPal emails\n")

        print("Contacts to migrate:")
        for row in contacts:
            contact_id, primary_email, paypal_email = row
            print(f"  {primary_email[:40]:40} → PayPal: {paypal_email}")
        print()

    def migrate_emails(self, contacts):
        """Migrate PayPal emails to contact_emails table."""
        self.log(f"\nProcessing {len(contacts)} PayPal emails...")

        for row in contacts:
            contact_id, primary_email, paypal_email = row

            # Clean email
            cleaned_email = self.clean_email(paypal_email)

            # Validate
            if not self.validate_email(cleaned_email):
                self.log(f"  ⚠ {primary_email}: Invalid PayPal email '{paypal_email}'", 'WARN')
                self.stats['invalid_email'] += 1
                continue

            # Check if already exists
            if self.email_exists_in_table(contact_id, cleaned_email):
                self.log(f"  ⚠ {primary_email}: PayPal email already in table")
                self.stats['already_exists'] += 1
                continue

            # Also check if it matches primary
            if cleaned_email.lower() == primary_email.lower():
                self.log(f"  ⚠ {primary_email}: PayPal email same as primary (skipping)")
                self.stats['already_exists'] += 1
                continue

            # Insert
            try:
                if not self.dry_run:
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
                            %s, %s, 'paypal', false, false, NOW(), NOW()
                        )
                    """, (contact_id, cleaned_email))

                    self.stats['migrated'] += 1
                    self.log(f"  ✓ {primary_email}: Migrated PayPal email '{cleaned_email}'")
                else:
                    self.stats['migrated'] += 1
                    self.log(f"  Would migrate: {primary_email} → {cleaned_email}")

            except Exception as e:
                self.log(f"  Failed to migrate {primary_email}: {e}", 'ERROR')
                self.stats['errors'] += 1

    def verify_after(self):
        """Verify migration was successful."""
        if self.dry_run:
            return

        self.log("\nVerifying migration...")

        # Check remaining
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND paypal_email IS NOT NULL
              AND paypal_email != ''
              AND paypal_email != email
              AND NOT EXISTS (
                  SELECT 1 FROM contact_emails
                  WHERE contact_emails.contact_id = contacts.id
                    AND LOWER(contact_emails.email) = LOWER(contacts.paypal_email)
              )
        """)

        remaining = self.cursor.fetchone()[0]

        print("\n" + "=" * 80)
        print("AFTER MIGRATION - VERIFICATION")
        print("=" * 80)
        print(f"Contacts still needing migration: {remaining}")

        # Show migrated emails
        self.cursor.execute("""
            SELECT c.email, ce.email as paypal_email
            FROM contact_emails ce
            JOIN contacts c ON c.id = ce.contact_id
            WHERE ce.source = 'paypal'
            ORDER BY ce.created_at DESC
            LIMIT 10
        """)

        print("\nMigrated PayPal emails (sample):")
        for row in self.cursor.fetchall():
            print(f"  ✓ {row[0]} → PayPal: {row[1]}")
            self.stats['verified'] += 1
        print()

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "=" * 80)
        print("PAYPAL EMAIL MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Emails migrated:           {self.stats['migrated']}")
        print(f"Already existed:           {self.stats['already_exists']}")
        print(f"Invalid emails:            {self.stats['invalid_email']}")
        print(f"Errors:                    {self.stats['errors']}")
        if not self.dry_run:
            print(f"Verified successful:       {self.stats['verified']}")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠ DRY RUN MODE - No changes were made")
            print("Run with --execute to apply changes")
        else:
            if self.stats['errors'] == 0:
                print("\n✅ PayPal email migration completed successfully!")
            else:
                print(f"\n⚠ Completed with {self.stats['errors']} errors")

    def run(self):
        """Main execution."""
        try:
            self.connect()

            if self.dry_run:
                print("\n" + "=" * 80)
                print("DRY RUN MODE - Preview Changes")
                print("=" * 80)

            # Get contacts with different PayPal emails
            contacts = self.get_contacts_with_different_paypal_emails()

            if not contacts:
                self.log("No PayPal emails need migration - all done!", 'SUCCESS')
                return 0

            # Show before state
            self.print_before_state(contacts)

            # Migrate emails
            self.migrate_emails(contacts)

            # Commit transaction
            if not self.dry_run:
                if self.stats['errors'] == 0:
                    self.conn.commit()
                    self.log("Transaction committed successfully", 'SUCCESS')
                else:
                    self.conn.rollback()
                    self.log("Transaction rolled back due to errors", 'ERROR')
                    return 1

            # Verify
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
        description='Migrate different PayPal emails to contact_emails table',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (default is dry-run)'
    )

    args = parser.parse_args()

    migrator = PayPalEmailMigrator(dry_run=not args.execute)
    return migrator.run()


if __name__ == '__main__':
    sys.exit(main())
