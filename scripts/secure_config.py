"""
Secure configuration loading - FAANG standards
NO DEFAULTS, fail fast if credentials missing

This module provides secure configuration loading without fallback defaults.
All configuration must be provided via environment variables.

Usage:
    from secure_config import get_database_url, get_config

    # Get just the database URL
    db_url = get_database_url()

    # Get all configuration
    config = get_config()

Never commit credentials to git!
Set them in your .env file or environment variables.
"""
import os
import sys
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Raised when required configuration is missing."""
    pass


def get_database_url() -> str:
    """
    Get database URL from environment.

    Fails fast if DATABASE_URL is not set.
    NO fallback to hardcoded values.

    Returns:
        str: Database connection URL

    Raises:
        ConfigError: If DATABASE_URL environment variable is not set

    Example:
        >>> url = get_database_url()
        >>> # Use url with psycopg2 or other database library
    """
    url = os.getenv('DATABASE_URL')

    if not url:
        raise ConfigError(
            "DATABASE_URL environment variable is required.\n"
            "Set it in your .env file or environment.\n"
            "Never commit credentials to git!\n"
            "\n"
            "Example:\n"
            "  export DATABASE_URL='postgresql://user:pass@host:5432/dbname'\n"
            "Or create a .env file:\n"
            "  echo 'DATABASE_URL=postgresql://...' > .env\n"
        )

    # Validate format (basic check)
    if not url.startswith('postgresql://'):
        raise ConfigError(
            f"DATABASE_URL must start with 'postgresql://'\n"
            f"Got: {url[:20]}..."
        )

    return url


def get_webhook_secret(source: str) -> Optional[str]:
    """
    Get webhook secret for a specific source.

    Args:
        source: The webhook source (e.g., 'kajabi', 'paypal', 'ticket_tailor')

    Returns:
        Optional[str]: The webhook secret, or None if not configured

    Example:
        >>> secret = get_webhook_secret('kajabi')
    """
    env_var = f'{source.upper()}_WEBHOOK_SECRET'
    return os.getenv(env_var)


def get_api_key(service: str) -> Optional[str]:
    """
    Get API key for a specific service.

    Args:
        service: The service name (e.g., 'zoho', 'usps')

    Returns:
        Optional[str]: The API key, or None if not configured

    Example:
        >>> api_key = get_api_key('zoho')
    """
    env_var = f'{service.upper()}_API_KEY'
    return os.getenv(env_var)


def get_config() -> Dict[str, Any]:
    """
    Load all required configuration.

    Returns:
        Dict with all config values

    Raises:
        ConfigError: If any required config is missing

    Example:
        >>> config = get_config()
        >>> db_url = config['database_url']
    """
    return {
        'database_url': get_database_url(),
        # Add other required config here as needed
        # 'api_key': get_api_key('service'),
        # 'webhook_secret': get_webhook_secret('source'),
    }


def load_env_file(env_file: str = '.env') -> None:
    """
    Load environment variables from a .env file.

    This is a simple implementation. For production, consider using
    python-dotenv library.

    Args:
        env_file: Path to .env file (default: '.env')

    Example:
        >>> load_env_file()
        >>> url = get_database_url()
    """
    if not os.path.exists(env_file):
        return

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                os.environ[key.strip()] = value


# Example usage and self-test
if __name__ == '__main__':
    print("Secure Configuration Module - Self Test")
    print("=" * 50)

    try:
        # Try to load .env file if it exists
        load_env_file()
        print("✅ .env file loaded (if present)")

        # Test database URL
        config = get_config()
        print("✅ Configuration loaded successfully")
        print(f"   Database URL: {config['database_url'][:30]}...")

        print("\n✅ All tests passed!")
        print("\nConfiguration is properly set up.")

    except ConfigError as e:
        print(f"❌ Configuration error:\n{e}")
        print("\n" + "=" * 50)
        print("SETUP INSTRUCTIONS:")
        print("=" * 50)
        print("1. Create a .env file in the project root:")
        print("   touch .env")
        print("\n2. Add your database URL:")
        print("   echo 'DATABASE_URL=postgresql://...' >> .env")
        print("\n3. Make sure .env is in .gitignore:")
        print("   grep -q '.env' .gitignore || echo '.env' >> .gitignore")
        print("\n4. Never commit credentials to git!")
        print("=" * 50)
        sys.exit(1)
