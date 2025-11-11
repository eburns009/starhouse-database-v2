#!/usr/bin/env python3
"""
Analyze email subscription status across multiple sources:
1. Kajabi subscribed list (1011_email_subscribed.csv)
2. Kajabi unsubscribed list (11102025unsubscribed.csv)
3. Ticket Tailor consent list (ticket_tailor_data.csv)
4. Current database status

Creates a comprehensive report showing:
- Total counts from each source
- Overlaps and discrepancies
- Database vs Kajabi status comparison
- Ticket Tailor opt-ins not in database
"""

import os
import csv
import psycopg2
from typing import Dict, Set, List, Tuple
from collections import defaultdict

def get_db_connection():
    """Get database connection from environment variable."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)

def load_kajabi_subscribed() -> Set[str]:
    """Load emails from Kajabi subscribed list."""
    emails = set()
    file_path = "kajabi 3 files review/1011_email_subscribed.csv"

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.add(email)

    return emails

def load_kajabi_unsubscribed() -> Set[str]:
    """Load emails from Kajabi unsubscribed list."""
    emails = set()
    file_path = "kajabi 3 files review/11102025unsubscribed.csv"

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.add(email)

    return emails

def load_ticket_tailor_consents() -> Dict[str, str]:
    """
    Load emails from Ticket Tailor with consent status.
    Returns dict mapping email -> consent answer.
    """
    consents = {}
    file_path = "kajabi 3 files review/ticket_tailor_data.csv"

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            consent = row.get('Are you open to receive emails from StarHouse?', '').strip()
            if email:
                # Track the most recent consent status (later rows override earlier)
                consents[email] = consent

    return consents

def get_database_status() -> Dict[str, Tuple[bool, int]]:
    """
    Get email subscription status from database.
    Returns dict mapping email -> (email_subscribed, contact_id).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, email, email_subscribed
                FROM contacts
                WHERE email IS NOT NULL AND email != ''
                ORDER BY id
            """)

            status = {}
            for contact_id, email, email_subscribed in cur.fetchall():
                email_lower = email.strip().lower()
                status[email_lower] = (email_subscribed, contact_id)

            return status
    finally:
        conn.close()

def analyze_sources():
    """Perform comprehensive analysis of all email subscription sources."""

    print("=" * 80)
    print("EMAIL SUBSCRIPTION SOURCE ANALYSIS")
    print("=" * 80)
    print()

    # Load all sources
    print("Loading data from all sources...")
    kajabi_subscribed = load_kajabi_subscribed()
    kajabi_unsubscribed = load_kajabi_unsubscribed()
    ticket_tailor_consents = load_ticket_tailor_consents()
    db_status = get_database_status()

    print(f"✓ Loaded {len(kajabi_subscribed):,} emails from Kajabi subscribed list")
    print(f"✓ Loaded {len(kajabi_unsubscribed):,} emails from Kajabi unsubscribed list")
    print(f"✓ Loaded {len(ticket_tailor_consents):,} unique emails from Ticket Tailor")
    print(f"✓ Loaded {len(db_status):,} contacts from database")
    print()

    # Analyze Ticket Tailor consents
    tt_yes = {email for email, consent in ticket_tailor_consents.items()
              if consent.lower() == 'yes'}
    tt_no = {email for email, consent in ticket_tailor_consents.items()
             if consent.lower() == 'no'}
    tt_blank = {email for email, consent in ticket_tailor_consents.items()
                if not consent}

    print("-" * 80)
    print("TICKET TAILOR CONSENT BREAKDOWN")
    print("-" * 80)
    print(f"Yes to emails: {len(tt_yes):,}")
    print(f"No to emails: {len(tt_no):,}")
    print(f"Blank/no answer: {len(tt_blank):,}")
    print()

    # Check for overlaps between Kajabi lists
    overlap = kajabi_subscribed & kajabi_unsubscribed
    print("-" * 80)
    print("KAJABI LIST OVERLAPS")
    print("-" * 80)
    if overlap:
        print(f"⚠️  WARNING: {len(overlap)} emails appear in BOTH subscribed and unsubscribed lists!")
        print("First 10 overlapping emails:")
        for email in sorted(overlap)[:10]:
            print(f"  - {email}")
    else:
        print("✓ No overlaps - lists are mutually exclusive")
    print()

    # Database analysis
    db_subscribed = {email for email, (subscribed, _) in db_status.items() if subscribed}
    db_unsubscribed = {email for email, (subscribed, _) in db_status.items() if not subscribed}

    print("-" * 80)
    print("DATABASE STATUS")
    print("-" * 80)
    print(f"Subscribed (email_subscribed = true): {len(db_subscribed):,}")
    print(f"Unsubscribed (email_subscribed = false): {len(db_unsubscribed):,}")
    print()

    # Compare Kajabi subscribed with database
    print("-" * 80)
    print("KAJABI SUBSCRIBED vs DATABASE")
    print("-" * 80)

    kajabi_sub_in_db = kajabi_subscribed & set(db_status.keys())
    kajabi_sub_not_in_db = kajabi_subscribed - set(db_status.keys())

    print(f"Kajabi subscribed emails in database: {len(kajabi_sub_in_db):,}")
    print(f"Kajabi subscribed emails NOT in database: {len(kajabi_sub_not_in_db):,}")

    # Of those in DB, how many are marked as subscribed?
    kajabi_sub_db_subscribed = kajabi_subscribed & db_subscribed
    kajabi_sub_db_unsubscribed = kajabi_subscribed & db_unsubscribed

    print(f"\nOf Kajabi subscribed emails in database:")
    print(f"  ✓ Marked as subscribed in DB: {len(kajabi_sub_db_subscribed):,}")
    print(f"  ✗ Marked as UNSUBSCRIBED in DB: {len(kajabi_sub_db_unsubscribed):,}")

    if kajabi_sub_db_unsubscribed:
        print(f"\n⚠️  MISMATCH: {len(kajabi_sub_db_unsubscribed)} contacts subscribed in Kajabi but unsubscribed in DB")
        print("First 20 examples:")
        for email in sorted(kajabi_sub_db_unsubscribed)[:20]:
            contact_id = db_status[email][1]
            print(f"  - {email} (ID: {contact_id})")
    print()

    # Compare Kajabi unsubscribed with database
    print("-" * 80)
    print("KAJABI UNSUBSCRIBED vs DATABASE")
    print("-" * 80)

    kajabi_unsub_in_db = kajabi_unsubscribed & set(db_status.keys())
    kajabi_unsub_not_in_db = kajabi_unsubscribed - set(db_status.keys())

    print(f"Kajabi unsubscribed emails in database: {len(kajabi_unsub_in_db):,}")
    print(f"Kajabi unsubscribed emails NOT in database: {len(kajabi_unsub_not_in_db):,}")

    # Of those in DB, how many are marked as unsubscribed?
    kajabi_unsub_db_subscribed = kajabi_unsubscribed & db_subscribed
    kajabi_unsub_db_unsubscribed = kajabi_unsubscribed & db_unsubscribed

    print(f"\nOf Kajabi unsubscribed emails in database:")
    print(f"  ✓ Marked as unsubscribed in DB: {len(kajabi_unsub_db_unsubscribed):,}")
    print(f"  ✗ Marked as SUBSCRIBED in DB: {len(kajabi_unsub_db_subscribed):,}")

    if kajabi_unsub_db_subscribed:
        print(f"\n⚠️  MISMATCH: {len(kajabi_unsub_db_subscribed)} contacts unsubscribed in Kajabi but subscribed in DB")
        print("First 20 examples:")
        for email in sorted(kajabi_unsub_db_subscribed)[:20]:
            contact_id = db_status[email][1]
            print(f"  - {email} (ID: {contact_id})")
    print()

    # Ticket Tailor analysis
    print("-" * 80)
    print("TICKET TAILOR OPT-INS vs DATABASE")
    print("-" * 80)

    tt_yes_in_db = tt_yes & set(db_status.keys())
    tt_yes_not_in_db = tt_yes - set(db_status.keys())

    print(f"Ticket Tailor 'Yes' emails in database: {len(tt_yes_in_db):,}")
    print(f"Ticket Tailor 'Yes' emails NOT in database: {len(tt_yes_not_in_db):,}")

    # Of those in DB, how many are marked as subscribed?
    tt_yes_db_subscribed = tt_yes & db_subscribed
    tt_yes_db_unsubscribed = tt_yes & db_unsubscribed

    print(f"\nOf Ticket Tailor 'Yes' emails in database:")
    print(f"  ✓ Marked as subscribed in DB: {len(tt_yes_db_subscribed):,}")
    print(f"  ✗ Marked as UNSUBSCRIBED in DB: {len(tt_yes_db_unsubscribed):,}")

    if tt_yes_db_unsubscribed:
        print(f"\n⚠️  ATTENTION: {len(tt_yes_db_unsubscribed)} contacts said YES in Ticket Tailor but are unsubscribed in DB")
        print("First 20 examples:")
        for email in sorted(tt_yes_db_unsubscribed)[:20]:
            contact_id = db_status[email][1]
            print(f"  - {email} (ID: {contact_id})")
    print()

    # Summary of total subscription list
    print("=" * 80)
    print("COMPREHENSIVE EMAIL LIST SUMMARY")
    print("=" * 80)

    # All unique emails that should be subscribed
    all_should_subscribe = kajabi_subscribed | tt_yes

    print(f"\nTotal unique emails that SHOULD be subscribed:")
    print(f"  Kajabi subscribed: {len(kajabi_subscribed):,}")
    print(f"  Ticket Tailor 'Yes': {len(tt_yes):,}")
    print(f"  Overlap between Kajabi and TT: {len(kajabi_subscribed & tt_yes):,}")
    print(f"  TOTAL UNIQUE: {len(all_should_subscribe):,}")

    # How many are actually subscribed in DB?
    should_sub_and_are = all_should_subscribe & db_subscribed
    should_sub_but_arent = all_should_subscribe & db_unsubscribed
    should_sub_not_in_db = all_should_subscribe - set(db_status.keys())

    print(f"\nDatabase status of emails that should be subscribed:")
    print(f"  ✓ Actually subscribed in DB: {len(should_sub_and_are):,}")
    print(f"  ✗ NOT subscribed in DB: {len(should_sub_but_arent):,}")
    print(f"  ? Not in database at all: {len(should_sub_not_in_db):,}")

    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if kajabi_sub_db_unsubscribed:
        print(f"\n1. UPDATE {len(kajabi_sub_db_unsubscribed)} contacts from Kajabi subscribed list")
        print("   These are marked as subscribed in Kajabi but unsubscribed in DB")

    if tt_yes_db_unsubscribed:
        print(f"\n2. UPDATE {len(tt_yes_db_unsubscribed)} contacts from Ticket Tailor 'Yes' list")
        print("   These opted in via Ticket Tailor but are unsubscribed in DB")

    if kajabi_sub_not_in_db:
        print(f"\n3. CONSIDER IMPORTING {len(kajabi_sub_not_in_db)} contacts from Kajabi")
        print("   These are subscribed in Kajabi but not in our database")

    if tt_yes_not_in_db:
        print(f"\n4. CONSIDER IMPORTING {len(tt_yes_not_in_db)} contacts from Ticket Tailor")
        print("   These said 'Yes' to emails but are not in our database")

    print()

    # Generate detailed lists for follow-up
    return {
        'kajabi_subscribed': kajabi_subscribed,
        'kajabi_unsubscribed': kajabi_unsubscribed,
        'tt_yes': tt_yes,
        'tt_no': tt_no,
        'db_subscribed': db_subscribed,
        'db_unsubscribed': db_unsubscribed,
        'kajabi_sub_db_unsubscribed': kajabi_sub_db_unsubscribed,
        'kajabi_unsub_db_subscribed': kajabi_unsub_db_subscribed,
        'tt_yes_db_unsubscribed': tt_yes_db_unsubscribed,
        'should_sub_but_arent': should_sub_but_arent,
    }

if __name__ == '__main__':
    results = analyze_sources()
