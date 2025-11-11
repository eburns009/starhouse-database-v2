#!/usr/bin/env python3
"""
Verify Ticket Tailor email consent data and create clean import file for Kajabi.
"""

import csv
from collections import Counter

def analyze_ticket_tailor():
    """Analyze Ticket Tailor consent responses."""

    print("="*80)
    print("TICKET TAILOR EMAIL CONSENT VERIFICATION")
    print("="*80)
    print()

    all_responses = []
    unique_emails = {}  # Track unique emails with their consent

    with open("kajabi 3 files review/ticket_tailor_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = row.get('Email', '').strip().lower()
            consent = row.get('Are you open to receive emails from StarHouse?', '').strip()
            name = row.get('Name', '').strip()
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()

            all_responses.append(consent)

            if email:
                # Keep most recent entry (later rows override)
                unique_emails[email] = {
                    'email': row.get('Email', '').strip(),  # Keep original case
                    'name': name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'consent': consent
                }

    print(f"Total rows in Ticket Tailor file: {len(all_responses):,}")
    print(f"Unique email addresses: {len(unique_emails):,}")
    print()

    # Count consent responses
    consent_counts = Counter(all_responses)
    print("-"*80)
    print("CONSENT RESPONSE BREAKDOWN (all rows)")
    print("-"*80)
    for consent, count in sorted(consent_counts.items()):
        if consent:
            print(f"{consent}: {count:,}")
        else:
            print(f"(Blank): {count:,}")
    print()

    # Unique email consent breakdown
    unique_yes = {email: data for email, data in unique_emails.items() if data['consent'].lower() == 'yes'}
    unique_no = {email: data for email, data in unique_emails.items() if data['consent'].lower() == 'no'}
    unique_blank = {email: data for email, data in unique_emails.items() if not data['consent']}

    print("-"*80)
    print("UNIQUE EMAIL CONSENT BREAKDOWN")
    print("-"*80)
    print(f"Yes: {len(unique_yes):,}")
    print(f"No: {len(unique_no):,}")
    print(f"Blank: {len(unique_blank):,}")
    print(f"TOTAL: {len(unique_emails):,}")
    print()

    return unique_yes

def load_kajabi_subscribed():
    """Load Kajabi subscribed emails."""
    emails = set()
    with open("kajabi 3 files review/1011_email_subscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.add(email)
    return emails

def create_kajabi_import_file():
    """Create clean import file for Kajabi with only new Ticket Tailor opt-ins."""

    print("-"*80)
    print("CREATING KAJABI IMPORT FILE")
    print("-"*80)
    print()

    # Get Ticket Tailor Yes emails
    tt_yes = analyze_ticket_tailor()

    # Get Kajabi subscribed emails
    kajabi_emails = load_kajabi_subscribed()
    print(f"Kajabi subscribed emails: {len(kajabi_emails):,}")
    print()

    # Find emails NOT in Kajabi
    new_emails = {email: data for email, data in tt_yes.items() if email not in kajabi_emails}
    already_in_kajabi = {email: data for email, data in tt_yes.items() if email in kajabi_emails}

    print("-"*80)
    print("TICKET TAILOR 'YES' BREAKDOWN")
    print("-"*80)
    print(f"Total Ticket Tailor 'Yes' emails: {len(tt_yes):,}")
    print(f"  Already in Kajabi subscribed: {len(already_in_kajabi):,}")
    print(f"  NEW (not in Kajabi): {len(new_emails):,}")
    print()

    # Create import file with Name and Email only
    output_file = "kajabi 3 files review/IMPORT_TO_KAJABI_ticket_tailor_new_subscribers.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'Email'])
        writer.writeheader()

        for email in sorted(new_emails.keys()):
            data = new_emails[email]
            writer.writerow({
                'Name': data['name'],
                'Email': data['email']
            })

    print("="*80)
    print("IMPORT FILE CREATED")
    print("="*80)
    print(f"\nFile: {output_file}")
    print(f"Records: {len(new_emails):,}")
    print(f"Columns: Name, Email")
    print()
    print("These are contacts who:")
    print("  ✓ Said 'Yes' to receive emails from StarHouse in Ticket Tailor")
    print("  ✓ Are NOT currently in your Kajabi subscribed list")
    print()

    # Show first 20 records
    print("First 20 records to be imported:")
    print("-"*80)
    print(f"{'Name':<40} {'Email':<50}")
    print("-"*80)
    for i, email in enumerate(sorted(new_emails.keys())[:20], 1):
        data = new_emails[email]
        print(f"{data['name']:<40} {data['email']:<50}")

    if len(new_emails) > 20:
        print(f"... and {len(new_emails) - 20} more")

    print()
    print("="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"\n✓ Ticket Tailor file has {len(tt_yes):,} unique 'Yes' responses")
    print(f"✓ {len(new_emails):,} are new contacts not in Kajabi")
    print(f"✓ Import file ready: {output_file}")
    print()

    return new_emails

if __name__ == '__main__':
    new_contacts = create_kajabi_import_file()
