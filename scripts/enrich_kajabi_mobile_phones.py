#!/usr/bin/env python3
"""
Import Kajabi mobile phone numbers to enrich contacts missing phone data.

This script extracts the "Mobile Phone Number (mobile_phone_number)" field
from the Kajabi contacts CSV and enriches contacts that don't have a phone number.

FAANG Quality Standards:
- Dry-run mode by default
- Never overwrites existing phone numbers
- Tracks data provenance (phone_source = 'kajabi_mobile')
- Idempotent operations
- Comprehensive logging

Usage:
    python3 scripts/enrich_kajabi_mobile_phones.py --dry-run
    python3 scripts/enrich_kajabi_mobile_phones.py --execute
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, level: str = 'INFO') -> None:
    """Log message with timestamp and color."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    colors = {
        'INFO': Colors.BLUE,
        'SUCCESS': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'HEADER': Colors.HEADER,
    }
    color = colors.get(level, '')
    print(f"{color}[{timestamp}] {level}: {message}{Colors.ENDC}")

def load_mobile_phones_from_csv() -> Dict[str, str]:
    """
    Load mobile phone numbers from Kajabi CSV.

    Returns: Dict mapping email -> mobile_phone
    """
    csv_path = 'kajabi 3 files review/kajabi contacts.csv'
    if not os.path.exists(csv_path):
        log(f"CSV file not found: {csv_path}", 'ERROR')
        sys.exit(1)

    mobile_phones = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            mobile = row.get('Mobile Phone Number (mobile_phone_number)', '').strip()

            if email and mobile:
                mobile_phones[email] = mobile

    log(f"Loaded {len(mobile_phones)} mobile phone numbers from CSV", 'SUCCESS')
    return mobile_phones

def get_contacts_without_phones(cursor) -> List[Dict]:
    """Get all Kajabi contacts that don't have a phone number."""
    cursor.execute("""
        SELECT
            id,
            email,
            first_name,
            last_name,
            phone,
            kajabi_id
        FROM contacts
        WHERE source_system = 'kajabi'
          AND (phone IS NULL OR phone = '')
          AND deleted_at IS NULL
        ORDER BY email
    """)

    contacts = cursor.fetchall()
    log(f"Found {len(contacts)} Kajabi contacts without phone numbers", 'INFO')
    return contacts

def enrich_contacts(mobile_phones: Dict[str, str], dry_run: bool) -> Dict:
    """Enrich contacts with mobile phone numbers."""
    log(f"\n{'='*80}", 'HEADER')
    log(f"ENRICHMENT MODE: {'DRY-RUN' if dry_run else 'EXECUTE'}", 'HEADER')
    log(f"{'='*80}\n", 'HEADER')

    # Connect to database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        log("DATABASE_URL not set", 'ERROR')
        sys.exit(1)

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    results = {
        'total_missing_phones': 0,
        'mobile_phones_available': len(mobile_phones),
        'enriched': 0,
        'no_mobile_available': 0,
        'details': []
    }

    try:
        # Get contacts without phones
        contacts = get_contacts_without_phones(cursor)
        results['total_missing_phones'] = len(contacts)

        if not contacts:
            log("No contacts need phone enrichment", 'INFO')
            return results

        log(f"\nProcessing {len(contacts)} contacts...\n", 'INFO')

        for contact in contacts:
            email = contact['email'].lower()

            # Check if mobile phone available
            if email not in mobile_phones:
                results['no_mobile_available'] += 1
                continue

            mobile_phone = mobile_phones[email]

            # Perform enrichment
            if not dry_run:
                cursor.execute("""
                    UPDATE contacts
                    SET
                        phone = %s,
                        phone_source = 'kajabi_mobile',
                        updated_at = NOW()
                    WHERE id = %s
                      AND (phone IS NULL OR phone = '')
                      AND deleted_at IS NULL
                """, (mobile_phone, contact['id']))

                if cursor.rowcount == 0:
                    log(f"⊘ Race condition for {email}", 'WARNING')
                    continue

            results['enriched'] += 1
            results['details'].append({
                'email': email,
                'name': f"{contact['first_name']} {contact['last_name']}",
                'mobile_phone': mobile_phone,
                'kajabi_id': contact['kajabi_id']
            })

            if results['enriched'] % 100 == 0:
                log(f"✓ Enriched {results['enriched']} contacts...", 'INFO')

        # Commit changes
        if not dry_run:
            conn.commit()
            log(f"\n✓ Changes committed to database", 'SUCCESS')
        else:
            conn.rollback()
            log(f"\n⊘ Dry-run complete - no changes made", 'INFO')

    except Exception as e:
        conn.rollback()
        log(f"Error during enrichment: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    return results

def print_summary(results: Dict, dry_run: bool) -> None:
    """Print enrichment summary."""
    log(f"\n{'='*80}", 'HEADER')
    log(f"MOBILE PHONE ENRICHMENT SUMMARY ({'DRY-RUN' if dry_run else 'EXECUTED'})", 'HEADER')
    log(f"{'='*80}", 'HEADER')

    log(f"Total Kajabi contacts without phones: {results['total_missing_phones']}", 'INFO')
    log(f"Mobile phones available in CSV: {results['mobile_phones_available']}", 'INFO')
    log(f"✓ Contacts enriched: {results['enriched']}", 'SUCCESS')
    log(f"⊘ No mobile phone available: {results['no_mobile_available']}", 'WARNING')

    if results['enriched'] > 0:
        improvement_pct = (results['enriched'] / results['total_missing_phones'] * 100) if results['total_missing_phones'] > 0 else 0
        log(f"\n📈 Coverage improvement: {improvement_pct:.1f}%", 'SUCCESS')

        # Show sample enrichments
        log(f"\n{'='*80}", 'HEADER')
        log("SAMPLE ENRICHMENTS (first 10):", 'HEADER')
        log(f"{'='*80}", 'HEADER')

        for detail in results['details'][:10]:
            log(f"\n✓ {detail['name']} ({detail['email']})", 'SUCCESS')
            log(f"  Mobile: {detail['mobile_phone']}", 'INFO')
            log(f"  Kajabi ID: {detail['kajabi_id']}", 'INFO')

        if len(results['details']) > 10:
            log(f"\n... and {len(results['details']) - 10} more", 'INFO')

    log(f"\n{'='*80}\n", 'HEADER')

def main():
    """Main execution function."""
    # Parse arguments
    dry_run = True
    if len(sys.argv) > 1:
        if sys.argv[1] == '--execute':
            dry_run = False
        elif sys.argv[1] == '--dry-run':
            dry_run = True
        else:
            log("Usage: python3 scripts/enrich_kajabi_mobile_phones.py [--dry-run|--execute]", 'ERROR')
            sys.exit(1)

    # Load mobile phones from CSV
    mobile_phones = load_mobile_phones_from_csv()

    # Enrich contacts
    results = enrich_contacts(mobile_phones, dry_run)

    # Print summary
    print_summary(results, dry_run)

    # Save results
    if results['enriched'] > 0:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode = 'dryrun' if dry_run else 'execute'
        output_file = f"kajabi_mobile_enrichment_{mode}_{timestamp}.json"

        import json
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'mode': mode,
                'results': results
            }, f, indent=2, default=str)

        log(f"Report saved to: {output_file}", 'SUCCESS')

    if dry_run:
        log("\n⚠️  Run with --execute to apply changes", 'WARNING')

if __name__ == '__main__':
    main()
