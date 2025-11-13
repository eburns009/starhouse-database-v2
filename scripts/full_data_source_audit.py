#!/usr/bin/env python3
"""
FULL DATA SOURCE AUDIT - Get accurate counts
"""

import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=" * 100)
print("FULL DATA SOURCE AUDIT")
print("=" * 100)

# Get total counts using count parameter
print("\n📊 TOTAL CONTACTS")
print("-" * 100)

total = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').execute()
print(f"Total active contacts: {total.count:,}")

# Count by each source ID
print("\n📍 CONTACTS BY SOURCE ID")
print("-" * 100)

kajabi = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('kajabi_id', 'null').execute()
print(f"Kajabi ID present:        {kajabi.count:6,}")

paypal = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('paypal_payer_id', 'null').execute()
print(f"PayPal Payer ID present:  {paypal.count:6,}")

tt = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('ticket_tailor_id', 'null').execute()
print(f"Ticket Tailor ID present: {tt.count:6,}")

zoho = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('zoho_id', 'null').execute()
print(f"Zoho ID present:          {zoho.count:6,}")

qb = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('quickbooks_id', 'null').execute()
print(f"QuickBooks ID present:    {qb.count:6,}")

mc = supabase.table('contacts').select('id', count='exact').is_('deleted_at', 'null').not_.is_('mailchimp_id', 'null').execute()
print(f"MailChimp ID present:     {mc.count:6,}")

# Count by source_system field
print("\n🏷️  CONTACTS BY SOURCE_SYSTEM FIELD")
print("-" * 100)

# Get distinct values
response = supabase.rpc('get_contact_sources_summary').execute()
if response.data is None:
    # Fallback: sample contacts to see source_system values
    sample = supabase.table('contacts').select('source_system').is_('deleted_at', 'null').limit(5000).execute()
    from collections import Counter
    sources = Counter(c['source_system'] for c in sample.data if c['source_system'])
    for source, count in sources.most_common():
        print(f"  {source:20} ~{count:,} (sampled)")
else:
    for row in response.data:
        print(f"  {row['source_system']:20} {row['count']:6,}")

# Overlap analysis
print("\n🔗 SOURCE OVERLAP ANALYSIS")
print("-" * 100)

# Kajabi + Zoho
kz = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .not_.is_('zoho_id', 'null').execute()
print(f"Kajabi + Zoho:            {kz.count:6,} contacts")

# Kajabi + PayPal
kp = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .not_.is_('paypal_payer_id', 'null').execute()
print(f"Kajabi + PayPal:          {kp.count:6,} contacts")

# Kajabi + Ticket Tailor
kt = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .not_.is_('ticket_tailor_id', 'null').execute()
print(f"Kajabi + Ticket Tailor:   {kt.count:6,} contacts")

# All three active sources
all_three = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .not_.is_('paypal_payer_id', 'null')\
    .not_.is_('ticket_tailor_id', 'null').execute()
print(f"Kajabi + PayPal + TT:     {all_three.count:6,} contacts")

# Only Kajabi (no other IDs)
only_kajabi = supabase.table('contacts').select('id', count='exact')\
    .is_('deleted_at', 'null')\
    .not_.is_('kajabi_id', 'null')\
    .is_('paypal_payer_id', 'null')\
    .is_('ticket_tailor_id', 'null')\
    .is_('zoho_id', 'null').execute()
print(f"ONLY Kajabi (pure):       {only_kajabi.count:6,} contacts")

# Check today's 329 contacts
print("\n🆕 TODAY'S 329 NEW CONTACTS")
print("-" * 100)

new_today = supabase.table('contacts').select('id, email', count='exact')\
    .is_('deleted_at', 'null')\
    .gte('created_at', '2025-11-12T04:31:00')\
    .lte('created_at', '2025-11-12T04:35:00')\
    .execute()

print(f"Contacts created during import: {new_today.count}")

# Check first few for duplicates
if new_today.count > 0:
    print("\nChecking first 20 for duplicate emails...")
    dupes_found = 0
    for contact in new_today.data[:20]:
        email = contact['email']
        # Count total contacts with this email
        count = supabase.table('contacts').select('id', count='exact')\
            .is_('deleted_at', 'null')\
            .eq('email', email).execute()

        if count.count > 1:
            dupes_found += 1
            print(f"  ⚠️  {email}: {count.count} total records (DUPLICATE)")

    if dupes_found == 0:
        print(f"  ✅ First 20 checked - no duplicates found")
    else:
        print(f"  ⚠️  Found {dupes_found} duplicates in first 20!")

# Subscription data
print("\n💳 SUBSCRIPTION DATA")
print("-" * 100)

total_subs = supabase.table('subscriptions').select('id', count='exact').is_('deleted_at', 'null').execute()
print(f"Total subscriptions: {total_subs.count:,}")

active_subs = supabase.table('subscriptions').select('id', count='exact').is_('deleted_at', 'null').eq('status', 'active').execute()
print(f"Active subscriptions: {active_subs.count:,}")

# Transaction data
print("\n💰 TRANSACTION DATA")
print("-" * 100)

total_trans = supabase.table('transactions').select('id', count='exact').execute()
print(f"Total transactions: {total_trans.count:,}")

paypal_trans = supabase.table('transactions').select('id', count='exact').eq('payment_processor', 'paypal').execute()
print(f"PayPal transactions: {paypal_trans.count:,}")

kajabi_trans = supabase.table('transactions').select('id', count='exact').eq('payment_processor', 'kajabi').execute()
print(f"Kajabi transactions: {kajabi_trans.count:,}")

print("\n" + "=" * 100)
print("📊 SUMMARY")
print("=" * 100)
print(f"""
WHAT WE COLLECT:
  📱 Kajabi:        {kajabi.count:6,} contacts (PRIMARY - membership platform)
  💳 PayPal:        {paypal.count:6,} contacts (payment tracking)
  🎫 Ticket Tailor: {tt.count:6,} contacts (event tickets)
  📇 Zoho:          {zoho.count:6,} contacts (LEGACY - old CRM)
  💼 QuickBooks:    {qb.count:6,} contacts (accounting)
  📧 MailChimp:     {mc.count:6,} contacts (email marketing)

OVERLAPS (Same person in multiple systems):
  Kajabi + Zoho:           {kz.count:6,} contacts
  Kajabi + PayPal:         {kp.count:6,} contacts
  Kajabi + Ticket Tailor:  {kt.count:6,} contacts

PURE SOURCES (No overlap):
  Only Kajabi:             {only_kajabi.count:6,} contacts

TODAY'S IMPORT:
  New contacts created:    {new_today.count:6,} contacts

DATA VOLUME:
  Total contacts:          {total.count:6,}
  Total subscriptions:     {total_subs.count:6,}
  Total transactions:      {total_trans.count:6,}
""")

print("=" * 100)
