#!/usr/bin/env python3
"""
Generate SQL scripts to fix email subscription discrepancies found in analysis.
"""

import os
import csv
import psycopg2
from typing import Set, Dict, Tuple

def get_db_connection():
    """Get database connection from environment variable."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)

def load_kajabi_subscribed() -> Set[str]:
    """Load emails from Kajabi subscribed list."""
    emails = set()
    with open("kajabi 3 files review/1011_email_subscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.add(email)
    return emails

def load_kajabi_unsubscribed() -> Set[str]:
    """Load emails from Kajabi unsubscribed list."""
    emails = set()
    with open("kajabi 3 files review/11102025unsubscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.add(email)
    return emails

def load_ticket_tailor_opt_ins() -> Set[str]:
    """Load emails that said Yes to email consent in Ticket Tailor."""
    emails = set()
    with open("kajabi 3 files review/ticket_tailor_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            consent = row.get('Are you open to receive emails from StarHouse?', '').strip()
            if email and consent.lower() == 'yes':
                emails.add(email)
    return emails

def get_database_status() -> Dict[str, Tuple[bool, int]]:
    """Get email subscription status from database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, email, email_subscribed
                FROM contacts
                WHERE email IS NOT NULL AND email != ''
            """)
            status = {}
            for contact_id, email, email_subscribed in cur.fetchall():
                email_lower = email.strip().lower()
                status[email_lower] = (email_subscribed, contact_id)
            return status
    finally:
        conn.close()

def generate_sql_scripts():
    """Generate SQL scripts to fix discrepancies."""

    print("Loading data...")
    kajabi_subscribed = load_kajabi_subscribed()
    kajabi_unsubscribed = load_kajabi_unsubscribed()
    tt_opt_ins = load_ticket_tailor_opt_ins()
    db_status = get_database_status()

    db_subscribed = {email for email, (subscribed, _) in db_status.items() if subscribed}
    db_unsubscribed = {email for email, (subscribed, _) in db_status.items() if not subscribed}

    # Find discrepancies
    # 1. Unsubscribed in Kajabi but subscribed in DB (CRITICAL)
    kajabi_unsub_db_subscribed = kajabi_unsubscribed & db_subscribed

    # 2. Subscribed in Kajabi but unsubscribed in DB
    kajabi_sub_db_unsubscribed = kajabi_subscribed & db_unsubscribed

    # 3. Ticket Tailor Yes but unsubscribed in DB
    tt_yes_db_unsubscribed = tt_opt_ins & db_unsubscribed

    # Note: heidi@heidirose.com appears in both lists 2 and 3, so we need to deduplicate
    should_subscribe = (kajabi_sub_db_unsubscribed | tt_yes_db_unsubscribed)

    print(f"\nFound {len(kajabi_unsub_db_subscribed)} emails to mark as UNSUBSCRIBED")
    print(f"Found {len(should_subscribe)} emails to mark as SUBSCRIBED")

    # Generate Script 1: Respect unsubscribe preferences
    with open("scripts/fix_email_subscriptions_respect_unsubscribes.sql", "w") as f:
        f.write("""-- CRITICAL: Respect Unsubscribe Preferences
--
-- These contacts unsubscribed in Kajabi but are still marked as subscribed in our database.
-- We must honor their unsubscribe preference for legal compliance (CAN-SPAM, GDPR).
--
-- Count: {count} contacts
-- Generated: 2025-11-11
--
-- IMPORTANT: Review these changes before executing in production.

BEGIN;

-- Mark as unsubscribed
UPDATE contacts
SET
    email_subscribed = false,
    updated_at = NOW()
WHERE LOWER(email) IN (
{emails}
)
AND email_subscribed = true;

-- Verify the update
SELECT
    COUNT(*) as updated_count,
    'Should be {count}' as expected
FROM contacts
WHERE LOWER(email) IN (
{emails}
);

-- Uncomment to commit:
-- COMMIT;

-- Or rollback if something looks wrong:
ROLLBACK;
""".format(
            count=len(kajabi_unsub_db_subscribed),
            emails=",\n".join(f"    '{email}'" for email in sorted(kajabi_unsub_db_subscribed))
        ))

    # Generate Script 2: Honor opt-ins
    with open("scripts/fix_email_subscriptions_honor_opt_ins.sql", "w") as f:
        f.write("""-- Honor Opt-in Preferences
--
-- These contacts are subscribed in Kajabi or said "Yes" to email consent in Ticket Tailor,
-- but are currently marked as unsubscribed in our database.
--
-- Count: {count} contacts
-- Generated: 2025-11-11
--
-- IMPORTANT: Review these changes before executing in production.

BEGIN;

-- Mark as subscribed
UPDATE contacts
SET
    email_subscribed = true,
    updated_at = NOW()
WHERE LOWER(email) IN (
{emails}
)
AND email_subscribed = false;

-- Verify the update
SELECT
    COUNT(*) as updated_count,
    'Should be {count}' as expected
FROM contacts
WHERE LOWER(email) IN (
{emails}
);

-- Show the contacts being updated
SELECT
    id,
    email,
    first_name,
    last_name,
    CASE
        WHEN LOWER(email) IN ({kajabi_list}) THEN 'Kajabi Subscribed'
        ELSE ''
    END as kajabi_status,
    CASE
        WHEN LOWER(email) IN ({tt_list}) THEN 'Ticket Tailor Yes'
        ELSE ''
    END as tt_status
FROM contacts
WHERE LOWER(email) IN (
{emails}
)
ORDER BY email;

-- Uncomment to commit:
-- COMMIT;

-- Or rollback if something looks wrong:
ROLLBACK;
""".format(
            count=len(should_subscribe),
            emails=",\n".join(f"    '{email}'" for email in sorted(should_subscribe)),
            kajabi_list=", ".join(f"'{email}'" for email in sorted(kajabi_sub_db_unsubscribed)),
            tt_list=", ".join(f"'{email}'" for email in sorted(tt_yes_db_unsubscribed))
        ))

    print("\n✓ Generated scripts/fix_email_subscriptions_respect_unsubscribes.sql")
    print("✓ Generated scripts/fix_email_subscriptions_honor_opt_ins.sql")

    # Generate detailed CSV exports for review
    with open("scripts/emails_to_unsubscribe.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'contact_id', 'source'])
        for email in sorted(kajabi_unsub_db_subscribed):
            contact_id = db_status[email][1]
            writer.writerow([email, contact_id, 'Kajabi Unsubscribed'])

    with open("scripts/emails_to_subscribe.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'contact_id', 'source'])
        for email in sorted(should_subscribe):
            contact_id = db_status[email][1]
            sources = []
            if email in kajabi_sub_db_unsubscribed:
                sources.append('Kajabi Subscribed')
            if email in tt_yes_db_unsubscribed:
                sources.append('Ticket Tailor Yes')
            writer.writerow([email, contact_id, ' + '.join(sources)])

    print("\n✓ Generated scripts/emails_to_unsubscribe.csv (for review)")
    print("✓ Generated scripts/emails_to_subscribe.csv (for review)")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review the CSV files to verify the lists are correct")
    print("2. Review the SQL scripts")
    print("3. Execute scripts in order:")
    print("   a. fix_email_subscriptions_respect_unsubscribes.sql (PRIORITY 1)")
    print("   b. fix_email_subscriptions_honor_opt_ins.sql")
    print("\nIMPORTANT: Each script uses transactions with ROLLBACK by default.")
    print("Change ROLLBACK to COMMIT after verifying the results.")

if __name__ == '__main__':
    generate_sql_scripts()
