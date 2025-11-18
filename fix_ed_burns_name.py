#!/usr/bin/env python3
"""
Fix Ed Burns Name in Staff Members Table
One-time script to correct the typo: "Erik Burns" → "Ed Burns"
"""

from supabase import create_client, Client

# Supabase credentials from .env.local
SUPABASE_URL = "https://lnagadkqejnopgfxwlkb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxuYWdhZGtxZWpub3BnZnh3bGtiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTY3NDQ5NSwiZXhwIjoyMDc3MjUwNDk1fQ.nlEC-b2uw_PLAx3tJCPkyVbocsAVfcfnTiATtC96E50"

def main():
    # Create Supabase client with service role key (bypasses RLS)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("=" * 60)
    print("Fixing Ed Burns Name in Staff Members")
    print("=" * 60)

    email = "eburns009@gmail.com"

    # Check current name
    print(f"\n1. Current state:")
    try:
        current = supabase.table('staff_members').select('*').eq('email', email).execute()
        if current.data:
            print(f"   Email: {current.data[0]['email']}")
            print(f"   Display Name: {current.data[0].get('display_name', 'NULL')}")
            print(f"   Role: {current.data[0]['role']}")
        else:
            print(f"   ❌ No staff member found with email: {email}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Update name
    print(f"\n2. Updating display name to 'Ed Burns'...")
    try:
        update_result = supabase.table('staff_members').update({
            'display_name': 'Ed Burns'
        }).eq('email', email).execute()

        print(f"   ✅ Successfully updated!")
    except Exception as e:
        print(f"   ❌ Error updating: {e}")
        return

    # Verify
    print(f"\n3. Verification:")
    try:
        final = supabase.table('staff_members').select('*').eq('email', email).execute()
        if final.data:
            print(f"   Email: {final.data[0]['email']}")
            print(f"   Display Name: {final.data[0].get('display_name', 'NULL')}")
            print(f"   Role: {final.data[0]['role']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ NAME CORRECTED!")
    print("=" * 60)
    print("\nRefresh the /staff page to see 'Ed Burns'")
    print("=" * 60)

if __name__ == "__main__":
    main()
