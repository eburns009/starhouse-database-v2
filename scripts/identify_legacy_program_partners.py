#!/usr/bin/env python3
"""
Legacy Program Partner Identifier
==================================
Helps identify Individual members who should be classified as Program Partners
by analyzing:
1. PayPal transaction data (Item Title)
2. Current database tags
3. Manual list provided by user

Usage:
    python3 scripts/identify_legacy_program_partners.py
"""

import csv
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secure_config import get_database_url


# Database connection string
# Database connection - NO DEFAULTS, fails fast if missing
DB_CONNECTION = get_database_url()

def load_paypal_data(filepath):
    """Load PayPal export and categorize by membership type"""
    individual_members = defaultdict(lambda: {'transactions': [], 'item_titles': set()})
    program_partners = defaultdict(lambda: {'transactions': [], 'item_titles': set()})

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['Type'] != 'Subscription Payment' or row['Status'] != 'Completed':
                continue

            email = row['From Email Address'].strip().lower()
            item_title = row['Item Title'].strip()

            # Classify based on Item Title
            is_program_partner = any(keyword in item_title.lower() for keyword in
                                    ['program partner', 'luminary', 'celestial', 'astral'])

            if is_program_partner:
                program_partners[email]['transactions'].append(row)
                program_partners[email]['item_titles'].add(item_title)
            else:
                individual_members[email]['transactions'].append(row)
                individual_members[email]['item_titles'].add(item_title)

    return individual_members, program_partners

def get_current_tags(conn):
    """Get all tags from database"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT
            t.name as tag_name,
            COUNT(ct.contact_id) as contact_count
        FROM tags t
        LEFT JOIN contact_tags ct ON t.id = ct.tag_id
        GROUP BY t.id, t.name
        ORDER BY t.name
    """)
    return cursor.fetchall()

def get_contacts_by_tag(conn, tag_pattern):
    """Get contacts matching tag pattern"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT DISTINCT
            c.email,
            c.first_name,
            c.last_name,
            array_agg(DISTINCT t.name) as tags
        FROM contacts c
        JOIN contact_tags ct ON c.id = ct.contact_id
        JOIN tags t ON ct.tag_id = t.id
        WHERE t.name ILIKE %s
        GROUP BY c.id, c.email, c.first_name, c.last_name
        ORDER BY c.last_name, c.first_name
    """, (f'%{tag_pattern}%',))
    return cursor.fetchall()

def main():
    print("="*100)
    print("LEGACY PROGRAM PARTNER IDENTIFICATION TOOL")
    print("="*100)

    # Load PayPal data
    print("\n1️⃣  Analyzing PayPal Transaction Data...")
    print("-"*100)

    individual_members, program_partners = load_paypal_data('data/Paypal_Import')

    print(f"\n✅ Found in PayPal data:")
    print(f"   Program Partners (by Item Title): {len(program_partners)} unique emails")
    print(f"   Individual Members (by Item Title): {len(individual_members)} unique emails")

    # Find people who have BOTH individual and program partner payments
    conflicting_emails = set(individual_members.keys()) & set(program_partners.keys())

    if conflicting_emails:
        print(f"\n⚠️  ATTENTION: {len(conflicting_emails)} people have BOTH Individual AND Program Partner payments!")
        print(f"   These are likely legacy Program Partners who are now on Individual plans:")
        print()
        for email in sorted(conflicting_emails):
            ind_titles = individual_members[email]['item_titles']
            pp_titles = program_partners[email]['item_titles']
            print(f"   📧 {email}")
            print(f"      Individual payments: {', '.join(sorted(ind_titles))}")
            print(f"      Program Partner payments: {', '.join(sorted(pp_titles))}")
            print()

    # Try to connect to database and check tags
    print("\n2️⃣  Checking Database Tags...")
    print("-"*100)

    try:
        conn = psycopg2.connect(DB_CONNECTION)

        # Get all tags
        print("\n📋 All tags in database:")
        all_tags = get_current_tags(conn)

        partner_related_tags = []
        for tag in all_tags:
            tag_name = tag['tag_name'].lower()
            if any(keyword in tag_name for keyword in ['partner', 'program', 'luminary', 'celestial', 'astral']):
                partner_related_tags.append(tag)
                print(f"   ⭐ {tag['tag_name']:40} ({tag['contact_count']} contacts)")
            elif tag['contact_count'] > 0:
                print(f"      {tag['tag_name']:40} ({tag['contact_count']} contacts)")

        # Get contacts with Program Partner tags
        if partner_related_tags:
            print("\n3️⃣  Contacts with Program Partner Tags...")
            print("-"*100)

            for tag_info in partner_related_tags:
                tag_name = tag_info['tag_name']
                print(f"\n🏷️  Tag: '{tag_name}' ({tag_info['contact_count']} contacts)")

                contacts = get_contacts_by_tag(conn, tag_name.split()[0])  # Match first word

                for contact in contacts[:10]:  # Show first 10
                    print(f"   • {contact['first_name']} {contact['last_name']:20} <{contact['email']}>")
                    print(f"     Tags: {', '.join(contact['tags'])}")

                if len(contacts) > 10:
                    print(f"   ... and {len(contacts) - 10} more")

        conn.close()

    except Exception as e:
        print(f"⚠️  Could not connect to database: {e}")
        print("   Skipping tag analysis (you can still review PayPal data above)")

    # Generate recommendations
    print("\n\n4️⃣  RECOMMENDATIONS")
    print("="*100)

    print("""
Based on the analysis, here's how to proceed:

OPTION A: Create a Manual List (Recommended if you know the names)
─────────────────────────────────────────────────────────────────
Create a CSV file with the legacy Program Partners:

File: data/legacy_program_partners.csv
Format:
email,correct_level,notes
counselingwholelife@gmail.com,Luminary Partner,Was on Antares but should be Luminary
d.caracciolo0808@gmail.com,Celestial Partner,Was on Antares but should be Celestial

Then I'll update the import script to check this list and classify correctly.


OPTION B: Tag-Based Classification (If tags are accurate)
──────────────────────────────────────────────────────────
If the database tags correctly identify Program Partners, I can:
1. Query tags before import
2. Auto-classify those contacts as Program Partners
3. Override the PayPal Item Title classification


OPTION C: Import First, Fix Later (Not recommended)
────────────────────────────────────────────────────
1. Import everything as-is
2. Use legacy_program_partner_corrections table
3. Run bulk update script later

This works but creates temporary incorrect data.


OPTION D: Hybrid Approach (Best of both worlds)
────────────────────────────────────────────────
1. You provide a list of known legacy Program Partners
2. I also check for Program Partner tags in database
3. Import script prioritizes: Manual list > Tags > PayPal Item Title
4. Any remaining edge cases go to corrections table

""")

    if conflicting_emails:
        print(f"⚠️  IMPORTANT: You have {len(conflicting_emails)} people with BOTH types of payments.")
        print(f"   Please review the list above and decide their correct classification.")
        print(f"\n   Quick check - are these people currently Program Partners?")
        print(f"   If YES: They should be classified as Program Partner")
        print(f"   If NO: They were Program Partners but downgraded to Individual")

    print("\n\n" + "="*100)
    print("NEXT STEPS")
    print("="*100)
    print("""
1. Review the conflicting emails above (if any)
2. Choose your preferred approach (A, B, C, or D)
3. If Option A or D: Create data/legacy_program_partners.csv
4. Let me know which option you prefer, and I'll:
   - Update the import script accordingly
   - OR help you create the corrections list
   - OR proceed with standard import

What would you like to do?
""")

if __name__ == '__main__':
    main()
