#!/usr/bin/env python3
"""Quick test of Mailchimp tag parsing"""
import pandas as pd

MAILCHIMP_FILE = 'kajabi 3 files review/Mailchimp export 9-29-2020.csv'

df = pd.read_csv(MAILCHIMP_FILE, encoding='utf-8')

print("Sample TAGS column values:")
print("=" * 100)

# Show first 20 non-null tags
count = 0
for idx, row in df.iterrows():
    if pd.notna(row['TAGS']) and row['TAGS']:
        print(f"\n{idx}. Email: {row['Email Address']}")
        print(f"   TAGS raw: {repr(row['TAGS'])}")
        print(f"   TAGS type: {type(row['TAGS'])}")
        count += 1
        if count >= 10:
            break

print("\n" + "=" * 100)
print(f"Total rows with TAGS: {df['TAGS'].notna().sum()}")
print(f"Total rows without TAGS: {df['TAGS'].isna().sum()}")
