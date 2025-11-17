#!/usr/bin/env python3
"""
Analyze Google Contacts labels and prepare tag mapping
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict
from db_config import get_database_url

# Load Google Contacts
df = pd.read_csv('/workspaces/starhouse-database-v2/kajabi 3 files review/ascpr_google_contacts.csv')

print("=" * 80)
print("GOOGLE CONTACTS LABEL ANALYSIS")
print("=" * 80)

# Parse all labels
label_counts = defaultdict(int)
label_to_contacts = defaultdict(list)

for idx, row in df.iterrows():
    labels = row.get('Labels')
    email = row.get('E-mail 1 - Value')

    if pd.notna(labels) and pd.notna(email):
        # Split by ::: to get individual labels
        label_list = [l.strip() for l in str(labels).split(':::')]
        for label in label_list:
            label_counts[label] += 1
            label_to_contacts[label].append(email)

print(f"\nTotal unique labels: {len(label_counts)}")
print(f"\nAll labels (sorted by frequency):\n")

for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{count:5,} | {label}")

# Connect to database
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres.lnagadkqejnopgfxwlkb',
    password=get_database_url().split('@')[0].split(':')[-1],
    host='aws-1-us-east-2.pooler.supabase.com',
    port='5432'
)

cur = conn.cursor(cursor_factory=RealDictCursor)

# Get existing tags
cur.execute("SELECT id, name, description FROM tags ORDER BY name")
existing_tags = cur.fetchall()

print(f"\n" + "=" * 80)
print("EXISTING DATABASE TAGS")
print("=" * 80)
print(f"\nTotal tags in database: {len(existing_tags)}\n")

for tag in existing_tags:
    print(f"{tag['name']:40} | {tag['description'] or '(no description)'}")

cur.close()
conn.close()

# Suggest mapping
print("\n" + "=" * 80)
print("SUGGESTED LABEL-TO-TAG MAPPING")
print("=" * 80)

mappings = {
    # System labels to skip
    '* myContacts': 'SKIP (universal system label)',
    'Imported on 5/10': 'SKIP (import metadata)',
    'Imported on 11/9': 'SKIP (import metadata)',
    'Imported on 11/9 1': 'SKIP (import metadata)',

    # Priority labels to map
    'Current Keepers': 'CREATE TAG: Current Keeper',
    '11-9-2025 Current Keepers': 'MERGE WITH: Current Keeper',
    'Paid Members': 'CREATE TAG: Paid Member',
    'Complimentary Members': 'CREATE TAG: Complimentary Member',
    'Program Partner': 'CREATE TAG: Program Partner',
    'Preferred Keepers': 'CREATE TAG: Preferred Keeper',
    'Past Keepers': 'CREATE TAG: Past Keeper',

    # Event/Date labels
    'New Keeper 4/12/25': 'CREATE TAG: New Keeper (or add date to notes)',
    'New Keeper 4/13 2024': 'MERGE WITH: New Keeper',
    'New Keeper 9/7/2024': 'MERGE WITH: New Keeper',

    # Program/Interest labels
    'StarHouse Mysteries': 'CREATE TAG: StarHouse Mysteries',
    'EarthStar Experience': 'CREATE TAG: EarthStar Experience',
    'Sacred Sites as Consciousness Tools': 'CREATE TAG: Sacred Sites Workshop',
    'The Grand Conjunction of Jupiter and Saturn 2020': 'SKIP (historic event)',
    'StarHouse 30th Birthday Watch Party': 'SKIP (historic event)',
    'StarWisdom at StarHouse': 'CREATE TAG: StarWisdom',
}

print("\nPriority Mappings:\n")
for label, mapping in mappings.items():
    count = label_counts.get(label, 0)
    if count > 0:
        print(f"{count:5,} | {label:45} -> {mapping}")
