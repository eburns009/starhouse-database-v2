#!/usr/bin/env python3
"""
Analyze current capitalization state of names and addresses
"""
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgres://***REMOVED***@***REMOVED***:6543/postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")  # SECURITY: No hardcoded credentials


def analyze_capitalization():
    conn = psycopg2.connect(DB_URL, password=DB_PASSWORD)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print(f"{'=' * 100}")
    print("CAPITALIZATION ANALYSIS")
    print(f"{'=' * 100}\n")

    # Analyze first names
    print("FIRST NAMES:")
    cur.execute("""
        SELECT first_name, COUNT(*) as cnt
        FROM contacts
        WHERE first_name IS NOT NULL
        GROUP BY first_name
        HAVING first_name != initcap(first_name)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_first = cur.fetchall()

    if bad_first:
        print(f"  Found {len(bad_first)} unique improperly capitalized first names")
        print("  Samples:")
        for row in bad_first[:10]:
            print(f"    '{row['first_name']}' (should be '{row['first_name'].title()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All first names properly capitalized")
    print()

    # Analyze last names
    print("LAST NAMES:")
    cur.execute("""
        SELECT last_name, COUNT(*) as cnt
        FROM contacts
        WHERE last_name IS NOT NULL
        GROUP BY last_name
        HAVING last_name != initcap(last_name)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_last = cur.fetchall()

    if bad_last:
        print(f"  Found {len(bad_last)} unique improperly capitalized last names")
        print("  Samples:")
        for row in bad_last[:10]:
            print(f"    '{row['last_name']}' (should be '{row['last_name'].title()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All last names properly capitalized")
    print()

    # Analyze addresses (billing)
    print("BILLING ADDRESSES:")
    cur.execute("""
        SELECT address_line_1, COUNT(*) as cnt
        FROM contacts
        WHERE address_line_1 IS NOT NULL
        GROUP BY address_line_1
        HAVING address_line_1 != initcap(address_line_1)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_addr = cur.fetchall()

    if bad_addr:
        print(f"  Found {len(bad_addr)} unique improperly capitalized addresses")
        print("  Samples:")
        for row in bad_addr[:10]:
            print(f"    '{row['address_line_1']}' (should be '{row['address_line_1'].title()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All billing addresses properly capitalized")
    print()

    # Analyze cities (billing)
    print("BILLING CITIES:")
    cur.execute("""
        SELECT city, COUNT(*) as cnt
        FROM contacts
        WHERE city IS NOT NULL
        GROUP BY city
        HAVING city != initcap(city)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_city = cur.fetchall()

    if bad_city:
        print(f"  Found {len(bad_city)} unique improperly capitalized cities")
        print("  Samples:")
        for row in bad_city[:10]:
            print(f"    '{row['city']}' (should be '{row['city'].title()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All billing cities properly capitalized")
    print()

    # Analyze states (should be uppercase)
    print("BILLING STATES:")
    cur.execute("""
        SELECT state, COUNT(*) as cnt
        FROM contacts
        WHERE state IS NOT NULL AND LENGTH(state) <= 3
        GROUP BY state
        HAVING state != UPPER(state)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_state = cur.fetchall()

    if bad_state:
        print(f"  Found {len(bad_state)} unique improperly capitalized state codes")
        print("  Samples:")
        for row in bad_state[:10]:
            print(f"    '{row['state']}' (should be '{row['state'].upper()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All state codes properly capitalized")
    print()

    # Analyze shipping addresses
    print("SHIPPING ADDRESSES:")
    cur.execute("""
        SELECT shipping_address_line_1, COUNT(*) as cnt
        FROM contacts
        WHERE shipping_address_line_1 IS NOT NULL
        GROUP BY shipping_address_line_1
        HAVING shipping_address_line_1 != initcap(shipping_address_line_1)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_ship = cur.fetchall()

    if bad_ship:
        print(f"  Found {len(bad_ship)} unique improperly capitalized shipping addresses")
        print("  Samples:")
        for row in bad_ship[:10]:
            print(f"    '{row['shipping_address_line_1']}' (should be '{row['shipping_address_line_1'].title()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All shipping addresses properly capitalized")
    print()

    # Analyze shipping cities
    print("SHIPPING CITIES:")
    cur.execute("""
        SELECT shipping_city, COUNT(*) as cnt
        FROM contacts
        WHERE shipping_city IS NOT NULL
        GROUP BY shipping_city
        HAVING shipping_city != initcap(shipping_city)
        ORDER BY cnt DESC
        LIMIT 20
    """)
    bad_ship_city = cur.fetchall()

    if bad_ship_city:
        print(f"  Found {len(bad_ship_city)} unique improperly capitalized shipping cities")
        print("  Samples:")
        for row in bad_ship_city[:10]:
            print(f"    '{row['shipping_city']}' (should be '{row['shipping_city'].title()}') - {row['cnt']} contacts")
    else:
        print("  ✓ All shipping cities properly capitalized")
    print()

    # Count total contacts needing updates
    cur.execute("""
        SELECT COUNT(*) as cnt FROM contacts
        WHERE
            (first_name IS NOT NULL AND first_name != initcap(first_name))
            OR (last_name IS NOT NULL AND last_name != initcap(last_name))
            OR (address_line_1 IS NOT NULL AND address_line_1 != initcap(address_line_1))
            OR (city IS NOT NULL AND city != initcap(city))
            OR (state IS NOT NULL AND LENGTH(state) <= 3 AND state != UPPER(state))
            OR (shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 != initcap(shipping_address_line_1))
            OR (shipping_city IS NOT NULL AND shipping_city != initcap(shipping_city))
            OR (shipping_state IS NOT NULL AND LENGTH(shipping_state) <= 3 AND shipping_state != UPPER(shipping_state))
    """)
    total_needing_update = cur.fetchone()['cnt']

    print(f"{'=' * 100}")
    print(f"SUMMARY: {total_needing_update:,} contacts need capitalization fixes")
    print(f"{'=' * 100}\n")

    cur.close()
    conn.close()


if __name__ == '__main__':
    analyze_capitalization()
