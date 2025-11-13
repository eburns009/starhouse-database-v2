#!/usr/bin/env python3
"""Check Lynn specifically"""
import os
from supabase import create_client, Client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(url, key)

# Database
db_response = supabase.table('contacts').select('*').eq('email', 'amber@the360emergence.com').execute()
db = db_response.data[0] if db_response.data else None

print("DATABASE:")
print(f"  first_name: '{db['first_name']}'")
print(f"  last_name: '{db['last_name']}'")
print(f"  additional_name: '{db.get('additional_name')}'")
print(f"  Full: '{db['first_name']} {db['last_name']}'")

# Kajabi CSV
import csv
with open("/workspaces/starhouse-database-v2/kajabi 3 files review/11102025kajabi.csv", 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Email'].lower() == 'amber@the360emergence.com':
            print("\nKAJABI CSV:")
            print(f"  Name (full): '{row['Name']}'")
            print(f"  First Name: '{row['First Name']}'")
            print(f"  Last Name: '{row['Last Name']}'")
            print(f"  Name (custom): '{row.get('Name (name)', '')}'")

            print("\nCOMPARISON:")
            if row['First Name'] == db['first_name']:
                print(f"  ✓ First names match: '{row['First Name']}'")
            else:
                print(f"  ✗ First names differ: Kajabi='{row['First Name']}' vs DB='{db['first_name']}'")

            if row['Last Name'] == db['last_name']:
                print(f"  ✓ Last names match: '{row['Last Name']}'")
            else:
                print(f"  ✗ Last names differ: Kajabi='{row['Last Name']}' vs DB='{db['last_name']}'")

            kajabi_full = row['Name']
            db_full = f"{db['first_name']} {db['last_name']}"
            if kajabi_full == db_full:
                print(f"  ✓ Full names match: '{kajabi_full}'")
            else:
                print(f"  ✗ Full names differ:")
                print(f"    Kajabi: '{kajabi_full}'")
                print(f"    DB:     '{db_full}'")
                print(f"    ISSUE: Kajabi has 3 words, DB has 2 words")
                print(f"    Missing: 'Amber' (middle name)")
            break
