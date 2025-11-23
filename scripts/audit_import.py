#!/usr/bin/env python3
"""Audit QuickBooks donor import changes."""

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'], cursor_factory=RealDictCursor)
cur = conn.cursor()

print('=' * 60)
print('CONTACT TABLE AUDIT - Import Session')
print('=' * 60)

# 1. Check contact modifications in last hour
cur.execute('''
    SELECT
        COUNT(*) as total_contacts,
        COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '1 hour') as recently_updated
    FROM contacts
''')
result = cur.fetchone()
print(f"""
1. Contact Modifications:
   Total contacts: {result['total_contacts']}
   Updated in last hour: {result['recently_updated']}
""")

# 2. Show recently updated contacts
cur.execute('''
    SELECT
        id,
        email,
        first_name,
        last_name,
        phone,
        address_line_1,
        source_system,
        updated_at
    FROM contacts
    WHERE updated_at > NOW() - INTERVAL '1 hour'
    ORDER BY updated_at DESC
    LIMIT 20
''')
rows = cur.fetchall()
print('2. Recently Updated Contacts (top 20):')
if rows:
    for row in rows:
        enriched = []
        if row['phone']: enriched.append('phone')
        if row['address_line_1']: enriched.append('address')
        enriched_str = f" [has: {', '.join(enriched)}]" if enriched else ''
        print(f"   {row['first_name']} {row['last_name']} ({row['email']}){enriched_str}")
else:
    print('   No contacts updated in last hour')

# 3. Check external_identities created in last hour
cur.execute('''
    SELECT
        COUNT(*) as total_qb_identities,
        COUNT(DISTINCT contact_id) as unique_contacts_linked
    FROM external_identities
    WHERE system = 'quickbooks'
    AND created_at > NOW() - INTERVAL '1 hour'
''')
result = cur.fetchone()
print(f"""
3. External Identities Created (last hour):
   QB identities created: {result['total_qb_identities']}
   Unique contacts linked: {result['unique_contacts_linked']}
""")

# 4. Check enrichment in last hour
cur.execute('''
    SELECT
        ei.metadata->>'enriched_fields' as enriched_fields,
        COUNT(*) as count
    FROM external_identities ei
    WHERE system = 'quickbooks'
    AND created_at > NOW() - INTERVAL '1 hour'
    AND ei.metadata->>'enriched_fields' IS NOT NULL
    GROUP BY enriched_fields
    ORDER BY count DESC
''')
rows = cur.fetchall()
print('4. Enrichment Summary (last hour):')
if rows:
    for row in rows:
        print(f"   {row['enriched_fields']}: {row['count']} contacts")
else:
    print('   No enrichment recorded')

# 5. Check donors created
cur.execute('''
    SELECT
        COUNT(*) as total_donors,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as new_donors
    FROM donors
''')
result = cur.fetchone()
print(f"""
5. Donors:
   Total donors: {result['total_donors']}
   Created in last hour: {result['new_donors']}
""")

# 6. Check transactions created
cur.execute('''
    SELECT
        COUNT(*) as total,
        SUM(amount) FILTER (WHERE transaction_type != 'refund') as positive_sum,
        SUM(amount) FILTER (WHERE transaction_type = 'refund') as refunds
    FROM transactions
    WHERE is_donation = true
    AND created_at > NOW() - INTERVAL '1 hour'
''')
result = cur.fetchone()
print(f"""
6. Donation Transactions (last hour):
   Total transactions: {result['total']}
   Donations total: ${result['positive_sum'] or 0:,.2f}
   Refunds total: ${abs(result['refunds'] or 0):,.2f}
""")

# 7. Total QB identities ever
cur.execute('''
    SELECT COUNT(*) as total FROM external_identities WHERE system = 'quickbooks'
''')
total = cur.fetchone()['total']
print(f"""
7. Total QB Identities in System: {total}
""")

conn.close()
