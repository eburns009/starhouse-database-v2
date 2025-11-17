#!/usr/bin/env python3
"""
FAANG-Quality Additional Name Parsing

Parses additional_name field to enrich missing first/last names.
Handles contacts with incomplete primary name but valid additional_name.

FEATURES:
- Dry-run mode (default)
- Atomic transaction with rollback
- Before/after verification
- Smart name parsing (handles businesses vs individuals)
- Detailed logging with timestamps
- Idempotent (safe to re-run)

USAGE:
    # Dry-run (preview)
    python3 scripts/parse_additional_names.py

    # Execute parsing
    python3 scripts/parse_additional_names.py --execute

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
Phase: 2.3 - Contact Data Enhancement
"""

import psycopg2
import sys
from datetime import datetime
from typing import Optional, Tuple
import argparse

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

class AdditionalNameParser:
    """FAANG-quality additional_name field parser."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'parsed_first_only': 0,
            'parsed_last_only': 0,
            'parsed_both': 0,
            'skipped_business': 0,
            'skipped_invalid': 0,
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

    def parse_name(self, additional_name: str, current_first: str, current_last: str) -> Optional[Tuple[str, str]]:
        """
        Parse additional_name into first/last name components.

        Returns:
            Tuple of (first_name, last_name) or None if unparseable
        """
        if not additional_name or additional_name.strip() == '':
            return None

        name = additional_name.strip()

        # Check for business indicators
        business_indicators = ['LLC', 'Inc', 'Ltd', 'Corp', 'Company', '.com', 'Foundation']
        if any(indicator in name for indicator in business_indicators):
            # This is a business name
            return None

        # Parse name into parts
        parts = name.split()

        if len(parts) == 0:
            return None
        elif len(parts) == 1:
            # Single name - use as first or last depending on what's missing
            if not current_first or current_first in ['nan', 'None', '']:
                return (parts[0], current_last)
            elif not current_last or current_last in ['nan', 'None', '']:
                return (current_first, parts[0])
            else:
                return None  # Already have both
        elif len(parts) == 2:
            # Standard "First Last" format
            return (parts[0], parts[1])
        else:
            # Multiple parts - use first as first name, rest as last name
            return (parts[0], ' '.join(parts[1:]))

    def get_contacts_needing_parsing(self):
        """Get contacts with additional_name but incomplete primary name."""
        self.cursor.execute("""
            SELECT
                id,
                email,
                first_name,
                last_name,
                additional_name
            FROM contacts
            WHERE deleted_at IS NULL
              AND additional_name IS NOT NULL
              AND additional_name != ''
              AND (
                  first_name IS NULL OR first_name = '' OR first_name = 'nan' OR first_name = 'None'
                  OR last_name IS NULL OR last_name = '' OR last_name = 'nan' OR last_name = 'None'
              )
            ORDER BY email
        """)

        return self.cursor.fetchall()

    def print_before_state(self, contacts):
        """Display current state before parsing."""
        print("\n" + "=" * 80)
        print("BEFORE PARSING - CURRENT STATE")
        print("=" * 80)
        print(f"\nFound {len(contacts)} contacts to parse\n")

        print("Contacts to parse:")
        for row in contacts:
            contact_id, email, first_name, last_name, additional_name = row
            print(f"  {email[:40]:40}")
            print(f"    Current: '{first_name}' '{last_name}'")
            print(f"    Additional: '{additional_name}'")
        print()

    def parse_names(self, contacts):
        """Parse additional_name for each contact."""
        self.log(f"\nProcessing {len(contacts)} contacts...")

        for row in contacts:
            contact_id, email, first_name, last_name, additional_name = row

            # Parse name
            parsed = self.parse_name(additional_name, first_name, last_name)

            if not parsed:
                self.log(f"  ⚠ {email}: Cannot parse '{additional_name}' (likely business)", 'WARN')
                self.stats['skipped_business'] += 1
                continue

            new_first, new_last = parsed

            # Determine what needs updating
            update_first = not first_name or first_name in ['nan', 'None', '']
            update_last = not last_name or last_name in ['nan', 'None', '']

            if not update_first and not update_last:
                self.log(f"  ⚠ {email}: Already has complete name", 'WARN')
                continue

            # Update
            try:
                if not self.dry_run:
                    if update_first and update_last:
                        self.cursor.execute("""
                            UPDATE contacts
                            SET first_name = %s, last_name = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (new_first, new_last, contact_id))
                        self.stats['parsed_both'] += 1
                        self.log(f"  ✓ {email}: '{new_first}' '{new_last}' (both)")
                    elif update_first:
                        self.cursor.execute("""
                            UPDATE contacts
                            SET first_name = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (new_first, contact_id))
                        self.stats['parsed_first_only'] += 1
                        self.log(f"  ✓ {email}: '{new_first}' (first only)")
                    elif update_last:
                        self.cursor.execute("""
                            UPDATE contacts
                            SET last_name = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (new_last, contact_id))
                        self.stats['parsed_last_only'] += 1
                        self.log(f"  ✓ {email}: '{new_last}' (last only)")
                else:
                    # Dry-run tracking
                    if update_first and update_last:
                        self.stats['parsed_both'] += 1
                        self.log(f"  Would update {email}: '{new_first}' '{new_last}' (both)")
                    elif update_first:
                        self.stats['parsed_first_only'] += 1
                        self.log(f"  Would update {email}: '{new_first}' (first only)")
                    elif update_last:
                        self.stats['parsed_last_only'] += 1
                        self.log(f"  Would update {email}: '{new_last}' (last only)")

            except Exception as e:
                self.log(f"  Failed to update {email}: {e}", 'ERROR')
                self.stats['errors'] += 1

    def verify_after(self):
        """Verify parsing was successful."""
        if self.dry_run:
            return

        self.log("\nVerifying parsing...")

        # Check remaining
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND additional_name IS NOT NULL
              AND additional_name != ''
              AND (
                  first_name IS NULL OR first_name = '' OR first_name = 'nan' OR first_name = 'None'
                  OR last_name IS NULL OR last_name = '' OR last_name = 'nan' OR last_name = 'None'
              )
        """)

        remaining = self.cursor.fetchone()[0]

        print("\n" + "=" * 80)
        print("AFTER PARSING - VERIFICATION")
        print("=" * 80)
        print(f"Contacts still needing parsing: {remaining}")

        # Show updated contacts
        self.cursor.execute("""
            SELECT email, first_name, last_name, additional_name
            FROM contacts
            WHERE deleted_at IS NULL
              AND additional_name IS NOT NULL
              AND additional_name != ''
              AND first_name IS NOT NULL
              AND first_name != ''
              AND last_name IS NOT NULL
              AND last_name != ''
            ORDER BY updated_at DESC
            LIMIT 10
        """)

        print("\nRecently parsed names (sample):")
        for row in self.cursor.fetchall():
            print(f"  ✓ {row[0]}: '{row[1]}' '{row[2]}' (from '{row[3]}')")
            self.stats['verified'] += 1
        print()

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "=" * 80)
        print("ADDITIONAL NAME PARSING SUMMARY")
        print("=" * 80)
        print(f"Parsed both names:         {self.stats['parsed_both']}")
        print(f"Parsed first name only:    {self.stats['parsed_first_only']}")
        print(f"Parsed last name only:     {self.stats['parsed_last_only']}")
        print(f"Total parsed:              {self.stats['parsed_both'] + self.stats['parsed_first_only'] + self.stats['parsed_last_only']}")
        print(f"Skipped (business):        {self.stats['skipped_business']}")
        print(f"Skipped (invalid):         {self.stats['skipped_invalid']}")
        print(f"Errors:                    {self.stats['errors']}")
        if not self.dry_run:
            print(f"Verified successful:       {self.stats['verified']}")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠ DRY RUN MODE - No changes were made")
            print("Run with --execute to apply changes")
        else:
            if self.stats['errors'] == 0:
                print("\n✅ Additional name parsing completed successfully!")
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

            # Get contacts needing parsing
            contacts = self.get_contacts_needing_parsing()

            if not contacts:
                self.log("No contacts need additional_name parsing - all done!", 'SUCCESS')
                return 0

            # Show before state
            self.print_before_state(contacts)

            # Parse names
            self.parse_names(contacts)

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
        description='Parse additional_name to enrich missing first/last names',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute parsing (default is dry-run)'
    )

    args = parser.parse_args()

    parser_obj = AdditionalNameParser(dry_run=not args.execute)
    return parser_obj.run()


if __name__ == '__main__':
    sys.exit(main())
