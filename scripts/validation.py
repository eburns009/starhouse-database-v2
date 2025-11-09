"""
Data validation and sanitization utilities.

Provides robust validation for emails, phone numbers, and other data types.
"""
import re
from typing import Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime


# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize user input string.

    Args:
        value: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove control characters except newline
    value = ''.join(char for char in value if ord(char) >= 32 or char == '\n')

    # Trim whitespace
    value = value.strip()

    # Limit length
    value = value[:max_length]

    # Remove CSV injection prefixes
    if value and value[0] in ['=', '+', '-', '@']:
        value = "'" + value

    return value


def validate_email(email: str) -> Optional[str]:
    """
    Validate and normalize email address.

    Args:
        email: Email address to validate

    Returns:
        Normalized email address or None if invalid
    """
    if not email or not isinstance(email, str):
        return None

    email = email.strip().lower()

    # Check if empty after stripping
    if not email:
        return None

    # Basic validation
    if '@' not in email:
        return None

    # Regex validation
    if not EMAIL_REGEX.match(email):
        return None

    # Check for common invalid patterns
    if email.startswith('@') or email.endswith('@'):
        return None

    parts = email.split('@')
    if len(parts) != 2:
        return None

    local, domain = parts
    if not local or not domain:
        return None

    # Check domain has TLD
    if '.' not in domain:
        return None

    domain_parts = domain.split('.')
    if any(not part for part in domain_parts):
        return None

    return email


def parse_decimal(value: str) -> Optional[Decimal]:
    """
    Parse decimal value from string, handling various formats.

    Args:
        value: String representation of decimal number

    Returns:
        Decimal value or None if invalid
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()
    if value in ['', 'N/A', 'null', 'None']:
        return None

    try:
        # Remove currency symbols and commas
        clean = value.replace('$', '').replace(',', '').replace('€', '').replace('£', '').strip()
        if not clean:
            return None
        return Decimal(clean)
    except (ValueError, InvalidOperation):
        return None


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse date string to ISO format.

    Args:
        date_str: Date string in various formats

    Returns:
        ISO formatted date string or None if invalid
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if date_str in ['', 'N/A', 'null', 'None']:
        return None

    try:
        # Try ISO format with time: "2020-11-05 11:10:44 -0700"
        if '-' in date_str and ':' in date_str:
            # Split off timezone if present
            date_part = date_str.split('.')[0]
            if ' ' in date_part:
                # May have timezone at end
                parts = date_part.rsplit(' ', 1)
                # Check if last part is timezone (starts with + or -)
                if len(parts) > 1 and parts[1] and parts[1][0] in ['+', '-']:
                    date_part = parts[0]
            dt = datetime.strptime(date_part, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')

        # Try Kajabi format: "Dec 19, 2021"
        dt = datetime.strptime(date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return None


def parse_comma_separated(value: str) -> list[str]:
    """
    Parse comma-separated string into list of items.

    Args:
        value: Comma-separated string

    Returns:
        List of trimmed items
    """
    if not value or not isinstance(value, str):
        return []

    value = value.strip()
    if value in ['', 'N/A', 'null', 'None']:
        return []

    # Split and clean each item
    items = [item.strip() for item in value.split(',')]
    return [item for item in items if item]


def validate_phone(phone: str) -> Optional[str]:
    """
    Basic phone number validation and normalization.

    Args:
        phone: Phone number string

    Returns:
        Normalized phone number or None if invalid
    """
    if not phone or not isinstance(phone, str):
        return None

    # Remove common formatting characters
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Must have at least 10 digits
    if len(cleaned) < 10:
        return None

    return phone.strip()


def validate_postal_code(postal_code: str, country: str = 'US') -> Optional[str]:
    """
    Validate postal/zip code.

    Args:
        postal_code: Postal code string
        country: Country code (default: US)

    Returns:
        Validated postal code or None if invalid
    """
    if not postal_code or not isinstance(postal_code, str):
        return None

    postal_code = postal_code.strip().upper()

    if country == 'US':
        # US ZIP code: 5 digits or 5+4 format
        if re.match(r'^\d{5}(-\d{4})?$', postal_code):
            return postal_code
    elif country == 'CA':
        # Canadian postal code: A1A 1A1
        if re.match(r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$', postal_code):
            return postal_code
    else:
        # Generic: allow if not empty
        return postal_code if postal_code else None

    return None
