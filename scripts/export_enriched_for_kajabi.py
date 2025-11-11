#!/usr/bin/env python3
"""
Export ALL enriched contact data for Kajabi import.
This includes corrected addresses, enriched names, phones, and all other fields.
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, List

def get_db_connection():
    """Get database connection from environment."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def export_for_kajabi_import(conn, output_path: str) -> None:
    """
    Export all contacts that exist in Kajabi with enriched/corrected data.
    Format: Kajabi-compatible CSV for bulk import.
    """
    print("Exporting enriched contacts for Kajabi import...")

    cursor = conn.cursor(cursor_factory=DictCursor)

    # Get all contacts that have Kajabi IDs (these exist in Kajabi)
    cursor.execute("""
        SELECT
            kajabi_id,
            email,
            first_name,
            last_name,
            phone,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country,
            source_system,
            paypal_email,
            paypal_first_name,
            paypal_last_name,
            zoho_id
        FROM contacts
        WHERE kajabi_id IS NOT NULL
        ORDER BY email
    """)

    contacts = cursor.fetchall()
    cursor.close()

    print(f"Found {len(contacts)} contacts with Kajabi IDs")

    # Write Kajabi-compatible CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Kajabi import header (must match exact field names)
        writer.writerow([
            'ID',  # Kajabi ID for matching existing records
            'Email',
            'First Name',
            'Last Name',
            'Phone Number (phone_number)',
            'Address (address_line_1)',
            'Address Line 2 (address_line_2)',
            'City (address_city)',
            'State (address_state)',
            'Zip Code (address_zip)',
            'Country (address_country)'
        ])

        # Write each contact
        for row in contacts:
            writer.writerow([
                row['kajabi_id'],
                row['email'],
                row['first_name'] or '',
                row['last_name'] or '',
                row['phone'] or '',
                row['address_line_1'] or '',
                row['address_line_2'] or '',
                row['city'] or '',
                row['state'] or '',
                row['postal_code'] or '',
                row['country'] or ''
            ])

    print(f"✅ Export complete: {output_path}")
    print(f"   Records exported: {len(contacts)}")
    return len(contacts)

def export_new_contacts_only(conn, output_path: str) -> None:
    """
    Export contacts that exist in database but NOT in Kajabi.
    These would be new contacts to add to Kajabi.
    """
    print("\nExporting new contacts (not in Kajabi)...")

    cursor = conn.cursor(cursor_factory=DictCursor)

    # Get contacts without Kajabi IDs
    cursor.execute("""
        SELECT
            email,
            first_name,
            last_name,
            phone,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            country,
            source_system,
            paypal_email,
            zoho_id
        FROM contacts
        WHERE kajabi_id IS NULL
        AND email IS NOT NULL
        AND email != ''
        ORDER BY email
    """)

    contacts = cursor.fetchall()
    cursor.close()

    print(f"Found {len(contacts)} new contacts not in Kajabi")

    if len(contacts) == 0:
        print("No new contacts to export")
        return 0

    # Write Kajabi-compatible CSV (no ID field, these are new)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Kajabi import header for new contacts
        writer.writerow([
            'Email',
            'First Name',
            'Last Name',
            'Phone Number (phone_number)',
            'Address (address_line_1)',
            'Address Line 2 (address_line_2)',
            'City (address_city)',
            'State (address_state)',
            'Zip Code (address_zip)',
            'Country (address_country)'
        ])

        # Write each contact
        for row in contacts:
            writer.writerow([
                row['email'],
                row['first_name'] or '',
                row['last_name'] or '',
                row['phone'] or '',
                row['address_line_1'] or '',
                row['address_line_2'] or '',
                row['city'] or '',
                row['state'] or '',
                row['postal_code'] or '',
                row['country'] or ''
            ])

    print(f"✅ Export complete: {output_path}")
    print(f"   Records exported: {len(contacts)}")
    return len(contacts)

def generate_summary_report(conn, kajabi_count: int, new_count: int, output_path: str) -> None:
    """Generate summary report of export."""
    print("\nGenerating summary report...")

    cursor = conn.cursor(cursor_factory=DictCursor)

    # Get statistics
    cursor.execute("""
        SELECT
            COUNT(*) FILTER (WHERE kajabi_id IS NOT NULL) as with_kajabi_id,
            COUNT(*) FILTER (WHERE kajabi_id IS NULL) as without_kajabi_id,
            COUNT(*) FILTER (WHERE paypal_email IS NOT NULL) as enriched_from_paypal,
            COUNT(*) FILTER (WHERE zoho_id IS NOT NULL) as linked_to_zoho,
            COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone != '') as with_phone,
            COUNT(*) FILTER (WHERE city IS NOT NULL AND city != '') as with_city
        FROM contacts
    """)

    stats = cursor.fetchone()
    cursor.close()

    with open(output_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("KAJABI EXPORT SUMMARY\n")
        f.write("="*80 + "\n\n")

        f.write("EXPORT FILES GENERATED:\n")
        f.write("-"*80 + "\n")
        f.write(f"1. kajabi_full_enriched_export.csv ({kajabi_count} records)\n")
        f.write(f"   - All contacts that exist in Kajabi\n")
        f.write(f"   - Includes all enriched/corrected data\n")
        f.write(f"   - Ready for Kajabi bulk update import\n\n")

        f.write(f"2. kajabi_new_contacts_only.csv ({new_count} records)\n")
        f.write(f"   - Contacts in database but not in Kajabi\n")
        f.write(f"   - Optional: import these as new contacts\n")
        f.write(f"   - May include PayPal-only contacts\n\n")

        f.write("DATABASE STATISTICS:\n")
        f.write("-"*80 + "\n")
        f.write(f"Contacts with Kajabi ID: {stats['with_kajabi_id']}\n")
        f.write(f"Contacts without Kajabi ID: {stats['without_kajabi_id']}\n")
        f.write(f"Enriched from PayPal: {stats['enriched_from_paypal']}\n")
        f.write(f"Linked to Zoho: {stats['linked_to_zoho']}\n")
        f.write(f"With phone numbers: {stats['with_phone']}\n")
        f.write(f"With city data: {stats['with_city']}\n\n")

        f.write("IMPORT INSTRUCTIONS:\n")
        f.write("-"*80 + "\n")
        f.write("1. In Kajabi, go to Contacts > Import\n")
        f.write("2. Upload: kajabi_full_enriched_export.csv\n")
        f.write("3. Map fields to match column headers\n")
        f.write("4. Select 'Update existing contacts by ID'\n")
        f.write("5. Run import\n")
        f.write("6. Verify data in Kajabi UI\n")
        f.write("7. Re-export contacts from Kajabi\n")
        f.write("8. Run next weekly import with clean Kajabi data\n\n")

        f.write("WHAT THIS EXPORT INCLUDES:\n")
        f.write("-"*80 + "\n")
        f.write("✅ Corrected addresses (city capitalization, address_line_2 cleanup)\n")
        f.write("✅ Enriched names from PayPal\n")
        f.write("✅ Validated phone numbers\n")
        f.write("✅ All duplicate merge results\n")
        f.write("✅ Cross-system enrichment (PayPal, Zoho, Ticket Tailor)\n\n")

        f.write("="*80 + "\n")

    print(f"✅ Summary report saved: {output_path}")

def main() -> None:
    """Main export function."""
    export_dir = "/workspaces/starhouse-database-v2/data/current"

    # Output paths
    kajabi_export = os.path.join(export_dir, "kajabi_full_enriched_export.csv")
    new_contacts_export = os.path.join(export_dir, "kajabi_new_contacts_only.csv")
    summary_report = os.path.join(export_dir, "kajabi_export_summary.txt")

    try:
        conn = get_db_connection()

        print("="*80)
        print("EXPORTING ENRICHED DATA FOR KAJABI")
        print("="*80)
        print()

        # Export existing Kajabi contacts with enriched data
        kajabi_count = export_for_kajabi_import(conn, kajabi_export)

        # Export new contacts not in Kajabi
        new_count = export_new_contacts_only(conn, new_contacts_export)

        # Generate summary
        generate_summary_report(conn, kajabi_count, new_count, summary_report)

        conn.close()

        print("\n" + "="*80)
        print("EXPORT COMPLETE")
        print("="*80)
        print(f"\nFiles generated:")
        print(f"1. {kajabi_export}")
        print(f"   → Import this to Kajabi to update existing contacts")
        print(f"\n2. {new_contacts_export}")
        print(f"   → Optional: import new contacts from PayPal/other sources")
        print(f"\n3. {summary_report}")
        print(f"   → Read this for import instructions")
        print("\n" + "="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
