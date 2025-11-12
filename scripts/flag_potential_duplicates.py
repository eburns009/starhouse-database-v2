#!/usr/bin/env python3
"""
Flag Potential Duplicates
=========================
Identifies and flags potential duplicate contacts in the database for UI review.

Duplicate Detection Logic:
1. Same first_name + last_name (different emails)
2. Optional: Same phone number
3. Optional: Same address

Creates flags in database so UI can show "Potential Duplicate" warnings.

Usage:
  # Dry-run (recommended first)
  python3 scripts/flag_potential_duplicates.py --dry-run

  # Execute (add flags to database)
  python3 scripts/flag_potential_duplicates.py --execute

  # Clear all flags
  python3 scripts/flag_potential_duplicates.py --clear
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from datetime import datetime
import json

def print_header(text):
    print("=" * 80)
    print(text)
    print("=" * 80)

def add_duplicate_flag_column(cur, dry_run=False):
    """Add potential_duplicate_group column if it doesn't exist"""

    # Check if column exists
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='contacts'
        AND column_name='potential_duplicate_group';
    """)

    if cur.fetchone():
        print("✓ Column 'potential_duplicate_group' already exists")
        return False

    if dry_run:
        print("[DRY-RUN] Would add column 'potential_duplicate_group' to contacts table")
        return True

    # Add column
    cur.execute("""
        ALTER TABLE contacts
        ADD COLUMN potential_duplicate_group TEXT,
        ADD COLUMN potential_duplicate_reason TEXT,
        ADD COLUMN potential_duplicate_flagged_at TIMESTAMPTZ;
    """)

    # Add index for performance
    cur.execute("""
        CREATE INDEX idx_contacts_duplicate_group
        ON contacts(potential_duplicate_group)
        WHERE potential_duplicate_group IS NOT NULL;
    """)

    print("✓ Added duplicate flag columns to contacts table")
    return True

def find_duplicate_groups(cur):
    """Find groups of potential duplicates"""

    # Find name-based duplicates (same first + last name)
    # Use STRING_AGG with delimiter we can split on
    cur.execute("""
        SELECT
            first_name,
            last_name,
            COUNT(*) as contact_count,
            STRING_AGG(id::text, '||' ORDER BY created_at) as contact_ids_str,
            STRING_AGG(email, '||' ORDER BY created_at) as emails_str,
            STRING_AGG(COALESCE(phone, ''), '||' ORDER BY created_at) as phones_str,
            STRING_AGG(COALESCE(address_line_1, ''), '||' ORDER BY created_at) as addresses_str,
            -- Check if phones match
            COUNT(DISTINCT phone) FILTER (WHERE phone IS NOT NULL AND phone != '') as unique_phones,
            -- Check if addresses match
            COUNT(DISTINCT address_line_1) FILTER (WHERE address_line_1 IS NOT NULL AND address_line_1 != '') as unique_addresses
        FROM contacts
        WHERE deleted_at IS NULL
          AND source_system = 'kajabi'
          AND first_name IS NOT NULL
          AND last_name IS NOT NULL
          AND first_name != ''
          AND last_name != ''
        GROUP BY first_name, last_name
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC, last_name, first_name;
    """)

    groups = []
    for row in cur.fetchall():
        # Create unique group ID
        group_id = f"name_{row['first_name'].lower().replace(' ', '_')}_{row['last_name'].lower().replace(' ', '_')}"

        # Determine confidence level
        if row['unique_phones'] == 1 and row['unique_addresses'] == 1:
            confidence = 'high'  # Same name, phone, AND address
            reason = f"Same name + phone + address"
        elif row['unique_phones'] == 1:
            confidence = 'high'  # Same name + phone
            reason = f"Same name + phone"
        elif row['unique_addresses'] == 1:
            confidence = 'medium'  # Same name + address
            reason = f"Same name + address"
        else:
            confidence = 'low'  # Just same name
            reason = f"Same name ({row['contact_count']} accounts)"

        # Split strings into lists
        contact_ids = row['contact_ids_str'].split('||') if row['contact_ids_str'] else []
        emails = row['emails_str'].split('||') if row['emails_str'] else []
        phones = row['phones_str'].split('||') if row['phones_str'] else []
        addresses = row['addresses_str'].split('||') if row['addresses_str'] else []

        groups.append({
            'group_id': group_id,
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'contact_count': row['contact_count'],
            'contact_ids': contact_ids,
            'emails': emails,
            'phones': phones,
            'addresses': addresses,
            'confidence': confidence,
            'reason': reason
        })

    return groups

def flag_duplicates(cur, groups, dry_run=False):
    """Apply duplicate flags to contacts"""

    stats = {
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'total_contacts_flagged': 0
    }

    for group in groups:
        # Update each contact in the group
        for contact_id in group['contact_ids']:
            if dry_run:
                stats['total_contacts_flagged'] += 1
                if group['confidence'] == 'high':
                    stats['high_confidence'] += 1
                elif group['confidence'] == 'medium':
                    stats['medium_confidence'] += 1
                else:
                    stats['low_confidence'] += 1
            else:
                cur.execute("""
                    UPDATE contacts
                    SET potential_duplicate_group = %s,
                        potential_duplicate_reason = %s,
                        potential_duplicate_flagged_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """, (group['group_id'], group['reason'], contact_id))

                stats['total_contacts_flagged'] += 1
                if group['confidence'] == 'high':
                    stats['high_confidence'] += 1
                elif group['confidence'] == 'medium':
                    stats['medium_confidence'] += 1
                else:
                    stats['low_confidence'] += 1

    return stats

def clear_duplicate_flags(cur, dry_run=False):
    """Clear all duplicate flags"""

    if dry_run:
        cur.execute("""
            SELECT COUNT(*)
            FROM contacts
            WHERE potential_duplicate_group IS NOT NULL
        """)
        count = cur.fetchone()[0]
        print(f"[DRY-RUN] Would clear flags from {count} contacts")
        return count

    cur.execute("""
        UPDATE contacts
        SET potential_duplicate_group = NULL,
            potential_duplicate_reason = NULL,
            potential_duplicate_flagged_at = NULL,
            updated_at = NOW()
        WHERE potential_duplicate_group IS NOT NULL
    """)

    count = cur.rowcount
    print(f"✓ Cleared flags from {count} contacts")
    return count

def print_sample_duplicates(groups, limit=10):
    """Print sample duplicates for review"""

    print(f"\nSample Duplicate Groups (showing {limit}):")
    print("-" * 80)

    for i, group in enumerate(groups[:limit], 1):
        print(f"\n{i}. {group['first_name']} {group['last_name']} ({group['contact_count']} accounts)")
        print(f"   Confidence: {group['confidence'].upper()}")
        print(f"   Reason: {group['reason']}")
        print(f"   Emails:")
        # Handle both list and array types
        emails = group['emails'] if isinstance(group['emails'], list) else list(group['emails'])
        for email in emails:
            if email:  # Skip None/empty
                print(f"     - {email}")
        # Handle phones
        phones = group['phones'] if isinstance(group['phones'], list) else list(group['phones'])
        phone_set = set([p for p in phones if p])
        if phone_set:
            print(f"   Phones: {', '.join(phone_set)}")

def main():
    # Parse args
    dry_run = '--execute' not in sys.argv
    clear_mode = '--clear' in sys.argv

    print_header("POTENTIAL DUPLICATE FLAGGING")
    print(f"Mode: {'CLEAR' if clear_mode else ('DRY-RUN' if dry_run else 'EXECUTE')}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not dry_run and not clear_mode:
        print("\n⚠️  EXECUTE MODE - Changes will be made!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n")

    # Connect to database
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.set_session(autocommit=False)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # Clear mode
            if clear_mode:
                print("\n" + "=" * 80)
                print("CLEARING DUPLICATE FLAGS")
                print("=" * 80)
                count = clear_duplicate_flags(cur, dry_run)

                if not dry_run:
                    conn.commit()
                    print(f"\n✓ Transaction committed - {count} contacts cleared")
                else:
                    conn.rollback()

                return

            # Add column if needed
            print("\n" + "=" * 80)
            print("STEP 1: CHECK DATABASE SCHEMA")
            print("=" * 80)
            add_duplicate_flag_column(cur, dry_run)

            # Find duplicates
            print("\n" + "=" * 80)
            print("STEP 2: FINDING DUPLICATE GROUPS")
            print("=" * 80)

            groups = find_duplicate_groups(cur)

            print(f"\nFound {len(groups)} duplicate groups:")

            # Count by confidence
            high = len([g for g in groups if g['confidence'] == 'high'])
            medium = len([g for g in groups if g['confidence'] == 'medium'])
            low = len([g for g in groups if g['confidence'] == 'low'])

            print(f"  🔴 High confidence (name + phone/address): {high}")
            print(f"  🟡 Medium confidence (name + address): {medium}")
            print(f"  🟢 Low confidence (name only): {low}")

            # Print samples
            print_sample_duplicates(groups, limit=15)

            # Flag duplicates
            print("\n" + "=" * 80)
            print("STEP 3: FLAGGING DUPLICATES")
            print("=" * 80)

            stats = flag_duplicates(cur, groups, dry_run)

            print(f"\n{'[DRY-RUN] Would flag' if dry_run else 'Flagged'} {stats['total_contacts_flagged']} contacts:")
            print(f"  🔴 High confidence: {stats['high_confidence']}")
            print(f"  🟡 Medium confidence: {stats['medium_confidence']}")
            print(f"  🟢 Low confidence: {stats['low_confidence']}")

            # Commit or rollback
            if dry_run:
                conn.rollback()
                print("\n✓ DRY-RUN: All changes rolled back")
            else:
                conn.commit()
                print("\n✓ COMMITTED: All changes saved")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

    # Print next steps
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)

    if dry_run:
        print("\nTo apply flags to database:")
        print("  python3 scripts/flag_potential_duplicates.py --execute")
        print("\nTo clear all flags:")
        print("  python3 scripts/flag_potential_duplicates.py --clear")
    else:
        print("\nDuplicate flags have been added to the database!")
        print("\nNext: Update the UI to show duplicate warnings")
        print("  1. Show 'Potential Duplicate' badge in contact list")
        print("  2. Add 'View Duplicates' button to contact detail page")
        print("  3. Create admin page to review and merge duplicates")
        print("\nTo clear flags later:")
        print("  python3 scripts/flag_potential_duplicates.py --clear")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
