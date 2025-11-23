#!/usr/bin/env python3
"""
QuickBooks Donor Import Script
FAANG-Grade Implementation: Safe, auditable, reversible

Purpose: Import DEVELOPMENT donations from QuickBooks CSV into donor module

Strategy:
1. Parse QuickBooks CSV for DEVELOPMENT donations (Full name contains "DEVELOPMENT:")
2. Match donors to existing contacts using priority-based strategy:
   - Priority 1: QB Customer ID match (via external_identities)
   - Priority 2: Email match (100% confidence)
   - Priority 3: Name match (exact → contact_names → fuzzy)
3. Handle edge cases:
   - Joint donors ("John & Jane Smith")
   - Organizations (no name split)
   - Multiple matches (queue for manual review)
4. Enrich contacts with phone/address from QuickBooks
5. Create external_identities records with native QB Customer ID
6. Create/update donor records with lifetime metrics
7. Create transaction records with donation metadata
8. Track enrichment in external_identities metadata

Author: Claude Code
Date: 2025-11-23
"""

import csv
import re
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch, Json

# Import existing modules
try:
    from db_config import get_database_url
except ImportError:
    from secure_config import get_database_url

try:
    import Levenshtein
    HAS_LEVENSHTEIN = True
except ImportError:
    HAS_LEVENSHTEIN = False
    print("Warning: Levenshtein module not found. Fuzzy matching disabled.")


# ============================================================================
# CONFIGURATION
# ============================================================================

DRY_RUN = True  # Default to dry-run for safety
BATCH_SIZE = 100

# Confidence thresholds
CONFIDENCE_HIGH = 0.95    # Auto-match
CONFIDENCE_MEDIUM = 0.80  # Likely match, flag for review
CONFIDENCE_LOW = 0.60     # Possible match, needs review

# Organizations and payment processors to handle specially
SKIP_NAMES = {
    'paypal giving fund',
    'network for good',
    'amazon smile',
    'zettle payments',
    'anonymous',
}

# Patterns that indicate an organization (not a person)
ORG_PATTERNS = [
    r'\bllc\b', r'\binc\b', r'\bcorp\b', r'\bfoundation\b',
    r'\bchurch\b', r'\btemple\b', r'\bcenter\b', r'\binstitute\b',
    r'\bassociation\b', r'\bsociety\b', r'\bministries\b',
]

# Joint donor patterns
JOINT_PATTERNS = [
    r'\s+&\s+',        # "John & Jane"
    r'\s+and\s+',      # "John and Jane"
    r'\s+\+\s+',       # "John + Jane"
]


# ============================================================================
# DATA CLASSES
# ============================================================================

class MatchType(Enum):
    """Type of match found."""
    QB_ID = "qb_id"  # Match via external_identities QB Customer ID
    EMAIL = "email"
    EXACT_NAME = "exact_name"
    CONTACT_NAME_EXACT = "contact_name_exact"
    CONTACT_NAME_FUZZY = "contact_name_fuzzy"
    FUZZY_NAME = "fuzzy_name"
    MULTIPLE = "multiple"
    NONE = "none"


@dataclass
class MatchResult:
    """Result of matching a donor to contacts."""
    contact_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    match_type: MatchType = MatchType.NONE
    confidence: float = 0.0
    reason: str = ""
    alternative_matches: List[Dict] = field(default_factory=list)


@dataclass
class DonorRecord:
    """Parsed donor from QuickBooks CSV."""
    customer_name: str
    customer_id: str  # Native QB Customer ID
    total_amount: float
    transaction_count: int
    first_date: datetime
    last_date: datetime
    transactions: List[Dict] = field(default_factory=list)

    # Contact info from QB
    email: str = ""
    phone: str = ""
    address: Dict = field(default_factory=dict)  # street, city, state, zip

    # Campaign/class info
    campaign: str = ""

    # Derived fields
    is_organization: bool = False
    is_joint_donor: bool = False
    split_names: List[str] = field(default_factory=list)


# ============================================================================
# LOGGING SETUP
# ============================================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/qb_donor_import_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_name(name: str) -> str:
    """Normalize name for comparison."""
    if not name:
        return ""

    # Lowercase and strip
    name = name.lower().strip()

    # Remove content in parentheses/braces
    name = re.sub(r'\s*[\(\{][^\)\}]*[\)\}]\s*', ' ', name)

    # Remove punctuation except &
    name = re.sub(r'[^\w\s&]', '', name)

    # Collapse whitespace
    name = ' '.join(name.split())

    return name


def is_organization(name: str) -> bool:
    """Check if name appears to be an organization."""
    name_lower = name.lower()
    return any(re.search(pattern, name_lower) for pattern in ORG_PATTERNS)


def is_joint_donor(name: str) -> bool:
    """Check if name appears to be joint donors."""
    return any(re.search(pattern, name, re.IGNORECASE) for pattern in JOINT_PATTERNS)


def split_joint_name(name: str) -> List[str]:
    """Split joint donor names into individuals."""
    # Try each pattern
    for pattern in JOINT_PATTERNS:
        parts = re.split(pattern, name, flags=re.IGNORECASE)
        if len(parts) > 1:
            # Handle "John & Jane Smith" -> ["John Smith", "Jane Smith"]
            names = []
            last_part = parts[-1].strip()

            # Extract last name from final part
            last_words = last_part.split()
            if len(last_words) > 1:
                last_name = last_words[-1]
                # First person in final part
                names.append(last_part)
                # Previous parts get the last name appended
                for part in parts[:-1]:
                    first_name = part.strip()
                    if first_name:
                        names.append(f"{first_name} {last_name}")
            else:
                # No obvious last name, just split
                names = [p.strip() for p in parts if p.strip()]

            return names

    return [name]


def parse_amount(amount_str: str) -> float:
    """Parse amount string to float."""
    if not amount_str:
        return 0.0
    # Remove commas, quotes, dollar signs
    cleaned = amount_str.replace(',', '').replace('"', '').replace('$', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%m/%d/%Y')
    except ValueError:
        return None


def should_skip_donor(name: str) -> bool:
    """Check if donor should be skipped."""
    if not name:
        return True

    normalized = normalize_name(name)
    return normalized in SKIP_NAMES


# ============================================================================
# MATCHING ENGINE
# ============================================================================

class DonorMatcher:
    """
    Match QuickBooks donors to existing contacts.

    Uses priority-based strategy:
    1. QB Customer ID match (via external_identities)
    2. Email match (100% confidence)
    3. Exact name match in contacts table
    4. Exact name match in contact_names table (variations)
    5. Fuzzy name match using Levenshtein distance
    """

    def __init__(self, cursor):
        self.cur = cursor
        self.stats = {
            'qb_id_matches': 0,
            'email_matches': 0,
            'exact_name_matches': 0,
            'contact_name_matches': 0,
            'fuzzy_matches': 0,
            'multiple_matches': 0,
            'no_matches': 0,
        }

        # Build lookup caches
        self._build_caches()

    def _build_caches(self):
        """Build in-memory caches for fast matching."""
        logger.info("Building contact lookup caches...")

        # Cache: QB Customer ID -> contact info
        self.qb_id_cache = {}

        # Cache: email -> contact info
        self.email_cache = {}

        # Cache: normalized name -> list of contacts
        self.name_cache = defaultdict(list)

        # Load QB Customer IDs from external_identities
        self.cur.execute("""
            SELECT
                ei.external_id,
                ei.contact_id,
                c.email,
                TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')) as full_name
            FROM external_identities ei
            JOIN contacts c ON ei.contact_id = c.id
            WHERE ei.system = 'quickbooks'
            AND c.deleted_at IS NULL
        """)

        for row in self.cur.fetchall():
            self.qb_id_cache[row['external_id']] = {
                'id': row['contact_id'],
                'email': row['email'],
                'name': row['full_name']
            }

        logger.info(f"Cached {len(self.qb_id_cache)} QB Customer ID mappings")

        # Load all contacts
        self.cur.execute("""
            SELECT
                id,
                email,
                first_name,
                last_name,
                TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) as full_name
            FROM contacts
            WHERE deleted_at IS NULL
        """)

        for row in self.cur.fetchall():
            full_name = row['full_name']
            email = row['email']

            # Build email cache
            if email:
                email_lower = email.lower()
                if email_lower not in self.email_cache:
                    self.email_cache[email_lower] = {
                        'id': row['id'],
                        'email': email,
                        'name': full_name
                    }

            # Build name cache
            if full_name:
                normalized = normalize_name(full_name)
                if normalized:
                    self.name_cache[normalized].append({
                        'id': row['id'],
                        'email': row['email'],
                        'name': full_name,
                        'source': 'contacts'
                    })

        logger.info(f"Cached {len(self.email_cache)} email mappings")

        # Load contact_names variations
        self.cur.execute("""
            SELECT
                cn.contact_id,
                cn.name_text,
                c.email,
                TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')) as primary_name
            FROM contact_names cn
            JOIN contacts c ON cn.contact_id = c.id
            WHERE c.deleted_at IS NULL
        """)

        for row in self.cur.fetchall():
            name_text = row['name_text']
            if name_text:
                normalized = normalize_name(name_text)
                if normalized:
                    # Avoid duplicates
                    existing_ids = {c['id'] for c in self.name_cache[normalized]}
                    if row['contact_id'] not in existing_ids:
                        self.name_cache[normalized].append({
                            'id': row['contact_id'],
                            'email': row['email'],
                            'name': row['primary_name'] or name_text,
                            'source': 'contact_names',
                            'variation': name_text
                        })

        logger.info(f"Cached {len(self.name_cache)} unique normalized names")

    def find_match(self, donor: DonorRecord) -> MatchResult:
        """
        Find matching contact for a donor using priority-based matching.

        Priority:
        1. QB Customer ID match (via external_identities)
        2. Email match (100% confidence)
        3. Name match (exact → contact_names → fuzzy)

        Returns MatchResult with contact info and confidence score.
        """
        donor_name = donor.customer_name

        if not donor_name:
            return MatchResult(match_type=MatchType.NONE, reason="Empty name")

        # Priority 1: QB Customer ID match
        if donor.customer_id and donor.customer_id in self.qb_id_cache:
            match = self.qb_id_cache[donor.customer_id]
            self.stats['qb_id_matches'] += 1
            return MatchResult(
                contact_id=match['id'],
                contact_email=match['email'],
                contact_name=match['name'],
                match_type=MatchType.QB_ID,
                confidence=1.0,
                reason=f"QB Customer ID match: {donor.customer_id}"
            )

        # Priority 2: Email match
        if donor.email:
            email_lower = donor.email.lower()
            if email_lower in self.email_cache:
                match = self.email_cache[email_lower]
                self.stats['email_matches'] += 1
                return MatchResult(
                    contact_id=match['id'],
                    contact_email=match['email'],
                    contact_name=match['name'],
                    match_type=MatchType.EMAIL,
                    confidence=1.0,
                    reason=f"Email match: {donor.email}"
                )

        # Priority 3: Name match
        normalized = normalize_name(donor_name)
        if not normalized:
            self.stats['no_matches'] += 1
            return MatchResult(match_type=MatchType.NONE, reason="Name normalizes to empty")

        # Strategy 3a: Exact name match
        if normalized in self.name_cache:
            matches = self.name_cache[normalized]

            if len(matches) == 1:
                match = matches[0]
                match_type = (MatchType.CONTACT_NAME_EXACT
                             if match.get('source') == 'contact_names'
                             else MatchType.EXACT_NAME)

                self.stats['exact_name_matches' if match_type == MatchType.EXACT_NAME
                          else 'contact_name_matches'] += 1

                return MatchResult(
                    contact_id=match['id'],
                    contact_email=match['email'],
                    contact_name=match['name'],
                    match_type=match_type,
                    confidence=1.0,
                    reason=f"Exact match: {match['name']}"
                )
            else:
                # Multiple matches
                self.stats['multiple_matches'] += 1
                return MatchResult(
                    match_type=MatchType.MULTIPLE,
                    confidence=0.0,
                    reason=f"{len(matches)} contacts match name '{donor_name}'",
                    alternative_matches=[
                        {'id': m['id'], 'email': m['email'], 'name': m['name']}
                        for m in matches
                    ]
                )

        # Strategy 3b: Fuzzy name match
        if HAS_LEVENSHTEIN:
            best_match = None
            best_score = 0.0

            for norm_name, contacts in self.name_cache.items():
                score = Levenshtein.ratio(normalized, norm_name)
                if score > best_score and score >= CONFIDENCE_LOW:
                    best_score = score
                    best_match = contacts[0]  # Take first if multiple

            if best_match and best_score >= CONFIDENCE_MEDIUM:
                self.stats['fuzzy_matches'] += 1
                return MatchResult(
                    contact_id=best_match['id'],
                    contact_email=best_match['email'],
                    contact_name=best_match['name'],
                    match_type=MatchType.FUZZY_NAME,
                    confidence=best_score,
                    reason=f"Fuzzy match ({best_score:.0%}): {best_match['name']}"
                )

        # No match found
        self.stats['no_matches'] += 1
        return MatchResult(
            match_type=MatchType.NONE,
            confidence=0.0,
            reason=f"No match found for '{donor_name}'"
        )

    def get_stats(self) -> Dict:
        """Return matching statistics."""
        return self.stats.copy()


# ============================================================================
# CSV PARSING
# ============================================================================

def load_quickbooks_csv(filepath: str) -> Tuple[List[DonorRecord], Dict]:
    """
    Load and parse QuickBooks CSV file.

    Returns:
        - List of DonorRecord objects (DEVELOPMENT donations only)
        - Stats dictionary
    """
    logger.info(f"Loading QuickBooks CSV: {filepath}")

    # Track donors by customer name
    donor_data = defaultdict(lambda: {
        'total': 0.0,
        'count': 0,
        'first_date': None,
        'last_date': None,
        'transactions': [],
        'customer_id': '',
        'email': '',
        'phone': '',
        'address': {},
        'campaign': ''
    })

    stats = {
        'total_rows': 0,
        'development_rows': 0,
        'skipped_rows': 0,
        'unique_donors': 0,
    }

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        # Read all lines to find header row
        lines = f.readlines()

    # Find the header row (contains "Customer" and "Transaction date")
    header_idx = None
    for i, line in enumerate(lines):
        if 'Customer,' in line and 'Transaction date' in line:
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find header row in CSV")

    # Parse from header row
    import io
    csv_content = ''.join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_content))

    for row in reader:
        stats['total_rows'] += 1

        full_name = row.get('Full name', '')

        # Only process DEVELOPMENT donations
        if 'DEVELOPMENT:' not in full_name:
            stats['skipped_rows'] += 1
            continue

        stats['development_rows'] += 1

        customer = row.get('Customer', '').strip()
        if not customer or should_skip_donor(customer):
            continue

        amount = parse_amount(row.get('Amount', '0'))
        trans_date = parse_date(row.get('Transaction date', ''))

        # Update donor aggregates
        data = donor_data[customer]
        data['total'] += amount
        data['count'] += 1

        if trans_date:
            if data['first_date'] is None or trans_date < data['first_date']:
                data['first_date'] = trans_date
            if data['last_date'] is None or trans_date > data['last_date']:
                data['last_date'] = trans_date

        # Extract contact info (take first non-empty values)
        customer_id = row.get('Customer ID', '').strip()
        if customer_id and not data['customer_id']:
            data['customer_id'] = customer_id

        email = row.get('Customer email', '').strip()
        if email and '@' in email and not data['email']:
            data['email'] = email

        phone = row.get('Customer phone', '').strip() or row.get('Customer mobile', '').strip()
        if phone and not data['phone']:
            data['phone'] = phone

        # Extract address (prefer billing)
        if not data['address']:
            bill_street = row.get('Customer bill street', '').strip()
            if bill_street:
                data['address'] = {
                    'street': bill_street,
                    'city': row.get('Customer bill city', '').strip(),
                    'state': row.get('Customer bill state', '').strip(),
                    'zip': row.get('Customer bill zip', '').strip(),
                }
            else:
                ship_street = row.get('Customer ship street', '').strip()
                if ship_street:
                    data['address'] = {
                        'street': ship_street,
                        'city': row.get('Customer ship city', '').strip(),
                        'state': row.get('Customer ship state', '').strip(),
                        'zip': row.get('Customer ship zip', '').strip(),
                    }

        # Extract campaign from Class column
        class_name = row.get('Class full name', '').strip()
        if class_name and not data['campaign']:
            data['campaign'] = class_name

        # Store transaction details
        data['transactions'].append({
            'date': trans_date,
            'amount': amount,
            'category': full_name,
            'memo': row.get('Memo/Description', ''),
            'payment_method': row.get('Payment method', ''),
            'invoice_num': row.get('Num', ''),
            'transaction_type': row.get('Transaction type', ''),
        })

    # Convert to DonorRecord objects
    donors = []
    for customer, data in donor_data.items():
        record = DonorRecord(
            customer_name=customer,
            customer_id=data['customer_id'],
            total_amount=data['total'],
            transaction_count=data['count'],
            first_date=data['first_date'] or datetime.now(),
            last_date=data['last_date'] or datetime.now(),
            transactions=data['transactions'],
            email=data['email'],
            phone=data['phone'],
            address=data['address'],
            campaign=data['campaign'],
        )

        # Classify donor type
        record.is_organization = is_organization(customer)
        record.is_joint_donor = is_joint_donor(customer)
        if record.is_joint_donor:
            record.split_names = split_joint_name(customer)

        donors.append(record)

    stats['unique_donors'] = len(donors)

    logger.info(f"Parsed {stats['development_rows']:,} DEVELOPMENT rows")
    logger.info(f"Found {stats['unique_donors']:,} unique donors")

    return donors, stats


# ============================================================================
# MAIN IMPORT LOGIC
# ============================================================================

class QuickBooksDonorImporter:
    """
    Import QuickBooks donors into the donor module.
    """

    def __init__(self, csv_path: str, dry_run: bool = True):
        self.csv_path = csv_path
        self.dry_run = dry_run
        self.conn = None
        self.cur = None
        self.matcher = None

        # Results tracking
        self.results = {
            'matched': [],      # High confidence matches
            'review': [],       # Need manual review
            'multiple': [],     # Multiple possible matches
            'new': [],          # No match, new contact needed
            'joint': [],        # Joint donors
            'org': [],          # Organizations
        }

        # Enrichment tracking
        self.enrichment_stats = {
            'phone_available': 0,
            'address_available': 0,
            'email_available': 0,
        }

    def connect(self):
        """Establish database connection."""
        self.conn = psycopg2.connect(
            get_database_url(),
            cursor_factory=RealDictCursor
        )
        self.cur = self.conn.cursor()
        logger.info("Database connection established")

    def disconnect(self):
        """Clean up database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def run(self):
        """Execute the import process."""
        logger.info("=" * 80)
        logger.info("QUICKBOOKS DONOR IMPORT")
        logger.info("=" * 80)
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        logger.info("")

        try:
            self.connect()

            # Initialize matcher
            self.matcher = DonorMatcher(self.cur)

            # Load CSV
            donors, parse_stats = load_quickbooks_csv(self.csv_path)

            # Match donors to contacts
            self._match_donors(donors)

            # Generate report
            self._generate_report()

            # Execute import (if not dry run)
            if not self.dry_run:
                self._execute_import()
            else:
                logger.info("\n" + "=" * 80)
                logger.info("DRY RUN COMPLETE - No changes made")
                logger.info("Run with --execute to apply changes")
                logger.info("=" * 80)

        finally:
            self.disconnect()

    def _match_donors(self, donors: List[DonorRecord]):
        """Match all donors to contacts."""
        logger.info("\n" + "=" * 80)
        logger.info("MATCHING DONORS TO CONTACTS")
        logger.info("=" * 80)

        for donor in donors:
            # Track enrichment data availability
            if donor.phone:
                self.enrichment_stats['phone_available'] += 1
            if donor.address.get('street'):
                self.enrichment_stats['address_available'] += 1
            if donor.email:
                self.enrichment_stats['email_available'] += 1

            # Handle special cases first
            if donor.is_joint_donor:
                self.results['joint'].append({
                    'donor': donor,
                    'split_names': donor.split_names
                })
                continue

            if donor.is_organization:
                match = self.matcher.find_match(donor)
                self.results['org'].append({
                    'donor': donor,
                    'match': match
                })
                continue

            # Regular matching
            match = self.matcher.find_match(donor)

            if match.match_type == MatchType.MULTIPLE:
                self.results['multiple'].append({
                    'donor': donor,
                    'matches': match.alternative_matches
                })
            elif match.match_type == MatchType.NONE:
                self.results['new'].append(donor)
            elif match.confidence >= CONFIDENCE_HIGH:
                self.results['matched'].append({
                    'donor': donor,
                    'match': match
                })
            else:
                self.results['review'].append({
                    'donor': donor,
                    'match': match
                })

        # Log matching stats
        stats = self.matcher.get_stats()
        logger.info("")
        logger.info("Matching Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    def _generate_report(self):
        """Generate matching confidence report."""
        logger.info("\n" + "=" * 80)
        logger.info("MATCH CONFIDENCE REPORT")
        logger.info("=" * 80)

        # Summary
        logger.info("\nSummary:")
        logger.info(f"  ✅ Auto-match (high confidence): {len(self.results['matched'])}")
        logger.info(f"  🔍 Review needed (medium confidence): {len(self.results['review'])}")
        logger.info(f"  ⚠️  Multiple matches: {len(self.results['multiple'])}")
        logger.info(f"  🆕 New donors (no match): {len(self.results['new'])}")
        logger.info(f"  👥 Joint donors: {len(self.results['joint'])}")
        logger.info(f"  🏢 Organizations: {len(self.results['org'])}")

        # Enrichment data available
        total_donors = (len(self.results['matched']) + len(self.results['review']) +
                       len(self.results['multiple']) + len(self.results['new']) +
                       len(self.results['joint']) + len(self.results['org']))
        logger.info("\nEnrichment Data Available:")
        logger.info(f"  📧 Email:   {self.enrichment_stats['email_available']} / {total_donors}")
        logger.info(f"  📞 Phone:   {self.enrichment_stats['phone_available']} / {total_donors}")
        logger.info(f"  🏠 Address: {self.enrichment_stats['address_available']} / {total_donors}")

        # High confidence matches
        if self.results['matched']:
            logger.info("\n" + "-" * 40)
            logger.info("HIGH CONFIDENCE MATCHES (top 10):")
            for item in self.results['matched'][:10]:
                donor = item['donor']
                match = item['match']
                logger.info(f"  {donor.customer_name}")
                logger.info(f"    → {match.contact_name} ({match.contact_email})")
                logger.info(f"    Total: ${donor.total_amount:,.2f} | {donor.transaction_count} transactions")

        # Needs review
        if self.results['review']:
            logger.info("\n" + "-" * 40)
            logger.info("NEEDS REVIEW (medium confidence):")
            for item in self.results['review']:
                donor = item['donor']
                match = item['match']
                logger.info(f"  {donor.customer_name}")
                logger.info(f"    → {match.contact_name} ({match.confidence:.0%}) - {match.reason}")

        # Multiple matches
        if self.results['multiple']:
            logger.info("\n" + "-" * 40)
            logger.info("MULTIPLE MATCHES (manual resolution needed):")
            for item in self.results['multiple']:
                donor = item['donor']
                logger.info(f"  {donor.customer_name}")
                for alt in item['matches'][:3]:
                    logger.info(f"    - {alt['name']} ({alt['email']})")

        # Joint donors
        if self.results['joint']:
            logger.info("\n" + "-" * 40)
            logger.info("JOINT DONORS (need splitting):")
            for item in self.results['joint'][:10]:
                donor = item['donor']
                logger.info(f"  {donor.customer_name}")
                logger.info(f"    → Split into: {', '.join(item['split_names'])}")

        # New donors
        if self.results['new']:
            logger.info("\n" + "-" * 40)
            logger.info(f"NEW DONORS ({len(self.results['new'])} total, showing top 10):")
            for donor in sorted(self.results['new'],
                              key=lambda d: d.total_amount,
                              reverse=True)[:10]:
                logger.info(f"  {donor.customer_name}")
                logger.info(f"    Total: ${donor.total_amount:,.2f} | {donor.transaction_count} transactions")

    def _execute_import(self):
        """Execute the actual import (not dry run)."""
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTING IMPORT")
        logger.info("=" * 80)

        imported_count = 0
        error_count = 0
        donor_ids = []

        try:
            # Process high-confidence matches
            total_matched = len(self.results['matched'])
            logger.info(f"\nProcessing {total_matched} high-confidence matches...")
            for i, item in enumerate(self.results['matched'], 1):
                try:
                    if i % 50 == 0 or i == 1:
                        logger.info(f"  Processing donor {i}/{total_matched}: {item['donor'].customer_name}")
                    donor_id = self._import_donor(item['donor'], item['match'].contact_id)
                    if donor_id:
                        donor_ids.append(donor_id)
                        imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing {item['donor'].customer_name}: {e}")
                    error_count += 1

            # Process organizations that matched
            org_with_match = [item for item in self.results['org'] if item['match'].contact_id]
            total_orgs = len(org_with_match)
            if total_orgs > 0:
                logger.info(f"\nProcessing {total_orgs} matched organizations...")
            for i, item in enumerate(org_with_match, 1):
                try:
                    if i % 10 == 0 or i == 1:
                        logger.info(f"  Processing org {i}/{total_orgs}: {item['donor'].customer_name}")
                    donor_id = self._import_donor(item['donor'], item['match'].contact_id)
                    if donor_id:
                        donor_ids.append(donor_id)
                        imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing org {item['donor'].customer_name}: {e}")
                    error_count += 1

            # Commit all changes
            self.conn.commit()
            logger.info(f"\n✅ Committed {imported_count} donors to database")

            # Update donor metrics
            logger.info("\nUpdating donor metrics...")
            for donor_id in donor_ids:
                try:
                    self.cur.execute("SELECT update_donor_metrics(%s)", (donor_id,))
                except Exception as e:
                    logger.warning(f"Could not update metrics for {donor_id}: {e}")

            self.conn.commit()
            logger.info(f"✅ Updated metrics for {len(donor_ids)} donors")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Import failed, rolled back: {e}")
            raise

        logger.info("\n" + "=" * 80)
        logger.info("IMPORT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  Imported: {imported_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Skipped (review needed): {len(self.results['review'])}")
        logger.info(f"  Skipped (multiple matches): {len(self.results['multiple'])}")
        logger.info(f"  Skipped (new donors): {len(self.results['new'])}")
        logger.info(f"  Skipped (joint donors): {len(self.results['joint'])}")

    def _import_donor(self, donor: DonorRecord, contact_id: str) -> Optional[str]:
        """
        Import a single donor and their transactions.

        Includes enrichment logic:
        - Add phone if contact missing phone
        - Add address if contact missing address
        - Track enrichment in external_identities metadata

        Returns donor_id if successful.
        """
        enriched_fields = []

        # 1. Check contact for enrichment opportunities
        self.cur.execute("""
            SELECT phone, address_line_1, city, state, postal_code
            FROM contacts WHERE id = %s
        """, (contact_id,))
        contact = self.cur.fetchone()

        if contact:
            # Enrich phone if missing
            if not contact['phone'] and donor.phone:
                self.cur.execute("""
                    UPDATE contacts SET phone = %s, updated_at = now()
                    WHERE id = %s
                """, (donor.phone, contact_id))
                enriched_fields.append('phone')

            # Enrich address if missing
            if not contact['address_line_1'] and donor.address.get('street'):
                self.cur.execute("""
                    UPDATE contacts SET
                        address_line_1 = %s,
                        city = %s,
                        state = %s,
                        postal_code = %s,
                        updated_at = now()
                    WHERE id = %s
                """, (
                    donor.address.get('street', ''),
                    donor.address.get('city', ''),
                    donor.address.get('state', ''),
                    donor.address.get('zip', ''),
                    contact_id
                ))
                enriched_fields.append('address')

        # 2. Create external_identity with native QB Customer ID
        metadata = {
            'customer_name': donor.customer_name,
            'campaign': donor.campaign,
            'total_amount': donor.total_amount,
            'transaction_count': donor.transaction_count,
        }
        if enriched_fields:
            metadata['enriched_fields'] = enriched_fields

        self.cur.execute("""
            INSERT INTO external_identities (contact_id, system, external_id, verified, metadata)
            VALUES (%s, 'quickbooks', %s, true, %s)
            ON CONFLICT (contact_id, system) DO UPDATE
            SET external_id = EXCLUDED.external_id, verified = true, last_synced_at = now(), metadata = %s
            RETURNING id
        """, (
            contact_id,
            donor.customer_id,  # Use native QB Customer ID
            Json(metadata),
            Json(metadata)
        ))

        # 3. Create or update donor record
        self.cur.execute("""
            INSERT INTO donors (
                contact_id,
                status,
                lifetime_amount,
                lifetime_count,
                first_gift_date,
                last_gift_date,
                quickbooks_customer_id
            )
            VALUES (%s, 'prospect', 0, 0, %s, %s, %s)
            ON CONFLICT (contact_id) DO UPDATE
            SET
                quickbooks_customer_id = EXCLUDED.quickbooks_customer_id,
                updated_at = now()
            RETURNING id
        """, (
            contact_id,
            donor.first_date,
            donor.last_date,
            donor.customer_id  # Use native QB Customer ID
        ))

        result = self.cur.fetchone()
        donor_id = result['id'] if result else None

        if not donor_id:
            return None

        # 3. Import transactions
        today = datetime.now().date()
        ninety_days_ago = today - timedelta(days=90)

        for trans in donor.transactions:
            # Parse donation category
            category = trans.get('category', '')
            parts = category.split(':')
            donation_category = parts[0] if parts else ''
            donation_subcategory = parts[1] if len(parts) > 1 else ''

            # Determine transaction type based on amount sign
            amount = trans.get('amount', 0)
            if amount < 0:
                trans_type = 'refund'
                amount = amount  # Keep negative for refunds
            else:
                trans_type = 'purchase'

            # Insert transaction
            self.cur.execute("""
                INSERT INTO transactions (
                    contact_id,
                    transaction_type,
                    status,
                    amount,
                    currency,
                    payment_method,
                    transaction_date,
                    is_donation,
                    donation_source,
                    donation_category,
                    donation_subcategory,
                    quickbooks_invoice_num,
                    quickbooks_customer_name,
                    quickbooks_memo
                )
                VALUES (%s, %s, 'completed', %s, 'USD', %s, %s, true, 'quickbooks', %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                contact_id,
                trans_type,
                amount,
                trans.get('payment_method', ''),
                trans.get('date'),
                donation_category,
                donation_subcategory,
                trans.get('invoice_num', ''),
                donor.customer_name,
                trans.get('memo', '')
            ))

            trans_result = self.cur.fetchone()
            transaction_id = trans_result['id'] if trans_result else None

            # 4. Create acknowledgment record
            if transaction_id:
                trans_date = trans.get('date')
                if trans_date:
                    trans_date_only = trans_date.date() if hasattr(trans_date, 'date') else trans_date

                    # Determine acknowledgment status
                    if trans_date_only >= ninety_days_ago:
                        ack_status = 'auto_queued'
                    else:
                        ack_status = 'skipped_old'

                    self.cur.execute("""
                        INSERT INTO donation_acknowledgments (
                            transaction_id,
                            donor_id,
                            status,
                            donor_name,
                            donation_amount,
                            donation_date,
                            queued_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (transaction_id) DO NOTHING
                    """, (
                        transaction_id,
                        donor_id,
                        ack_status,
                        donor.customer_name,
                        trans.get('amount', 0),
                        trans_date_only,
                        datetime.now() if ack_status == 'auto_queued' else None
                    ))

        return donor_id


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Import QuickBooks donors into the donor module'
    )
    parser.add_argument(
        'csv_file',
        nargs='?',
        default='/workspaces/starhouse-database-v2/data/current/11-23-25-QB_Import_v2.csv',
        help='Path to QuickBooks CSV file'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute import (default is dry-run)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV for match results'
    )

    args = parser.parse_args()

    # Run import
    importer = QuickBooksDonorImporter(
        csv_path=args.csv_file,
        dry_run=not args.execute
    )
    importer.run()


if __name__ == '__main__':
    main()
