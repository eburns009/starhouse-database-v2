#!/usr/bin/env python3
"""Check if Mailchimp data has been imported"""
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import get_database_url

DB_URL = get_database_url()

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("\n" + "=" * 100)
print("CHECKING FOR MAILCHIMP DATA IN DATABASE")
print("=" * 100)

# Check for source_system = 'mailchimp'
cursor.execute("""
    SELECT COUNT(*) as count
    FROM contacts
    WHERE source_system = 'mailchimp'
""")
result = cursor.fetchone()
print(f"\nContacts with source_system = 'mailchimp': {result['count']}")

# Check for source_system LIKE '%mail%'
cursor.execute("""
    SELECT source_system, COUNT(*) as count
    FROM contacts
    WHERE source_system ILIKE '%mail%'
    GROUP BY source_system
    ORDER BY count DESC
""")
results = cursor.fetchall()
if results:
    print("\nContacts with 'mail' in source_system:")
    for r in results:
        print(f"  {r['source_system']}: {r['count']}")
else:
    print("\nNo contacts with 'mail' in source_system")

# Check sample emails from Mailchimp file
sample_emails = [
    'wendalion9@gmail.com',  # Wendy Nelson
    'ravenr@humboldt1.com',   # Marjorie Kieselhorst-Eckart (top donor!)
    'kianaprema@gmail.com',   # Kiana Prema (donor we just enriched)
    'lilaplays@gmail.com',    # Laura Cannon
    'ccrw1286@comcast.net'    # Roy Wingate
]

print("\n" + "=" * 100)
print("CHECKING SAMPLE EMAILS FROM MAILCHIMP FILE:")
print("=" * 100)

for email in sample_emails:
    cursor.execute("""
        SELECT email, first_name, last_name, source_system, created_at
        FROM contacts
        WHERE email = %s
    """, (email,))
    result = cursor.fetchone()
    if result:
        print(f"✅ {email:35s} Found - {result['first_name']} {result['last_name']} (source: {result['source_system']})")
    else:
        print(f"❌ {email:35s} NOT FOUND")

# Check all distinct source_systems
cursor.execute("""
    SELECT source_system, COUNT(*) as count
    FROM contacts
    GROUP BY source_system
    ORDER BY count DESC
""")
results = cursor.fetchall()
print("\n" + "=" * 100)
print("ALL SOURCE SYSTEMS IN DATABASE:")
print("=" * 100)
for r in results:
    system = r['source_system'] or '(NULL/Unknown)'
    print(f"  {system:30s} {r['count']:>6,} contacts")

conn.close()
