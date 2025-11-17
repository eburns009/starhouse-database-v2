#!/usr/bin/env python3
"""
Comprehensive Database Contacts Summary
FAANG-Grade Analysis: Complete overview of contact database

Provides:
1. Total contacts and growth
2. Data completeness statistics
3. Source attribution breakdown
4. Tag statistics
5. Geographic distribution
6. Recent activity
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import Counter
from db_config import get_database_url

def format_number(num):
    """Format number with commas"""
    return f"{num:,}"

def get_database_summary():
    """Generate comprehensive database summary"""

    print("=" * 80)
    print("STARHOUSE CONTACT DATABASE - COMPREHENSIVE SUMMARY")
    print("=" * 80)
    print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.lnagadkqejnopgfxwlkb',
        password=get_database_url().split('@')[0].split(':')[-1],
        host='aws-1-us-east-2.pooler.supabase.com',
        port='5432'
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("   Connected ✓\n")

    # 1. TOTAL CONTACTS
    print("📊 TOTAL CONTACTS")
    print("-" * 80)

    cur.execute("SELECT COUNT(*) as total FROM contacts")
    total_contacts = cur.fetchone()['total']
    print(f"Total contacts in database: {format_number(total_contacts)}\n")

    # 2. DATA COMPLETENESS
    print("📋 DATA COMPLETENESS")
    print("-" * 80)

    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(email) as has_email,
            COUNT(paypal_email) as has_paypal_email,
            COUNT(phone) as has_phone,
            COUNT(paypal_business_name) as has_organization,
            COUNT(address_line_1) as has_address,
            COUNT(city) as has_city,
            COUNT(state) as has_state,
            COUNT(postal_code) as has_postal_code
        FROM contacts
    """)
    completeness = cur.fetchone()

    total = completeness['total']
    print(f"Primary Email:     {format_number(completeness['has_email']):>6} ({completeness['has_email']/total*100:>5.1f}%)")
    print(f"PayPal Email:      {format_number(completeness['has_paypal_email']):>6} ({completeness['has_paypal_email']/total*100:>5.1f}%)")
    print(f"Phone:             {format_number(completeness['has_phone']):>6} ({completeness['has_phone']/total*100:>5.1f}%)")
    print(f"Organization:      {format_number(completeness['has_organization']):>6} ({completeness['has_organization']/total*100:>5.1f}%)")
    print(f"Address (line 1):  {format_number(completeness['has_address']):>6} ({completeness['has_address']/total*100:>5.1f}%)")
    print(f"City:              {format_number(completeness['has_city']):>6} ({completeness['has_city']/total*100:>5.1f}%)")
    print(f"State:             {format_number(completeness['has_state']):>6} ({completeness['has_state']/total*100:>5.1f}%)")
    print(f"Postal Code:       {format_number(completeness['has_postal_code']):>6} ({completeness['has_postal_code']/total*100:>5.1f}%)")
    print()

    # 3. SOURCE ATTRIBUTION
    print("🏷️  SOURCE ATTRIBUTION")
    print("-" * 80)

    # Phone sources
    cur.execute("""
        SELECT phone_source, COUNT(*) as count
        FROM contacts
        WHERE phone IS NOT NULL
        GROUP BY phone_source
        ORDER BY count DESC
    """)
    print("Phone Sources:")
    for row in cur.fetchall():
        source = row['phone_source'] or 'unknown'
        print(f"  {source:<20} {format_number(row['count']):>6} contacts")

    # Address sources
    cur.execute("""
        SELECT billing_address_source, COUNT(*) as count
        FROM contacts
        WHERE address_line_1 IS NOT NULL
        GROUP BY billing_address_source
        ORDER BY count DESC
    """)
    print("\nAddress Sources:")
    for row in cur.fetchall():
        source = row['billing_address_source'] or 'unknown'
        print(f"  {source:<20} {format_number(row['count']):>6} contacts")
    print()

    # 4. ADDRESS VALIDATION STATUS
    print("✅ ADDRESS VALIDATION STATUS")
    print("-" * 80)

    cur.execute("""
        SELECT
            COUNT(CASE WHEN address_line_1 IS NOT NULL THEN 1 END) as total_addresses,
            COUNT(billing_usps_validated_at) as validated,
            COUNT(CASE WHEN billing_usps_dpv_match_code = 'Y' THEN 1 END) as fully_deliverable,
            COUNT(CASE WHEN billing_usps_vacant = true THEN 1 END) as vacant,
            COUNT(CASE WHEN billing_usps_county IS NOT NULL THEN 1 END) as has_county,
            COUNT(CASE WHEN billing_usps_latitude IS NOT NULL THEN 1 END) as geocoded
        FROM contacts
    """)
    validation = cur.fetchone()

    total_addr = validation['total_addresses']
    if total_addr > 0:
        print(f"Total Addresses:        {format_number(total_addr):>6}")
        print(f"USPS Validated:         {format_number(validation['validated']):>6} ({validation['validated']/total_addr*100:>5.1f}%)")
        print(f"Fully Deliverable:      {format_number(validation['fully_deliverable']):>6} ({validation['fully_deliverable']/total_addr*100:>5.1f}%)")
        print(f"With County Data:       {format_number(validation['has_county']):>6} ({validation['has_county']/total_addr*100:>5.1f}%)")
        print(f"Geocoded (lat/long):    {format_number(validation['geocoded']):>6} ({validation['geocoded']/total_addr*100:>5.1f}%)")
        print(f"Vacant (flagged):       {format_number(validation['vacant']):>6}")
    print()

    # 5. GEOGRAPHIC DISTRIBUTION
    print("🌎 GEOGRAPHIC DISTRIBUTION")
    print("-" * 80)

    # By state
    cur.execute("""
        SELECT state, COUNT(*) as count
        FROM contacts
        WHERE state IS NOT NULL
        GROUP BY state
        ORDER BY count DESC
        LIMIT 10
    """)
    print("Top 10 States:")
    for row in cur.fetchall():
        print(f"  {row['state']:<10} {format_number(row['count']):>6} contacts")

    # By county (validated addresses)
    cur.execute("""
        SELECT billing_usps_county, COUNT(*) as count
        FROM contacts
        WHERE billing_usps_county IS NOT NULL
        GROUP BY billing_usps_county
        ORDER BY count DESC
        LIMIT 10
    """)
    print("\nTop 10 Counties (USPS validated):")
    for row in cur.fetchall():
        print(f"  {row['billing_usps_county']:<20} {format_number(row['count']):>6} contacts")
    print()

    # 6. TAG STATISTICS
    print("🏷️  TAG STATISTICS")
    print("-" * 80)

    cur.execute("SELECT COUNT(*) as total FROM tags")
    total_tags = cur.fetchone()['total']
    print(f"Total tags: {format_number(total_tags)}\n")

    cur.execute("""
        SELECT t.name, COUNT(ct.contact_id) as contact_count
        FROM tags t
        LEFT JOIN contact_tags ct ON t.id = ct.tag_id
        GROUP BY t.id, t.name
        ORDER BY contact_count DESC
        LIMIT 20
    """)
    print("Top 20 Tags by Contact Count:")
    for row in cur.fetchall():
        print(f"  {row['name']:<40} {format_number(row['contact_count']):>6} contacts")
    print()

    # 7. RECENT ACTIVITY
    print("📅 RECENT ACTIVITY (Last 7 Days)")
    print("-" * 80)

    seven_days_ago = datetime.now() - timedelta(days=7)

    cur.execute("""
        SELECT COUNT(*) as count
        FROM contacts
        WHERE created_at >= %s
    """, (seven_days_ago,))
    new_contacts = cur.fetchone()['count']

    cur.execute("""
        SELECT COUNT(*) as count
        FROM contacts
        WHERE updated_at >= %s
    """, (seven_days_ago,))
    updated_contacts = cur.fetchone()['count']

    cur.execute("""
        SELECT COUNT(*) as count
        FROM contacts
        WHERE billing_usps_validated_at >= %s
    """, (seven_days_ago,))
    validated_recently = cur.fetchone()['count']

    print(f"New contacts created:      {format_number(new_contacts):>6}")
    print(f"Contacts updated:          {format_number(updated_contacts):>6}")
    print(f"Addresses validated:       {format_number(validated_recently):>6}")
    print()

    # 8. EMAIL SUBSCRIPTION STATUS
    print("📧 EMAIL SUBSCRIPTION STATUS")
    print("-" * 80)

    cur.execute("""
        SELECT
            COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed,
            COUNT(CASE WHEN email_subscribed = false THEN 1 END) as unsubscribed,
            COUNT(CASE WHEN email_subscribed IS NULL THEN 1 END) as unknown
        FROM contacts
    """)
    subs = cur.fetchone()

    print(f"Subscribed:    {format_number(subs['subscribed']):>6} ({subs['subscribed']/total*100:>5.1f}%)")
    print(f"Unsubscribed:  {format_number(subs['unsubscribed']):>6} ({subs['unsubscribed']/total*100:>5.1f}%)")
    print(f"Unknown:       {format_number(subs['unknown']):>6} ({subs['unknown']/total*100:>5.1f}%)")
    print()

    # 9. DATA QUALITY SCORE
    print("⭐ DATA QUALITY SCORE")
    print("-" * 80)

    cur.execute("""
        SELECT
            AVG(
                CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN address_line_1 IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN state IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN postal_code IS NOT NULL THEN 1 ELSE 0 END
            ) * 100.0 / 6 as avg_completeness
        FROM contacts
    """)
    quality = cur.fetchone()['avg_completeness']

    print(f"Average Data Completeness: {quality:.1f}% (of 6 key fields)")
    print()

    # 10. MEMBERSHIP CATEGORIES (from recent tags)
    print("👥 MEMBERSHIP CATEGORIES")
    print("-" * 80)

    cur.execute("""
        SELECT t.name, COUNT(ct.contact_id) as count
        FROM tags t
        JOIN contact_tags ct ON t.id = ct.tag_id
        WHERE t.name IN ('Paid Members', 'Complimentary Members', 'Current Keepers',
                         'Past Keepers', 'Preferred Keepers', 'Program Partner',
                         'Previous Program Partner', 'Made Donation')
        GROUP BY t.name
        ORDER BY count DESC
    """)
    print("Member Types:")
    for row in cur.fetchall():
        print(f"  {row['name']:<30} {format_number(row['count']):>6} contacts")
    print()

    # SUMMARY
    print("=" * 80)
    print("QUICK SUMMARY")
    print("=" * 80)
    print(f"Total Contacts:        {format_number(total_contacts)}")
    print(f"With Email:            {format_number(completeness['has_email'])} ({completeness['has_email']/total*100:.1f}%)")
    print(f"With Phone:            {format_number(completeness['has_phone'])} ({completeness['has_phone']/total*100:.1f}%)")
    print(f"With Address:          {format_number(completeness['has_address'])} ({completeness['has_address']/total*100:.1f}%)")
    print(f"USPS Validated:        {format_number(validation['validated'])} addresses")
    print(f"Email Subscribed:      {format_number(subs['subscribed'])} ({subs['subscribed']/total*100:.1f}%)")
    print(f"Total Tags:            {format_number(total_tags)}")
    print(f"Avg Completeness:      {quality:.1f}%")
    print("=" * 80)

    # Cleanup
    cur.close()
    conn.close()

if __name__ == '__main__':
    get_database_summary()
