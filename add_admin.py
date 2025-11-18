#!/usr/bin/env python3
"""
Add Admin User to Staff Members Table
Simple script to bootstrap the first admin user
"""

from supabase import create_client, Client
import os

# Supabase credentials from .env.local
SUPABASE_URL = "https://lnagadkqejnopgfxwlkb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxuYWdhZGtxZWpub3BnZnh3bGtiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTY3NDQ5NSwiZXhwIjoyMDc3MjUwNDk1fQ.nlEC-b2uw_PLAx3tJCPkyVbocsAVfcfnTiATtC96E50"

def main():
    # Create Supabase client with service role key (bypasses RLS)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("=" * 60)
    print("Adding Admin User to Staff Members")
    print("=" * 60)

    # Admin email
    admin_email = "eburns009@gmail.com"

    # Check if staff_members table exists and show current members
    print("\n1. Checking current staff members...")
    try:
        result = supabase.table('staff_members').select('*').execute()
        if result.data:
            print(f"   Found {len(result.data)} existing staff members:")
            for member in result.data:
                print(f"   - {member['email']} ({member['role']}) - Active: {member['active']}")
        else:
            print("   No existing staff members found")
    except Exception as e:
        print(f"   Error checking staff members: {e}")

    # Check if admin already exists
    print(f"\n2. Checking if {admin_email} already exists...")
    try:
        existing = supabase.table('staff_members').select('*').eq('email', admin_email).execute()
        if existing.data:
            print(f"   ✅ User already exists with role: {existing.data[0]['role']}")
            if existing.data[0]['role'] != 'admin':
                print(f"   Updating role to 'admin'...")
                update_result = supabase.table('staff_members').update({
                    'role': 'admin',
                    'active': True
                }).eq('email', admin_email).execute()
                print(f"   ✅ Updated to admin role")
            else:
                print(f"   Already an admin - no changes needed")
            return
    except Exception as e:
        print(f"   No existing user found (this is normal for first admin)")

    # Add new admin
    print(f"\n3. Adding {admin_email} as admin...")
    try:
        insert_result = supabase.table('staff_members').insert({
            'email': admin_email,
            'role': 'admin',
            'display_name': 'Ed Burns',
            'active': True,
            'added_by': 'bootstrap_script',
            'notes': 'Initial admin user - added via bootstrap script'
        }).execute()

        print(f"   ✅ Successfully added {admin_email} as admin!")
        print(f"   Display Name: Ed Burns")
        print(f"   Role: admin")
        print(f"   Active: true")

    except Exception as e:
        print(f"   ❌ Error adding admin: {e}")
        return

    # Verify
    print("\n4. Verification - Current staff members:")
    try:
        final_result = supabase.table('staff_members').select('*').execute()
        for member in final_result.data:
            status = "✅ ACTIVE" if member['active'] else "❌ INACTIVE"
            print(f"   {status} {member['email']} ({member['role']})")
            if member.get('display_name'):
                print(f"      Display Name: {member['display_name']}")
    except Exception as e:
        print(f"   Error in verification: {e}")

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Go to your Vercel app")
    print("2. Sign in with: eburns009@gmail.com")
    print("3. Navigate to /staff to access the Staff Management page")
    print("=" * 60)

if __name__ == "__main__":
    main()
