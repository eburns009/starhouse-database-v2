#!/usr/bin/env python3
"""Quick check of enrichment status"""
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Check top donors by total_spent
cursor.execute("""
    SELECT first_name, last_name, email, total_spent, transaction_count, source_system
    FROM contacts
    WHERE total_spent > 0
    ORDER BY total_spent DESC
    LIMIT 20
""")

results = cursor.fetchall()

print("\nTop 20 Contacts by Total Spent:")
print("=" * 100)
for i, r in enumerate(results, 1):
    print(f"{i:2d}. {r['first_name']} {r['last_name']:30s} ${r['total_spent']:>10,.2f}  Count: {r['transaction_count']:3d}  Source: {r['source_system']}")

# Check if All Seasons Chalice was enriched
cursor.execute("""
    SELECT first_name, last_name, total_spent, transaction_count, updated_at
    FROM contacts
    WHERE LOWER(first_name || ' ' || last_name) LIKE '%all seasons chalice%'
""")

asc_result = cursor.fetchone()
if asc_result:
    print("\n" + "=" * 100)
    print("All Seasons Chalice Check:")
    print(f"  Name: {asc_result['first_name']} {asc_result['last_name']}")
    print(f"  Total Spent: ${asc_result['total_spent']:,.2f}")
    print(f"  Transaction Count: {asc_result['transaction_count']}")
    print(f"  Last Updated: {asc_result['updated_at']}")

conn.close()
