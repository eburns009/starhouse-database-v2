#!/usr/bin/env python3
"""
Enrich donor list with email addresses and mailing addresses from the database.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import sys

# Database connection parameters
DB_PARAMS = {
    'host': '***REMOVED***',
    'port': '6543',
    'database': 'postgres',
    'user': '***REMOVED***',
    'password': '***REMOVED***'
}

# Donor names from the file
DONORS = [
    ("Grainger Foundation", "$10,000.00"),
    ("Lila Tressemer", "$5,500.00"),
    ("Virginia Jordan", "$5,000.00"),
    ("Tova Jacober", "$5,000.00"),
    ("Steiner King Foundation", "$5,000.00"),
    ("Harwood Ferguson", "$5,000.00"),
    ("All Seasons Chalice", "$2,502.00"),
    ("Furr Institute", "$1,000.00"),
    ("Betsy Workman", "$1,000.00"),
    ("Candice Knight", "$741.00"),
    ("Corin Blanchard", "$690.00"),
    ("Susie Kincade", "$675.00"),
    ("Stefanie Smith", "$558.00"),
    ("Sunshine Snow Removal LLC", "$500.00"),
    ("Stephanie Bollman", "$500.00"),
    ("Margo King", "$500.00"),
    ("Jim Paschis", "$415.00"),
    ("Melissa Lago", "$327.00"),
    ("Roberta Mylan", "$300.00"),
    ("Brian Gray", "$300.00"),
    ("Three Swallows Foundation", "$250.00"),
    ("Renee Goldberg", "$250.00"),
    ("Organic Roots Catering", "$250.00"),
    ("Jana Stratton", "$250.00"),
    ("David Weihnacht", "$250.00"),
    ("Cathleen & Joshua Shoenfeld", "$250.00"),
    ("Abby Jepson-Kuhl", "$250.00"),
    ("Thomas Hast", "$200.00"),
    ("Lara Darvie", "$200.00"),
    ("Jade M'Lynn", "$200.00"),
    ("Chien Lin", "$200.00"),
    ("Jack Swift", "$185.00"),
    ("Shannon O'Kane", "$172.00"),
    ("Daniel Rubenstein", "$170.00"),
    ("Corey Strohmeyer", "$155.00"),
    ("Tending the Sacred, LLC", "$150.00"),
    ("Scott Thurnauer", "$150.00"),
    ("Keith Whittier", "$150.00"),
    ("Kathleen Cameron Hallett", "$150.00"),
    ("Gurpreet Gill", "$150.00"),
    ("Eric Fisher", "$150.00"),
    ("CAYA Studios LLC", "$150.00"),
    ("Colorado Gives Foundation", "$142.71"),
    ("Elizabeth de Lorimier", "$140.00"),
    ("Roy A. Wingate", "$135.00"),
    ("John Hazekamp", "$115.00"),
    ("Christine Harvey", "$110.00"),
    ("Heather Baines", "$108.00"),
    ("The Star Trilogy", "$106.00"),
    ("Kimara Evans", "$105.00"),
    ("Steven Leovy", "$100.00"),
    ("Stephen Donnelly", "$100.00"),
    ("Rita Haramy", "$100.00"),
    ("Rebecca Arnold", "$100.00"),
    ("Raki Suman", "$100.00"),
    ("Paula Slick", "$100.00"),
    ("Patricia Ramey", "$100.00"),
    ("Matthew Samek", "$100.00"),
    ("Mary Thieme", "$100.00"),
    ("Mary Daye", "$100.00"),
    ("Mark Cronshaw {c}", "$100.00"),
    ("Marissa Bramlett", "$100.00"),
    ("Mari Clements", "$100.00"),
    ("Marella. Colyvas", "$100.00"),
    ("Kirsten Hutcheson", "$100.00"),
    ("Kathryn Holt", "$100.00"),
    ("Joan Soper", "$100.00"),
    ("Jessica W. Mazonson", "$100.00"),
    ("Janeene Touchton", "$100.00"),
    ("Hsu Mei Chi", "$100.00"),
    ("Greg Temple", "$100.00"),
    ("Elissa Langenegger", "$100.00"),
    ("Deborah Ogden", "$100.00"),
    ("Debbie Burns", "$100.00"),
    ("Barbara Hope-Gaiti", "$100.00"),
    ("Barbara Holden", "$100.00"),
    ("Paul Humes", "$90.00"),
    ("Colleen McCloskey", "$90.00"),
    ("Donna Renzetti", "$85.00"),
    ("Cristina & Jeff Bowen", "$85.00"),
    ("Madhavii Shirman", "$84.00"),
    ("Scott Burd", "$83.00"),
    ("Sydney Greene", "$80.00"),
    ("Michelle Backus", "$80.00"),
    ("Katherine Woller", "$80.00"),
    ("Jenna Buffaloe", "$80.00"),
    ("Brooke & Rose LeVan", "$80.00"),
    ("Arisa La Fond", "$80.00"),
    ("Amanda Pinelli Palumbo", "$80.00"),
    ("Katharine S. Roske", "$77.00"),
    ("Lee Cook", "$75.00"),
    ("Katie Brown", "$75.00"),
    ("Jeremy May", "$75.00"),
    ("Laura Brown {C}", "$73.00"),
    ("Meriku Lewis", "$70.00"),
    ("Graham Kirsh", "$60.00"),
    ("Brianna Jacobs", "$60.00"),
    ("Katherine Phelps", "$55.55"),
    ("Ashley Young", "$55.00"),
    ("Kristy King", "$52.00"),
    ("Kelly Notaras", "$52.00"),
    ("Ixeeya Beacher", "$52.00"),
    ("Grace Halsey", "$52.00"),
    ("Shiva Coffey", "$50.00"),
    ("Roger Walker", "$50.00"),
    ("Robert Schiappacasse", "$50.00"),
    ("Lisa Range", "$50.00"),
    ("Lisa Devine", "$50.00"),
    ("Lindsay Balgooyen", "$50.00"),
    ("Lauren Barnard", "$50.00"),
    ("Laine Gerritsen", "$50.00"),
    ("Francesca Militeau", "$50.00"),
    ("Erin Parks", "$50.00"),
    ("Elaine Duncan", "$50.00"),
    ("Amy Henschke", "$50.00"),
    ("Mason Mostajo", "$44.00"),
    ("Virginia. Lynn Anderson", "$35.00"),
    ("Tim Percival", "$35.00"),
    ("Kimberley Wukitsch", "$35.00"),
    ("Jon Crowder", "$35.00"),
    ("Iain Gillespie", "$35.00"),
    ("Debra A Mies", "$35.00"),
    ("Cultivating Spirits LLC", "$35.00"),
    ("Anastacia _Nutt", "$35.00"),
    ("James Pino", "$33.00"),
    ("Lon Goldstein", "$30.00"),
    ("Karen Kenney", "$30.00"),
    ("Ines Manteuffel", "$30.00"),
    ("Holly a McCann", "$30.00"),
    ("Louis Fioravanti", "$27.00"),
    ("Jamie Hartman", "$27.00"),
    ("Susan Reinhardt", "$25.00"),
    ("Rachel L. Martinez", "$25.00"),
    ("Nancy Linsley", "$25.00"),
    ("Nancy Hough", "$25.00"),
    ("Michael Schulenburg", "$25.00"),
    ("Margot Zaher", "$25.00"),
    ("Janice Hall", "$25.00"),
    ("E Van Leuwen Hall", "$25.00"),
    ("Darleen Gegich", "$25.00"),
    ("Daniela Papi Thornton", "$25.00"),
    ("Cynthia Bedell", "$25.00"),
    ("Cordelia A Wilkerson", "$25.00"),
    ("Christine Huston", "$25.00"),
    ("Carolyn Hart", "$25.00"),
    ("Brett Kingstone", "$25.00"),
    ("Attila Kassa", "$25.00"),
    ("Alan Kaplan", "$25.00"),
    ("Adam Harvey", "$22.00"),
    ("Wildly Alive, Inc", "$20.00"),
    ("Wendy Maunu", "$20.00"),
    ("Shana Turner", "$20.00"),
    ("Michelle Nicholls", "$20.00"),
    ("Maya Reisz", "$20.00"),
    ("Matt Meyer", "$20.00"),
    ("Lori Kochevar", "$20.00"),
    ("John & Patricia Stewart", "$20.00"),
    ("Jo Forkish", "$20.00"),
    ("Jennifer Newton", "$20.00"),
    ("Gregory Miller", "$20.00"),
    ("Catherine D. Boerder", "$20.00"),
    ("Ben Phelan", "$20.00"),
    ("Alana Shaw", "$20.00"),
    ("Sandra Zeese", "$15.00"),
    ("Lindsay Caron Epstein", "$15.00"),
    ("Liam Hoppe", "$15.00"),
    ("John R Jordan", "$15.00"),
    ("Jennifer Bowen", "$15.00"),
    ("Eric Witte", "$15.00"),
    ("Christine Golden", "$15.00"),
    ("Ben Levi", "$15.00"),
    ("PayPal Giving Fund", "$14.00"),
    ("Your Best Version LLC", "$12.12"),
    ("Shanti Medina {C}", "$12.00"),
    ("Tatiana Chicu", "$10.00"),
    ("Nancy Redfeather", "$10.00"),
    ("Lisa Dalton", "$10.00"),
    ("Kent Spies", "$10.00"),
    ("Dalila Orozco", "$10.00"),
    ("Divine Union Academy", "$5.55"),
]


def search_contact(conn, name):
    """
    Search for a contact by name in the database.
    Returns contact information including emails and addresses.
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Clean the name for searching
    clean_name = name.strip()

    # Try exact match first on full name (concatenated)
    cursor.execute("""
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.first_name || ' ' || COALESCE(c.last_name, '') as full_name,
            c.email,
            c.paypal_email,
            c.paypal_business_name,
            c.address_line_1,
            c.address_line_2,
            c.city,
            c.state,
            c.postal_code,
            c.country,
            c.shipping_address_line_1,
            c.shipping_address_line_2,
            c.shipping_city,
            c.shipping_state,
            c.shipping_postal_code,
            c.shipping_country
        FROM contacts c
        WHERE (c.first_name || ' ' || COALESCE(c.last_name, '')) ILIKE %s
        LIMIT 1
    """, (clean_name,))

    result = cursor.fetchone()

    # If no exact match, try case-insensitive partial match
    if not result:
        cursor.execute("""
            SELECT
                c.id,
                c.first_name,
                c.last_name,
                c.first_name || ' ' || COALESCE(c.last_name, '') as full_name,
                c.email,
                c.paypal_email,
                c.paypal_business_name,
                c.address_line_1,
                c.address_line_2,
                c.city,
                c.state,
                c.postal_code,
                c.country,
                c.shipping_address_line_1,
                c.shipping_address_line_2,
                c.shipping_city,
                c.shipping_state,
                c.shipping_postal_code,
                c.shipping_country
            FROM contacts c
            WHERE (c.first_name || ' ' || COALESCE(c.last_name, '')) ILIKE %s
               OR c.paypal_business_name ILIKE %s
               OR c.first_name ILIKE %s
               OR c.last_name ILIKE %s
            LIMIT 1
        """, (f'%{clean_name}%', f'%{clean_name}%', f'%{clean_name}%', f'%{clean_name}%'))

        result = cursor.fetchone()

    cursor.close()
    return result


def format_address(addr_line1, addr_line2, city, state, postal, country):
    """Format address components into a single string."""
    parts = []
    if addr_line1:
        parts.append(addr_line1)
    if addr_line2:
        parts.append(addr_line2)

    city_state_zip = []
    if city:
        city_state_zip.append(city)
    if state:
        city_state_zip.append(state)
    if postal:
        city_state_zip.append(postal)

    if city_state_zip:
        parts.append(' '.join(city_state_zip))

    if country and country.upper() not in ['US', 'USA', 'UNITED STATES']:
        parts.append(country)

    return ', '.join(parts) if parts else ''


def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_PARAMS)

    print(f"Processing {len(DONORS)} donors...\n")

    results = []
    matched_count = 0

    for name, total in DONORS:
        contact = search_contact(conn, name)

        if contact:
            matched_count += 1

            # Format mailing addresses
            billing_address = format_address(
                contact['address_line_1'],
                contact['address_line_2'],
                contact['city'],
                contact['state'],
                contact['postal_code'],
                contact['country']
            )

            shipping_address = format_address(
                contact['shipping_address_line_1'],
                contact['shipping_address_line_2'],
                contact['shipping_city'],
                contact['shipping_state'],
                contact['shipping_postal_code'],
                contact['shipping_country']
            )

            # Determine alternate name
            alt_name = ''
            if contact['paypal_business_name'] and contact['paypal_business_name'] != name:
                alt_name = contact['paypal_business_name']
            elif contact['full_name'] and contact['full_name'].strip() != name:
                alt_name = contact['full_name']

            # Determine emails
            email1 = contact['email'] or ''
            email2 = ''
            if contact['paypal_email'] and contact['paypal_email'] != contact['email']:
                email2 = contact['paypal_email']

            results.append({
                'Name': name,
                'Other name if possible': alt_name,
                'Email 1': email1,
                'Email 2': email2,
                'Billing Address': billing_address,
                'Shipping Address': shipping_address if shipping_address != billing_address else '',
                'Totals': total
            })
        else:
            # No match found
            results.append({
                'Name': name,
                'Other name if possible': '',
                'Email 1': '',
                'Email 2': '',
                'Billing Address': '',
                'Shipping Address': '',
                'Totals': total
            })

    conn.close()

    print("=" * 80)
    print(f"ENRICHMENT RESULTS")
    print("=" * 80)
    print(f"Total donors: {len(DONORS)}")
    print(f"Matched in database: {matched_count}")
    print(f"Not found: {len(DONORS) - matched_count}")
    print("=" * 80)
    print()

    # Print results as TSV
    print("Name\tOther name if possible\tEmail 1\tEmail 2\tBilling Address\tShipping Address\tTotals")
    for row in results:
        print(f"{row['Name']}\t{row['Other name if possible']}\t{row['Email 1']}\t{row['Email 2']}\t{row['Billing Address']}\t{row['Shipping Address']}\t{row['Totals']}")

    print()
    print("=" * 80)
    print("DETAILED MATCHES")
    print("=" * 80)

    for row in results:
        if row['Email 1'] or row['Email 2']:
            print(f"\n{row['Name']} ({row['Totals']})")
            if row['Other name if possible']:
                print(f"  Alt Name: {row['Other name if possible']}")
            if row['Email 1']:
                print(f"  Email 1: {row['Email 1']}")
            if row['Email 2']:
                print(f"  Email 2: {row['Email 2']}")
            if row['Billing Address']:
                print(f"  Billing: {row['Billing Address']}")
            if row['Shipping Address']:
                print(f"  Shipping: {row['Shipping Address']}")


if __name__ == '__main__':
    main()
