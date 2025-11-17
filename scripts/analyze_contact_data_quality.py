#!/usr/bin/env python3
"""
FAANG-Quality Contact Data Quality Analysis
Analyzes contacts table to identify enrichment opportunities

Focus Areas:
- Name completeness and variations
- Email consolidation opportunities
- Phone number enrichment
- Duplicate detection strategies
- Data source utilization
"""

import psycopg2
from collections import Counter, defaultdict
import re

DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

def analyze_name_data(cursor):
    """Analyze name field completeness and opportunities."""

    print("=" * 80)
    print("1. NAME DATA ANALYSIS")
    print("=" * 80)
    print()

    # Basic name completeness
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(first_name) as has_first_name,
            COUNT(last_name) as has_last_name,
            COUNT(CASE WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN 1 END) as has_full_name,
            COUNT(additional_name) as has_additional_name,
            COUNT(paypal_first_name) as has_paypal_first_name,
            COUNT(paypal_last_name) as has_paypal_last_name,
            COUNT(paypal_business_name) as has_business_name
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    row = cursor.fetchone()
    total = row[0]

    print("📊 NAME COMPLETENESS")
    print(f"   Total contacts: {total:,}")
    print(f"   Has first_name: {row[1]:,} ({row[1]/total*100:.1f}%)")
    print(f"   Has last_name: {row[2]:,} ({row[2]/total*100:.1f}%)")
    print(f"   Has BOTH (full name): {row[3]:,} ({row[3]/total*100:.1f}%)")
    print(f"   Has additional_name: {row[4]:,} ({row[4]/total*100:.1f}%)")
    print(f"   Has paypal_first_name: {row[5]:,} ({row[5]/total*100:.1f}%)")
    print(f"   Has paypal_last_name: {row[6]:,} ({row[6]/total*100:.1f}%)")
    print(f"   Has business_name: {row[7]:,} ({row[7]/total*100:.1f}%)")
    print()

    # Opportunities: PayPal names not copied to primary
    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND (first_name IS NULL OR last_name IS NULL)
          AND paypal_first_name IS NOT NULL
          AND paypal_last_name IS NOT NULL
    """)

    paypal_name_opps = cursor.fetchone()[0]
    print("💡 NAME ENRICHMENT OPPORTUNITIES")
    print(f"   Contacts missing primary name but have PayPal name: {paypal_name_opps:,}")

    # Additional names that could be parsed
    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND additional_name IS NOT NULL
          AND (first_name IS NULL OR last_name IS NULL)
    """)

    additional_name_opps = cursor.fetchone()[0]
    print(f"   Contacts with additional_name but incomplete primary: {additional_name_opps:,}")

    # Check contact_names table usage
    cursor.execute("""
        SELECT
            COUNT(DISTINCT contact_id) as contacts_with_alt_names,
            COUNT(*) as total_alt_names,
            COUNT(CASE WHEN name_type = 'business' THEN 1 END) as business_names,
            COUNT(CASE WHEN name_type = 'nickname' THEN 1 END) as nicknames,
            COUNT(CASE WHEN name_type = 'maiden' THEN 1 END) as maiden_names
        FROM contact_names
    """)

    row = cursor.fetchone()
    if row[0]:
        print()
        print("📋 CONTACT_NAMES TABLE USAGE")
        print(f"   Contacts with alternative names: {row[0]:,}")
        print(f"   Total alternative names stored: {row[1]:,}")
        print(f"   Business names: {row[2]:,}")
        print(f"   Nicknames: {row[3]:,}")
        print(f"   Maiden names: {row[4]:,}")

    print()
    return {
        'paypal_name_opps': paypal_name_opps,
        'additional_name_opps': additional_name_opps
    }


def analyze_email_data(cursor):
    """Analyze email field completeness and consolidation opportunities."""

    print("=" * 80)
    print("2. EMAIL DATA ANALYSIS")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(email) as has_primary_email,
            COUNT(paypal_email) as has_paypal_email,
            COUNT(additional_email) as has_additional_email,
            COUNT(zoho_email) as has_zoho_email,
            COUNT(CASE WHEN secondary_emails != '[]'::jsonb THEN 1 END) as has_secondary_emails
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    row = cursor.fetchone()
    total = row[0]

    print("📊 EMAIL COMPLETENESS")
    print(f"   Total contacts: {total:,}")
    print(f"   Has primary email: {row[1]:,} ({row[1]/total*100:.1f}%)")
    print(f"   Has paypal_email: {row[2]:,} ({row[2]/total*100:.1f}%)")
    print(f"   Has additional_email: {row[3]:,} ({row[3]/total*100:.1f}%)")
    print(f"   Has zoho_email: {row[4]:,} ({row[4]/total*100:.1f}%)")
    print(f"   Has secondary_emails (JSONB): {row[5]:,} ({row[5]/total*100:.1f}%)")
    print()

    # Email mismatches - different emails in different fields
    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND paypal_email IS NOT NULL
          AND email != paypal_email
    """)

    email_mismatches = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND additional_email IS NOT NULL
          AND email != additional_email
    """)

    additional_different = cursor.fetchone()[0]

    print("💡 EMAIL CONSOLIDATION OPPORTUNITIES")
    print(f"   PayPal email differs from primary: {email_mismatches:,}")
    print(f"   Additional email differs from primary: {additional_different:,}")

    # Check contact_emails table usage
    cursor.execute("""
        SELECT
            COUNT(DISTINCT contact_id) as contacts_with_multi_emails,
            COUNT(*) as total_emails,
            COUNT(CASE WHEN email_type = 'work' THEN 1 END) as work_emails,
            COUNT(CASE WHEN email_type = 'personal' THEN 1 END) as personal_emails,
            COUNT(CASE WHEN is_outreach = true THEN 1 END) as outreach_emails,
            COUNT(CASE WHEN deliverable = true THEN 1 END) as deliverable_emails
        FROM contact_emails
    """)

    row = cursor.fetchone()
    if row[0]:
        print()
        print("📋 CONTACT_EMAILS TABLE USAGE")
        print(f"   Contacts with multiple emails: {row[0]:,}")
        print(f"   Total emails stored: {row[1]:,}")
        print(f"   Work emails: {row[2]:,}")
        print(f"   Personal emails: {row[3]:,}")
        print(f"   Outreach emails: {row[4]:,}")
        print(f"   Deliverable (verified): {row[5]:,}")

    print()
    return {
        'email_mismatches': email_mismatches,
        'additional_different': additional_different
    }


def analyze_phone_data(cursor):
    """Analyze phone number completeness and opportunities."""

    print("=" * 80)
    print("3. PHONE DATA ANALYSIS")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(phone) as has_phone,
            COUNT(paypal_phone) as has_paypal_phone,
            COUNT(additional_phone) as has_additional_phone,
            COUNT(zoho_phone) as has_zoho_phone,
            COUNT(CASE WHEN phone_verified = true THEN 1 END) as phone_verified_count
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    row = cursor.fetchone()
    total = row[0]

    print("📊 PHONE COMPLETENESS")
    print(f"   Total contacts: {total:,}")
    print(f"   Has phone: {row[1]:,} ({row[1]/total*100:.1f}%)")
    print(f"   Has paypal_phone: {row[2]:,} ({row[2]/total*100:.1f}%)")
    print(f"   Has additional_phone: {row[3]:,} ({row[3]/total*100:.1f}%)")
    print(f"   Has zoho_phone: {row[4]:,} ({row[4]/total*100:.1f}%)")
    print(f"   Phone verified: {row[5]:,} ({row[5]/row[1]*100 if row[1] > 0 else 0:.1f}% of those with phone)")
    print()

    # Phone enrichment opportunities
    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND phone IS NULL
          AND (paypal_phone IS NOT NULL OR additional_phone IS NOT NULL OR zoho_phone IS NOT NULL)
    """)

    phone_opps = cursor.fetchone()[0]

    print("💡 PHONE ENRICHMENT OPPORTUNITIES")
    print(f"   Contacts missing primary phone but have alt phone: {phone_opps:,}")

    # Different phone numbers
    cursor.execute("""
        SELECT COUNT(*)
        FROM contacts
        WHERE deleted_at IS NULL
          AND phone IS NOT NULL
          AND additional_phone IS NOT NULL
          AND phone != additional_phone
    """)

    different_phones = cursor.fetchone()[0]
    print(f"   Contacts with different primary and additional phone: {different_phones:,}")

    print()
    return {
        'phone_opps': phone_opps,
        'different_phones': different_phones
    }


def analyze_duplicates(cursor):
    """Analyze potential duplicate contacts."""

    print("=" * 80)
    print("4. DUPLICATE DETECTION ANALYSIS")
    print("=" * 80)
    print()

    # Exact email duplicates (shouldn't exist due to unique constraint, but check other emails)
    cursor.execute("""
        SELECT
            paypal_email,
            COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
          AND paypal_email IS NOT NULL
        GROUP BY paypal_email
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)

    paypal_email_dupes = cursor.fetchall()

    if paypal_email_dupes:
        print("⚠️  DUPLICATE PAYPAL EMAILS (same PayPal email, different contacts)")
        for email, count in paypal_email_dupes[:5]:
            print(f"   {email}: {count} contacts")
        print()

    # Name duplicates (exact match)
    cursor.execute("""
        SELECT
            first_name,
            last_name,
            COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
          AND first_name IS NOT NULL
          AND last_name IS NOT NULL
        GROUP BY first_name, last_name
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)

    name_dupes = cursor.fetchall()
    total_name_dupes = sum(row[2] for row in name_dupes)

    if name_dupes:
        print("⚠️  DUPLICATE NAMES (same first + last name, different contacts)")
        for first, last, count in name_dupes[:5]:
            print(f"   {first} {last}: {count} contacts")
        print(f"   Total duplicate name groups (top 10): {len(name_dupes)}")
        print()

    # Check if duplicates are flagged
    cursor.execute("""
        SELECT
            COUNT(*) as total_flagged,
            COUNT(DISTINCT potential_duplicate_group) as unique_groups
        FROM contacts
        WHERE deleted_at IS NULL
          AND potential_duplicate_group IS NOT NULL
    """)

    row = cursor.fetchone()
    if row[0]:
        print("🏴 FLAGGED DUPLICATES")
        print(f"   Contacts flagged as potential duplicates: {row[0]:,}")
        print(f"   Unique duplicate groups: {row[1]:,}")
        print()

    return {
        'paypal_email_dupes': len(paypal_email_dupes),
        'name_dupes': len(name_dupes)
    }


def analyze_source_utilization(cursor):
    """Analyze how well we're using data from different sources."""

    print("=" * 80)
    print("5. DATA SOURCE UTILIZATION")
    print("=" * 80)
    print()

    # Source field utilization
    cursor.execute("""
        SELECT
            additional_name_source,
            COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
          AND additional_name IS NOT NULL
        GROUP BY additional_name_source
        ORDER BY count DESC
    """)

    name_sources = cursor.fetchall()
    if name_sources:
        print("📊 ADDITIONAL NAME SOURCES")
        for source, count in name_sources:
            print(f"   {source or '(null)'}: {count:,}")
        print()

    cursor.execute("""
        SELECT
            additional_email_source,
            COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
          AND additional_email IS NOT NULL
        GROUP BY additional_email_source
        ORDER BY count DESC
    """)

    email_sources = cursor.fetchall()
    if email_sources:
        print("📧 ADDITIONAL EMAIL SOURCES")
        for source, count in email_sources:
            print(f"   {source or '(null)'}: {count:,}")
        print()

    cursor.execute("""
        SELECT
            additional_phone_source,
            COUNT(*) as count
        FROM contacts
        WHERE deleted_at IS NULL
          AND additional_phone IS NOT NULL
        GROUP BY additional_phone_source
        ORDER BY count DESC
    """)

    phone_sources = cursor.fetchall()
    if phone_sources:
        print("📞 ADDITIONAL PHONE SOURCES")
        for source, count in phone_sources:
            print(f"   {source or '(null)'}: {count:,}")
        print()


def generate_recommendations(name_data, email_data, phone_data, dupe_data):
    """Generate FAANG-quality recommendations."""

    print("=" * 80)
    print("6. FAANG ENGINEERING RECOMMENDATIONS")
    print("=" * 80)
    print()

    recommendations = []

    # Rec 1: Name consolidation
    if name_data['paypal_name_opps'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Name Enrichment',
            'action': 'Copy PayPal names to primary name fields',
            'impact': f"{name_data['paypal_name_opps']} contacts",
            'effort': 'Low',
            'script': 'enrich_names_from_paypal.py'
        })

    if name_data['additional_name_opps'] > 0:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Name Enrichment',
            'action': 'Parse additional_name to extract first/last',
            'impact': f"{name_data['additional_name_opps']} contacts",
            'effort': 'Medium (requires name parsing logic)',
            'script': 'parse_additional_names.py'
        })

    # Rec 2: Email consolidation
    if email_data['email_mismatches'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Email Consolidation',
            'action': 'Migrate PayPal emails to contact_emails table',
            'impact': f"{email_data['email_mismatches']} contacts with alternative emails",
            'effort': 'Low',
            'script': 'migrate_emails_to_contact_emails.py'
        })

    if email_data['additional_different'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Email Consolidation',
            'action': 'Migrate additional_email to contact_emails table',
            'impact': f"{email_data['additional_different']} contacts",
            'effort': 'Low',
            'script': 'migrate_additional_emails.py'
        })

    # Rec 3: Phone enrichment
    if phone_data['phone_opps'] > 0:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Phone Enrichment',
            'action': 'Copy alternative phones to primary phone field',
            'impact': f"{phone_data['phone_opps']} contacts gain primary phone",
            'effort': 'Low',
            'script': 'enrich_phones_from_alternatives.py'
        })

    # Rec 4: Duplicate resolution
    if dupe_data['paypal_email_dupes'] > 0 or dupe_data['name_dupes'] > 0:
        recommendations.append({
            'priority': 'CRITICAL',
            'category': 'Data Quality',
            'action': 'Review and merge duplicate contacts',
            'impact': f"{dupe_data['paypal_email_dupes'] + dupe_data['name_dupes']} duplicate groups",
            'effort': 'High (requires manual review)',
            'script': 'merge_duplicate_contacts.py'
        })

    # Rec 5: Structured data migration
    recommendations.append({
        'priority': 'LOW',
        'category': 'Schema Modernization',
        'action': 'Migrate all emails/names to contact_emails/contact_names tables',
        'impact': 'Better multi-value support, cleaner schema',
        'effort': 'High (schema migration)',
        'script': 'migrate_to_structured_tables.py'
    })

    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['priority']}] {rec['action']}")
        print(f"   Category: {rec['category']}")
        print(f"   Impact: {rec['impact']}")
        print(f"   Effort: {rec['effort']}")
        print(f"   Suggested script: {rec['script']}")
        print()

    return recommendations


def main():
    """Main execution."""

    print("=" * 80)
    print("CONTACT DATA QUALITY ANALYSIS - FAANG Engineering")
    print("=" * 80)
    print()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Run all analyses
    name_data = analyze_name_data(cursor)
    email_data = analyze_email_data(cursor)
    phone_data = analyze_phone_data(cursor)
    dupe_data = analyze_duplicates(cursor)
    analyze_source_utilization(cursor)
    recommendations = generate_recommendations(name_data, email_data, phone_data, dupe_data)

    # Summary
    print("=" * 80)
    print("EXECUTIVE SUMMARY")
    print("=" * 80)
    print()
    print(f"📊 Total Enrichment Opportunities:")
    print(f"   Name enrichment: {name_data['paypal_name_opps'] + name_data['additional_name_opps']:,}")
    print(f"   Email consolidation: {email_data['email_mismatches'] + email_data['additional_different']:,}")
    print(f"   Phone enrichment: {phone_data['phone_opps']:,}")
    print(f"   Duplicate groups: {dupe_data['paypal_email_dupes'] + dupe_data['name_dupes']:,}")
    print()
    print(f"📝 Actionable Recommendations: {len(recommendations)}")
    print()

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
