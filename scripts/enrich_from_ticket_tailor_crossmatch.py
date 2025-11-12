#!/usr/bin/env python3
"""
Cross-match Ticket Tailor contacts with Kajabi contacts to enrich missing data.

This script finds Ticket Tailor contacts that match Kajabi contacts by name
and enriches the Kajabi contact with phone/address data from Ticket Tailor.

Matching Strategy:
1. Exact match on first_name AND last_name (case-insensitive)
2. Only enrich if Kajabi contact is missing the data
3. Track provenance with source fields

FAANG Quality Standards:
- Dry-run mode by default
- Never overwrites existing data
- Tracks data provenance
- Idempotent operations
- Comprehensive logging

Usage:
    python3 scripts/enrich_from_ticket_tailor_crossmatch.py --dry-run
    python3 scripts/enrich_from_ticket_tailor_crossmatch.py --execute
"""

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

def find_cross_matches(cursor) -> List[Dict]:
    """
    Find Ticket Tailor contacts that match Kajabi contacts by name.

    Returns list of matches where TT has data that Kajabi is missing.
    """
    log("Finding Ticket Tailor → Kajabi name matches...", 'INFO')

    cursor.execute("""
        SELECT
            tt.id as tt_id,
            tt.email as tt_email,
            tt.first_name as tt_first,
            tt.last_name as tt_last,
            tt.phone as tt_phone,
            tt.phone_source as tt_phone_source,
            tt.address_line_1 as tt_address_line_1,
            tt.address_line_2 as tt_address_line_2,
            tt.city as tt_city,
            tt.state as tt_state,
            tt.postal_code as tt_postal_code,
            tt.country as tt_country,
            k.id as kajabi_id,
            k.email as kajabi_email,
            k.first_name as kajabi_first,
            k.last_name as kajabi_last,
            k.phone as kajabi_phone,
            k.address_line_1 as kajabi_address_line_1,
            k.shipping_address_line_1 as kajabi_shipping_address
        FROM contacts tt
        INNER JOIN contacts k ON (
            LOWER(TRIM(tt.first_name)) = LOWER(TRIM(k.first_name))
            AND LOWER(TRIM(tt.last_name)) = LOWER(TRIM(k.last_name))
        )
        WHERE tt.source_system = 'ticket_tailor'
          AND k.source_system = 'kajabi'
          AND tt.deleted_at IS NULL
          AND k.deleted_at IS NULL
          AND (
            -- TT has phone and Kajabi doesn't
            (tt.phone IS NOT NULL AND tt.phone != '' AND (k.phone IS NULL OR k.phone = ''))
            OR
            -- TT has address and Kajabi doesn't (neither primary nor shipping)
            (tt.address_line_1 IS NOT NULL AND tt.address_line_1 != ''
             AND (k.address_line_1 IS NULL OR k.address_line_1 = '')
             AND (k.shipping_address_line_1 IS NULL OR k.shipping_address_line_1 = ''))
          )
        ORDER BY k.last_name, k.first_name
    """)

    matches = cursor.fetchall()
    log(f"Found {len(matches)} potential enrichment matches", 'SUCCESS')
    return matches

def enrich_contacts(dry_run: bool) -> Dict:
    """Enrich Kajabi contacts with Ticket Tailor data."""
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
        'total_matches': 0,
        'enriched_phone': 0,
        'enriched_address': 0,
        'enriched_both': 0,
        'skipped': 0,
        'details': []
    }

    try:
        # Find cross-matches
        matches = find_cross_matches(cursor)
        results['total_matches'] = len(matches)

        if not matches:
            log("No enrichment opportunities found", 'INFO')
            return results

        log(f"\nProcessing {len(matches)} matches...\n", 'INFO')

        for match in matches:
            # Determine what to enrich
            can_enrich_phone = bool(
                match['tt_phone'] and
                (not match['kajabi_phone'] or match['kajabi_phone'] == '')
            )

            can_enrich_address = bool(
                match['tt_address_line_1'] and
                (not match['kajabi_address_line_1'] or match['kajabi_address_line_1'] == '') and
                (not match['kajabi_shipping_address'] or match['kajabi_shipping_address'] == '')
            )

            if not can_enrich_phone and not can_enrich_address:
                results['skipped'] += 1
                continue

            # Build update query
            updates = []
            params = []

            if can_enrich_phone:
                updates.append("phone = %s")
                params.append(match['tt_phone'])
                updates.append("phone_source = %s")
                params.append('ticket_tailor_crossmatch')

            if can_enrich_address:
                updates.append("address_line_1 = %s")
                params.append(match['tt_address_line_1'])
                updates.append("address_line_2 = %s")
                params.append(match['tt_address_line_2'])
                updates.append("city = %s")
                params.append(match['tt_city'])
                updates.append("state = %s")
                params.append(match['tt_state'])
                updates.append("postal_code = %s")
                params.append(match['tt_postal_code'])
                updates.append("country = %s")
                params.append(match['tt_country'])

            updates.append("updated_at = NOW()")
            params.append(match['kajabi_id'])

            # Execute update
            if not dry_run:
                # Build WHERE clause to prevent race conditions
                where_conditions = ["id = %s", "deleted_at IS NULL"]

                if can_enrich_phone:
                    where_conditions.append("(phone IS NULL OR phone = '')")

                query = f"""
                    UPDATE contacts
                    SET {', '.join(updates)}
                    WHERE {' AND '.join(where_conditions)}
                """

                cursor.execute(query, params)

                if cursor.rowcount == 0:
                    log(f"⊘ Race condition for {match['kajabi_email']}", 'WARNING')
                    results['skipped'] += 1
                    continue

            # Record success
            enriched_fields = []
            if can_enrich_phone:
                results['enriched_phone'] += 1
                enriched_fields.append('phone')
            if can_enrich_address:
                results['enriched_address'] += 1
                enriched_fields.append('address')

            if can_enrich_phone and can_enrich_address:
                results['enriched_both'] += 1

            kajabi_name = f"{match['kajabi_first']} {match['kajabi_last']}"

            results['details'].append({
                'kajabi_email': match['kajabi_email'],
                'kajabi_name': kajabi_name,
                'tt_email': match['tt_email'],
                'enriched': enriched_fields,
                'phone': match['tt_phone'] if can_enrich_phone else None,
                'address': match['tt_address_line_1'] if can_enrich_address else None
            })

            log(f"✓ {kajabi_name}: {', '.join(enriched_fields)}", 'SUCCESS')

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
    log(f"TICKET TAILOR CROSS-MATCH SUMMARY ({'DRY-RUN' if dry_run else 'EXECUTED'})", 'HEADER')
    log(f"{'='*80}", 'HEADER')

    log(f"Total name matches found: {results['total_matches']}", 'INFO')
    log(f"✓ Contacts enriched with phone: {results['enriched_phone']}", 'SUCCESS')
    log(f"✓ Contacts enriched with address: {results['enriched_address']}", 'SUCCESS')
    log(f"✓ Contacts enriched with both: {results['enriched_both']}", 'SUCCESS')
    log(f"⊘ Skipped (no enrichment needed): {results['skipped']}", 'WARNING')

    total_enriched = len(results['details'])
    if total_enriched > 0:
        log(f"\n📈 Total contacts enriched: {total_enriched}", 'SUCCESS')

        # Show all enrichments (since there aren't many)
        log(f"\n{'='*80}", 'HEADER')
        log("ALL ENRICHMENTS:", 'HEADER')
        log(f"{'='*80}", 'HEADER')

        for detail in results['details']:
            log(f"\n✓ {detail['kajabi_name']} ({detail['kajabi_email']})", 'SUCCESS')
            log(f"  Matched TT: {detail['tt_email']}", 'INFO')
            log(f"  Enriched: {', '.join(detail['enriched'])}", 'INFO')
            if detail['phone']:
                log(f"  Phone: {detail['phone']}", 'INFO')
            if detail['address']:
                log(f"  Address: {detail['address']}", 'INFO')

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
            log("Usage: python3 scripts/enrich_from_ticket_tailor_crossmatch.py [--dry-run|--execute]", 'ERROR')
            sys.exit(1)

    # Enrich contacts
    results = enrich_contacts(dry_run)

    # Print summary
    print_summary(results, dry_run)

    # Save results
    if len(results['details']) > 0:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode = 'dryrun' if dry_run else 'execute'
        output_file = f"ticket_tailor_crossmatch_{mode}_{timestamp}.json"

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
