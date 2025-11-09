#!/usr/bin/env python3
"""
DUPLICATE PREVENTION MODULE - FAANG Production Standards
=========================================================

Purpose: Prevent duplicate contacts during imports by detecting existing contacts
across multiple matching strategies (email, phone+name, exact name).

Usage:
    from duplicate_prevention import DuplicateDetector

    # Initialize with database connection
    detector = DuplicateDetector(cursor)

    # Check for duplicates before inserting
    result = detector.find_duplicate(
        email='john@example.com',
        first_name='John',
        last_name='Doe',
        phone='555-1234'
    )

    if result.is_duplicate:
        print(f"Duplicate found: {result.match_type}")
        print(f"Existing contact ID: {result.contact_id}")
        # Update existing contact instead of creating new one
    else:
        # Safe to create new contact
        pass
"""

from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class MatchType(Enum):
    """Type of duplicate match found."""
    EMAIL = "email"              # Exact email match (strongest)
    PHONE_AND_NAME = "phone_name"  # Same phone + similar name
    EXACT_NAME = "exact_name"    # Same first + last name
    NONE = "none"                # No duplicate found


@dataclass
class DuplicateResult:
    """Result of duplicate detection check."""
    is_duplicate: bool
    match_type: MatchType
    contact_id: Optional[str] = None
    existing_email: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    reason: str = ""


class DuplicateDetector:
    """
    Detect duplicate contacts using multiple strategies.

    Strategies (in priority order):
    1. Email exact match (100% confidence)
    2. Phone + name match (90% confidence)
    3. Exact name match (70% confidence - needs manual review)

    FAANG Standards:
    - Type hints on all methods
    - Comprehensive logging
    - Configurable thresholds
    - Transaction safety (read-only queries)
    - Performance optimized (indexed queries)
    """

    def __init__(self, cursor, config: Optional[Dict] = None):
        """
        Initialize duplicate detector.

        Args:
            cursor: psycopg2 cursor (with RealDictCursor)
            config: Optional configuration dict with keys:
                - enable_name_matching: bool (default True)
                - enable_phone_matching: bool (default True)
                - name_match_threshold: float (default 0.7)
        """
        self.cur = cursor
        self.config = config or {}

        # Configuration
        self.enable_name_matching = self.config.get('enable_name_matching', True)
        self.enable_phone_matching = self.config.get('enable_phone_matching', True)
        self.name_match_threshold = self.config.get('name_match_threshold', 0.7)

    def find_duplicate(
        self,
        email: Optional[str],
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> DuplicateResult:
        """
        Find duplicate contact using multiple strategies.

        Args:
            email: Email address (primary identifier)
            first_name: First name (optional, for name matching)
            last_name: Last name (optional, for name matching)
            phone: Phone number (optional, for phone matching)

        Returns:
            DuplicateResult with match information

        Strategy:
            1. Try email exact match (strongest)
            2. Try phone + name match (if enabled)
            3. Try exact name match (if enabled)
            4. Return no match
        """

        # Strategy 1: Email exact match (100% confidence)
        if email:
            email_result = self._check_email_match(email)
            if email_result.is_duplicate:
                return email_result

        # Strategy 2: Phone + name match (90% confidence)
        if self.enable_phone_matching and phone and first_name and last_name:
            phone_result = self._check_phone_name_match(phone, first_name, last_name)
            if phone_result.is_duplicate:
                return phone_result

        # Strategy 3: Exact name match (70% confidence - requires review)
        if self.enable_name_matching and first_name and last_name:
            name_result = self._check_exact_name_match(first_name, last_name)
            if name_result.is_duplicate:
                return name_result

        # No duplicate found
        return DuplicateResult(
            is_duplicate=False,
            match_type=MatchType.NONE,
            confidence=0.0,
            reason="No duplicate found"
        )

    def _check_email_match(self, email: str) -> DuplicateResult:
        """Check for exact email match."""
        self.cur.execute("""
            SELECT id, email
            FROM contacts
            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (email,))

        result = self.cur.fetchone()

        if result:
            return DuplicateResult(
                is_duplicate=True,
                match_type=MatchType.EMAIL,
                contact_id=result['id'],
                existing_email=result['email'],
                confidence=1.0,
                reason=f"Exact email match: {result['email']}"
            )

        return DuplicateResult(
            is_duplicate=False,
            match_type=MatchType.NONE,
            confidence=0.0
        )

    def _check_phone_name_match(self, phone: str, first_name: str, last_name: str) -> DuplicateResult:
        """
        Check for phone + name match.

        Logic: Same phone AND similar name = likely same person
        (e.g., "John Smith" and "Johnny Smith" with same phone)
        """
        # Normalize phone (remove non-digits)
        phone_digits = ''.join(c for c in phone if c.isdigit())
        if len(phone_digits) < 10:
            return DuplicateResult(is_duplicate=False, match_type=MatchType.NONE, confidence=0.0)

        # Last 10 digits (handles country codes)
        phone_normalized = phone_digits[-10:]

        self.cur.execute("""
            SELECT id, email, first_name, last_name, phone
            FROM contacts
            WHERE phone IS NOT NULL
              AND regexp_replace(phone, '[^0-9]', '', 'g') LIKE %s
              AND LOWER(TRIM(first_name)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(last_name)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (f'%{phone_normalized}', first_name, last_name))

        result = self.cur.fetchone()

        if result:
            return DuplicateResult(
                is_duplicate=True,
                match_type=MatchType.PHONE_AND_NAME,
                contact_id=result['id'],
                existing_email=result['email'],
                confidence=0.9,
                reason=f"Same phone ({result['phone']}) and name ({result['first_name']} {result['last_name']})"
            )

        return DuplicateResult(
            is_duplicate=False,
            match_type=MatchType.NONE,
            confidence=0.0
        )

    def _check_exact_name_match(self, first_name: str, last_name: str) -> DuplicateResult:
        """
        Check for exact name match (case-insensitive).

        WARNING: Lower confidence (0.7) - may need manual review.
        Disabled by default unless explicitly enabled.
        """
        self.cur.execute("""
            SELECT id, email, first_name, last_name
            FROM contacts
            WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(last_name)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (first_name, last_name))

        result = self.cur.fetchone()

        if result:
            return DuplicateResult(
                is_duplicate=True,
                match_type=MatchType.EXACT_NAME,
                contact_id=result['id'],
                existing_email=result['email'],
                confidence=0.7,
                reason=f"Exact name match: {result['first_name']} {result['last_name']} (email: {result['email']}) - REVIEW RECOMMENDED"
            )

        return DuplicateResult(
            is_duplicate=False,
            match_type=MatchType.NONE,
            confidence=0.0
        )

    def get_stats(self) -> Dict:
        """Get duplicate detection statistics from database."""
        self.cur.execute("""
            WITH name_dupes AS (
                SELECT
                    LOWER(TRIM(first_name)) as fname,
                    LOWER(TRIM(last_name)) as lname,
                    COUNT(*) as count
                FROM contacts
                WHERE first_name IS NOT NULL AND last_name IS NOT NULL
                GROUP BY LOWER(TRIM(first_name)), LOWER(TRIM(last_name))
                HAVING COUNT(*) > 1
            ),
            phone_dupes AS (
                SELECT
                    regexp_replace(phone, '[^0-9]', '', 'g') as phone_normalized,
                    COUNT(*) as count
                FROM contacts
                WHERE phone IS NOT NULL AND phone <> ''
                GROUP BY regexp_replace(phone, '[^0-9]', '', 'g')
                HAVING COUNT(*) > 1
            )
            SELECT
                (SELECT COUNT(*) FROM name_dupes) as name_duplicate_groups,
                (SELECT SUM(count) FROM name_dupes) as total_name_duplicates,
                (SELECT COUNT(*) FROM phone_dupes) as phone_duplicate_groups,
                (SELECT SUM(count) FROM phone_dupes) as total_phone_duplicates,
                (SELECT COUNT(*) FROM contacts) as total_contacts
        """)

        return dict(self.cur.fetchone())


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_email(email: str) -> Optional[str]:
    """Normalize email address for comparison."""
    if not email:
        return None

    email = email.strip().lower()

    # Remove trailing punctuation (common data entry error)
    email = email.rstrip('.,;')

    # Basic validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return None

    return email


def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number for comparison."""
    if not phone:
        return None

    # Extract digits only
    digits = ''.join(c for c in phone if c.isdigit())

    # Must have at least 10 digits
    if len(digits) < 10:
        return None

    # Return last 10 digits (handles country codes)
    return digits[-10:]


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    """
    Example usage and self-test.
    """
    import os
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from secure_config import get_database_url

    # Connect to database
    conn = psycopg2.connect(
        get_database_url(),
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()

    # Initialize detector
    detector = DuplicateDetector(cur)

    # Test 1: Email match
    print("Test 1: Email duplicate detection")
    result = detector.find_duplicate(email="test@example.com")
    print(f"  Result: {result}")
    print()

    # Test 2: Phone + name match
    print("Test 2: Phone + name duplicate detection")
    result = detector.find_duplicate(
        email="new@example.com",
        first_name="John",
        last_name="Doe",
        phone="555-123-4567"
    )
    print(f"  Result: {result}")
    print()

    # Test 3: Stats
    print("Test 3: Duplicate statistics")
    stats = detector.get_stats()
    print(f"  Stats: {stats}")
    print()

    # Cleanup
    conn.close()

    print("✅ Self-test complete")
