#!/usr/bin/env python3
"""
Contact Enrichment - Final Pass
================================
Cross-source enrichment using phone, name, and address matching.

This script finds enrichment opportunities where:
1. Phone matches between Kajabi ↔ Ticket Tailor
2. Name + Address matches between Kajabi ↔ other sources
3. Missing phone numbers that can be filled from other sources

Run modes:
  --dry-run: Show what would be enriched (default)
  --execute: Actually update the database
"""

import psycopg2
import os
import sys
from datetime import datetime
import json

def print_header(text):
    print("=" * 80)
    print(text)
    print("=" * 80)

def get_enrichment_opportunities(cur):
    """Find all enrichment opportunities across sources."""
    opportunities = []

    # 1. Phone-based: Kajabi ↔ Ticket Tailor
    cur.execute("""
        SELECT
            k.id as kajabi_id,
            k.email as kajabi_email,
            k.first_name || ' ' || k.last_name as kajabi_name,
            k.phone as kajabi_phone,
            tt.id as tt_id,
            tt.email as tt_email,
            tt.first_name || ' ' || tt.last_name as tt_name,
            tt.phone as shared_phone,
            tt.ticket_tailor_id
        FROM contacts k
        INNER JOIN contacts tt ON k.phone = tt.phone
        WHERE k.deleted_at IS NULL
        AND tt.deleted_at IS NULL
        AND k.kajabi_id IS NOT NULL
        AND tt.source_system = 'ticket_tailor'
        AND k.ticket_tailor_id IS NULL
        AND k.phone IS NOT NULL
        AND k.phone != ''
        AND k.id != tt.id
    """)

    for row in cur.fetchall():
        opportunities.append({
            'type': 'phone_match_ticket_tailor',
            'kajabi_id': row[0],
            'kajabi_email': row[1],
            'kajabi_name': row[2],
            'signal': f'phone: {row[7]}',
            'action': 'add_ticket_tailor_id',
            'ticket_tailor_id': row[8],
            'tt_contact_id': row[4],
            'tt_email': row[5],
            'tt_name': row[6]
        })

    # 2. Name + Address: Kajabi missing phone ↔ Other sources have phone
    cur.execute("""
        SELECT
            k.id as kajabi_id,
            k.email as kajabi_email,
            k.first_name || ' ' || k.last_name as kajabi_name,
            k.phone as kajabi_phone,
            k.address_line_1,
            o.id as other_id,
            o.email as other_email,
            o.first_name || ' ' || o.last_name as other_name,
            o.phone as other_phone,
            o.source_system,
            o.ticket_tailor_id,
            k.ticket_tailor_id as kajabi_tt_id
        FROM contacts k
        INNER JOIN contacts o ON
            LOWER(TRIM(k.address_line_1)) = LOWER(TRIM(o.address_line_1))
            AND LOWER(TRIM(k.last_name)) = LOWER(TRIM(o.last_name))
        WHERE k.deleted_at IS NULL
        AND o.deleted_at IS NULL
        AND k.kajabi_id IS NOT NULL
        AND o.kajabi_id IS NULL
        AND (k.phone IS NULL OR k.phone = '')
        AND o.phone IS NOT NULL
        AND o.phone != ''
        AND k.address_line_1 IS NOT NULL
        AND k.address_line_1 != ''
        AND k.id != o.id
    """)

    for row in cur.fetchall():
        action_items = []
        action_items.append(f'add_phone: {row[8]}')

        # If other source is ticket_tailor and kajabi doesn't have TT ID
        if row[9] == 'ticket_tailor' and row[10] and not row[11]:
            action_items.append(f'add_ticket_tailor_id: {row[10]}')

        opportunities.append({
            'type': 'name_address_match',
            'kajabi_id': row[0],
            'kajabi_email': row[1],
            'kajabi_name': row[2],
            'signal': f'last_name + address: {row[4]}',
            'action': ', '.join(action_items),
            'new_phone': row[8],
            'other_contact_id': row[5],
            'other_email': row[6],
            'other_name': row[7],
            'other_source': row[9],
            'ticket_tailor_id': row[10] if row[9] == 'ticket_tailor' else None
        })

    # 3. Name + Address: Kajabi has phone ↔ Other has different phone (confirmation)
    cur.execute("""
        SELECT
            k.id as kajabi_id,
            k.email as kajabi_email,
            k.first_name || ' ' || k.last_name as kajabi_name,
            k.phone as kajabi_phone,
            k.address_line_1,
            o.id as other_id,
            o.email as other_email,
            o.first_name || ' ' || o.last_name as other_name,
            o.phone as other_phone,
            o.source_system,
            o.ticket_tailor_id,
            k.ticket_tailor_id as kajabi_tt_id
        FROM contacts k
        INNER JOIN contacts o ON
            LOWER(TRIM(k.address_line_1)) = LOWER(TRIM(o.address_line_1))
            AND LOWER(TRIM(k.last_name)) = LOWER(TRIM(o.last_name))
        WHERE k.deleted_at IS NULL
        AND o.deleted_at IS NULL
        AND k.kajabi_id IS NOT NULL
        AND o.kajabi_id IS NULL
        AND k.phone IS NOT NULL
        AND k.phone != ''
        AND o.phone IS NOT NULL
        AND o.phone != ''
        AND k.phone != o.phone
        AND k.address_line_1 IS NOT NULL
        AND k.address_line_1 != ''
        AND k.id != o.id
    """)

    for row in cur.fetchall():
        action_items = []

        # If other source is ticket_tailor and kajabi doesn't have TT ID
        if row[9] == 'ticket_tailor' and row[10] and not row[11]:
            action_items.append(f'add_ticket_tailor_id: {row[10]}')

            opportunities.append({
                'type': 'name_address_match_diff_phone',
                'kajabi_id': row[0],
                'kajabi_email': row[1],
                'kajabi_name': row[2],
                'signal': f'last_name + address: {row[4]}',
                'action': ', '.join(action_items) if action_items else 'link_only',
                'kajabi_phone': row[3],
                'other_phone': row[8],
                'other_contact_id': row[5],
                'other_email': row[6],
                'other_name': row[7],
                'other_source': row[9],
                'ticket_tailor_id': row[10],
                'note': 'Different phones - link but keep existing'
            })

    return opportunities

def apply_enrichment(cur, opportunity, dry_run=True):
    """Apply a single enrichment opportunity."""

    if opportunity['type'] == 'phone_match_ticket_tailor':
        # Check if ticket_tailor_id already exists (might be used by another contact)
        if not dry_run:
            cur.execute("""
                SELECT id, email, first_name || ' ' || last_name as name
                FROM contacts
                WHERE ticket_tailor_id = %s
                AND id != %s
            """, (opportunity['ticket_tailor_id'], opportunity['kajabi_id']))

            existing = cur.fetchone()
            if existing:
                print(f"   ⚠️  SKIPPED: ticket_tailor_id {opportunity['ticket_tailor_id']} already used by {existing[2]} ({existing[1]})")
                print(f"               Different people sharing same phone - keeping separate")
                return

        # Add ticket_tailor_id to Kajabi contact
        if dry_run:
            print(f"   [DRY-RUN] Would update contact {opportunity['kajabi_id']}:")
            print(f"             SET ticket_tailor_id = '{opportunity['ticket_tailor_id']}'")
        else:
            cur.execute("""
                UPDATE contacts
                SET ticket_tailor_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (opportunity['ticket_tailor_id'], opportunity['kajabi_id']))
            print(f"   ✓ Updated: Added ticket_tailor_id to {opportunity['kajabi_name']}")

    elif opportunity['type'] == 'name_address_match':
        # Add phone and optionally ticket_tailor_id
        updates = []
        params = []

        if opportunity.get('new_phone'):
            updates.append("phone = %s")
            params.append(opportunity['new_phone'])

        if opportunity.get('ticket_tailor_id'):
            # Check if ticket_tailor_id already exists
            if not dry_run:
                cur.execute("""
                    SELECT id, email, first_name || ' ' || last_name as name
                    FROM contacts
                    WHERE ticket_tailor_id = %s
                    AND id != %s
                """, (opportunity['ticket_tailor_id'], opportunity['kajabi_id']))

                existing = cur.fetchone()
                if existing:
                    print(f"   ⚠️  SKIPPED linking to TT ID {opportunity['ticket_tailor_id']}: already used by {existing[2]} ({existing[1]})")
                else:
                    updates.append("ticket_tailor_id = %s")
                    params.append(opportunity['ticket_tailor_id'])
            else:
                updates.append("ticket_tailor_id = %s")
                params.append(opportunity['ticket_tailor_id'])

        if updates:
            updates.append("updated_at = NOW()")
            params.append(opportunity['kajabi_id'])

            if dry_run:
                print(f"   [DRY-RUN] Would update contact {opportunity['kajabi_id']}:")
                if opportunity.get('new_phone'):
                    print(f"             SET phone = '{opportunity['new_phone']}'")
                if opportunity.get('ticket_tailor_id'):
                    print(f"             SET ticket_tailor_id = '{opportunity['ticket_tailor_id']}'")
            else:
                query = f"""
                    UPDATE contacts
                    SET {', '.join(updates)}
                    WHERE id = %s
                """
                cur.execute(query, params)
                print(f"   ✓ Updated: {opportunity['kajabi_name']}")
                if opportunity.get('new_phone'):
                    print(f"      Added phone: {opportunity['new_phone']}")
                if opportunity.get('ticket_tailor_id'):
                    print(f"      Added ticket_tailor_id: {opportunity['ticket_tailor_id']}")

    elif opportunity['type'] == 'name_address_match_diff_phone':
        # Only add ticket_tailor_id, keep existing phone
        if opportunity.get('ticket_tailor_id'):
            # Check if ticket_tailor_id already exists
            if not dry_run:
                cur.execute("""
                    SELECT id, email, first_name || ' ' || last_name as name
                    FROM contacts
                    WHERE ticket_tailor_id = %s
                    AND id != %s
                """, (opportunity['ticket_tailor_id'], opportunity['kajabi_id']))

                existing = cur.fetchone()
                if existing:
                    print(f"   ⚠️  SKIPPED: ticket_tailor_id {opportunity['ticket_tailor_id']} already used by {existing[2]} ({existing[1]})")
                    return

            if dry_run:
                print(f"   [DRY-RUN] Would update contact {opportunity['kajabi_id']}:")
                print(f"             SET ticket_tailor_id = '{opportunity['ticket_tailor_id']}'")
                print(f"             (Keeping existing phone: {opportunity['kajabi_phone']})")
            else:
                cur.execute("""
                    UPDATE contacts
                    SET ticket_tailor_id = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (opportunity['ticket_tailor_id'], opportunity['kajabi_id']))
                print(f"   ✓ Updated: {opportunity['kajabi_name']}")
                print(f"      Added ticket_tailor_id: {opportunity['ticket_tailor_id']}")
                print(f"      Kept existing phone: {opportunity['kajabi_phone']}")

def main():
    # Check if execute mode
    dry_run = '--execute' not in sys.argv

    # Connect to database
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print_header("CONTACT ENRICHMENT - FINAL PASS")
    print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    print(f"Time: {datetime.now().isoformat()}")

    if not dry_run:
        print("\n⚠️  EXECUTE MODE - Changes will be made to the database!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        import time
        for i in range(5, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n   Starting execution...")

    # Get enrichment opportunities
    print("\n" + "=" * 80)
    print("FINDING ENRICHMENT OPPORTUNITIES")
    print("=" * 80)

    opportunities = get_enrichment_opportunities(cur)

    print(f"\nFound {len(opportunities)} enrichment opportunities:")
    print(f"  • Phone matches (Kajabi ↔ TT): {len([o for o in opportunities if o['type'] == 'phone_match_ticket_tailor'])}")
    print(f"  • Name + Address (add phone): {len([o for o in opportunities if o['type'] == 'name_address_match'])}")
    print(f"  • Name + Address (link only): {len([o for o in opportunities if o['type'] == 'name_address_match_diff_phone'])}")

    if len(opportunities) == 0:
        print("\n✓ No enrichment opportunities found - database is already well-enriched!")
        cur.close()
        conn.close()
        return

    # Group by type
    print("\n" + "=" * 80)
    print("ENRICHMENT DETAILS")
    print("=" * 80)

    for opp_type in ['phone_match_ticket_tailor', 'name_address_match', 'name_address_match_diff_phone']:
        type_opps = [o for o in opportunities if o['type'] == opp_type]
        if type_opps:
            if opp_type == 'phone_match_ticket_tailor':
                print("\n1. Phone-Based Linking (Kajabi ↔ Ticket Tailor)")
            elif opp_type == 'name_address_match':
                print("\n2. Name + Address Enrichment (Add Phone)")
            else:
                print("\n3. Name + Address Linking (Different Phones)")

            for opp in type_opps:
                print(f"\n   Kajabi Contact:")
                print(f"      Name: {opp['kajabi_name']}")
                print(f"      Email: {opp['kajabi_email']}")
                print(f"      Signal: {opp['signal']}")
                print(f"   → Action: {opp['action']}")
                if opp.get('other_name'):
                    print(f"      Matched with: {opp['other_name']} ({opp['other_email']}) from {opp['other_source']}")

    # Apply enrichments
    print("\n" + "=" * 80)
    print("APPLYING ENRICHMENTS")
    print("=" * 80)

    for i, opp in enumerate(opportunities, 1):
        print(f"\n[{i}/{len(opportunities)}] Enriching: {opp['kajabi_name']}")
        apply_enrichment(cur, opp, dry_run=dry_run)

    # Commit or rollback
    if not dry_run:
        print("\n" + "=" * 80)
        print("COMMITTING CHANGES")
        print("=" * 80)
        conn.commit()
        print("✓ Transaction committed successfully")
    else:
        conn.rollback()

    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    cur.execute("""
        SELECT
            COUNT(*) as total_kajabi,
            SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone,
            SUM(CASE WHEN ticket_tailor_id IS NOT NULL THEN 1 ELSE 0 END) as with_tt_link
        FROM contacts
        WHERE deleted_at IS NULL
        AND kajabi_id IS NOT NULL
    """)
    row = cur.fetchone()

    print(f"\nKajabi Contact Enrichment Status:")
    print(f"  Total Kajabi contacts: {row[0]:,}")
    print(f"  With phone: {row[1]:,} ({100*row[1]/row[0]:.1f}%)")
    print(f"  With Ticket Tailor link: {row[2]:,} ({100*row[2]/row[0]:.1f}%)")

    print("\n" + "=" * 80)
    if dry_run:
        print("✓ DRY-RUN COMPLETE")
        print("=" * 80)
        print("\nTo apply these changes, run:")
        print("  python3 scripts/enrich_contacts_final_pass.py --execute")
    else:
        print("✓ ENRICHMENT COMPLETE")
        print("=" * 80)

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
