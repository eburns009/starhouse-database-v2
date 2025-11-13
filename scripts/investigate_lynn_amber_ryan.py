import os
from supabase import create_client
import json
from datetime import datetime

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("INVESTIGATING: Lynn Amber Ryan")
print("=" * 80)

# First, let's check the schema by getting one contact
print("\n0. CHECKING CONTACT SCHEMA...")
response = supabase.table('contacts').select('*').limit(1).execute()
if response.data:
    print("Available columns:", list(response.data[0].keys()))

# Search for contact by name (trying different column names)
print("\n1. SEARCHING FOR CONTACT BY NAME...")
# Try 'name' column
try:
    response = supabase.table('contacts').select('*').ilike('name', '%Lynn%Amber%Ryan%').execute()
    contacts_by_name = response.data
    print(f"✓ Found {len(contacts_by_name)} contact(s) matching full name pattern")
except Exception as e:
    print(f"Search by full pattern failed, trying variations...")
    contacts_by_name = []

if not contacts_by_name:
    # Try just "Lynn Ryan"
    try:
        response = supabase.table('contacts').select('*').ilike('name', '%Lynn%Ryan%').execute()
        contacts_by_name = response.data
        print(f"✓ Found {len(contacts_by_name)} contact(s) with 'Lynn Ryan'")
    except:
        contacts_by_name = []

# Search by email containing "lynn" or "amber" or "ryan"
print("\n2. SEARCHING FOR CONTACT BY EMAIL...")
try:
    response = supabase.table('contacts').select('*').or_('email.ilike.%lynn%,email.ilike.%amber%,email.ilike.%ryan%').execute()
    email_matches = response.data
    print(f"✓ Found {len(email_matches)} contact(s) with email containing lynn/amber/ryan")
except Exception as e:
    print(f"Email search error: {e}")
    email_matches = []

# Also search in name field
print("\n3. SEARCHING IN NAME FIELD...")
try:
    response = supabase.table('contacts').select('*').or_('name.ilike.%lynn%,name.ilike.%amber%,name.ilike.%ryan%').execute()
    name_matches = response.data
    # Filter to those that have multiple matches
    name_matches = [c for c in name_matches if 
                   ('lynn' in c.get('name', '').lower() and ('amber' in c.get('name', '').lower() or 'ryan' in c.get('name', '').lower())) or
                   ('amber' in c.get('name', '').lower() and 'ryan' in c.get('name', '').lower())]
    print(f"✓ Found {len(name_matches)} contact(s) with name containing multiple parts")
except Exception as e:
    print(f"Name search error: {e}")
    name_matches = []

# Combine results
all_contacts = contacts_by_name + email_matches + name_matches
# Remove duplicates by id
unique_contacts = list({c['id']: c for c in all_contacts}.values())

print(f"\n{'='*80}")
print(f"TOTAL UNIQUE CONTACTS FOUND: {len(unique_contacts)}")
print(f"{'='*80}")

for contact in unique_contacts:
    print(f"\n📧 CONTACT DETAILS:")
    print(f"   ID: {contact['id']}")
    print(f"   Name: {contact.get('name', 'N/A')}")
    print(f"   Email: {contact.get('email', 'N/A')}")
    print(f"   Source: {contact.get('source', 'N/A')}")
    print(f"   Lock Level: {contact.get('lock_level', 'N/A')}")
    print(f"   Email Subscribed: {contact.get('email_subscribed', 'N/A')}")
    print(f"   Kajabi ID: {contact.get('kajabi_id', 'N/A')}")
    print(f"   Created: {contact.get('created_at', 'N/A')}")
    print(f"   Updated: {contact.get('updated_at', 'N/A')}")
    
    # Get subscriptions
    print(f"\n   📋 SUBSCRIPTIONS:")
    subs_response = supabase.table('subscriptions').select('*').eq('contact_id', contact['id']).execute()
    subscriptions = subs_response.data
    
    if subscriptions:
        print(f"   ✓ Found {len(subscriptions)} subscription(s)")
        for i, sub in enumerate(subscriptions, 1):
            print(f"\n   Subscription #{i}:")
            print(f"      ID: {sub['id']}")
            print(f"      Kajabi Sub ID: {sub.get('kajabi_subscription_id', 'N/A')}")
            print(f"      Product: {sub.get('product_name', 'N/A')}")
            print(f"      Amount: ${sub.get('amount', 0)}")
            print(f"      Billing Cycle: {sub.get('billing_cycle', 'N/A')}")
            print(f"      Status: {sub.get('status', 'N/A')}")
            print(f"      Start Date: {sub.get('start_date', 'N/A')}")
            print(f"      End Date: {sub.get('end_date', 'N/A')}")
            print(f"      Created: {sub.get('created_at', 'N/A')}")
            print(f"      Updated: {sub.get('updated_at', 'N/A')}")
    else:
        print(f"   ✗ No subscriptions found")
    
    # Get transactions
    print(f"\n   💰 TRANSACTIONS:")
    trans_response = supabase.table('transactions').select('*').eq('contact_id', contact['id']).order('transaction_date', desc=True).limit(10).execute()
    transactions = trans_response.data
    
    if transactions:
        print(f"   ✓ Found {len(transactions)} recent transaction(s) (showing last 10)")
        for i, trans in enumerate(transactions[:5], 1):  # Show first 5
            print(f"\n   Transaction #{i}:")
            print(f"      Date: {trans.get('transaction_date', 'N/A')}")
            print(f"      Amount: ${trans.get('amount', 0)}")
            print(f"      Source: {trans.get('source', 'N/A')}")
            print(f"      Description: {trans.get('description', 'N/A')[:50]}")
            print(f"      Status: {trans.get('status', 'N/A')}")
        if len(transactions) > 5:
            print(f"\n   ... and {len(transactions) - 5} more transactions")
    else:
        print(f"   ✗ No transactions found")

# If no contacts found, do a broader search
if len(unique_contacts) == 0:
    print("\n" + "="*80)
    print("NO CONTACTS FOUND - Checking if contact exists at all...")
    print("="*80)
    
    print("\nPlease provide:")
    print("1. The exact email address for Lynn Amber Ryan")
    print("2. Or the Kajabi contact ID")
    print("3. Or any other identifying information")

print("\n" + "="*80)
print("INVESTIGATION COMPLETE")
print("="*80)

