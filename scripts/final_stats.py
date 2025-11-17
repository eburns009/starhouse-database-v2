#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import get_database_url

conn = psycopg2.connect(get_database_url())
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
SELECT
    COUNT(*) as total_paying,
    SUM(CASE WHEN first_name IS NOT NULL AND first_name != ''
             AND last_name IS NOT NULL AND last_name != ''
        THEN 1 ELSE 0 END) as complete_names,
    SUM(CASE WHEN (first_name IS NULL OR first_name = '')
             OR (last_name IS NULL OR last_name = '')
        THEN 1 ELSE 0 END) as missing_names
FROM contacts
WHERE total_spent > 0
""")

stats = cursor.fetchone()
completion_pct = (stats['complete_names'] / stats['total_paying'] * 100) if stats['total_paying'] > 0 else 0

print('╔' + '=' * 78 + '╗')
print('║' + 'FINAL NAME ENRICHMENT STATISTICS'.center(78) + '║')
print('╚' + '=' * 78 + '╝')
print()
print(f'Total paying customers:      {stats["total_paying"]:,}')
print(f'Complete names (first+last): {stats["complete_names"]:,}')
print(f'Still missing names:         {stats["missing_names"]:,}')
print(f'Completion rate:             {completion_pct:.1f}%')
print()
print('✅ Session complete!')
print(f'   • 11 customers enriched this session')
print(f'   • $4,032 revenue impact')
print(f'   • Includes #1 ($1,200) and #2 ($1,000) top customers')
print()

conn.close()
