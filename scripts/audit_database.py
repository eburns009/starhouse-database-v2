#!/usr/bin/env python3
"""
Database Audit Script - Phase 1, Day 2-3
FAANG-Grade Database Health Check

Runs comprehensive audit queries and outputs results for DATABASE_AUDIT.md

Usage:
    python3 scripts/audit_database.py
"""

import sys
import os
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import get_connection

def run_audit():
    """Run all database audit queries and print results."""

    print("=" * 80)
    print("DATABASE AUDIT - StarHouse Platform")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    conn = get_connection()
    cur = conn.cursor()

    # ================================================================
    # 1. TABLE ROW COUNTS
    # ================================================================
    print("## 1. TABLE ROW COUNTS")
    print("-" * 60)

    cur.execute("""
        SELECT
            relname as tablename,
            n_live_tup as row_count,
            n_dead_tup as dead_rows
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC;
    """)

    rows = cur.fetchall()
    print(f"{'Table':<40} {'Rows':>10} {'Dead':>10}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<40} {row[1]:>10,} {row[2]:>10,}")
    print()

    # ================================================================
    # 2. TABLES WITHOUT PRIMARY KEYS
    # ================================================================
    print("## 2. TABLES WITHOUT PRIMARY KEYS")
    print("-" * 60)

    cur.execute("""
        SELECT t.tablename
        FROM pg_tables t
        WHERE t.schemaname = 'public'
          AND NOT EXISTS (
            SELECT 1 FROM pg_indexes i
            WHERE i.tablename = t.tablename
              AND i.schemaname = 'public'
              AND i.indexname LIKE '%pkey%'
          )
        ORDER BY t.tablename;
    """)

    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  - {row[0]}")
    else:
        print("  ✓ All tables have primary keys")
    print()

    # ================================================================
    # 3. FOREIGN KEY RELATIONSHIPS
    # ================================================================
    print("## 3. FOREIGN KEY RELATIONSHIPS")
    print("-" * 60)

    cur.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name;
    """)

    rows = cur.fetchall()
    print(f"{'Table.Column':<40} {'References':>30}")
    print("-" * 70)
    for row in rows:
        print(f"{row[0]}.{row[1]:<30} -> {row[2]}.{row[3]}")
    print()

    # ================================================================
    # 4. DUPLICATE CONTACTS BY EMAIL
    # ================================================================
    print("## 4. DUPLICATE CONTACTS BY EMAIL")
    print("-" * 60)

    cur.execute("""
        SELECT email, COUNT(*) as count
        FROM contacts
        WHERE email IS NOT NULL
        GROUP BY email
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 20;
    """)

    rows = cur.fetchall()
    if rows:
        print(f"{'Email':<50} {'Count':>10}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<50} {row[1]:>10}")
    else:
        print("  ✓ No duplicate emails found")
    print()

    # ================================================================
    # 5. DUPLICATE EXTERNAL IDENTITIES
    # ================================================================
    print("## 5. DUPLICATE EXTERNAL IDENTITIES")
    print("-" * 60)

    try:
        cur.execute("""
            SELECT system, external_id, COUNT(*) as count
            FROM external_identities
            GROUP BY system, external_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 20;
        """)

        rows = cur.fetchall()
        if rows:
            print(f"{'System':<20} {'External ID':<30} {'Count':>10}")
            print("-" * 60)
            for row in rows:
                print(f"{row[0]:<20} {row[1]:<30} {row[2]:>10}")
        else:
            print("  ✓ No duplicate external identities found")
    except Exception as e:
        print(f"  (Table may not exist: {e})")
    print()

    # ================================================================
    # 6. CONTACTS DATA COMPLETENESS
    # ================================================================
    print("## 6. CONTACTS DATA COMPLETENESS")
    print("-" * 60)

    cur.execute("""
        SELECT
            COUNT(*) as total_contacts,
            COUNT(email) as has_email,
            COUNT(first_name) as has_first_name,
            COUNT(last_name) as has_last_name,
            COUNT(phone) as has_phone,
            COUNT(address_line_1) as has_address,
            ROUND(100.0 * COUNT(email) / NULLIF(COUNT(*), 0), 2) as email_pct,
            ROUND(100.0 * COUNT(first_name) / NULLIF(COUNT(*), 0), 2) as first_name_pct,
            ROUND(100.0 * COUNT(last_name) / NULLIF(COUNT(*), 0), 2) as last_name_pct,
            ROUND(100.0 * COUNT(phone) / NULLIF(COUNT(*), 0), 2) as phone_pct,
            ROUND(100.0 * COUNT(address_line_1) / NULLIF(COUNT(*), 0), 2) as address_pct
        FROM contacts;
    """)

    row = cur.fetchone()
    print(f"Total Contacts: {row[0]:,}")
    print()
    print(f"{'Field':<20} {'Count':>10} {'Percentage':>12}")
    print("-" * 42)
    print(f"{'Email':<20} {row[1]:>10,} {row[6]:>10.1f}%")
    print(f"{'First Name':<20} {row[2]:>10,} {row[7]:>10.1f}%")
    print(f"{'Last Name':<20} {row[3]:>10,} {row[8]:>10.1f}%")
    print(f"{'Phone':<20} {row[4]:>10,} {row[9]:>10.1f}%")
    print(f"{'Address':<20} {row[5]:>10,} {row[10]:>10.1f}%")
    print()

    # ================================================================
    # 7. CONTACTS WITHOUT SOURCE TRACKING
    # ================================================================
    print("## 7. CONTACTS WITHOUT SOURCE TRACKING")
    print("-" * 60)

    try:
        cur.execute("""
            SELECT COUNT(*) as contacts_without_source
            FROM contacts c
            WHERE NOT EXISTS (
                SELECT 1 FROM external_identities ei
                WHERE ei.contact_id = c.id
            );
        """)

        row = cur.fetchone()
        print(f"Contacts without external identity: {row[0]:,}")
    except Exception as e:
        print(f"  (Could not check: {e})")
    print()

    # ================================================================
    # 8. RLS (ROW LEVEL SECURITY) STATUS
    # ================================================================
    print("## 8. RLS (ROW LEVEL SECURITY) STATUS")
    print("-" * 60)

    cur.execute("""
        SELECT
            tablename,
            rowsecurity
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)

    rows = cur.fetchall()
    enabled = 0
    disabled = 0
    print(f"{'Table':<40} {'RLS Enabled':>15}")
    print("-" * 55)
    for row in rows:
        status = "✓ Yes" if row[1] else "✗ No"
        print(f"{row[0]:<40} {status:>15}")
        if row[1]:
            enabled += 1
        else:
            disabled += 1
    print()
    print(f"Summary: {enabled} enabled, {disabled} disabled")
    print()

    # ================================================================
    # 9. RLS POLICIES
    # ================================================================
    print("## 9. RLS POLICIES")
    print("-" * 60)

    cur.execute("""
        SELECT
            tablename,
            policyname,
            cmd
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname;
    """)

    rows = cur.fetchall()
    if rows:
        print(f"{'Table':<30} {'Policy':<35} {'Command':>10}")
        print("-" * 75)
        for row in rows:
            print(f"{row[0]:<30} {row[1]:<35} {row[2]:>10}")
    else:
        print("  No RLS policies found")
    print()

    # ================================================================
    # 10. INDEX USAGE STATISTICS
    # ================================================================
    print("## 10. INDEX USAGE STATISTICS")
    print("-" * 60)

    cur.execute("""
        SELECT
            relname as table_name,
            seq_scan,
            seq_tup_read,
            idx_scan,
            idx_tup_fetch,
            CASE
                WHEN (seq_scan + idx_scan) > 0
                THEN ROUND(100.0 * idx_scan / (seq_scan + idx_scan), 2)
                ELSE 0
            END as index_usage_pct
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
          AND (seq_scan + idx_scan) > 0
        ORDER BY seq_scan DESC
        LIMIT 20;
    """)

    rows = cur.fetchall()
    print(f"{'Table':<30} {'Seq Scans':>12} {'Idx Scans':>12} {'Idx %':>8}")
    print("-" * 62)
    for row in rows:
        print(f"{row[0]:<30} {row[1]:>12,} {row[3]:>12,} {row[5]:>7.1f}%")
    print()

    # ================================================================
    # 11. TABLE SIZES
    # ================================================================
    print("## 11. TABLE SIZES")
    print("-" * 60)

    cur.execute("""
        SELECT
            tablename,
            pg_size_pretty(pg_total_relation_size(quote_ident(tablename)::regclass)) as total_size,
            pg_size_pretty(pg_relation_size(quote_ident(tablename)::regclass)) as table_size,
            pg_size_pretty(pg_indexes_size(quote_ident(tablename)::regclass)) as index_size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(quote_ident(tablename)::regclass) DESC;
    """)

    rows = cur.fetchall()
    print(f"{'Table':<30} {'Total':>12} {'Data':>12} {'Indexes':>12}")
    print("-" * 66)
    for row in rows:
        print(f"{row[0]:<30} {row[1]:>12} {row[2]:>12} {row[3]:>12}")
    print()

    # ================================================================
    # 12. INDEXES LIST
    # ================================================================
    print("## 12. INDEXES BY TABLE")
    print("-" * 60)

    cur.execute("""
        SELECT
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
    """)

    rows = cur.fetchall()
    current_table = None
    for row in rows:
        if row[0] != current_table:
            if current_table:
                print()
            current_table = row[0]
            print(f"\n### {current_table}")
        print(f"  - {row[1]}")
    print()

    # ================================================================
    # 13. TRANSACTIONS BY SOURCE SYSTEM
    # ================================================================
    print("## 13. TRANSACTIONS BY SOURCE SYSTEM")
    print("-" * 60)

    try:
        cur.execute("""
            SELECT
                source_system,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                MIN(transaction_date) as earliest,
                MAX(transaction_date) as latest
            FROM transactions
            GROUP BY source_system
            ORDER BY transaction_count DESC;
        """)

        rows = cur.fetchall()
        if rows:
            print(f"{'Source':<15} {'Count':>10} {'Total $':>15} {'Date Range'}")
            print("-" * 70)
            for row in rows:
                total = f"${row[2]:,.2f}" if row[2] else "$0.00"
                dates = f"{row[3]} to {row[4]}" if row[3] and row[4] else "N/A"
                print(f"{row[0] or 'NULL':<15} {row[1]:>10,} {total:>15} {dates}")
        else:
            print("  No transactions found")
    except Exception as e:
        print(f"  (Could not check: {e})")
    print()

    # ================================================================
    # 14. SUBSCRIPTION STATUS BREAKDOWN
    # ================================================================
    print("## 14. SUBSCRIPTION STATUS BREAKDOWN")
    print("-" * 60)

    try:
        cur.execute("""
            SELECT
                status,
                COUNT(*) as count,
                SUM(amount) as total_mrr
            FROM subscriptions
            GROUP BY status
            ORDER BY count DESC;
        """)

        rows = cur.fetchall()
        if rows:
            print(f"{'Status':<20} {'Count':>10} {'Total MRR':>15}")
            print("-" * 45)
            for row in rows:
                mrr = f"${row[2]:,.2f}" if row[2] else "$0.00"
                print(f"{row[0] or 'NULL':<20} {row[1]:>10,} {mrr:>15}")
        else:
            print("  No subscriptions found")
    except Exception as e:
        print(f"  (Could not check: {e})")
    print()

    # ================================================================
    # 15. ORPHANED RECORDS CHECK
    # ================================================================
    print("## 15. ORPHANED RECORDS CHECK")
    print("-" * 60)

    # Check for transactions without contacts
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM transactions t
            WHERE NOT EXISTS (
                SELECT 1 FROM contacts c WHERE c.id = t.contact_id
            );
        """)
        orphaned_txn = cur.fetchone()[0]
        print(f"Transactions without contacts: {orphaned_txn:,}")
    except Exception as e:
        print(f"  Transactions check failed: {e}")

    # Check for subscriptions without contacts
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM subscriptions s
            WHERE NOT EXISTS (
                SELECT 1 FROM contacts c WHERE c.id = s.contact_id
            );
        """)
        orphaned_sub = cur.fetchone()[0]
        print(f"Subscriptions without contacts: {orphaned_sub:,}")
    except Exception as e:
        print(f"  Subscriptions check failed: {e}")

    print()

    # Cleanup
    cur.close()
    conn.close()

    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    run_audit()
