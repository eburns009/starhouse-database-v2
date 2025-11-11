#!/usr/bin/env python3
"""
Analyze new import files and predict impact on database.

Shows:
- How many new contacts
- How many updates to existing contacts
- What data would be overwritten
- Subscription status changes
"""

import csv
import sys
import os
from typing import Dict, Set, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url

DB_CONNECTION = get_database_url()

def normalize_email(email: str) -> str:
    """Normalize email for comparison."""
    if not email:
        return ''
    return email.strip().lower()

def analyze_kajabi_import(filepath: str) -> Dict:
    """Analyze what would happen if we import Kajabi file."""
    print(f"\n{'='*80}")
    print(f"  ANALYZING KAJABI IMPORT: {os.path.basename(filepath)}")
    print(f"{'='*80}\n")

    # Load Kajabi data
    kajabi_emails = set()
    kajabi_contacts = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = normalize_email(row.get('Email', ''))
            if email:
                kajabi_emails.add(email)
                kajabi_contacts[email] = {
                    'first_name': row.get('First Name', ''),
                    'last_name': row.get('Last Name', ''),
                    'phone': row.get('Phone Number (phone_number)', ''),
                    'kajabi_id': row.get('ID', ''),
                }

    print(f"📊 Kajabi file: {len(kajabi_emails):,} contacts\n")

    # Connect to database
    conn = psycopg2.connect(DB_CONNECTION)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get current contacts
    cur.execute("""
        SELECT
            id,
            email,
            first_name,
            last_name,
            phone,
            source_system,
            email_subscribed,
            kajabi_id,
            zoho_id,
            paypal_email,
            additional_email,
            (additional_email IS NOT NULL) as was_merged
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    db_contacts = {normalize_email(row['email']): row for row in cur.fetchall()}

    print(f"📊 Database: {len(db_contacts):,} contacts\n")

    # Analysis
    new_contacts = []
    updates = []
    would_overwrite_source = []
    would_overwrite_enriched = []

    for email in kajabi_emails:
        if email not in db_contacts:
            new_contacts.append(email)
        else:
            db_contact = db_contacts[email]
            updates.append(email)

            # Check if source_system would be overwritten
            if db_contact['source_system'] and db_contact['source_system'] != 'kajabi':
                would_overwrite_source.append({
                    'email': email,
                    'current_source': db_contact['source_system'],
                    'was_merged': db_contact['was_merged']
                })

            # Check if enriched data would be lost
            has_enriched = (
                db_contact['zoho_id'] or
                db_contact['paypal_email'] or
                db_contact['additional_email'] or
                db_contact['was_merged']
            )
            if has_enriched:
                would_overwrite_enriched.append({
                    'email': email,
                    'zoho_id': bool(db_contact['zoho_id']),
                    'paypal_email': bool(db_contact['paypal_email']),
                    'additional_email': bool(db_contact['additional_email']),
                    'was_merged': db_contact['was_merged']
                })

    # Contacts in DB but not in new Kajabi export
    removed_from_kajabi = [
        email for email in db_contacts.keys()
        if email not in kajabi_emails and db_contacts[email]['kajabi_id']
    ]

    # Print results
    print(f"📈 NEW CONTACTS (would be added):")
    print(f"   {len(new_contacts):,} contacts\n")

    print(f"🔄 UPDATES (existing contacts):")
    print(f"   {len(updates):,} contacts would be updated\n")

    print(f"⚠️  SOURCE SYSTEM OVERWRITES:")
    print(f"   {len(would_overwrite_source):,} contacts would have source_system changed to 'kajabi'")
    if would_overwrite_source:
        print(f"\n   Examples:")
        for item in would_overwrite_source[:5]:
            merged = " (MERGED)" if item['was_merged'] else ""
            print(f"   - {item['email']}: {item['current_source']} → kajabi{merged}")
        if len(would_overwrite_source) > 5:
            print(f"   ... and {len(would_overwrite_source) - 5} more")
    print()

    print(f"🔧 ENRICHED DATA AT RISK:")
    print(f"   {len(would_overwrite_enriched):,} contacts have enriched data that could be affected")
    if would_overwrite_enriched:
        print(f"\n   Breakdown:")
        print(f"   - Zoho linked: {sum(1 for x in would_overwrite_enriched if x['zoho_id'])}")
        print(f"   - PayPal enriched: {sum(1 for x in would_overwrite_enriched if x['paypal_email'])}")
        print(f"   - Additional emails: {sum(1 for x in would_overwrite_enriched if x['additional_email'])}")
        print(f"   - From merges: {sum(1 for x in would_overwrite_enriched if x['was_merged'])}")
    print()

    print(f"❌ REMOVED FROM KAJABI:")
    print(f"   {len(removed_from_kajabi):,} contacts with kajabi_id are NOT in new export")
    if removed_from_kajabi:
        print(f"\n   Examples:")
        for email in removed_from_kajabi[:5]:
            print(f"   - {email}")
        if len(removed_from_kajabi) > 5:
            print(f"   ... and {len(removed_from_kajabi) - 5} more")
    print()

    conn.close()

    return {
        'total_in_file': len(kajabi_emails),
        'new_contacts': len(new_contacts),
        'updates': len(updates),
        'would_overwrite_source': len(would_overwrite_source),
        'would_overwrite_enriched': len(would_overwrite_enriched),
        'removed_from_kajabi': len(removed_from_kajabi),
    }


def analyze_ticket_tailor_import(filepath: str) -> Dict:
    """Analyze what would happen if we import Ticket Tailor file."""
    print(f"\n{'='*80}")
    print(f"  ANALYZING TICKET TAILOR IMPORT: {os.path.basename(filepath)}")
    print(f"{'='*80}\n")

    # Load Ticket Tailor data
    tt_emails = set()
    tt_contacts = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = normalize_email(row.get('Email', ''))
            if email:
                tt_emails.add(email)
                tt_contacts[email] = {
                    'first_name': row.get('First Name', ''),
                    'last_name': row.get('Last Name', ''),
                    'phone': row.get('Mobile number', ''),
                    'order_id': row.get('Order ID', ''),
                    'event_name': row.get('Event name', ''),
                    'opted_in': row.get('Are you open to receive emails from StarHouse?', '').lower() == 'yes',
                }

    print(f"📊 Ticket Tailor file: {len(tt_emails):,} contacts\n")

    # Connect to database
    conn = psycopg2.connect(DB_CONNECTION)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get current contacts
    cur.execute("""
        SELECT
            id,
            email,
            source_system,
            email_subscribed
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    db_contacts = {normalize_email(row['email']): row for row in cur.fetchall()}

    # Analysis
    new_contacts = []
    updates = []
    new_opt_ins = 0

    for email in tt_emails:
        contact_info = tt_contacts[email]
        if email not in db_contacts:
            new_contacts.append(email)
            if contact_info['opted_in']:
                new_opt_ins += 1
        else:
            updates.append(email)
            # If they opted in and aren't currently subscribed, that's a new opt-in
            if contact_info['opted_in'] and not db_contacts[email]['email_subscribed']:
                new_opt_ins += 1

    print(f"📈 NEW CONTACTS (would be added):")
    print(f"   {len(new_contacts):,} contacts")
    print(f"   {new_opt_ins} new opt-ins\n")

    print(f"🔄 UPDATES (existing contacts):")
    print(f"   {len(updates):,} contacts already in database\n")

    conn.close()

    return {
        'total_in_file': len(tt_emails),
        'new_contacts': len(new_contacts),
        'updates': len(updates),
        'new_opt_ins': new_opt_ins,
    }


def main():
    kajabi_file = "kajabi 3 files review/11102025kajabi.csv"
    tt_file = "kajabi 3 files review/ticket tailor export.csv"

    print("="*80)
    print("  IMPORT IMPACT ANALYSIS")
    print("="*80)

    # Analyze Kajabi
    kajabi_stats = analyze_kajabi_import(kajabi_file)

    # Analyze Ticket Tailor
    tt_stats = analyze_ticket_tailor_import(tt_file)

    # Summary
    print(f"\n{'='*80}")
    print(f"  SUMMARY & RECOMMENDATIONS")
    print(f"{'='*80}\n")

    print("📊 IMPACT SUMMARY:\n")
    print(f"Kajabi Import:")
    print(f"  ✅ {kajabi_stats['new_contacts']:,} new contacts")
    print(f"  🔄 {kajabi_stats['updates']:,} updates")
    print(f"  ⚠️  {kajabi_stats['would_overwrite_source']:,} source system overwrites")
    print(f"  🔧 {kajabi_stats['would_overwrite_enriched']:,} enriched contacts affected")
    print(f"  ❌ {kajabi_stats['removed_from_kajabi']:,} removed from Kajabi\n")

    print(f"Ticket Tailor Import:")
    print(f"  ✅ {tt_stats['new_contacts']:,} new contacts")
    print(f"  📧 {tt_stats['new_opt_ins']} new opt-ins")
    print(f"  🔄 {tt_stats['updates']:,} already in database\n")

    print("🎯 RECOMMENDATION:\n")

    if kajabi_stats['would_overwrite_source'] > 0 or kajabi_stats['would_overwrite_enriched'] > 0:
        print("⚠️  DANGER: Current import script will DESTROY enriched data!")
        print()
        print("You need a PROTECTED IMPORT that:")
        print("  1. Creates NEW contacts from Kajabi")
        print("  2. Updates ONLY Kajabi-specific fields (kajabi_id, kajabi_member_id)")
        print("  3. NEVER overwrites source_system from other sources")
        print("  4. PRESERVES all enriched data (zoho_id, paypal_email, etc.)")
        print()
        print("I can create this protected import script for you.")
    else:
        print("✅ Safe to import - no enriched data at risk")

    print()


if __name__ == '__main__':
    main()
