#!/usr/bin/env python3
"""Quick script to analyze Ticket Tailor data for enrichment."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
cursor = conn.cursor()

# Check Ticket Tailor contacts with valuable data
cursor.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(phone) as has_phone,
        COUNT(address_line_1) as has_address,
        COUNT(CASE WHEN phone IS NOT NULL AND address_line_1 IS NOT NULL THEN 1 END) as has_both
    FROM contacts
    WHERE source_system = 'ticket_tailor'
      AND deleted_at IS NULL
""")

stats = cursor.fetchone()
print("Ticket Tailor Contact Statistics:")
print(f"  Total: {stats['total']}")
print(f"  Has Phone: {stats['has_phone']}")
print(f"  Has Address: {stats['has_address']}")
print(f"  Has Both: {stats['has_both']}")

# Check potential matches by email domain similarity
cursor.execute("""
    SELECT
        tt.id as tt_id,
        tt.email as tt_email,
        tt.first_name as tt_first,
        tt.last_name as tt_last,
        tt.phone as tt_phone,
        tt.address_line_1 as tt_address,
        k.id as kajabi_id,
        k.email as kajabi_email,
        k.first_name as kajabi_first,
        k.last_name as kajabi_last,
        k.phone as kajabi_phone,
        k.address_line_1 as kajabi_address
    FROM contacts tt
    INNER JOIN contacts k ON (
        LOWER(tt.first_name) = LOWER(k.first_name)
        AND LOWER(tt.last_name) = LOWER(k.last_name)
    )
    WHERE tt.source_system = 'ticket_tailor'
      AND k.source_system = 'kajabi'
      AND tt.deleted_at IS NULL
      AND k.deleted_at IS NULL
      AND (
        (tt.phone IS NOT NULL AND (k.phone IS NULL OR k.phone = ''))
        OR (tt.address_line_1 IS NOT NULL AND (k.address_line_1 IS NULL OR k.address_line_1 = ''))
      )
    LIMIT 20
""")

matches = cursor.fetchall()
print(f"\nPotential Name Matches (first 20): {len(matches)}")

if matches:
    for match in matches[:10]:
        print(f"\n  TT: {match['tt_first']} {match['tt_last']} ({match['tt_email']})")
        print(f"      Phone: {match['tt_phone']}, Address: {match['tt_address']}")
        print(f"  Kajabi: {match['kajabi_first']} {match['kajabi_last']} ({match['kajabi_email']})")
        print(f"      Phone: {match['kajabi_phone']}, Address: {match['kajabi_address']}")
        print(f"      Can enrich: ", end="")
        enrichments = []
        if match['tt_phone'] and not match['kajabi_phone']:
            enrichments.append("phone")
        if match['tt_address'] and not match['kajabi_address']:
            enrichments.append("address")
        print(", ".join(enrichments) if enrichments else "nothing")

cursor.close()
conn.close()
