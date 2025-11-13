#!/usr/bin/env python3
"""Check contacts table schema"""
import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Get one record to see all columns
response = supabase.table('contacts').select('*').limit(1).execute()

if response.data:
    print("Contacts table columns:")
    for col in sorted(response.data[0].keys()):
        print(f"  - {col}")

    # Check for name-related columns
    name_cols = [c for c in response.data[0].keys() if 'name' in c.lower()]
    print(f"\nName-related columns ({len(name_cols)}):")
    for col in sorted(name_cols):
        print(f"  - {col}")
