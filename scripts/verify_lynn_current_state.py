#!/usr/bin/env python3
"""
Verify Lynn Amber Ryan's current state in the database
and test if the tokenized search logic would find her.
"""

import psycopg2
import os
import sys

# Database connection - Supabase uses a connection string format
# Extract database connection details from Supabase URL
supabase_url = os.environ.get('SUPABASE_URL', '')
# Supabase PostgreSQL connection format:
# postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')

# Try to get the service role key which contains the JWT
service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

# Construct PostgreSQL connection string
# For Supabase, we need to use the pooler connection
db_host = f"aws-0-us-east-1.pooler.supabase.com"
db_port = "6543"
db_name = "postgres"
db_user = "postgres.lnagadkqejnopgfxwlkb"

# Ask for password if not set
db_password = os.environ.get('SUPABASE_DB_PASSWORD', '')
if not db_password:
    print("Note: SUPABASE_DB_PASSWORD not set in environment")
    print("You can find it in: Supabase Dashboard > Project Settings > Database > Connection string")
    print("Or use the Supabase client libraries instead")
    sys.exit(1)

conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)
cur = conn.cursor()

print("=" * 80)
print("LYNN AMBER RYAN - CURRENT STATE VERIFICATION")
print("=" * 80)

# 1. Find Lynn by email
print("\n1. SEARCHING FOR LYNN BY EMAIL (amber@the360emergence.com)")
print("-" * 80)
cur.execute("""
    SELECT
        id,
        first_name,
        last_name,
        additional_name,
        email,
        paypal_first_name,
        paypal_last_name,
        paypal_business_name,
        kajabi_id,
        deleted_at
    FROM contacts
    WHERE email = 'amber@the360emergence.com'
""")

contact = cur.fetchone()
if not contact:
    print("❌ ERROR: Lynn not found by email!")
    sys.exit(1)

contact_id, first_name, last_name, additional_name, email, \
    paypal_first_name, paypal_last_name, paypal_business_name, \
    kajabi_id, deleted_at = contact

print(f"✓ Found contact:")
print(f"  ID: {contact_id}")
print(f"  First Name: {first_name}")
print(f"  Last Name: {last_name}")
print(f"  Additional Name: {additional_name}")
print(f"  Email: {email}")
print(f"  PayPal First Name: {paypal_first_name}")
print(f"  PayPal Last Name: {paypal_last_name}")
print(f"  PayPal Business Name: {paypal_business_name}")
print(f"  Kajabi ID: {kajabi_id}")
print(f"  Deleted: {deleted_at}")

# 2. Check if contact is deleted
print("\n2. DELETION STATUS")
print("-" * 80)
if deleted_at:
    print(f"❌ CRITICAL: Contact is DELETED! deleted_at = {deleted_at}")
    print("   This is why she doesn't show up in the UI!")
else:
    print("✓ Contact is NOT deleted (deleted_at IS NULL)")

# 3. Check subscriptions
print("\n3. ACTIVE SUBSCRIPTIONS")
print("-" * 80)
cur.execute("""
    SELECT
        s.id,
        s.kajabi_subscription_id,
        s.status,
        s.amount,
        s.billing_cycle,
        s.product_id,
        p.name as product_name
    FROM subscriptions s
    LEFT JOIN products p ON s.product_id = p.id
    WHERE s.contact_id = %s
    AND s.status = 'active'
    ORDER BY s.created_at DESC
""", (contact_id,))

subscriptions = cur.fetchall()
print(f"✓ Found {len(subscriptions)} active subscription(s)")
for sub in subscriptions:
    sub_id, kajabi_sub_id, status, amount, billing_cycle, product_id, product_name = sub
    print(f"\n  Subscription ID: {sub_id}")
    print(f"  Kajabi Sub ID: {kajabi_sub_id}")
    print(f"  Status: {status}")
    print(f"  Amount: ${amount}/{billing_cycle}")
    print(f"  Product ID: {product_id}")
    print(f"  Product Name: {product_name}")

# 4. Simulate tokenized search with AND logic
print("\n4. SIMULATING TOKENIZED SEARCH: 'Lynn Amber Ryan'")
print("-" * 80)

search_query = "Lynn Amber Ryan"
words = search_query.lower().split()
print(f"Search words: {words}")

search_fields = [
    ('first_name', first_name),
    ('last_name', last_name),
    ('additional_name', additional_name),
    ('paypal_first_name', paypal_first_name),
    ('paypal_last_name', paypal_last_name),
    ('paypal_business_name', paypal_business_name),
    ('email', email),
]

print("\nChecking if ALL words match (AND logic):")
all_words_match = True
for word in words:
    print(f"\n  Word: '{word}'")
    word_found_in_field = False
    for field_name, field_value in search_fields:
        if field_value and word in field_value.lower():
            print(f"    ✓ Found in {field_name}: {field_value}")
            word_found_in_field = True

    if not word_found_in_field:
        print(f"    ❌ NOT found in any field!")
        all_words_match = False

print("\n" + "=" * 80)
if all_words_match:
    print("✅ ALL WORDS MATCH - Lynn SHOULD be found by tokenized search")
else:
    print("❌ NOT ALL WORDS MATCH - Lynn will NOT be found by tokenized search")
print("=" * 80)

# 5. Test actual database query that UI would use
print("\n5. TESTING ACTUAL UI QUERY (with OR conditions)")
print("-" * 80)

# Build the query like the UI does
words_escaped = [w.replace('%', '%%') for w in words]
conditions = []
for word in words_escaped:
    for field in ['first_name', 'last_name', 'additional_name', 'paypal_first_name',
                   'paypal_last_name', 'paypal_business_name', 'email', 'phone']:
        conditions.append(f"{field} ILIKE '%{word}%'")

or_query = " OR ".join(conditions)

cur.execute(f"""
    SELECT
        id,
        first_name,
        last_name,
        email
    FROM contacts
    WHERE deleted_at IS NULL
    AND ({or_query})
    LIMIT 200
""")

results = cur.fetchall()
print(f"✓ Database returned {len(results)} contact(s) using OR logic")

# Check if Lynn is in results
lynn_in_results = False
for result in results:
    if result[0] == contact_id:
        lynn_in_results = True
        break

if lynn_in_results:
    print("✓ Lynn IS in the database results")
else:
    print("❌ Lynn is NOT in the database results")

# 6. Final verdict
print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if deleted_at:
    print("❌ PROBLEM FOUND: Contact is DELETED (deleted_at IS NOT NULL)")
    print("   SOLUTION: Set deleted_at = NULL to restore the contact")
elif not lynn_in_results:
    print("❌ PROBLEM: Lynn not found by UI query")
    print("   Need to investigate query logic")
elif not all_words_match:
    print("❌ PROBLEM: Client-side AND filtering will exclude Lynn")
    print("   Need to check which word is not matching")
else:
    print("✅ NO PROBLEMS FOUND: Lynn should show up in UI")
    print("   If she doesn't, check:")
    print("   1. Browser cache (hard refresh)")
    print("   2. Deployment status on Vercel")
    print("   3. Check browser console for errors")

conn.close()
