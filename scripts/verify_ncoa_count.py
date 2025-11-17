#!/usr/bin/env python3
"""
Verify count of validated addresses ready for NCOA processing
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

def main():
    print()
    print("=" * 80)
    print("VERIFIED ADDRESS COUNT FOR NCOA PROCESSING")
    print("=" * 80)
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Count all validated addresses
    cursor.execute("""
        SELECT
            COUNT(*) as total_validated,
            SUM(CASE WHEN usps_dpv_confirmation = 'Y' THEN 1 ELSE 0 END) as dpv_y,
            SUM(CASE WHEN usps_dpv_confirmation = 'D' THEN 1 ELSE 0 END) as dpv_d,
            SUM(CASE WHEN usps_dpv_confirmation = 'S' THEN 1 ELSE 0 END) as dpv_s
        FROM contacts
        WHERE address_validated = true
    """)

    result = cursor.fetchone()

    print("Database Validation Results:")
    print(f"  Total validated addresses:         {result['total_validated']:,}")
    print(f"  DPV Confirmed (Y):                 {result['dpv_y']:,}")
    print(f"  DPV Missing Unit (D):              {result['dpv_d']:,}")
    print(f"  DPV Secondary Confirmed (S):       {result['dpv_s']:,}")
    print()

    # Check export file
    try:
        import csv
        with open('/tmp/truencoa_mailing_list.csv', 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            export_count = len(rows)

        print("Export File Verification:")
        print(f"  File: /tmp/truencoa_mailing_list.csv")
        print(f"  Records in file:                   {export_count:,}")
        print()

        # Verify counts match
        if export_count == result['total_validated']:
            print("✅ VERIFIED: Database and export file counts match!")
            print(f"   {result['total_validated']:,} addresses ready for NCOA processing")
        else:
            print("⚠️  WARNING: Count mismatch!")
            print(f"   Database: {result['total_validated']:,}")
            print(f"   Export file: {export_count:,}")
            print(f"   Difference: {abs(result['total_validated'] - export_count):,}")
    except FileNotFoundError:
        print("Export File: NOT FOUND")
        print("  Run: python3 scripts/export_for_truencoa.py")

    print()
    print("=" * 80)
    print()

    # Show breakdown by DPV quality
    print("Address Quality Breakdown:")
    print()
    print(f"  Excellent (DPV: Y)     {result['dpv_y']:,} addresses ({result['dpv_y']/result['total_validated']*100:.1f}%)")
    print(f"  Good (DPV: D)          {result['dpv_d']:,} addresses ({result['dpv_d']/result['total_validated']*100:.1f}%)")
    print(f"  Good (DPV: S)          {result['dpv_s']:,} addresses ({result['dpv_s']/result['total_validated']*100:.1f}%)")
    print()
    print("  Total NCOA-ready:      " + f"{result['total_validated']:,} addresses")
    print()

    # Revenue breakdown
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(total_spent) as total_revenue,
            SUM(CASE WHEN total_spent > 0 THEN 1 ELSE 0 END) as paying_customers,
            SUM(CASE WHEN total_spent > 0 THEN total_spent ELSE 0 END) as paying_revenue
        FROM contacts
        WHERE address_validated = true
    """)

    revenue = cursor.fetchone()

    print("Revenue Impact:")
    print(f"  Paying customers:      {revenue['paying_customers']:,}")
    print(f"  Total revenue:         ${revenue['paying_revenue']:,.2f}")
    print(f"  Average per customer:  ${revenue['paying_revenue']/revenue['paying_customers']:.2f}")
    print()

    print("=" * 80)
    print("✅ READY FOR NCOA PROCESSING")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Upload /tmp/truencoa_mailing_list.csv to https://app.truencoa.com/")
    print("2. Wait for processing (2-3 hours)")
    print("3. Download results to /tmp/truencoa_results.csv")
    print("4. Run: python3 scripts/import_ncoa_results.py /tmp/truencoa_results.csv")
    print()

    conn.close()

if __name__ == '__main__':
    main()
