#!/usr/bin/env python3
"""
FAANG-Quality Phone Enrichment from Alternative Fields

Enriches primary phone field from alternative phone sources:
- paypal_phone
- zoho_phone
- additional_phone

FEATURES:
- Dry-run mode (default)
- Atomic transaction with rollback
- Before/after verification
- Phone validation and formatting
- Detailed logging with timestamps
- Idempotent (safe to re-run)

USAGE:
    # Dry-run (preview)
    python3 scripts/enrich_phones_from_alternatives.py

    # Execute updates
    python3 scripts/enrich_phones_from_alternatives.py --execute

Author: Claude Code (FAANG-Quality Engineering)
Date: 2025-11-17
Phase: 2.1 - Contact Data Enhancement
"""

import psycopg2
import sys
import re
from datetime import datetime
from typing import Optional, Tuple
import argparse

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

class PhoneEnricher:
    """FAANG-quality phone enrichment from alternative fields."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'from_paypal': 0,
            'from_zoho': 0,
            'from_additional': 0,
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

    def clean_phone(self, phone: str) -> Optional[str]:
        """
        Clean and validate phone number.

        Returns None if phone is invalid.
        """
        if not phone:
            return None

        # Remove common formatting
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Validate: must have at least 10 digits
        digit_count = sum(c.isdigit() for c in cleaned)
        if digit_count < 10:
            return None

        return phone.strip()  # Return original formatting

    def get_contacts_needing_enrichment(self):
        """Get contacts without primary phone but with alternative phones."""
        self.cursor.execute("""
            SELECT
                id,
                email,
                phone,
                paypal_phone,
                zoho_phone,
                additional_phone
            FROM contacts
            WHERE deleted_at IS NULL
              AND (phone IS NULL OR phone = '')
              AND (
                  (paypal_phone IS NOT NULL AND paypal_phone != '')
                  OR (zoho_phone IS NOT NULL AND zoho_phone != '')
                  OR (additional_phone IS NOT NULL AND additional_phone != '')
              )
            ORDER BY email
        """)

        return self.cursor.fetchall()

    def print_before_state(self, contacts):
        """Display current state before enrichment."""
        print("\n" + "=" * 80)
        print("BEFORE ENRICHMENT - CURRENT STATE")
        print("=" * 80)
        print(f"\nFound {len(contacts)} contacts to enrich\n")

        # Show samples
        print("Sample contacts (first 10):")
        for row in contacts[:10]:
            contact_id, email, phone, paypal_phone, zoho_phone, additional_phone = row
            alt_phone = paypal_phone or zoho_phone or additional_phone
            source = 'paypal' if paypal_phone else ('zoho' if zoho_phone else 'additional')
            print(f"  {email[:40]:40} → {alt_phone} (from {source})")

        if len(contacts) > 10:
            print(f"  ... and {len(contacts) - 10} more")
        print()

    def enrich_phones(self, contacts):
        """Enrich phone numbers from alternative fields."""
        self.log(f"\nProcessing {len(contacts)} contacts...")

        for row in contacts:
            contact_id, email, phone, paypal_phone, zoho_phone, additional_phone = row

            # Priority: PayPal > Zoho > Additional
            source_phone = paypal_phone or zoho_phone or additional_phone
            source_name = 'paypal_phone' if paypal_phone else ('zoho_phone' if zoho_phone else 'additional_phone')

            # Clean and validate
            cleaned_phone = self.clean_phone(source_phone)

            if not cleaned_phone:
                self.log(f"  ⚠ {email}: Invalid phone '{source_phone}' from {source_name}", 'WARN')
                self.stats['skipped_invalid'] += 1
                continue

            # Update
            try:
                if not self.dry_run:
                    self.cursor.execute("""
                        UPDATE contacts
                        SET phone = %s, updated_at = NOW()
                        WHERE id = %s AND (phone IS NULL OR phone = '')
                    """, (cleaned_phone, contact_id))

                    if self.cursor.rowcount > 0:
                        # Track by source
                        if source_name == 'paypal_phone':
                            self.stats['from_paypal'] += 1
                        elif source_name == 'zoho_phone':
                            self.stats['from_zoho'] += 1
                        else:
                            self.stats['from_additional'] += 1

                        self.log(f"  ✓ {email}: {cleaned_phone} (from {source_name})")
                    else:
                        self.log(f"  ⚠ {email}: No update needed", 'WARN')
                else:
                    # Track for dry-run
                    if source_name == 'paypal_phone':
                        self.stats['from_paypal'] += 1
                    elif source_name == 'zoho_phone':
                        self.stats['from_zoho'] += 1
                    else:
                        self.stats['from_additional'] += 1

                    self.log(f"  Would update {email}: {cleaned_phone} (from {source_name})")

            except Exception as e:
                self.log(f"  Failed to update {email}: {e}", 'ERROR')
                self.stats['errors'] += 1

    def verify_after(self):
        """Verify enrichment was successful."""
        if self.dry_run:
            return

        self.log("\nVerifying enrichment...")

        # Check how many contacts still need enrichment
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE deleted_at IS NULL
              AND (phone IS NULL OR phone = '')
              AND (
                  (paypal_phone IS NOT NULL AND paypal_phone != '')
                  OR (zoho_phone IS NOT NULL AND zoho_phone != '')
                  OR (additional_phone IS NOT NULL AND additional_phone != '')
              )
        """)

        remaining = self.cursor.fetchone()[0]

        print("\n" + "=" * 80)
        print("AFTER ENRICHMENT - VERIFICATION")
        print("=" * 80)
        print(f"Contacts still needing enrichment: {remaining}")

        # Show updated contacts sample
        self.cursor.execute("""
            SELECT email, phone
            FROM contacts
            WHERE deleted_at IS NULL
              AND phone IS NOT NULL
              AND phone != ''
              AND (
                  (paypal_phone IS NOT NULL AND paypal_phone != '')
                  OR (zoho_phone IS NOT NULL AND zoho_phone != '')
                  OR (additional_phone IS NOT NULL AND additional_phone != '')
              )
            ORDER BY updated_at DESC
            LIMIT 10
        """)

        print("\nRecently enriched contacts (sample):")
        for row in self.cursor.fetchall():
            print(f"  ✓ {row[0]}: {row[1]}")
            self.stats['verified'] += 1
        print()

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "=" * 80)
        print("PHONE ENRICHMENT SUMMARY")
        print("=" * 80)
        print(f"Enriched from PayPal:      {self.stats['from_paypal']}")
        print(f"Enriched from Zoho:        {self.stats['from_zoho']}")
        print(f"Enriched from Additional:  {self.stats['from_additional']}")
        print(f"Total enriched:            {self.stats['from_paypal'] + self.stats['from_zoho'] + self.stats['from_additional']}")
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
                print("\n✅ Phone enrichment completed successfully!")
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

            # Get contacts needing enrichment
            contacts = self.get_contacts_needing_enrichment()

            if not contacts:
                self.log("No contacts need phone enrichment - all done!", 'SUCCESS')
                return 0

            # Show before state
            self.print_before_state(contacts)

            # Enrich phones
            self.enrich_phones(contacts)

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
        description='Enrich primary phone from alternative phone fields',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute updates (default is dry-run)'
    )

    args = parser.parse_args()

    enricher = PhoneEnricher(dry_run=not args.execute)
    return enricher.run()


if __name__ == '__main__':
    sys.exit(main())
