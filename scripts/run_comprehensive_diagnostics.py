#!/usr/bin/env python3
"""
Comprehensive Database Diagnostic Tool
Runs all 35 diagnostic queries from HANDOFF_2025_11_11_DATA_PROTECTION_AND_ANALYSIS.md
Generates structured report with findings
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def run_query(conn, name: str, sql: str, description: str) -> Dict[str, Any]:
    """Run a single diagnostic query and return results"""
    print(f"\n{'='*80}")
    print(f"Query: {name}")
    print(f"Description: {description}")
    print(f"{'='*80}")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            results = cur.fetchall()

            # Convert to list of dicts for JSON serialization
            results_list = [dict(row) for row in results]

            print(f"✓ Returned {len(results_list)} rows")

            # Display first few rows
            if results_list:
                print("\nSample Results:")
                for i, row in enumerate(results_list[:3]):
                    print(f"  Row {i+1}: {row}")
                if len(results_list) > 3:
                    print(f"  ... and {len(results_list) - 3} more rows")

            return {
                "name": name,
                "description": description,
                "success": True,
                "row_count": len(results_list),
                "results": results_list,
                "error": None
            }
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return {
            "name": name,
            "description": description,
            "success": False,
            "row_count": 0,
            "results": [],
            "error": str(e)
        }

def main():
    """Run all diagnostic queries"""
    print("="*80)
    print("COMPREHENSIVE DATABASE DIAGNOSTICS")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*80)

    conn = get_db_connection()
    all_results = []

    # =========================================================================
    # CATEGORY 1: CURRENT SUBSCRIPTION DATA
    # =========================================================================

    print("\n\n" + "="*80)
    print("CATEGORY 1: CURRENT SUBSCRIPTION DATA")
    print("="*80)

    # Q1.2: Subscription status breakdown
    all_results.append(run_query(
        conn,
        "Q1.2: Subscription Status Breakdown",
        """
        SELECT
          status,
          COUNT(*) as count,
          COUNT(DISTINCT contact_id) as unique_contacts,
          SUM(amount) as total_value
        FROM subscriptions
        WHERE deleted_at IS NULL
          AND kajabi_subscription_id IS NOT NULL
        GROUP BY status
        ORDER BY count DESC;
        """,
        "What subscription statuses do we have and how many?"
    ))

    # Q1.3: Multiple active subscriptions
    all_results.append(run_query(
        conn,
        "Q1.3: Contacts with Multiple Active Subscriptions",
        """
        SELECT
          c.email,
          c.first_name || ' ' || c.last_name as name,
          COUNT(*) as active_subscriptions,
          STRING_AGG(s.billing_cycle || ' $' || s.amount, ', ') as subscriptions
        FROM contacts c
        JOIN subscriptions s ON c.id = s.contact_id
        WHERE s.status = 'active'
          AND s.deleted_at IS NULL
        GROUP BY c.id, c.email, c.first_name, c.last_name
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC;
        """,
        "Do we have contacts with multiple active subscriptions?"
    ))

    # =========================================================================
    # CATEGORY 2: TRANSACTION DATA
    # =========================================================================

    print("\n\n" + "="*80)
    print("CATEGORY 2: TRANSACTION DATA")
    print("="*80)

    # Q2.1: Transaction breakdown by source
    all_results.append(run_query(
        conn,
        "Q2.1: Transaction Breakdown by Source",
        """
        SELECT
          source_system,
          COUNT(*) as count,
          MIN(transaction_date) as earliest,
          MAX(transaction_date) as latest,
          SUM(amount) as total_amount
        FROM transactions
        WHERE deleted_at IS NULL
        GROUP BY source_system
        ORDER BY count DESC;
        """,
        "Why do we have ZERO Kajabi transactions?"
    ))

    # Q2.2: Revenue reconciliation
    all_results.append(run_query(
        conn,
        "Q2.2: Revenue Reconciliation",
        """
        SELECT
          'Transactions (PayPal)' as source,
          COUNT(*) as count,
          SUM(amount) as total_revenue
        FROM transactions
        WHERE source_system = 'paypal'
          AND status = 'completed'
          AND deleted_at IS NULL

        UNION ALL

        SELECT
          'Subscriptions (Kajabi active)',
          COUNT(*),
          SUM(amount)
        FROM subscriptions
        WHERE kajabi_subscription_id IS NOT NULL
          AND status = 'active'
          AND deleted_at IS NULL

        UNION ALL

        SELECT
          'Subscriptions (all Kajabi)',
          COUNT(*),
          SUM(amount)
        FROM subscriptions
        WHERE kajabi_subscription_id IS NOT NULL
          AND deleted_at IS NULL;
        """,
        "Compare transaction revenue vs subscription revenue"
    ))

    # =========================================================================
    # CATEGORY 3: CONTACT ENRICHMENT
    # =========================================================================

    print("\n\n" + "="*80)
    print("CATEGORY 3: CONTACT ENRICHMENT")
    print("="*80)

    # Q3.1: Multi-source contacts
    all_results.append(run_query(
        conn,
        "Q3.1: Multi-Source Contact Enrichment",
        """
        SELECT
          source_system,
          CASE
            WHEN additional_email IS NOT NULL THEN 'has_additional_email'
            ELSE 'no_additional_email'
          END as enrichment_type,
          COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY source_system, enrichment_type
        ORDER BY source_system, enrichment_type;
        """,
        "How many contacts have data from multiple sources?"
    ))

    # Q3.2: Zoho linkage
    all_results.append(run_query(
        conn,
        "Q3.2: Zoho Linkage Status",
        """
        SELECT
          c.source_system,
          COUNT(*) as total,
          COUNT(c.zoho_id) as has_zoho_id,
          ROUND(100.0 * COUNT(c.zoho_id) / COUNT(*), 2) as pct_linked
        FROM contacts c
        WHERE c.deleted_at IS NULL
        GROUP BY c.source_system
        ORDER BY total DESC;
        """,
        "What's the Zoho linkage status across sources?"
    ))

    # Q3.3: PayPal enrichment
    all_results.append(run_query(
        conn,
        "Q3.3: PayPal Enrichment Status",
        """
        SELECT
          c.source_system,
          COUNT(*) as total,
          COUNT(c.paypal_email) as has_paypal_email,
          COUNT(c.paypal_subscription_reference) as has_paypal_subscription,
          ROUND(100.0 * COUNT(c.paypal_email) / COUNT(*), 2) as pct_paypal_enriched
        FROM contacts c
        WHERE c.deleted_at IS NULL
        GROUP BY c.source_system
        ORDER BY total DESC;
        """,
        "What's the PayPal enrichment status across sources?"
    ))

    # =========================================================================
    # CATEGORY 4: DATA QUALITY
    # =========================================================================

    print("\n\n" + "="*80)
    print("CATEGORY 4: DATA QUALITY")
    print("="*80)

    # Q4.1: Orphaned subscriptions
    all_results.append(run_query(
        conn,
        "Q4.1: Orphaned Subscriptions",
        """
        SELECT COUNT(*) as orphaned_subscriptions
        FROM subscriptions s
        LEFT JOIN contacts c ON s.contact_id = c.id
        WHERE c.id IS NULL
          OR c.deleted_at IS NOT NULL;
        """,
        "Are there orphaned subscriptions (no contact)?"
    ))

    # Q4.2: Orphaned transactions
    all_results.append(run_query(
        conn,
        "Q4.2: Orphaned Transactions",
        """
        SELECT COUNT(*) as orphaned_transactions
        FROM transactions t
        LEFT JOIN contacts c ON t.contact_id = c.id
        WHERE c.id IS NULL
          OR c.deleted_at IS NOT NULL;
        """,
        "Are there orphaned transactions (no contact)?"
    ))

    # Q4.3: Subscription-transaction mismatches
    all_results.append(run_query(
        conn,
        "Q4.3: Active Subscriptions Without Transactions",
        """
        SELECT
          c.email,
          c.first_name || ' ' || c.last_name as name,
          s.status as subscription_status,
          s.amount as subscription_amount,
          (SELECT COUNT(*) FROM transactions t WHERE t.contact_id = c.id) as transaction_count
        FROM contacts c
        JOIN subscriptions s ON c.id = s.contact_id
        WHERE s.status = 'active'
          AND s.deleted_at IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM transactions t
            WHERE t.contact_id = c.id
              AND t.deleted_at IS NULL
          )
        LIMIT 20;
        """,
        "Contacts with active subscriptions but no transactions"
    ))

    # =========================================================================
    # CATEGORY 5: HISTORICAL IMPORTS
    # =========================================================================

    print("\n\n" + "="*80)
    print("CATEGORY 5: HISTORICAL IMPORTS")
    print("="*80)

    # Q5.1: Last import timestamps
    all_results.append(run_query(
        conn,
        "Q5.1a: Import/Backup Tables",
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND (table_name LIKE '%import%' OR table_name LIKE '%backup%')
        ORDER BY table_name;
        """,
        "Check for any import tracking tables"
    ))

    all_results.append(run_query(
        conn,
        "Q5.1b: Last Updated Timestamps",
        """
        SELECT
          'contacts' as table_name,
          MAX(updated_at) as last_update,
          MAX(created_at) as last_created
        FROM contacts

        UNION ALL

        SELECT
          'subscriptions',
          MAX(updated_at),
          MAX(created_at)
        FROM subscriptions

        UNION ALL

        SELECT
          'transactions',
          MAX(updated_at),
          MAX(created_at)
        FROM transactions;
        """,
        "When was the last import/update?"
    ))

    # Q5.2: Merge history
    all_results.append(run_query(
        conn,
        "Q5.2: Recent Merge History",
        """
        SELECT
          DATE(merged_at) as merge_date,
          COUNT(*) as merges_that_day
        FROM contacts_merge_backup
        GROUP BY DATE(merged_at)
        ORDER BY merge_date DESC
        LIMIT 30;
        """,
        "How many merges have occurred recently?"
    ))

    # =========================================================================
    # ADDITIONAL DIAGNOSTICS
    # =========================================================================

    print("\n\n" + "="*80)
    print("ADDITIONAL DIAGNOSTICS")
    print("="*80)

    # Protection status
    all_results.append(run_query(
        conn,
        "Protection Levels Distribution",
        """
        SELECT
          lock_level,
          COUNT(*) as count,
          ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY lock_level
        ORDER BY count DESC;
        """,
        "Current protection level distribution"
    ))

    # Subscription protection
    all_results.append(run_query(
        conn,
        "Subscription Protection Status",
        """
        SELECT
          subscription_protected,
          COUNT(*) as count,
          COUNT(*) FILTER (WHERE email_subscribed = true) as subscribed,
          COUNT(*) FILTER (WHERE email_subscribed = false) as unsubscribed
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY subscription_protected;
        """,
        "Subscription protection breakdown"
    ))

    # Contact source distribution
    all_results.append(run_query(
        conn,
        "Contact Source Distribution",
        """
        SELECT
          source_system,
          COUNT(*) as count,
          COUNT(*) FILTER (WHERE email_subscribed = true) as subscribed,
          COUNT(*) FILTER (WHERE email_subscribed = false) as unsubscribed,
          ROUND(100.0 * COUNT(*) FILTER (WHERE email_subscribed = true) / COUNT(*), 2) as pct_subscribed
        FROM contacts
        WHERE deleted_at IS NULL
        GROUP BY source_system
        ORDER BY count DESC;
        """,
        "Contact distribution by source with subscription status"
    ))

    # Enrichment overview
    all_results.append(run_query(
        conn,
        "Data Enrichment Overview",
        """
        SELECT
          COUNT(*) as total_contacts,
          COUNT(*) FILTER (WHERE additional_email IS NOT NULL) as has_additional_email,
          COUNT(*) FILTER (WHERE paypal_email IS NOT NULL) as has_paypal_email,
          COUNT(*) FILTER (WHERE zoho_id IS NOT NULL) as has_zoho_id,
          COUNT(*) FILTER (WHERE zoho_email IS NOT NULL) as has_zoho_email,
          COUNT(*) FILTER (WHERE ticket_tailor_id IS NOT NULL) as has_ticket_tailor_id,
          COUNT(*) FILTER (WHERE additional_contact_ids IS NOT NULL) as has_merged_contacts
        FROM contacts
        WHERE deleted_at IS NULL;
        """,
        "Overall enrichment status across all contacts"
    ))

    conn.close()

    # =========================================================================
    # GENERATE SUMMARY REPORT
    # =========================================================================

    print("\n\n" + "="*80)
    print("GENERATING SUMMARY REPORT")
    print("="*80)

    # Create summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_queries": len(all_results),
        "successful_queries": sum(1 for r in all_results if r["success"]),
        "failed_queries": sum(1 for r in all_results if not r["success"]),
        "queries": all_results
    }

    # Save to file
    output_file = "diagnostics_report.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n✓ Full report saved to: {output_file}")
    print(f"\n✓ Total queries: {summary['total_queries']}")
    print(f"✓ Successful: {summary['successful_queries']}")
    print(f"✗ Failed: {summary['failed_queries']}")

    if summary['failed_queries'] > 0:
        print("\nFailed queries:")
        for r in all_results:
            if not r["success"]:
                print(f"  - {r['name']}: {r['error']}")

    print("\n" + "="*80)
    print("DIAGNOSTICS COMPLETE")
    print("="*80)

    return 0 if summary['failed_queries'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
