#!/usr/bin/env python3
"""
Verify that contacts in the Ticket Tailor import list are NOT in Kajabi's unsubscribed list.
This is critical to ensure we don't import contacts who have previously unsubscribed.
"""

import csv

def load_kajabi_unsubscribed():
    """Load emails from Kajabi unsubscribed list."""
    emails = set()
    with open("kajabi 3 files review/11102025unsubscribed.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.add(email)
    return emails

def load_import_list():
    """Load emails from the import file."""
    emails = {}
    with open("kajabi 3 files review/IMPORT_TO_KAJABI_ticket_tailor_new_subscribers.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            name = row.get('Name', '').strip()
            if email:
                emails[email] = name
    return emails

def verify_import():
    """Verify that import contacts are not in unsubscribed list."""

    print("="*80)
    print("IMPORT LIST VERIFICATION AGAINST UNSUBSCRIBED LIST")
    print("="*80)
    print()

    print("Loading data...")
    kajabi_unsubscribed = load_kajabi_unsubscribed()
    import_contacts = load_import_list()

    print(f"✓ Kajabi unsubscribed: {len(kajabi_unsubscribed):,} emails")
    print(f"✓ Import list: {len(import_contacts):,} contacts")
    print()

    # Find contacts in import list that are also in unsubscribed list
    conflicts = {email: name for email, name in import_contacts.items()
                 if email in kajabi_unsubscribed}

    print("-"*80)
    print("VERIFICATION RESULTS")
    print("-"*80)
    print()

    if conflicts:
        print(f"⚠️  WARNING: Found {len(conflicts)} contacts in BOTH lists!")
        print()
        print("These contacts are in the import file BUT are also in Kajabi's unsubscribed list:")
        print("They should NOT be imported as they have previously unsubscribed.")
        print()
        print(f"{'Email':<45} {'Name':<35}")
        print("-"*80)
        for email, name in sorted(conflicts.items()):
            print(f"{email:<45} {name:<35}")
        print()

        # Calculate safe contacts
        safe_contacts = len(import_contacts) - len(conflicts)
        print("="*80)
        print("RECOMMENDATION")
        print("="*80)
        print(f"\n⚠️  DO NOT IMPORT these {len(conflicts)} contacts - they have unsubscribed")
        print(f"✓ Safe to import: {safe_contacts} contacts")
        print()
        print("Action needed: Remove these contacts from the import file before importing.")
        print()

        # Create a clean import file automatically
        print("Creating clean import file...")
        create_clean_import_file(import_contacts, conflicts)
    else:
        print("✓ VERIFICATION PASSED")
        print()
        print(f"All {len(import_contacts)} contacts in the import list are safe to import.")
        print("None of them appear in Kajabi's unsubscribed list.")
        print()
        print("="*80)
        print("READY TO IMPORT")
        print("="*80)
        print(f"\n✓ File: IMPORT_TO_KAJABI_ticket_tailor_new_subscribers.csv")
        print(f"✓ Contacts: {len(import_contacts)}")
        print(f"✓ Status: All contacts verified - none have unsubscribed")
        print()

def create_clean_import_file(all_contacts, conflicts):
    """Create a clean import file with conflicts removed."""
    clean_contacts = {email: name for email, name in all_contacts.items()
                     if email not in conflicts}

    output_file = "kajabi 3 files review/IMPORT_TO_KAJABI_ticket_tailor_VERIFIED_CLEAN.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'Email'])
        writer.writeheader()
        for email in sorted(clean_contacts.keys()):
            writer.writerow({
                'Name': clean_contacts[email],
                'Email': email
            })

    print(f"\n✓ Clean import file created: {output_file}")
    print(f"✓ Contains {len(clean_contacts)} verified contacts")
    print(f"✓ Removed {len(conflicts)} previously unsubscribed contacts")

if __name__ == '__main__':
    verify_import()
