#!/usr/bin/env python3
"""
COMPREHENSIVE DATA SOURCE AUDIT
================================

Purpose: Understand what we have from ALL sources and identify the mess

Sources to audit:
1. Kajabi (membership platform)
2. PayPal (payments)
3. Ticket Tailor (event tickets)
4. Zoho (old CRM)
5. QuickBooks (accounting)
6. MailChimp (email marketing)
"""

import os
from supabase import create_client
from collections import defaultdict

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=" * 100)
print("COMPREHENSIVE DATA SOURCE AUDIT")
print("=" * 100)

# Get all contacts with source information
response = supabase.table('contacts').select(
    'id, email, first_name, last_name, '
    'kajabi_id, zoho_id, ticket_tailor_id, quickbooks_id, mailchimp_id, '
    'paypal_email, paypal_payer_id, '
    'source_system, created_at, deleted_at'
).is_('deleted_at', 'null').execute()

contacts = response.data
total_contacts = len(contacts)

print(f"\n📊 TOTAL CONTACTS: {total_contacts}")
print("=" * 100)

# Analyze by source
source_counts = defaultdict(int)
source_examples = defaultdict(list)

for contact in contacts:
    sources = []

    if contact.get('kajabi_id'):
        sources.append('kajabi')
    if contact.get('zoho_id'):
        sources.append('zoho')
    if contact.get('ticket_tailor_id'):
        sources.append('ticket_tailor')
    if contact.get('quickbooks_id'):
        sources.append('quickbooks')
    if contact.get('mailchimp_id'):
        sources.append('mailchimp')
    if contact.get('paypal_payer_id'):
        sources.append('paypal')

    # Count by primary source
    primary_source = contact.get('source_system', 'unknown')
    source_counts[primary_source] += 1

    # Track multi-source contacts
    if len(sources) > 1:
        key = '+'.join(sorted(sources))
        source_counts[f"MULTI: {key}"] += 1
        if len(source_examples[key]) < 3:
            source_examples[key].append(contact.get('email'))

print("\n1️⃣  CONTACTS BY PRIMARY SOURCE")
print("-" * 100)
for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
    if not source.startswith('MULTI'):
        print(f"  {source:20} {count:6,} contacts")

print("\n2️⃣  CONTACTS WITH MULTIPLE SOURCE IDs (POTENTIAL DUPLICATES)")
print("-" * 100)
for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
    if source.startswith('MULTI'):
        print(f"  {source:40} {count:6,} contacts")
        key = source.replace('MULTI: ', '')
        if source_examples[key]:
            print(f"      Examples: {', '.join(source_examples[key][:3])}")

# Analyze what each source provides
print("\n3️⃣  WHAT EACH SOURCE PROVIDES")
print("-" * 100)

print("\n  📱 KAJABI (Membership Platform)")
kajabi_count = sum(1 for c in contacts if c.get('kajabi_id'))
print(f"     Contacts: {kajabi_count:,}")
print(f"     Provides: Names, Email, Member ID, Subscription data, Tags, Products")
print(f"     Status: ✅ ACTIVE - Primary source of truth")

print("\n  💳 PAYPAL (Payment Processor)")
paypal_count = sum(1 for c in contacts if c.get('paypal_payer_id'))
print(f"     Contacts: {paypal_count:,}")
print(f"     Provides: Payer ID, Business names, Transactions, Subscription IDs")
print(f"     Status: ✅ ACTIVE - Payment tracking")

print("\n  🎫 TICKET TAILOR (Event Tickets)")
tt_count = sum(1 for c in contacts if c.get('ticket_tailor_id'))
print(f"     Contacts: {tt_count:,}")
print(f"     Provides: Event attendees, Ticket purchases")
print(f"     Status: ✅ ACTIVE - Event management")

print("\n  📇 ZOHO (Old CRM)")
zoho_count = sum(1 for c in contacts if c.get('zoho_id'))
print(f"     Contacts: {zoho_count:,}")
print(f"     Provides: Historical contact data")
print(f"     Status: ⚠️  LEGACY - No longer importing")

print("\n  💼 QUICKBOOKS (Accounting)")
qb_count = sum(1 for c in contacts if c.get('quickbooks_id'))
print(f"     Contacts: {qb_count:,}")
print(f"     Provides: Customer financial records")
print(f"     Status: ❓ UNKNOWN - Need to check if still importing")

print("\n  📧 MAILCHIMP (Email Marketing)")
mc_count = sum(1 for c in contacts if c.get('mailchimp_id'))
print(f"     Contacts: {mc_count:,}")
print(f"     Provides: Email subscription status")
print(f"     Status: ❓ UNKNOWN - Need to check if still importing")

# Find duplicates by email
print("\n4️⃣  DUPLICATE EMAIL ANALYSIS")
print("-" * 100)
email_counts = defaultdict(list)
for contact in contacts:
    email = contact.get('email', '').lower().strip()
    if email:
        email_counts[email].append(contact['id'])

duplicates = {email: ids for email, ids in email_counts.items() if len(ids) > 1}
print(f"  Duplicate emails: {len(duplicates)}")
if duplicates:
    print(f"  ⚠️  WARNING: Found {len(duplicates)} duplicate email addresses!")
    for email, ids in list(duplicates.items())[:5]:
        print(f"      {email}: {len(ids)} records")

# Check the 329 new contacts
print("\n5️⃣  ANALYZING THE 329 NEW CONTACTS FROM TODAY")
print("-" * 100)
new_today = supabase.table('contacts').select('email, first_name, last_name, kajabi_id, source_system')\
    .is_('deleted_at', 'null')\
    .gte('created_at', '2025-11-12T04:31:00')\
    .lte('created_at', '2025-11-12T04:35:00')\
    .execute()

print(f"  New contacts created during import: {len(new_today.data)}")

# Check if any of these emails existed before with different IDs
potential_dupes = 0
for new_contact in new_today.data[:50]:  # Check first 50
    email = new_contact['email'].lower()
    # Search for older contacts with same email
    older = supabase.table('contacts').select('id, email, kajabi_id')\
        .eq('email', email)\
        .lt('created_at', '2025-11-12T04:31:00')\
        .execute()

    if older.data:
        potential_dupes += 1

if potential_dupes > 0:
    print(f"  ⚠️  Found {potential_dupes} of the new contacts have matching emails in older records!")
    print(f"  This suggests duplicates were created during import")
else:
    print(f"  ✓ First 50 checked - no duplicate emails found")

print("\n" + "=" * 100)
print("📋 SUMMARY")
print("=" * 100)
print(f"""
WHAT WE HAVE:
  • Total Contacts: {total_contacts:,}
  • From Kajabi: {kajabi_count:,}
  • From PayPal: {paypal_count:,}
  • From Ticket Tailor: {tt_count:,}
  • From Zoho (legacy): {zoho_count:,}
  • From QuickBooks: {qb_count:,}
  • From MailChimp: {mc_count:,}

POTENTIAL ISSUES:
  • Duplicate emails: {len(duplicates)}
  • Multi-source contacts: {sum(1 for c in contacts if len([x for x in [c.get('kajabi_id'), c.get('zoho_id'), c.get('ticket_tailor_id')] if x]) > 1):,}
  • New contacts today: {len(new_today.data)} (need to verify not duplicates)

CURRENTLY ACTIVE IMPORTS:
  ✅ Kajabi - membership platform (PRIMARY)
  ✅ PayPal - payment tracking
  ✅ Ticket Tailor - event tickets
  ⚠️  Others - status unknown
""")

print("=" * 100)
print("RECOMMENDATION: Need to define source priority and deduplication strategy")
print("=" * 100)
