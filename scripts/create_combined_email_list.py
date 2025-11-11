#!/usr/bin/env python3
"""
Create a combined email subscription list from Kajabi and Ticket Tailor.

Strategy:
1. Kajabi is the main source (subscribed list takes precedence)
2. Add Ticket Tailor "Yes" emails that are NOT already in Kajabi
3. Remove duplicates
4. Report what Ticket Tailor emails are new vs already in Kajabi
"""

import csv
from typing import Set, Dict, Tuple

def load_kajabi_subscribed() -> Dict[str, dict]:
    """Load emails from Kajabi subscribed list with full contact data."""
    contacts = {}
    with open("kajabi 3 files review/1011_email_subscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                contacts[email] = {
                    'email': row.get('Email', '').strip(),
                    'first_name': row.get('First Name', '').strip(),
                    'last_name': row.get('Last Name', '').strip(),
                    'name': row.get('Name', '').strip(),
                    'source': 'Kajabi Subscribed'
                }
    return contacts

def load_ticket_tailor_opt_ins() -> Dict[str, dict]:
    """Load emails that said Yes to email consent in Ticket Tailor."""
    contacts = {}
    with open("kajabi 3 files review/ticket_tailor_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            consent = row.get('Are you open to receive emails from StarHouse?', '').strip()
            if email and consent.lower() == 'yes':
                # Keep most recent entry (later rows override earlier ones)
                contacts[email] = {
                    'email': row.get('Email', '').strip(),
                    'first_name': row.get('First Name', '').strip(),
                    'last_name': row.get('Last Name', '').strip(),
                    'name': row.get('Name', '').strip(),
                    'source': 'Ticket Tailor Yes'
                }
    return contacts

def create_combined_list():
    """Create combined subscription list with Kajabi as primary source."""

    print("="*80)
    print("COMBINED EMAIL SUBSCRIPTION LIST")
    print("="*80)
    print()

    # Load both sources
    print("Loading data...")
    kajabi_contacts = load_kajabi_subscribed()
    tt_contacts = load_ticket_tailor_opt_ins()

    print(f"✓ Kajabi subscribed: {len(kajabi_contacts):,} unique emails")
    print(f"✓ Ticket Tailor 'Yes': {len(tt_contacts):,} unique emails")
    print()

    # Find overlaps and unique emails
    kajabi_emails = set(kajabi_contacts.keys())
    tt_emails = set(tt_contacts.keys())

    overlap = kajabi_emails & tt_emails
    tt_only = tt_emails - kajabi_emails

    print("-"*80)
    print("OVERLAP ANALYSIS")
    print("-"*80)
    print(f"Emails in BOTH Kajabi and Ticket Tailor: {len(overlap):,}")
    print(f"Ticket Tailor emails NOT in Kajabi: {len(tt_only):,}")
    print()

    # Create combined list: Kajabi + unique TT emails
    combined = {}

    # Add all Kajabi contacts
    for email, contact in kajabi_contacts.items():
        combined[email] = contact.copy()

    # Add Ticket Tailor contacts that are NOT in Kajabi
    for email in tt_only:
        combined[email] = tt_contacts[email].copy()
        combined[email]['source'] = 'Ticket Tailor Yes (NEW - not in Kajabi)'

    print("-"*80)
    print("COMBINED LIST SUMMARY")
    print("-"*80)
    print(f"Total unique subscribed emails: {len(combined):,}")
    print(f"  - From Kajabi: {len(kajabi_contacts):,}")
    print(f"  - From Ticket Tailor (new): {len(tt_only):,}")
    print()

    # Export combined list
    output_file = "kajabi 3 files review/combined_email_subscription_list.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['email', 'first_name', 'last_name', 'name', 'source'])
        writer.writeheader()
        for email in sorted(combined.keys()):
            writer.writerow(combined[email])

    print(f"✓ Combined list exported to: {output_file}")
    print()

    # Export Ticket Tailor emails NOT in Kajabi (for detailed review)
    tt_new_file = "kajabi 3 files review/ticket_tailor_new_emails_not_in_kajabi.csv"
    with open(tt_new_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['email', 'first_name', 'last_name', 'name'])
        writer.writeheader()
        for email in sorted(tt_only):
            contact = tt_contacts[email]
            writer.writerow({
                'email': contact['email'],
                'first_name': contact['first_name'],
                'last_name': contact['last_name'],
                'name': contact['name']
            })

    print(f"✓ New Ticket Tailor emails exported to: {tt_new_file}")
    print()

    # Export overlap for reference
    overlap_file = "kajabi 3 files review/emails_in_both_kajabi_and_ticket_tailor.csv"
    with open(overlap_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['email', 'kajabi_name', 'tt_name'])
        writer.writeheader()
        for email in sorted(overlap):
            writer.writerow({
                'email': email,
                'kajabi_name': kajabi_contacts[email]['name'],
                'tt_name': tt_contacts[email]['name']
            })

    print(f"✓ Overlap list exported to: {overlap_file}")
    print()

    # Detailed breakdown of Ticket Tailor emails
    print("-"*80)
    print("TICKET TAILOR EMAIL BREAKDOWN")
    print("-"*80)
    print(f"\nOf {len(tt_emails):,} Ticket Tailor 'Yes' emails:")
    print(f"  - Already in Kajabi subscribed: {len(overlap):,} ({len(overlap)/len(tt_emails)*100:.1f}%)")
    print(f"  - NEW (not in Kajabi): {len(tt_only):,} ({len(tt_only)/len(tt_emails)*100:.1f}%)")
    print()

    if tt_only:
        print("First 20 NEW Ticket Tailor emails (not in Kajabi):")
        for i, email in enumerate(sorted(tt_only)[:20], 1):
            contact = tt_contacts[email]
            print(f"  {i:2d}. {contact['email']:<40} {contact['name']}")
        if len(tt_only) > 20:
            print(f"  ... and {len(tt_only) - 20} more")
    print()

    print("="*80)
    print("FILES GENERATED")
    print("="*80)
    print(f"\n1. {output_file}")
    print(f"   Combined subscription list ({len(combined):,} emails)")
    print(f"   Kajabi as primary source + unique Ticket Tailor opt-ins\n")

    print(f"2. {tt_new_file}")
    print(f"   Ticket Tailor emails NOT in Kajabi ({len(tt_only):,} emails)")
    print(f"   These are new opt-ins from Ticket Tailor events\n")

    print(f"3. {overlap_file}")
    print(f"   Emails that appear in BOTH sources ({len(overlap):,} emails)")
    print(f"   For verification/reconciliation purposes\n")

    return {
        'combined': combined,
        'tt_only': tt_only,
        'overlap': overlap
    }

if __name__ == '__main__':
    results = create_combined_list()
