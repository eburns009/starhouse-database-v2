#!/usr/bin/env python3
"""
ADDRESS DATA QUALITY REPORT
===========================

Generates a comprehensive data quality report for address fields in the contacts table.

Reports on:
- Overall address completeness
- Pattern detection (city in line_2, duplicates, field reversals)
- Source system breakdown
- Data quality metrics
- Trending over time

Usage:
  python3 scripts/address_data_quality_report.py
  python3 scripts/address_data_quality_report.py --output reports/address_quality_$(date +%Y%m%d).txt
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONNECTION = get_database_url()

# ============================================================================
# REPORT FUNCTIONS
# ============================================================================

def generate_report(output_file: Optional[str] = None) -> None:
    """
    Generate comprehensive address data quality report.

    Args:
        output_file: Optional path to save report (default: print to stdout)
    """
    # Connect to database
    conn = psycopg2.connect(DB_CONNECTION)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    report_lines = []

    def add_line(line: str = ""):
        """Add line to report."""
        report_lines.append(line)
        if not output_file:
            print(line)

    try:
        # Header
        add_line("=" * 80)
        add_line("ADDRESS DATA QUALITY REPORT")
        add_line("=" * 80)
        add_line(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        add_line()

        # Overall statistics
        add_line("OVERALL STATISTICS")
        add_line("-" * 80)

        cur.execute("""
            SELECT
                COUNT(*) as total_contacts,
                COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL) as with_address,
                COUNT(*) FILTER (WHERE city IS NOT NULL) as with_city,
                COUNT(*) FILTER (WHERE state IS NOT NULL) as with_state,
                COUNT(*) FILTER (WHERE postal_code IS NOT NULL) as with_postal,
                COUNT(*) FILTER (WHERE country IS NOT NULL) as with_country,
                ROUND(100.0 * COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL) / COUNT(*), 1) as address_pct,
                ROUND(100.0 * COUNT(*) FILTER (WHERE city IS NOT NULL) / NULLIF(COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL), 0), 1) as city_completion_pct
            FROM contacts
        """)
        stats = cur.fetchone()

        add_line(f"Total Contacts:          {stats['total_contacts']:,}")
        add_line(f"With Addresses:          {stats['with_address']:,} ({stats['address_pct']}%)")
        add_line(f"With City:               {stats['with_city']:,} ({stats['city_completion_pct']}% of addresses)")
        add_line(f"With State:              {stats['with_state']:,}")
        add_line(f"With Postal Code:        {stats['with_postal']:,}")
        add_line(f"With Country:            {stats['with_country']:,}")
        add_line()

        # Pattern detection
        add_line("PATTERN DETECTION")
        add_line("-" * 80)

        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE address_line_2 IS NOT NULL AND city IS NULL AND address_line_1 IS NOT NULL) as pattern1_city_in_line2,
                COUNT(*) FILTER (WHERE address_line_1 = address_line_2 AND address_line_1 IS NOT NULL) as pattern2_duplicates,
                COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL AND LENGTH(address_line_1) < 10 AND address_line_2 IS NOT NULL AND LENGTH(address_line_2) > 10) as pattern3_field_reversal
            FROM contacts
        """)
        patterns = cur.fetchone()

        add_line(f"Pattern 1 (City in line 2):     {patterns['pattern1_city_in_line2']:,}")
        add_line(f"Pattern 2 (Duplicates):         {patterns['pattern2_duplicates']:,}")
        add_line(f"Pattern 3 (Field Reversal):     {patterns['pattern3_field_reversal']:,}")

        total_issues = sum(patterns.values())
        add_line(f"Total Issues:                   {total_issues:,}")

        if total_issues == 0:
            add_line()
            add_line("✅ NO ISSUES DETECTED - Data quality is excellent!")
        else:
            issue_pct = round(100.0 * total_issues / stats['with_address'], 1)
            add_line(f"Issue Rate:                     {issue_pct}% of contacts with addresses")

        add_line()

        # Source system breakdown
        add_line("SOURCE SYSTEM BREAKDOWN")
        add_line("-" * 80)

        cur.execute("""
            SELECT
                source_system,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL) as with_address,
                ROUND(100.0 * COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL) / COUNT(*), 1) as address_pct
            FROM contacts
            GROUP BY source_system
            ORDER BY total DESC
        """)
        sources = cur.fetchall()

        add_line(f"{'Source':<20} {'Total':>10} {'With Address':>15} {'Address %':>12}")
        add_line("-" * 80)
        for source in sources:
            add_line(f"{source['source_system']:<20} {source['total']:>10,} {source['with_address']:>15,} {source['address_pct']:>11}%")

        add_line()

        # Address quality by source
        add_line("ADDRESS QUALITY BY SOURCE")
        add_line("-" * 80)

        cur.execute("""
            SELECT
                source_system,
                COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL) as with_address,
                COUNT(*) FILTER (WHERE city IS NOT NULL) as with_city,
                ROUND(100.0 * COUNT(*) FILTER (WHERE city IS NOT NULL) / NULLIF(COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL), 0), 1) as city_completion
            FROM contacts
            WHERE address_line_1 IS NOT NULL
            GROUP BY source_system
            ORDER BY with_address DESC
        """)
        quality = cur.fetchall()

        add_line(f"{'Source':<20} {'Addresses':>12} {'With City':>12} {'City %':>10}")
        add_line("-" * 80)
        for q in quality:
            add_line(f"{q['source_system']:<20} {q['with_address']:>12,} {q['with_city']:>12,} {q['city_completion']:>9}%")

        add_line()

        # Recent updates
        add_line("RECENT UPDATES (Last 7 Days)")
        add_line("-" * 80)

        cur.execute("""
            SELECT
                DATE(updated_at) as update_date,
                COUNT(*) as updates,
                COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL) as with_address
            FROM contacts
            WHERE updated_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(updated_at)
            ORDER BY update_date DESC
        """)
        recent = cur.fetchall()

        if recent:
            add_line(f"{'Date':<15} {'Updates':>12} {'With Address':>15}")
            add_line("-" * 80)
            for r in recent:
                add_line(f"{r['update_date']:<15} {r['updates']:>12,} {r['with_address']:>15,}")
        else:
            add_line("No updates in the last 7 days")

        add_line()

        # Recommendations
        add_line("RECOMMENDATIONS")
        add_line("-" * 80)

        if total_issues > 0:
            add_line("⚠️  Address quality issues detected:")
            add_line()
            if patterns['pattern1_city_in_line2'] > 0:
                add_line(f"   - Run fix script for Pattern 1 ({patterns['pattern1_city_in_line2']} contacts)")
            if patterns['pattern2_duplicates'] > 0:
                add_line(f"   - Run fix script for Pattern 2 ({patterns['pattern2_duplicates']} contacts)")
            if patterns['pattern3_field_reversal'] > 0:
                add_line(f"   - Manual review needed for Pattern 3 ({patterns['pattern3_field_reversal']} contacts)")
            add_line()
            add_line("   Command:")
            add_line("   python3 scripts/fix_address_data_quality.py --dry-run")
        else:
            add_line("✅ Data quality is excellent!")
            add_line()
            add_line("   - Continue running weekly imports with validation enabled")
            add_line("   - Monitor data quality metrics monthly")

        add_line()
        add_line("=" * 80)
        add_line("END OF REPORT")
        add_line("=" * 80)

    finally:
        cur.close()
        conn.close()

    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(report_lines))
        print(f"\n📄 Report saved to: {output_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Generate address data quality report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--output',
        help='Output file path (default: print to stdout)'
    )

    args = parser.parse_args()

    try:
        generate_report(args.output)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
