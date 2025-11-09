"""
Pytest configuration and fixtures for Kajabi import tests.

This file is automatically loaded by pytest and provides shared fixtures
and configuration for all tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add scripts directory to path so we can import modules
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))


@pytest.fixture
def sample_csv_dir():
    """Return path to sample CSV directory."""
    return Path(__file__).parent.parent / 'data' / 'samples'


@pytest.fixture
def sample_contacts_csv(sample_csv_dir):
    """Return path to sample contacts CSV if it exists."""
    csv_path = sample_csv_dir / 'v2_contacts.csv'
    if csv_path.exists():
        return str(csv_path)
    return None


@pytest.fixture
def sample_subscriptions_csv(sample_csv_dir):
    """Return path to sample subscriptions CSV if it exists."""
    csv_path = sample_csv_dir / 'v2_subscriptions.csv'
    if csv_path.exists():
        return str(csv_path)
    return None


@pytest.fixture
def sample_transactions_csv(sample_csv_dir):
    """Return path to sample transactions CSV if it exists."""
    csv_path = sample_csv_dir / 'v2_transactions.csv'
    if csv_path.exists():
        return str(csv_path)
    return None


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    def _create_csv(filename, content):
        csv_file = tmp_path / filename
        csv_file.write_text(content)
        return str(csv_file)
    return _create_csv


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires database)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
