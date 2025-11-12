#!/usr/bin/env python3
"""
Enrich Kajabi contacts with identified opportunities from enrichment analysis.

This script implements the 6 specific enrichment opportunities identified:
- 1 phone match (ticket_tailor_id enrichment)
- 5 name+address matches (phone number enrichment)

FAANG Quality Standards:
- Dry-run mode by default
- Never overwrites existing data
- Tracks data provenance
- Idempotent operations
- Comprehensive logging

Usage:
    python3 scripts/enrich_identified_opportunities.py --dry-run
    python3 scripts/enrich_identified_opportunities.py --execute
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# ANSI color codes for terminal output
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

def load_opportunities() -> List[Dict]:
    """Load enrichment opportunities from JSON file."""
    file_path = 'enrichment_opportunities.json'
    if not os.path.exists(file_path):
        log(f"Enrichment file not found: {file_path}", 'ERROR')
        sys.exit(1)

    with open(file_path, 'r') as f:
        data = json.load(f)

    log(f"Loaded {len(data['opportunities'])} opportunities from {file_path}", 'SUCCESS')
    return data['opportunities']

def get_contact_current_state(cursor, kajabi_id: str) -> Optional[Dict]:
    """Get current state of a Kajabi contact."""
    cursor.execute("""
        SELECT
            id,
            email,
            first_name,
            last_name,
            phone,
            phone_source,
            ticket_tailor_id,
            address_line_1
        FROM contacts
        WHERE kajabi_id = %s
          AND deleted_at IS NULL
    """, (kajabi_id,))

    return cursor.fetchone()

def enrich_phone_match(cursor, opportunity: Dict, dry_run: bool) -> Dict:
    """
    Handle phone match opportunity (add ticket_tailor_id).

    Returns: Dict with success status and details
    """
    kajabi_id = opportunity['kajabi_id']
    source_id = opportunity['source_id']

    # Get current state
    contact = get_contact_current_state(cursor, kajabi_id)
    if not contact:
        return {
            'success': False,
            'reason': 'Contact not found',
            'kajabi_id': kajabi_id
        }

    # Check if ticket_tailor_id already set
    if contact['ticket_tailor_id']:
        return {
            'success': False,
            'reason': f'ticket_tailor_id already set: {contact["ticket_tailor_id"]}',
            'kajabi_id': kajabi_id,
            'skipped': True
        }

    # Perform update
    if not dry_run:
        cursor.execute("""
            UPDATE contacts
            SET
                ticket_tailor_id = %s,
                updated_at = NOW()
            WHERE kajabi_id = %s
              AND deleted_at IS NULL
              AND (ticket_tailor_id IS NULL OR ticket_tailor_id = '')
        """, (source_id, kajabi_id))

        affected = cursor.rowcount
        if affected == 0:
            return {
                'success': False,
                'reason': 'No rows updated (race condition)',
                'kajabi_id': kajabi_id
            }

    return {
        'success': True,
        'kajabi_id': kajabi_id,
        'email': contact['email'],
        'name': f"{contact['first_name']} {contact['last_name']}",
        'action': 'Added ticket_tailor_id',
        'value': source_id,
        'phone': opportunity['phone']
    }

def enrich_name_address_match(cursor, opportunity: Dict, dry_run: bool) -> Dict:
    """
    Handle name+address match opportunity (add phone number).

    Returns: Dict with success status and details
    """
    kajabi_id = opportunity['kajabi_id']
    phone = opportunity['other_phone']
    source = opportunity['source']

    # Get current state
    contact = get_contact_current_state(cursor, kajabi_id)
    if not contact:
        return {
            'success': False,
            'reason': 'Contact not found',
            'kajabi_id': kajabi_id
        }

    # Check if phone already set
    if contact['phone']:
        return {
            'success': False,
            'reason': f'Phone already set: {contact["phone"]}',
            'kajabi_id': kajabi_id,
            'skipped': True
        }

    # Perform update
    if not dry_run:
        cursor.execute("""
            UPDATE contacts
            SET
                phone = %s,
                phone_source = %s,
                updated_at = NOW()
            WHERE kajabi_id = %s
              AND deleted_at IS NULL
              AND (phone IS NULL OR phone = '')
        """, (phone, source, kajabi_id))

        affected = cursor.rowcount
        if affected == 0:
            return {
                'success': False,
                'reason': 'No rows updated (race condition)',
                'kajabi_id': kajabi_id
            }

    return {
        'success': True,
        'kajabi_id': kajabi_id,
        'email': contact['email'],
        'name': f"{contact['first_name']} {contact['last_name']}",
        'action': 'Added phone',
        'value': phone,
        'source': source,
        'address': opportunity['address']
    }

def process_opportunities(opportunities: List[Dict], dry_run: bool) -> Dict:
    """Process all enrichment opportunities."""
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
        'total': len(opportunities),
        'successful': 0,
        'skipped': 0,
        'failed': 0,
        'details': []
    }

    try:
        for idx, opportunity in enumerate(opportunities, 1):
            log(f"\n--- Opportunity {idx}/{len(opportunities)} ---", 'HEADER')
            log(f"Type: {opportunity['type']}")
            log(f"Kajabi: {opportunity['kajabi_name']} ({opportunity['kajabi_email']})")
            log(f"Signal: {opportunity['signal']}")
            log(f"Action: {opportunity['action']}")

            # Route to appropriate handler
            if opportunity['type'] == 'phone_match':
                result = enrich_phone_match(cursor, opportunity, dry_run)
            elif opportunity['type'] == 'name_address_match':
                result = enrich_name_address_match(cursor, opportunity, dry_run)
            else:
                log(f"Unknown opportunity type: {opportunity['type']}", 'ERROR')
                results['failed'] += 1
                continue

            # Record result
            results['details'].append(result)

            if result['success']:
                results['successful'] += 1
                log(f"✓ {result['action']}: {result['value']}", 'SUCCESS')
                if dry_run:
                    log("  (Would execute in non-dry-run mode)", 'INFO')
            elif result.get('skipped'):
                results['skipped'] += 1
                log(f"⊘ Skipped: {result['reason']}", 'WARNING')
            else:
                results['failed'] += 1
                log(f"✗ Failed: {result['reason']}", 'ERROR')

        # Commit if not dry-run
        if not dry_run:
            conn.commit()
            log("\n✓ Changes committed to database", 'SUCCESS')
        else:
            conn.rollback()
            log("\n⊘ Dry-run complete - no changes made", 'INFO')

    except Exception as e:
        conn.rollback()
        log(f"Error processing opportunities: {e}", 'ERROR')
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
    log(f"ENRICHMENT SUMMARY ({'DRY-RUN' if dry_run else 'EXECUTED'})", 'HEADER')
    log(f"{'='*80}", 'HEADER')

    log(f"Total Opportunities: {results['total']}", 'INFO')
    log(f"✓ Successful: {results['successful']}", 'SUCCESS')
    log(f"⊘ Skipped: {results['skipped']}", 'WARNING')
    log(f"✗ Failed: {results['failed']}", 'ERROR')

    if results['successful'] > 0:
        log(f"\n{'='*80}", 'HEADER')
        log("SUCCESSFUL ENRICHMENTS:", 'HEADER')
        log(f"{'='*80}", 'HEADER')

        for detail in results['details']:
            if detail['success']:
                log(f"\n✓ {detail['name']} ({detail['email']})", 'SUCCESS')
                log(f"  Action: {detail['action']}", 'INFO')
                log(f"  Value: {detail['value']}", 'INFO')
                if 'source' in detail:
                    log(f"  Source: {detail['source']}", 'INFO')
                if 'phone' in detail:
                    log(f"  Phone Match: {detail['phone']}", 'INFO')
                if 'address' in detail:
                    log(f"  Address Match: {detail['address']}", 'INFO')

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
            log("Usage: python3 scripts/enrich_identified_opportunities.py [--dry-run|--execute]", 'ERROR')
            sys.exit(1)

    # Load opportunities
    opportunities = load_opportunities()

    # Process opportunities
    results = process_opportunities(opportunities, dry_run)

    # Print summary
    print_summary(results, dry_run)

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    mode = 'dryrun' if dry_run else 'execute'
    output_file = f"enrichment_report_{mode}_{timestamp}.json"

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
