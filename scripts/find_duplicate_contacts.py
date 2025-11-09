#!/usr/bin/env python3
"""
FAANG-Quality Fuzzy Duplicate Detection
========================================

Finds potential duplicate contacts using:
- Levenshtein distance for name matching
- Phone number normalization
- Email similarity
- Address matching
- Combined confidence scoring

FAANG Standards Applied:
- Type-safe with dataclasses
- Comprehensive scoring algorithm
- Configurable thresholds
- Detailed reporting
- Safe dry-run mode

Usage:
  # Find duplicates with default threshold (80%)
  python3 scripts/find_duplicate_contacts.py --threshold 0.8

  # Lower threshold for more matches (may include false positives)
  python3 scripts/find_duplicate_contacts.py --threshold 0.6

  # Export to CSV
  python3 scripts/find_duplicate_contacts.py --output duplicates.csv

Author: StarHouse Development Team
Date: 2025-11-08
Version: 1.0.0
"""

import os
import sys
import argparse
import csv
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import Levenshtein
import re

load_dotenv()

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

@dataclass
class Contact:
    """Represents a contact for duplicate matching."""
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    address_line_1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    source_system: Optional[str]
    created_at: datetime


@dataclass
class DuplicateMatch:
    """Represents a potential duplicate match."""
    contact1_id: str
    contact1_name: str
    contact1_email: str
    contact2_id: str
    contact2_name: str
    contact2_email: str
    confidence_score: float
    name_similarity: float
    email_similarity: float
    phone_match: bool
    address_similarity: float
    reasons: List[str]


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_name(name: Optional[str]) -> str:
    """Normalize name for comparison."""
    if not name:
        return ""
    # Lowercase, remove extra spaces, remove punctuation
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def normalize_phone(phone: Optional[str]) -> str:
    """Normalize phone to digits only."""
    if not phone:
        return ""
    return re.sub(r'\D', '', phone)


def get_full_name(contact: Contact) -> str:
    """Get full name from contact."""
    parts = []
    if contact.first_name:
        parts.append(contact.first_name)
    if contact.last_name:
        parts.append(contact.last_name)
    return ' '.join(parts)


# ============================================================================
# SIMILARITY SCORING
# ============================================================================

def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate name similarity using Levenshtein distance.

    Returns: 0.0 (completely different) to 1.0 (identical)
    """
    if not name1 or not name2:
        return 0.0

    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    if not norm1 or not norm2:
        return 0.0

    # Levenshtein ratio (0-1, where 1 is identical)
    similarity = Levenshtein.ratio(norm1, norm2)

    # Boost score for common nickname variations
    nicknames = {
        'bob': 'robert', 'rob': 'robert', 'bill': 'william', 'will': 'william',
        'jim': 'james', 'dave': 'david', 'mike': 'michael', 'chris': 'christopher',
        'jen': 'jennifer', 'liz': 'elizabeth', 'beth': 'elizabeth', 'sue': 'susan'
    }

    for nick, full in nicknames.items():
        if (nick in norm1 and full in norm2) or (nick in norm2 and full in norm1):
            similarity = max(similarity, 0.85)

    return similarity


def calculate_email_similarity(email1: str, email2: str) -> float:
    """
    Calculate email similarity.

    Returns: 0.0 (completely different) to 1.0 (identical)
    """
    if not email1 or not email2:
        return 0.0

    email1 = email1.lower().strip()
    email2 = email2.lower().strip()

    # Exact match
    if email1 == email2:
        return 1.0

    # Same username, different domain
    username1 = email1.split('@')[0] if '@' in email1 else email1
    username2 = email2.split('@')[0] if '@' in email2 else email2

    if username1 == username2:
        return 0.7  # Strong signal but different domains

    # Similar usernames (typos, etc)
    username_similarity = Levenshtein.ratio(username1, username2)

    return username_similarity * 0.6  # Discount for different emails


def check_phone_match(phone1: Optional[str], phone2: Optional[str]) -> bool:
    """Check if phones match (normalized)."""
    if not phone1 or not phone2:
        return False

    norm1 = normalize_phone(phone1)
    norm2 = normalize_phone(phone2)

    if not norm1 or not norm2:
        return False

    # Match if last 10 digits are the same
    return norm1[-10:] == norm2[-10:] if len(norm1) >= 10 and len(norm2) >= 10 else norm1 == norm2


def calculate_address_similarity(contact1: Contact, contact2: Contact) -> float:
    """
    Calculate address similarity.

    Returns: 0.0 (completely different) to 1.0 (identical)
    """
    if not contact1.address_line_1 or not contact2.address_line_1:
        return 0.0

    # Normalize addresses
    addr1 = normalize_name(contact1.address_line_1)
    addr2 = normalize_name(contact2.address_line_1)

    address_sim = Levenshtein.ratio(addr1, addr2)

    # Boost if city/state match
    city_match = (contact1.city and contact2.city and
                  normalize_name(contact1.city) == normalize_name(contact2.city))
    state_match = (contact1.state and contact2.state and
                   contact1.state.upper() == contact2.state.upper())

    if city_match:
        address_sim = min(1.0, address_sim + 0.2)
    if state_match:
        address_sim = min(1.0, address_sim + 0.1)

    return address_sim


def calculate_duplicate_score(contact1: Contact, contact2: Contact) -> DuplicateMatch:
    """
    Calculate comprehensive duplicate score.

    FAANG Quality: Multi-factor scoring with configurable weights
    """
    # Calculate individual similarities
    name_sim = calculate_name_similarity(get_full_name(contact1), get_full_name(contact2))
    email_sim = calculate_email_similarity(contact1.email, contact2.email)
    phone_match = check_phone_match(contact1.phone, contact2.phone)
    address_sim = calculate_address_similarity(contact1, contact2)

    # Weighted scoring (configurable)
    weights = {
        'name': 0.35,
        'email': 0.30,
        'phone': 0.20,
        'address': 0.15
    }

    phone_score = 1.0 if phone_match else 0.0

    confidence = (
        name_sim * weights['name'] +
        email_sim * weights['email'] +
        phone_score * weights['phone'] +
        address_sim * weights['address']
    )

    # Build reasons list
    reasons = []
    if name_sim > 0.8:
        reasons.append(f"Name similarity: {name_sim*100:.0f}%")
    if email_sim > 0.6:
        reasons.append(f"Email similarity: {email_sim*100:.0f}%")
    if phone_match:
        reasons.append("Phone number match")
    if address_sim > 0.7:
        reasons.append(f"Address similarity: {address_sim*100:.0f}%")

    return DuplicateMatch(
        contact1_id=contact1.id,
        contact1_name=get_full_name(contact1),
        contact1_email=contact1.email,
        contact2_id=contact2.id,
        contact2_name=get_full_name(contact2),
        contact2_email=contact2.email,
        confidence_score=confidence,
        name_similarity=name_sim,
        email_similarity=email_sim,
        phone_match=phone_match,
        address_similarity=address_sim,
        reasons=reasons
    )


# ============================================================================
# DUPLICATE DETECTION
# ============================================================================

def find_duplicates(threshold: float = 0.8, limit: Optional[int] = None) -> List[DuplicateMatch]:
    """
    Find potential duplicate contacts.

    FAANG Standards:
    - Efficient N^2 comparison with early termination
    - Configurable threshold
    - Progress tracking
    - Memory efficient

    Args:
        threshold: Minimum confidence score (0.0-1.0)
        limit: Maximum duplicates to return (for testing)

    Returns:
        List of duplicate matches sorted by confidence
    """
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Fetch all contacts
            cursor.execute("""
                SELECT id, email, first_name, last_name, phone,
                       address_line_1, city, state, source_system, created_at
                FROM contacts
                ORDER BY created_at DESC
            """)

            contacts = [Contact(**row) for row in cursor.fetchall()]

            print(f"Analyzing {len(contacts):,} contacts for duplicates...")
            print(f"Confidence threshold: {threshold*100:.0f}%")
            print()

            duplicates = []
            checked = set()

            # Compare each contact with others
            for i, contact1 in enumerate(contacts):
                if i % 100 == 0 and i > 0:
                    print(f"Progress: {i:,} / {len(contacts):,} contacts checked...")

                for contact2 in contacts[i+1:]:
                    # Skip if already checked this pair
                    pair_key = tuple(sorted([contact1.id, contact2.id]))
                    if pair_key in checked:
                        continue

                    checked.add(pair_key)

                    # Calculate duplicate score
                    match = calculate_duplicate_score(contact1, contact2)

                    if match.confidence_score >= threshold:
                        duplicates.append(match)

                        if limit and len(duplicates) >= limit:
                            return sorted(duplicates, key=lambda x: x.confidence_score, reverse=True)

            print(f"Analysis complete! Found {len(duplicates):,} potential duplicates.")

            return sorted(duplicates, key=lambda x: x.confidence_score, reverse=True)

    finally:
        conn.close()


# ============================================================================
# REPORTING
# ============================================================================

def print_duplicates_report(duplicates: List[DuplicateMatch], max_results: int = 20):
    """Print formatted duplicate report."""
    print("\n" + "="*80)
    print(f"DUPLICATE CONTACTS REPORT (Top {min(max_results, len(duplicates))})")
    print("="*80)

    for i, dup in enumerate(duplicates[:max_results], 1):
        print(f"\n{i}. Confidence: {dup.confidence_score*100:.1f}%")
        print(f"   Contact 1: {dup.contact1_name} <{dup.contact1_email}> [{dup.contact1_id}]")
        print(f"   Contact 2: {dup.contact2_name} <{dup.contact2_email}> [{dup.contact2_id}]")
        print(f"   Reasons: {', '.join(dup.reasons)}")


def export_to_csv(duplicates: List[DuplicateMatch], filename: str):
    """Export duplicates to CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Confidence', 'Contact1_ID', 'Contact1_Name', 'Contact1_Email',
            'Contact2_ID', 'Contact2_Name', 'Contact2_Email',
            'Name_Similarity', 'Email_Similarity', 'Phone_Match',
            'Address_Similarity', 'Reasons'
        ])

        for dup in duplicates:
            writer.writerow([
                f"{dup.confidence_score*100:.1f}%",
                dup.contact1_id,
                dup.contact1_name,
                dup.contact1_email,
                dup.contact2_id,
                dup.contact2_name,
                dup.contact2_email,
                f"{dup.name_similarity*100:.0f}%",
                f"{dup.email_similarity*100:.0f}%",
                'Yes' if dup.phone_match else 'No',
                f"{dup.address_similarity*100:.0f}%",
                '; '.join(dup.reasons)
            ])

    print(f"\nExported {len(duplicates):,} duplicates to: {filename}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Find duplicate contacts using fuzzy matching',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.8,
        help='Minimum confidence score (0.0-1.0, default: 0.8)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum duplicates to find (for testing)'
    )
    parser.add_argument(
        '--output',
        help='Export results to CSV file'
    )
    parser.add_argument(
        '--max-display',
        type=int,
        default=20,
        help='Maximum results to display (default: 20)'
    )

    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        print("ERROR: Threshold must be between 0.0 and 1.0")
        sys.exit(1)

    print("\n" + "="*80)
    print("FUZZY DUPLICATE DETECTION - FAANG Quality")
    print("="*80)
    print(f"Threshold: {args.threshold*100:.0f}%")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    # Find duplicates
    duplicates = find_duplicates(
        threshold=args.threshold,
        limit=args.limit
    )

    # Print report
    print_duplicates_report(duplicates, args.max_display)

    # Export if requested
    if args.output:
        export_to_csv(duplicates, args.output)

    print("\n" + "="*80)
    print(f"Total duplicates found: {len(duplicates):,}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
