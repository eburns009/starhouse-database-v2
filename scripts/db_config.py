#!/usr/bin/env python3
"""
Secure Database Configuration Module (FAANG Standards)

Loads database credentials from environment variables with:
- Comprehensive error handling and validation
- Security-focused logging (no credential exposure)
- Connection helper functions
- Environment-based configuration
- Clear error messages for debugging

SECURITY: NEVER hardcode credentials in scripts - always use this module.

Usage:
    from db_config import get_database_url, get_connection

    # Get database URL
    DATABASE_URL = get_database_url()

    # Or get a connection directly
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contacts LIMIT 1")
    ...

Author: Security Fix Team
Date: 2025-11-17
"""

import os
import sys
from pathlib import Path
from typing import Optional, Any


def get_database_url(production: bool = False) -> str:
    """
    Get database URL from environment variable.

    Looks for DATABASE_URL (or PRODUCTION_DATABASE_URL) in:
    1. Environment variables
    2. .env file in project root

    Args:
        production: If True, use PRODUCTION_DATABASE_URL instead of DATABASE_URL

    Returns:
        str: Database connection URL

    Raises:
        ValueError: If required DATABASE_URL is not set
    """
    # Try to load from .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv

        # Find project root (where .env should be)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        env_file = project_root / '.env'

        if env_file.exists():
            load_dotenv(env_file)
            print(f"[INFO] Loaded credentials from {env_file}")
        else:
            print(f"[WARN] No .env file found at {env_file}")
            print(f"[INFO] Copy .env.example to .env and fill in your credentials")
    except ImportError:
        print("[WARN] python-dotenv not installed. Install with: pip install python-dotenv")
        print("[INFO] Falling back to environment variables only")

    # Get DATABASE_URL from environment
    env_var_name = 'PRODUCTION_DATABASE_URL' if production else 'DATABASE_URL'
    database_url = os.getenv(env_var_name)

    if not database_url:
        print("\n" + "=" * 80)
        print(f"ERROR: {env_var_name} environment variable not set")
        print("=" * 80)
        print()
        if production:
            print("To fix this, add PRODUCTION_DATABASE_URL to your .env file")
            print("Get this from Supabase Dashboard → Settings → Database → Connection string")
        else:
            print("To fix this:")
            print("1. Copy .env.example to .env:")
            print("   cp .env.example .env")
            print()
            print("2. Edit .env and add your database credentials")
        print()
        print("3. Re-run the script")
        print()
        print("=" * 80)
        sys.exit(1)

    # Validate it looks like a PostgreSQL URL
    if not database_url.startswith('postgresql://'):
        print("\n" + "=" * 80)
        print("ERROR: DATABASE_URL must start with 'postgresql://'")
        print("=" * 80)
        print(f"Current value: {database_url[:30]}...")
        print()
        print("Expected format:")
        print("postgresql://username:password@host:port/database")
        print()
        print("=" * 80)
        sys.exit(1)

    return database_url


def get_environment() -> str:
    """
    Get current environment (production, staging, development).

    Returns:
        str: Environment name (default: 'development')
    """
    return os.getenv('ENVIRONMENT', 'development')


def is_debug() -> bool:
    """
    Check if debug mode is enabled.

    Returns:
        bool: True if DEBUG=true in environment
    """
    return os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')


def get_connection(autocommit: bool = True) -> Any:
    """
    Create a database connection using psycopg2.

    Args:
        autocommit: Whether to enable autocommit mode (default: True)

    Returns:
        psycopg2 connection object

    Raises:
        ImportError: If psycopg2 is not installed
        Exception: If connection fails

    Example:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM contacts")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
    """
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed", file=sys.stderr)
        print("Install with: pip install psycopg2-binary", file=sys.stderr)
        raise

    database_url = get_database_url()

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = autocommit
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}", file=sys.stderr)
        print("Check DATABASE_URL in .env file", file=sys.stderr)
        raise


def test_connection() -> bool:
    """
    Test database connection and print diagnostics.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        print("Testing database connection...")
        conn = get_connection()
        cur = conn.cursor()

        # Test query
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]

        # Get connection info without exposing password
        cur.execute("""
            SELECT current_database() as db,
                   current_user as user,
                   inet_server_addr() as host,
                   inet_server_port() as port
        """)
        info = cur.fetchone()

        cur.close()
        conn.close()

        print("✓ Connection successful!")
        print(f"✓ Database: {info[0]}")
        print(f"✓ User: {info[1]}")
        print(f"✓ Host: {info[2]}:{info[3]}")
        print(f"✓ PostgreSQL: {version.split(',')[0]}")

        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    """Test database configuration and connection."""
    print("=" * 80)
    print("DATABASE CONFIGURATION TEST (FAANG Standards)")
    print("=" * 80)
    print()

    # Test 1: Configuration loading
    print("[1/3] Testing configuration loading...")
    try:
        url = get_database_url()
        # Mask the password for security
        parts = url.split('@')
        if len(parts) == 2:
            creds = parts[0].replace('postgresql://', '').split(':')
            user = creds[0] if creds else 'unknown'
            masked_url = f"postgresql://{user}:****@{parts[1]}"
        else:
            masked_url = "postgresql://****"

        print(f"  ✓ DATABASE_URL: {masked_url}")
        print(f"  ✓ Environment: {get_environment()}")
        print(f"  ✓ Debug mode: {is_debug()}")
        print()
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        sys.exit(1)

    # Test 2: Database connection
    print("[2/3] Testing database connection...")
    if not test_connection():
        print()
        print("=" * 80)
        print("FAILED: Could not connect to database")
        print("=" * 80)
        sys.exit(1)
    print()

    # Test 3: Query execution
    print("[3/3] Testing query execution...")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM contacts")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"  ✓ Query successful")
        print(f"  ✓ Contacts in database: {count:,}")
    except Exception as e:
        print(f"  ✗ Query failed: {e}")
        sys.exit(1)

    print()
    print("=" * 80)
    print("SUCCESS: All tests passed!")
    print("=" * 80)
    sys.exit(0)
