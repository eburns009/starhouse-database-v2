#!/usr/bin/env python3
"""
Fix subscription product links by matching amount and billing cycle.

This script links subscriptions missing product_id to products by matching:
- Amount (exact match)
- Billing cycle (normalized: Month→monthly, Year→annual)

FAANG Quality Standards:
- Dry-run mode by default
- Never overwrites existing product_id
- Tracks which products were matched
- Idempotent operations
- Comprehensive logging

Usage:
    python3 scripts/fix_subscription_product_links.py --dry-run
    python3 scripts/fix_subscription_product_links.py --execute
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
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

def normalize_billing_cycle(cycle: str) -> str:
    """Normalize billing cycle to standard format."""
    cycle_lower = cycle.lower().strip()
    if cycle_lower in ['month', 'monthly']:
        return 'monthly'
    elif cycle_lower in ['year', 'annual', 'yearly']:
        return 'annual'
    return cycle_lower

def build_product_lookup(cursor) -> Dict[Tuple[float, str], str]:
    """
    Build a lookup table of products by (amount, billing_cycle) -> product_id.

    Returns: Dict mapping (amount, normalized_cycle) -> product_id
    """
    log("Building product lookup table...", 'INFO')

    cursor.execute("""
        SELECT DISTINCT
            p.id as product_id,
            p.name as product_name,
            s.amount,
            s.billing_cycle
        FROM products p
        INNER JOIN subscriptions s ON s.product_id = p.id AND s.deleted_at IS NULL
        WHERE p.deleted_at IS NULL
        ORDER BY p.name, s.amount
    """)

    lookup = {}
    for row in cursor.fetchall():
        amount = float(row['amount'])
        cycle = normalize_billing_cycle(row['billing_cycle'])
        key = (amount, cycle)

        if key in lookup:
            # If multiple products match, prefer the first one (alphabetically)
            log(f"Duplicate pricing: ${amount}/{cycle} → {row['product_name']}", 'WARNING')
        else:
            lookup[key] = {
                'product_id': row['product_id'],
                'product_name': row['product_name']
            }

    log(f"Built lookup table with {len(lookup)} unique price points", 'SUCCESS')
    return lookup

def fix_subscription_links(product_lookup: Dict, dry_run: bool) -> Dict:
    """Fix subscription product links."""
    log(f"\n{'='*80}", 'HEADER')
    log(f"FIXING MODE: {'DRY-RUN' if dry_run else 'EXECUTE'}", 'HEADER')
    log(f"{'='*80}\n", 'HEADER')

    # Connect to database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        log("DATABASE_URL not set", 'ERROR')
        sys.exit(1)

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    results = {
        'total_missing': 0,
        'matched': 0,
        'no_match': 0,
        'details': []
    }

    try:
        # Get subscriptions without product_id
        cursor.execute("""
            SELECT
                id,
                contact_id,
                amount,
                billing_cycle,
                kajabi_subscription_id,
                payment_processor,
                status
            FROM subscriptions
            WHERE product_id IS NULL
              AND deleted_at IS NULL
            ORDER BY amount DESC, billing_cycle
        """)

        unmatched_subs = cursor.fetchall()
        results['total_missing'] = len(unmatched_subs)

        log(f"Found {len(unmatched_subs)} subscriptions without product_id", 'INFO')

        if not unmatched_subs:
            log("No subscriptions need fixing", 'INFO')
            return results

        log(f"\nProcessing {len(unmatched_subs)} subscriptions...\n", 'INFO')

        # Group by amount/cycle for reporting
        by_key = {}
        for sub in unmatched_subs:
            amount = float(sub['amount'])
            cycle = normalize_billing_cycle(sub['billing_cycle'])
            key = (amount, cycle)

            # Try to find matching product
            if key in product_lookup:
                product_info = product_lookup[key]

                # Update subscription
                if not dry_run:
                    cursor.execute("""
                        UPDATE subscriptions
                        SET
                            product_id = %s,
                            updated_at = NOW()
                        WHERE id = %s
                          AND product_id IS NULL
                          AND deleted_at IS NULL
                    """, (product_info['product_id'], sub['id']))

                    if cursor.rowcount == 0:
                        log(f"⊘ Race condition for subscription {sub['id']}", 'WARNING')
                        continue

                results['matched'] += 1

                # Track for summary
                if key not in by_key:
                    by_key[key] = {
                        'product_name': product_info['product_name'],
                        'count': 0
                    }
                by_key[key]['count'] += 1

                results['details'].append({
                    'subscription_id': sub['id'],
                    'amount': amount,
                    'cycle': cycle,
                    'product_name': product_info['product_name'],
                    'status': sub['status']
                })

            else:
                results['no_match'] += 1
                log(f"⊘ No product found for ${amount}/{cycle} (sub: {sub['kajabi_subscription_id']})", 'WARNING')

        # Commit changes
        if not dry_run:
            conn.commit()
            log(f"\n✓ Changes committed to database", 'SUCCESS')
        else:
            conn.rollback()
            log(f"\n⊘ Dry-run complete - no changes made", 'INFO')

        # Report by key
        if by_key:
            log(f"\n{'='*80}", 'HEADER')
            log("MATCHED SUBSCRIPTIONS BY PRODUCT:", 'HEADER')
            log(f"{'='*80}", 'HEADER')

            for (amount, cycle), info in sorted(by_key.items(), key=lambda x: x[1]['count'], reverse=True):
                log(f"\n✓ ${amount:6}/{cycle:7} => {info['product_name']}", 'SUCCESS')
                log(f"  Matched {info['count']} subscriptions", 'INFO')

    except Exception as e:
        conn.rollback()
        log(f"Error fixing subscriptions: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    return results

def print_summary(results: Dict, dry_run: bool) -> None:
    """Print fixing summary."""
    log(f"\n{'='*80}", 'HEADER')
    log(f"SUBSCRIPTION PRODUCT LINK SUMMARY ({'DRY-RUN' if dry_run else 'EXECUTED'})", 'HEADER')
    log(f"{'='*80}", 'HEADER')

    log(f"Total subscriptions missing product_id: {results['total_missing']}", 'INFO')
    log(f"✓ Matched to products: {results['matched']}", 'SUCCESS')
    log(f"⊘ No matching product found: {results['no_match']}", 'WARNING')

    if results['matched'] > 0:
        match_pct = (results['matched'] / results['total_missing'] * 100) if results['total_missing'] > 0 else 0
        log(f"\n📈 Match rate: {match_pct:.1f}%", 'SUCCESS')

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
            log("Usage: python3 scripts/fix_subscription_product_links.py [--dry-run|--execute]", 'ERROR')
            sys.exit(1)

    # Connect to get product lookup
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        log("DATABASE_URL not set", 'ERROR')
        sys.exit(1)

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # Build product lookup
    product_lookup = build_product_lookup(cursor)

    cursor.close()
    conn.close()

    # Fix subscriptions
    results = fix_subscription_links(product_lookup, dry_run)

    # Print summary
    print_summary(results, dry_run)

    # Save results
    if results['matched'] > 0:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode = 'dryrun' if dry_run else 'execute'
        output_file = f"subscription_product_fix_{mode}_{timestamp}.json"

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
