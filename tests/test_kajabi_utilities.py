"""
Unit tests for Kajabi importer utility functions.

Run with:
    pytest tests/test_kajabi_utilities.py -v
    pytest tests/test_kajabi_utilities.py -v --cov=scripts.weekly_import_kajabi_simple
"""
import pytest
from decimal import Decimal
from datetime import datetime

# Import utility functions from the script
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from weekly_import_kajabi_simple import (
    parse_decimal,
    parse_date,
    parse_comma_separated,
    normalize_email,
    map_payment_status,
)


class TestParseDecimal:
    """Tests for parse_decimal function."""

    def test_parse_valid_decimal(self):
        """Should parse a valid decimal string."""
        assert parse_decimal("1234.56") == Decimal("1234.56")

    def test_parse_decimal_with_dollar_sign(self):
        """Should remove dollar sign and parse."""
        assert parse_decimal("$1234.56") == Decimal("1234.56")

    def test_parse_decimal_with_comma(self):
        """Should remove commas and parse."""
        assert parse_decimal("1,234.56") == Decimal("1234.56")

    def test_parse_decimal_with_both(self):
        """Should remove both dollar and comma."""
        assert parse_decimal("$1,234.56") == Decimal("1234.56")

    def test_parse_zero(self):
        """Should parse zero."""
        assert parse_decimal("0") == Decimal("0")

    def test_parse_negative(self):
        """Should parse negative numbers."""
        assert parse_decimal("-123.45") == Decimal("-123.45")

    def test_parse_empty_string(self):
        """Should return None for empty string."""
        assert parse_decimal("") is None

    def test_parse_whitespace(self):
        """Should handle whitespace."""
        assert parse_decimal("  123.45  ") == Decimal("123.45")

    def test_parse_na(self):
        """Should return None for N/A."""
        assert parse_decimal("N/A") is None

    def test_parse_null(self):
        """Should return None for null."""
        assert parse_decimal("null") is None

    def test_parse_invalid(self):
        """Should return None for invalid input."""
        assert parse_decimal("invalid") is None
        assert parse_decimal("abc123") is None


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_iso_format_with_time(self):
        """Should parse ISO format with time."""
        result = parse_date("2020-11-05 11:10:44 -0700")
        assert result == "2020-11-05 11:10:44"

    def test_parse_kajabi_format(self):
        """Should parse Kajabi format (Dec 19, 2021)."""
        result = parse_date("Dec 19, 2021")
        assert result == "2021-12-19"

    def test_parse_empty_string(self):
        """Should return None for empty string."""
        assert parse_date("") is None

    def test_parse_na(self):
        """Should return None for N/A."""
        assert parse_date("N/A") is None

    def test_parse_null(self):
        """Should return None for null."""
        assert parse_date("null") is None

    def test_parse_invalid(self):
        """Should return None for invalid date."""
        assert parse_date("invalid date") is None


class TestParseCommaSeparated:
    """Tests for parse_comma_separated function."""

    def test_parse_single_item(self):
        """Should parse a single item."""
        assert parse_comma_separated("Item 1") == ["Item 1"]

    def test_parse_multiple_items(self):
        """Should parse multiple comma-separated items."""
        result = parse_comma_separated("Item 1, Item 2, Item 3")
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_with_extra_whitespace(self):
        """Should trim whitespace from items."""
        result = parse_comma_separated("  Item 1  ,  Item 2  ,  Item 3  ")
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_empty_string(self):
        """Should return empty list for empty string."""
        assert parse_comma_separated("") == []

    def test_parse_na(self):
        """Should return empty list for N/A."""
        assert parse_comma_separated("N/A") == []

    def test_parse_null(self):
        """Should return empty list for null."""
        assert parse_comma_separated("null") == []

    def test_parse_single_comma(self):
        """Should handle single comma."""
        result = parse_comma_separated("Item 1,")
        assert result == ["Item 1"]

    def test_parse_complex_names(self):
        """Should handle complex product/tag names."""
        result = parse_comma_separated(
            "A New Astrology: Basics of Star Wisdom, The 12 Senses, Star Wisdom at the StarHouse"
        )
        assert len(result) == 3
        assert "A New Astrology: Basics of Star Wisdom" in result


class TestNormalizeEmail:
    """Tests for normalize_email function."""

    def test_normalize_valid_email(self):
        """Should normalize a valid email."""
        assert normalize_email("TEST@EXAMPLE.COM") == "test@example.com"

    def test_normalize_with_whitespace(self):
        """Should trim whitespace."""
        assert normalize_email("  test@example.com  ") == "test@example.com"

    def test_normalize_mixed_case(self):
        """Should lowercase email."""
        assert normalize_email("Test.User@Example.COM") == "test.user@example.com"

    def test_invalid_email_no_at(self):
        """Should return None for email without @."""
        assert normalize_email("notanemail") is None

    def test_invalid_email_no_domain(self):
        """Should return None for email without domain."""
        assert normalize_email("test@") is None

    def test_invalid_email_no_tld(self):
        """Should return None for email without TLD."""
        assert normalize_email("test@example") is None

    def test_empty_string(self):
        """Should return None for empty string."""
        assert normalize_email("") is None

    def test_na(self):
        """Should return None for N/A."""
        assert normalize_email("N/A") is None

    def test_null(self):
        """Should return None for null."""
        assert normalize_email("null") is None

    def test_valid_complex_email(self):
        """Should handle complex but valid emails."""
        email = "user.name+tag@example.co.uk"
        assert normalize_email(email) == email.lower()


class TestMapPaymentStatus:
    """Tests for map_payment_status function."""

    def test_map_succeeded_to_completed(self):
        """Should map 'succeeded' to 'completed'."""
        assert map_payment_status("succeeded") == "completed"

    def test_map_success_to_completed(self):
        """Should map 'success' to 'completed'."""
        assert map_payment_status("success") == "completed"

    def test_map_completed(self):
        """Should keep 'completed' as 'completed'."""
        assert map_payment_status("completed") == "completed"

    def test_map_failed(self):
        """Should keep 'failed' as 'failed'."""
        assert map_payment_status("failed") == "failed"

    def test_map_failure_to_failed(self):
        """Should map 'failure' to 'failed'."""
        assert map_payment_status("failure") == "failed"

    def test_map_pending(self):
        """Should keep 'pending' as 'pending'."""
        assert map_payment_status("pending") == "pending"

    def test_map_refunded(self):
        """Should keep 'refunded' as 'refunded'."""
        assert map_payment_status("refunded") == "refunded"

    def test_map_refund_to_refunded(self):
        """Should map 'refund' to 'refunded'."""
        assert map_payment_status("refund") == "refunded"

    def test_map_disputed(self):
        """Should keep 'disputed' as 'disputed'."""
        assert map_payment_status("disputed") == "disputed"

    def test_map_dispute_to_disputed(self):
        """Should map 'dispute' to 'disputed'."""
        assert map_payment_status("dispute") == "disputed"

    def test_map_case_insensitive(self):
        """Should handle case-insensitive input."""
        assert map_payment_status("SUCCEEDED") == "completed"
        assert map_payment_status("Failed") == "failed"

    def test_map_with_whitespace(self):
        """Should handle whitespace."""
        assert map_payment_status("  succeeded  ") == "completed"

    def test_map_unknown_defaults_to_completed(self):
        """Should default unknown statuses to 'completed'."""
        assert map_payment_status("unknown") == "completed"
        assert map_payment_status("weird_status") == "completed"

    def test_map_empty_defaults_to_completed(self):
        """Should default empty string to 'completed'."""
        assert map_payment_status("") == "completed"


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_process_kajabi_contact_row(self):
        """Should process a typical Kajabi contact row."""
        # Simulate a row from Kajabi contacts export
        email = normalize_email("  TEST@EXAMPLE.COM  ")
        assert email == "test@example.com"

        tags = parse_comma_separated("Member, Cultural Renewal, Star Wisdom")
        assert len(tags) == 3
        assert "Member" in tags

        products = parse_comma_separated("Course A, Course B, Membership Portal")
        assert len(products) == 3

    def test_process_kajabi_transaction_row(self):
        """Should process a typical Kajabi transaction row."""
        email = normalize_email("customer@example.com")
        assert email == "customer@example.com"

        amount = parse_decimal("$1,234.56")
        assert amount == Decimal("1234.56")

        status = map_payment_status("succeeded")
        assert status == "completed"

        date = parse_date("Dec 19, 2021")
        assert date == "2021-12-19"

    def test_handle_missing_data(self):
        """Should gracefully handle missing/invalid data."""
        assert normalize_email("") is None
        assert parse_decimal("N/A") is None
        assert parse_date("null") is None
        assert parse_comma_separated("") == []
        assert map_payment_status("") == "completed"  # Safe default


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
