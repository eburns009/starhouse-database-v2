#!/usr/bin/env python3
"""
COMPLETE DATA AUDIT - All sources, all contacts
"""

import os
from supabase import create_client
from collections import defaultdict

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=" * 100)
print("COMPLETE DATA SOURCE AUDIT - STARHOUSE DATABASE")
print("=" * 100)

# Get totals using count
print("\n📊 TOTAL COUNTS")
print("-" * 100)

total = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').execute()
print(f"Total active contacts: {total.count:,}")

# Count by each source ID field
kajabi_count = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('kajabi_id', 'null').execute()
zoho_count = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('zoho_id', 'null').execute()
paypal_count = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('paypal_payer_id', 'null').execute()
tt_count = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('ticket_tailor_id', 'null').execute()
qb_count = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('quickbooks_id', 'null').execute()
mc_count = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('mailchimp_id', 'null').execute()

print("\n📍 CONTACTS BY SOURCE ID FIELD")
print("-" * 100)
print(f"  Kajabi ID:        {kajabi_count.count:6,} contacts")
print(f"  Zoho ID:          {zoho_count.count:6,} contacts")
print(f"  PayPal Payer ID:  {paypal_count.count:6,} contacts")
print(f"  Ticket Tailor ID: {tt_count.count:6,} contacts")
print(f"  QuickBooks ID:    {qb_count.count:6,} contacts")
print(f"  MailChimp ID:     {mc_count.count:6,} contacts")

# Overlap analysis - Kajabi + Zoho duplicates
print("\n🔗 DUPLICATE ANALYSIS (Multiple Source IDs)")
print("-" * 100)

kajabi_zoho = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .not_.is_('zoho_id', 'null').execute()
print(f"  Kajabi + Zoho:    {kajabi_zoho.count:6,} contacts (DUPLICATES - need resolution)")

only_kajabi = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .is_('zoho_id', 'null').execute()
print(f"  ONLY Kajabi:      {only_kajabi.count:6,} contacts (clean)")

only_zoho = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .is_('kajabi_id', 'null')\
    .not_.is_('zoho_id', 'null').execute()
print(f"  ONLY Zoho:        {only_zoho.count:6,} contacts (legacy orphans)")

# Check the 329 new contacts
print("\n🆕 TODAY'S NEW CONTACTS (2025-11-12 Import)")
print("-" * 100)

new_today = supabase.table('contacts').select('id, email, kajabi_id', count='exact')\
    .is_('deleted_at', 'null')\
    .gte('created_at', '2025-11-12T04:31:00')\
    .lte('created_at', '2025-11-12T04:35:00')\
    .execute()

print(f"  New contacts created: {new_today.count:,}")

# Check if these are actually duplicates
if new_today.count > 0:
    print(f"\n  Checking if the {new_today.count} new contacts are duplicates...")
    print(f"  (Searching for older contacts with same email)")

    duplicate_count = 0
    checked = 0

    for contact in new_today.data:
        if checked >= 100:  # Check first 100
            break
        checked += 1

        email = contact['email']
        # Find contacts with same email created BEFORE today's import
        older = supabase.table('contacts').select('id', count='exact')\
            .eq('email', email)\
            .lt('created_at', '2025-11-12T04:31:00')\
            .execute()

        if older.count > 0:
            duplicate_count += 1
            if duplicate_count <= 5:  # Show first 5 examples
                print(f"    ⚠️  {email}: Has {older.count} older record(s) (DUPLICATE)")

    if duplicate_count > 0:
        print(f"\n  ❌ PROBLEM: {duplicate_count} of {checked} checked are DUPLICATES")
        print(f"     These should have been UPDATES, not INSERTS")
    else:
        print(f"  ✅ First {checked} checked - no duplicates found (legitimate new contacts)")

# Subscription data
print("\n💳 SUBSCRIPTION DATA")
print("-" * 100)

total_subs = supabase.table('subscriptions').select('id', count='exact').is_('deleted_at', 'null').execute()
active_subs = supabase.table('subscriptions').select('id', count='exact').is_('deleted_at', 'null').eq('status', 'active').execute()
print(f"  Total subscriptions: {total_subs.count:,}")
print(f"  Active subscriptions: {active_subs.count:,}")

# Transaction data
print("\n💰 TRANSACTION DATA")
print("-" * 100)

total_trans = supabase.table('transactions').select('id', count='exact').execute()
paypal_trans = supabase.table('transactions').select('id', count='exact').eq('payment_processor', 'paypal').execute()
kajabi_trans = supabase.table('transactions').select('id', count='exact').eq('payment_processor', 'kajabi').execute()

print(f"  Total transactions: {total_trans.count:,}")
print(f"  PayPal transactions: {paypal_trans.count:,}")
print(f"  Kajabi transactions: {kajabi_trans.count:,}")

# Source system breakdown (sample to understand distribution)
print("\n🏷️  SOURCE SYSTEM FIELD (Sample of 2000)")
print("-" * 100)

sample = supabase.table('contacts').select('source_system').is_('deleted_at', 'null').limit(2000).execute()
source_counts = defaultdict(int)
for contact in sample.data:
    source = contact.get('source_system', 'null')
    source_counts[source] += 1

for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(sample.data)) * 100
    print(f"  {source:20} {count:6,} ({pct:5.1f}% of sample)")

print("\n" + "=" * 100)
print("📋 EXECUTIVE SUMMARY")
print("=" * 100)
print(f"""
WHERE OUR {total.count:,} CONTACTS COME FROM:
┌─────────────────────────────────────────────────────────────────┐
│ PRIMARY SOURCES (Active imports)                                │
├─────────────────────────────────────────────────────────────────┤
│  📱 Kajabi:        {kajabi_count.count:6,} ({kajabi_count.count/total.count*100:5.1f}%) - Membership platform     │
│  💳 PayPal:        {paypal_count.count:6,} ({paypal_count.count/total.count*100:5.1f}%) - Payment tracking         │
│  🎫 Ticket Tailor: {tt_count.count:6,} ({tt_count.count/total.count*100:5.1f}%) - Event tickets             │
├─────────────────────────────────────────────────────────────────┤
│ LEGACY SOURCES (No longer importing)                            │
├─────────────────────────────────────────────────────────────────┤
│  📇 Zoho:          {zoho_count.count:6,} ({zoho_count.count/total.count*100:5.1f}%) - Old CRM (frozen)        │
├─────────────────────────────────────────────────────────────────┤
│ UNUSED SOURCES (Never imported)                                 │
├─────────────────────────────────────────────────────────────────┤
│  💼 QuickBooks:    {qb_count.count:6,} ({qb_count.count/total.count*100:5.1f}%) - Accounting                  │
│  📧 MailChimp:     {mc_count.count:6,} ({mc_count.count/total.count*100:5.1f}%) - Email marketing             │
└─────────────────────────────────────────────────────────────────┘

THE DUPLICATE PROBLEM:
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  {kajabi_zoho.count:,} contacts in BOTH Kajabi AND Zoho (duplicates)    │
│  ✅  {only_kajabi.count:,} contacts ONLY in Kajabi (clean)                   │
│  ⚠️  {only_zoho.count:,} contacts ONLY in Zoho (legacy orphans)              │
│  🆕  {new_today.count:,} contacts created today (investigating)              │
└─────────────────────────────────────────────────────────────────┘

WHAT THIS MEANS:
  - Kajabi is our #1 source ({kajabi_count.count/total.count*100:.0f}% of contacts)
  - {kajabi_zoho.count:,} duplicates need resolution (Kajabi should win)
  - {only_zoho.count:,} Zoho orphans need decision (keep or remove?)
  - {new_today.count:,} new contacts need verification (duplicates or legitimate?)

BUSINESS DATA:
  - {active_subs.count} active subscriptions generating revenue
  - {total_trans.count:,} total transactions recorded
  - {paypal_trans.count:,} PayPal transactions tracked
""")

print("=" * 100)
print("NEXT STEPS: Review docs/DATA_AUDIT_2025_11_12_WHAT_WE_COLLECT_AND_WHY.md")
print("=" * 100)
